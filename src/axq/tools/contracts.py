"""Strict fact-only contracts for deterministic analytical tools."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from axq.runtime import FreshnessStatus, SharedRuntimeState
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class ToolCategory(StrEnum):
    STRUCTURE = "structure"
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    STATISTICS = "statistics"
    VOLUME = "volume"
    BREAKOUT = "breakout"
    SESSION_CONTEXT = "session_context"
    SIMILARITY = "similarity"
    SLOW_CONTEXT = "slow_context"
    PREDICTIVE_MODEL = "predictive_model"


class ToolStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"


FactScalar = bool | int | FiniteFloat | str
_DECISION_NAMES = {"action", "decision", "recommendation", "signal"}
_DECISION_VALUES = {"BUY", "SELL", "ENTER", "HOLD", "STRONG BUY", "STRONG SELL"}


class ToolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ToolFact(ToolModel):
    name: str = Field(min_length=1)
    value: FactScalar
    unit: str | None = None

    @model_validator(mode="after")
    def reject_trading_decisions(self) -> ToolFact:
        normalized_name = self.name.strip().lower()
        name_tokens = set(re.split(r"[^a-z0-9]+", normalized_name))
        normalized_value = re.sub(r"[_-]+", " ", str(self.value).strip().upper())
        if name_tokens & _DECISION_NAMES or normalized_value in _DECISION_VALUES:
            raise ValueError("tool facts cannot contain a trading decision")
        return self


class ToolQuality(ToolModel):
    valid: bool
    sample_size: int | None = Field(default=None, ge=0)
    missing_fields: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


class ToolProvenance(ToolModel):
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    source_identity: str | None = None


class FeatureValue(ToolModel):
    name: str = Field(min_length=1)
    value: FactScalar


class CausalFeatureSnapshot(ToolModel):
    snapshot_id: str = ""
    symbol: str = Field(min_length=1)
    base_timeframe: str = Field(min_length=1)
    as_of: UTCDateTime
    available_at: UTCDateTime
    feature_manifest_id: str = Field(min_length=1)
    completed_timeframes: tuple[str, ...]
    values: tuple[FeatureValue, ...]
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)

    @field_validator("base_timeframe")
    @classmethod
    def normalize_base_timeframe(cls, value: str) -> str:
        return value.upper()

    @field_validator("completed_timeframes")
    @classmethod
    def normalize_completed_timeframes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted({item.upper() for item in value}))

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> CausalFeatureSnapshot:
        if self.available_at < self.as_of:
            raise ValueError("feature available_at must not precede as_of")
        names = [item.name for item in self.values]
        if names != sorted(names) or len(names) != len(set(names)):
            raise ValueError("feature values must be unique and sorted by name")
        identity = self.model_dump(mode="json", exclude={"snapshot_id"})
        expected = f"fs-{canonical_hash(identity)[:20]}"
        if self.snapshot_id and self.snapshot_id != expected:
            raise ValueError("snapshot_id does not match feature content")
        object.__setattr__(self, "snapshot_id", expected)
        return self

    @classmethod
    def from_mapping(
        cls,
        *,
        symbol: str,
        base_timeframe: str,
        as_of: Any,
        available_at: Any,
        feature_manifest_id: str,
        completed_timeframes: tuple[str, ...],
        values: Mapping[str, Any],
        source: str,
        source_version: str,
    ) -> CausalFeatureSnapshot:
        normalized: list[FeatureValue] = []
        for name, raw_value in sorted(values.items()):
            value = raw_value.item() if hasattr(raw_value, "item") else raw_value
            if value is None or (isinstance(value, float) and math.isnan(value)):
                continue
            normalized.append(FeatureValue(name=name, value=value))
        return cls(
            symbol=symbol,
            base_timeframe=base_timeframe,
            as_of=as_of,
            available_at=available_at,
            feature_manifest_id=feature_manifest_id,
            completed_timeframes=completed_timeframes,
            values=tuple(normalized),
            source=source,
            source_version=source_version,
        )

    def as_mapping(self) -> dict[str, FactScalar]:
        return {item.name: item.value for item in self.values}


class ToolInput(ToolModel):
    state: SharedRuntimeState
    feature_snapshot: CausalFeatureSnapshot | None = None

    @model_validator(mode="after")
    def validate_symbol(self) -> ToolInput:
        if (
            self.feature_snapshot is not None
            and self.feature_snapshot.symbol != self.state.market.symbol
        ):
            raise ValueError("feature snapshot symbol does not match runtime state")
        return self


class ToolResult(ToolModel):
    result_id: str = ""
    tool_name: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    category: ToolCategory
    as_of: UTCDateTime
    available_at: UTCDateTime
    runtime_state_id: str = Field(min_length=1)
    input_snapshot_id: str = Field(min_length=1)
    freshness: FreshnessStatus
    status: ToolStatus
    facts: tuple[ToolFact, ...] = ()
    quality: ToolQuality
    warnings: tuple[str, ...] = ()
    provenance: tuple[ToolProvenance, ...] = ()

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ToolResult:
        if self.available_at > self.as_of:
            raise ValueError("tool result cannot be available after its as_of time")
        if self.status is ToolStatus.AVAILABLE and not self.quality.valid:
            raise ValueError("available tool result must be valid")
        identity = self.model_dump(mode="json", exclude={"result_id"})
        expected = f"tool-{canonical_hash(identity)[:20]}"
        if self.result_id and self.result_id != expected:
            raise ValueError("result_id does not match tool result content")
        object.__setattr__(self, "result_id", expected)
        return self


class AnalyticalTool(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def category(self) -> ToolCategory: ...

    def evaluate(self, tool_input: ToolInput) -> ToolResult:
        """Return deterministic facts for one causal input."""


def fact_name(label: str) -> str:
    """Normalize a factual label for stable probability-field names."""
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
