from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    ExecutionFeedbackState,
    ExecutionStatus,
    ExposureState,
    FreshnessStatus,
    MarketState,
    OrderBookState,
    OrderState,
    OrderType,
    PositionBookState,
    PositionSide,
    PositionState,
    RuntimeEvent,
    RuntimeEventType,
    SharedRuntimeState,
    SourceCursor,
)

T0 = datetime(2026, 9, 9, 12, 0, tzinfo=UTC)


def freshness(
    component: str,
    status: FreshnessStatus = FreshnessStatus.AVAILABLE,
) -> ComponentFreshness:
    return ComponentFreshness(
        component=component,
        status=status,
        observed_at=T0,
        available_at=T0 + timedelta(milliseconds=10),
        stale_after_ms=5_000,
    )


def account(*, equity: float | None = 10_050.0) -> AccountState:
    return AccountState(
        source="mt5",
        account_id="demo-123",
        as_of=T0,
        freshness=freshness("account"),
        currency="USD",
        balance=10_000.0,
        equity=equity,
        free_margin=9_000.0,
        used_margin=1_050.0,
        margin_level=957.14,
        floating_pnl=50.0,
        daily_realized_pnl=0.0,
        daily_unrealized_pnl=50.0,
        daily_drawdown=0.0,
        total_drawdown=0.0,
    )


def market() -> MarketState:
    return MarketState(
        source="mt5",
        symbol="XAUUSD",
        as_of=T0,
        freshness=freshness("market"),
        bid=2500.10,
        ask=2500.30,
        last=2500.20,
        spread_points=20.0,
        base_timeframe="M5",
        completed_timeframes=("M5", "M15", "H1"),
        feature_manifest_id="fm-example",
    )


def position() -> PositionState:
    return PositionState(
        source="mt5",
        broker_ticket=123456,
        replay_position_id=None,
        symbol="XAUUSD",
        side=PositionSide.BUY,
        volume_lots=0.20,
        opened_at=T0 - timedelta(minutes=12),
        open_price=2498.0,
        current_price=2500.1,
        stop_loss=2493.0,
        take_profit=2508.0,
        floating_pnl=42.0,
        commission=-1.0,
        swap=0.0,
        setup_id="setup-a",
        thesis_id="thesis-a",
    )


def order() -> OrderState:
    return OrderState(
        source="replay",
        broker_ticket=None,
        replay_order_id="replay-order-7",
        symbol="XAUUSD",
        order_type=OrderType.BUY_LIMIT,
        volume_lots=0.10,
        created_at=T0 - timedelta(minutes=2),
        price=2499.0,
        stop_loss=2494.0,
        take_profit=2509.0,
        setup_id="setup-a",
        thesis_id="thesis-a",
    )


def feedback() -> ExecutionFeedbackState:
    return ExecutionFeedbackState(
        source="mt5",
        instruction_id="instruction-1",
        broker_ticket=123456,
        replay_execution_id=None,
        status=ExecutionStatus.FILLED,
        event_time=T0,
        observed_at=T0 + timedelta(milliseconds=20),
        requested_volume_lots=0.20,
        filled_volume_lots=0.20,
        requested_price=2500.2,
        fill_price=2500.3,
        slippage_points=10.0,
        commission=-1.0,
        swap=0.0,
        broker_code="10009",
        broker_message="request completed",
    )


def shared_state(*, recorded_at: datetime) -> SharedRuntimeState:
    current_position = position()
    current_order = order()
    return SharedRuntimeState(
        as_of=T0 + timedelta(milliseconds=25),
        market=market(),
        account=account(),
        positions=PositionBookState(
            source="mt5",
            as_of=T0,
            freshness=freshness("positions"),
            positions=(current_position,),
        ),
        orders=OrderBookState(
            source="mt5",
            as_of=T0,
            freshness=freshness("orders"),
            orders=(current_order,),
        ),
        exposure=ExposureState(
            as_of=T0,
            freshness=freshness("exposure"),
            gross_lots=0.20,
            net_lots=0.20,
            gross_notional=500.02,
            net_notional=500.02,
        ),
        broker_constraints=BrokerConstraints(
            source="mt5",
            symbol="XAUUSD",
            as_of=T0,
            freshness=freshness("broker_constraints"),
            trade_allowed=True,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point_size=0.01,
            tick_size=0.01,
            tick_value_loss=1.0,
            stops_level_points=10.0,
            freeze_level_points=0.0,
        ),
        component_freshness=(freshness("market"), freshness("account")),
        source_cursors=(SourceCursor(source="mt5", source_sequence=91),),
        latest_execution_feedback=feedback(),
        recorded_at=recorded_at,
    )


def test_runtime_event_identity_excludes_ingestion_time_and_roundtrips() -> None:
    payload = market()
    base = {
        "event_type": RuntimeEventType.M5_CLOSED,
        "event_time": T0,
        "observed_at": T0 + timedelta(milliseconds=10),
        "available_at": T0 + timedelta(milliseconds=20),
        "source": "mt5",
        "source_version": "5.0.45",
        "source_sequence": 42,
        "symbol": "XAUUSD",
        "payload": payload,
    }
    first = RuntimeEvent(**base, ingested_at=T0 + timedelta(seconds=1))
    second = RuntimeEvent(**base, ingested_at=T0 + timedelta(seconds=9))

    assert first.event_id == second.event_id
    assert first.ordering_key == (
        T0 + timedelta(milliseconds=20),
        42,
        first.event_id,
    )
    restored = RuntimeEvent.model_validate_json(first.model_dump_json())
    assert restored == first
    assert json.loads(first.model_dump_json())["event_id"] == first.event_id


def test_runtime_event_identity_changes_with_semantic_ordering_input() -> None:
    base = RuntimeEvent(
        event_type=RuntimeEventType.ACCOUNT_UPDATED,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
        source="mt5",
        source_version="5.0.45",
        source_sequence=1,
        payload=account(),
    )
    changed = RuntimeEvent(
        event_type=RuntimeEventType.ACCOUNT_UPDATED,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
        source="mt5",
        source_version="5.0.45",
        source_sequence=2,
        payload=account(),
    )
    assert base.event_id != changed.event_id


@pytest.mark.parametrize("field", ["event_time", "observed_at", "available_at"])
def test_runtime_event_rejects_naive_timestamps(field: str) -> None:
    values = {
        "event_type": RuntimeEventType.ACCOUNT_UPDATED,
        "event_time": T0,
        "observed_at": T0,
        "available_at": T0,
        "source": "mt5",
        "source_version": "5.0.45",
        "source_sequence": 1,
        "payload": account(),
    }
    values[field] = datetime(2026, 9, 9, 12, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        RuntimeEvent.model_validate(values)


def test_aware_non_utc_timestamp_is_normalized_to_utc() -> None:
    plus_eight = timezone(timedelta(hours=8))
    value = ComponentFreshness(
        component="market",
        status=FreshnessStatus.AVAILABLE,
        observed_at=datetime(2026, 9, 9, 20, 0, tzinfo=plus_eight),
        available_at=datetime(2026, 9, 9, 20, 0, microsecond=1_000, tzinfo=plus_eight),
    )
    assert value.observed_at == T0
    assert value.observed_at.tzinfo is UTC


def test_event_time_observation_and_availability_order_is_enforced() -> None:
    with pytest.raises(ValidationError, match="event_time <= observed_at <= available_at"):
        RuntimeEvent(
            event_type=RuntimeEventType.TICK,
            event_time=T0,
            observed_at=T0 + timedelta(seconds=2),
            available_at=T0 + timedelta(seconds=1),
            source="mt5",
            source_version="5.0.45",
            source_sequence=2,
            payload=market(),
        )


def test_event_type_requires_matching_typed_payload() -> None:
    with pytest.raises(ValidationError, match="payload"):
        RuntimeEvent(
            event_type=RuntimeEventType.ACCOUNT_UPDATED,
            event_time=T0,
            observed_at=T0,
            available_at=T0,
            source="mt5",
            source_version="5.0.45",
            source_sequence=1,
            payload=market(),
        )


def test_unknown_stale_and_known_zero_are_distinct() -> None:
    unknown = AccountState(
        source="mt5",
        account_id="demo-123",
        as_of=T0,
        freshness=ComponentFreshness(
            component="account",
            status=FreshnessStatus.UNKNOWN,
            reason="terminal has not synchronized account state",
        ),
    )
    known_zero = account(equity=0.0)
    stale = account().model_copy(
        update={
            "freshness": ComponentFreshness(
                component="account",
                status=FreshnessStatus.STALE,
                observed_at=T0 - timedelta(minutes=1),
                available_at=T0 - timedelta(minutes=1),
                stale_after_ms=5_000,
                reason="account heartbeat expired",
            )
        }
    )

    assert unknown.equity is None
    assert known_zero.equity == 0.0
    assert stale.equity == 10_050.0
    with pytest.raises(ValidationError, match="unknown or unavailable"):
        AccountState(
            source="mt5",
            account_id="demo-123",
            as_of=T0,
            freshness=ComponentFreshness(
                component="account", status=FreshnessStatus.UNAVAILABLE, reason="logged out"
            ),
            equity=0.0,
        )


def test_position_and_order_preserve_broker_or_replay_identity() -> None:
    live_position = position()
    replay_order = order()
    assert live_position.broker_ticket == 123456
    assert live_position.position_id.startswith("pos-")
    assert replay_order.replay_order_id == "replay-order-7"
    assert replay_order.order_id.startswith("ord-")
    assert live_position.position_id == position().position_id
    assert replay_order.order_id == order().order_id

    with pytest.raises(ValidationError, match="broker_ticket or replay_position_id"):
        PositionState(
            source="mt5",
            symbol="XAUUSD",
            side=PositionSide.BUY,
            volume_lots=0.1,
            opened_at=T0,
            open_price=2500.0,
        )


def test_shared_state_identity_excludes_recording_time_and_serializes() -> None:
    first = shared_state(recorded_at=T0 + timedelta(seconds=1))
    second = shared_state(recorded_at=T0 + timedelta(seconds=9))

    assert first.state_id == second.state_id
    assert first.account.free_margin == 9_000.0
    assert first.positions.positions[0].broker_ticket == 123456
    assert first.orders.orders[0].replay_order_id == "replay-order-7"
    assert first.exposure.net_lots == 0.20
    assert first.latest_execution_feedback is not None
    assert first.latest_execution_feedback.status is ExecutionStatus.FILLED
    restored = SharedRuntimeState.model_validate_json(first.model_dump_json())
    assert restored == first


def test_state_identity_changes_when_account_content_changes() -> None:
    original = shared_state(recorded_at=T0)
    changed_payload = original.model_dump(exclude={"state_id", "recorded_at"})
    changed_payload["account"] = account(equity=9_999.0)
    changed = SharedRuntimeState.model_validate(changed_payload)
    assert original.state_id != changed.state_id


def test_non_finite_financial_value_is_rejected() -> None:
    with pytest.raises(ValidationError, match="finite"):
        account(equity=float("inf"))
