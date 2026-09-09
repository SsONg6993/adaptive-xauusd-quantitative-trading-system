"""Canonical, serializable shared runtime-state contracts."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from axq.versioning import canonical_hash


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("financial values must be finite")
    return value


UTCDateTime = Annotated[datetime, AfterValidator(_as_utc)]
FiniteFloat = Annotated[float, AfterValidator(_finite)]


class RuntimeStateModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class FreshnessStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    AVAILABLE = "AVAILABLE"


class ComponentFreshness(RuntimeStateModel):
    component: str = Field(min_length=1)
    status: FreshnessStatus
    observed_at: UTCDateTime | None = None
    available_at: UTCDateTime | None = None
    stale_after_ms: int | None = Field(default=None, gt=0)
    reason: str | None = None

    @model_validator(mode="after")
    def validate_timing(self) -> ComponentFreshness:
        if (self.observed_at is None) != (self.available_at is None):
            raise ValueError("observed_at and available_at must be supplied together")
        if (
            self.observed_at is not None
            and self.available_at is not None
            and self.available_at < self.observed_at
        ):
            raise ValueError("available_at must not precede observed_at")
        if (
            self.status in {FreshnessStatus.AVAILABLE, FreshnessStatus.STALE}
            and self.observed_at is None
        ):
            raise ValueError("available or stale state requires observation timestamps")
        if self.status is FreshnessStatus.UNAVAILABLE and not self.reason:
            raise ValueError("unavailable state requires a reason")
        return self


class MarketState(RuntimeStateModel):
    source: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    as_of: UTCDateTime
    freshness: ComponentFreshness
    bid: FiniteFloat | None = Field(default=None, gt=0)
    ask: FiniteFloat | None = Field(default=None, gt=0)
    last: FiniteFloat | None = Field(default=None, gt=0)
    spread_points: FiniteFloat | None = Field(default=None, ge=0)
    base_timeframe: str | None = None
    completed_timeframes: tuple[str, ...] = ()
    feature_manifest_id: str | None = None
    market_data_version: str | None = None

    @model_validator(mode="after")
    def validate_unknown_values(self) -> MarketState:
        values = (self.bid, self.ask, self.last, self.spread_points)
        if self.freshness.status in {
            FreshnessStatus.UNKNOWN,
            FreshnessStatus.UNAVAILABLE,
        } and any(value is not None for value in values):
            raise ValueError("unknown or unavailable market state cannot contain measurements")
        if self.bid is not None and self.ask is not None and self.ask < self.bid:
            raise ValueError("ask must not be below bid")
        return self


class AccountState(RuntimeStateModel):
    source: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    as_of: UTCDateTime
    freshness: ComponentFreshness
    currency: str | None = None
    balance: FiniteFloat | None = Field(default=None, ge=0)
    equity: FiniteFloat | None = Field(default=None, ge=0)
    free_margin: FiniteFloat | None = None
    used_margin: FiniteFloat | None = Field(default=None, ge=0)
    margin_level: FiniteFloat | None = Field(default=None, ge=0)
    floating_pnl: FiniteFloat | None = None
    daily_realized_pnl: FiniteFloat | None = None
    daily_unrealized_pnl: FiniteFloat | None = None
    daily_drawdown: FiniteFloat | None = Field(default=None, ge=0)
    total_drawdown: FiniteFloat | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_unknown_values(self) -> AccountState:
        values = (
            self.balance,
            self.equity,
            self.free_margin,
            self.used_margin,
            self.margin_level,
            self.floating_pnl,
            self.daily_realized_pnl,
            self.daily_unrealized_pnl,
            self.daily_drawdown,
            self.total_drawdown,
        )
        if self.freshness.status in {
            FreshnessStatus.UNKNOWN,
            FreshnessStatus.UNAVAILABLE,
        } and any(value is not None for value in values):
            raise ValueError("unknown or unavailable account state cannot contain measurements")
        return self


class PositionSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class PositionState(RuntimeStateModel):
    position_id: str = ""
    source: str = Field(min_length=1)
    broker_ticket: int | None = Field(default=None, gt=0)
    replay_position_id: str | None = None
    symbol: str = Field(min_length=1)
    side: PositionSide
    volume_lots: FiniteFloat = Field(gt=0)
    opened_at: UTCDateTime
    open_price: FiniteFloat = Field(gt=0)
    current_price: FiniteFloat | None = Field(default=None, gt=0)
    stop_loss: FiniteFloat | None = Field(default=None, gt=0)
    take_profit: FiniteFloat | None = Field(default=None, gt=0)
    floating_pnl: FiniteFloat | None = None
    commission: FiniteFloat | None = None
    swap: FiniteFloat | None = None
    setup_id: str | None = None
    thesis_id: str | None = None

    @model_validator(mode="after")
    def require_external_identity(self) -> PositionState:
        if self.broker_ticket is None and not self.replay_position_id:
            raise ValueError("broker_ticket or replay_position_id is required")
        identity = self.model_dump(mode="json", exclude={"position_id"})
        expected = f"pos-{canonical_hash(identity)[:20]}"
        if self.position_id and self.position_id != expected:
            raise ValueError("position_id does not match position content")
        object.__setattr__(self, "position_id", expected)
        return self


class OrderType(StrEnum):
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"
    BUY_STOP_LIMIT = "BUY_STOP_LIMIT"
    SELL_STOP_LIMIT = "SELL_STOP_LIMIT"


class OrderState(RuntimeStateModel):
    order_id: str = ""
    source: str = Field(min_length=1)
    broker_ticket: int | None = Field(default=None, gt=0)
    replay_order_id: str | None = None
    symbol: str = Field(min_length=1)
    order_type: OrderType
    volume_lots: FiniteFloat = Field(gt=0)
    created_at: UTCDateTime
    price: FiniteFloat = Field(gt=0)
    stop_loss: FiniteFloat | None = Field(default=None, gt=0)
    take_profit: FiniteFloat | None = Field(default=None, gt=0)
    expires_at: UTCDateTime | None = None
    setup_id: str | None = None
    thesis_id: str | None = None

    @model_validator(mode="after")
    def validate_order(self) -> OrderState:
        if self.broker_ticket is None and not self.replay_order_id:
            raise ValueError("broker_ticket or replay_order_id is required")
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must follow created_at")
        expected = f"ord-{canonical_hash(self.model_dump(mode='json', exclude={'order_id'}))[:20]}"
        if self.order_id and self.order_id != expected:
            raise ValueError("order_id does not match order content")
        object.__setattr__(self, "order_id", expected)
        return self


class PositionBookState(RuntimeStateModel):
    source: str = Field(min_length=1)
    as_of: UTCDateTime
    freshness: ComponentFreshness
    positions: tuple[PositionState, ...] = ()


class OrderBookState(RuntimeStateModel):
    source: str = Field(min_length=1)
    as_of: UTCDateTime
    freshness: ComponentFreshness
    orders: tuple[OrderState, ...] = ()


class ExposureState(RuntimeStateModel):
    as_of: UTCDateTime
    freshness: ComponentFreshness
    gross_lots: FiniteFloat | None = Field(default=None, ge=0)
    net_lots: FiniteFloat | None = None
    gross_notional: FiniteFloat | None = Field(default=None, ge=0)
    net_notional: FiniteFloat | None = None

    @model_validator(mode="after")
    def validate_unknown_values(self) -> ExposureState:
        values = (self.gross_lots, self.net_lots, self.gross_notional, self.net_notional)
        if self.freshness.status in {
            FreshnessStatus.UNKNOWN,
            FreshnessStatus.UNAVAILABLE,
        } and any(value is not None for value in values):
            raise ValueError(
                "unknown or unavailable exposure state cannot contain measurements"
            )
        return self


class BrokerConstraints(RuntimeStateModel):
    source: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    as_of: UTCDateTime
    freshness: ComponentFreshness
    trade_allowed: bool | None = None
    volume_min: FiniteFloat | None = Field(default=None, gt=0)
    volume_max: FiniteFloat | None = Field(default=None, gt=0)
    volume_step: FiniteFloat | None = Field(default=None, gt=0)
    point_size: FiniteFloat | None = Field(default=None, gt=0)
    tick_size: FiniteFloat | None = Field(default=None, gt=0)
    tick_value_loss: FiniteFloat | None = Field(default=None, gt=0)
    stops_level_points: FiniteFloat | None = Field(default=None, ge=0)
    freeze_level_points: FiniteFloat | None = Field(default=None, ge=0)


class ExecutionStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"


class ExecutionFeedbackState(RuntimeStateModel):
    feedback_id: str = ""
    source: str = Field(min_length=1)
    instruction_id: str = Field(min_length=1)
    broker_ticket: int | None = Field(default=None, gt=0)
    replay_execution_id: str | None = None
    status: ExecutionStatus
    event_time: UTCDateTime
    observed_at: UTCDateTime
    requested_volume_lots: FiniteFloat | None = Field(default=None, gt=0)
    filled_volume_lots: FiniteFloat | None = Field(default=None, ge=0)
    requested_price: FiniteFloat | None = Field(default=None, gt=0)
    fill_price: FiniteFloat | None = Field(default=None, gt=0)
    slippage_points: FiniteFloat | None = None
    commission: FiniteFloat | None = None
    swap: FiniteFloat | None = None
    broker_code: str | None = None
    broker_message: str | None = None

    @model_validator(mode="after")
    def validate_timing(self) -> ExecutionFeedbackState:
        if self.observed_at < self.event_time:
            raise ValueError("observed_at must not precede event_time")
        identity = self.model_dump(mode="json", exclude={"feedback_id"})
        expected = f"xfb-{canonical_hash(identity)[:20]}"
        if self.feedback_id and self.feedback_id != expected:
            raise ValueError("feedback_id does not match execution feedback content")
        object.__setattr__(self, "feedback_id", expected)
        return self


class SlowContextState(RuntimeStateModel):
    provider: str = Field(min_length=1)
    context_version: str = Field(min_length=1)
    effective_at: UTCDateTime
    expires_at: UTCDateTime
    content_hash: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_expiry(self) -> SlowContextState:
        if self.expires_at <= self.effective_at:
            raise ValueError("expires_at must follow effective_at")
        return self


class SourceCursor(RuntimeStateModel):
    source: str = Field(min_length=1)
    source_sequence: int = Field(ge=0)
    event_id: str | None = Field(default=None, min_length=1)
    available_at: UTCDateTime | None = None


class EventCursor(RuntimeStateModel):
    available_at: UTCDateTime
    source_sequence: int = Field(ge=0)
    event_id: str = Field(min_length=1)


class SharedRuntimeState(RuntimeStateModel):
    state_id: str = ""
    as_of: UTCDateTime
    market: MarketState
    account: AccountState
    positions: PositionBookState
    orders: OrderBookState
    exposure: ExposureState
    broker_constraints: BrokerConstraints
    component_freshness: tuple[ComponentFreshness, ...]
    source_cursors: tuple[SourceCursor, ...] = ()
    last_event: EventCursor | None = None
    execution_feedback: tuple[ExecutionFeedbackState, ...] = ()
    latest_execution_feedback: ExecutionFeedbackState | None = None
    slow_context: tuple[SlowContextState, ...] = ()
    recorded_at: UTCDateTime | None = None

    @model_validator(mode="after")
    def bind_identity(self) -> SharedRuntimeState:
        identity = self.model_dump(mode="json", exclude={"state_id", "recorded_at"})
        expected = f"state-{canonical_hash(identity)[:20]}"
        if self.state_id and self.state_id != expected:
            raise ValueError("state_id does not match runtime state content")
        object.__setattr__(self, "state_id", expected)
        return self
