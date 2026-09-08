"""Frozen, manifest-bound Quant Agent inference."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import numpy as np
import pandas as pd

from axq.quant.artifacts import load_artifact, verify_run
from axq.quant.calibration import ProbabilityCalibrator
from axq.quant.manifest import ModelManifest
from axq.quant.metrics import signals_from_probabilities
from axq.quant.preprocessing import FrozenPreprocessor
from axq.quant.trainer import EncodedClassifier
from axq.schemas import AgentPrediction, Signal


class QuantAgent:
    def __init__(self, run_dir: str | Path) -> None:
        self.run_dir = Path(run_dir)
        self.manifest = verify_run(self.run_dir)
        hashes = self.manifest.artifact_hashes
        paths = self.manifest.artifact_paths
        self.model: EncodedClassifier = load_artifact(
            self.run_dir / paths["model"], hashes["model"]
        )
        self.preprocessing: FrozenPreprocessor = load_artifact(
            self.run_dir / paths["preprocessing"], hashes["preprocessing"]
        )
        self.calibration: ProbabilityCalibrator = load_artifact(
            self.run_dir / paths["calibration"], hashes["calibration"]
        )
        config: dict[str, Any] = load_artifact_json(
            self.run_dir / paths["training_config"]
        )
        self.minimum_confidence = float(config["hold_policy"]["minimum_confidence"])
        self.explicit_neutral_class = bool(
            config["hold_policy"]["explicit_neutral_class"]
        )
        self.maximum_data_age_ms = int(config["maximum_data_age_ms"])

    def predict_probabilities(self, feature_row: dict[str, Any] | pd.Series) -> np.ndarray:
        frame = pd.DataFrame([dict(feature_row)])
        transformed = self.preprocessing.transform(frame)
        return np.asarray(
            self.calibration.transform(self.model.predict_proba(transformed))[0],
            dtype=float,
        )

    def predict(
        self,
        feature_row: dict[str, Any] | pd.Series,
        *,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        data_freshness_ms: int,
        feature_manifest_id: str,
        dataset_id: str | None = None,
        snapshot_id: UUID | None = None,
    ) -> AgentPrediction:
        self._validate_compatibility(feature_manifest_id, dataset_id)
        if data_freshness_ms > self.maximum_data_age_ms:
            raise ValueError("Feature row is stale")
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Inference timestamp must be timezone-aware")
        aware = timestamp.astimezone(UTC)
        probability = self.predict_probabilities(feature_row)
        signals, confidence = signals_from_probabilities(
            probability.reshape(1, -1),
            self.model.classes_,
            minimum_confidence=self.minimum_confidence,
            explicit_neutral_class=self.explicit_neutral_class,
        )
        signal = Signal(str(signals[0]))
        class_probabilities = {
            str(label): float(probability[index])
            for index, label in enumerate(self.model.classes_)
        }
        reasons = self._explain(feature_row, signal)
        positive = class_probabilities.get("UP", class_probabilities.get("BUY", 0.0))
        negative = class_probabilities.get("DOWN", class_probabilities.get("SELL", 0.0))
        score = positive - negative
        return AgentPrediction(
            snapshot_id=snapshot_id or uuid4(),
            agent="quant",
            symbol=symbol,
            timeframe=timeframe,
            timestamp=aware,
            signal=signal,
            score=float(score),
            confidence=float(confidence[0]),
            data_freshness_ms=data_freshness_ms,
            model_version=self.manifest.model_id,
            feature_version=self.manifest.feature_manifest_id,
            dataset_id=self.manifest.dataset_id,
            label_manifest_id=self.manifest.label_manifest_id,
            reasons=reasons,
            metadata={
                "class_probabilities": class_probabilities,
                "target_column": self.manifest.target_column,
                "split_manifest_id": self.manifest.split_manifest_id,
                "feature_list_version": self.manifest.feature_list_version,
            },
        )

    def _validate_compatibility(
        self, feature_manifest_id: str, dataset_id: str | None
    ) -> None:
        if feature_manifest_id != self.manifest.feature_manifest_id:
            raise ValueError("Feature manifest is incompatible with model")
        if dataset_id is not None and dataset_id != self.manifest.dataset_id:
            raise ValueError("Dataset identity is incompatible with model")

    def _explain(
        self, feature_row: dict[str, Any] | pd.Series, signal: Signal
    ) -> dict[str, Any]:
        estimator = self.model.estimator
        coefficients = getattr(estimator, "coef_", None)
        if coefficients is None:
            importance = getattr(estimator, "feature_importances_", None)
            if importance is None:
                return {"method": "class_probability"}
            order = np.argsort(np.asarray(importance))[-5:][::-1]
            return {
                "method": "feature_importance",
                "top_features": [self.preprocessing.selected_features[i] for i in order],
            }
        transformed = self.preprocessing.transform(pd.DataFrame([dict(feature_row)]))[0]
        probability = self.predict_probabilities(feature_row)
        class_index = int(np.argmax(probability))
        matrix = np.asarray(coefficients)
        row = matrix[0] if matrix.shape[0] == 1 else matrix[class_index]
        contributions = transformed * row
        order = np.argsort(np.abs(contributions))[-5:][::-1]
        return {
            "method": "logistic_contribution",
            "predicted_signal": signal.value,
            "top": [
                {
                    "feature": self.preprocessing.selected_features[i],
                    "contribution": float(contributions[i]),
                }
                for i in order
            ],
        }


def load_artifact_json(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object in {path}")
    return payload


def load_manifest(run_dir: str | Path) -> ModelManifest:
    return verify_run(run_dir)
