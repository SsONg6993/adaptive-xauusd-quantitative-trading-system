"""Narrow, optional, read-only MetaTrader 5 dashboard boundary."""

from __future__ import annotations

import importlib
import math
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Literal, Protocol, cast

from pydantic import Field, field_validator

from axq.dashboard.contracts import ComponentState, ComponentStatus, DashboardModel


class MT5ReadError(RuntimeError):
    """A live MT5 snapshot could not be read safely."""


class _MT5Module(Protocol):
    POSITION_TYPE_BUY: int
    POSITION_TYPE_SELL: int

    def initialize(self, **kwargs: object) -> bool: ...

    def shutdown(self) -> None: ...

    def last_error(self) -> object: ...

    def terminal_info(self) -> object: ...

    def account_info(self) -> object: ...

    def positions_get(self) -> object: ...

    def symbol_info_tick(self, symbol: str) -> object: ...


class MT5ReadOnlyAdapter(Protocol):
    @property
    def position_type_buy(self) -> int: ...

    @property
    def position_type_sell(self) -> int: ...

    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def terminal_info(self) -> Mapping[str, object] | None: ...

    def account_info(self) -> Mapping[str, object] | None: ...

    def positions(self) -> tuple[Mapping[str, object], ...]: ...

    def tick(self, symbol: str) -> Mapping[str, object] | None: ...


def _load_module() -> _MT5Module:
    try:
        return cast(_MT5Module, importlib.import_module("MetaTrader5"))
    except ImportError as error:
        raise MT5ReadError("MetaTrader5 package is unavailable") from error


class MetaTrader5ReadOnlyAdapter:
    """Direct MT5 reader with no account-login or trading-operation surface."""

    def __init__(
        self,
        *,
        terminal_path: str | None = None,
        module_loader: Callable[[], _MT5Module] = _load_module,
    ) -> None:
        self._terminal_path = terminal_path
        self._module_loader = module_loader
        self._module: _MT5Module | None = None

    def connect(self) -> None:
        try:
            module = self._module_loader()
        except ImportError as error:
            raise MT5ReadError("MetaTrader5 package is unavailable") from error
        arguments: dict[str, object] = {}
        if self._terminal_path:
            arguments["path"] = self._terminal_path
        if not module.initialize(**arguments):
            initialize_error = module.last_error()
            module.shutdown()
            raise MT5ReadError(f"MT5 initialize failed: {initialize_error}")
        self._module = module

    def disconnect(self) -> None:
        if self._module is not None:
            self._module.shutdown()
        self._module = None

    def _connected_module(self) -> _MT5Module:
        if self._module is None:
            raise MT5ReadError("MT5 not connected")
        return self._module

    @property
    def position_type_buy(self) -> int:
        return self._connected_module().POSITION_TYPE_BUY

    @property
    def position_type_sell(self) -> int:
        return self._connected_module().POSITION_TYPE_SELL

    def terminal_info(self) -> Mapping[str, object] | None:
        return _mapping(self._connected_module().terminal_info())

    def account_info(self) -> Mapping[str, object] | None:
        return _mapping(self._connected_module().account_info())

    def positions(self) -> tuple[Mapping[str, object], ...]:
        return _mappings(self._connected_module().positions_get())

    def tick(self, symbol: str) -> Mapping[str, object] | None:
        return _mapping(self._connected_module().symbol_info_tick(symbol))


class LiveMT5Position(DashboardModel):
    symbol: str = Field(min_length=1)
    direction: Literal["BUY", "SELL", "UNKNOWN"]
    volume: float
    open_price: float
    current_price: float | None = None
    floating_pnl: float | None = None


class LiveMT5Snapshot(DashboardModel):
    component: ComponentStatus
    quote_component: ComponentStatus
    configured_symbol: str = Field(min_length=1)
    canonical_instrument: Literal["XAUUSD"] = "XAUUSD"
    resolved_broker_symbol: str = Field(min_length=1)
    account_login: int | None = None
    server: str | None = None
    balance: float | None = None
    equity: float | None = None
    margin: float | None = None
    free_margin: float | None = None
    floating_pnl: float | None = None
    positions: tuple[LiveMT5Position, ...] = ()
    bid: float | None = None
    ask: float | None = None
    spread: float | None = None
    last_refreshed: datetime
    quote_updated_at: datetime | None = None

    @field_validator("last_refreshed", "quote_updated_at")
    @classmethod
    def require_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("MT5 dashboard timestamps must be timezone-aware")
        return value.astimezone(UTC)


def _mapping(value: object) -> Mapping[str, object] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_dict = getattr(value, "_asdict", None)
    if callable(as_dict):
        mapped = as_dict()
        if isinstance(mapped, Mapping):
            return {str(key): item for key, item in mapped.items()}
    raise MT5ReadError(f"Unsupported MT5 response type: {type(value).__name__}")


def _mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if value is None:
        return ()
    if not isinstance(value, (tuple, list)):
        raise MT5ReadError("Unsupported MT5 positions response")
    results: list[Mapping[str, object]] = []
    for item in value:
        mapped = _mapping(item)
        if mapped is None:
            raise MT5ReadError("MT5 positions response contains an empty record")
        results.append(mapped)
    return tuple(results)


def _number(record: Mapping[str, object], field: str) -> float | None:
    value = record.get(field)
    if value is None or isinstance(value, bool):
        return None
    if not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _text(record: Mapping[str, object], field: str) -> str | None:
    value = record.get(field)
    return value if isinstance(value, str) and value else None


def _login(record: Mapping[str, object]) -> int | None:
    value = record.get("login")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _position(
    record: Mapping[str, object],
    *,
    buy_type: int,
    sell_type: int,
) -> LiveMT5Position:
    raw_type = record.get("type")
    direction: Literal["BUY", "SELL", "UNKNOWN"] = "UNKNOWN"
    if raw_type == buy_type:
        direction = "BUY"
    elif raw_type == sell_type:
        direction = "SELL"
    symbol = _text(record, "symbol")
    volume = _number(record, "volume")
    open_price = _number(record, "price_open")
    if symbol is None or volume is None or open_price is None:
        raise MT5ReadError("MT5 position is missing required read-only fields")
    return LiveMT5Position(
        symbol=symbol,
        direction=direction,
        volume=volume,
        open_price=open_price,
        current_price=_number(record, "price_current"),
        floating_pnl=_number(record, "profit"),
    )


def _quote_time(tick: Mapping[str, object]) -> datetime | None:
    milliseconds = _number(tick, "time_msc")
    if milliseconds is not None and milliseconds > 0:
        return datetime.fromtimestamp(milliseconds / 1_000, tz=UTC)
    seconds = _number(tick, "time")
    if seconds is not None and seconds > 0:
        return datetime.fromtimestamp(seconds, tz=UTC)
    return None


def _empty_snapshot(
    *,
    symbol: str,
    observed_at: datetime,
    state: ComponentState,
    detail: str,
) -> LiveMT5Snapshot:
    unavailable_quote = ComponentStatus(
        component="Live quote",
        state=ComponentState.UNAVAILABLE,
        detail=f"No valid tick is available for configured symbol {symbol}.",
    )
    return LiveMT5Snapshot(
        component=ComponentStatus(component="MT5", state=state, detail=detail),
        quote_component=unavailable_quote,
        configured_symbol=symbol,
        resolved_broker_symbol=symbol,
        last_refreshed=observed_at,
    )


def read_live_mt5_snapshot(
    *,
    symbol: str,
    terminal_path: str | None = None,
    adapter: MT5ReadOnlyAdapter | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> LiveMT5Snapshot:
    """Read one live snapshot using exactly the configured symbol and no mutations."""

    configured_symbol = symbol.strip()
    observed_at = now()
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("MT5 dashboard clock must be timezone-aware")
    observed_at = observed_at.astimezone(UTC)
    if not configured_symbol:
        return _empty_snapshot(
            symbol="Symbol not configured",
            observed_at=observed_at,
            state=ComponentState.NOT_CONFIGURED,
            detail="MT5 symbol is not configured",
        )
    reader = adapter or MetaTrader5ReadOnlyAdapter(terminal_path=terminal_path)
    connected = False
    try:
        reader.connect()
        connected = True
        terminal = reader.terminal_info()
        if terminal is None or terminal.get("connected") is not True:
            return _empty_snapshot(
                symbol=configured_symbol,
                observed_at=observed_at,
                state=ComponentState.NOT_CONFIGURED,
                detail="MT5 not connected",
            )
        account = reader.account_info()
        if account is None:
            return _empty_snapshot(
                symbol=configured_symbol,
                observed_at=observed_at,
                state=ComponentState.UNAVAILABLE,
                detail="MT5 account data is unavailable",
            )
        positions = tuple(
            _position(
                item,
                buy_type=reader.position_type_buy,
                sell_type=reader.position_type_sell,
            )
            for item in reader.positions()
        )
        tick = reader.tick(configured_symbol)
        bid = None if tick is None else _number(tick, "bid")
        ask = None if tick is None else _number(tick, "ask")
        valid_tick = bid is not None and ask is not None and bid > 0 and ask >= bid
        quote_at = None if tick is None else _quote_time(tick)
        quote_is_stale = (
            valid_tick
            and quote_at is not None
            and (
                observed_at - quote_at < timedelta(0)
                or observed_at - quote_at > timedelta(minutes=5)
            )
        )
        quote_state = (
            ComponentState.UNAVAILABLE
            if not valid_tick or quote_at is None
            else ComponentState.STALE
            if quote_is_stale
            else ComponentState.AVAILABLE
        )
        quote_status = ComponentStatus(
            component="Live quote",
            state=quote_state,
            detail=(
                f"Quote for {configured_symbol} is stale; waiting for fresh data."
                if quote_state is ComponentState.STALE
                else
                f"Live quote available for {configured_symbol}."
                if quote_state is ComponentState.AVAILABLE
                else f"No valid tick is available for configured symbol {configured_symbol}."
            ),
            as_of=None if quote_at is None else quote_at.isoformat(),
        )
        return LiveMT5Snapshot(
            component=ComponentStatus(
                component="MT5",
                state=ComponentState.ONLINE,
                detail="MT5 connected",
                as_of=observed_at.isoformat(),
            ),
            quote_component=quote_status,
            configured_symbol=configured_symbol,
            resolved_broker_symbol=configured_symbol,
            account_login=_login(account),
            server=_text(account, "server"),
            balance=_number(account, "balance"),
            equity=_number(account, "equity"),
            margin=_number(account, "margin"),
            free_margin=_number(account, "margin_free"),
            floating_pnl=_number(account, "profit"),
            positions=positions,
            bid=bid if valid_tick else None,
            ask=ask if valid_tick else None,
            spread=(None if not valid_tick else cast(float, ask) - cast(float, bid)),
            last_refreshed=observed_at,
            quote_updated_at=quote_at,
        )
    except Exception as error:
        return _empty_snapshot(
            symbol=configured_symbol,
            observed_at=observed_at,
            state=ComponentState.NOT_CONFIGURED,
            detail="MT5 not connected" if isinstance(error, MT5ReadError) else "MT5 read error",
        )
    finally:
        if connected:
            reader.disconnect()


__all__ = [
    "LiveMT5Position",
    "LiveMT5Snapshot",
    "MT5ReadError",
    "MT5ReadOnlyAdapter",
    "MetaTrader5ReadOnlyAdapter",
    "read_live_mt5_snapshot",
]
