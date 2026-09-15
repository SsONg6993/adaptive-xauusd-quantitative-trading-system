"""Leakage-safe Phase 3 dataset assembly."""

from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from axq.data.synchronization import synchronize_completed_bars
from axq.data.timeframes import timeframe_delta
from axq.data.validation import validate_candles
from axq.datasets.config import RowPolicy, SplitPolicy
from axq.datasets.manifest import DatasetManifest
from axq.datasets.quality import dataset_quality_report
from axq.datasets.splits import SplitManifest, chronological_split
from axq.features import FeatureManifest, default_registry
from axq.labels import LabelDefinition, LabelManifest, generate_labels
from axq.versioning import canonical_hash


@dataclass(frozen=True)
class DatasetBuildResult:
    frame: pd.DataFrame
    manifest: DatasetManifest
    feature_manifest: FeatureManifest
    label_manifest: LabelManifest
    split_manifest: SplitManifest | None
    quality_report: dict[str, Any]


def dataframe_hash(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps([str(column) for column in frame.columns]).encode())
    digest.update(json.dumps([str(dtype) for dtype in frame.dtypes]).encode())
    digest.update(pd.util.hash_pandas_object(frame, index=True).to_numpy().tobytes())
    return digest.hexdigest()


def _validate_source_frames(
    frames: Mapping[str, pd.DataFrame], base_timeframe: str
) -> None:
    if base_timeframe.upper() not in {key.upper() for key in frames}:
        raise ValueError(f"Missing base timeframe {base_timeframe}")
    for timeframe, frame in frames.items():
        report = validate_candles(frame, timeframe)
        if not report.valid:
            raise ValueError(f"Invalid {timeframe} source: {list(report.errors)}")


def _completed_source_frames(
    frames: Mapping[str, pd.DataFrame],
    *,
    data_available_at: datetime | pd.Timestamp,
) -> dict[str, pd.DataFrame]:
    cutoff = pd.Timestamp(data_available_at)
    if cutoff.tzinfo is None:
        raise ValueError("data_available_at must be timezone-aware")
    cutoff = cutoff.tz_convert("UTC")
    completed: dict[str, pd.DataFrame] = {}
    for timeframe, source in frames.items():
        frame = source.copy()
        opened_at = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
        closes_at = opened_at + pd.Timedelta(timeframe_delta(timeframe))
        frame = frame.loc[closes_at <= cutoff].copy()
        frame["timestamp"] = opened_at.loc[frame.index]
        completed[timeframe] = frame.reset_index(drop=True)
    return completed


def assemble_dataset(
    frames: Mapping[str, pd.DataFrame],
    *,
    dataset_name: str,
    symbol: str,
    base_timeframe: str,
    feature_set_version: str,
    feature_groups: Iterable[str],
    feature_parameters: Mapping[str, Mapping[str, Any]],
    label_definition: LabelDefinition,
    data_available_at: datetime | pd.Timestamp,
    row_policy: RowPolicy | None = None,
    split_policy: SplitPolicy | None = None,
    storage_format: str = "parquet",
    git_commit: str | None = None,
    lower_timeframe: pd.DataFrame | None = None,
) -> DatasetBuildResult:
    policy = row_policy or RowPolicy()
    groups = list(feature_groups)
    base = base_timeframe.upper()
    normalized = _completed_source_frames(
        {key.upper(): value.copy() for key, value in frames.items()},
        data_available_at=data_available_at,
    )
    _validate_source_frames(normalized, base)
    synchronized = synchronize_completed_bars(normalized, base_timeframe=base)
    if synchronized["timestamp"].duplicated().any():
        raise ValueError("Duplicate decision source timestamps are forbidden")
    source_hash = dataframe_hash(synchronized)
    registry = default_registry()
    featured = registry.compute(
        synchronized,
        enabled_groups=groups,
        parameters=feature_parameters,
    )
    feature_manifest = registry.manifest(
        feature_set_version=feature_set_version,
        enabled_groups=groups,
        parameters=feature_parameters,
        available_source_columns=synchronized.columns,
    )
    feature_columns = [
        entry.feature_name
        for entry in feature_manifest.entries
        if entry.enabled and entry.feature_name in featured.columns
    ]
    if not feature_columns:
        raise ValueError("Dataset has no enabled feature columns")
    decision_timestamp = pd.to_datetime(featured["timestamp"], utc=True) + pd.Timedelta(
        timeframe_delta(base)
    )
    label_input = featured.copy()
    label_input["candle_open_timestamp"] = pd.to_datetime(
        featured["timestamp"], utc=True
    )
    label_input["timestamp"] = decision_timestamp
    labels = generate_labels(
        label_input,
        label_definition,
        lower_timeframe=lower_timeframe,
    )
    if set(feature_columns) & set(labels.frame.columns):
        raise ValueError("Feature/label column overlap detected")
    combined = featured.join(labels.frame)
    combined["candle_open_timestamp"] = pd.to_datetime(combined["timestamp"], utc=True)
    combined["decision_timestamp"] = decision_timestamp
    selected_columns = [
        "candle_open_timestamp",
        "decision_timestamp",
        *feature_columns,
        *labels.manifest.target_columns,
        *labels.manifest.metadata_columns,
    ]
    dataset = combined[selected_columns].copy()
    rows_before = len(dataset)
    maximum_warmup = max(
        entry.warmup_rows for entry in feature_manifest.entries if entry.enabled
    )
    if policy.drop_before_max_warmup:
        dataset = dataset.iloc[maximum_warmup:].copy()
    rows_after_warmup = len(dataset)
    missing_critical = set(policy.critical_feature_columns) - set(feature_columns)
    if missing_critical:
        raise ValueError(f"Unknown critical feature columns: {sorted(missing_critical)}")
    if policy.critical_feature_columns:
        dataset = dataset.dropna(subset=policy.critical_feature_columns)
    if not policy.retain_optional_nans:
        dataset = dataset.dropna(subset=feature_columns)
    if policy.drop_incomplete_labels:
        dataset = dataset.dropna(subset=labels.manifest.target_columns)
    dataset = dataset.reset_index(drop=True)
    if dataset.empty:
        raise ValueError("Row policy removed every dataset row")
    split_manifest = None
    if split_policy is not None:
        split_manifest = chronological_split(
            len(dataset),
            train_fraction=split_policy.train_fraction,
            validation_fraction=split_policy.validation_fraction,
            label_horizon_bars=label_definition.horizon_bars,
            purge_bars=split_policy.purge_bars,
            embargo_bars=split_policy.embargo_bars,
        )
    boundaries = None
    if split_manifest:
        fold = split_manifest.folds[0]
        boundaries = {
            "train": fold.train.model_dump(),
            "validation": fold.validation.model_dump(),
            "oos": fold.oos.model_dump(),
        }
    config_body = {
        "dataset_name": dataset_name,
        "symbol": symbol,
        "base_timeframe": base,
        "higher_timeframes": sorted(set(normalized) - {base}),
        "feature_set_version": feature_set_version,
        "feature_groups": groups,
        "feature_parameters": feature_parameters,
        "label": label_definition.model_dump(mode="json"),
        "row_policy": policy.model_dump(mode="json"),
        "split_policy": split_policy.model_dump(mode="json") if split_policy else None,
        "storage_format": storage_format,
        "data_available_at": pd.Timestamp(data_available_at).tz_convert("UTC").isoformat(),
    }
    content_hash = dataframe_hash(dataset)
    manifest = DatasetManifest(
        dataset_name=dataset_name,
        symbol=symbol,
        base_timeframe=base,
        higher_timeframes=sorted(set(normalized) - {base}),
        start_timestamp=dataset["decision_timestamp"].iloc[0],
        end_timestamp=dataset["decision_timestamp"].iloc[-1],
        row_count=len(dataset),
        feature_count=len(feature_columns),
        target_count=len(labels.manifest.target_columns),
        feature_columns=feature_columns,
        target_columns=labels.manifest.target_columns,
        label_metadata_columns=labels.manifest.metadata_columns,
        feature_manifest_id=feature_manifest.manifest_id,
        label_manifest_id=labels.manifest.manifest_id,
        split_manifest_id=split_manifest.manifest_id if split_manifest else None,
        source_data_hash=source_hash,
        dataset_content_hash=content_hash,
        configuration_hash=canonical_hash(config_body),
        decision_timestamp_convention=(
            f"{base} candle open timestamp plus {timeframe_delta(base)}; "
            "features include the just-completed candle; source bars close at or before "
            f"data_available_at={pd.Timestamp(data_available_at).tz_convert('UTC').isoformat()}"
        ),
        train_validation_oos_boundaries=boundaries,
        storage_format=storage_format,
        git_commit=git_commit,
    )
    quality = dataset_quality_report(
        dataset,
        rows_before_filtering=rows_before,
        rows_after_warmup=rows_after_warmup,
        feature_columns=feature_columns,
        target_columns=labels.manifest.target_columns,
        label_metadata_columns=labels.manifest.metadata_columns,
        split_manifest=split_manifest,
        maximum_warmup_rows=maximum_warmup,
    )
    quality["missingness_by_reason"] = {
        "insufficient_history_rows_removed": rows_before - rows_after_warmup,
        "structural_unavailable_cells_retained": int(
            dataset[
                [column for column in feature_columns if column.startswith("structure_")]
            ].isna().sum().sum()
        ),
        "missing_broker_data_rows": 0,
        "optional_unavailable_features": [
            entry.feature_name for entry in feature_manifest.entries if not entry.enabled
        ],
        "missing_mtf_context_cells": int(
            dataset[
                [column for column in feature_columns if column.startswith("mtf_")]
            ].isna().sum().sum()
        ),
    }
    return DatasetBuildResult(
        dataset,
        manifest,
        feature_manifest,
        labels.manifest,
        split_manifest,
        quality,
    )


def write_dataset(result: DatasetBuildResult, output_root: Path) -> Path:
    target = output_root / result.manifest.dataset_id
    manifest_path = target / "dataset.manifest.json"
    if target.exists():
        if not manifest_path.exists():
            raise FileExistsError(f"Dataset directory exists without manifest: {target}")
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("dataset_content_hash") != result.manifest.dataset_content_hash:
            raise FileExistsError(f"Dataset ID collision with different content: {target}")
        return target
    output_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".dataset-", dir=output_root))
    try:
        if result.manifest.storage_format == "parquet":
            try:
                result.frame.to_parquet(temporary / "dataset.parquet", index=False)
            except ImportError as exc:
                raise RuntimeError(
                    "Parquet storage requires pyarrow; install the dataset optional dependency"
                ) from exc
        elif result.manifest.storage_format == "csv_debug":
            result.frame.to_csv(temporary / "dataset.csv.gz", index=False, compression="gzip")
        else:
            raise ValueError(f"Unsupported storage format: {result.manifest.storage_format}")
        result.manifest.write(temporary / "dataset.manifest.json")
        result.feature_manifest.write(temporary / "feature.manifest.json")
        result.label_manifest.write(temporary / "label.manifest.json")
        if result.split_manifest:
            result.split_manifest.write(temporary / "split.manifest.json")
        (temporary / "quality.json").write_text(
            json.dumps(result.quality_report, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        temporary.rename(target)
    except Exception:
        for child in temporary.iterdir():
            child.unlink()
        temporary.rmdir()
        raise
    return target
