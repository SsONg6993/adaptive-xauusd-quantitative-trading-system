"""Strict configuration contracts for local Quant development."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.quant.config import Architecture, QuantTrainingConfig
from axq.versioning import canonical_hash


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hold_thresholds: list[float] = Field(
        default_factory=lambda: [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
    )
    temporal_frequency: Literal["month", "quarter", "year"] = "month"
    session_columns: list[str] = Field(
        default_factory=lambda: [
            "session_asia",
            "session_london",
            "session_new_york",
            "session_london_ny_overlap",
        ]
    )

    @model_validator(mode="after")
    def validate_thresholds(self) -> EvaluationConfig:
        if not self.hold_thresholds or any(
            value < 0.0 or value > 1.0 for value in self.hold_thresholds
        ):
            raise ValueError("hold_thresholds must contain probabilities in [0, 1]")
        if len(set(self.hold_thresholds)) != len(self.hold_thresholds):
            raise ValueError("hold_thresholds must be unique")
        return self


class WalkForwardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    mode: Literal["expanding", "rolling"] = "expanding"
    train_length: int = Field(default=10_000, gt=0)
    validation_length: int = Field(default=2_000, gt=0)
    oos_length: int = Field(default=2_000, gt=0)
    step_size: int = Field(default=2_000, gt=0)
    purge_bars: int = Field(default=0, ge=0)
    embargo_bars: int = Field(default=0, ge=0)
    max_folds: int | None = Field(default=None, gt=0)


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    name: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    output_root: Path = Path("runtime/experiments/quant")
    training: QuantTrainingConfig
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    walk_forward: WalkForwardConfig = Field(default_factory=WalkForwardConfig)
    tags: list[str] = Field(default_factory=list)

    @property
    def config_hash(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))


class SuiteConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    name: str = Field(min_length=1)
    experiments: list[Path] = Field(min_length=1)
    output_root: Path = Path("runtime/experiments/quant/suites")
    continue_on_failure: bool = True
    resume: bool = True


class AblationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature_groups: list[str] = Field(default_factory=list)
    single_features: list[str] = Field(default_factory=list)
    include_all_features: bool = True


class TuningConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    architecture: Architecture
    objective_scope: Literal["validation", "walk_forward_validation"]
    metric: Literal["log_loss", "brier_score", "balanced_accuracy"]
    direction: Literal["minimize", "maximize"] = "minimize"
    n_trials: int = Field(default=25, gt=0)
    random_seed: int = 42

    @model_validator(mode="after")
    def validate_architecture(self) -> TuningConfig:
        allowed = {
            Architecture.RANDOM_FOREST,
            Architecture.XGBOOST,
            Architecture.LIGHTGBM,
        }
        if self.architecture not in allowed:
            raise ValueError("Tuning is prepared only for Random Forest, XGBoost, LightGBM")
        return self


def _load_mapping(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Configuration must be a YAML mapping: {path}")
    return payload


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    source = Path(path).resolve()
    config = ExperimentConfig.model_validate(_load_mapping(source))
    training = config.training.model_copy(
        update={
            "dataset_dir": (source.parent / config.training.dataset_dir).resolve()
            if not config.training.dataset_dir.is_absolute()
            else config.training.dataset_dir,
            "output_root": (source.parent / config.training.output_root).resolve()
            if not config.training.output_root.is_absolute()
            else config.training.output_root,
        }
    )
    output_root = (
        (source.parent / config.output_root).resolve()
        if not config.output_root.is_absolute()
        else config.output_root
    )
    return config.model_copy(update={"training": training, "output_root": output_root})


def load_suite_config(path: str | Path) -> SuiteConfig:
    source = Path(path).resolve()
    config = SuiteConfig.model_validate(_load_mapping(source))
    return config.model_copy(
        update={
            "experiments": [
                (source.parent / item).resolve() if not item.is_absolute() else item
                for item in config.experiments
            ],
            "output_root": (source.parent / config.output_root).resolve()
            if not config.output_root.is_absolute()
            else config.output_root,
        }
    )


def load_tuning_config(path: str | Path) -> TuningConfig:
    return TuningConfig.model_validate(_load_mapping(Path(path)))


def load_walk_forward_config(path: str | Path) -> WalkForwardConfig:
    return WalkForwardConfig.model_validate(_load_mapping(Path(path)))


def load_ablation_config(path: str | Path) -> AblationConfig:
    return AblationConfig.model_validate(_load_mapping(Path(path)))


def development_run_id(
    config: ExperimentConfig, *, dataset_id: str, git_identity: str
) -> str:
    identity = canonical_hash(
        {
            "config": config.model_dump(mode="json"),
            "dataset_id": dataset_id,
            "git_identity": git_identity,
        }
    )[:20]
    return f"qdev-{config.name}-{identity}"
