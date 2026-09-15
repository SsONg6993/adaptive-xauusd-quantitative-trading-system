from __future__ import annotations

from datetime import UTC, datetime

from axq.runtime import (
    ComponentFreshness,
    FreshnessStatus,
    MarketState,
    RuntimeEvent,
    RuntimeEventType,
)
from axq.runtime.scanner import scan_m5_candidate
from axq.runtime.shadow import CandidateDirection, CandidateResult, ScanReason
from axq.tools import CausalFeatureSnapshot


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 14, hour, minute, tzinfo=UTC)


def _event(at: datetime) -> RuntimeEvent:
    return RuntimeEvent(
        event_type=RuntimeEventType.M5_CLOSED,
        event_time=at,
        observed_at=at,
        available_at=at,
        source="mt5-shadow",
        source_version="1.0.0",
        source_sequence=int(at.timestamp()),
        symbol="XAUUSD",
        payload=MarketState(
            source="mt5-shadow",
            symbol="XAUUSD",
            as_of=at,
            freshness=ComponentFreshness(
                component="market",
                status=FreshnessStatus.AVAILABLE,
                observed_at=at,
                available_at=at,
                stale_after_ms=300_000,
            ),
            bid=2500.0,
            ask=2500.2,
            last=2500.1,
            spread_points=20.0,
            base_timeframe="M5",
            completed_timeframes=("M5", "M15"),
            feature_manifest_id="fm-shadow-v1",
        ),
    )


def _values() -> dict[str, float | bool]:
    return {
        "m15_structure_bias": 1.0,
        "m15_trend_adx_14": 24.0,
        "m15_statistics_efficiency_ratio_20": 0.32,
        "m15_volatility_expansion": 1.0,
        "m15_breakout_above": False,
        "m15_breakout_below": False,
        "structure_hh": 0.0,
        "structure_hl": 0.0,
        "structure_lh": 0.0,
        "structure_ll": 0.0,
        "structure_bos_up": False,
        "structure_bos_down": False,
        "structure_choch_up": False,
        "structure_choch_down": False,
        "breakout_above_20": False,
        "breakout_below_20": False,
        "breakout_failed_up_20": False,
        "breakout_failed_down_20": False,
        "breakout_retest_up_20": False,
        "breakout_retest_down_20": False,
        "trend_close_to_ema_20": 0.0,
        "trend_plus_di_14": 20.0,
        "trend_minus_di_14": 20.0,
        "momentum_macd_hist_12_26_9": 0.0,
        "momentum_rsi_14": 50.0,
    }


def _snapshot(at: datetime, values: dict[str, float | bool]) -> CausalFeatureSnapshot:
    return CausalFeatureSnapshot.from_mapping(
        symbol="XAUUSD",
        base_timeframe="M5",
        as_of=at,
        available_at=at,
        feature_manifest_id="fm-shadow-v1",
        completed_timeframes=("M5", "M15"),
        values=values,
        source="phase2-feature-engine",
        source_version="2.0.0",
    )


def test_window_is_half_open_in_malaysia_time() -> None:
    for at, expected in (
        (_at(11, 55), CandidateResult.OUTSIDE_WINDOW),
        (_at(12, 0), CandidateResult.NO_SETUP),
        (_at(14, 55), CandidateResult.NO_SETUP),
        (_at(15, 0), CandidateResult.OUTSIDE_WINDOW),
    ):
        context, scan = scan_m5_candidate(
            _event(at),
            _snapshot(at, _values()),
            configured_symbol="XAUUSD",
            resolved_broker_symbol="XAUUSD.sc",
            instrument_resolution_id="rbi-shadow",
            expected_manifest_id="fm-shadow-v1",
        )
        assert scan.result is expected
        assert (context is None) is (expected is CandidateResult.OUTSIDE_WINDOW)


def test_all_applicable_trigger_groups_are_preserved_in_canonical_order() -> None:
    at = _at(12)
    values = _values() | {
        "structure_hh": 1.0,
        "structure_bos_up": True,
        "breakout_above_20": True,
        "breakout_failed_down_20": True,
        "trend_close_to_ema_20": 0.002,
        "momentum_macd_hist_12_26_9": 0.06,
    }
    context, scan = scan_m5_candidate(
        _event(at),
        _snapshot(at, values),
        configured_symbol="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        expected_manifest_id="fm-shadow-v1",
    )

    assert context is not None
    assert context.canonical_instrument == "XAUUSD"
    assert context.resolved_broker_symbol == "XAUUSD.sc"
    assert context.instrument_resolution_id == "rbi-shadow"
    assert scan.result is CandidateResult.CANDIDATE
    assert scan.direction is CandidateDirection.BULLISH
    assert scan.reason_codes == (
        ScanReason.M5_BULLISH_STRUCTURE_ACTIVATION,
        ScanReason.M5_BULLISH_BREAKOUT_ACTIVATION,
        ScanReason.M5_BULLISH_QUANT_ACTIVATION,
        ScanReason.M15_CONTEXT_SUPPORTS,
    )
    assert {item.feature_name for item in scan.triggers} >= {
        "structure_hh",
        "structure_bos_up",
        "breakout_above_20",
        "breakout_failed_down_20",
        "trend_close_to_ema_20",
        "momentum_macd_hist_12_26_9",
    }


def test_mixed_activation_is_conflicted_and_m15_never_vetoes() -> None:
    at = _at(12)
    values = _values() | {
        "structure_bos_up": True,
        "breakout_below_20": True,
        "trend_close_to_ema_20": 0.002,
        "momentum_macd_hist_12_26_9": -0.06,
    }
    _context, scan = scan_m5_candidate(
        _event(at),
        _snapshot(at, values),
        configured_symbol="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        expected_manifest_id="fm-shadow-v1",
    )

    assert scan.result is CandidateResult.CANDIDATE_CONFLICTED
    assert scan.direction is CandidateDirection.CONFLICTED
    assert scan.reason_codes == (
        ScanReason.M5_BULLISH_STRUCTURE_ACTIVATION,
        ScanReason.M5_BEARISH_BREAKOUT_ACTIVATION,
        ScanReason.M5_BULLISH_QUANT_ACTIVATION,
        ScanReason.M5_BEARISH_QUANT_ACTIVATION,
        ScanReason.M15_CONTEXT_NEUTRAL,
        ScanReason.BIDIRECTIONAL_ACTIVATION,
    )


def test_only_scanner_required_fields_fail_closed() -> None:
    at = _at(12)
    values = _values()
    values.pop("momentum_rsi_14")
    values["unrelated_feature"] = 123.0

    context, scan = scan_m5_candidate(
        _event(at),
        _snapshot(at, values),
        configured_symbol="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        expected_manifest_id="fm-shadow-v1",
    )

    assert context is None
    assert scan.result is CandidateResult.UNAVAILABLE
    assert scan.reason_codes == (ScanReason.REQUIRED_FEATURE_UNAVAILABLE,)
    assert scan.missing_features == ("momentum_rsi_14",)


def test_bearish_predicate_is_symmetric() -> None:
    at = _at(12)
    values = _values() | {
        "structure_lh": 1.0,
        "structure_ll": 1.0,
        "structure_bos_down": True,
        "structure_choch_down": True,
        "breakout_below_20": True,
        "breakout_retest_down_20": True,
        "breakout_failed_up_20": True,
        "trend_close_to_ema_20": -0.001,
        "trend_minus_di_14": 23.0,
        "trend_plus_di_14": 20.0,
        "momentum_macd_hist_12_26_9": -0.05,
        "momentum_rsi_14": 45.0,
    }
    _context, scan = scan_m5_candidate(
        _event(at),
        _snapshot(at, values),
        configured_symbol="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        expected_manifest_id="fm-shadow-v1",
    )

    assert scan.result is CandidateResult.CANDIDATE
    assert scan.direction is CandidateDirection.BEARISH
    assert tuple(item.feature_name for item in scan.triggers) == tuple(
        sorted(item.feature_name for item in scan.triggers)
    )
    assert ScanReason.M15_CONTEXT_OPPOSES in scan.reason_codes
