from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.runtime import (
    AccountState,
    ComponentFreshness,
    ExecutionFeedbackState,
    ExecutionStatus,
    FreshnessStatus,
    InMemoryEventSource,
    MarketState,
    OrderBookState,
    OrderState,
    OrderType,
    PositionBookState,
    PositionSide,
    PositionState,
    ReplayClock,
    RuntimeEvent,
    RuntimeEventType,
    SlowContextState,
    SystemUTCClock,
    initial_runtime_state,
    reduce_state,
)

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def fresh(component: str, at: datetime) -> ComponentFreshness:
    return ComponentFreshness(
        component=component,
        status=FreshnessStatus.AVAILABLE,
        observed_at=at,
        available_at=at,
        stale_after_ms=5_000,
    )


def market(price: float, at: datetime = T0) -> MarketState:
    return MarketState(
        source="mt5",
        symbol="XAUUSD",
        as_of=at,
        freshness=fresh("market", at),
        bid=price,
        ask=price + 0.2,
        last=price + 0.1,
        spread_points=20.0,
        base_timeframe="M5",
        completed_timeframes=("M5",),
    )


def account(
    equity: float | None,
    at: datetime = T0,
    status: FreshnessStatus = FreshnessStatus.AVAILABLE,
) -> AccountState:
    component = (
        fresh("account", at)
        if status is FreshnessStatus.AVAILABLE
        else ComponentFreshness(
            component="account",
            status=status,
            observed_at=at if status is FreshnessStatus.STALE else None,
            available_at=at if status is FreshnessStatus.STALE else None,
            stale_after_ms=5_000 if status is FreshnessStatus.STALE else None,
            reason="stale heartbeat" if status is FreshnessStatus.STALE else "not synchronized",
        )
    )
    known = status in {FreshnessStatus.AVAILABLE, FreshnessStatus.STALE}
    return AccountState(
        source="mt5",
        account_id="demo-123",
        as_of=at,
        freshness=component,
        currency="USD",
        balance=10_000.0 if known else None,
        equity=equity if known else None,
        free_margin=9_000.0 if known else None,
        used_margin=1_000.0 if known else None,
        floating_pnl=equity - 10_000.0 if equity is not None and known else None,
        daily_realized_pnl=0.0 if known else None,
    )


def positions(items: tuple[PositionState, ...], at: datetime = T0) -> PositionBookState:
    return PositionBookState(
        source="mt5", as_of=at, freshness=fresh("positions", at), positions=items
    )


def orders(items: tuple[OrderState, ...], at: datetime = T0) -> OrderBookState:
    return OrderBookState(source="mt5", as_of=at, freshness=fresh("orders", at), orders=items)


def position(ticket: int) -> PositionState:
    return PositionState(
        source="mt5",
        broker_ticket=ticket,
        symbol="XAUUSD",
        side=PositionSide.BUY,
        volume_lots=0.1,
        opened_at=T0,
        open_price=2500.0,
    )


def order(ticket: int) -> OrderState:
    return OrderState(
        source="mt5",
        broker_ticket=ticket,
        symbol="XAUUSD",
        order_type=OrderType.BUY_LIMIT,
        volume_lots=0.1,
        created_at=T0,
        price=2499.0,
    )


def feedback(
    status: ExecutionStatus,
    at: datetime,
    *,
    instruction_id: str = "instruction-1",
) -> ExecutionFeedbackState:
    return ExecutionFeedbackState(
        source="mt5",
        instruction_id=instruction_id,
        broker_ticket=1001,
        status=status,
        event_time=at,
        observed_at=at,
        requested_volume_lots=0.1,
        filled_volume_lots=0.1 if status is ExecutionStatus.FILLED else None,
    )


def event(
    event_type: RuntimeEventType,
    payload: object,
    sequence: int,
    *,
    event_time: datetime = T0,
    observed_at: datetime | None = None,
    available_at: datetime | None = None,
    ingested_at: datetime | None = None,
    source: str = "mt5",
) -> RuntimeEvent:
    observed = observed_at or event_time
    available = available_at or observed
    return RuntimeEvent(
        event_type=event_type,
        event_time=event_time,
        observed_at=observed,
        available_at=available,
        ingested_at=ingested_at,
        source=source,
        source_version="1.0",
        source_sequence=sequence,
        symbol="XAUUSD",
        payload=payload,  # type: ignore[arg-type]
    )


def apply(events: list[RuntimeEvent], *, replay: bool) -> str:
    state = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    source = InMemoryEventSource(events)
    if replay:
        clock = ReplayClock(T0 - timedelta(seconds=1))
        for item in source.events():
            clock.advance_to(item.available_at)
            state = reduce_state(state, item, now=clock.now())
    else:
        clock = SystemUTCClock()
        for item in source.events():
            state = reduce_state(state, item, now=clock.now())
    return state.state_id


def test_event_source_uses_canonical_deterministic_order() -> None:
    late = event(RuntimeEventType.M5_CLOSED, market(2501.0, T0 + timedelta(seconds=2)), 3,
                 event_time=T0 + timedelta(seconds=2))
    first = event(RuntimeEventType.M5_CLOSED, market(2499.0), 1)
    tied = event(RuntimeEventType.M5_CLOSED, market(2500.0), 2)

    result = list(InMemoryEventSource([late, tied, first]).events())
    assert result == sorted(result, key=lambda item: item.ordering_key)


def test_replay_clock_advances_deterministically_and_rejects_backwards_time() -> None:
    clock = ReplayClock(T0)
    clock.advance_to(T0 + timedelta(seconds=2))
    assert clock.now() == T0 + timedelta(seconds=2)
    clock.advance_to(T0 + timedelta(seconds=2))
    with pytest.raises(ValueError, match="backwards"):
        clock.advance_to(T0 + timedelta(seconds=1))
    with pytest.raises(ValueError, match="timezone-aware"):
        ReplayClock(datetime(2025, 1, 6, 12, 0))


def test_live_and_replay_use_same_reducer_and_produce_same_identity() -> None:
    events = [
        event(RuntimeEventType.M5_CLOSED, market(2500.0), 1),
        event(RuntimeEventType.ACCOUNT_UPDATED, account(10_050.0), 2),
    ]
    assert apply(events, replay=False) == apply(events, replay=True)


def test_exact_duplicate_is_an_identity_preserving_noop() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    update = event(RuntimeEventType.M5_CLOSED, market(2500.0), 1)
    applied = reduce_state(initial, update, now=T0)
    duplicate = reduce_state(applied, update, now=T0 + timedelta(seconds=1))
    assert duplicate is applied
    assert duplicate.state_id == applied.state_id


def test_reducer_rejects_payload_mismatch_that_bypassed_event_validation() -> None:
    invalid = RuntimeEvent.model_construct(
        event_id="ev-invalid",
        event_type=RuntimeEventType.ACCOUNT_UPDATED,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
        source="mt5",
        source_version="1.0",
        source_sequence=1,
        symbol="XAUUSD",
        payload=market(2500.0),
    )
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    with pytest.raises(ValueError, match="payload does not match"):
        reduce_state(initial, invalid, now=T0)


def test_stale_source_sequence_and_sequence_collision_are_rejected() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    applied = reduce_state(initial, event(RuntimeEventType.M5_CLOSED, market(2500.0), 2), now=T0)
    with pytest.raises(ValueError, match="stale source sequence"):
        reduce_state(
            applied,
            event(RuntimeEventType.M5_CLOSED, market(2499.0), 1),
            now=T0,
        )
    with pytest.raises(ValueError, match="sequence collision"):
        reduce_state(
            applied,
            event(RuntimeEventType.M5_CLOSED, market(2502.0), 2),
            now=T0,
        )


def test_globally_earlier_availability_is_rejected() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    later = event(
        RuntimeEventType.ACCOUNT_UPDATED,
        account(10_000.0, T0 + timedelta(seconds=2)),
        1,
        event_time=T0 + timedelta(seconds=2),
        available_at=T0 + timedelta(seconds=2),
        source="account",
    )
    applied = reduce_state(initial, later, now=T0 + timedelta(seconds=2))
    earlier = event(
        RuntimeEventType.M5_CLOSED,
        market(2500.0, T0 + timedelta(seconds=1)),
        10,
        event_time=T0 + timedelta(seconds=1),
        available_at=T0 + timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="global event order"):
        reduce_state(applied, earlier, now=T0 + timedelta(seconds=3))


def test_older_event_time_is_accepted_when_causally_available_later() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    first = event(RuntimeEventType.M5_CLOSED, market(2500.0), 1)
    state = reduce_state(initial, first, now=T0)
    delayed_at = T0 + timedelta(seconds=5)
    delayed = event(
        RuntimeEventType.ACCOUNT_UPDATED,
        account(10_050.0, T0 - timedelta(seconds=10)),
        2,
        event_time=T0 - timedelta(seconds=10),
        observed_at=T0 - timedelta(seconds=9),
        available_at=delayed_at,
    )
    updated = reduce_state(state, delayed, now=delayed_at)
    assert updated.account.equity == 10_050.0
    assert updated.as_of == delayed_at


def test_market_and_account_updates_replace_their_typed_components() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    with_market = reduce_state(
        initial, event(RuntimeEventType.M5_CLOSED, market(2500.0), 1), now=T0
    )
    complete = reduce_state(
        with_market, event(RuntimeEventType.ACCOUNT_UPDATED, account(10_050.0), 2), now=T0
    )
    assert complete.market.bid == 2500.0
    assert complete.account.equity == 10_050.0


def test_stale_account_retains_known_values_but_unknown_does_not() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    known = reduce_state(
        initial, event(RuntimeEventType.ACCOUNT_UPDATED, account(10_050.0), 1), now=T0
    )
    stale_at = T0 + timedelta(seconds=2)
    stale_payload = account(None, stale_at, FreshnessStatus.STALE)
    stale = reduce_state(
        known,
        event(
            RuntimeEventType.ACCOUNT_UPDATED,
            stale_payload,
            2,
            event_time=stale_at,
            available_at=stale_at,
        ),
        now=stale_at,
    )
    assert stale.account.equity == 10_050.0
    assert stale.account.freshness.status is FreshnessStatus.STALE

    unknown_at = T0 + timedelta(seconds=3)
    unknown = reduce_state(
        stale,
        event(
            RuntimeEventType.ACCOUNT_UPDATED,
            account(None, unknown_at, FreshnessStatus.UNKNOWN),
            3,
            event_time=unknown_at,
            available_at=unknown_at,
        ),
        now=unknown_at,
    )
    assert unknown.account.equity is None


def test_position_and_order_updates_are_authoritative_full_snapshots() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    one_position = reduce_state(
        initial,
        event(RuntimeEventType.POSITIONS_UPDATED, positions((position(11),)), 1),
        now=T0,
    )
    no_positions = reduce_state(
        one_position,
        event(RuntimeEventType.POSITIONS_UPDATED, positions((), T0 + timedelta(seconds=1)), 2,
              event_time=T0 + timedelta(seconds=1)),
        now=T0 + timedelta(seconds=1),
    )
    assert no_positions.positions.positions == ()

    one_order = reduce_state(
        no_positions,
        event(RuntimeEventType.ORDERS_UPDATED, orders((order(21),), T0 + timedelta(seconds=2)), 3,
              event_time=T0 + timedelta(seconds=2)),
        now=T0 + timedelta(seconds=2),
    )
    no_orders = reduce_state(
        one_order,
        event(RuntimeEventType.ORDERS_UPDATED, orders((), T0 + timedelta(seconds=3)), 4,
              event_time=T0 + timedelta(seconds=3)),
        now=T0 + timedelta(seconds=3),
    )
    assert no_orders.orders.orders == ()


def test_late_execution_ack_cannot_regress_newer_feedback() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    filled = reduce_state(
        initial,
        event(RuntimeEventType.EXECUTION_FEEDBACK, feedback(ExecutionStatus.FILLED, T0), 1),
        now=T0,
    )
    later = T0 + timedelta(seconds=1)
    late_ack = event(
        RuntimeEventType.EXECUTION_FEEDBACK,
        feedback(ExecutionStatus.ACCEPTED, later),
        2,
        event_time=later,
    )
    with pytest.raises(ValueError, match="execution feedback regression"):
        reduce_state(filled, late_ack, now=later)


def test_execution_feedback_retains_and_validates_each_instruction() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    first = reduce_state(
        initial,
        event(RuntimeEventType.EXECUTION_FEEDBACK, feedback(ExecutionStatus.FILLED, T0), 1),
        now=T0,
    )
    second_at = T0 + timedelta(seconds=1)
    second = reduce_state(
        first,
        event(
            RuntimeEventType.EXECUTION_FEEDBACK,
            feedback(
                ExecutionStatus.ACCEPTED,
                second_at,
                instruction_id="instruction-2",
            ),
            2,
            event_time=second_at,
        ),
        now=second_at,
    )
    assert tuple(item.instruction_id for item in second.execution_feedback) == (
        "instruction-1",
        "instruction-2",
    )

    regression_at = T0 + timedelta(seconds=2)
    with pytest.raises(ValueError, match="execution feedback regression"):
        reduce_state(
            second,
            event(
                RuntimeEventType.EXECUTION_FEEDBACK,
                feedback(ExecutionStatus.ACCEPTED, regression_at),
                3,
                event_time=regression_at,
            ),
            now=regression_at,
        )


def test_slow_context_uses_availability_not_older_effective_time() -> None:
    initial = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    available = T0 + timedelta(minutes=2)
    context = SlowContextState(
        provider="calendar",
        context_version="calendar-v1",
        effective_at=T0 - timedelta(hours=1),
        expires_at=T0 + timedelta(hours=1),
        content_hash="sha256-example",
    )
    delayed = event(
        RuntimeEventType.SLOW_CONTEXT_UPDATED,
        context,
        1,
        event_time=T0 - timedelta(hours=1),
        observed_at=T0 - timedelta(minutes=30),
        available_at=available,
        source="calendar",
    )
    with pytest.raises(ValueError, match="not yet available"):
        reduce_state(initial, delayed, now=available - timedelta(microseconds=1))
    updated = reduce_state(initial, delayed, now=available)
    assert updated.as_of == available
    assert updated.slow_context == (context,)


def test_equivalent_streams_ignore_ingestion_time_in_final_identity() -> None:
    first = event(
        RuntimeEventType.M5_CLOSED,
        market(2500.0),
        1,
        ingested_at=T0 + timedelta(seconds=1),
    )
    second = event(
        RuntimeEventType.M5_CLOSED,
        market(2500.0),
        1,
        ingested_at=T0 + timedelta(seconds=9),
    )
    assert first.event_id == second.event_id
    assert apply([first], replay=True) == apply([second], replay=True)
