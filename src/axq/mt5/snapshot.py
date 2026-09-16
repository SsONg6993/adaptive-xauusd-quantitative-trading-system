"""Read-only MT5 broker snapshot acquisition into canonical recovery state."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from axq.execution_boundary import (
    BrokerIntentLink,
    BrokerObjectKind,
    BrokerRecoverySnapshot,
)
from axq.mt5.contracts import (
    MT5Constants,
    MT5Gateway,
    MT5PersistedIntentLink,
    MT5SnapshotError,
    MT5SymbolMapping,
)
from axq.mt5.time_normalization import MT5BrokerTimeNormalizer, MT5TimeNormalizationError
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    ExposureState,
    FreshnessStatus,
    MarketState,
    OrderBookState,
    OrderState,
    OrderType,
    PositionBookState,
    PositionSide,
    PositionState,
)
from axq.runtime.clock import ensure_utc


class MT5BrokerSnapshotProvider:
    """Acquire one exact-symbol read-only broker snapshot without state mutation."""

    def __init__(
        self,
        *,
        gateway: MT5Gateway,
        symbol_mapping: MT5SymbolMapping,
        clock: Callable[[], datetime],
        source: str,
        source_version: str,
        stale_after_ms: int,
        select_symbol: bool = True,
        broker_time_normalizer: MT5BrokerTimeNormalizer | None = None,
    ) -> None:
        if stale_after_ms <= 0:
            raise ValueError("stale_after_ms must be positive")
        self._gateway = gateway
        self._mapping = symbol_mapping
        self._clock = clock
        self._source = source
        self._source_version = source_version
        self._stale_after_ms = stale_after_ms
        self._select_symbol = select_symbol
        self._broker_time = broker_time_normalizer

    def capture(
        self,
        *,
        linkages: tuple[MT5PersistedIntentLink, ...] = (),
    ) -> BrokerRecoverySnapshot:
        try:
            self._gateway.connect()
        except Exception as exc:
            raise MT5SnapshotError(f"CONNECTION_FAILED: {exc}") from exc
        observed_at = ensure_utc(self._clock())
        terminal = self._required(self._gateway.terminal_info(), "TERMINAL_UNAVAILABLE")
        if terminal.get("connected") is not True:
            raise MT5SnapshotError("DISCONNECTED: MT5 terminal is not connected")
        account_raw = self._required(self._gateway.account_info(), "ACCOUNT_UNAVAILABLE")
        broker_symbol = self._mapping.to_broker(self._mapping.internal_symbol)
        if self._select_symbol and not self._gateway.symbol_select(broker_symbol, True):
            raise MT5SnapshotError(
                f"SYMBOL_UNAVAILABLE: configured broker symbol {broker_symbol!r} cannot be selected"
            )
        symbol = self._required(
            self._gateway.symbol_info(broker_symbol),
            "SYMBOL_INFO_UNAVAILABLE",
        )
        if symbol.get("name") != broker_symbol:
            raise MT5SnapshotError("SYMBOL_MISMATCH: broker returned an unexpected symbol")
        tick = self._required(
            self._gateway.symbol_info_tick(broker_symbol),
            "TICK_UNAVAILABLE",
        )
        if self._broker_time is not None:
            # Observation time is arrival time: capture it after the broker read.
            observed_at = ensure_utc(self._clock())
        if self._broker_time is None:
            tick_time = _record_time(tick, observed_at)
        else:
            raw_seconds = _optional_int(tick.get("time"))
            if raw_seconds is None:
                raise MT5SnapshotError("TICK_TIME_UNAVAILABLE: broker tick has no time")
            try:
                tick_time = self._broker_time.normalize_tick(
                    raw_tick_time=raw_seconds,
                    raw_tick_time_msc=_optional_int(tick.get("time_msc")),
                    observed_at=observed_at,
                ).normalized_at
            except MT5TimeNormalizationError as exc:
                raise MT5SnapshotError(f"CLOCK_NORMALIZATION_FAILED: {exc}") from exc
            if tick_time > observed_at:
                # Preserve the exact normalized timestamp and wait only for the
                # already-validated sub-second operational skew to become causal.
                time.sleep((tick_time - observed_at).total_seconds())
                observed_at = ensure_utc(self._clock())
        if self._broker_time is None and tick_time > observed_at:
            raise MT5SnapshotError("CLOCK_SKEW: broker tick is later than observation time")
        if tick_time > observed_at:
            raise MT5SnapshotError(
                "CLOCK_SKEW: normalized broker tick remains later than observation time"
            )
        available_at = observed_at
        account = self._account(account_raw, observed_at)
        market = self._market(tick, symbol, tick_time, observed_at)
        provenance = _provenance_by_ticket(linkages)
        position_values = tuple(
            self._position(item, broker_symbol, provenance)
            for item in self._gateway.positions_get(broker_symbol)
        )
        order_values = tuple(
            self._order(item, broker_symbol, provenance)
            for item in self._gateway.orders_get(broker_symbol)
        )
        freshness = self._freshness("positions", observed_at)
        positions = PositionBookState(
            source=self._source,
            as_of=observed_at,
            freshness=freshness,
            positions=tuple(sorted(position_values, key=lambda item: item.position_id)),
        )
        orders = OrderBookState(
            source=self._source,
            as_of=observed_at,
            freshness=self._freshness("orders", observed_at),
            orders=tuple(sorted(order_values, key=lambda item: item.order_id)),
        )
        constraints = self._constraints(symbol, terminal, account_raw, observed_at)
        exposure = self._exposure(position_values, symbol, observed_at)
        intent_links = _canonical_links(linkages, position_values, order_values)
        return BrokerRecoverySnapshot(
            source=self._source,
            source_version=self._source_version,
            as_of=observed_at,
            observed_at=observed_at,
            available_at=available_at,
            account=account,
            market=market,
            positions=positions,
            orders=orders,
            exposure=exposure,
            broker_constraints=constraints,
            intent_links=intent_links,
        )

    @staticmethod
    def _required(
        value: Mapping[str, object] | None,
        code: str,
    ) -> Mapping[str, object]:
        if value is None:
            raise MT5SnapshotError(f"{code}: required MT5 response is unavailable")
        return value

    def _freshness(self, component: str, observed_at: datetime) -> ComponentFreshness:
        return ComponentFreshness(
            component=component,
            status=FreshnessStatus.AVAILABLE,
            observed_at=observed_at,
            available_at=observed_at,
            stale_after_ms=self._stale_after_ms,
        )

    def _account(self, raw: Mapping[str, object], at: datetime) -> AccountState:
        return AccountState(
            source=self._source,
            account_id=str(_required_int(raw, "login")),
            as_of=at,
            freshness=self._freshness("account", at),
            currency=_optional_str(raw.get("currency")),
            balance=_optional_float(raw.get("balance")),
            equity=_optional_float(raw.get("equity")),
            free_margin=_optional_float(raw.get("margin_free")),
            used_margin=_optional_float(raw.get("margin")),
            margin_level=_optional_float(raw.get("margin_level")),
            floating_pnl=_optional_float(raw.get("profit")),
        )

    def _market(
        self,
        tick: Mapping[str, object],
        symbol: Mapping[str, object],
        tick_time: datetime,
        observed_at: datetime,
    ) -> MarketState:
        point = _optional_float(symbol.get("point"))
        bid = _optional_float(tick.get("bid"))
        ask = _optional_float(tick.get("ask"))
        spread = None
        if point is not None and bid is not None and ask is not None:
            spread = round((ask - bid) / point, 10)
        age_ms = (observed_at - tick_time).total_seconds() * 1_000
        minimum_age_ms = (
            -self._broker_time.policy.future_tolerance_seconds * 1_000
            if self._broker_time is not None
            else 0
        )
        status = (
            FreshnessStatus.AVAILABLE
            if minimum_age_ms <= age_ms <= self._stale_after_ms
            else FreshnessStatus.STALE
        )
        freshness = ComponentFreshness(
            component="market",
            status=status,
            observed_at=observed_at,
            available_at=observed_at,
            stale_after_ms=self._stale_after_ms,
        )
        return MarketState(
            source=self._source,
            symbol=self._mapping.internal_symbol,
            as_of=tick_time,
            freshness=freshness,
            bid=bid,
            ask=ask,
            last=_optional_broker_last(tick.get("last")),
            spread_points=spread,
            base_timeframe="TICK",
            market_data_version=self._source_version,
        )

    def _position(
        self,
        raw: Mapping[str, object],
        broker_symbol: str,
        provenance: dict[tuple[BrokerObjectKind, int], MT5PersistedIntentLink],
    ) -> PositionState:
        _require_symbol(raw, broker_symbol)
        ticket = _required_int(raw, "ticket")
        link = provenance.get((BrokerObjectKind.POSITION, ticket))
        position_type = _required_int(raw, "type")
        if position_type == self._gateway.constants.position_type_buy:
            side = PositionSide.BUY
        elif position_type == self._gateway.constants.position_type_sell:
            side = PositionSide.SELL
        else:
            raise MT5SnapshotError(f"UNSUPPORTED_POSITION_TYPE: {position_type}")
        return PositionState(
            source=self._source,
            broker_ticket=ticket,
            symbol=self._mapping.internal_symbol,
            side=side,
            volume_lots=_required_float(raw, "volume"),
            opened_at=_epoch_seconds(_required_int(raw, "time")),
            open_price=_required_float(raw, "price_open"),
            current_price=_optional_float(raw.get("price_current")),
            stop_loss=_optional_price(raw.get("sl")),
            take_profit=_optional_price(raw.get("tp")),
            floating_pnl=_optional_float(raw.get("profit")),
            commission=_optional_float(raw.get("commission")),
            swap=_optional_float(raw.get("swap")),
            setup_id=link.setup_id if link else None,
            thesis_id=link.thesis_id if link else None,
        )

    def _order(
        self,
        raw: Mapping[str, object],
        broker_symbol: str,
        provenance: dict[tuple[BrokerObjectKind, int], MT5PersistedIntentLink],
    ) -> OrderState:
        _require_symbol(raw, broker_symbol)
        ticket = _required_int(raw, "ticket")
        link = provenance.get((BrokerObjectKind.ORDER, ticket))
        order_type = _order_type(_required_int(raw, "type"), self._gateway.constants)
        expiration = _optional_int(raw.get("time_expiration"))
        return OrderState(
            source=self._source,
            broker_ticket=ticket,
            symbol=self._mapping.internal_symbol,
            order_type=order_type,
            volume_lots=_required_float(raw, "volume_current"),
            created_at=_epoch_seconds(_required_int(raw, "time_setup")),
            price=_required_float(raw, "price_open"),
            stop_loss=_optional_price(raw.get("sl")),
            take_profit=_optional_price(raw.get("tp")),
            expires_at=_epoch_seconds(expiration) if expiration else None,
            setup_id=link.setup_id if link else None,
            thesis_id=link.thesis_id if link else None,
        )

    def _constraints(
        self,
        symbol: Mapping[str, object],
        terminal: Mapping[str, object],
        account: Mapping[str, object],
        at: datetime,
    ) -> BrokerConstraints:
        trade_mode = _optional_int(symbol.get("trade_mode"))
        trade_allowed = (
            terminal.get("trade_allowed") is True
            and account.get("trade_allowed") is True
            and account.get("trade_expert") is True
            and trade_mode is not None
            and trade_mode != self._gateway.constants.symbol_trade_mode_disabled
        )
        return BrokerConstraints(
            source=self._source,
            symbol=self._mapping.internal_symbol,
            as_of=at,
            freshness=self._freshness("broker_constraints", at),
            trade_allowed=trade_allowed,
            digits=_optional_int(symbol.get("digits")),
            volume_min=_optional_float(symbol.get("volume_min")),
            volume_max=_optional_float(symbol.get("volume_max")),
            volume_step=_optional_float(symbol.get("volume_step")),
            point_size=_optional_float(symbol.get("point")),
            tick_size=_optional_float(symbol.get("trade_tick_size")),
            tick_value_loss=_optional_float(symbol.get("trade_tick_value_loss")),
            stops_level_points=_optional_float(symbol.get("trade_stops_level")),
            freeze_level_points=_optional_float(symbol.get("trade_freeze_level")),
        )

    def _exposure(
        self,
        positions: tuple[PositionState, ...],
        symbol: Mapping[str, object],
        at: datetime,
    ) -> ExposureState:
        gross_lots = round(sum(item.volume_lots for item in positions), 10)
        net_lots = round(
            sum(
                item.volume_lots if item.side is PositionSide.BUY else -item.volume_lots
                for item in positions
            ),
            10,
        )
        contract_size = _optional_float(symbol.get("trade_contract_size"))
        notionals: tuple[float, ...] | None = None
        if contract_size is not None and all(
            item.current_price is not None for item in positions
        ):
            values: list[float] = []
            for item in positions:
                assert item.current_price is not None
                values.append(item.volume_lots * contract_size * item.current_price)
            notionals = tuple(values)
        gross_notional = round(sum(notionals), 10) if notionals is not None else None
        net_notional = None
        if notionals is not None:
            net_notional = round(
                sum(
                    value if item.side is PositionSide.BUY else -value
                    for item, value in zip(positions, notionals, strict=True)
                ),
                10,
            )
        return ExposureState(
            as_of=at,
            freshness=self._freshness("exposure", at),
            gross_lots=gross_lots,
            net_lots=net_lots,
            gross_notional=gross_notional,
            net_notional=net_notional,
        )


def _provenance_by_ticket(
    linkages: tuple[MT5PersistedIntentLink, ...],
) -> dict[tuple[BrokerObjectKind, int], MT5PersistedIntentLink]:
    values: dict[tuple[BrokerObjectKind, int], MT5PersistedIntentLink] = {}
    for linkage in linkages:
        key = (linkage.object_kind, linkage.broker_ticket)
        if key in values:
            raise MT5SnapshotError("DUPLICATE_LINKAGE: broker ticket has multiple intent links")
        values[key] = linkage
    return values


def _canonical_links(
    linkages: tuple[MT5PersistedIntentLink, ...],
    positions: tuple[PositionState, ...],
    orders: tuple[OrderState, ...],
) -> tuple[BrokerIntentLink, ...]:
    position_by_ticket = {item.broker_ticket: item.position_id for item in positions}
    order_by_ticket = {item.broker_ticket: item.order_id for item in orders}
    results: list[BrokerIntentLink] = []
    for linkage in sorted(linkages, key=lambda item: item.linkage_id):
        objects = (
            position_by_ticket
            if linkage.object_kind is BrokerObjectKind.POSITION
            else order_by_ticket
        )
        object_id = objects.get(linkage.broker_ticket)
        if object_id is None:
            raise MT5SnapshotError(
                f"MISSING_EXACT_LINK: exact broker ticket {linkage.broker_ticket} is absent"
            )
        results.append(
            BrokerIntentLink(
                intent_id=linkage.intent_id,
                object_kind=linkage.object_kind,
                broker_object_id=object_id,
                broker_ticket=linkage.broker_ticket,
                transport_execution_id=linkage.transport_execution_id,
            )
        )
    return tuple(results)


def _order_type(value: int, constants: MT5Constants) -> OrderType:
    pairs = {
        constants.order_type_buy_limit: OrderType.BUY_LIMIT,
        constants.order_type_sell_limit: OrderType.SELL_LIMIT,
        constants.order_type_buy_stop: OrderType.BUY_STOP,
        constants.order_type_sell_stop: OrderType.SELL_STOP,
        constants.order_type_buy_stop_limit: OrderType.BUY_STOP_LIMIT,
        constants.order_type_sell_stop_limit: OrderType.SELL_STOP_LIMIT,
    }
    try:
        return pairs[value]
    except KeyError as exc:
        raise MT5SnapshotError(f"UNSUPPORTED_ORDER_TYPE: {value}") from exc


def _record_time(raw: Mapping[str, object], fallback: datetime) -> datetime:
    milliseconds = _optional_int(raw.get("time_msc"))
    if milliseconds:
        return datetime.fromtimestamp(milliseconds / 1_000, tz=UTC)
    seconds = _optional_int(raw.get("time"))
    return _epoch_seconds(seconds) if seconds else fallback


def _epoch_seconds(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=UTC)


def _require_symbol(raw: Mapping[str, object], expected: str) -> None:
    if raw.get("symbol") != expected:
        raise MT5SnapshotError("SYMBOL_MISMATCH: broker object uses an unexpected symbol")


def _required_int(raw: Mapping[str, object], field: str) -> int:
    value = _optional_int(raw.get(field))
    if value is None:
        raise MT5SnapshotError(f"MISSING_FIELD: {field}")
    return value


def _required_float(raw: Mapping[str, object], field: str) -> float:
    value = _optional_float(raw.get(field))
    if value is None:
        raise MT5SnapshotError(f"MISSING_FIELD: {field}")
    return value


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MT5SnapshotError(f"INVALID_NUMERIC_VALUE: {value!r}")
    return float(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise MT5SnapshotError(f"INVALID_INTEGER_VALUE: {value!r}")
    return value


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MT5SnapshotError(f"INVALID_STRING_VALUE: {value!r}")
    return value


def _optional_price(value: object) -> float | None:
    result = _optional_float(value)
    return None if result in {None, 0.0} else result


def _optional_broker_last(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) and result > 0 else None
