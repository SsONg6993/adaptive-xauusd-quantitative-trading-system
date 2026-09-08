from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from axq.datasets import RowPolicy, SplitPolicy, assemble_dataset, write_dataset
from axq.labels import LabelDefinition, LabelKind
from axq.quant.calibration import ProbabilityCalibrator
from axq.quant.config import (
    Architecture,
    CalibrationConfig,
    FeatureSelectionConfig,
    HoldPolicyConfig,
    PreprocessingConfig,
    QuantTrainingConfig,
)
from axq.quant.dataset import load_training_dataset
from axq.quant.evaluation import evaluate_saved_run
from axq.quant.inference import QuantAgent
from axq.quant.metrics import evaluate_predictions, signals_from_probabilities
from axq.quant.models import MajorityClassifier
from axq.quant.preprocessing import FrozenPreprocessor
from axq.quant.registry import LocalModelRegistry, ModelState
from axq.quant.trainer import train_quant_model


def candles(rows: int = 110) -> pd.DataFrame:
    x = np.arange(rows, dtype=float)
    close = 2000.0 + np.sin(x / 2.3) * 2.0 + x * 0.02
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-05", periods=rows, freq="5min", tz="UTC"),
            "open": close - np.cos(x) * 0.1,
            "high": close + 0.4,
            "low": close - 0.4,
            "close": close,
            "tick_volume": 100 + x % 13,
            "spread": 20,
        }
    )


def dataset_dir(tmp_path: Path) -> Path:
    result = assemble_dataset(
        {"M5": candles()},
        dataset_name="phase4-tiny",
        symbol="XAUUSD",
        base_timeframe="M5",
        feature_set_version="phase4-test-v1",
        feature_groups=["price_action", "volatility"],
        feature_parameters={"volatility_v2": {"atr_period": 2, "rolling_period": 3}},
        label_definition=LabelDefinition(
            name="next_3", version="direction-3-test", kind=LabelKind.DIRECTION,
            horizon_bars=3, neutral_threshold=0.0002,
        ),
        row_policy=RowPolicy(
            critical_feature_columns=["pa_body", "pa_range", "vol_atr_2"]
        ),
        split_policy=SplitPolicy(purge_bars=3),
        storage_format="parquet",
        git_commit="test-git-identity",
    )
    return write_dataset(result, tmp_path / "datasets")


def config(data: Path, output: Path, *, calibration: str = "none") -> QuantTrainingConfig:
    return QuantTrainingConfig(
        architecture=Architecture.LOGISTIC,
        dataset_dir=data,
        output_root=output,
        preprocessing=PreprocessingConfig(imputation="median", scaler="standard"),
        feature_selection=FeatureSelectionConfig(variance_threshold=0.0),
        model_hyperparameters={"C": 0.5},
        calibration=CalibrationConfig(method=calibration),
        hold_policy=HoldPolicyConfig(minimum_confidence=0.55),
    )


def test_dataset_manifest_compatibility_and_exact_feature_order(tmp_path: Path) -> None:
    root = dataset_dir(tmp_path)
    loaded = load_training_dataset(root)
    assert list(loaded.frame.columns)[2 : 2 + len(loaded.manifest.feature_columns)] == (
        loaded.manifest.feature_columns
    )
    payload = json.loads((root / "feature.manifest.json").read_text())
    payload["entries"][0]["implementation_version"] = "tampered"
    (root / "feature.manifest.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="Corrupt manifest_id"):
        load_training_dataset(root)


def test_training_only_preprocessing_and_nan_inf_policy() -> None:
    train = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [2.0, 2.0, 2.0]})
    processor = FrozenPreprocessor.fit(
        train,
        ["a", "b"],
        PreprocessingConfig(imputation="median", scaler="standard"),
        FeatureSelectionConfig(variance_threshold=0.0),
    )
    assert processor.fit_row_count == 3
    assert processor.medians is not None and processor.medians["a"] == 2.0
    assert processor.selected_features == ["a"]
    with pytest.raises(ValueError, match="Infinite"):
        processor.transform(pd.DataFrame({"a": [np.inf], "b": [2.0]}))
    with pytest.raises(ValueError, match="Missing required"):
        processor.transform(pd.DataFrame({"a": [1.0]}))


def test_majority_and_prior_baselines() -> None:
    target = np.asarray([0, 0, 0, 1])
    x = np.zeros((4, 1))
    majority = MajorityClassifier().fit(x, target)
    prior = MajorityClassifier(use_priors=True).fit(x, target)
    assert majority.predict_proba(x[:1]).tolist() == [[1.0, 0.0]]
    assert prior.predict_proba(x[:1]).tolist() == [[0.75, 0.25]]


def test_hold_threshold_and_explicit_neutral_class() -> None:
    classes = np.asarray(["DOWN", "NEUTRAL", "UP"])
    probabilities = np.asarray([[0.45, 0.10, 0.45], [0.1, 0.7, 0.2]])
    signals, confidence = signals_from_probabilities(
        probabilities, classes, minimum_confidence=0.6, explicit_neutral_class=True
    )
    assert signals.tolist() == ["HOLD", "HOLD"]
    assert confidence.tolist() == pytest.approx([0.45, 0.7])


@pytest.mark.parametrize("method", ["sigmoid", "isotonic"])
def test_calibration_pipeline(method: str) -> None:
    classes = np.asarray(["DOWN", "NEUTRAL", "UP"])
    probabilities = np.asarray(
        [[0.8, 0.1, 0.1], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]] * 3
    )
    target = np.asarray(["DOWN", "NEUTRAL", "UP"] * 3)
    calibrated = ProbabilityCalibrator.fit(
        method, probabilities, target, classes
    ).transform(probabilities)
    assert calibrated.shape == probabilities.shape
    np.testing.assert_allclose(calibrated.sum(axis=1), 1.0)


def test_logistic_tiny_fit_serialization_inference_and_oos_scope(tmp_path: Path) -> None:
    data = dataset_dir(tmp_path)
    result = train_quant_model(config(data, tmp_path / "models", calibration="sigmoid"))
    assert result.manifest.class_mapping == {
        "DOWN": "SELL", "NEUTRAL": "HOLD", "UP": "BUY"
    }
    assert set(result.metrics) == {"train", "validation", "oos"}
    summary = json.loads((result.run_dir / "run_summary.json").read_text())
    loaded = load_training_dataset(data)
    train, validation, _ = loaded.split_frames()
    assert summary["fit_scopes"]["model"] == "TRAIN"
    assert summary["fit_scopes"]["calibration"] == "VALIDATION"
    assert summary["fit_rows"]["model"] == len(train)
    assert summary["fit_rows"]["calibration"] == len(validation)
    agent = QuantAgent(result.run_dir)
    row = loaded.frame.iloc[-1]
    before = agent.predict_probabilities(row)
    reloaded = QuantAgent(result.run_dir)
    np.testing.assert_allclose(before, reloaded.predict_probabilities(row))
    prediction = reloaded.predict(
        row,
        symbol="XAUUSD",
        timeframe="M5",
        timestamp=datetime(2026, 1, 6, tzinfo=UTC),
        data_freshness_ms=100,
        feature_manifest_id=loaded.manifest.feature_manifest_id,
        dataset_id=loaded.manifest.dataset_id,
    )
    assert prediction.signal.value in {"BUY", "SELL", "HOLD"}
    assert prediction.dataset_id == loaded.manifest.dataset_id
    assert prediction.label_manifest_id == loaded.manifest.label_manifest_id
    with pytest.raises(ValueError, match="Feature manifest"):
        reloaded.predict(
            row,
            symbol="XAUUSD",
            timeframe="M5",
            timestamp=datetime.now(UTC),
            data_freshness_ms=1,
            feature_manifest_id="wrong",
        )
    missing = row.drop(loaded.manifest.feature_columns[0])
    with pytest.raises(ValueError, match="Missing required"):
        reloaded.predict_probabilities(missing)
    reproduced = train_quant_model(config(data, tmp_path / "models", calibration="sigmoid"))
    assert reproduced.manifest.model_id == result.manifest.model_id
    replayed = evaluate_saved_run(str(result.run_dir), str(data))
    assert replayed["confusion_matrix"] == result.metrics["oos"]["confusion_matrix"]


def test_model_registry_requires_explicit_promotion_evidence(tmp_path: Path) -> None:
    registry = LocalModelRegistry(tmp_path / "registry.json")
    assert registry.register("m1", "runs/m1").state is ModelState.CANDIDATE
    assert registry.transition("m1", ModelState.CHALLENGER).state is ModelState.CHALLENGER
    with pytest.raises(ValueError, match="evidence"):
        registry.transition("m1", ModelState.CHAMPION)
    promoted = registry.transition(
        "m1", ModelState.CHAMPION, evidence={"reviewed": True, "metrics": ["oos", "ece"]}
    )
    assert promoted.state is ModelState.CHAMPION


def test_confidence_bucket_and_frequency_diagnostics() -> None:
    target = pd.Series(["DOWN", "UP", "UP"])
    classes = np.asarray(["DOWN", "UP"])
    probabilities = np.asarray([[0.8, 0.2], [0.48, 0.52], [0.1, 0.9]])
    report = evaluate_predictions(
        target,
        probabilities,
        classes,
        minimum_confidence=0.55,
        explicit_neutral_class=True,
    )
    assert report["prediction_distribution"]["HOLD"] == pytest.approx(1 / 3)
    assert report["opportunity_utilization"] == pytest.approx(2 / 3)
    assert report["confidence_buckets"]
