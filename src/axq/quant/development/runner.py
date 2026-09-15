"""Single-experiment planning and artifact orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from axq.quant.dataset import load_training_dataset
from axq.quant.development.artifacts import (
    file_hash,
    verify_development_run,
    write_development_manifest,
    write_json_atomic,
    write_text_atomic,
)
from axq.quant.development.config import ExperimentConfig, development_run_id
from axq.quant.development.diagnostics import (
    calibration_diagnostics,
    overfitting_report,
    segment_predictions,
    threshold_diagnostics,
)
from axq.quant.development.state import RunStateStore
from axq.quant.device import resolve_device
from axq.quant.inference import QuantAgent
from axq.quant.metrics import signals_from_probabilities
from axq.quant.trainer import _git_identity, train_quant_model


@dataclass(frozen=True)
class DevelopmentRunResult:
    run_id: str
    run_dir: Path
    model_run_dir: Path
    manifest: dict[str, Any]


def plan_experiment(config: ExperimentConfig) -> dict[str, Any]:
    dataset = load_training_dataset(config.training.dataset_dir)
    git_identity = _git_identity()
    run_id = development_run_id(
        config, dataset_id=dataset.manifest.dataset_id, git_identity=git_identity
    )
    device = resolve_device(config.training.device, config.training.architecture)
    return {
        "status": "DRY_RUN",
        "run_id": run_id,
        "run_dir": str(config.output_root / run_id),
        "dataset_id": dataset.manifest.dataset_id,
        "feature_manifest_id": dataset.manifest.feature_manifest_id,
        "label_manifest_id": dataset.manifest.label_manifest_id,
        "split_manifest_id": dataset.split_manifest.manifest_id,
        "architecture": config.training.architecture.value,
        "device": device,
        "fit_performed": False,
        "final_oos_use": "NOT_ACCESSED",
        "development_selection_scopes": ["TRAIN", "VALIDATION", "WALK_FORWARD_VALIDATION"],
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _prediction_frame(
    frame: pd.DataFrame,
    probability: np.ndarray,
    classes: np.ndarray,
    threshold: float,
    *,
    target_column: str,
    metadata_columns: list[str],
) -> pd.DataFrame:
    labels = np.asarray(classes, dtype=str)[np.argmax(probability, axis=1)]
    signals, confidence = signals_from_probabilities(
        probability,
        classes,
        minimum_confidence=threshold,
        explicit_neutral_class=True,
    )
    result = pd.DataFrame(
        {
            "decision_timestamp": pd.to_datetime(frame["decision_timestamp"], utc=True),
            "actual_label": frame[target_column].astype(str).to_numpy(),
            "predicted_label": labels,
            "signal": signals,
            "confidence": confidence,
        }
    )
    for index, name in enumerate(classes):
        result[f"probability_{name}"] = probability[:, index]
    for name in metadata_columns:
        if name in frame and name not in result:
            result[name] = frame[name].to_numpy()
    return result


def run_experiment(config: ExperimentConfig) -> DevelopmentRunResult:
    plan = plan_experiment(config)
    run_id = str(plan["run_id"])
    run_dir = config.output_root / run_id
    state = RunStateStore(run_dir / "status.json")
    if (run_dir / "development.manifest.json").is_file():
        manifest = verify_development_run(run_dir)
        return DevelopmentRunResult(
            run_id, run_dir, Path(str(manifest["model_run_dir"])), manifest
        )
    state.start(run_id, config_hash=config.config_hash)
    try:
        trained = train_quant_model(config.training, evaluate_final_oos=False)
        dataset = load_training_dataset(config.training.dataset_dir)
        agent = QuantAgent(trained.run_dir)
        _, validation, _ = dataset.split_frames()
        probability = agent.calibration.transform(
            agent.model.predict_proba(agent.preprocessing.transform(validation))
        )
        target = validation[trained.manifest.target_column]
        predictions = _prediction_frame(
            validation,
            probability,
            agent.model.classes_,
            config.training.hold_policy.minimum_confidence,
            target_column=trained.manifest.target_column,
            metadata_columns=dataset.manifest.label_metadata_columns,
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        predictions.to_parquet(run_dir / "predictions.parquet", index=False)
        validation_metrics = trained.metrics["validation"]
        pd.DataFrame(validation_metrics["confidence_buckets"]).to_csv(
            run_dir / "confidence_buckets.csv", index=False
        )
        stability: dict[str, Any] = {
            config.evaluation.temporal_frequency: segment_predictions(
                validation,
                probability,
                agent.model.classes_,
                target_column=trained.manifest.target_column,
                segment=config.evaluation.temporal_frequency,
                minimum_confidence=config.training.hold_policy.minimum_confidence,
            ),
            "session": {},
            "regime_interface": [
                "trending",
                "ranging",
                "breakout",
                "high_volatility",
                "low_volatility",
                "news_driven",
            ],
        }
        for column in config.evaluation.session_columns:
            if column in validation.columns:
                stability["session"][column] = segment_predictions(
                    validation,
                    probability,
                    agent.model.classes_,
                    target_column=trained.manifest.target_column,
                    segment="session",
                    session_column=column,
                    minimum_confidence=config.training.hold_policy.minimum_confidence,
                )
        explanation = _read_json(trained.run_dir / "explanations.json")
        artifacts: dict[str, Any] = {
            "metrics.json": trained.metrics,
            "feature_importance.json": explanation,
            "calibration.json": calibration_diagnostics(
                target, probability, agent.model.classes_,
                minimum_confidence=config.training.hold_policy.minimum_confidence,
            ),
            "stability.json": stability,
            "model_manifest.json": trained.manifest.model_dump(mode="json")
            | {"model_id": trained.manifest.model_id},
        }
        summary = {
            "run_id": run_id,
            "status": "COMPLETE",
            "architecture": trained.manifest.architecture,
            "model_id": trained.manifest.model_id,
            "model_run_dir": str(trained.run_dir),
            "dataset_id": trained.manifest.dataset_id,
            "feature_manifest_id": trained.manifest.feature_manifest_id,
            "feature_count": len(trained.manifest.selected_features),
            "config_hash": config.config_hash,
            "final_oos_use": "NOT_ACCESSED",
            "threshold_diagnostics": threshold_diagnostics(
                probability, agent.model.classes_, config.evaluation.hold_thresholds
            ),
            "overfitting": overfitting_report(trained.metrics),
            "temporal_stability": "stability.json",
            "transaction_cost_interface": ["spread", "commission", "slippage", "swap"],
            "profitability_claim": False,
            "automatic_promotion": False,
            "real_training_scale": "TINY_TEST_ONLY"
            if len(dataset.frame) <= 5_000
            else "USER_LOCAL_RUN",
        }
        artifacts["run_summary.json"] = summary
        for name, payload in artifacts.items():
            write_json_atomic(run_dir / name, payload)
        report = (
            f"# Quant development run {run_id}\n\n"
            f"- Model: `{trained.manifest.model_id}`\n"
            f"- Architecture: `{trained.manifest.architecture}`\n"
            f"- Dataset: `{trained.manifest.dataset_id}`\n"
            "- Final OOS use: not accessed; explicit final evaluation is separate\n"
            "- Profitability claim: none; execution-aware backtesting is required later.\n"
        )
        write_text_atomic(run_dir / "report.md", report)
        names = [
            "metrics.json",
            "predictions.parquet",
            "confidence_buckets.csv",
            "feature_importance.json",
            "calibration.json",
            "stability.json",
            "run_summary.json",
            "model_manifest.json",
            "report.md",
        ]
        manifest = write_development_manifest(
            run_dir,
            {
                "schema_version": "1.0",
                "run_id": run_id,
                "config_hash": config.config_hash,
                "model_id": trained.manifest.model_id,
                "model_run_dir": str(trained.run_dir),
                "dataset_id": trained.manifest.dataset_id,
                "final_oos_use": "NOT_ACCESSED",
                "real_training_scale": summary["real_training_scale"],
            },
            names,
        )
        state.complete(
            run_id,
            config_hash=config.config_hash,
            artifacts={name: file_hash(run_dir / name) for name in names},
        )
        return DevelopmentRunResult(run_id, run_dir, trained.run_dir, manifest)
    except Exception as exc:
        state.fail(run_id, config_hash=config.config_hash, failure=f"{type(exc).__name__}: {exc}")
        raise
