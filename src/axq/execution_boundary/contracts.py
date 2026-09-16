"""Strict contracts for deterministic execution intent and broker feedback."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.schemas import Signal
from axq.versioning import canonical_hash


class ExecutionBoundaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ExecutionMode(StrEnum):
    DISABLED = "DISABLED"
    DRY_RUN = "DRY_RUN"
    DEMO_ENABLED = "DEMO_ENABLED"


class ExecutionAccountMode(StrEnum):
    UNKNOWN = "UNKNOWN"
    DEMO = "DEMO"
    LIVE = "LIVE"


class ExecutionOrderType(StrEnum):
    MARKET = "MARKET"


class ExecutionResultStatus(StrEnum):
    NO_ACTION = "NO_ACTION"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ExecutionReason(StrEnum):
    EXECUTION_DISABLED = "EXECUTION_DISABLED"
    DRY_RUN = "DRY_RUN"
    LIVE_ACCOUNT_BLOCKED = "LIVE_ACCOUNT_BLOCKED"
    UNKNOWN_ACCOUNT_MODE = "UNKNOWN_ACCOUNT_MODE"
    INTENT_EXPIRED = "INTENT_EXPIRED"
    OBSERVATION_STALE = "OBSERVATION_STALE"
    SYMBOL_MISMATCH = "SYMBOL_MISMATCH"
    SPREAD_LIMIT = "SPREAD_LIMIT"
    SLIPPAGE_LIMIT = "SLIPPAGE_LIMIT"
    PRICE_DEVIATION_LIMIT = "PRICE_DEVIATION_LIMIT"
    BROKER_REJECTED = "BROKER_REJECTED"
    BROKER_CANCELLED = "BROKER_CANCELLED"
    BROKER_EXPIRED = "BROKER_EXPIRED"
    TRANSPORT_FAILED = "TRANSPORT_FAILED"
    UNKNOWN_SUBMISSION = "UNKNOWN_SUBMISSION"
    INVALID_BROKER_REPORT = "INVALID_BROKER_REPORT"


class ExecutionPolicy(ExecutionBoundaryModel):
    policy_id: str = ""
    policy_version: str = Field(min_length=1)
    mode: ExecutionMode
    intent_ttl_seconds: int = Field(gt=0)
    max_observation_latency_seconds: float = Field(gt=0.0)
    max_actual_spread_points: float = Field(ge=0.0)
    max_pre_submit_slippage_points: float = Field(ge=0.0)
    max_price_deviation_points: float = Field(ge=0.0)

    @model_validator(mode="after")
    def bind_identity(self) -> ExecutionPolicy:
        identity = self.model_dump(mode="json", exclude={"policy_id"})
        expected = f"ep-{canonical_hash(identity)[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match execution policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class ExecutionIntent(ExecutionBoundaryModel):
    intent_id: str = ""
    evidence_bundle_id: str = Field(min_length=1)
    master_proposal_id: str = Field(min_length=1)
    discipline_outcome_id: str = Field(min_length=1)
    risk_outcome_id: str = Field(min_length=1)
    risk_context_id: str = Field(min_length=1)
    setup_id: str = Field(min_length=1)
    thesis_id: str = Field(min_length=1)
    scenario_id: str | None = None
    symbol: str = Field(min_length=1)
    broker_symbol: str = Field(min_length=1)
    broker_source: str = Field(min_length=1)
    point_size: FiniteFloat = Field(gt=0.0)
    direction: Signal
    approved_volume_lots: FiniteFloat = Field(gt=0.0)
    order_type: ExecutionOrderType
    requested_entry_price: FiniteFloat = Field(gt=0.0)
    stop_loss_price: FiniteFloat = Field(gt=0.0)
    take_profit_price: None = None
    as_of: UTCDateTime
    available_at: UTCDateTime
    expires_at: UTCDateTime
    execution_policy_id: str = Field(min_length=1)
    execution_policy_version: str = Field(min_length=1)
    execution_mode: ExecutionMode

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ExecutionIntent:
        if self.direction is Signal.HOLD:
            raise ValueError("HOLD cannot become an execution intent")
        if self.available_at > self.as_of:
            raise ValueError("execution intent cannot be available after as_of")
        if self.expires_at <= self.available_at:
            raise ValueError("execution intent expiry must follow availability")
        valid_stop = (
            self.direction is Signal.BUY and self.stop_loss_price < self.requested_entry_price
        ) or (
            self.direction is Signal.SELL and self.stop_loss_price > self.requested_entry_price
        )
        if not valid_stop:
            raise ValueError("execution intent stop cannot increase directional risk")
        identity = self.model_dump(mode="json", exclude={"intent_id"})
        expected = f"xi-{canonical_hash(identity)[:20]}"
        if self.intent_id and self.intent_id != expected:
            raise ValueError("intent_id does not match execution intent content")
        object.__setattr__(self, "intent_id", expected)
        return self


class ExecutionObservation(ExecutionBoundaryModel):
    observation_id: str = ""
    observed_at: UTCDateTime
    available_at: UTCDateTime
    account_mode: ExecutionAccountMode
    broker_symbol: str = Field(min_length=1)
    market_price: FiniteFloat = Field(gt=0.0)
    spread_points: FiniteFloat = Field(ge=0.0)
    estimated_slippage_points: FiniteFloat = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ExecutionObservation:
        if self.available_at < self.observed_at:
            raise ValueError("execution observation availability cannot precede observation")
        identity = self.model_dump(mode="json", exclude={"observation_id"})
        expected = f"xo-{canonical_hash(identity)[:20]}"
        if self.observation_id and self.observation_id != expected:
            raise ValueError("observation_id does not match execution observation content")
        object.__setattr__(self, "observation_id", expected)
        return self


class BrokerExecutionReport(ExecutionBoundaryModel):
    report_id: str = ""
    status: ExecutionResultStatus
    event_time: UTCDateTime
    observed_at: UTCDateTime
    available_at: UTCDateTime
    broker_ticket: int | None = Field(default=None, gt=0)
    transport_execution_id: str | None = Field(default=None, min_length=1)
    filled_volume_lots: FiniteFloat = Field(ge=0.0)
    fill_price: FiniteFloat | None = Field(default=None, gt=0.0)
    broker_retcode: str | None = None
    broker_status: str | None = None
    message: str | None = None

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> BrokerExecutionReport:
        forbidden = {
            ExecutionResultStatus.NO_ACTION,
            ExecutionResultStatus.UNKNOWN,
        }
        if self.status in forbidden:
            raise ValueError("transport report cannot claim local-only execution status")
        if not self.event_time <= self.observed_at <= self.available_at:
            raise ValueError("report timestamps must be causally ordered")
        if self.filled_volume_lots > 0 and self.fill_price is None:
            raise ValueError("filled broker report requires fill price")
        identity = self.model_dump(mode="json", exclude={"report_id"})
        expected = f"xr-{canonical_hash(identity)[:20]}"
        if self.report_id and self.report_id != expected:
            raise ValueError("report_id does not match broker report content")
        object.__setattr__(self, "report_id", expected)
        return self


class ExecutionResult(ExecutionBoundaryModel):
    result_id: str = ""
    execution_intent_id: str = Field(min_length=1)
    evidence_bundle_id: str = Field(min_length=1)
    master_proposal_id: str = Field(min_length=1)
    discipline_outcome_id: str = Field(min_length=1)
    risk_outcome_id: str = Field(min_length=1)
    setup_id: str = Field(min_length=1)
    thesis_id: str = Field(min_length=1)
    scenario_id: str | None = None
    symbol: str = Field(min_length=1)
    direction: Signal
    status: ExecutionResultStatus
    reason_code: ExecutionReason | None = None
    reason: str | None = Field(default=None, max_length=500)
    requested_volume_lots: FiniteFloat = Field(gt=0.0)
    filled_volume_lots: FiniteFloat | None = Field(default=None, ge=0.0)
    remaining_volume_lots: FiniteFloat | None = Field(default=None, ge=0.0)
    requested_price: FiniteFloat = Field(gt=0.0)
    fill_price: FiniteFloat | None = Field(default=None, gt=0.0)
    actual_spread_points: FiniteFloat | None = Field(default=None, ge=0.0)
    realized_slippage_points: FiniteFloat | None = None
    broker_ticket: int | None = Field(default=None, gt=0)
    transport_execution_id: str | None = Field(default=None, min_length=1)
    broker_retcode: str | None = None
    broker_status: str | None = None
    event_time: UTCDateTime
    observed_at: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ExecutionResult:
        if self.direction is Signal.HOLD:
            raise ValueError("execution result direction cannot be HOLD")
        if not self.event_time <= self.observed_at <= self.available_at:
            raise ValueError("execution result timestamps must be causally ordered")
        if self.status is ExecutionResultStatus.UNKNOWN:
            if self.filled_volume_lots is not None or self.remaining_volume_lots is not None:
                raise ValueError("unknown submission cannot claim known volume state")
        else:
            if self.filled_volume_lots is None or self.remaining_volume_lots is None:
                raise ValueError("known execution status requires fill and remaining volumes")
            total = self.filled_volume_lots + self.remaining_volume_lots
            if not math.isclose(total, self.requested_volume_lots, abs_tol=1e-10):
                raise ValueError("filled and remaining volume must equal requested volume")
            if self.status is ExecutionResultStatus.PARTIALLY_FILLED and not (
                0 < self.filled_volume_lots < self.requested_volume_lots
            ):
                raise ValueError("partial fill requires a strict partial volume")
            if self.status is ExecutionResultStatus.FILLED and not math.isclose(
                self.filled_volume_lots,
                self.requested_volume_lots,
                abs_tol=1e-10,
            ):
                raise ValueError("filled result must fill the requested volume")
        if (self.filled_volume_lots or 0.0) > 0 and self.fill_price is None:
            raise ValueError("positive fill volume requires fill price")
        if self.status in {
            ExecutionResultStatus.NO_ACTION,
            ExecutionResultStatus.REJECTED,
            ExecutionResultStatus.FAILED,
            ExecutionResultStatus.UNKNOWN,
        } and self.reason_code is None:
            raise ValueError("non-success execution status requires a reason code")
        identity = self.model_dump(mode="json", exclude={"result_id"})
        expected = f"xe-{canonical_hash(identity)[:20]}"
        if self.result_id and self.result_id != expected:
            raise ValueError("result_id does not match execution result content")
        object.__setattr__(self, "result_id", expected)
        return self
