"""Exact-symbol read-only completed-bar source for live shadow operation."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, NamedTuple, cast

import pandas as pd

from axq.features import default_registry
from axq.mt5.contracts import MT5Gateway
from axq.mt5.time_normalization import (
    MT5BrokerTimeNormalizer,
    MT5TimeNormalizationError,
    MT5TimestampNormalizationTrace,
)
from axq.runtime import (
    ComponentFreshness,
    FreshnessStatus,
    MarketState,
    RuntimeEvent,
    RuntimeEventType,
)
from axq.runtime.shadow import LiveMarketStatus, ShadowMarketAvailability
from axq.tools import CausalFeatureSnapshot

_GROUPS = ("trend", "momentum", "volatility", "breakout", "statistical", "market_structure")
_SOURCE_COLUMNS = ("timestamp", "open", "high", "low", "close", "tick_volume", "spread")


class LiveShadowBar(NamedTuple):
    event: RuntimeEvent
    feature_snapshot: CausalFeatureSnapshot
    m5_trace: MT5TimestampNormalizationTrace
    m15_trace: MT5TimestampNormalizationTrace


class LiveShadowPoll(NamedTuple):
    status: LiveMarketStatus
    availability: ShadowMarketAvailability
    bar: LiveShadowBar | None = None


def _tick_epochs(tick: Mapping[str, object]) -> tuple[int, int | None] | None:
    seconds = tick.get("time")
    milliseconds = tick.get("time_msc")
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds <= 0:
        return None
    value_msc = (
        int(milliseconds)
        if isinstance(milliseconds, (int, float))
        and not isinstance(milliseconds, bool)
        and milliseconds > 0
        else None
    )
    return int(seconds), value_msc


def _broker_last(tick: Mapping[str, object]) -> float | None:
    value = tick.get("last")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = float(value)
        return result if math.isfinite(result) and result > 0 else None
    return None


def _quote(tick: Mapping[str, object]) -> tuple[float, float] | None:
    bid_value = tick.get("bid")
    ask_value = tick.get("ask")
    if (
        isinstance(bid_value, bool)
        or not isinstance(bid_value, (int, float))
        or isinstance(ask_value, bool)
        or not isinstance(ask_value, (int, float))
    ):
        return None
    bid = float(bid_value)
    ask = float(ask_value)
    if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask < bid:
        return None
    return bid, ask


def _frame(
    rows: tuple[Mapping[str, object], ...],
    minutes: int,
    now: datetime,
    normalizer: MT5BrokerTimeNormalizer,
) -> pd.DataFrame:
    if not rows:
        raise ValueError("configured symbol returned no market bars")
    frame = pd.DataFrame(rows)
    missing = set(_SOURCE_COLUMNS[1:]) - set(frame.columns)
    if "time" not in frame or missing:
        raise ValueError(
            f"MT5 rates are missing fields: {sorted(missing | ({'time'} - set(frame)))}"
        )
    frame["_raw_broker_time"] = frame["time"].astype("int64")
    frame["timestamp"] = frame["_raw_broker_time"].map(
        normalizer.normalize_epoch_seconds
    )
    frame = frame.loc[frame["timestamp"] + timedelta(minutes=minutes) <= now]
    if frame.empty:
        raise ValueError("configured symbol has no completed market bars")
    if frame["timestamp"].duplicated().any():
        raise ValueError("configured symbol returned duplicate market bars")
    return frame[[*_SOURCE_COLUMNS, "_raw_broker_time"]].sort_values(
        "timestamp"
    ).reset_index(drop=True)


def _flag(value: object) -> object:
    return bool(float(cast(Any, value))) if pd.notna(cast(Any, value)) else value


def _available_values(values: Mapping[str, object]) -> dict[str, object]:
    """Drop mathematically unavailable values without inventing numeric defaults."""
    return {name: value for name, value in values.items() if not bool(pd.isna(cast(Any, value)))}


class MT5CompletedM5Source:
    """Poll completed M5/M15 history without discovery or terminal mutation."""

    def __init__(
        self,
        *,
        gateway: MT5Gateway,
        internal_symbol: str,
        broker_symbol: str,
        instrument_resolution_id: str,
        point_size: float,
        clock: Callable[[], datetime],
        history_bars: int = 320,
        stale_after_ms: int = 300_000,
        broker_time_normalizer: MT5BrokerTimeNormalizer,
    ) -> None:
        if history_bars < 250:
            raise ValueError("shadow feature warm-up requires at least 250 bars")
        if stale_after_ms <= 0:
            raise ValueError("stale_after_ms must be positive")
        if point_size <= 0:
            raise ValueError("point_size must be positive")
        self._gateway = gateway
        self._internal_symbol = internal_symbol
        self._broker_symbol = broker_symbol
        self._instrument_resolution_id = instrument_resolution_id
        self._point_size = point_size
        self._clock = clock
        self._history_bars = history_bars
        self._stale_after_ms = stale_after_ms
        self._broker_time = broker_time_normalizer
        self._last_close: datetime | None = None
        registry = default_registry()
        self._manifest = registry.manifest(
            feature_set_version="live-shadow-v1",
            enabled_groups=_GROUPS,
            available_source_columns=_SOURCE_COLUMNS,
        )

    @property
    def feature_manifest_id(self) -> str:
        return self._manifest.manifest_id

    def _availability(
        self,
        *,
        now: datetime,
        status: LiveMarketStatus,
        reason_code: str,
        tick_at: datetime | None,
        latest_m5: datetime | None = None,
        raw_tick_at: datetime | None = None,
    ) -> ShadowMarketAvailability:
        return ShadowMarketAvailability(
            resolved_broker_symbol=self._broker_symbol,
            instrument_resolution_id=self._instrument_resolution_id,
            time_offset_resolution_id=self._broker_time.resolution.resolution_id,
            observed_at=now,
            available_at=now,
            raw_broker_tick_at=raw_tick_at,
            broker_tick_at=tick_at,
            latest_completed_m5_at=latest_m5,
            status=status,
            reason_code=reason_code,
        )

    def poll(self) -> LiveShadowPoll:
        raw_now = self._clock()
        if raw_now.tzinfo is None or raw_now.utcoffset() is None:
            raise ValueError("shadow source clock must be timezone-aware")
        now = raw_now.astimezone(UTC)
        tick = self._gateway.symbol_info_tick(self._broker_symbol)
        if tick is None:
            availability = self._availability(
                now=now,
                status=LiveMarketStatus.UNAVAILABLE,
                reason_code="QUOTE_UNAVAILABLE",
                tick_at=None,
            )
            return LiveShadowPoll(availability.status, availability)
        # Arrival/observation time is captured after the broker response.
        now = self._clock().astimezone(UTC)
        tick_epochs = _tick_epochs(tick)
        if tick_epochs is None:
            availability = self._availability(
                now=now,
                status=LiveMarketStatus.UNAVAILABLE,
                reason_code="QUOTE_TIMESTAMP_UNAVAILABLE",
                tick_at=None,
            )
            return LiveShadowPoll(availability.status, availability)
        raw_tick_time, raw_tick_time_msc = tick_epochs
        raw_tick_at = datetime.fromtimestamp(
            (raw_tick_time_msc / 1_000) if raw_tick_time_msc else raw_tick_time,
            tz=UTC,
        )
        try:
            tick_trace = self._broker_time.normalize_tick(
                raw_tick_time=raw_tick_time,
                raw_tick_time_msc=raw_tick_time_msc,
                observed_at=now,
            )
        except MT5TimeNormalizationError as error:
            availability = self._availability(
                now=now,
                status=LiveMarketStatus.UNAVAILABLE,
                reason_code=f"BROKER_TIME_NORMALIZATION_FAILED:{type(error).__name__}",
                tick_at=None,
                raw_tick_at=raw_tick_at,
            )
            return LiveShadowPoll(availability.status, availability)
        tick_at = tick_trace.normalized_at
        age_ms = (now - tick_at).total_seconds() * 1_000
        if (
            age_ms < -self._broker_time.policy.future_tolerance_seconds * 1_000
            or age_ms > self._stale_after_ms
        ):
            availability = self._availability(
                now=now,
                status=LiveMarketStatus.STALE_QUOTE,
                reason_code="STALE_QUOTE",
                tick_at=tick_at,
                raw_tick_at=raw_tick_at,
            )
            return LiveShadowPoll(availability.status, availability)
        quote = _quote(tick)
        if quote is None:
            availability = self._availability(
                now=now,
                status=LiveMarketStatus.UNAVAILABLE,
                reason_code="QUOTE_UNAVAILABLE",
                tick_at=tick_at,
                raw_tick_at=raw_tick_at,
            )
            return LiveShadowPoll(availability.status, availability)
        m5_raw = self._gateway.copy_rates_from_pos(self._broker_symbol, "M5", 0, self._history_bars)
        m15_raw = self._gateway.copy_rates_from_pos(
            self._broker_symbol, "M15", 0, self._history_bars
        )
        m5 = _frame(m5_raw, 5, now, self._broker_time)
        m15 = _frame(m15_raw, 15, now, self._broker_time)
        close_time = m5.iloc[-1]["timestamp"].to_pydatetime() + timedelta(minutes=5)
        completed_bar_age_ms = (now - close_time).total_seconds() * 1_000
        if completed_bar_age_ms < 0 or completed_bar_age_ms > self._stale_after_ms:
            availability = self._availability(
                now=now,
                status=LiveMarketStatus.WAITING_FOR_NEXT_M5,
                reason_code="NO_FRESH_COMPLETED_M5",
                tick_at=tick_at,
                latest_m5=close_time,
                raw_tick_at=raw_tick_at,
            )
            return LiveShadowPoll(availability.status, availability)
        if self._last_close == close_time:
            availability = self._availability(
                now=now,
                status=LiveMarketStatus.WAITING_FOR_NEXT_M5,
                reason_code="WAITING_FOR_NEXT_COMPLETED_M5",
                tick_at=tick_at,
                latest_m5=close_time,
                raw_tick_at=raw_tick_at,
            )
            return LiveShadowPoll(availability.status, availability)
        m15 = m15.loc[m15["timestamp"] + timedelta(minutes=15) <= close_time]
        if m15.empty:
            raise ValueError("no completed M15 context is causally available")
        m5_trace = self._broker_time.trace(
            raw_epoch_seconds=int(m5.iloc[-1]["_raw_broker_time"]),
            source_kind="M5",
        )
        m15_trace = self._broker_time.trace(
            raw_epoch_seconds=int(m15.iloc[-1]["_raw_broker_time"]),
            source_kind="M15",
        )
        if m5_trace.normalized_at + timedelta(minutes=5) != close_time:
            raise ValueError("normalized M5 trace does not match decision close")
        if m15_trace.normalized_at + timedelta(minutes=15) > close_time:
            raise ValueError("normalized M15 context violates causal availability")
        registry = default_registry()
        m5_features = registry.compute(m5, enabled_groups=_GROUPS)
        m15_features = registry.compute(m15, enabled_groups=_GROUPS)
        m5_row = m5_features.iloc[-1]
        m15_row = m15_features.iloc[-1]
        values: dict[str, object] = {
            "m15_structure_bias": m15_row["structure_bias"],
            "m15_trend_adx_14": m15_row["trend_adx_14"],
            "m15_statistics_efficiency_ratio_20": m15_row["stat_efficiency_ratio_20"],
            "m15_volatility_expansion": m15_row["structure_range_expansion_20"],
            "m15_breakout_above": _flag(m15_row["breakout_above_20"]),
            "m15_breakout_below": _flag(m15_row["breakout_below_20"]),
        }
        for name in (
            "structure_hh",
            "structure_hl",
            "structure_lh",
            "structure_ll",
            "structure_bos_up",
            "structure_bos_down",
            "structure_choch_up",
            "structure_choch_down",
            "breakout_above_20",
            "breakout_below_20",
            "breakout_failed_up_20",
            "breakout_failed_down_20",
            "breakout_retest_up_20",
            "breakout_retest_down_20",
            "trend_close_to_ema_20",
            "trend_plus_di_14",
            "trend_minus_di_14",
            "momentum_macd_hist_12_26_9",
            "momentum_rsi_14",
            "trend_adx_14",
            "stat_return_zscore_20",
            "stat_efficiency_ratio_20",
            "structure_bias",
            "structure_range_expansion_20",
            "vol_atr_14",
        ):
            values[name] = m5_row[name]
        values.update(
            {
                "m5_structure_bias": m5_row["structure_bias"],
                "breakout_above": _flag(m5_row["breakout_above_20"]),
                "breakout_below": _flag(m5_row["breakout_below_20"]),
                "statistics_zscore_20": m5_row["stat_return_zscore_20"],
                "statistics_efficiency_ratio_20": m5_row["stat_efficiency_ratio_20"],
                "volatility_expansion": m5_row["structure_range_expansion_20"],
            }
        )
        for name in (
            "structure_hh",
            "structure_hl",
            "structure_lh",
            "structure_ll",
            "structure_bos_up",
            "structure_bos_down",
            "structure_choch_up",
            "structure_choch_down",
            "breakout_above_20",
            "breakout_below_20",
            "breakout_failed_up_20",
            "breakout_failed_down_20",
            "breakout_retest_up_20",
            "breakout_retest_down_20",
        ):
            values[name] = _flag(values[name])
        bid, ask = quote
        freshness = ComponentFreshness(
            component="market",
            status=FreshnessStatus.AVAILABLE,
            observed_at=now,
            available_at=now,
            stale_after_ms=300_000,
        )
        market = MarketState(
            source="mt5-shadow",
            symbol=self._internal_symbol,
            as_of=close_time,
            freshness=freshness,
            bid=bid,
            ask=ask,
            last=_broker_last(tick),
            spread_points=round((ask - bid) / self._point_size, 10),
            base_timeframe="M5",
            completed_timeframes=("M5", "M15"),
            feature_manifest_id=self.feature_manifest_id,
            market_data_version="mt5-shadow-v1",
        )
        event = RuntimeEvent(
            event_type=RuntimeEventType.M5_CLOSED,
            event_time=close_time,
            observed_at=now,
            available_at=now,
            source="mt5-shadow",
            source_version="1.0.0",
            source_sequence=int(close_time.timestamp()),
            symbol=self._internal_symbol,
            payload=market,
        )
        snapshot = CausalFeatureSnapshot.from_mapping(
            symbol=self._internal_symbol,
            base_timeframe="M5",
            as_of=close_time,
            available_at=now,
            feature_manifest_id=self.feature_manifest_id,
            completed_timeframes=("M5", "M15"),
            values=_available_values(values),
            source="phase2-feature-engine",
            source_version="2.0.0",
        )
        self._last_close = close_time
        availability = self._availability(
            now=now,
            status=LiveMarketStatus.BAR_READY,
            reason_code="NEW_COMPLETED_M5_AVAILABLE",
            tick_at=tick_at,
            latest_m5=close_time,
            raw_tick_at=raw_tick_at,
        )
        return LiveShadowPoll(
            availability.status,
            availability,
            LiveShadowBar(
                event=event,
                feature_snapshot=snapshot,
                m5_trace=m5_trace,
                m15_trace=m15_trace,
            ),
        )


__all__ = ["LiveMarketStatus", "LiveShadowBar", "LiveShadowPoll", "MT5CompletedM5Source"]
