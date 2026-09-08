"""Strict, hashable configuration for Quant Agent training."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field

from axq.versioning import canonical_hash


class Architecture(StrEnum):
    MAJORITY = "majority"
    PRIOR = "prior"
    LOGISTIC = "logistic_regression"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"


class Device(StrEnum):
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class PreprocessingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    imputation: Literal["none", "median"] = "median"
    scaler: Literal["none", "standard", "robust"] = "standard"


class FeatureSelectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    variance_threshold: float | None = Field(default=None, ge=0.0)
    correlation_threshold: float | None = Field(default=None, gt=0.0, le=1.0)


class CalibrationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method: Literal["none", "sigmoid", "isotonic"] = "none"


class HoldPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    minimum_confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    explicit_neutral_class: bool = True


class QuantTrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent: str = "quant"
    architecture: Architecture
    dataset_dir: Path
    target_column: str | None = None
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    feature_selection: FeatureSelectionConfig = Field(
        default_factory=FeatureSelectionConfig
    )
    model_hyperparameters: dict[str, Any] = Field(default_factory=dict)
    random_seed: int = 42
    class_weighting: Literal["none", "balanced"] = "none"
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    hold_policy: HoldPolicyConfig = Field(default_factory=HoldPolicyConfig)
    output_root: Path = Path("runtime/models/quant")
    device: Device = Device.AUTO
    maximum_data_age_ms: int = Field(default=600_000, ge=0)

    @property
    def config_hash(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))


def load_quant_config(path: str | Path) -> QuantTrainingConfig:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Quant configuration must be a YAML mapping")
    return QuantTrainingConfig.model_validate(payload)
