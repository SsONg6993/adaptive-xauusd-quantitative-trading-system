"""Dedicated append-only transport contracts for safe position actions."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.execution_boundary import ExecutionReason, ExecutionResultStatus
from axq.position_actions.contracts import PositionActionIntent, PositionActionType
from axq.runtime import (
    ExecutionFeedbackState,
    ExecutionStatus,
    PositionSide,
    RuntimeEvent,
    RuntimeEventType,
)
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class PositionActionTransportResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    result_id: str = ""
    position_action_intent_id: str = Field(min_length=1)
    action_type: PositionActionType
    position_id: str = Field(min_length=1)
    broker_ticket: int = Field(gt=0)
    symbol: str = Field(min_length=1)
    position_side: PositionSide
    status: ExecutionResultStatus
    reason_code: ExecutionReason | None = None
    reason: str | None = Field(default=None, max_length=500)
    requested_volume_lots: FiniteFloat | None = Field(default=None, gt=0.0)
    executed_volume_lots: FiniteFloat | None = Field(default=None, ge=0.0)
    requested_stop_loss: FiniteFloat | None = Field(default=None, gt=0.0)
    fill_price: FiniteFloat | None = Field(default=None, gt=0.0)
    transport_execution_id: str | None = Field(default=None, min_length=1)
    broker_retcode: str | None = None
    broker_status: str | None = None
    event_time: UTCDateTime
    observed_at: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PositionActionTransportResult:
        if not self.event_time <= self.observed_at <= self.available_at:
            raise ValueError("position-action result timestamps must be causally ordered")
        if self.status is ExecutionResultStatus.UNKNOWN:
            if self.executed_volume_lots is not None:
                raise ValueError("UNKNOWN position action cannot claim executed volume")
        elif self.status in {
            ExecutionResultStatus.NO_ACTION,
            ExecutionResultStatus.REJECTED,
            ExecutionResultStatus.FAILED,
        } and self.reason_code is None:
            raise ValueError("non-success position action requires a reason code")
        if self.action_type is PositionActionType.CLOSE_POSITION:
            if self.requested_volume_lots is None:
                raise ValueError("close result requires requested volume")
            if self.status is ExecutionResultStatus.FILLED and not math.isclose(
                self.executed_volume_lots or 0.0,
                self.requested_volume_lots,
                abs_tol=1e-10,
                rel_tol=0.0,
            ):
                raise ValueError("filled close must fill the requested volume")
            if self.status is ExecutionResultStatus.PARTIALLY_FILLED and not (
                0.0 < (self.executed_volume_lots or 0.0) < self.requested_volume_lots
            ):
                raise ValueError("partial close requires strict partial volume")
        elif self.requested_volume_lots is not None or self.executed_volume_lots is not None:
            raise ValueError("protective-stop result cannot claim traded volume")
        identity = self.model_dump(mode="json", exclude={"result_id"})
        expected = f"patr-{canonical_hash(identity)[:20]}"
        if self.result_id and self.result_id != expected:
            raise ValueError("result_id does not match position-action result content")
        object.__setattr__(self, "result_id", expected)
        return self


class PositionActionTransportTransitionType(StrEnum):
    RESERVED = "RESERVED"
    RESULT_RECORDED = "RESULT_RECORDED"


class PositionActionTransportTransition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    transition_id: str = ""
    transition_type: PositionActionTransportTransitionType
    intent_id: str = Field(min_length=1)
    intent: PositionActionIntent | None = None
    result: PositionActionTransportResult | None = None
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PositionActionTransportTransition:
        if self.transition_type is PositionActionTransportTransitionType.RESERVED:
            if self.intent is None or self.result is not None:
                raise ValueError("reservation requires only an intent")
        elif self.result is None or self.intent is not None:
            raise ValueError("result transition requires only a result")
        identity = self.model_dump(mode="json", exclude={"transition_id"})
        expected = f"patt-{canonical_hash(identity)[:20]}"
        if self.transition_id and self.transition_id != expected:
            raise ValueError("transition_id does not match transition content")
        object.__setattr__(self, "transition_id", expected)
        return self


class PositionActionTransportLedger(Protocol):
    def get(self, intent_id: str) -> PositionActionTransportResult | None: ...
    def reserve(self, intent: PositionActionIntent) -> bool: ...
    def record(self, result: PositionActionTransportResult) -> None: ...
    def requires_reconciliation(self, intent_id: str) -> bool: ...


class InMemoryPositionActionTransportLedger:
    def __init__(self) -> None:
        self._reserved: set[str] = set()
        self._results: dict[str, PositionActionTransportResult] = {}

    def get(self, intent_id: str) -> PositionActionTransportResult | None:
        return self._results.get(intent_id)

    def reserve(self, intent: PositionActionIntent) -> bool:
        if intent.intent_id in self._reserved:
            return False
        self._reserved.add(intent.intent_id)
        return True

    def record(self, result: PositionActionTransportResult) -> None:
        if result.position_action_intent_id not in self._reserved:
            raise ValueError("position-action intent must be reserved before recording")
        prior = self.get(result.position_action_intent_id)
        if prior is not None and prior != result:
            raise ValueError("position-action intent already has a different result")
        self._results[result.position_action_intent_id] = result

    def requires_reconciliation(self, intent_id: str) -> bool:
        result = self.get(intent_id)
        return intent_id in self._reserved and (
            result is None or result.status is ExecutionResultStatus.UNKNOWN
        )


_STATUS_MAP = {
    ExecutionResultStatus.ACCEPTED: ExecutionStatus.ACCEPTED,
    ExecutionResultStatus.PARTIALLY_FILLED: ExecutionStatus.PARTIALLY_FILLED,
    ExecutionResultStatus.FILLED: ExecutionStatus.CLOSED,
    ExecutionResultStatus.REJECTED: ExecutionStatus.REJECTED,
    ExecutionResultStatus.FAILED: ExecutionStatus.FAILED,
    ExecutionResultStatus.UNKNOWN: ExecutionStatus.UNKNOWN,
}


def position_action_result_to_runtime_event(
    result: PositionActionTransportResult,
    *,
    source: str,
    source_version: str,
    source_sequence: int,
) -> RuntimeEvent | None:
    if result.status is ExecutionResultStatus.NO_ACTION:
        return None
    status = _STATUS_MAP[result.status]
    if result.action_type is PositionActionType.MODIFY_PROTECTIVE_STOP and (
        result.status is ExecutionResultStatus.FILLED
    ):
        status = ExecutionStatus.ACCEPTED
    feedback = ExecutionFeedbackState(
        source=source,
        instruction_id=result.position_action_intent_id,
        broker_ticket=result.broker_ticket,
        replay_execution_id=result.transport_execution_id,
        status=status,
        event_time=result.event_time,
        observed_at=result.observed_at,
        requested_volume_lots=result.requested_volume_lots,
        filled_volume_lots=result.executed_volume_lots,
        requested_price=result.requested_stop_loss,
        fill_price=result.fill_price,
        broker_code=result.broker_retcode,
        broker_message=result.reason or result.broker_status,
    )
    return RuntimeEvent(
        event_type=RuntimeEventType.EXECUTION_FEEDBACK,
        event_time=result.event_time,
        observed_at=result.observed_at,
        available_at=result.available_at,
        source=source,
        source_version=source_version,
        source_sequence=source_sequence,
        symbol=result.symbol,
        payload=feedback,
    )
