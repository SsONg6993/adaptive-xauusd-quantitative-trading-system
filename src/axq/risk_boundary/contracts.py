"""Strict contracts for the deterministic financial Risk boundary."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.discipline import DisciplineResult
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ExposureState,
    MarketState,
    OrderBookState,
    PositionBookState,
)
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.schemas import Signal
from axq.versioning import canonical_hash


class RiskBoundaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class RiskResult(StrEnum):
    PASS = "PASS"
    REJECT = "REJECT"
    NO_ACTION = "NO_ACTION"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class RiskReason(StrEnum):
    PASSED = "PASSED"
    DISCIPLINE_NOT_PASSED = "DISCIPLINE_NOT_PASSED"
    KILL_SWITCH = "KILL_SWITCH"
    EMERGENCY_DAILY_DRAWDOWN = "EMERGENCY_DAILY_DRAWDOWN"
    EMERGENCY_TOTAL_DRAWDOWN = "EMERGENCY_TOTAL_DRAWDOWN"
    ACCOUNT_NOT_FRESH = "ACCOUNT_NOT_FRESH"
    MARKET_NOT_FRESH = "MARKET_NOT_FRESH"
    POSITION_BOOK_NOT_FRESH = "POSITION_BOOK_NOT_FRESH"
    ORDER_BOOK_NOT_FRESH = "ORDER_BOOK_NOT_FRESH"
    EXPOSURE_NOT_FRESH = "EXPOSURE_NOT_FRESH"
    BROKER_CONSTRAINTS_NOT_FRESH = "BROKER_CONSTRAINTS_NOT_FRESH"
    MISSING_ACCOUNT_VALUES = "MISSING_ACCOUNT_VALUES"
    ACCOUNT_INCONSISTENT = "ACCOUNT_INCONSISTENT"
    INSUFFICIENT_FREE_MARGIN = "INSUFFICIENT_FREE_MARGIN"
    MARGIN_LEVEL_LIMIT = "MARGIN_LEVEL_LIMIT"
    DAILY_DRAWDOWN_LIMIT = "DAILY_DRAWDOWN_LIMIT"
    TOTAL_DRAWDOWN_LIMIT = "TOTAL_DRAWDOWN_LIMIT"
    POSITION_LIMIT = "POSITION_LIMIT"
    PENDING_ORDER_LIMIT = "PENDING_ORDER_LIMIT"
    MISSING_EXPOSURE_VALUES = "MISSING_EXPOSURE_VALUES"
    GROSS_EXPOSURE_LIMIT = "GROSS_EXPOSURE_LIMIT"
    NET_EXPOSURE_LIMIT = "NET_EXPOSURE_LIMIT"
    SPREAD_UNAVAILABLE = "SPREAD_UNAVAILABLE"
    SPREAD_LIMIT = "SPREAD_LIMIT"
    SLIPPAGE_UNAVAILABLE = "SLIPPAGE_UNAVAILABLE"
    SLIPPAGE_LIMIT = "SLIPPAGE_LIMIT"
    BROKER_TRADING_DISABLED = "BROKER_TRADING_DISABLED"
    MISSING_BROKER_VALUES = "MISSING_BROKER_VALUES"
    INVALID_STOP_DIRECTION = "INVALID_STOP_DIRECTION"
    MINIMUM_STOP_DISTANCE = "MINIMUM_STOP_DISTANCE"
    BROKER_STOP_LEVEL = "BROKER_STOP_LEVEL"
    BROKER_FREEZE_LEVEL = "BROKER_FREEZE_LEVEL"
    MISSING_SIZING_INPUTS = "MISSING_SIZING_INPUTS"
    VOLUME_BELOW_MINIMUM = "VOLUME_BELOW_MINIMUM"


class RiskPolicy(RiskBoundaryModel):
    policy_id: str = ""
    policy_version: str = Field(min_length=1)
    risk_fraction_per_trade: float = Field(gt=0.0, le=0.1)
    max_daily_drawdown_fraction: float = Field(gt=0.0, lt=1.0)
    emergency_daily_drawdown_fraction: float = Field(gt=0.0, lt=1.0)
    max_total_drawdown_fraction: float = Field(gt=0.0, lt=1.0)
    emergency_total_drawdown_fraction: float = Field(gt=0.0, lt=1.0)
    minimum_margin_level: float = Field(gt=0.0)
    free_margin_buffer_fraction: float = Field(ge=0.0, le=10.0)
    max_open_positions: int = Field(gt=0)
    max_pending_orders: int = Field(ge=0)
    max_gross_lots: float = Field(gt=0.0)
    max_abs_net_lots: float = Field(gt=0.0)
    max_spread_points: float = Field(ge=0.0)
    max_slippage_points: float = Field(ge=0.0)
    max_component_age_seconds: float = Field(gt=0.0)
    minimum_stop_distance_points: float = Field(ge=0.0)
    max_approved_volume_lots: float = Field(gt=0.0)
    account_consistency_tolerance_fraction: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> RiskPolicy:
        if self.emergency_daily_drawdown_fraction <= self.max_daily_drawdown_fraction:
            raise ValueError("emergency daily drawdown must exceed the ordinary limit")
        if self.emergency_total_drawdown_fraction <= self.max_total_drawdown_fraction:
            raise ValueError("emergency total drawdown must exceed the ordinary limit")
        identity = self.model_dump(mode="json", exclude={"policy_id"})
        expected = f"rp-{canonical_hash(identity)[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match Risk policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class RiskContext(RiskBoundaryModel):
    context_id: str = ""
    as_of: UTCDateTime
    available_at: UTCDateTime
    symbol: str = Field(min_length=1)
    account: AccountState
    market: MarketState
    positions: PositionBookState
    orders: OrderBookState
    exposure: ExposureState
    broker_constraints: BrokerConstraints
    entry_price: FiniteFloat | None = Field(default=None, gt=0.0)
    stop_loss_price: FiniteFloat | None = Field(default=None, gt=0.0)
    estimated_margin_required: FiniteFloat | None = Field(default=None, gt=0.0)
    estimated_slippage_points: FiniteFloat | None = Field(default=None, ge=0.0)
    daily_drawdown_fraction: FiniteFloat = Field(ge=0.0, le=1.0)
    total_drawdown_fraction: FiniteFloat = Field(ge=0.0, le=1.0)
    kill_switch_active: bool

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> RiskContext:
        if self.available_at > self.as_of:
            raise ValueError("Risk context cannot be available after as_of")
        states = (
            self.account,
            self.market,
            self.positions,
            self.orders,
            self.exposure,
            self.broker_constraints,
        )
        if any(state.as_of > self.as_of for state in states):
            raise ValueError("Risk context cannot contain future state")
        if any(
            state.freshness.available_at is not None
            and state.freshness.available_at > self.as_of
            for state in states
        ):
            raise ValueError("Risk context cannot contain future availability")
        if self.market.symbol != self.symbol or self.broker_constraints.symbol != self.symbol:
            raise ValueError("Risk market and broker symbols must match context symbol")
        if any(position.symbol != self.symbol for position in self.positions.positions):
            raise ValueError("Risk positions must match context symbol")
        if any(order.symbol != self.symbol for order in self.orders.orders):
            raise ValueError("Risk orders must match context symbol")
        identity = self.model_dump(mode="json", exclude={"context_id"})
        expected = f"rc-{canonical_hash(identity)[:20]}"
        if self.context_id and self.context_id != expected:
            raise ValueError("context_id does not match Risk context content")
        object.__setattr__(self, "context_id", expected)
        return self


class RiskOutcome(RiskBoundaryModel):
    outcome_id: str = ""
    master_proposal_id: str = Field(min_length=1)
    evidence_bundle_id: str = Field(min_length=1)
    discipline_outcome_id: str = Field(min_length=1)
    discipline_result: DisciplineResult
    risk_policy_id: str = Field(min_length=1)
    risk_policy_version: str = Field(min_length=1)
    risk_context_id: str = Field(min_length=1)
    setup_id: str | None = None
    thesis_id: str | None = None
    scenario_id: str | None = None
    symbol: str = Field(min_length=1)
    as_of: UTCDateTime
    available_at: UTCDateTime
    master_decision: Signal
    result: RiskResult
    eligible_for_execution: bool
    reason_codes: tuple[RiskReason, ...] = Field(min_length=1)
    risk_fraction: float = Field(ge=0.0, le=1.0)
    risk_budget_amount: FiniteFloat | None = Field(default=None, gt=0.0)
    stop_distance_points: FiniteFloat | None = Field(default=None, gt=0.0)
    approved_volume_lots: FiniteFloat | None = Field(default=None, gt=0.0)
    projected_gross_lots: FiniteFloat | None = Field(default=None, ge=0.0)
    projected_net_lots: FiniteFloat | None = None
    estimated_margin_required: FiniteFloat | None = Field(default=None, gt=0.0)
    rationale: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> RiskOutcome:
        if self.available_at > self.as_of:
            raise ValueError("Risk outcome cannot be available after as_of")
        if self.eligible_for_execution != (self.result is RiskResult.PASS):
            raise ValueError("only PASS may remain eligible for future execution")
        sized = (
            self.risk_budget_amount,
            self.stop_distance_points,
            self.approved_volume_lots,
            self.projected_gross_lots,
            self.projected_net_lots,
            self.estimated_margin_required,
        )
        if self.result is RiskResult.PASS and any(value is None for value in sized):
            raise ValueError("PASS requires complete deterministic sizing output")
        if self.result is not RiskResult.PASS and any(value is not None for value in sized):
            raise ValueError("non-PASS outcomes cannot approve or project a trade")
        if self.result is RiskResult.NO_ACTION and (
            self.discipline_result is DisciplineResult.PASS
        ):
            raise ValueError("NO_ACTION requires a non-PASS Discipline outcome")
        emergency_reasons = {
            RiskReason.KILL_SWITCH,
            RiskReason.EMERGENCY_DAILY_DRAWDOWN,
            RiskReason.EMERGENCY_TOTAL_DRAWDOWN,
        }
        if self.result is RiskResult.EMERGENCY_STOP and not (
            set(self.reason_codes) & emergency_reasons
        ):
            raise ValueError("EMERGENCY_STOP requires an emergency reason")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("Risk reason codes must be unique")
        identity = self.model_dump(mode="json", exclude={"outcome_id"})
        expected = f"ro-{canonical_hash(identity)[:20]}"
        if self.outcome_id and self.outcome_id != expected:
            raise ValueError("outcome_id does not match Risk outcome content")
        object.__setattr__(self, "outcome_id", expected)
        return self
