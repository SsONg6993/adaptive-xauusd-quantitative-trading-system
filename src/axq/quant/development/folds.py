"""Fresh-state, fold-local development evaluation before immutable final OOS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder  # type: ignore[import-untyped]

from axq.datasets.splits import SplitFold, SplitManifest, walk_forward_splits
from axq.quant.calibration import ProbabilityCalibrator
from axq.quant.config import QuantTrainingConfig
from axq.quant.development.artifacts import file_hash, write_json_atomic
from axq.quant.development.config import WalkForwardConfig
from axq.quant.development.state import RunStateStore
from axq.quant.metrics import evaluate_predictions
from axq.quant.models import build_model
from axq.quant.preprocessing import FrozenPreprocessor
from axq.quant.trainer import EncodedClassifier
from axq.versioning import canonical_hash


@dataclass
class DevelopmentFoldResult:
    fold: int
    preprocessing: FrozenPreprocessor
    model: EncodedClassifier
    calibrator: ProbabilityCalibrator
    metrics: dict[str, Any]
    probabilities: np.ndarray
    predicted_labels: np.ndarray
    selected_features: list[str]
    fit_scopes: dict[str, str]

    def summary(self) -> dict[str, Any]:
        return {
            "fold": self.fold,
            "selected_features": self.selected_features,
            "fit_scopes": self.fit_scopes,
            "fit_rows": {
                "preprocessing": self.preprocessing.fit_row_count,
                "model": self.preprocessing.fit_row_count,
                "calibration": self.calibrator.fit_row_count,
            },
            "metrics": self.metrics,
            "registered": False,
        }


def development_split_manifest(
    *,
    row_count: int,
    final_oos_start: int,
    label_horizon_bars: int,
    policy: WalkForwardConfig,
) -> SplitManifest:
    if final_oos_start <= 0 or final_oos_start > row_count:
        raise ValueError("Immutable final OOS boundary is outside the dataset")
    manifest = walk_forward_splits(
        final_oos_start,
        mode=policy.mode,
        train_length=policy.train_length,
        validation_length=policy.validation_length,
        oos_length=policy.oos_length,
        step_size=policy.step_size,
        label_horizon_bars=label_horizon_bars,
        purge_bars=policy.purge_bars,
        embargo_bars=policy.embargo_bars,
    )
    folds = manifest.folds[: policy.max_folds] if policy.max_folds else manifest.folds
    return manifest.model_copy(
        update={
            "row_count": row_count,
            "folds": folds,
            "policy": manifest.policy
            | {
                "development_row_count": final_oos_start,
                "immutable_final_oos_start": final_oos_start,
                "final_oos_use": "EVALUATION_ONLY",
            },
        }
    )


def _slice(frame: pd.DataFrame, bounds: Any) -> pd.DataFrame:
    return frame.iloc[bounds.start : bounds.stop].copy()


def run_development_fold(
    frame: pd.DataFrame,
    fold: SplitFold,
    *,
    features: list[str],
    target_column: str,
    config: QuantTrainingConfig,
    metadata_columns: list[str] | None = None,
) -> DevelopmentFoldResult:
    np.random.seed(config.random_seed + fold.fold)
    train = _slice(frame, fold.train)
    validation = _slice(frame, fold.validation)
    evaluation = _slice(frame, fold.oos)
    if min(len(train), len(validation), len(evaluation)) <= 0:
        raise ValueError("Development fold contains an empty split")
    preprocessing = FrozenPreprocessor.fit(
        train, features, config.preprocessing, config.feature_selection
    )
    encoder = LabelEncoder().fit(train[target_column].astype(str))
    observed = set(
        pd.concat([validation[target_column], evaluation[target_column]])
        .astype(str)
        .unique()
    )
    if observed - set(encoder.classes_):
        raise ValueError("Development fold contains a class absent from fold TRAIN")
    estimator = build_model(config, selected_device="cpu")
    estimator.fit(
        preprocessing.transform(train),
        encoder.transform(train[target_column].astype(str)),
    )
    model = EncodedClassifier(estimator=estimator, classes_=encoder.classes_)
    calibrator = ProbabilityCalibrator.fit(
        config.calibration.method,
        model.predict_proba(preprocessing.transform(validation)),
        validation[target_column].astype(str).to_numpy(),
        model.classes_,
    )
    metrics: dict[str, Any] = {}
    probabilities = np.empty((0, len(model.classes_)))
    predicted = np.empty(0, dtype=str)
    for name, split in (
        ("train", train),
        ("validation", validation),
        ("fold_oos", evaluation),
    ):
        split_probability = calibrator.transform(
            model.predict_proba(preprocessing.transform(split))
        )
        metadata = None
        if metadata_columns:
            available = [column for column in metadata_columns if column in split]
            metadata = split[available].reset_index(drop=True) if available else None
        metrics[name] = evaluate_predictions(
            split[target_column],
            split_probability,
            model.classes_,
            minimum_confidence=config.hold_policy.minimum_confidence,
            explicit_neutral_class=config.hold_policy.explicit_neutral_class,
            metadata=metadata,
        )
        if name == "fold_oos":
            probabilities = split_probability
            predicted = np.asarray(model.classes_, dtype=str)[
                np.argmax(split_probability, axis=1)
            ]
    return DevelopmentFoldResult(
        fold=fold.fold,
        preprocessing=preprocessing,
        model=model,
        calibrator=calibrator,
        metrics=metrics,
        probabilities=probabilities,
        predicted_labels=predicted,
        selected_features=preprocessing.selected_features,
        fit_scopes={
            "preprocessing": "FOLD_TRAIN",
            "feature_selection": "FOLD_TRAIN",
            "model": "FOLD_TRAIN",
            "calibration": "FOLD_VALIDATION",
            "evaluation": "FOLD_OOS",
        },
    )


def fold_identity(
    fold: SplitFold, *, dataset_id: str, config_hash: str, features: list[str]
) -> str:
    identity = canonical_hash(
        {
            "fold": fold.model_dump(mode="json"),
            "dataset_id": dataset_id,
            "config_hash": config_hash,
            "features": features,
        }
    )[:16]
    return f"fold-{fold.fold:03d}-{identity}"


def completed_fold_summary(
    output_dir: str | Path, fold_id: str, *, config_hash: str
) -> dict[str, Any] | None:
    state = RunStateStore(Path(output_dir) / fold_id / "status.json")
    payload = state.load()
    if not payload:
        return None
    if payload.get("run_id") != fold_id or payload.get("config_hash") != config_hash:
        raise ValueError("Completed fold identity mismatch")
    summary = Path(output_dir) / fold_id / "fold_summary.json"
    if payload.get("status") != "COMPLETE" or not summary.is_file():
        return None
    import json

    result = json.loads(summary.read_text(encoding="utf-8"))
    return result if isinstance(result, dict) else None


def _aggregate_fold_metrics(folds: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "accuracy",
        "balanced_accuracy",
        "f1_macro",
        "log_loss",
        "brier_score",
        "expected_calibration_error",
        "prediction_coverage",
    ]
    aggregate: dict[str, Any] = {}
    for key in keys:
        values = np.asarray(
            [item["metrics"]["fold_oos"][key] for item in folds], dtype=float
        )
        aggregate[key] = {
            "mean": float(values.mean()),
            "median": float(np.median(values)),
            "std": float(values.std(ddof=0)),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
        }
    balanced = [float(item["metrics"]["fold_oos"]["balanced_accuracy"]) for item in folds]
    aggregate["best_fold"] = int(folds[int(np.argmax(balanced))]["fold"])
    aggregate["worst_fold"] = int(folds[int(np.argmin(balanced))]["fold"])
    aggregate["temporal_degradation"] = balanced[-1] - balanced[0]
    return aggregate


def run_walk_forward(
    frame: pd.DataFrame,
    manifest: SplitManifest,
    *,
    features: list[str],
    target_column: str,
    config: QuantTrainingConfig,
    dataset_id: str,
    output_dir: str | Path,
    metadata_columns: list[str] | None = None,
) -> dict[str, Any]:
    final_oos_start = manifest.policy.get("immutable_final_oos_start")
    if not isinstance(final_oos_start, int):
        raise ValueError("Walk-forward manifest lacks immutable final OOS boundary")
    if any(fold.oos.stop > final_oos_start for fold in manifest.folds):
        raise ValueError("Development fold overlaps immutable final OOS")
    root = Path(output_dir)
    rows: list[dict[str, Any]] = []
    for fold in manifest.folds:
        fold_id = fold_identity(
            fold,
            dataset_id=dataset_id,
            config_hash=config.config_hash,
            features=features,
        )
        completed = completed_fold_summary(root, fold_id, config_hash=config.config_hash)
        if completed is not None:
            rows.append(completed | {"status": "SKIPPED_COMPLETE"})
            continue
        fold_dir = root / fold_id
        state = RunStateStore(fold_dir / "status.json")
        state.start(fold_id, config_hash=config.config_hash)
        try:
            result = run_development_fold(
                frame,
                fold,
                features=features,
                target_column=target_column,
                config=config,
                metadata_columns=metadata_columns,
            )
            evaluation = _slice(frame, fold.oos)
            confidence = result.probabilities.max(axis=1)
            predictions = pd.DataFrame(
                {
                    "decision_timestamp": pd.to_datetime(
                        evaluation["decision_timestamp"], utc=True
                    ),
                    "actual_label": evaluation[target_column].astype(str).to_numpy(),
                    "predicted_label": result.predicted_labels,
                    "confidence": confidence,
                }
            )
            for index, label in enumerate(result.model.classes_):
                predictions[f"probability_{label}"] = result.probabilities[:, index]
            fold_dir.mkdir(parents=True, exist_ok=True)
            predictions_path = fold_dir / "predictions.parquet"
            predictions.to_parquet(predictions_path, index=False)
            summary = result.summary() | {
                "fold_id": fold_id,
                "status": "COMPLETE",
                "dataset_id": dataset_id,
                "model_identity": canonical_hash(
                    {
                        "fold_id": fold_id,
                        "selected_features": result.selected_features,
                        "architecture": config.architecture.value,
                    }
                ),
                "periods": {
                    name: {
                        "start": pd.to_datetime(
                            _slice(frame, bounds)["decision_timestamp"], utc=True
                        )
                        .iloc[0]
                        .isoformat(),
                        "end": pd.to_datetime(_slice(frame, bounds)["decision_timestamp"], utc=True)
                        .iloc[-1]
                        .isoformat(),
                        "rows": bounds.size,
                    }
                    for name, bounds in (
                        ("train", fold.train),
                        ("validation", fold.validation),
                        ("fold_oos", fold.oos),
                    )
                },
                "registered": False,
            }
            summary_path = fold_dir / "fold_summary.json"
            write_json_atomic(summary_path, summary)
            state.complete(
                fold_id,
                config_hash=config.config_hash,
                artifacts={
                    "fold_summary": file_hash(summary_path),
                    "predictions": file_hash(predictions_path),
                },
            )
            rows.append(summary)
        except Exception as exc:
            state.fail(
                fold_id,
                config_hash=config.config_hash,
                failure=f"{type(exc).__name__}: {exc}",
            )
            raise
    completed_rows = [row for row in rows if row["status"] in {"COMPLETE", "SKIPPED_COMPLETE"}]
    summary = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "split_manifest_id": manifest.manifest_id,
        "folds": rows,
        "aggregate": _aggregate_fold_metrics(completed_rows),
        "immutable_final_oos_start": final_oos_start,
        "immutable_final_oos_used_for_development": False,
        "fold_models_registered": False,
    }
    write_json_atomic(root / "walk_forward_summary.json", summary)
    return summary
