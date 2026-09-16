from __future__ import annotations

import numpy as np
import pandas as pd

from axq.quant.development.challenger import evaluate_challenger_evidence
from axq.quant.development.diagnostics import (
    compare_calibration_methods,
    overfitting_report,
    segment_predictions,
    threshold_diagnostics,
)
from axq.quant.development.drift import (
    distribution_drift,
    ks_statistic,
    psi,
    quant_drift_report,
)


def test_threshold_diagnostics_reports_frequency_without_selecting_threshold() -> None:
    probabilities = np.asarray([[0.8, 0.2], [0.55, 0.45], [0.3, 0.7]])
    classes = np.asarray(["DOWN", "UP"])

    rows = threshold_diagnostics(probabilities, classes, [0.5, 0.6])

    assert rows[0]["signal_counts"] == {"BUY": 1, "SELL": 2, "HOLD": 0}
    assert rows[0]["actionable_coverage"] == 1.0
    assert rows[1]["signal_counts"] == {"BUY": 1, "SELL": 1, "HOLD": 1}
    assert rows[1]["actionable_coverage"] == 2 / 3
    assert all("selected" not in row for row in rows)


def test_temporal_and_session_segmentation_evaluates_each_observed_group() -> None:
    frame = pd.DataFrame(
        {
            "decision_timestamp": pd.to_datetime(
                [
                    "2026-01-01T00:00:00Z",
                    "2026-01-02T00:00:00Z",
                    "2026-02-01T00:00:00Z",
                    "2026-02-02T00:00:00Z",
                ],
                utc=True,
            ),
            "target": ["DOWN", "UP", "UP", "DOWN"],
            "session": ["Asia", "London", "Asia", "London"],
        }
    )
    probabilities = np.asarray(
        [[0.8, 0.2], [0.2, 0.8], [0.1, 0.9], [0.7, 0.3]]
    )

    monthly = segment_predictions(
        frame,
        probabilities,
        np.asarray(["DOWN", "UP"]),
        target_column="target",
        segment="month",
    )
    sessions = segment_predictions(
        frame,
        probabilities,
        np.asarray(["DOWN", "UP"]),
        target_column="target",
        segment="session",
        session_column="session",
    )

    assert [row["segment"] for row in monthly] == ["2026-01", "2026-02"]
    assert {row["segment"] for row in sessions} == {"Asia", "London"}
    assert all(row["accuracy"] == 1.0 for row in monthly + sessions)


def test_drift_metrics_are_zero_for_identical_samples_and_flag_shift() -> None:
    reference = np.asarray([0.0, 0.0, 1.0, 1.0])
    shifted = np.asarray([10.0, 10.0, 11.0, 11.0])

    assert psi(reference, reference, bins=2) == 0.0
    assert ks_statistic(reference, reference) == 0.0
    report = distribution_drift(reference, shifted, bins=2)
    assert report["ks_statistic"] == 1.0
    assert report["psi"] > 0.0


def test_overfitting_and_challenger_contract_are_advisory() -> None:
    flags = overfitting_report(
        {
            "train": {"balanced_accuracy": 0.95, "prediction_coverage": 0.9},
            "validation": {"balanced_accuracy": 0.51, "prediction_coverage": 0.01},
        }
    )
    evidence = evaluate_challenger_evidence(
        {
            "sample_size": 100,
            "walk_forward_folds": 1,
            "beats_simple_baseline": False,
            "calibration_acceptable": True,
            "temporally_stable": False,
            "frequency_collapse": True,
            "reproducible": True,
        },
        minimum_sample_size=1000,
        minimum_folds=3,
    )

    assert "train_validation_gap" in flags["flags"]
    assert "actionable_coverage_collapse" in flags["flags"]
    assert evidence["eligible_for_review"] is False
    assert "minimum_sample_size" in evidence["unmet_requirements"]
    assert evidence["registry_transition_performed"] is False


def test_calibration_comparison_fits_validation_and_only_evaluates_next_slice() -> None:
    classes = np.asarray(["DOWN", "UP"])
    validation_probability = np.asarray(
        [[0.8, 0.2], [0.2, 0.8], [0.7, 0.3], [0.3, 0.7]]
    )
    evaluation_probability = np.asarray([[0.6, 0.4], [0.4, 0.6]])

    report = compare_calibration_methods(
        validation_probability,
        np.asarray(["DOWN", "UP", "DOWN", "UP"]),
        evaluation_probability,
        pd.Series(["DOWN", "UP"]),
        classes,
        methods=["none", "sigmoid"],
    )

    assert report["fit_scope"] == "VALIDATION"
    assert report["evaluation_scope"] == "FOLD_OOS_OR_FINAL_OOS"
    assert report["selected_method"] is None
    assert report["methods"]["sigmoid"]["calibrator_fit_rows"] == 4


def test_quant_drift_report_covers_all_monitoring_interfaces() -> None:
    reference = pd.DataFrame({"f": [0.0, 0.0, 1.0, 1.0]})
    current = pd.DataFrame({"f": [1.0, 1.0, 2.0, 2.0]})

    report = quant_drift_report(
        reference,
        current,
        reference_signals=np.asarray(["BUY", "SELL", "HOLD", "BUY"]),
        current_signals=np.asarray(["HOLD", "HOLD", "HOLD", "BUY"]),
        reference_confidence=np.asarray([0.6, 0.6, 0.5, 0.7]),
        current_confidence=np.asarray([0.5, 0.5, 0.5, 0.6]),
        reference_metrics={"balanced_accuracy": 0.6, "expected_calibration_error": 0.1},
        current_metrics={"balanced_accuracy": 0.5, "expected_calibration_error": 0.2},
    )

    assert set(report) >= {
        "feature_drift",
        "prediction_distribution_drift",
        "confidence_drift",
        "calibration_drift",
        "performance_drift",
        "actionable_coverage_drift",
    }
    assert report["autonomous_retraining"] is False
