from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from axq.datasets import (
    RowPolicy,
    SplitPolicy,
    assemble_dataset,
    chronological_split,
    walk_forward_splits,
    write_dataset,
)
from axq.datasets.preprocessing import fit_on_training_only
from axq.labels import LabelDefinition, LabelKind, ThresholdMode


def candles(rows: int = 80, frequency: str = "5min") -> pd.DataFrame:
    x = np.arange(rows, dtype=float)
    close = 100.0 + 0.05 * x + np.sin(x / 3.0)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-05", periods=rows, freq=frequency, tz="UTC"),
            "open": close - 0.1,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "tick_volume": 100 + x % 11,
            "spread": 20,
        }
    )


def definition(threshold: float = 0.0) -> LabelDefinition:
    return LabelDefinition(
        name="next_3",
        version="direction-3-v1",
        kind=LabelKind.DIRECTION,
        horizon_bars=3,
        threshold_mode=ThresholdMode.PERCENTAGE,
        neutral_threshold=threshold,
    )


def build(
    frame: pd.DataFrame,
    *,
    threshold: float = 0.0,
    split: SplitPolicy | None = None,
    storage_format: str = "csv_debug",
):
    return assemble_dataset(
        {"M5": frame},
        dataset_name="tiny",
        symbol="XAUUSD",
        base_timeframe="M5",
        feature_set_version="test-v1",
        feature_groups=["price_action", "volatility"],
        feature_parameters={
            "volatility_v2": {"atr_period": 2, "rolling_period": 3}
        },
        label_definition=definition(threshold),
        row_policy=RowPolicy(
            critical_feature_columns=["pa_body", "pa_range", "vol_atr_2"]
        ),
        split_policy=split,
        storage_format=storage_format,
        git_commit="abc123",
    )


def test_split_chronology_purge_and_embargo() -> None:
    manifest = chronological_split(
        100,
        train_fraction=0.6,
        validation_fraction=0.2,
        label_horizon_bars=5,
        purge_bars=2,
        embargo_bars=3,
    )
    fold = manifest.folds[0]
    assert (fold.train.start, fold.train.stop) == (0, 55)
    assert (fold.validation.start, fold.validation.stop) == (63, 75)
    assert (fold.oos.start, fold.oos.stop) == (83, 100)
    assert fold.train.stop + manifest.purge_bars <= 60
    assert fold.validation.stop + manifest.purge_bars <= 80


def test_walk_forward_split_definitions_are_deterministic() -> None:
    first = walk_forward_splits(
        80, mode="expanding", train_length=30, validation_length=10,
        oos_length=10, step_size=10, label_horizon_bars=3, purge_bars=3,
        embargo_bars=1,
    )
    second = walk_forward_splits(
        80, mode="expanding", train_length=30, validation_length=10,
        oos_length=10, step_size=10, label_horizon_bars=3, purge_bars=3,
        embargo_bars=1,
    )
    assert first.manifest_id == second.manifest_id
    assert len(first.folds) == 4
    assert first.folds[1].train.start == 0
    rolling = walk_forward_splits(
        80, mode="rolling", train_length=30, validation_length=10,
        oos_length=10, step_size=10, label_horizon_bars=3,
    )
    assert rolling.folds[1].train.start == 10


class RecordingTransformer:
    def __init__(self) -> None:
        self.rows_seen = -1
        self.maximum = np.nan

    def fit(self, values: pd.DataFrame) -> RecordingTransformer:
        self.rows_seen = len(values)
        self.maximum = float(values.max().max())
        return self


def test_preprocessing_fits_training_only() -> None:
    frame = pd.DataFrame({"feature": list(range(60)) + [10_000] * 40})
    split = chronological_split(
        100, label_horizon_bars=3, purge_bars=3, embargo_bars=0
    ).folds[0]
    component = RecordingTransformer()
    fit_on_training_only(component, frame, fold=split, feature_columns=["feature"])
    assert component.rows_seen == split.train.size
    assert component.maximum < 10_000


def test_dataset_reproducibility_config_identity_and_separation() -> None:
    first = build(candles(), split=SplitPolicy(purge_bars=3))
    second = build(candles(), split=SplitPolicy(purge_bars=3))
    changed = build(candles(), threshold=0.001, split=SplitPolicy(purge_bars=3))
    assert first.manifest.dataset_id == second.manifest.dataset_id
    assert first.manifest.dataset_id != changed.manifest.dataset_id
    assert first.manifest.feature_manifest_id == first.feature_manifest.manifest_id
    assert first.manifest.label_manifest_id == first.label_manifest.manifest_id
    assert not set(first.manifest.feature_columns) & set(
        first.manifest.target_columns + first.manifest.label_metadata_columns
    )
    assert first.quality_report["feature_label_separation"]
    assert first.quality_report["rows_after_warmup"] < first.quality_report[
        "rows_before_filtering"
    ]


def test_future_mutation_does_not_change_earlier_dataset_rows() -> None:
    source = candles()
    baseline = build(source)
    mutated = source.copy()
    mutated.loc[50:, ["open", "high", "low", "close"]] += 1000.0
    changed = build(mutated)
    cutoff = pd.Timestamp("2026-01-05 04:10Z")
    earlier_columns = [
        "decision_timestamp",
        *baseline.manifest.feature_columns,
    ]
    left = baseline.frame.loc[
        baseline.frame["decision_timestamp"] <= cutoff, earlier_columns
    ].reset_index(drop=True)
    right = changed.frame.loc[
        changed.frame["decision_timestamp"] <= cutoff, earlier_columns
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right)


def test_mtf_causality_and_exact_close_boundary() -> None:
    m5 = candles(36)
    h1 = candles(3, "1h")
    kwargs = dict(
        dataset_name="mtf",
        symbol="XAUUSD",
        base_timeframe="M5",
        feature_set_version="test",
        feature_groups=["price_action", "multi_timeframe"],
        feature_parameters={},
        label_definition=LabelDefinition(
            name="next_1", version="v1", kind=LabelKind.DIRECTION, horizon_bars=1
        ),
        row_policy=RowPolicy(),
        split_policy=None,
        storage_format="csv_debug",
    )
    baseline = assemble_dataset({"M5": m5, "H1": h1}, **kwargs)
    first_ratio = baseline.frame["mtf_close_ratio_h1"].first_valid_index()
    assert first_ratio is not None
    assert baseline.frame.loc[first_ratio, "decision_timestamp"] == pd.Timestamp(
        "2026-01-05 01:05Z"
    )
    changed_h1 = h1.copy()
    changed_h1.loc[1:, ["open", "high", "low", "close"]] += 500
    changed = assemble_dataset({"M5": m5, "H1": changed_h1}, **kwargs)
    mask = baseline.frame["decision_timestamp"] <= pd.Timestamp("2026-01-05 02:00Z")
    pd.testing.assert_series_equal(
        baseline.frame.loc[mask, "mtf_close_ratio_h1"],
        changed.frame.loc[mask, "mtf_close_ratio_h1"],
    )


def test_duplicate_timestamp_rejected() -> None:
    source = candles()
    duplicated = pd.concat([source, source.iloc[[5]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        build(duplicated)


def test_immutable_debug_storage(tmp_path: Path) -> None:
    result = build(candles())
    target = write_dataset(result, tmp_path)
    assert (target / "dataset.csv.gz").exists()
    assert write_dataset(result, tmp_path) == target
    manifest_path = target / "dataset.manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["dataset_content_hash"] = "tampered"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(FileExistsError, match="different content"):
        write_dataset(result, tmp_path)
