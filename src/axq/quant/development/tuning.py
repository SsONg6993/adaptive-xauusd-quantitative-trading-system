"""Optuna execution support constrained to pre-final-OOS development folds."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import numpy as np

from axq.datasets.splits import SplitManifest
from axq.quant.dataset import TrainingDataset
from axq.quant.development.artifacts import write_json_atomic
from axq.quant.development.config import ExperimentConfig, TuningConfig
from axq.quant.development.folds import run_development_fold


def tuning_plan(
    config: TuningConfig, *, dataset_id: str, development_split_id: str
) -> dict[str, Any]:
    return {
        **config.model_dump(mode="json"),
        "dataset_id": dataset_id,
        "development_split_id": development_split_id,
        "allowed_selection_scopes": ["train", "validation", "walk_forward_validation"],
        "immutable_final_oos_access": False,
        "automatic_final_model_choice": False,
        "status": "PREPARED_NOT_STARTED",
    }


def _parameters(trial: Any, architecture: str) -> dict[str, Any]:
    if architecture == "random_forest":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 100, 800, step=100),
            "max_depth": trial.suggest_int("max_depth", 4, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 2, 30),
            "n_jobs": -1,
        }
    if architecture == "xgboost":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 200, 1000, step=100),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "tree_method": "hist",
            "n_jobs": -1,
        }
    if architecture == "lightgbm":
        return {
            "n_estimators": trial.suggest_int("n_estimators", 200, 1000, step=100),
            "num_leaves": trial.suggest_int("num_leaves", 15, 127),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.15, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "n_jobs": -1,
            "verbosity": -1,
        }
    raise ValueError(f"Unsupported tuning architecture: {architecture}")


def run_optuna_study(
    tuning: TuningConfig,
    experiment: ExperimentConfig,
    dataset: TrainingDataset,
    development_splits: SplitManifest,
    *,
    output_dir: str | Path,
) -> dict[str, Any]:
    final_oos_start = development_splits.policy.get("immutable_final_oos_start")
    if not isinstance(final_oos_start, int) or any(
        fold.oos.stop > final_oos_start for fold in development_splits.folds
    ):
        raise ValueError("Tuning split overlaps or lacks immutable final OOS boundary")
    if tuning.architecture is not experiment.training.architecture:
        raise ValueError("Tuning and experiment architectures differ")
    optuna = importlib.import_module("optuna")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    target = experiment.training.target_column or dataset.manifest.target_columns[0]

    def objective(trial: Any) -> float:
        trial_config = experiment.training.model_copy(
            update={"model_hyperparameters": _parameters(trial, tuning.architecture.value)}
        )
        values = []
        for fold in development_splits.folds:
            result = run_development_fold(
                dataset.frame,
                fold,
                features=dataset.manifest.feature_columns,
                target_column=target,
                config=trial_config,
                metadata_columns=dataset.manifest.label_metadata_columns,
            )
            values.append(float(result.metrics["fold_oos"][tuning.metric]))
        return float(np.mean(values))

    study = optuna.create_study(
        study_name=f"quant-{tuning.architecture.value}-{dataset.manifest.dataset_id}",
        direction=tuning.direction,
        storage=f"sqlite:///{(root / 'study.sqlite3').as_posix()}",
        load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=tuning.random_seed),
    )
    study.optimize(objective, n_trials=tuning.n_trials)
    report = tuning_plan(
        tuning,
        dataset_id=dataset.manifest.dataset_id,
        development_split_id=development_splits.manifest_id,
    ) | {
        "status": "COMPLETE",
        "best_value": float(study.best_value),
        "best_parameters": dict(study.best_params),
        "completed_trials": len(study.trials),
        "final_oos_evaluated": False,
    }
    write_json_atomic(root / "tuning_summary.json", report)
    return report
