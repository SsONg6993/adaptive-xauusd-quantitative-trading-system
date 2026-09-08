"""Typed configuration loading with environment overrides."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = "sqlite:///runtime/axq.sqlite3"
    busy_timeout_ms: int = Field(default=5_000, ge=0)


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: str = "INFO"
    path: Path = Path("runtime/logs/axq.jsonl")


class IpcConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str = "atomic_file"
    shared_dir: Path = Path("runtime/ipc")
    max_signal_age_seconds: int = Field(default=15, gt=0)
    heartbeat_timeout_seconds: int = Field(default=10, gt=0)


class FeatureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str = "features-v0.1"
    groups: list[str] = Field(default_factory=lambda: ["price_action", "trend", "volatility"])
    parameters: dict[str, dict[str, Any]] = Field(default_factory=dict)


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    environment: str = "development"
    symbols: list[str] = Field(default_factory=lambda: ["XAUUSD"])
    timeframes: list[str] = Field(default_factory=lambda: ["M5", "M15", "H1", "H4"])
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    ipc: IpcConfig = Field(default_factory=IpcConfig)
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    llm_enabled: bool = False
    external_news_enabled: bool = False


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - exercised on minimal installs
        try:
            return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            raise RuntimeError("Install PyYAML to load YAML configuration") from exc
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")
    return cast(dict[str, Any], payload)


def load_config(path: str | Path) -> AppConfig:
    """Load a configuration file and apply safe, explicit environment overrides."""
    payload = _read_yaml(Path(path))
    if value := os.getenv("AXQ_DATABASE_URL"):
        payload.setdefault("database", {})["url"] = value
    if value := os.getenv("AXQ_LOG_LEVEL"):
        payload.setdefault("logging", {})["level"] = value
    if value := os.getenv("AXQ_LOG_PATH"):
        payload.setdefault("logging", {})["path"] = value
    return AppConfig.model_validate(payload)
