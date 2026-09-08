"""Distribution-drift interfaces without autonomous retraining."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _finite(values: np.ndarray | pd.Series) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return array[np.isfinite(array)]


def psi(reference: np.ndarray, current: np.ndarray, *, bins: int = 10) -> float:
    reference_values = _finite(reference)
    current_values = _finite(current)
    if not len(reference_values) or not len(current_values) or bins < 2:
        raise ValueError("PSI requires non-empty finite samples and at least two bins")
    minimum = float(reference_values.min())
    maximum = float(reference_values.max())
    if minimum == maximum:
        return 0.0 if np.all(current_values == minimum) else float("inf")
    edges = np.linspace(minimum, maximum, bins + 1)
    edges[0], edges[-1] = -np.inf, np.inf
    reference_counts = np.histogram(reference_values, bins=edges)[0] / len(reference_values)
    current_counts = np.histogram(current_values, bins=edges)[0] / len(current_values)
    epsilon = 1e-6
    reference_safe = np.clip(reference_counts, epsilon, None)
    current_safe = np.clip(current_counts, epsilon, None)
    return float(np.sum((current_safe - reference_safe) * np.log(current_safe / reference_safe)))


def ks_statistic(reference: np.ndarray, current: np.ndarray) -> float:
    left = np.sort(_finite(reference))
    right = np.sort(_finite(current))
    if not len(left) or not len(right):
        raise ValueError("KS statistic requires non-empty finite samples")
    points = np.sort(np.unique(np.concatenate([left, right])))
    left_cdf = np.searchsorted(left, points, side="right") / len(left)
    right_cdf = np.searchsorted(right, points, side="right") / len(right)
    return float(np.max(np.abs(left_cdf - right_cdf)))


def distribution_drift(
    reference: np.ndarray, current: np.ndarray, *, bins: int = 10
) -> dict[str, float]:
    return {
        "psi": psi(reference, current, bins=bins),
        "ks_statistic": ks_statistic(reference, current),
    }


def feature_drift_report(
    reference: pd.DataFrame, current: pd.DataFrame, *, bins: int = 10
) -> dict[str, Any]:
    common = sorted(
        set(reference.select_dtypes(include="number").columns)
        & set(current.select_dtypes(include="number").columns)
    )
    return {
        "features": {
            name: distribution_drift(
                reference[name].to_numpy(), current[name].to_numpy(), bins=bins
            )
            for name in common
        },
        "autonomous_retraining": False,
    }


def _categorical_distribution(values: np.ndarray) -> dict[str, float]:
    series = pd.Series(np.asarray(values, dtype=str))
    return {str(key): float(value) for key, value in series.value_counts(normalize=True).items()}


def quant_drift_report(
    reference_features: pd.DataFrame,
    current_features: pd.DataFrame,
    *,
    reference_signals: np.ndarray,
    current_signals: np.ndarray,
    reference_confidence: np.ndarray,
    current_confidence: np.ndarray,
    reference_metrics: dict[str, Any],
    current_metrics: dict[str, Any],
) -> dict[str, Any]:
    reference_distribution = _categorical_distribution(reference_signals)
    current_distribution = _categorical_distribution(current_signals)
    names = sorted(set(reference_distribution) | set(current_distribution))
    total_variation = 0.5 * sum(
        abs(reference_distribution.get(name, 0.0) - current_distribution.get(name, 0.0))
        for name in names
    )
    reference_actionable = float(np.mean(np.asarray(reference_signals) != "HOLD"))
    current_actionable = float(np.mean(np.asarray(current_signals) != "HOLD"))
    reference_calibration = reference_metrics.get("expected_calibration_error")
    current_calibration = current_metrics.get("expected_calibration_error")
    reference_performance = reference_metrics.get("balanced_accuracy")
    current_performance = current_metrics.get("balanced_accuracy")
    return {
        "feature_drift": feature_drift_report(reference_features, current_features),
        "prediction_distribution_drift": {
            "reference": reference_distribution,
            "current": current_distribution,
            "total_variation": float(total_variation),
        },
        "confidence_drift": distribution_drift(
            reference_confidence, current_confidence
        ),
        "calibration_drift": {
            "reference": reference_calibration,
            "current": current_calibration,
            "delta": float(current_calibration - reference_calibration)
            if isinstance(reference_calibration, (int, float))
            and isinstance(current_calibration, (int, float))
            else None,
        },
        "performance_drift": {
            "reference": reference_performance,
            "current": current_performance,
            "delta": float(current_performance - reference_performance)
            if isinstance(reference_performance, (int, float))
            and isinstance(current_performance, (int, float))
            else None,
        },
        "actionable_coverage_drift": {
            "reference": reference_actionable,
            "current": current_actionable,
            "delta": current_actionable - reference_actionable,
        },
        "autonomous_retraining": False,
    }
