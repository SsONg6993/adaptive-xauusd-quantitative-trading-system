"""Fail-closed MetaTrader 5 entry preflight and request construction."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from axq.execution_boundary import (
    ExecutionAccountMode,
    ExecutionIntent,
    ExecutionObservation,
    TransportFailure,
)
from axq.mt5.contracts import MT5Gateway, MT5SymbolMapping
from axq.runtime.clock import ensure_utc
from axq.schemas import Signal


class MT5TransportConfig(BaseModel):
    """Explicit transport values; changing them is an operational decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    deviation_points: int = Field(default=20, ge=0)
    magic: int = Field(default=71008, ge=0)
    max_tick_age_seconds: float = Field(default=5.0, gt=0.0)


def default_mt5_transport_config() -> MT5TransportConfig:
    return MT5TransportConfig()


class MT5EntryPreflight:
    """Acquire submission-time facts and build an exact market-entry request."""

    def __init__(
        self,
        *,
        gateway: MT5Gateway,
        symbol_mapping: MT5SymbolMapping,
        config: MT5TransportConfig,
        clock: Callable[[], datetime],
        kill_switch: Callable[[], bool],
    ) -> None:
        self._gateway = gateway
        self._mapping = symbol_mapping
        self._config = config
        self._clock = clock
        self._kill_switch = kill_switch

    def observe(self, intent: ExecutionIntent) -> ExecutionObservation:
        facts = self._facts(intent)
        tick_time = _tick_time(facts.tick)
        available_at = ensure_utc(self._clock())
        if tick_time > available_at:
            raise TransportFailure("MT5 tick is later than the local UTC clock")
        bid = _positive_float(facts.tick, "bid")
        ask = _positive_float(facts.tick, "ask")
        if ask < bid:
            raise TransportFailure("MT5 ask is below bid")
        point = _positive_float(facts.symbol, "point")
        market_price = ask if intent.direction is Signal.BUY else bid
        return ExecutionObservation(
            observed_at=tick_time,
            available_at=available_at,
            account_mode=_account_mode(facts.account, self._gateway),
            broker_symbol=facts.broker_symbol,
            market_price=market_price,
            spread_points=(ask - bid) / point,
            estimated_slippage_points=0.0,
        )

    def validate(self, intent: ExecutionIntent, _: ExecutionObservation) -> None:
        request = self.checked_request(intent)
        try:
            check = self._gateway.order_check(request)
        except Exception as exc:
            raise TransportFailure(f"MT5 order_check failed: {exc}") from exc
        if check is None:
            raise TransportFailure(
                f"MT5 order_check returned no result: {self._gateway.last_error()!r}"
            )
        if _int_value(check.get("retcode"), default=-1) != 0:
            raise TransportFailure(
                "MT5 order_check rejected request: "
                f"retcode={check.get('retcode')!r} comment={check.get('comment')!r}"
            )

    def checked_request(self, intent: ExecutionIntent) -> dict[str, object]:
        """Re-acquire all mutable facts immediately before a broker operation."""

        if self._kill_switch():
            raise TransportFailure("execution kill switch is active")
        facts = self._facts(intent)
        if _account_mode(facts.account, self._gateway) is not ExecutionAccountMode.DEMO:
            raise TransportFailure("broker account is not a verified demo account")
        if not _truthy(facts.terminal, "trade_allowed"):
            raise TransportFailure("terminal trading is disabled")
        if not _truthy(facts.account, "trade_allowed") or not _truthy(
            facts.account, "trade_expert"
        ):
            raise TransportFailure("account expert trading is disabled")
        constants = self._gateway.constants
        if _int_value(
            facts.symbol.get("trade_mode"),
            default=constants.symbol_trade_mode_disabled,
        ) == (
            constants.symbol_trade_mode_disabled
        ):
            raise TransportFailure("symbol trading is disabled")

        _validate_tick_freshness(facts.tick, ensure_utc(self._clock()), self._config)

        broker_symbol = facts.broker_symbol
        if str(facts.symbol.get("name", "")) != broker_symbol:
            raise TransportFailure("broker returned a different symbol")
        point = _positive_float(facts.symbol, "point")
        tick_size = _positive_float(facts.symbol, "trade_tick_size")
        if not math.isclose(point, intent.point_size, rel_tol=0.0, abs_tol=1e-12):
            raise TransportFailure("configured point size differs from broker point size")
        _validate_volume(intent.approved_volume_lots, facts.symbol)

        bid = _positive_float(facts.tick, "bid")
        ask = _positive_float(facts.tick, "ask")
        price = ask if intent.direction is Signal.BUY else bid
        _validate_stop(intent, price, point, tick_size, facts.symbol)
        order_type = (
            constants.order_type_buy
            if intent.direction is Signal.BUY
            else constants.order_type_sell
        )
        request: dict[str, object] = {
            "action": constants.trade_action_deal,
            "symbol": broker_symbol,
            "volume": intent.approved_volume_lots,
            "type": order_type,
            "price": price,
            "sl": intent.stop_loss_price,
            "deviation": self._config.deviation_points,
            "magic": self._config.magic,
            "comment": intent.intent_id,
            "type_time": constants.order_time_gtc,
            "type_filling": constants.order_filling_ioc,
        }
        return request

    def _facts(self, intent: ExecutionIntent) -> _SubmissionFacts:
        try:
            self._gateway.connect()
            terminal = self._gateway.terminal_info()
            account = self._gateway.account_info()
            broker_symbol = self._mapping.to_broker(intent.symbol)
            if broker_symbol != intent.broker_symbol:
                raise TransportFailure("intent broker symbol differs from explicit mapping")
            if terminal is None or not _truthy(terminal, "connected"):
                raise TransportFailure("MT5 terminal is not connected")
            if account is None:
                raise TransportFailure("MT5 account information is unavailable")
            if not self._gateway.symbol_select(broker_symbol, True):
                raise TransportFailure("configured MT5 symbol could not be selected")
            symbol = self._gateway.symbol_info(broker_symbol)
            tick = self._gateway.symbol_info_tick(broker_symbol)
            if symbol is None or tick is None:
                raise TransportFailure("MT5 symbol or tick facts are unavailable")
            return _SubmissionFacts(terminal, account, symbol, tick, broker_symbol)
        except TransportFailure:
            raise
        except Exception as exc:
            raise TransportFailure(f"MT5 preflight failed: {exc}") from exc


class _SubmissionFacts:
    def __init__(
        self,
        terminal: Mapping[str, object],
        account: Mapping[str, object],
        symbol: Mapping[str, object],
        tick: Mapping[str, object],
        broker_symbol: str,
    ) -> None:
        self.terminal = terminal
        self.account = account
        self.symbol = symbol
        self.tick = tick
        self.broker_symbol = broker_symbol


def _account_mode(
    account: Mapping[str, object], gateway: MT5Gateway
) -> ExecutionAccountMode:
    trade_mode = _int_value(account.get("trade_mode"), default=-1)
    constants = gateway.constants
    if trade_mode == constants.account_trade_mode_demo:
        return ExecutionAccountMode.DEMO
    if trade_mode == constants.account_trade_mode_real:
        return ExecutionAccountMode.LIVE
    return ExecutionAccountMode.UNKNOWN


def _tick_time(tick: Mapping[str, object]) -> datetime:
    raw = tick.get("time_msc")
    if raw is None:
        raise TransportFailure("MT5 tick lacks time_msc")
    return datetime.fromtimestamp(_float_value(raw) / 1000.0, tz=UTC)


def _positive_float(values: Mapping[str, object], name: str) -> float:
    try:
        value = _float_value(values[name])
    except (KeyError, TypeError, ValueError) as exc:
        raise TransportFailure(f"MT5 {name} is unavailable") from exc
    if not math.isfinite(value) or value <= 0.0:
        raise TransportFailure(f"MT5 {name} must be finite and positive")
    return value


def _truthy(values: Mapping[str, object], name: str) -> bool:
    return values.get(name) is True or values.get(name) == 1


def _validate_volume(volume: float, symbol: Mapping[str, object]) -> None:
    minimum = _positive_float(symbol, "volume_min")
    maximum = _positive_float(symbol, "volume_max")
    step = _positive_float(symbol, "volume_step")
    if volume < minimum - 1e-12 or volume > maximum + 1e-12:
        raise TransportFailure("approved volume violates broker min/max constraints")
    steps = (volume - minimum) / step
    if not math.isclose(steps, round(steps), rel_tol=0.0, abs_tol=1e-8):
        raise TransportFailure("approved volume is not on the broker volume grid")


def _validate_stop(
    intent: ExecutionIntent,
    price: float,
    point: float,
    tick_size: float,
    symbol: Mapping[str, object],
) -> None:
    stop = intent.stop_loss_price
    directional = (intent.direction is Signal.BUY and stop < price) or (
        intent.direction is Signal.SELL and stop > price
    )
    if not directional:
        raise TransportFailure("stop loss would not reduce directional risk")
    grid = stop / tick_size
    if not math.isclose(grid, round(grid), rel_tol=0.0, abs_tol=1e-7):
        raise TransportFailure("stop loss is not aligned to broker tick size")
    stops_level = _int_value(symbol.get("trade_stops_level"), default=0)
    if abs(price - stop) + 1e-12 < stops_level * point:
        raise TransportFailure("stop loss violates broker stops level")


def _validate_tick_freshness(
    tick: Mapping[str, object], now: datetime, config: MT5TransportConfig
) -> None:
    tick_at = _tick_time(tick)
    age = (now - tick_at).total_seconds()
    if age < 0.0:
        raise TransportFailure("MT5 tick is later than the local UTC clock")
    if age > config.max_tick_age_seconds:
        raise TransportFailure("MT5 tick is stale at submission time")


def _int_value(value: object, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, (str, bytes, bytearray, int, float)):
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise TransportFailure(f"MT5 integer value is invalid: {value!r}") from exc
    raise TransportFailure(f"MT5 integer value is invalid: {value!r}")


def _float_value(value: object) -> float:
    if isinstance(value, (str, bytes, bytearray, int, float)):
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise TransportFailure(f"MT5 numeric value is invalid: {value!r}") from exc
    raise TransportFailure(f"MT5 numeric value is invalid: {value!r}")
