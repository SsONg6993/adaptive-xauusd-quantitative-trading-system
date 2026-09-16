from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.mt5.symbols import GoldSymbolConfiguration, resolve_gold_instrument
from axq.mt5.time_normalization import (
    MT5BrokerEnvironmentIdentity,
    MT5BrokerTimeNormalizer,
    MT5BrokerTimePolicy,
    MT5TimeNormalizationError,
    infer_broker_time_offset,
)
from axq.orchestration.shadow_runtime import resolve_session_broker_time
from axq.runtime.journal import SQLiteRuntimeJournal

OBSERVED = datetime(2026, 9, 14, 7, 9, 28, tzinfo=UTC)


def _environment(*, server: str = "VantageInternational-Demo") -> MT5BrokerEnvironmentIdentity:
    return MT5BrokerEnvironmentIdentity(
        broker_server=server,
        account_login_digest="login-digest",
        account_trade_mode=0,
        terminal_company="MetaQuotes Ltd.",
        terminal_build=5327,
    )


def _resolution(*, raw_offset: timedelta = timedelta(hours=3)):
    raw = OBSERVED + raw_offset
    return infer_broker_time_offset(
        raw_tick_time=int(raw.timestamp()),
        raw_tick_time_msc=int(raw.timestamp() * 1_000),
        observed_at=OBSERVED,
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-test",
        environment=_environment(),
    )


def test_infers_explicit_whole_hour_offset_and_normalizes_vantage_plus_three() -> None:
    resolution = _resolution()
    normalizer = MT5BrokerTimeNormalizer(resolution)

    assert resolution.offset_seconds == 10_800
    assert resolution.raw_tick_at == datetime(2026, 9, 14, 10, 9, 28, tzinfo=UTC)
    assert resolution.normalized_tick_at == OBSERVED
    assert normalizer.normalize_epoch_seconds(
        int(datetime(2026, 9, 14, 10, 5, tzinfo=UTC).timestamp())
    ) == datetime(2026, 9, 14, 7, 5, tzinfo=UTC)


def test_fractional_half_hour_offset_fails_closed_without_rounding() -> None:
    with pytest.raises(MT5TimeNormalizationError, match="whole-hour"):
        _resolution(raw_offset=timedelta(hours=3, minutes=30))


def test_offset_residual_beyond_tolerance_fails_closed() -> None:
    policy = MT5BrokerTimePolicy(inference_residual_tolerance_seconds=5)
    raw = OBSERVED + timedelta(hours=3, seconds=6)

    with pytest.raises(MT5TimeNormalizationError, match="residual"):
        infer_broker_time_offset(
            raw_tick_time=int(raw.timestamp()),
            raw_tick_time_msc=int(raw.timestamp() * 1_000),
            observed_at=OBSERVED,
            canonical_instrument="XAUUSD",
            resolved_broker_symbol="XAUUSD.sc",
            instrument_resolution_id="rbi-test",
            environment=_environment(),
            policy=policy,
        )


def test_persisted_resolution_reuse_requires_exact_environment_compatibility() -> None:
    resolution = _resolution()
    normalizer = MT5BrokerTimeNormalizer.from_persisted(
        resolution,
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-test",
        environment=_environment(),
    )
    assert normalizer.resolution.resolution_id == resolution.resolution_id

    with pytest.raises(MT5TimeNormalizationError, match="environment"):
        MT5BrokerTimeNormalizer.from_persisted(
            resolution,
            canonical_instrument="XAUUSD",
            resolved_broker_symbol="XAUUSD.sc",
            instrument_resolution_id="rbi-test",
            environment=_environment(server="AnotherBroker-Demo"),
        )


def test_fresh_tick_offset_change_is_rejected_mid_session() -> None:
    normalizer = MT5BrokerTimeNormalizer(_resolution())
    changed_raw = OBSERVED + timedelta(hours=2)

    with pytest.raises(MT5TimeNormalizationError, match="changed"):
        normalizer.normalize_tick(
            raw_tick_time=int(changed_raw.timestamp()),
            raw_tick_time_msc=int(changed_raw.timestamp() * 1_000),
            observed_at=OBSERVED,
        )


def test_stale_tick_uses_frozen_offset_without_reinferring() -> None:
    normalizer = MT5BrokerTimeNormalizer(_resolution())
    stale_canonical = OBSERVED - timedelta(days=2)
    stale_raw = stale_canonical + timedelta(hours=3)

    normalized = normalizer.normalize_tick(
        raw_tick_time=int(stale_raw.timestamp()),
        raw_tick_time_msc=int(stale_raw.timestamp() * 1_000),
        observed_at=OBSERVED,
    )

    assert normalized.normalized_at == stale_canonical
    assert normalized.offset_seconds == 10_800


def test_future_normalized_timestamp_fails_closed() -> None:
    normalizer = MT5BrokerTimeNormalizer(_resolution())
    future_raw = OBSERVED + timedelta(hours=3, seconds=2)

    with pytest.raises(MT5TimeNormalizationError, match="future"):
        normalizer.normalize_tick(
            raw_tick_time=int(future_raw.timestamp()),
            raw_tick_time_msc=int(future_raw.timestamp() * 1_000),
            observed_at=OBSERVED,
        )


class _SessionGateway:
    def __init__(self, tick_at: datetime, *, server: str = "VantageInternational-Demo") -> None:
        self.tick_at = tick_at
        self.server = server

    def symbol_info(self, symbol: str):
        return {"name": symbol, "point": 0.01}

    def symbol_info_tick(self, symbol: str):
        return {
            "symbol": symbol,
            "time": int(self.tick_at.timestamp()),
            "time_msc": int(self.tick_at.timestamp() * 1_000),
            "bid": 4300.0,
            "ask": 4300.2,
        }

    def terminal_info(self):
        return {"company": "MetaQuotes Ltd.", "build": 5327}

    def account_info(self):
        return {"server": self.server, "login": 123456, "trade_mode": 0}


def test_stale_startup_reuses_only_compatible_persisted_resolution(tmp_path) -> None:
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    gateway = _SessionGateway(OBSERVED + timedelta(hours=3))
    instrument = resolve_gold_instrument(
        gateway,
        GoldSymbolConfiguration.single("XAUUSD.sc"),
        resolved_at=OBSERVED,
    )
    first = resolve_session_broker_time(
        gateway=gateway,
        journal=journal,
        instrument_resolution=instrument,
        clock=lambda: OBSERVED,
    )
    journal.append_semantic(
        first.resolution,
        event_id=None,
        available_at=first.resolution.resolved_at,
    )
    gateway.tick_at = OBSERVED - timedelta(days=2) + timedelta(hours=3)

    reused = resolve_session_broker_time(
        gateway=gateway,
        journal=journal,
        instrument_resolution=instrument,
        clock=lambda: OBSERVED,
    )

    assert reused.resolution.resolution_id == first.resolution.resolution_id
    assert reused.normalize_tick(
        raw_tick_time=int(gateway.tick_at.timestamp()),
        raw_tick_time_msc=int(gateway.tick_at.timestamp() * 1_000),
        observed_at=OBSERVED,
    ).normalized_at == OBSERVED - timedelta(days=2)


def test_stale_startup_rejects_persisted_resolution_from_other_server(tmp_path) -> None:
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    gateway = _SessionGateway(OBSERVED + timedelta(hours=3))
    instrument = resolve_gold_instrument(
        gateway,
        GoldSymbolConfiguration.single("XAUUSD.sc"),
        resolved_at=OBSERVED,
    )
    first = resolve_session_broker_time(
        gateway=gateway,
        journal=journal,
        instrument_resolution=instrument,
        clock=lambda: OBSERVED,
    )
    journal.append_semantic(
        first.resolution,
        event_id=None,
        available_at=first.resolution.resolved_at,
    )
    gateway.server = "OtherBroker-Demo"
    gateway.tick_at = OBSERVED - timedelta(days=2) + timedelta(hours=3)

    with pytest.raises(MT5TimeNormalizationError, match="no compatible persisted"):
        resolve_session_broker_time(
            gateway=gateway,
            journal=journal,
            instrument_resolution=instrument,
            clock=lambda: OBSERVED,
        )
