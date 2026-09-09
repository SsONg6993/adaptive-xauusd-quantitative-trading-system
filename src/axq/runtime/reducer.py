"""Pure, validated reduction of runtime events into shared state."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from axq.runtime.clock import ensure_utc
from axq.runtime.events import RuntimeEvent, RuntimeEventType
from axq.runtime.state import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    EventCursor,
    ExecutionFeedbackState,
    ExecutionStatus,
    ExposureState,
    FreshnessStatus,
    MarketState,
    OrderBookState,
    PositionBookState,
    SharedRuntimeState,
    SlowContextState,
    SourceCursor,
)


def _unknown_freshness(component: str) -> ComponentFreshness:
    return ComponentFreshness(component=component, status=FreshnessStatus.UNKNOWN)


def initial_runtime_state(symbol: str, *, at: datetime) -> SharedRuntimeState:
    """Construct a canonical state with explicit unknown component values."""
    as_of = ensure_utc(at)
    freshness = tuple(
        _unknown_freshness(component)
        for component in (
            "market",
            "account",
            "positions",
            "orders",
            "exposure",
            "broker_constraints",
        )
    )
    by_component = {item.component: item for item in freshness}
    return SharedRuntimeState(
        as_of=as_of,
        market=MarketState(
            source="unknown",
            symbol=symbol,
            as_of=as_of,
            freshness=by_component["market"],
        ),
        account=AccountState(
            source="unknown",
            account_id="unknown",
            as_of=as_of,
            freshness=by_component["account"],
        ),
        positions=PositionBookState(
            source="unknown",
            as_of=as_of,
            freshness=by_component["positions"],
        ),
        orders=OrderBookState(
            source="unknown",
            as_of=as_of,
            freshness=by_component["orders"],
        ),
        exposure=ExposureState(
            as_of=as_of,
            freshness=by_component["exposure"],
        ),
        broker_constraints=BrokerConstraints(
            source="unknown",
            symbol=symbol,
            as_of=as_of,
            freshness=by_component["broker_constraints"],
        ),
        component_freshness=freshness,
    )


def _validate_payload(event: RuntimeEvent) -> None:
    expected: dict[RuntimeEventType, type[Any]] = {
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
    if not isinstance(event.payload, expected[event.event_type]):
        raise ValueError(f"payload does not match event type {event.event_type.value}")


def _source_cursor(state: SharedRuntimeState, source: str) -> SourceCursor | None:
    return next((cursor for cursor in state.source_cursors if cursor.source == source), None)


def _validate_order(state: SharedRuntimeState, event: RuntimeEvent) -> bool:
    cursor = _source_cursor(state, event.source)
    if cursor is not None:
        if cursor.source_sequence == event.source_sequence:
            if cursor.event_id == event.event_id:
                return False
            raise ValueError("source sequence collision")
        if event.source_sequence < cursor.source_sequence:
            raise ValueError("stale source sequence")
    if state.last_event is not None and event.ordering_key < (
        state.last_event.available_at,
        state.last_event.source_sequence,
        state.last_event.event_id,
    ):
        raise ValueError("event violates global event order")
    return True


_ACCOUNT_VALUE_FIELDS = (
    "currency",
    "balance",
    "equity",
    "free_margin",
    "used_margin",
    "margin_level",
    "floating_pnl",
    "daily_realized_pnl",
    "daily_unrealized_pnl",
    "daily_drawdown",
    "total_drawdown",
)


def _account_update(previous: AccountState, incoming: AccountState) -> AccountState:
    if incoming.freshness.status is not FreshnessStatus.STALE:
        return incoming
    data = incoming.model_dump(mode="python")
    for field in _ACCOUNT_VALUE_FIELDS:
        if data[field] is None:
            data[field] = getattr(previous, field)
    return AccountState.model_validate(data)


_EXECUTION_PROGRESS = {
    ExecutionStatus.SUBMITTED: 0,
    ExecutionStatus.ACCEPTED: 1,
    ExecutionStatus.PARTIALLY_FILLED: 2,
    ExecutionStatus.FILLED: 3,
    ExecutionStatus.CLOSED: 4,
}
_TERMINAL_EXECUTION_STATUSES = {
    ExecutionStatus.REJECTED,
    ExecutionStatus.CANCELLED,
    ExecutionStatus.EXPIRED,
    ExecutionStatus.FAILED,
    ExecutionStatus.CLOSED,
}


def _validate_execution_progress(
    previous: ExecutionFeedbackState | None,
    incoming: ExecutionFeedbackState,
) -> None:
    if previous is None or previous.instruction_id != incoming.instruction_id:
        return
    if previous.status in _TERMINAL_EXECUTION_STATUSES and incoming.status != previous.status:
        raise ValueError("execution feedback regression")
    previous_rank = _EXECUTION_PROGRESS.get(previous.status)
    incoming_rank = _EXECUTION_PROGRESS.get(incoming.status)
    if previous_rank is not None and (
        incoming_rank is None or incoming_rank < previous_rank
    ):
        raise ValueError("execution feedback regression")


def _updated_execution_feedback(
    state: SharedRuntimeState,
    incoming: ExecutionFeedbackState,
) -> tuple[ExecutionFeedbackState, ...]:
    values = {
        feedback.instruction_id: feedback for feedback in state.execution_feedback
    }
    previous = values.get(incoming.instruction_id)
    _validate_execution_progress(previous, incoming)
    values[incoming.instruction_id] = incoming
    return tuple(values[key] for key in sorted(values))


def _updated_freshness(
    state: SharedRuntimeState,
    component: ComponentFreshness,
) -> tuple[ComponentFreshness, ...]:
    values = {
        item.component: item
        for item in state.component_freshness
        if item.component != component.component
    }
    values[component.component] = component
    return tuple(values[key] for key in sorted(values))


def _updated_source_cursors(
    state: SharedRuntimeState,
    event: RuntimeEvent,
) -> tuple[SourceCursor, ...]:
    values = {cursor.source: cursor for cursor in state.source_cursors}
    values[event.source] = SourceCursor(
        source=event.source,
        source_sequence=event.source_sequence,
        event_id=event.event_id,
        available_at=event.available_at,
    )
    return tuple(values[key] for key in sorted(values))


def _updated_slow_context(
    state: SharedRuntimeState,
    incoming: SlowContextState,
) -> tuple[SlowContextState, ...]:
    values = {context.provider: context for context in state.slow_context}
    values[incoming.provider] = incoming
    return tuple(values[key] for key in sorted(values))


def reduce_state(
    previous: SharedRuntimeState,
    event: RuntimeEvent,
    *,
    now: datetime,
) -> SharedRuntimeState:
    """Apply one causally available event without consulting a wall clock."""
    reduction_time = ensure_utc(now)
    if reduction_time < event.available_at:
        raise ValueError("event is not yet available")
    _validate_payload(event)
    if not _validate_order(previous, event):
        return previous

    data = previous.model_dump(mode="python", exclude={"state_id"})
    component: ComponentFreshness | None = None
    if event.event_type in {
        RuntimeEventType.M5_CLOSED,
        RuntimeEventType.HTF_CLOSED,
        RuntimeEventType.TICK,
        RuntimeEventType.M1_CLOSED,
    }:
        market = MarketState.model_validate(event.payload)
        data["market"] = market
        component = market.freshness
    elif event.event_type is RuntimeEventType.ACCOUNT_UPDATED:
        account = AccountState.model_validate(event.payload)
        account = _account_update(previous.account, account)
        data["account"] = account
        component = account.freshness
    elif event.event_type is RuntimeEventType.POSITIONS_UPDATED:
        positions = PositionBookState.model_validate(event.payload)
        data["positions"] = positions
        component = positions.freshness
    elif event.event_type is RuntimeEventType.ORDERS_UPDATED:
        orders = OrderBookState.model_validate(event.payload)
        data["orders"] = orders
        component = orders.freshness
    elif event.event_type is RuntimeEventType.EXPOSURE_UPDATED:
        exposure = ExposureState.model_validate(event.payload)
        data["exposure"] = exposure
        component = exposure.freshness
    elif event.event_type is RuntimeEventType.BROKER_CONSTRAINTS_UPDATED:
        constraints = BrokerConstraints.model_validate(event.payload)
        data["broker_constraints"] = constraints
        component = constraints.freshness
    elif event.event_type is RuntimeEventType.EXECUTION_FEEDBACK:
        feedback = ExecutionFeedbackState.model_validate(event.payload)
        data["execution_feedback"] = _updated_execution_feedback(previous, feedback)
        data["latest_execution_feedback"] = feedback
    elif event.event_type is RuntimeEventType.SLOW_CONTEXT_UPDATED:
        context = SlowContextState.model_validate(event.payload)
        data["slow_context"] = _updated_slow_context(previous, context)

    if component is not None:
        data["component_freshness"] = _updated_freshness(previous, component)
    data["as_of"] = event.available_at
    data["source_cursors"] = _updated_source_cursors(previous, event)
    data["last_event"] = EventCursor(
        available_at=event.available_at,
        source_sequence=event.source_sequence,
        event_id=event.event_id,
    )
    data["recorded_at"] = reduction_time
    return SharedRuntimeState.model_validate(data)
