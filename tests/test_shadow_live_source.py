from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.mt5.live_source import LiveMarketStatus, MT5CompletedM5Source
from axq.mt5.time_normalization import (
    MT5BrokerEnvironmentIdentity,
    MT5BrokerTimeNormalizer,
    infer_broker_time_offset,
)
from axq.runtime import RuntimeEventType


class FakeRatesGateway:
    def __init__(self, now: datetime) -> None:
        self.now = now
        self.mutations = 0
        self.rate_calls = 0
        self.rate_requests: list[tuple[str, int]] = []
        self.symbol_info_calls = 0
        self.tick_symbols: list[str] = []

    def symbol_info(self, symbol: str) -> dict[str, object] | None:
        self.symbol_info_calls += 1
        return {"name": symbol, "point": 0.01}

    def symbol_info_tick(self, symbol: str) -> dict[str, object] | None:
        self.tick_symbols.append(symbol)
        return {
            "symbol": symbol,
            "bid": 2500.0,
            "ask": 2500.2,
            "last": 2500.1,
            "time": int(self.now.timestamp()),
        }

    def copy_rates_from_pos(
        self, symbol: str, timeframe: str, start_pos: int, count: int
    ) -> tuple[dict[str, object], ...]:
        del symbol, start_pos
        self.rate_calls += 1
        self.rate_requests.append((timeframe, count))
        minutes = 5 if timeframe == "M5" else 15
        rows = count
        last_open = self.now.replace(second=0, microsecond=0)
        last_open -= timedelta(minutes=last_open.minute % minutes)
        result = []
        for index in range(rows):
            opened = last_open - timedelta(minutes=minutes * (rows - index - 1))
            close = 2400.0 + index * 0.5
            result.append(
                {
                    "time": int(opened.timestamp()),
                    "open": close - 0.2,
                    "high": close + 0.8,
                    "low": close - 0.8,
                    "close": close,
                    "tick_volume": 100 + index,
                    "spread": 20,
                    "real_volume": 0,
                }
            )
        return tuple(result)

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        del symbol, enabled
        self.mutations += 1
        raise AssertionError("shadow source must not select symbols")

    def order_check(self, request: object) -> None:
        del request
        self.mutations += 1
        raise AssertionError("shadow source must not check orders")

    def order_send(self, request: object) -> None:
        del request
        self.mutations += 1
        raise AssertionError("shadow source must not send orders")


def _normalizer(now: datetime, *, hours: int = 0) -> MT5BrokerTimeNormalizer:
    raw = now + timedelta(hours=hours)
    return MT5BrokerTimeNormalizer(
        infer_broker_time_offset(
            raw_tick_time=int(raw.timestamp()),
            raw_tick_time_msc=int(raw.timestamp() * 1_000),
            observed_at=now,
            canonical_instrument="XAUUSD",
            resolved_broker_symbol="XAUUSD.sc",
            instrument_resolution_id="rbi-shadow",
            environment=MT5BrokerEnvironmentIdentity(
                broker_server="test",
                account_login_digest="login-digest",
                account_trade_mode=0,
                terminal_company="test",
                terminal_build=1,
            ),
        )
    )


def test_live_source_uses_latest_completed_m5_once_and_exact_symbol() -> None:
    now = datetime(2026, 9, 14, 12, 2, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now),
    )

    first = source.poll()
    second = source.poll()

    assert first.status is LiveMarketStatus.BAR_READY
    assert first.bar is not None
    assert first.bar.event.event_type is RuntimeEventType.M5_CLOSED
    assert first.bar.event.event_time == datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    assert first.bar.event.symbol == "XAUUSD"
    assert first.bar.event.payload.last == 2500.1
    assert first.bar.event.payload.freshness.observed_at == now
    assert first.bar.feature_snapshot.symbol == "XAUUSD"
    assert first.bar.feature_snapshot.completed_timeframes == ("M15", "M5")
    assert first.bar.feature_snapshot.feature_manifest_id == source.feature_manifest_id
    assert second.status is LiveMarketStatus.WAITING_FOR_NEXT_M5
    assert second.bar is None
    assert gateway.mutations == 0
    assert gateway.symbol_info_calls == 0
    assert gateway.rate_requests == [("M5", 2), ("M5", 320), ("M15", 2), ("M15", 320), ("M5", 2)]


def test_idle_poll_only_checks_tick_and_two_m5_rows() -> None:
    now = datetime(2026, 9, 14, 12, 2, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now),
    )

    assert source.poll().bar is not None
    gateway.rate_requests.clear()

    for _ in range(20):
        result = source.poll()
        assert result.status is LiveMarketStatus.WAITING_FOR_NEXT_M5
        assert source.last_performance.expensive_cycle is False

    assert gateway.rate_requests == [("M5", 2)] * 20


def test_new_m5_reuses_causally_unchanged_m15_features() -> None:
    gateway = FakeRatesGateway(datetime(2026, 9, 14, 12, 2, tzinfo=UTC))
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: gateway.now,
        broker_time_normalizer=_normalizer(gateway.now),
    )

    assert source.poll().bar is not None
    assert source.last_performance.m15_cache_hit is False
    gateway.rate_requests.clear()
    gateway.now += timedelta(minutes=5)

    second = source.poll()

    assert second.bar is not None
    assert source.last_performance.m15_cache_hit is True
    assert source.last_performance.m15_feature_latency_ms == 0.0
    assert gateway.rate_requests == [("M5", 2), ("M5", 320), ("M15", 2)]


def test_live_source_uses_startup_resolution_without_reresolving_or_fallback() -> None:
    now = datetime(2026, 9, 14, 12, 2, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    gateway.symbol_info = lambda symbol: None  # type: ignore[method-assign]
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now),
    )

    result = source.poll()

    assert result.bar is not None
    assert gateway.symbol_info_calls == 0
    assert gateway.tick_symbols == ["XAUUSD.sc"]
    assert gateway.mutations == 0


@pytest.mark.parametrize("broker_last", [0.0, -1.0, float("nan"), "invalid"])
def test_invalid_broker_last_is_never_replaced_with_midpoint(broker_last: object) -> None:
    now = datetime(2026, 9, 14, 12, 2, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "bid": 4348.10,
        "ask": 4348.45,
        "last": broker_last,
        "time": int(now.timestamp()),
    }
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now),
    )

    result = source.poll()

    assert result.bar is not None
    market = result.bar.event.payload
    assert market.bid == 4348.10
    assert market.ask == 4348.45
    assert market.last is None
    assert market.last != (4348.10 + 4348.45) / 2


def test_stale_weekend_quote_waits_without_requesting_or_emitting_old_bars() -> None:
    now = datetime(2026, 9, 14, 12, 2, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    stale_tick_at = now - timedelta(days=2)
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "bid": 4348.10,
        "ask": 4348.45,
        "last": 0.0,
        "time": int(stale_tick_at.timestamp()),
    }
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now),
    )

    result = source.poll()

    assert result.status is LiveMarketStatus.STALE_QUOTE
    assert result.bar is None
    assert result.availability.broker_tick_at == stale_tick_at
    assert gateway.rate_calls == 0


def test_invalid_bid_ask_waits_without_requesting_bars() -> None:
    now = datetime(2026, 9, 14, 12, 2, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "bid": 0.0,
        "ask": 4348.45,
        "last": 0.0,
        "time": int(now.timestamp()),
    }
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now),
    )

    result = source.poll()

    assert result.status is LiveMarketStatus.UNAVAILABLE
    assert result.bar is None
    assert result.availability.reason_code == "QUOTE_UNAVAILABLE"
    assert gateway.rate_calls == 0


def test_fresh_tick_does_not_emit_stale_completed_bar() -> None:
    now = datetime(2026, 9, 14, 12, 2, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    original_rates = gateway.copy_rates_from_pos

    def stale_rates(
        symbol: str, timeframe: str, start_pos: int, count: int
    ) -> tuple[dict[str, object], ...]:
        rows = original_rates(symbol, timeframe, start_pos, count)
        return tuple(
            row | {"time": int(row["time"]) - int(timedelta(days=2).total_seconds())}
            for row in rows
        )

    gateway.copy_rates_from_pos = stale_rates  # type: ignore[method-assign]
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now),
    )

    result = source.poll()

    assert result.status is LiveMarketStatus.WAITING_FOR_NEXT_M5
    assert result.bar is None
    assert result.availability.reason_code == "NO_FRESH_COMPLETED_M5"


def test_fresh_quote_recovers_without_restarting_source() -> None:
    now = datetime(2026, 9, 14, 12, 2, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    tick_at = [now - timedelta(days=2)]
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "bid": 4348.10,
        "ask": 4348.45,
        "last": 0.0,
        "time": int(tick_at[0].timestamp()),
    }
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now),
    )

    stale = source.poll()
    tick_at[0] = now
    recovered = source.poll()

    assert stale.status is LiveMarketStatus.STALE_QUOTE
    assert recovered.status is LiveMarketStatus.BAR_READY
    assert recovered.bar is not None
    assert recovered.bar.event.payload.freshness.observed_at == now


def test_plus_three_tick_and_rates_normalize_before_completed_bar_selection() -> None:
    now = datetime(2026, 9, 14, 7, 9, 28, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    original_rates = gateway.copy_rates_from_pos
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "bid": 4348.10,
        "ask": 4348.45,
        "last": 0.0,
        "time": int((now + timedelta(hours=3)).timestamp()),
        "time_msc": int((now + timedelta(hours=3)).timestamp() * 1_000),
    }

    def broker_time_rates(
        symbol: str, timeframe: str, start_pos: int, count: int
    ) -> tuple[dict[str, object], ...]:
        return tuple(
            row | {"time": int(row["time"]) + 10_800}
            for row in original_rates(symbol, timeframe, start_pos, count)
        )

    gateway.copy_rates_from_pos = broker_time_rates  # type: ignore[method-assign]
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now, hours=3),
    )

    result = source.poll()

    assert result.status is LiveMarketStatus.BAR_READY
    assert result.bar is not None
    assert result.bar.event.event_time == datetime(2026, 9, 14, 7, 5, tzinfo=UTC)
    assert result.bar.m15_trace.normalized_at <= result.bar.event.event_time
    assert result.bar.m5_trace.normalized_at + timedelta(minutes=5) == result.bar.event.event_time
    assert result.availability.broker_tick_at == now
    assert result.availability.raw_broker_tick_at == now + timedelta(hours=3)


def test_mid_session_offset_change_fails_closed_before_rate_or_decision_work() -> None:
    now = datetime(2026, 9, 14, 7, 9, 28, tzinfo=UTC)
    gateway = FakeRatesGateway(now)
    gateway.symbol_info_tick = lambda symbol: {  # type: ignore[method-assign]
        "symbol": symbol,
        "bid": 4348.10,
        "ask": 4348.45,
        "last": 0.0,
        "time": int((now + timedelta(hours=2)).timestamp()),
        "time_msc": int((now + timedelta(hours=2)).timestamp() * 1_000),
    }
    source = MT5CompletedM5Source(
        gateway=gateway,
        internal_symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        point_size=0.01,
        clock=lambda: now,
        broker_time_normalizer=_normalizer(now, hours=3),
    )

    result = source.poll()

    assert result.status is LiveMarketStatus.UNAVAILABLE
    assert result.bar is None
    assert result.availability.reason_code.startswith("BROKER_TIME_NORMALIZATION_FAILED")
    assert gateway.rate_calls == 0
