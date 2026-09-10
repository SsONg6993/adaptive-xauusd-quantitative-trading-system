"""Lazy concrete wrapper around the Windows-only MetaTrader5 package."""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from typing import Protocol, cast

from axq.mt5.contracts import MT5ConnectionError, MT5Constants


class _MT5Module(Protocol):
    ACCOUNT_TRADE_MODE_DEMO: int
    ACCOUNT_TRADE_MODE_CONTEST: int
    ACCOUNT_TRADE_MODE_REAL: int
    SYMBOL_TRADE_MODE_DISABLED: int
    POSITION_TYPE_BUY: int
    POSITION_TYPE_SELL: int
    ORDER_TYPE_BUY: int
    ORDER_TYPE_SELL: int
    ORDER_TYPE_BUY_LIMIT: int
    ORDER_TYPE_SELL_LIMIT: int
    ORDER_TYPE_BUY_STOP: int
    ORDER_TYPE_SELL_STOP: int
    ORDER_TYPE_BUY_STOP_LIMIT: int
    ORDER_TYPE_SELL_STOP_LIMIT: int
    TRADE_ACTION_DEAL: int
    TRADE_ACTION_SLTP: int
    ORDER_TIME_GTC: int
    ORDER_FILLING_IOC: int
    TRADE_RETCODE_REQUOTE: int
    TRADE_RETCODE_PLACED: int
    TRADE_RETCODE_DONE: int
    TRADE_RETCODE_DONE_PARTIAL: int

    def initialize(self, **kwargs: object) -> bool: ...

    def shutdown(self) -> None: ...

    def last_error(self) -> object: ...

    def terminal_info(self) -> object: ...

    def account_info(self) -> object: ...

    def symbol_select(self, symbol: str, enabled: bool) -> bool: ...

    def symbol_info(self, symbol: str) -> object: ...

    def symbol_info_tick(self, symbol: str) -> object: ...

    def positions_get(self, *, symbol: str | None = None) -> object: ...

    def orders_get(self, *, symbol: str | None = None) -> object: ...

    def order_check(self, request: dict[str, object]) -> object: ...

    def order_send(self, request: dict[str, object]) -> object: ...


def _load_mt5() -> _MT5Module:
    try:
        return cast(_MT5Module, importlib.import_module("MetaTrader5"))
    except ImportError as exc:
        raise MT5ConnectionError(
            "MetaTrader5 is unavailable; install the Windows-only 'mt5' extra"
        ) from exc


class MetaTrader5Gateway:
    """Operational gateway; paths and process state are never semantic identity."""

    def __init__(
        self,
        *,
        terminal_path: str | None = None,
        module_loader: Callable[[], _MT5Module] = _load_mt5,
    ) -> None:
        self._terminal_path = terminal_path
        self._module_loader = module_loader
        self._module: _MT5Module | None = None
        self._connected = False

    def connect(self) -> None:
        if self._connected:
            return
        module = self._module_loader()
        kwargs: dict[str, object] = {}
        if self._terminal_path is not None:
            kwargs["path"] = self._terminal_path
        if not module.initialize(**kwargs):
            raise MT5ConnectionError(f"MT5 initialize failed: {module.last_error()}")
        self._module = module
        self._connected = True

    def close(self) -> None:
        if self._connected and self._module is not None:
            self._module.shutdown()
        self._connected = False

    def _require_module(self) -> _MT5Module:
        if not self._connected or self._module is None:
            raise MT5ConnectionError("MT5 gateway is not connected")
        return self._module

    @property
    def constants(self) -> MT5Constants:
        module = self._require_module()
        return MT5Constants(
            account_trade_mode_demo=module.ACCOUNT_TRADE_MODE_DEMO,
            account_trade_mode_contest=module.ACCOUNT_TRADE_MODE_CONTEST,
            account_trade_mode_real=module.ACCOUNT_TRADE_MODE_REAL,
            symbol_trade_mode_disabled=module.SYMBOL_TRADE_MODE_DISABLED,
            position_type_buy=module.POSITION_TYPE_BUY,
            position_type_sell=module.POSITION_TYPE_SELL,
            order_type_buy=module.ORDER_TYPE_BUY,
            order_type_sell=module.ORDER_TYPE_SELL,
            order_type_buy_limit=module.ORDER_TYPE_BUY_LIMIT,
            order_type_sell_limit=module.ORDER_TYPE_SELL_LIMIT,
            order_type_buy_stop=module.ORDER_TYPE_BUY_STOP,
            order_type_sell_stop=module.ORDER_TYPE_SELL_STOP,
            order_type_buy_stop_limit=module.ORDER_TYPE_BUY_STOP_LIMIT,
            order_type_sell_stop_limit=module.ORDER_TYPE_SELL_STOP_LIMIT,
            trade_action_deal=module.TRADE_ACTION_DEAL,
            trade_action_sltp=module.TRADE_ACTION_SLTP,
            order_time_gtc=module.ORDER_TIME_GTC,
            order_filling_ioc=module.ORDER_FILLING_IOC,
            trade_retcode_requote=module.TRADE_RETCODE_REQUOTE,
            trade_retcode_placed=module.TRADE_RETCODE_PLACED,
            trade_retcode_done=module.TRADE_RETCODE_DONE,
            trade_retcode_done_partial=module.TRADE_RETCODE_DONE_PARTIAL,
        )

    def last_error(self) -> object:
        return self._require_module().last_error()

    def terminal_info(self) -> Mapping[str, object] | None:
        return _mapping(self._require_module().terminal_info())

    def account_info(self) -> Mapping[str, object] | None:
        return _mapping(self._require_module().account_info())

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        return self._require_module().symbol_select(symbol, enabled)

    def symbol_info(self, symbol: str) -> Mapping[str, object] | None:
        return _mapping(self._require_module().symbol_info(symbol))

    def symbol_info_tick(self, symbol: str) -> Mapping[str, object] | None:
        return _mapping(self._require_module().symbol_info_tick(symbol))

    def positions_get(self, symbol: str | None = None) -> tuple[Mapping[str, object], ...]:
        return _mappings(self._require_module().positions_get(symbol=symbol))

    def orders_get(self, symbol: str | None = None) -> tuple[Mapping[str, object], ...]:
        return _mappings(self._require_module().orders_get(symbol=symbol))

    def order_check(self, request: Mapping[str, object]) -> Mapping[str, object] | None:
        return _mapping(self._require_module().order_check(dict(request)))

    def order_send(self, request: Mapping[str, object]) -> Mapping[str, object] | None:
        return _mapping(self._require_module().order_send(dict(request)))


def _mapping(value: object) -> Mapping[str, object] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_dict = getattr(value, "_asdict", None)
    if callable(as_dict):
        result = as_dict()
        if isinstance(result, Mapping):
            return {str(key): item for key, item in result.items()}
    raise MT5ConnectionError(f"unsupported MT5 response type: {type(value).__name__}")


def _mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if value is None:
        return ()
    if not isinstance(value, (tuple, list)):
        raise MT5ConnectionError(f"unsupported MT5 collection type: {type(value).__name__}")
    results: list[Mapping[str, object]] = []
    for item in value:
        mapped = _mapping(item)
        if mapped is None:
            raise MT5ConnectionError("MT5 collection contains an empty record")
        results.append(mapped)
    return tuple(results)
