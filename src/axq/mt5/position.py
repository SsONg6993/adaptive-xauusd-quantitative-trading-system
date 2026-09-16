"""Demo-only MetaTrader 5 transport for Task 7 position-action intents."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from axq.execution_boundary import (
    ExecutionMode,
    ExecutionReason,
    ExecutionResultStatus,
    TransportFailure,
    UnknownSubmissionState,
)
from axq.mt5.contracts import MT5Gateway, MT5SymbolMapping
from axq.mt5.preflight import MT5TransportConfig, default_mt5_transport_config
from axq.position_actions import PositionActionIntent, PositionActionType
from axq.position_actions.transport import (
    PositionActionTransportLedger,
    PositionActionTransportResult,
)
from axq.runtime import PositionSide
from axq.runtime.clock import ensure_utc


class MT5PositionActionAdapter:
    """Idempotently translate an already-safe position action to exact MT5 calls."""

    def __init__(
        self,
        *,
        mode: ExecutionMode,
        ledger: PositionActionTransportLedger,
        gateway: MT5Gateway,
        symbol_mapping: MT5SymbolMapping,
        clock: Callable[[], datetime],
        kill_switch: Callable[[], bool],
        config: MT5TransportConfig | None = None,
    ) -> None:
        self._mode = mode
        self._ledger = ledger
        self._gateway = gateway
        self._mapping = symbol_mapping
        self._clock = clock
        self._kill_switch = kill_switch
        self._config = config or default_mt5_transport_config()

    def execute(self, intent: PositionActionIntent) -> PositionActionTransportResult:
        prior = self._ledger.get(intent.intent_id)
        if prior is not None:
            return prior
        if not self._ledger.reserve(intent):
            result = self._result(
                intent,
                status=ExecutionResultStatus.UNKNOWN,
                reason_code=ExecutionReason.UNKNOWN_SUBMISSION,
                reason="reserved position action requires reconciliation",
            )
            self._ledger.record(result)
            return result
        if self._mode is ExecutionMode.DISABLED:
            return self._record(
                self._result(
                    intent,
                    status=ExecutionResultStatus.NO_ACTION,
                    reason_code=ExecutionReason.EXECUTION_DISABLED,
                    reason=ExecutionReason.EXECUTION_DISABLED.value,
                )
            )
        try:
            request = self._checked_request(intent)
        except TransportFailure as exc:
            return self._record(
                self._result(
                    intent,
                    status=ExecutionResultStatus.FAILED,
                    reason_code=ExecutionReason.TRANSPORT_FAILED,
                    reason=str(exc),
                )
            )
        if self._mode is ExecutionMode.DRY_RUN:
            return self._record(
                self._result(
                    intent,
                    status=ExecutionResultStatus.NO_ACTION,
                    reason_code=ExecutionReason.DRY_RUN,
                    reason=ExecutionReason.DRY_RUN.value,
                )
            )
        try:
            # Re-read position/account/tick state and repeat order_check immediately
            # before crossing the only mutation boundary.
            request = self._checked_request(intent)
            response = self._gateway.order_send(request)
        except UnknownSubmissionState as exc:
            return self._record(
                self._result(
                    intent,
                    status=ExecutionResultStatus.UNKNOWN,
                    reason_code=ExecutionReason.UNKNOWN_SUBMISSION,
                    reason=str(exc),
                )
            )
        except TransportFailure as exc:
            return self._record(
                self._result(
                    intent,
                    status=ExecutionResultStatus.FAILED,
                    reason_code=ExecutionReason.TRANSPORT_FAILED,
                    reason=str(exc),
                )
            )
        except Exception as exc:
            return self._record(
                self._result(
                    intent,
                    status=ExecutionResultStatus.UNKNOWN,
                    reason_code=ExecutionReason.UNKNOWN_SUBMISSION,
                    reason=f"MT5 order_send outcome is unknown: {exc}",
                )
            )
        if response is None:
            return self._record(
                self._result(
                    intent,
                    status=ExecutionResultStatus.UNKNOWN,
                    reason_code=ExecutionReason.UNKNOWN_SUBMISSION,
                    reason="MT5 order_send returned no acknowledgement; reconciliation required",
                )
            )
        try:
            result = self._broker_result(intent, response)
        except Exception as exc:
            result = self._result(
                intent,
                status=ExecutionResultStatus.UNKNOWN,
                reason_code=ExecutionReason.UNKNOWN_SUBMISSION,
                reason=f"MT5 acknowledgement could not be interpreted: {exc}",
            )
        return self._record(result)

    def _checked_request(self, intent: PositionActionIntent) -> dict[str, object]:
        if self._kill_switch():
            raise TransportFailure("execution kill switch is active")
        try:
            self._gateway.connect()
            terminal = self._gateway.terminal_info()
            account = self._gateway.account_info()
            broker_symbol = self._mapping.to_broker(intent.symbol)
            if terminal is None or not _truthy(terminal.get("connected")):
                raise TransportFailure("MT5 terminal is not connected")
            if not _truthy(terminal.get("trade_allowed")):
                raise TransportFailure("terminal trading is disabled")
            if account is None or _int_value(account.get("trade_mode"), default=-1) != (
                self._gateway.constants.account_trade_mode_demo
            ):
                raise TransportFailure("broker account is not a verified demo account")
            if not _truthy(account.get("trade_allowed")) or not _truthy(
                account.get("trade_expert")
            ):
                raise TransportFailure("account expert trading is disabled")
            if intent.broker_ticket is None:
                raise TransportFailure("position action lacks exact broker ticket")
            if not self._gateway.symbol_select(broker_symbol, True):
                raise TransportFailure("configured MT5 symbol could not be selected")
            positions = tuple(self._gateway.positions_get(broker_symbol))
            matches = [
                item
                for item in positions
                if _int_value(item.get("ticket"), default=-1) == intent.broker_ticket
            ]
            if len(matches) != 1:
                raise TransportFailure("exact broker-ticket position match is unavailable")
            position = matches[0]
            symbol = self._gateway.symbol_info(broker_symbol)
            tick = self._gateway.symbol_info_tick(broker_symbol)
            if symbol is None or tick is None:
                raise TransportFailure("MT5 symbol or tick facts are unavailable")
            if str(symbol.get("name", "")) != broker_symbol:
                raise TransportFailure("broker returned a different symbol")
            if _int_value(
                symbol.get("trade_mode"),
                default=self._gateway.constants.symbol_trade_mode_disabled,
            ) == self._gateway.constants.symbol_trade_mode_disabled:
                raise TransportFailure("symbol trading is disabled")
            tick_raw = tick.get("time_msc")
            if tick_raw is None:
                raise TransportFailure("MT5 tick lacks time_msc")
            now = ensure_utc(self._clock())
            tick_at = datetime.fromtimestamp(_float_value(tick_raw) / 1000.0, tz=UTC)
            age = (now - tick_at).total_seconds()
            if age < 0.0 or age > self._config.max_tick_age_seconds:
                raise TransportFailure("MT5 tick is stale or ahead at submission time")
            self._validate_position(intent, position, broker_symbol)
            request = self._request(intent, position, symbol, tick, broker_symbol)
            check = self._gateway.order_check(request)
            if check is None or _int_value(check.get("retcode"), default=-1) != 0:
                raise TransportFailure(f"MT5 order_check rejected position action: {check!r}")
            return request
        except TransportFailure:
            raise
        except Exception as exc:
            raise TransportFailure(f"MT5 position-action preflight failed: {exc}") from exc

    def _validate_position(
        self,
        intent: PositionActionIntent,
        position: Mapping[str, object],
        broker_symbol: str,
    ) -> None:
        if str(position.get("symbol", "")) != broker_symbol:
            raise TransportFailure("exact ticket resolved to a different broker symbol")
        expected_type = (
            self._gateway.constants.position_type_buy
            if intent.position_side is PositionSide.BUY
            else self._gateway.constants.position_type_sell
        )
        if _int_value(position.get("type"), default=-1) != expected_type:
            raise TransportFailure("broker position direction changed")
        volume = _float_value(position.get("volume"), default=0.0)
        if not math.isclose(volume, intent.current_volume_lots, abs_tol=1e-10, rel_tol=0.0):
            raise TransportFailure("broker position volume changed")
        actual_stop = _optional_price(position.get("sl"))
        if not _optional_close(actual_stop, intent.existing_stop_loss):
            raise TransportFailure("broker protective stop changed")

    def _request(
        self,
        intent: PositionActionIntent,
        position: Mapping[str, object],
        symbol: Mapping[str, object],
        tick: Mapping[str, object],
        broker_symbol: str,
    ) -> dict[str, object]:
        constants = self._gateway.constants
        base: dict[str, object] = {
            "symbol": broker_symbol,
            "position": intent.broker_ticket,
            "magic": self._config.magic,
            "comment": intent.intent_id,
        }
        if intent.action_type is PositionActionType.MODIFY_PROTECTIVE_STOP:
            stop = intent.requested_new_stop_loss
            if stop is None:
                raise TransportFailure("protective action lacks requested stop")
            current_stop = _optional_price(position.get("sl"))
            risk_reducing = (
                intent.position_side is PositionSide.BUY
                and (current_stop is None or stop >= current_stop)
            ) or (
                intent.position_side is PositionSide.SELL
                and (current_stop is None or stop <= current_stop)
            )
            if not risk_reducing:
                raise TransportFailure("protective stop is not monotonic")
            point = _required_positive(symbol, "point")
            tick_size = _required_positive(symbol, "trade_tick_size")
            price = (
                _required_positive(tick, "bid")
                if intent.position_side is PositionSide.BUY
                else _required_positive(tick, "ask")
            )
            directional = (intent.position_side is PositionSide.BUY and stop < price) or (
                intent.position_side is PositionSide.SELL and stop > price
            )
            if not directional:
                raise TransportFailure("protective stop is on the invalid market side")
            if not math.isclose(
                stop / tick_size, round(stop / tick_size), abs_tol=1e-7, rel_tol=0.0
            ):
                raise TransportFailure("protective stop is off the broker tick grid")
            minimum = max(
                _int_value(symbol.get("trade_stops_level"), default=0),
                _int_value(symbol.get("trade_freeze_level"), default=0),
            )
            if abs(price - stop) + 1e-12 < minimum * point:
                raise TransportFailure("protective stop violates broker stop/freeze distance")
            return base | {
                "action": constants.trade_action_sltp,
                "sl": stop,
                "tp": _optional_price(position.get("tp")) or 0.0,
            }

        volume = intent.requested_close_volume_lots
        if volume is None or not math.isclose(
            volume, intent.current_volume_lots, abs_tol=1e-10, rel_tol=0.0
        ):
            raise TransportFailure("position action is not an exact full close")
        _validate_volume(volume, symbol)
        closing_buy = intent.position_side is PositionSide.SELL
        return base | {
            "action": constants.trade_action_deal,
            "volume": volume,
            "type": constants.order_type_buy if closing_buy else constants.order_type_sell,
            "price": _required_positive(tick, "ask" if closing_buy else "bid"),
            "deviation": self._config.deviation_points,
            "type_time": constants.order_time_gtc,
            "type_filling": constants.order_filling_ioc,
        }

    def _broker_result(
        self, intent: PositionActionIntent, response: Mapping[str, object]
    ) -> PositionActionTransportResult:
        retcode = _int_value(response.get("retcode"), default=-1)
        constants = self._gateway.constants
        status = {
            constants.trade_retcode_placed: ExecutionResultStatus.ACCEPTED,
            constants.trade_retcode_done: ExecutionResultStatus.FILLED,
            constants.trade_retcode_done_partial: ExecutionResultStatus.PARTIALLY_FILLED,
        }.get(retcode, ExecutionResultStatus.REJECTED)
        reason_code = (
            ExecutionReason.BROKER_REJECTED
            if status is ExecutionResultStatus.REJECTED
            else None
        )
        executed = None
        fill_price = None
        if intent.action_type is PositionActionType.CLOSE_POSITION:
            executed = _float_value(response.get("volume"), default=0.0)
            fill_price = _optional_price(response.get("price"))
        deal = _positive_int(response.get("deal"))
        order = _positive_int(response.get("order"))
        transport_id = f"mt5-deal-{deal}" if deal else f"mt5-order-{order}" if order else None
        return self._result(
            intent,
            status=status,
            reason_code=reason_code,
            reason=str(response.get("comment")) if reason_code else None,
            executed_volume_lots=executed,
            fill_price=fill_price,
            transport_execution_id=transport_id,
            broker_retcode=str(retcode),
            broker_status=str(response.get("comment", "")),
        )

    def _result(
        self,
        intent: PositionActionIntent,
        *,
        status: ExecutionResultStatus,
        reason_code: ExecutionReason | None,
        reason: str | None,
        executed_volume_lots: float | None = None,
        fill_price: float | None = None,
        transport_execution_id: str | None = None,
        broker_retcode: str | None = None,
        broker_status: str | None = None,
    ) -> PositionActionTransportResult:
        at = ensure_utc(self._clock())
        if intent.broker_ticket is None:
            raise ValueError("transport result requires exact broker ticket")
        return PositionActionTransportResult(
            position_action_intent_id=intent.intent_id,
            action_type=intent.action_type,
            position_id=intent.position_id,
            broker_ticket=intent.broker_ticket,
            symbol=intent.symbol,
            position_side=intent.position_side,
            status=status,
            reason_code=reason_code,
            reason=reason,
            requested_volume_lots=intent.requested_close_volume_lots,
            executed_volume_lots=executed_volume_lots,
            requested_stop_loss=intent.requested_new_stop_loss,
            fill_price=fill_price,
            transport_execution_id=transport_execution_id,
            broker_retcode=broker_retcode,
            broker_status=broker_status,
            event_time=at,
            observed_at=at,
            available_at=at,
        )

    def _record(self, result: PositionActionTransportResult) -> PositionActionTransportResult:
        self._ledger.record(result)
        return result


def _required_positive(values: Mapping[str, object], key: str) -> float:
    value = _float_value(values.get(key), default=0.0)
    if not math.isfinite(value) or value <= 0.0:
        raise TransportFailure(f"MT5 {key} must be finite and positive")
    return value


def _optional_price(value: object) -> float | None:
    parsed = _float_value(value, default=0.0)
    return parsed if math.isfinite(parsed) and parsed > 0.0 else None


def _optional_close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, abs_tol=1e-10, rel_tol=0.0)


def _positive_int(value: object) -> int | None:
    parsed = _int_value(value, default=0)
    return parsed if parsed > 0 else None


def _truthy(value: object) -> bool:
    return value is True or value == 1


def _int_value(value: object, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return int(value)
    raise ValueError(f"invalid MT5 integer value: {value!r}")


def _float_value(value: object, *, default: float | None = None) -> float:
    if value is None:
        if default is None:
            raise ValueError("missing MT5 numeric value")
        return default
    if isinstance(value, (str, bytes, bytearray, int, float)):
        return float(value)
    raise ValueError(f"invalid MT5 numeric value: {value!r}")


def _validate_volume(volume: float, symbol: Mapping[str, object]) -> None:
    minimum = _required_positive(symbol, "volume_min")
    maximum = _required_positive(symbol, "volume_max")
    step = _required_positive(symbol, "volume_step")
    if volume < minimum - 1e-12 or volume > maximum + 1e-12:
        raise TransportFailure("close volume violates broker min/max constraints")
    steps = (volume - minimum) / step
    if not math.isclose(steps, round(steps), abs_tol=1e-8, rel_tol=0.0):
        raise TransportFailure("close volume is not on the broker volume grid")


__all__ = ["MT5PositionActionAdapter"]
