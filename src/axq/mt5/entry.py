"""Demo-only MetaTrader 5 transport behind the shared execution boundary."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from datetime import datetime

from axq.execution_boundary import (
    BrokerExecutionReport,
    DemoExecutionAdapter,
    ExecutionAdapter,
    ExecutionIntent,
    ExecutionLedger,
    ExecutionObservation,
    ExecutionPolicy,
    ExecutionResult,
    ExecutionResultStatus,
    ExecutionTransport,
    TransportFailure,
    UnknownSubmissionState,
)
from axq.mt5.contracts import MT5Gateway, MT5SymbolMapping
from axq.mt5.preflight import (
    MT5EntryPreflight,
    MT5TransportConfig,
    default_mt5_transport_config,
)
from axq.runtime.clock import ensure_utc


class MT5ExecutionTransport(ExecutionTransport):
    """Translate one validated entry intent into one non-retried MT5 submission."""

    def __init__(
        self,
        *,
        gateway: MT5Gateway,
        preflight: MT5EntryPreflight,
        clock: Callable[[], datetime],
    ) -> None:
        self._gateway = gateway
        self._preflight = preflight
        self._clock = clock

    def submit(
        self, intent: ExecutionIntent, observation: ExecutionObservation
    ) -> BrokerExecutionReport:
        del observation
        request = self._preflight.checked_request(intent)
        try:
            check = self._gateway.order_check(request)
        except Exception as exc:
            raise TransportFailure(f"MT5 order_check failed before submission: {exc}") from exc
        if check is None:
            raise TransportFailure(
                f"MT5 order_check returned no result: {self._gateway.last_error()!r}"
            )
        if _int_value(check.get("retcode"), default=-1) != 0:
            raise TransportFailure(
                f"MT5 order_check rejected immediately before send: {check!r}"
            )
        try:
            response = self._gateway.order_send(request)
        except Exception as exc:
            raise UnknownSubmissionState(
                f"MT5 order_send outcome is unknown: {exc}"
            ) from exc
        if response is None:
            raise UnknownSubmissionState(
                "MT5 order_send returned no acknowledgement; reconciliation required"
            )
        try:
            return self._report(intent, response)
        except Exception as exc:
            raise UnknownSubmissionState(
                f"MT5 acknowledgement could not be interpreted: {exc}"
            ) from exc

    def _report(
        self, intent: ExecutionIntent, response: Mapping[str, object]
    ) -> BrokerExecutionReport:
        constants = self._gateway.constants
        retcode = _int_value(response.get("retcode"), default=-1)
        status = {
            constants.trade_retcode_placed: ExecutionResultStatus.ACCEPTED,
            constants.trade_retcode_done: ExecutionResultStatus.FILLED,
            constants.trade_retcode_done_partial: ExecutionResultStatus.PARTIALLY_FILLED,
        }.get(retcode, ExecutionResultStatus.REJECTED)
        volume = _float_value(response.get("volume"), default=0.0)
        price_raw = response.get("price")
        price = _float_value(price_raw) if price_raw not in {None, 0} else None
        if status is ExecutionResultStatus.FILLED and (
            not math.isclose(
                volume,
                intent.approved_volume_lots,
                abs_tol=1e-10,
                rel_tol=0.0,
            )
            or price is None
        ):
            raise ValueError("filled MT5 acknowledgement lacks exact volume or price")
        if status is ExecutionResultStatus.PARTIALLY_FILLED and not (
            0.0 < volume < intent.approved_volume_lots and price is not None
        ):
            raise ValueError("partial MT5 acknowledgement lacks strict fill facts")
        ticket = _positive_int(response.get("deal")) or _positive_int(
            response.get("order")
        )
        transport_id = None
        deal = _positive_int(response.get("deal"))
        order = _positive_int(response.get("order"))
        if deal is not None:
            transport_id = f"mt5-deal-{deal}"
        elif order is not None:
            transport_id = f"mt5-order-{order}"
        at = ensure_utc(self._clock())
        return BrokerExecutionReport(
            status=status,
            event_time=at,
            observed_at=at,
            available_at=at,
            broker_ticket=ticket,
            transport_execution_id=transport_id,
            filled_volume_lots=volume,
            fill_price=price,
            broker_retcode=str(retcode),
            broker_status=str(response.get("retcode", "")),
            message=(
                str(response["comment"]) if response.get("comment") is not None else None
            ),
        )


class MT5ExecutionAdapter(ExecutionAdapter):
    """Compose MT5 facts/transport with the existing durable demo adapter."""

    def __init__(
        self,
        *,
        policy: ExecutionPolicy,
        ledger: ExecutionLedger,
        gateway: MT5Gateway,
        symbol_mapping: MT5SymbolMapping,
        config: MT5TransportConfig,
        clock: Callable[[], datetime],
        kill_switch: Callable[[], bool],
    ) -> None:
        preflight = MT5EntryPreflight(
            gateway=gateway,
            symbol_mapping=symbol_mapping,
            config=config,
            clock=clock,
            kill_switch=kill_switch,
        )
        transport = MT5ExecutionTransport(
            gateway=gateway,
            preflight=preflight,
            clock=clock,
        )
        self._adapter = DemoExecutionAdapter(
            policy=policy,
            ledger=ledger,
            observation_provider=preflight.observe,
            transport=transport,
            preflight_validator=preflight.validate,
        )

    def execute(self, intent: ExecutionIntent) -> ExecutionResult:
        return self._adapter.execute(intent)


def _positive_int(value: object) -> int | None:
    parsed = _int_value(value, default=0)
    return parsed if parsed > 0 else None


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


__all__ = [
    "MT5ExecutionAdapter",
    "MT5ExecutionTransport",
    "MT5TransportConfig",
    "default_mt5_transport_config",
]
