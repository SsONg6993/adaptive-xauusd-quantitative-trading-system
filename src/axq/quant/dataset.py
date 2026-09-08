"""Strict loading and identity verification for immutable Phase 3 datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from axq.datasets.builder import dataframe_hash
from axq.datasets.manifest import DatasetManifest
from axq.datasets.splits import SplitManifest
from axq.features.manifest import FeatureManifest
from axq.labels.manifest import LabelManifest


@dataclass(frozen=True)
class TrainingDataset:
    root: Path
    frame: pd.DataFrame
    manifest: DatasetManifest
    feature_manifest: FeatureManifest
    label_manifest: LabelManifest
    split_manifest: SplitManifest

    def split_frames(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        fold = self.split_manifest.folds[0]
        return (
            self.frame.iloc[fold.train.start : fold.train.stop].copy(),
            self.frame.iloc[fold.validation.start : fold.validation.stop].copy(),
            self.frame.iloc[fold.oos.start : fold.oos.stop].copy(),
        )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required artifact is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest is not an object: {path}")
    return payload


def _parse_manifest(model: type[Any], payload: dict[str, Any], identity: str) -> Any:
    body = dict(payload)
    claimed = body.pop(identity, None)
    parsed = model.model_validate(body)
    actual = getattr(parsed, identity)
    if claimed != actual:
        raise ValueError(f"Corrupt {identity}: claimed {claimed!r}, computed {actual!r}")
    return parsed


def load_training_dataset(root: str | Path) -> TrainingDataset:
    directory = Path(root)
    manifest = _parse_manifest(
        DatasetManifest, _read_json(directory / "dataset.manifest.json"), "dataset_id"
    )
    features = _parse_manifest(
        FeatureManifest, _read_json(directory / "feature.manifest.json"), "manifest_id"
    )
    labels = _parse_manifest(
        LabelManifest, _read_json(directory / "label.manifest.json"), "manifest_id"
    )
    splits = _parse_manifest(
        SplitManifest, _read_json(directory / "split.manifest.json"), "manifest_id"
    )
    if directory.name != manifest.dataset_id:
        raise ValueError("Dataset directory name does not match dataset ID")
    identities = {
        "feature": (manifest.feature_manifest_id, features.manifest_id),
        "label": (manifest.label_manifest_id, labels.manifest_id),
        "split": (manifest.split_manifest_id, splits.manifest_id),
    }
    for name, (expected, actual) in identities.items():
        if expected != actual:
            raise ValueError(f"{name} manifest identity mismatch")
    data_path = directory / (
        "dataset.parquet" if manifest.storage_format == "parquet" else "dataset.csv.gz"
    )
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset payload is missing: {data_path}")
    frame = (
        pd.read_parquet(data_path)
        if manifest.storage_format == "parquet"
        else pd.read_csv(data_path)
    )
    required = [
        "candle_open_timestamp",
        "decision_timestamp",
        *manifest.feature_columns,
        *manifest.target_columns,
        *manifest.label_metadata_columns,
    ]
    if list(frame.columns) != required:
        raise ValueError("Dataset schema or exact feature/target order differs from manifest")
    if len(frame) != manifest.row_count or splits.row_count != len(frame):
        raise ValueError("Dataset or split row count mismatch")
    if dataframe_hash(frame) != manifest.dataset_content_hash:
        raise ValueError("Dataset content hash mismatch")
    timestamps = pd.to_datetime(frame["decision_timestamp"], utc=True)
    if not timestamps.is_monotonic_increasing:
        raise ValueError("Decision timestamps are not chronological")
    if timestamps.duplicated().any():
        raise ValueError("Duplicate decision timestamps are forbidden")
    if set(manifest.feature_columns) & set(
        manifest.target_columns + manifest.label_metadata_columns
    ):
        raise ValueError("Feature/target separation violated")
    values = frame[manifest.feature_columns].to_numpy(dtype=float)
    if np.isinf(values).any():
        raise ValueError("Infinite feature value violates training policy")
    return TrainingDataset(directory, frame, manifest, features, labels, splits)
