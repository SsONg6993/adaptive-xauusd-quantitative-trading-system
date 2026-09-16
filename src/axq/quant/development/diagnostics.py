"""Descriptive Quant diagnostics that never select or promote a model."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

from axq.quant.calibration import ProbabilityCalibrator
from axq.quant.metrics import evaluate_predictions, signals_from_probabilities


def threshold_diagnostics(
    probabilities: np.ndarray,
    classes: np.ndarray,
    thresholds: list[float],
    *,
    explicit_neutral_class: bool = True,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for threshold in thresholds:
        signals, confidence = signals_from_probabilities(
            probabilities,
            classes,
            minimum_confidence=threshold,
            explicit_neutral_class=explicit_neutral_class,
        )
        counts = {name: int(np.sum(signals == name)) for name in ("BUY", "SELL", "HOLD")}
        rows.append(
            {
                "threshold": float(threshold),
                "rows": len(signals),
                "signal_counts": counts,
                "signal_rates": {
                    name: count / len(signals) if len(signals) else 0.0
                    for name, count in counts.items()
                },
                "actionable_coverage": float(np.mean(signals != "HOLD"))
                if len(signals)
                else 0.0,
                "mean_confidence": float(np.mean(confidence)) if len(confidence) else None,
            }
        )
    return rows


def calibration_diagnostics(
    target: pd.Series,
    probabilities: np.ndarray,
    classes: np.ndarray,
    *,
    minimum_confidence: float = 0.5,
) -> dict[str, Any]:
    metrics = evaluate_predictions(
        target,
        probabilities,
        classes,
        minimum_confidence=minimum_confidence,
        explicit_neutral_class=True,
    )
    predicted = np.asarray(classes, dtype=str)[np.argmax(probabilities, axis=1)]
    confidence = probabilities.max(axis=1)
    correct = predicted == target.astype(str).to_numpy()
    return {
        "rows": len(target),
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score"],
        "expected_calibration_error": metrics["expected_calibration_error"],
        "reliability_bins": metrics["confidence_buckets"],
        "overconfidence_rate": float(np.mean((confidence >= 0.7) & ~correct)),
    }


def compare_calibration_methods(
    validation_probabilities: np.ndarray,
    validation_target: np.ndarray,
    evaluation_probabilities: np.ndarray,
    evaluation_target: pd.Series,
    classes: np.ndarray,
    *,
    methods: list[str],
) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for method in methods:
        calibrator = ProbabilityCalibrator.fit(
            method,
            validation_probabilities,
            validation_target,
            classes,
        )
        calibrated = calibrator.transform(evaluation_probabilities)
        reports[method] = calibration_diagnostics(
            evaluation_target, calibrated, classes
        ) | {"calibrator_fit_rows": calibrator.fit_row_count}
    return {
        "fit_scope": "VALIDATION",
        "evaluation_scope": "FOLD_OOS_OR_FINAL_OOS",
        "methods": reports,
        "selected_method": None,
        "selection_requires_development_evidence": True,
    }


def segment_predictions(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    classes: np.ndarray,
    *,
    target_column: str,
    segment: Literal["month", "quarter", "year", "session"],
    session_column: str | None = None,
    minimum_confidence: float = 0.5,
) -> list[dict[str, Any]]:
    if len(frame) != len(probabilities):
        raise ValueError("Frame and probability row counts differ")
    if segment == "session":
        if session_column is None or session_column not in frame:
            raise ValueError("Session segmentation requires an available session column")
        labels = frame[session_column].astype(str)
    else:
        timestamps = pd.to_datetime(frame["decision_timestamp"], utc=True)
        frequency = {"month": "M", "quarter": "Q", "year": "Y"}[segment]
        labels = timestamps.dt.tz_localize(None).dt.to_period(frequency).astype(str)
    rows: list[dict[str, Any]] = []
    for label in sorted(labels.unique()):
        positions = np.flatnonzero(labels.to_numpy() == label)
        metrics = evaluate_predictions(
            frame[target_column].iloc[positions],
            probabilities[positions],
            classes,
            minimum_confidence=minimum_confidence,
            explicit_neutral_class=True,
        )
        rows.append({"segment": str(label), **metrics})
    return rows


def opportunity_utilization(signals: np.ndarray) -> dict[str, Any]:
    values = np.asarray(signals, dtype=str)
    valid = len(values)
    counts = {name: int(np.sum(values == name)) for name in ("BUY", "SELL", "HOLD")}
    return {
        "valid_quant_opportunities": valid,
        "signal_counts": counts,
        "actionable": counts["BUY"] + counts["SELL"],
        "actionable_coverage": (counts["BUY"] + counts["SELL"]) / valid if valid else 0.0,
        "downstream_master_risk_rejections": None,
        "scope": "QUANT_ONLY",
    }


def overfitting_report(split_metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    flags: list[str] = []
    train = split_metrics.get("train", {})
    validation = split_metrics.get("validation", {})
    train_score = train.get("balanced_accuracy")
    validation_score = validation.get("balanced_accuracy")
    if (
        isinstance(train_score, (int, float))
        and isinstance(validation_score, (int, float))
        and float(train_score) - float(validation_score) >= 0.15
    ):
        flags.append("train_validation_gap")
    coverage = validation.get("prediction_coverage")
    if isinstance(coverage, (int, float)) and float(coverage) < 0.05:
        flags.append("actionable_coverage_collapse")
    train_confidence = train.get("confidence", {}).get("mean") if train else None
    validation_confidence = (
        validation.get("confidence", {}).get("mean") if validation else None
    )
    if isinstance(train_confidence, (int, float)) and isinstance(
        validation_confidence, (int, float)
    ) and float(train_confidence) - float(validation_confidence) >= 0.15:
        flags.append("confidence_degradation")
    return {"flags": flags, "requires_review": bool(flags), "automatic_decision": None}
