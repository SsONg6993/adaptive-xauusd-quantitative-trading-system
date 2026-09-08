"""Immutable model metadata; activation is data, not a source-code edit."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from axq.quant.manifest import ModelManifest
from axq.quant.registry import LocalModelRegistry, ModelState


class ModelRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: str
    agent_type: str
    architecture: str
    training_period: str
    validation_period: str
    oos_period: str
    feature_version: str
    dataset_version: str
    config_hash: str
    metrics: dict[str, float]
    model_path: Path
    onnx_path: Path | None = None
    scaler_path: Path | None = None
    feature_list: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    git_commit: str | None = None
    status: str = "CANDIDATE"

    @classmethod
    def from_quant_manifest(
        cls, manifest: ModelManifest, run_dir: str | Path
    ) -> ModelRecord:
        return cls(
            model_id=manifest.model_id,
            agent_type=manifest.agent_type,
            architecture=manifest.architecture,
            training_period=manifest.training_period,
            validation_period=manifest.validation_period,
            oos_period=manifest.oos_period,
            feature_version=manifest.feature_manifest_id,
            dataset_version=manifest.dataset_id,
            config_hash=manifest.config_hash,
            metrics={
                f"oos_{name}": float(value)
                for name, value in manifest.metrics.get("oos", {}).items()
                if isinstance(value, (int, float))
            },
            model_path=Path(run_dir) / manifest.artifact_paths["model"],
            scaler_path=Path(run_dir) / manifest.artifact_paths["preprocessing"],
            feature_list=manifest.selected_features,
            created_at=manifest.created_at,
            git_commit=manifest.git_commit,
            status=ModelState.CANDIDATE.value,
        )


__all__ = ["LocalModelRegistry", "ModelRecord", "ModelState"]
