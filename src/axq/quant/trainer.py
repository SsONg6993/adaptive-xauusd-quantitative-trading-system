"""Leakage-safe Quant Agent training orchestration."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder  # type: ignore[import-untyped]

from axq.quant.artifacts import dump_artifact, verify_run, write_json
from axq.quant.calibration import ProbabilityCalibrator
from axq.quant.config import QuantTrainingConfig
from axq.quant.dataset import TrainingDataset, load_training_dataset
from axq.quant.device import resolve_device
from axq.quant.experiment import ExperimentTracker
from axq.quant.manifest import ModelManifest
from axq.quant.metrics import evaluate_predictions, label_to_signal
from axq.quant.models import ProbabilisticClassifier, build_model
from axq.quant.preprocessing import FrozenPreprocessor
from axq.quant.registry import LocalModelRegistry


@dataclass
class EncodedClassifier:
    estimator: ProbabilisticClassifier
    classes_: np.ndarray

    def predict_proba(self, values: np.ndarray) -> np.ndarray:
        return np.asarray(self.estimator.predict_proba(values), dtype=float)


@dataclass(frozen=True)
class TrainingResult:
    run_dir: Path
    manifest: ModelManifest
    metrics: dict[str, Any]


def _git_identity() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Training requires a Git identity")
    commit = result.stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0:
        raise RuntimeError("Unable to inspect Git working tree")
    if not status.stdout:
        return commit
    digest = hashlib.sha256(status.stdout.encode())
    difference = subprocess.run(
        ["git", "diff", "--binary", "HEAD"],
        check=False,
        capture_output=True,
    )
    digest.update(difference.stdout)
    for line in sorted(status.stdout.splitlines()):
        if not line.startswith("?? "):
            continue
        path = Path(line[3:])
        if path.is_file():
            digest.update(path.as_posix().encode())
            digest.update(path.read_bytes())
    return f"{commit}-dirty-{digest.hexdigest()[:12]}"


def _period(frame: pd.DataFrame) -> str:
    timestamp = pd.to_datetime(frame["decision_timestamp"], utc=True)
    return f"{timestamp.iloc[0].isoformat()} / {timestamp.iloc[-1].isoformat()}"


def _target_column(dataset: TrainingDataset, requested: str | None) -> str:
    if requested is None:
        if len(dataset.manifest.target_columns) != 1:
            raise ValueError("target_column is required for a multi-target dataset")
        return dataset.manifest.target_columns[0]
    if requested not in dataset.manifest.target_columns:
        raise ValueError(f"Target is absent from label manifest: {requested}")
    return requested


def _metadata(dataset: TrainingDataset, frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[:, dataset.manifest.label_metadata_columns].reset_index(drop=True)


def _model_explanation(
    model: EncodedClassifier, selected_features: list[str]
) -> dict[str, Any]:
    coefficients = getattr(model.estimator, "coef_", None)
    if coefficients is not None:
        matrix = np.asarray(coefficients, dtype=float)
        names = [str(value) for value in model.classes_]
        if matrix.shape[0] == 1 and len(names) == 2:
            names = [names[1]]
        classes: dict[str, Any] = {}
        for index, label in enumerate(names):
            row = matrix[index]
            positive = np.argsort(row)[-10:][::-1]
            negative = np.argsort(row)[:10]
            classes[label] = {
                "top_positive": [
                    {"feature": selected_features[i], "coefficient": float(row[i])}
                    for i in positive
                ],
                "top_negative": [
                    {"feature": selected_features[i], "coefficient": float(row[i])}
                    for i in negative
                ],
            }
        return {"method": "coefficients", "classes": classes}
    importance = getattr(model.estimator, "feature_importances_", None)
    if importance is not None:
        values = np.asarray(importance, dtype=float)
        order = np.argsort(values)[-20:][::-1]
        return {
            "method": "feature_importance",
            "features": [
                {"feature": selected_features[i], "importance": float(values[i])}
                for i in order
            ],
            "permutation_importance_compatible": True,
            "shap_compatible": True,
        }
    return {"method": "none", "permutation_importance_compatible": True}


def train_quant_model(
    config: QuantTrainingConfig,
    *,
    evaluate_final_oos: bool = True,
) -> TrainingResult:
    np.random.seed(config.random_seed)
    dataset = load_training_dataset(config.dataset_dir)
    if not dataset.manifest.git_commit:
        raise ValueError("Dataset manifest lacks Git identity")
    target_column = _target_column(dataset, config.target_column)
    train, validation, oos = dataset.split_frames()
    features = list(dataset.manifest.feature_columns)
    processor = FrozenPreprocessor.fit(
        train, features, config.preprocessing, config.feature_selection
    )
    x_train = processor.transform(train)
    x_validation = processor.transform(validation)
    device = resolve_device(config.device, config.architecture)
    estimator = build_model(config, selected_device=str(device["selected"]))
    encoder = LabelEncoder().fit(train[target_column].astype(str))
    development_labels = set(validation[target_column].astype(str).unique())
    if development_labels - set(encoder.classes_):
        raise ValueError("VALIDATION contains a class absent from TRAIN")
    y_train = encoder.transform(train[target_column].astype(str))
    estimator.fit(x_train, y_train)
    model = EncodedClassifier(estimator=estimator, classes_=encoder.classes_)
    validation_probabilities = model.predict_proba(x_validation)
    calibrator = ProbabilityCalibrator.fit(
        config.calibration.method,
        validation_probabilities,
        validation[target_column].astype(str).to_numpy(),
        model.classes_,
    )
    split_metrics: dict[str, Any] = {}
    for name, frame in (("train", train), ("validation", validation)):
        probability = calibrator.transform(model.predict_proba(processor.transform(frame)))
        split_metrics[name] = evaluate_predictions(
            frame[target_column],
            probability,
            model.classes_,
            minimum_confidence=config.hold_policy.minimum_confidence,
            explicit_neutral_class=config.hold_policy.explicit_neutral_class,
            metadata=_metadata(dataset, frame),
        )
    if evaluate_final_oos:
        # Explicit one-way final evaluation after every fitted component is frozen.
        oos_probability = calibrator.transform(model.predict_proba(processor.transform(oos)))
        split_metrics["oos"] = evaluate_predictions(
            oos[target_column],
            oos_probability,
            model.classes_,
            minimum_confidence=config.hold_policy.minimum_confidence,
            explicit_neutral_class=config.hold_policy.explicit_neutral_class,
            metadata=_metadata(dataset, oos),
        )
    git_commit = _git_identity()
    mapping = {label: label_to_signal(label) for label in model.classes_}
    if not set(mapping.values()) <= {"BUY", "SELL", "HOLD"}:
        raise ValueError(f"Unsupported label-to-signal class mapping: {mapping}")
    provisional = ModelManifest(
        architecture=config.architecture.value,
        dataset_id=dataset.manifest.dataset_id,
        feature_manifest_id=dataset.manifest.feature_manifest_id,
        label_manifest_id=dataset.manifest.label_manifest_id,
        split_manifest_id=dataset.split_manifest.manifest_id,
        target_column=target_column,
        class_mapping=mapping,
        selected_features=processor.selected_features,
        feature_list_version=processor.feature_list_version,
        preprocessing_version="quant-preprocessing-1.0.0",
        calibration_method=config.calibration.method,
        training_period=_period(train),
        validation_period=_period(validation),
        oos_period=_period(oos),
        metrics=split_metrics,
        random_seed=config.random_seed,
        hyperparameters=config.model_hyperparameters,
        config_hash=config.config_hash,
        git_commit=git_commit,
        device=device,
        artifact_paths={},
        artifact_hashes={},
    )
    run_dir = config.output_root / provisional.model_id
    if run_dir.exists():
        manifest_path = run_dir / "model.manifest.json"
        if not manifest_path.exists():
            raise FileExistsError(f"Incomplete existing run directory: {run_dir}")
        existing = verify_run(run_dir)
        metrics = json.loads((run_dir / existing.artifact_paths["metrics"]).read_text())
        if not isinstance(metrics, dict):
            raise ValueError("Existing metrics artifact is invalid")
        return TrainingResult(run_dir, existing, metrics)
    run_dir.mkdir(parents=True, exist_ok=True)
    tracker = ExperimentTracker(config.output_root.parent / "experiments.sqlite3")
    tracker.start(
        provisional.model_id,
        config.architecture.value,
        dataset.manifest.dataset_id,
        config.model_dump(mode="json"),
        str(device["selected"]),
    )
    try:
        paths = {
            "model": "model.joblib",
            "preprocessing": "preprocessing.joblib",
            "calibration": "calibration.joblib",
            "selected_features": "selected_features.json",
            "training_config": "training_config.json",
            "metrics": "metrics.json",
            "confusion_matrices": "confusion_matrices.json",
            "class_mapping": "class_mapping.json",
            "run_summary": "run_summary.json",
            "explanations": "explanations.json",
        }
        hashes = {
            "model": dump_artifact(model, run_dir / paths["model"]),
            "preprocessing": dump_artifact(processor, run_dir / paths["preprocessing"]),
            "calibration": dump_artifact(calibrator, run_dir / paths["calibration"]),
            "selected_features": write_json(
                {
                    "version": processor.feature_list_version,
                    "features": processor.selected_features,
                },
                run_dir / paths["selected_features"],
            ),
            "training_config": write_json(
                config.model_dump(mode="json")
                | {"final_oos_evaluated": evaluate_final_oos},
                run_dir / paths["training_config"],
            ),
            "metrics": write_json(split_metrics, run_dir / paths["metrics"]),
            "confusion_matrices": write_json(
                {name: value["confusion_matrix"] for name, value in split_metrics.items()},
                run_dir / paths["confusion_matrices"],
            ),
            "class_mapping": write_json(mapping, run_dir / paths["class_mapping"]),
            "run_summary": write_json(
                {
                    "run_id": provisional.model_id,
                    "status": "COMPLETE",
                    "fit_scopes": {
                        "preprocessing": "TRAIN",
                        "model": "TRAIN",
                        "calibration": "VALIDATION",
                        "final_evaluation": "OOS" if evaluate_final_oos else "NOT_RUN",
                    },
                    "fit_rows": {
                        "preprocessing": processor.fit_row_count,
                        "model": len(train),
                        "calibration": calibrator.fit_row_count,
                    },
                },
                run_dir / paths["run_summary"],
            ),
            "explanations": write_json(
                _model_explanation(model, processor.selected_features),
                run_dir / paths["explanations"],
            ),
        }
        manifest = provisional.model_copy(
            update={"artifact_paths": paths, "artifact_hashes": hashes}
        )
        manifest.write(run_dir / "model.manifest.json")
        LocalModelRegistry(config.output_root / "registry.json").register(
            manifest.model_id, run_dir
        )
        tracker.finish(manifest.model_id, split_metrics)
    except Exception as exc:
        tracker.fail(provisional.model_id, str(exc))
        raise
    return TrainingResult(run_dir, manifest, split_metrics)


def metrics_json(result: TrainingResult) -> str:
    return json.dumps(result.metrics, indent=2, sort_keys=True)
