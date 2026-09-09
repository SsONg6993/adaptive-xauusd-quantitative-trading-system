"""Canonical runtime event envelopes for live and deterministic replay."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.runtime.state import (
    AccountState,
    BrokerConstraints,
    ExecutionFeedbackState,
    ExposureState,
    MarketState,
    OrderBookState,
    PositionBookState,
    SlowContextState,
    UTCDateTime,
)
from axq.versioning import canonical_hash


class RuntimeEventType(StrEnum):
    M5_CLOSED = "M5_CLOSED"
    HTF_CLOSED = "HTF_CLOSED"
    TICK = "TICK"
    M1_CLOSED = "M1_CLOSED"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    POSITIONS_UPDATED = "POSITIONS_UPDATED"
    ORDERS_UPDATED = "ORDERS_UPDATED"
    EXPOSURE_UPDATED = "EXPOSURE_UPDATED"
    BROKER_CONSTRAINTS_UPDATED = "BROKER_CONSTRAINTS_UPDATED"
    EXECUTION_FEEDBACK = "EXECUTION_FEEDBACK"
    SLOW_CONTEXT_UPDATED = "SLOW_CONTEXT_UPDATED"


EventPayload = (
    MarketState
    | AccountState
    | PositionBookState
    | OrderBookState
    | ExposureState
    | BrokerConstraints
    | ExecutionFeedbackState
    | SlowContextState
)


class RuntimeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    event_id: str = ""
    event_type: RuntimeEventType
    event_time: UTCDateTime
    observed_at: UTCDateTime
    available_at: UTCDateTime
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    source_sequence: int = Field(ge=0)
    symbol: str | None = None
    payload: EventPayload
    ingested_at: UTCDateTime | None = None

    @model_validator(mode="after")
    def validate_event(self) -> RuntimeEvent:
        if not self.event_time <= self.observed_at <= self.available_at:
            raise ValueError(
                "event timestamps must satisfy event_time <= observed_at <= available_at"
            )
        if self.ingested_at is not None and self.ingested_at < self.available_at:
            raise ValueError("ingested_at must not precede available_at")
        expected: dict[RuntimeEventType, type[BaseModel]] = {
            RuntimeEventType.M5_CLOSED: MarketState,
            RuntimeEventType.HTF_CLOSED: MarketState,
            RuntimeEventType.TICK: MarketState,
            RuntimeEventType.M1_CLOSED: MarketState,
            RuntimeEventType.ACCOUNT_UPDATED: AccountState,
            RuntimeEventType.POSITIONS_UPDATED: PositionBookState,
            RuntimeEventType.ORDERS_UPDATED: OrderBookState,
            RuntimeEventType.EXPOSURE_UPDATED: ExposureState,
            RuntimeEventType.BROKER_CONSTRAINTS_UPDATED: BrokerConstraints,
            RuntimeEventType.EXECUTION_FEEDBACK: ExecutionFeedbackState,
            RuntimeEventType.SLOW_CONTEXT_UPDATED: SlowContextState,
        }
        if not isinstance(self.payload, expected[self.event_type]):
            raise ValueError(f"payload does not match event type {self.event_type.value}")
        identity = self.model_dump(mode="json", exclude={"event_id", "ingested_at"})
        expected_id = f"ev-{canonical_hash(identity)[:20]}"
        if self.event_id and self.event_id != expected_id:
            raise ValueError("event_id does not match event content")
        object.__setattr__(self, "event_id", expected_id)
        return self

    @property
    def ordering_key(self) -> tuple[datetime, int, str]:
        return (self.available_at, self.source_sequence, self.event_id)
