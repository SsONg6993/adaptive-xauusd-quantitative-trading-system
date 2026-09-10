from __future__ import annotations

from collections import namedtuple

import pytest

from axq.mt5 import (
    MetaTrader5Gateway,
    MT5ConnectionError,
    MT5SymbolMapping,
)


class FakeMT5Module:
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_CONTEST = 1
    ACCOUNT_TRADE_MODE_REAL = 2
    SYMBOL_TRADE_MODE_DISABLED = 0
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_REQUOTE = 10004
    TRADE_RETCODE_PLACED = 10008
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_DONE_PARTIAL = 10010

    def __init__(self, *, initializes: bool = True) -> None:
        self.initializes = initializes
        self.initialize_calls: list[dict[str, object]] = []
        self.shutdown_calls = 0
        self.check_requests: list[dict[str, object]] = []
        self.send_requests: list[dict[str, object]] = []
        self.Record = namedtuple("Record", "login trade_mode connected")

    def initialize(self, **kwargs: object) -> bool:
        self.initialize_calls.append(dict(kwargs))
        return self.initializes

    def shutdown(self) -> None:
        self.shutdown_calls += 1

    def last_error(self) -> tuple[int, str]:
        return (1, "test error")

    def terminal_info(self):
        return self.Record(123, self.ACCOUNT_TRADE_MODE_DEMO, True)

    def account_info(self):
        return self.Record(456, self.ACCOUNT_TRADE_MODE_DEMO, True)

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        return symbol == "XAUUSD.demo" and enabled

    def symbol_info(self, symbol: str):
        return {"name": symbol, "digits": 2}

    def symbol_info_tick(self, symbol: str):
        return {"symbol": symbol, "bid": 2500.0, "ask": 2500.2}

    def positions_get(self, *, symbol: str | None = None):
        return ({"symbol": symbol, "ticket": 11},)

    def orders_get(self, *, symbol: str | None = None):
        return ({"symbol": symbol, "ticket": 12},)

    def order_check(self, request: dict[str, object]):
        self.check_requests.append(request)
        return {"retcode": 0, "comment": "check passed"}

    def order_send(self, request: dict[str, object]):
        self.send_requests.append(request)
        return {"retcode": self.TRADE_RETCODE_DONE, "order": 13}


def test_gateway_is_lazy_and_normalizes_external_named_tuples() -> None:
    module = FakeMT5Module()
    loads = 0

    def load_module():
        nonlocal loads
        loads += 1
        return module

    gateway = MetaTrader5Gateway(module_loader=load_module)
    assert loads == 0

    gateway.connect()

    assert loads == 1
    assert gateway.account_info() == {
        "login": 456,
        "trade_mode": 0,
        "connected": True,
    }
    assert gateway.terminal_info() == {
        "login": 123,
        "trade_mode": 0,
        "connected": True,
    }
    assert gateway.positions_get("XAUUSD.demo") == (
        {"symbol": "XAUUSD.demo", "ticket": 11},
    )
    assert gateway.orders_get("XAUUSD.demo") == (
        {"symbol": "XAUUSD.demo", "ticket": 12},
    )
    gateway.close()
    assert module.shutdown_calls == 1


def test_gateway_passes_operational_terminal_path_without_semantic_identity() -> None:
    module = FakeMT5Module()
    gateway = MetaTrader5Gateway(
        terminal_path=r"C:\Program Files\MetaTrader 5\terminal64.exe",
        module_loader=lambda: module,
    )

    gateway.connect()

    assert module.initialize_calls == [
        {"path": r"C:\Program Files\MetaTrader 5\terminal64.exe"}
    ]
    assert not hasattr(gateway, "gateway_id")


def test_gateway_initialization_failure_is_structured() -> None:
    module = FakeMT5Module(initializes=False)
    gateway = MetaTrader5Gateway(module_loader=lambda: module)

    with pytest.raises(MT5ConnectionError, match="test error"):
        gateway.connect()


def test_gateway_normalizes_check_send_and_constants() -> None:
    module = FakeMT5Module()
    gateway = MetaTrader5Gateway(module_loader=lambda: module)
    gateway.connect()
    request = {"action": 1, "symbol": "XAUUSD.demo"}

    assert gateway.order_check(request) == {"retcode": 0, "comment": "check passed"}
    assert gateway.order_send(request) == {"retcode": 10009, "order": 13}
    assert gateway.constants.account_trade_mode_demo == 0
    assert gateway.constants.trade_action_sltp == 6
    assert gateway.constants.trade_retcode_done_partial == 10010


def test_symbol_mapping_is_explicit_auditable_and_deterministic() -> None:
    first = MT5SymbolMapping(internal_symbol="XAUUSD", broker_symbol="XAUUSD.demo")
    second = MT5SymbolMapping.model_validate_json(first.model_dump_json())

    assert first.mapping_id == second.mapping_id
    assert first.to_broker("XAUUSD") == "XAUUSD.demo"
    assert first.to_internal("XAUUSD.demo") == "XAUUSD"
    with pytest.raises(ValueError, match="not configured"):
        first.to_broker("GOLD")
    with pytest.raises(ValueError, match="not configured"):
        first.to_internal("XAUUSD.other")
