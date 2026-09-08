"""Stable, versioned messages crossing agent, master, risk, and execution boundaries."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Signal(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class MarketRegime(StrEnum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    BREAKOUT = "BREAKOUT"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    NEWS_DRIVEN = "NEWS_DRIVEN"
    ABNORMAL = "ABNORMAL"
    UNKNOWN = "UNKNOWN"


class RiskStatus(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class StrictMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"


class AgentPrediction(StrictMessage):
    prediction_id: UUID = Field(default_factory=uuid4)
    snapshot_id: UUID
    agent: str
    symbol: str
    timeframe: str
    timestamp: datetime
    signal: Signal
    score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    data_freshness_ms: int = Field(ge=0)
    model_version: str
    feature_version: str
    reasons: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class MasterDecision(StrictMessage):
    decision_id: UUID = Field(default_factory=uuid4)
    snapshot_id: UUID
    symbol: str
    timestamp: datetime
    decision: Signal
    confidence: float = Field(ge=0.0, le=1.0)
    market_regime: MarketRegime = MarketRegime.UNKNOWN
    agent_scores: dict[str, float] = Field(default_factory=dict)
    entry_suggestion: float | None = Field(default=None, gt=0)
    sl_suggestion: float | None = Field(default=None, gt=0)
    tp_suggestion: float | None = Field(default=None, gt=0)
    reasons: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class RiskDecision(StrictMessage):
    risk_decision_id: UUID = Field(default_factory=uuid4)
    master_decision_id: UUID
    timestamp: datetime
    status: RiskStatus
    veto_reasons: list[str] = Field(default_factory=list)
    risk_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    stop_distance_points: float | None = Field(default=None, gt=0)
    approved_volume_lots: float | None = Field(default=None, gt=0)

    @field_validator("veto_reasons")
    @classmethod
    def rejection_needs_reason(cls, value: list[str]) -> list[str]:
        return [reason.strip() for reason in value if reason.strip()]

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value

    @model_validator(mode="after")
    def decision_is_consistent(self) -> RiskDecision:
        if self.status is RiskStatus.REJECTED and not self.veto_reasons:
            raise ValueError("rejected risk decision requires at least one veto reason")
        if self.status is RiskStatus.REJECTED and self.approved_volume_lots is not None:
            raise ValueError("rejected risk decision cannot approve volume")
        return self


class ExecutionInstruction(StrictMessage):
    instruction_id: UUID = Field(default_factory=uuid4)
    idempotency_key: UUID = Field(default_factory=uuid4)
    master_decision_id: UUID
    risk_decision_id: UUID
    symbol: str
    signal: Signal
    created_at: datetime
    expires_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    volume_lots: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)

    @field_validator("signal")
    @classmethod
    def no_hold_execution(cls, value: Signal) -> Signal:
        if value is Signal.HOLD:
            raise ValueError("HOLD cannot become an execution instruction")
        return value

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("execution timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def expiry_follows_creation(self) -> ExecutionInstruction:
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        return self
