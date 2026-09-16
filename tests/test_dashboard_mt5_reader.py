"""Read-only MT5 dashboard boundary tests."""

from __future__ import annotations

import ast
from collections import namedtuple
from datetime import UTC, datetime
from pathlib import Path

from axq.dashboard.contracts import ComponentState
from axq.dashboard.mt5_reader import (
    MetaTrader5ReadOnlyAdapter,
    read_live_mt5_snapshot,
)


class FakeMT5Module:
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1

    def __init__(
        self,
        *,
        initializes: bool = True,
        terminal: object | None = None,
        account: object | None = None,
        tick: object | None = None,
        positions: object = (),
    ) -> None:
        self.initializes = initializes
        self.terminal = terminal
        self.account = account
        self.tick = tick
        self.positions = positions
        self.initialize_calls: list[dict[str, object]] = []
        self.tick_symbols: list[str] = []
        self.shutdown_calls = 0

    def initialize(self, **kwargs: object) -> bool:
        self.initialize_calls.append(dict(kwargs))
        return self.initializes

    def shutdown(self) -> None:
        self.shutdown_calls += 1

    def last_error(self) -> tuple[int, str]:
        return (1, "offline fixture")

    def terminal_info(self) -> object | None:
        return self.terminal

    def account_info(self) -> object | None:
        return self.account

    def positions_get(self) -> object:
        return self.positions

    def symbol_info_tick(self, symbol: str) -> object | None:
        self.tick_symbols.append(symbol)
        return self.tick


def _record(name: str, **values: object) -> object:
    record = namedtuple(name, values)
    return record(**values)


def _now() -> datetime:
    return datetime(2026, 9, 12, 11, 30, tzinfo=UTC)


def test_adapter_initializes_without_account_credentials() -> None:
    module = FakeMT5Module(initializes=True)
    adapter = MetaTrader5ReadOnlyAdapter(
        terminal_path=r"C:\Program Files\MetaTrader 5\terminal64.exe",
        module_loader=lambda: module,
    )

    adapter.connect()
    adapter.disconnect()

    assert module.initialize_calls == [
        {"path": r"C:\Program Files\MetaTrader 5\terminal64.exe"}
    ]
    assert module.shutdown_calls == 1


def test_missing_mt5_package_is_reported_without_crashing() -> None:
    def missing_module() -> object:
        raise ImportError("MetaTrader5 not installed")

    snapshot = read_live_mt5_snapshot(
        symbol="XAUUSD.sc",
        adapter=MetaTrader5ReadOnlyAdapter(module_loader=missing_module),
        now=_now,
    )

    assert snapshot.component.state is ComponentState.NOT_CONFIGURED
    assert snapshot.component.detail == "MT5 not connected"
    assert snapshot.balance is None


def test_offline_terminal_and_unavailable_account_fail_closed() -> None:
    offline = FakeMT5Module(initializes=False)
    offline_snapshot = read_live_mt5_snapshot(
        symbol="XAUUSD.sc",
        adapter=MetaTrader5ReadOnlyAdapter(module_loader=lambda: offline),
        now=_now,
    )
    assert offline_snapshot.component.state is ComponentState.NOT_CONFIGURED
    assert offline_snapshot.component.detail == "MT5 not connected"
    assert offline.shutdown_calls == 1

    no_account = FakeMT5Module(
        terminal={"connected": True},
        account=None,
    )
    account_snapshot = read_live_mt5_snapshot(
        symbol="XAUUSD.sc",
        adapter=MetaTrader5ReadOnlyAdapter(module_loader=lambda: no_account),
        now=_now,
    )
    assert account_snapshot.component.state is ComponentState.UNAVAILABLE
    assert account_snapshot.component.detail == "MT5 account data is unavailable"


def test_valid_account_quote_and_positions_use_exact_configured_symbol() -> None:
    module = FakeMT5Module(
        terminal=_record("Terminal", connected=True),
        account=_record(
            "Account",
            login=123456,
            server="Broker-Demo",
            balance=10_000.0,
            equity=10_125.5,
            margin=250.0,
            margin_free=9_875.5,
            profit=125.5,
        ),
        tick=_record(
            "Tick",
            bid=2510.10,
            ask=2510.35,
            time_msc=1_789_208_400_000,
        ),
        positions=(
            _record(
                "Position",
                symbol="XAUUSD.sc",
                type=0,
                volume=0.2,
                price_open=2500.0,
                price_current=2510.1,
                profit=125.5,
            ),
        ),
    )

    snapshot = read_live_mt5_snapshot(
        symbol="XAUUSD.sc",
        adapter=MetaTrader5ReadOnlyAdapter(module_loader=lambda: module),
        now=_now,
    )

    assert snapshot.component.state is ComponentState.ONLINE
    assert snapshot.quote_component.state is ComponentState.STALE
    assert snapshot.quote_updated_at == datetime(2026, 9, 12, 10, 20, tzinfo=UTC)
    assert snapshot.account_login == 123456
    assert snapshot.server == "Broker-Demo"
    assert snapshot.balance == 10_000.0
    assert snapshot.equity == 10_125.5
    assert snapshot.margin == 250.0
    assert snapshot.free_margin == 9_875.5
    assert snapshot.floating_pnl == 125.5
    assert snapshot.bid == 2510.10
    assert snapshot.ask == 2510.35
    assert snapshot.spread == 0.25
    assert snapshot.configured_symbol == "XAUUSD.sc"
    assert snapshot.canonical_instrument == "XAUUSD"
    assert snapshot.resolved_broker_symbol == "XAUUSD.sc"
    assert module.tick_symbols == ["XAUUSD.sc"]
    assert len(snapshot.positions) == 1
    assert snapshot.positions[0].direction == "BUY"
    assert snapshot.positions[0].symbol == "XAUUSD.sc"


def test_missing_or_invalid_exact_symbol_tick_is_unavailable_without_fallback() -> None:
    module = FakeMT5Module(
        terminal={"connected": True},
        account={
            "login": 123,
            "server": "Broker-Demo",
            "balance": 1000.0,
            "equity": 1000.0,
            "margin": 0.0,
            "margin_free": 1000.0,
            "profit": 0.0,
        },
        tick=None,
    )

    snapshot = read_live_mt5_snapshot(
        symbol="XAUUSD.sc",
        adapter=MetaTrader5ReadOnlyAdapter(module_loader=lambda: module),
        now=_now,
    )

    assert snapshot.component.state is ComponentState.ONLINE
    assert snapshot.quote_component.state is ComponentState.UNAVAILABLE
    assert snapshot.bid is None
    assert snapshot.ask is None
    assert module.tick_symbols == ["XAUUSD.sc"]


def test_dashboard_mt5_boundary_contains_no_trading_mutation_methods() -> None:
    path = Path("src/axq/dashboard/mt5_reader.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    attributes = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }
    assert not attributes & {
        "order_check",
        "order_send",
        "symbol_select",
        "orders_get",
    }
