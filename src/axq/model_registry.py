"""Immutable model metadata; activation is data, not a source-code edit."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


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
