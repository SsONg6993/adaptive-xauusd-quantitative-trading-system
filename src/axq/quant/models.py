"""Simple baselines and lazy optional model adapters."""

from __future__ import annotations

from typing import Any, Protocol, cast

import numpy as np
from sklearn.ensemble import RandomForestClassifier  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]

from axq.quant.config import Architecture, QuantTrainingConfig


class ProbabilisticClassifier(Protocol):
    classes_: np.ndarray

    def fit(self, values: np.ndarray, target: np.ndarray) -> Any: ...
    def predict_proba(self, values: np.ndarray) -> np.ndarray: ...


class MajorityClassifier:
    def __init__(self, *, use_priors: bool = False) -> None:
        self.use_priors = use_priors
        self.classes_ = np.asarray([], dtype=object)
        self.probabilities_ = np.asarray([], dtype=float)

    def fit(self, values: np.ndarray, target: np.ndarray) -> MajorityClassifier:
        del values
        classes, counts = np.unique(target, return_counts=True)
        if len(classes) == 0:
            raise ValueError("Cannot fit a baseline without targets")
        self.classes_ = classes
        if self.use_priors:
            self.probabilities_ = counts / counts.sum()
        else:
            self.probabilities_ = np.zeros(len(classes), dtype=float)
            self.probabilities_[int(np.argmax(counts))] = 1.0
        return self

    def predict_proba(self, values: np.ndarray) -> np.ndarray:
        if not len(self.classes_):
            raise RuntimeError("Baseline is not fitted")
        return np.tile(self.probabilities_, (len(values), 1))


def build_model(
    config: QuantTrainingConfig, *, selected_device: str = "cpu"
) -> ProbabilisticClassifier:
    params = dict(config.model_hyperparameters)
    weight = "balanced" if config.class_weighting == "balanced" else None
    if config.architecture is Architecture.MAJORITY:
        return MajorityClassifier()
    if config.architecture is Architecture.PRIOR:
        return MajorityClassifier(use_priors=True)
    if config.architecture is Architecture.LOGISTIC:
        params.setdefault("max_iter", 300)
        return cast(ProbabilisticClassifier, LogisticRegression(
            random_state=config.random_seed,
            class_weight=weight,
            **params,
        ))
    if config.architecture is Architecture.RANDOM_FOREST:
        params.setdefault("n_estimators", 100)
        params.setdefault("n_jobs", 1)
        return cast(ProbabilisticClassifier, RandomForestClassifier(
            random_state=config.random_seed,
            class_weight=weight,
            **params,
        ))
    if config.architecture is Architecture.XGBOOST:
        try:
            from xgboost import XGBClassifier  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install the optional xgboost dependency") from exc
        return cast(ProbabilisticClassifier, XGBClassifier(
            random_state=config.random_seed,
            device=selected_device,
            **params,
        ))
    if config.architecture is Architecture.LIGHTGBM:
        try:
            from lightgbm import LGBMClassifier  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install the optional lightgbm dependency") from exc
        device_type = "gpu" if selected_device == "cuda" else "cpu"
        return cast(ProbabilisticClassifier, LGBMClassifier(
            random_state=config.random_seed,
            class_weight=weight,
            device_type=device_type,
            **params,
        ))
    raise ValueError(f"Unsupported architecture: {config.architecture}")
