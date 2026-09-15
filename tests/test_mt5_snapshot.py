from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.execution_boundary import BrokerObjectKind, broker_snapshot_runtime_events
from axq.mt5 import (
    MT5Constants,
    MT5PersistedIntentLink,
    MT5SnapshotError,
    MT5SymbolMapping,
)
from axq.mt5.snapshot import MT5BrokerSnapshotProvider
from axq.mt5.time_normalization import (
    MT5BrokerEnvironmentIdentity,
    MT5BrokerTimeNormalizer,
    infer_broker_time_offset,
)
from axq.runtime import (
    FreshnessStatus,
    OrderType,
    PositionSide,
    RuntimeEventType,
    initial_runtime_state,
    reduce_state,
)

NOW = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _constants() -> MT5Constants:
    return MT5Constants(
        account_trade_mode_demo=0,
        account_trade_mode_contest=1,
        account_trade_mode_real=2,
        symbol_trade_mode_disabled=0,
        position_type_buy=0,
        position_type_sell=1,
        order_type_buy=0,
        order_type_sell=1,
        order_type_buy_limit=2,
        order_type_sell_limit=3,
        order_type_buy_stop=4,
        order_type_sell_stop=5,
        order_type_buy_stop_limit=6,
        order_type_sell_stop_limit=7,
        trade_action_deal=1,
        trade_action_sltp=6,
        order_time_gtc=0,
        order_filling_ioc=1,
        trade_retcode_requote=10004,
        trade_retcode_placed=10008,
        trade_retcode_done=10009,
        trade_retcode_done_partial=10010,
    )


class SnapshotGateway:
    constants = _constants()

    def __init__(self, *, connected: bool = True) -> None:
        self.connected = connected
        self.connect_calls = 0

    def connect(self) -> None:
        self.connect_calls += 1

    def close(self) -> None:
        return None

    def last_error(self) -> object:
        return (0, "ok")

    def terminal_info(self):
        return {"connected": self.connected, "trade_allowed": True}

    def account_info(self):
        return {
            "login": 7654321,
            "trade_mode": 0,
            "trade_allowed": True,
            "trade_expert": True,
            "currency": "USD",
            "balance": 10_000.0,
            "equity": 10_050.0,
            "margin_free": 9_500.0,
            "margin": 500.0,
            "margin_level": 2010.0,
            "profit": 50.0,
        }

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        return symbol == "XAUUSD.demo" and enabled

    def symbol_info(self, symbol: str):
        return {
            "name": symbol,
            "visible": True,
            "trade_mode": 4,
            "digits": 2,
            "point": 0.01,
            "trade_tick_size": 0.01,
            "trade_tick_value_loss": 1.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
            "trade_stops_level": 20,
            "trade_freeze_level": 10,
            "trade_contract_size": 100.0,
        }

    def symbol_info_tick(self, symbol: str):
        return {
            "symbol": symbol,
            "time": int(NOW.timestamp()),
            "time_msc": int(NOW.timestamp() * 1000),
            "bid": 2500.0,
            "ask": 2500.2,
            "last": 2500.1,
            "volume": 12,
        }

    def positions_get(self, symbol: str | None = None):
        return (
            {
                "ticket": 101,
                "symbol": symbol,
                "type": 0,
                "volume": 0.05,
                "time": int((NOW.replace(minute=0)).timestamp()),
                "price_open": 2490.0,
                "price_current": 2500.0,
                "sl": 2480.0,
                "tp": 0.0,
                "profit": 50.0,
                "commission": -1.0,
                "swap": -0.5,
            },
        )

    def orders_get(self, symbol: str | None = None):
        return (
            {
                "ticket": 202,
                "symbol": symbol,
                "type": 2,
                "volume_current": 0.03,
                "time_setup": int((NOW.replace(minute=1)).timestamp()),
                "price_open": 2485.0,
                "sl": 2475.0,
                "tp": 2510.0,
                "time_expiration": 0,
            },
        )

    def order_check(self, request):
        raise AssertionError("snapshot must not check orders")

    def order_send(self, request):
        raise AssertionError("snapshot must not mutate broker state")


def _provider(gateway: SnapshotGateway) -> MT5BrokerSnapshotProvider:
    return MT5BrokerSnapshotProvider(
        gateway=gateway,
        symbol_mapping=MT5SymbolMapping(
            internal_symbol="XAUUSD",
            broker_symbol="XAUUSD.demo",
        ),
        clock=lambda: NOW,
        source="mt5-demo",
        source_version="1.0.0",
        stale_after_ms=30_000,
    )


def test_snapshot_maps_account_market_books_exposure_and_constraints() -> None:
    gateway = SnapshotGateway()
    snapshot = _provider(gateway).capture()

    assert snapshot.account.account_id == "7654321"
    assert snapshot.account.balance == 10_000.0
    assert snapshot.account.equity == 10_050.0
    assert snapshot.account.free_margin == 9_500.0
    assert snapshot.account.used_margin == 500.0
    assert snapshot.account.floating_pnl == 50.0
    assert snapshot.market.symbol == "XAUUSD"
    assert snapshot.market.as_of == NOW
    assert snapshot.market.bid == 2500.0
    assert snapshot.market.ask == 2500.2
    assert snapshot.market.spread_points == 20.0
    assert snapshot.positions.positions[0].broker_ticket == 101
    assert snapshot.positions.positions[0].side is PositionSide.BUY
    assert snapshot.positions.positions[0].take_profit is None
    assert snapshot.orders.orders[0].broker_ticket == 202
    assert snapshot.orders.orders[0].order_type is OrderType.BUY_LIMIT
    assert snapshot.orders.orders[0].volume_lots == 0.03
    assert snapshot.exposure.gross_lots == 0.05
    assert snapshot.exposure.net_lots == 0.05
    assert snapshot.exposure.gross_notional == 12_500.0
    assert snapshot.exposure.net_notional == 12_500.0
    assert snapshot.broker_constraints.digits == 2
    assert snapshot.broker_constraints.point_size == 0.01
    assert snapshot.broker_constraints.tick_size == 0.01
    assert snapshot.broker_constraints.trade_allowed is True
    assert gateway.connect_calls == 1


def test_shadow_snapshot_normalizes_tick_but_leaves_unverified_object_times_unchanged() -> None:
    gateway = SnapshotGateway()
    raw_tick = NOW + timedelta(hours=3)
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "time": int(raw_tick.timestamp()),
        "time_msc": int(raw_tick.timestamp() * 1_000),
        "bid": 2500.0,
        "ask": 2500.2,
        "last": 0.0,
    }
    resolution = infer_broker_time_offset(
        raw_tick_time=int(raw_tick.timestamp()),
        raw_tick_time_msc=int(raw_tick.timestamp() * 1_000),
        observed_at=NOW,
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.demo",
        instrument_resolution_id="rbi-test",
        environment=MT5BrokerEnvironmentIdentity(
            broker_server="test",
            account_login_digest="login-digest",
            account_trade_mode=0,
            terminal_company="test",
            terminal_build=1,
        ),
    )
    provider = MT5BrokerSnapshotProvider(
        gateway=gateway,
        symbol_mapping=MT5SymbolMapping(
            internal_symbol="XAUUSD", broker_symbol="XAUUSD.demo"
        ),
        clock=lambda: NOW,
        source="mt5-shadow",
        source_version="1.0.0",
        stale_after_ms=30_000,
        broker_time_normalizer=MT5BrokerTimeNormalizer(resolution),
    )

    snapshot = provider.capture()

    assert snapshot.market.as_of == NOW
    assert snapshot.market.freshness.observed_at == NOW
    assert snapshot.market.last is None
    # Position/order clock encoding is not proven equivalent to market-data encoding in V1.
    assert snapshot.positions.positions[0].opened_at == NOW.replace(minute=0)
    assert snapshot.orders.orders[0].created_at == NOW.replace(minute=1)


def test_shadow_snapshot_accepts_normalizer_operational_future_tolerance() -> None:
    gateway = SnapshotGateway()
    raw_tick = NOW + timedelta(hours=3, milliseconds=100)
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "time": int(raw_tick.timestamp()),
        "time_msc": int(raw_tick.timestamp() * 1_000),
        "bid": 2500.0,
        "ask": 2500.2,
        "last": 0.0,
    }
    resolution = infer_broker_time_offset(
        raw_tick_time=int(raw_tick.timestamp()),
        raw_tick_time_msc=int(raw_tick.timestamp() * 1_000),
        observed_at=NOW,
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.demo",
        instrument_resolution_id="rbi-test",
        environment=MT5BrokerEnvironmentIdentity(broker_server="test"),
    )
    clock_values = iter((NOW, NOW + timedelta(milliseconds=200)))
    provider = MT5BrokerSnapshotProvider(
        gateway=gateway,
        symbol_mapping=MT5SymbolMapping(
            internal_symbol="XAUUSD", broker_symbol="XAUUSD.demo"
        ),
        clock=lambda: next(clock_values),
        source="mt5-shadow",
        source_version="1.0.0",
        stale_after_ms=30_000,
        broker_time_normalizer=MT5BrokerTimeNormalizer(resolution),
    )

    snapshot = provider.capture()

    assert snapshot.market.as_of == NOW + timedelta(milliseconds=100)
    assert snapshot.market.freshness.available_at == NOW + timedelta(milliseconds=200)


def test_snapshot_preserves_positive_broker_last() -> None:
    snapshot = _provider(SnapshotGateway()).capture()

    assert snapshot.market.last == 2500.1


@pytest.mark.parametrize("broker_last", [0.0, -1.0, float("nan"), "invalid"])
def test_snapshot_maps_invalid_broker_last_to_none_without_changing_quote(
    broker_last: object,
) -> None:
    gateway = SnapshotGateway()
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "time": int(NOW.timestamp()),
        "time_msc": int(NOW.timestamp() * 1000),
        "bid": 4348.10,
        "ask": 4348.45,
        "last": broker_last,
        "volume": 0,
    }

    snapshot = _provider(gateway).capture()

    assert snapshot.market.bid == 4348.10
    assert snapshot.market.ask == 4348.45
    assert snapshot.market.last is None
    assert snapshot.market.last != (4348.10 + 4348.45) / 2
    assert snapshot.market.as_of == NOW


def test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object() -> None:
    linkage = MT5PersistedIntentLink(
        intent_id="xi-entry",
        object_kind=BrokerObjectKind.POSITION,
        broker_ticket=101,
        transport_execution_id="mt5-deal-999",
        setup_id="setup-1",
        thesis_id="thesis-1",
    )

    snapshot = _provider(SnapshotGateway()).capture(linkages=(linkage,))

    position = snapshot.positions.positions[0]
    assert position.setup_id == "setup-1"
    assert position.thesis_id == "thesis-1"
    assert snapshot.intent_links[0].intent_id == "xi-entry"
    assert snapshot.intent_links[0].broker_object_id == position.position_id
    assert snapshot.intent_links[0].broker_ticket == 101


def test_snapshot_linkage_never_fuzzy_matches_missing_ticket() -> None:
    linkage = MT5PersistedIntentLink(
        intent_id="xi-entry",
        object_kind=BrokerObjectKind.POSITION,
        broker_ticket=999,
        transport_execution_id="mt5-deal-999",
    )

    with pytest.raises(MT5SnapshotError, match="exact broker ticket"):
        _provider(SnapshotGateway()).capture(linkages=(linkage,))


def test_snapshot_creates_canonical_events_and_reduces_through_shared_path() -> None:
    snapshot = _provider(SnapshotGateway()).capture()
    events = broker_snapshot_runtime_events(snapshot, source_sequence_start=10)

    assert [event.event_type for event in events] == [
        RuntimeEventType.TICK,
        RuntimeEventType.ACCOUNT_UPDATED,
        RuntimeEventType.POSITIONS_UPDATED,
        RuntimeEventType.ORDERS_UPDATED,
        RuntimeEventType.EXPOSURE_UPDATED,
        RuntimeEventType.BROKER_CONSTRAINTS_UPDATED,
    ]
    state = initial_runtime_state("XAUUSD", at=NOW)
    for event in events:
        assert event.event_time.tzinfo is UTC
        assert event.event_time <= event.observed_at <= event.available_at
        state = reduce_state(state, event, now=event.available_at)
    assert state.account == snapshot.account
    assert state.positions == snapshot.positions
    assert state.broker_constraints == snapshot.broker_constraints


def test_disconnected_terminal_returns_structured_snapshot_failure() -> None:
    with pytest.raises(MT5SnapshotError, match="DISCONNECTED"):
        _provider(SnapshotGateway(connected=False)).capture()


def test_snapshot_does_not_mutate_shared_state_or_call_broker_transport() -> None:
    gateway = SnapshotGateway()
    snapshot = _provider(gateway).capture()
    assert snapshot.account.freshness.status is FreshnessStatus.AVAILABLE


def test_shadow_snapshot_does_not_select_the_explicit_symbol() -> None:
    gateway = SnapshotGateway()

    def reject_selection(symbol: str, enabled: bool) -> bool:
        del symbol, enabled
        raise AssertionError("shadow snapshot must not select a symbol")

    gateway.symbol_select = reject_selection  # type: ignore[method-assign]
    provider = MT5BrokerSnapshotProvider(
        gateway=gateway,
        symbol_mapping=MT5SymbolMapping(internal_symbol="XAUUSD", broker_symbol="XAUUSD.demo"),
        clock=lambda: NOW,
        source="mt5-shadow",
        source_version="1",
        stale_after_ms=30_000,
        select_symbol=False,
    )

    snapshot = provider.capture()

    assert snapshot.market.symbol == "XAUUSD"
