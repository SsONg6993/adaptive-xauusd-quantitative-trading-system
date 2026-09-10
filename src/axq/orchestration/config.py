"""Strict operational configuration for the Phase 7 runtime service."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from axq.orchestration.contracts import RuntimeMode


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    mode: RuntimeMode = RuntimeMode.DISABLED
    symbol: str = Field(min_length=1)
    broker_symbol: str = Field(min_length=1)
    runtime_journal_path: Path
    execution_ledger_path: Path
    position_action_ledger_path: Path
    mt5_terminal_path: Path | None = None
    event_poll_interval_ms: int = Field(default=1_000, ge=100, le=60_000)
    snapshot_interval_ms: int = Field(default=5_000, ge=500, le=300_000)
    safe_shutdown_timeout_seconds: int = Field(default=15, ge=1, le=300)
    feature_source: str = Field(default="causal-m5", min_length=1)
    policy_references: tuple[str, ...] = ()


def load_runtime_config(path: str | Path) -> RuntimeConfig:
    import yaml  # type: ignore[import-untyped]

    with Path(path).open(encoding="utf-8") as stream:
        payload = yaml.safe_load(stream)
    if not isinstance(payload, dict):
        raise ValueError("runtime configuration must be a mapping")
    return RuntimeConfig.model_validate(payload)
