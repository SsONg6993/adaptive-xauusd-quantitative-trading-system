"""Classification, calibration, trading-context, and coverage diagnostics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (  # type: ignore[import-untyped]
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize  # type: ignore[import-untyped]


def label_to_signal(label: str) -> str:
    normalized = label.upper()
    return {"UP": "BUY", "DOWN": "SELL", "NEUTRAL": "HOLD"}.get(
        normalized, normalized
    )


def signals_from_probabilities(
    probabilities: np.ndarray,
    classes: np.ndarray,
    *,
    minimum_confidence: float,
    explicit_neutral_class: bool,
) -> tuple[np.ndarray, np.ndarray]:
    indices = np.argmax(probabilities, axis=1)
    confidence = probabilities[np.arange(len(probabilities)), indices]
    labels = np.asarray(classes, dtype=str)[indices]
    signals = np.asarray([label_to_signal(label) for label in labels], dtype=object)
    if explicit_neutral_class:
        signals[np.char.upper(labels) == "NEUTRAL"] = "HOLD"
    signals[confidence < minimum_confidence] = "HOLD"
    return signals, confidence


def _confidence_bucket(value: float) -> str:
    if value < 0.55:
        return "0.50-0.55" if value >= 0.50 else "below-0.50"
    if value < 0.60:
        return "0.55-0.60"
    if value < 0.65:
        return "0.60-0.65"
    if value < 0.70:
        return "0.65-0.70"
    return "0.70+"


def evaluate_predictions(
    target: pd.Series,
    probabilities: np.ndarray,
    classes: np.ndarray,
    *,
    minimum_confidence: float,
    explicit_neutral_class: bool,
    metadata: pd.DataFrame | None = None,
) -> dict[str, Any]:
    y_true = target.astype(str).to_numpy()
    predicted_labels = np.asarray(classes, dtype=str)[np.argmax(probabilities, axis=1)]
    signals, confidence = signals_from_probabilities(
        probabilities,
        classes,
        minimum_confidence=minimum_confidence,
        explicit_neutral_class=explicit_neutral_class,
    )
    labels = [str(value) for value in classes]
    report: dict[str, Any] = {
        "row_count": len(y_true),
        "accuracy": float(accuracy_score(y_true, predicted_labels)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predicted_labels)),
        "precision_macro": float(
            precision_score(
                y_true,
                predicted_labels,
                labels=labels,
                average="macro",
                zero_division=0,
            )
        ),
        "recall_macro": float(
            recall_score(y_true, predicted_labels, labels=labels, average="macro", zero_division=0)
        ),
        "f1_macro": float(
            f1_score(y_true, predicted_labels, labels=labels, average="macro", zero_division=0)
        ),
        "confusion_matrix": confusion_matrix(y_true, predicted_labels, labels=labels).tolist(),
        "class_order": labels,
        "log_loss": float(log_loss(y_true, probabilities, labels=labels)),
        "class_distribution": pd.Series(y_true).value_counts(normalize=True).sort_index().to_dict(),
        "prediction_distribution": (
            pd.Series(signals).value_counts(normalize=True).sort_index().to_dict()
        ),
        "confidence": {
            "mean": float(np.mean(confidence)),
            "median": float(np.median(confidence)),
            "min": float(np.min(confidence)),
            "max": float(np.max(confidence)),
        },
        "confidence_buckets": {},
        "prediction_coverage": float(np.mean(signals != "HOLD")),
        "opportunity_utilization": float(np.mean(signals != "HOLD")),
    }
    one_hot = label_binarize(y_true, classes=classes)
    if len(classes) == 2:
        one_hot = np.column_stack([1 - one_hot.ravel(), one_hot.ravel()])
    report["brier_score"] = float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1)))
    if set(y_true) == set(labels):
        try:
            report["roc_auc_ovr_macro"] = float(
                roc_auc_score(one_hot, probabilities, average="macro", multi_class="ovr")
            )
            report["pr_auc_macro"] = float(
                average_precision_score(one_hot, probabilities, average="macro")
            )
        except ValueError:
            report["roc_auc_ovr_macro"] = None
            report["pr_auc_macro"] = None
    else:
        report["roc_auc_ovr_macro"] = None
        report["pr_auc_macro"] = None
    correctness = (predicted_labels == y_true).astype(float)
    expected_calibration_error = 0.0
    bucket_rows: list[dict[str, Any]] = []
    bucket_names = [_confidence_bucket(float(value)) for value in confidence]
    for bucket in ["below-0.50", "0.50-0.55", "0.55-0.60", "0.60-0.65", "0.65-0.70", "0.70+"]:
        mask = np.asarray([name == bucket for name in bucket_names])
        if not mask.any():
            continue
        mean_confidence = float(confidence[mask].mean())
        bucket_accuracy = float(correctness[mask].mean())
        row: dict[str, Any] = {
            "bucket": bucket,
            "rows": int(mask.sum()),
            "mean_confidence": mean_confidence,
            "accuracy": bucket_accuracy,
            "actionable_rate": float(np.mean(signals[mask] != "HOLD")),
        }
        expected_calibration_error += (mask.sum() / len(mask)) * abs(
            mean_confidence - bucket_accuracy
        )
        if metadata is not None:
            for column in metadata.columns:
                lowered = column.lower()
                if any(token in lowered for token in ("forward", "mfe", "mae")):
                    numeric = pd.to_numeric(
                        metadata[column].iloc[np.flatnonzero(mask)], errors="coerce"
                    ).dropna()
                    row[f"mean_{column}"] = (
                        float(numeric.mean()) if not numeric.empty else None
                    )
                    row[f"median_{column}"] = (
                        float(numeric.median()) if not numeric.empty else None
                    )
        bucket_rows.append(row)
    report["confidence_buckets"] = bucket_rows
    report["expected_calibration_error"] = float(expected_calibration_error)
    trading: dict[str, Any] = {}
    if metadata is not None:
        for predicted_class in labels:
            class_mask = predicted_labels == predicted_class
            if not class_mask.any():
                continue
            class_report: dict[str, Any] = {"rows": int(class_mask.sum())}
            for column in metadata.columns:
                lowered = column.lower()
                if any(token in lowered for token in ("forward", "mfe", "mae")):
                    numeric = pd.to_numeric(
                        metadata[column].iloc[np.flatnonzero(class_mask)], errors="coerce"
                    ).dropna()
                    class_report[f"mean_{column}"] = (
                        float(numeric.mean()) if not numeric.empty else None
                    )
                    class_report[f"median_{column}"] = (
                        float(numeric.median()) if not numeric.empty else None
                    )
            trading[predicted_class] = class_report
    report["trading_diagnostics_by_predicted_class"] = trading
    return report
