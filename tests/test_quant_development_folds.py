from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from axq.datasets.splits import IndexRange, SplitFold
from axq.features.manifest import FeatureManifest, FeatureManifestEntry
from axq.quant.config import Architecture, QuantTrainingConfig
from axq.quant.development.ablation import feature_ablation_variants
from axq.quant.development.config import WalkForwardConfig
from axq.quant.development.folds import (
    development_split_manifest,
    run_development_fold,
    run_walk_forward,
)


def frame() -> pd.DataFrame:
    values = np.arange(18, dtype=float)
    return pd.DataFrame(
        {
            "decision_timestamp": pd.date_range(
                "2026-01-01", periods=18, freq="5min", tz="UTC"
            ),
            "f1": values,
            "f2": values % 3,
            "target": np.where(values % 2 == 0, "DOWN", "UP"),
        }
    )


def fold() -> SplitFold:
    return SplitFold(
        fold=0,
        train=IndexRange(start=0, stop=8),
        validation=IndexRange(start=8, stop=12),
        oos=IndexRange(start=12, stop=16),
        purged_train_rows=0,
        purged_validation_rows=0,
        embargoed_validation_rows=0,
        embargoed_oos_rows=0,
    )


def test_each_fold_fits_fresh_state_on_its_own_train_and_validation_rows() -> None:
    config = QuantTrainingConfig(
        architecture=Architecture.LOGISTIC,
        dataset_dir="unused",
        calibration={"method": "sigmoid"},
    )

    first = run_development_fold(
        frame(), fold(), features=["f1", "f2"], target_column="target", config=config
    )
    second_fold = fold().model_copy(
        update={
            "fold": 1,
            "train": IndexRange(start=2, stop=10),
            "validation": IndexRange(start=10, stop=14),
            "oos": IndexRange(start=14, stop=18),
        }
    )
    second = run_development_fold(
        frame(), second_fold, features=["f1", "f2"], target_column="target", config=config
    )

    assert first.preprocessing is not second.preprocessing
    assert first.model is not second.model
    assert first.calibrator is not second.calibrator
    assert first.preprocessing.fit_row_count == 8
    assert first.calibrator.fit_row_count == 4
    assert first.fit_scopes == {
        "preprocessing": "FOLD_TRAIN",
        "feature_selection": "FOLD_TRAIN",
        "model": "FOLD_TRAIN",
        "calibration": "FOLD_VALIDATION",
        "evaluation": "FOLD_OOS",
    }


def test_walk_forward_generation_stops_before_immutable_final_oos() -> None:
    policy = WalkForwardConfig(
        enabled=True,
        train_length=8,
        validation_length=4,
        oos_length=4,
        step_size=4,
    )

    manifest = development_split_manifest(
        row_count=30,
        final_oos_start=20,
        label_horizon_bars=1,
        policy=policy,
    )

    assert max(item.oos.stop for item in manifest.folds) <= 20
    assert manifest.policy["immutable_final_oos_start"] == 20


def test_feature_group_ablation_uses_manifest_groups() -> None:
    manifest = FeatureManifest(
        feature_set_version="test",
        entries=[
            FeatureManifestEntry(
                feature_name=name,
                feature_group=group,
                parameters={},
                implementation_version="1",
                enabled=True,
                minimum_lookback=1,
                warmup_rows=0,
                valid_from_row=0,
                required_source_columns=["close"],
                output_dtype="float64",
                causal_status="causal",
            )
            for name, group in [("trend_a", "TREND"), ("mom_a", "MOMENTUM")]
        ],
    )

    variants = feature_ablation_variants(
        manifest,
        ["trend_a", "mom_a"],
        groups=["TREND", "MOMENTUM"],
        single_features=["mom_a"],
    )

    assert variants["ALL_FEATURES"] == ["trend_a", "mom_a"]
    assert variants["ALL_MINUS_TREND"] == ["mom_a"]
    assert variants["ALL_MINUS_MOMENTUM"] == ["trend_a"]
    assert variants["ALL_MINUS_FEATURE_mom_a"] == ["trend_a"]


def test_walk_forward_preserves_completed_fold_outputs_on_resume(tmp_path: Path) -> None:
    config = QuantTrainingConfig(
        architecture=Architecture.LOGISTIC,
        dataset_dir="unused",
        calibration={"method": "none"},
    )
    policy = WalkForwardConfig(
        enabled=True,
        train_length=6,
        validation_length=4,
        oos_length=4,
        step_size=4,
    )
    manifest = development_split_manifest(
        row_count=18,
        final_oos_start=18,
        label_horizon_bars=1,
        policy=policy,
    )

    first = run_walk_forward(
        frame(),
        manifest,
        features=["f1", "f2"],
        target_column="target",
        config=config,
        dataset_id="ds-test",
        output_dir=tmp_path,
    )
    second = run_walk_forward(
        frame(),
        manifest,
        features=["f1", "f2"],
        target_column="target",
        config=config,
        dataset_id="ds-test",
        output_dir=tmp_path,
    )

    assert len(first["folds"]) == 2
    assert all(item["status"] == "COMPLETE" for item in first["folds"])
    assert all(item["status"] == "SKIPPED_COMPLETE" for item in second["folds"])
    assert first["immutable_final_oos_used_for_development"] is False
