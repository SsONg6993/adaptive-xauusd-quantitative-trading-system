from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from axq.datasets import RowPolicy, SplitPolicy, assemble_dataset, write_dataset
from axq.labels import LabelDefinition, LabelKind
from axq.quant.development.artifacts import verify_development_run
from axq.quant.development.comparison import compare_runs
from axq.quant.development.config import ExperimentConfig
from axq.quant.development.runner import plan_experiment, run_experiment


def tiny_dataset(tmp_path: Path) -> Path:
    x = np.arange(110, dtype=float)
    close = 2000.0 + np.sin(x / 2.3) * 2.0 + x * 0.02
    candles = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-05", periods=110, freq="5min", tz="UTC"),
            "open": close - np.cos(x) * 0.1,
            "high": close + 0.4,
            "low": close - 0.4,
            "close": close,
            "tick_volume": 100 + x % 13,
            "spread": 20,
        }
    )
    result = assemble_dataset(
        {"M5": candles},
        dataset_name="phase5-tiny",
        symbol="XAUUSD",
        base_timeframe="M5",
        feature_set_version="phase5-test-v1",
        feature_groups=["price_action", "volatility"],
        feature_parameters={"volatility_v2": {"atr_period": 2, "rolling_period": 3}},
        label_definition=LabelDefinition(
            name="next_3",
            version="direction-3-test",
            kind=LabelKind.DIRECTION,
            horizon_bars=3,
            neutral_threshold=0.0002,
        ),
        row_policy=RowPolicy(
            critical_feature_columns=["pa_body", "pa_range", "vol_atr_2"]
        ),
        split_policy=SplitPolicy(purge_bars=3),
        storage_format="parquet",
        git_commit="test-git-identity",
    )
    return write_dataset(result, tmp_path / "datasets")


def experiment(tmp_path: Path, dataset: Path) -> ExperimentConfig:
    return ExperimentConfig.model_validate(
        {
            "name": "logistic-tiny",
            "output_root": tmp_path / "experiments",
            "training": {
                "architecture": "logistic_regression",
                "dataset_dir": dataset,
                "output_root": tmp_path / "models",
                "feature_selection": {"variance_threshold": 0.0},
                "model_hyperparameters": {"C": 0.5},
                "calibration": {"method": "sigmoid"},
                "hold_policy": {"minimum_confidence": 0.55},
            },
            "evaluation": {"hold_thresholds": [0.5, 0.6]},
        }
    )


def test_dry_run_validates_dataset_without_creating_or_fitting(tmp_path: Path) -> None:
    config = experiment(tmp_path, tiny_dataset(tmp_path))

    plan = plan_experiment(config)

    assert plan["status"] == "DRY_RUN"
    assert plan["final_oos_use"] == "EVALUATION_ONLY"
    assert plan["fit_performed"] is False
    assert not config.output_root.exists()
    assert not config.training.output_root.exists()


def test_tiny_run_writes_required_verified_artifacts(tmp_path: Path) -> None:
    config = experiment(tmp_path, tiny_dataset(tmp_path))

    result = run_experiment(config)
    verified = verify_development_run(result.run_dir)

    expected = {
        "metrics.json",
        "predictions.parquet",
        "confidence_buckets.csv",
        "feature_importance.json",
        "calibration.json",
        "stability.json",
        "run_summary.json",
        "model_manifest.json",
        "report.md",
    }
    assert expected <= {path.name for path in result.run_dir.iterdir()}
    assert verified["run_id"] == result.run_id
    assert verified["final_oos_use"] == "EVALUATION_ONLY"
    assert verified["real_training_scale"] == "TINY_TEST_ONLY"
    predictions = pd.read_parquet(result.run_dir / "predictions.parquet")
    assert any(
        token in column.lower()
        for column in predictions.columns
        for token in ("forward", "mfe", "mae", "bars_to", "outcome")
    )

    metrics_path = result.run_dir / "metrics.json"
    metrics_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        verify_development_run(result.run_dir)


def test_compare_runs_uses_multiple_evidence_dimensions(tmp_path: Path) -> None:
    runs: list[Path] = []
    for name, score, coverage in [("run-a", 0.55, 0.6), ("run-b", 0.58, 0.2)]:
        root = tmp_path / name
        root.mkdir()
        (root / "run_summary.json").write_text(
            json.dumps(
                {
                    "run_id": name,
                    "architecture": "logistic_regression",
                    "model_id": f"model-{name}",
                    "dataset_id": "ds-1",
                    "feature_count": 10,
                    "final_oos_use": "EVALUATION_ONLY",
                }
            ),
            encoding="utf-8",
        )
        (root / "metrics.json").write_text(
            json.dumps(
                {
                    "oos": {
                        "balanced_accuracy": score,
                        "log_loss": 0.8,
                        "brier_score": 0.4,
                        "prediction_coverage": coverage,
                    }
                }
            ),
            encoding="utf-8",
        )
        runs.append(root)

    comparison = compare_runs(runs, verify=False)

    assert [row["run_id"] for row in comparison["runs"]] == ["run-a", "run-b"]
    assert comparison["ranking"] is None
    assert comparison["accuracy_only_ranking_forbidden"] is True
