"""Bridge typed execution results into the shared Phase 6 runtime path."""

from __future__ import annotations

from axq.execution_boundary.contracts import ExecutionResult, ExecutionResultStatus
from axq.runtime import (
    ExecutionFeedbackState,
    ExecutionStatus,
    RuntimeEvent,
    RuntimeEventType,
)

_STATUS_MAP = {
    ExecutionResultStatus.SUBMITTED: ExecutionStatus.SUBMITTED,
    ExecutionResultStatus.ACCEPTED: ExecutionStatus.ACCEPTED,
    ExecutionResultStatus.PARTIALLY_FILLED: ExecutionStatus.PARTIALLY_FILLED,
    ExecutionResultStatus.FILLED: ExecutionStatus.FILLED,
    ExecutionResultStatus.REJECTED: ExecutionStatus.REJECTED,
    ExecutionResultStatus.CANCELLED: ExecutionStatus.CANCELLED,
    ExecutionResultStatus.EXPIRED: ExecutionStatus.EXPIRED,
    ExecutionResultStatus.FAILED: ExecutionStatus.FAILED,
    ExecutionResultStatus.UNKNOWN: ExecutionStatus.UNKNOWN,
}


def execution_result_to_runtime_event(
    result: ExecutionResult,
    *,
    source: str,
    source_version: str,
    source_sequence: int,
) -> RuntimeEvent | None:
    """Convert actionable execution feedback; local NO_ACTION stays local."""
    if result.status is ExecutionResultStatus.NO_ACTION:
        return None
    feedback = ExecutionFeedbackState(
        source=source,
        instruction_id=result.execution_intent_id,
        broker_ticket=result.broker_ticket,
        replay_execution_id=result.transport_execution_id,
        status=_STATUS_MAP[result.status],
        event_time=result.event_time,
        observed_at=result.observed_at,
        requested_volume_lots=result.requested_volume_lots,
        filled_volume_lots=result.filled_volume_lots,
        requested_price=result.requested_price,
        fill_price=result.fill_price,
        spread_points=result.actual_spread_points,
        slippage_points=result.realized_slippage_points,
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
