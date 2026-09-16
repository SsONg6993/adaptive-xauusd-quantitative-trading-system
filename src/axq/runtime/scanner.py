"""Pure causal M15-context/M5-candidate scanner."""

from __future__ import annotations

import math
from datetime import time
from zoneinfo import ZoneInfo

from axq.runtime.events import RuntimeEvent, RuntimeEventType
from axq.runtime.shadow import (
    CandidateDirection,
    CandidateResult,
    M5CandidateScan,
    M15ContextSnapshot,
    M15Regime,
    M15Structure,
    ScanFeatureReference,
    ScanReason,
)
from axq.tools import CausalFeatureSnapshot
from axq.tools.contracts import FactScalar

_MALAYSIA = ZoneInfo("Asia/Kuala_Lumpur")
_M15_NAMES = (
    "m15_breakout_above",
    "m15_breakout_below",
    "m15_statistics_efficiency_ratio_20",
    "m15_structure_bias",
    "m15_trend_adx_14",
    "m15_volatility_expansion",
)
_M5_NAMES = (
    "breakout_above_20",
    "breakout_below_20",
    "breakout_failed_down_20",
    "breakout_failed_up_20",
    "breakout_retest_down_20",
    "breakout_retest_up_20",
    "momentum_macd_hist_12_26_9",
    "momentum_rsi_14",
    "structure_bos_down",
    "structure_bos_up",
    "structure_choch_down",
    "structure_choch_up",
    "structure_hh",
    "structure_hl",
    "structure_lh",
    "structure_ll",
    "trend_close_to_ema_20",
    "trend_minus_di_14",
    "trend_plus_di_14",
)
SCANNER_REQUIRED_FEATURES = tuple(sorted((*_M15_NAMES, *_M5_NAMES)))


def _active_window(event: RuntimeEvent) -> bool:
    local = event.event_time.astimezone(_MALAYSIA).timetz().replace(tzinfo=None)
    return time(20, 0) <= local < time(23, 0)


def _is_true(value: FactScalar) -> bool:
    return value is True or value == 1.0


def _number(value: FactScalar) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("scanner numeric feature is invalid")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("scanner numeric feature is not finite")
    return result


def _reference(
    name: str,
    value: FactScalar,
    snapshot: CausalFeatureSnapshot,
) -> ScanFeatureReference:
    return ScanFeatureReference(
        feature_name=name,
        timeframe="M15" if name.startswith("m15_") else "M5",
        value=value,
        feature_snapshot_id=snapshot.snapshot_id,
        feature_manifest_id=snapshot.feature_manifest_id,
        source=snapshot.source,
        source_version=snapshot.source_version,
        available_at=snapshot.available_at,
    )


def _m15_context(
    event: RuntimeEvent,
    snapshot: CausalFeatureSnapshot,
    values: dict[str, FactScalar],
    resolved_broker_symbol: str,
    instrument_resolution_id: str,
) -> M15ContextSnapshot:
    bias = _number(values["m15_structure_bias"])
    structure = (
        M15Structure.BULLISH
        if bias > 0
        else M15Structure.BEARISH
        if bias < 0
        else M15Structure.NEUTRAL
    )
    adx = _number(values["m15_trend_adx_14"])
    efficiency = _number(values["m15_statistics_efficiency_ratio_20"])
    expansion = _number(values["m15_volatility_expansion"])
    if _is_true(values["m15_breakout_above"]) or _is_true(values["m15_breakout_below"]):
        regime = M15Regime.BREAKOUT
    elif expansion >= 1.25:
        regime = M15Regime.VOLATILITY_EXPANSION
    elif adx >= 25.0 and efficiency >= 0.35:
        regime = M15Regime.TRENDING
    elif adx < 20.0 and efficiency < 0.30:
        regime = M15Regime.RANGING
    else:
        regime = M15Regime.TRANSITION
    return M15ContextSnapshot(
        event_id=event.event_id,
        feature_snapshot_id=snapshot.snapshot_id,
        feature_manifest_id=snapshot.feature_manifest_id,
        symbol=event.symbol or snapshot.symbol,
        canonical_instrument="XAUUSD",
        resolved_broker_symbol=resolved_broker_symbol,
        instrument_resolution_id=instrument_resolution_id,
        as_of=event.event_time,
        available_at=snapshot.available_at,
        structure=structure,
        regime=regime,
        facts=tuple(_reference(name, values[name], snapshot) for name in _M15_NAMES),
    )


def scan_m5_candidate(
    event: RuntimeEvent,
    snapshot: CausalFeatureSnapshot,
    *,
    configured_symbol: str,
    resolved_broker_symbol: str,
    instrument_resolution_id: str,
    expected_manifest_id: str,
) -> tuple[M15ContextSnapshot | None, M5CandidateScan]:
    """Classify one completed M5 candle without invoking specialists."""

    if event.event_type is not RuntimeEventType.M5_CLOSED:
        raise ValueError("M5 candidate scanner accepts completed M5 events only")
    common = {
        "event_id": event.event_id,
        "symbol": configured_symbol,
        "canonical_instrument": "XAUUSD",
        "resolved_broker_symbol": resolved_broker_symbol,
        "instrument_resolution_id": instrument_resolution_id,
        "as_of": event.event_time,
        "available_at": event.available_at,
    }
    if not _active_window(event):
        return None, M5CandidateScan.model_validate(
            common
            | {
                "result": CandidateResult.OUTSIDE_WINDOW,
                "reason_codes": (ScanReason.OUTSIDE_ACTIVE_WINDOW,),
            }
        )
    validation_reason = None
    if event.symbol != configured_symbol or snapshot.symbol != configured_symbol:
        validation_reason = ScanReason.SYMBOL_MISMATCH
    elif snapshot.feature_manifest_id != expected_manifest_id:
        validation_reason = ScanReason.FEATURE_MANIFEST_MISMATCH
    elif "M5" not in snapshot.completed_timeframes:
        validation_reason = ScanReason.M5_NOT_COMPLETED
    elif "M15" not in snapshot.completed_timeframes:
        validation_reason = ScanReason.M15_CONTEXT_NOT_COMPLETED
    if validation_reason is not None:
        return None, M5CandidateScan.model_validate(
            common
            | {
                "feature_snapshot_id": snapshot.snapshot_id,
                "result": CandidateResult.UNAVAILABLE,
                "reason_codes": (validation_reason,),
            }
        )
    values = snapshot.as_mapping()
    missing = tuple(name for name in SCANNER_REQUIRED_FEATURES if name not in values)
    if missing:
        return None, M5CandidateScan.model_validate(
            common
            | {
                "feature_snapshot_id": snapshot.snapshot_id,
                "result": CandidateResult.UNAVAILABLE,
                "reason_codes": (ScanReason.REQUIRED_FEATURE_UNAVAILABLE,),
                "missing_features": missing,
            }
        )
    try:
        context = _m15_context(
            event,
            snapshot,
            values,
            resolved_broker_symbol,
            instrument_resolution_id,
        )
        bull_structure = tuple(
            name
            for name in ("structure_hh", "structure_hl", "structure_bos_up", "structure_choch_up")
            if _is_true(values[name])
        )
        bear_structure = tuple(
            name
            for name in (
                "structure_lh",
                "structure_ll",
                "structure_bos_down",
                "structure_choch_down",
            )
            if _is_true(values[name])
        )
        bull_breakout = tuple(
            name
            for name in ("breakout_above_20", "breakout_retest_up_20", "breakout_failed_down_20")
            if _is_true(values[name])
        )
        bear_breakout = tuple(
            name
            for name in ("breakout_below_20", "breakout_retest_down_20", "breakout_failed_up_20")
            if _is_true(values[name])
        )
        ema = _number(values["trend_close_to_ema_20"])
        plus = _number(values["trend_plus_di_14"])
        minus = _number(values["trend_minus_di_14"])
        macd = _number(values["momentum_macd_hist_12_26_9"])
        rsi = _number(values["momentum_rsi_14"])
    except ValueError:
        return None, M5CandidateScan.model_validate(
            common
            | {
                "feature_snapshot_id": snapshot.snapshot_id,
                "result": CandidateResult.UNAVAILABLE,
                "reason_codes": (ScanReason.REQUIRED_FEATURE_UNAVAILABLE,),
                "missing_features": (),
            }
        )
    bull_quant = tuple(
        name
        for name, active in (
            ("trend_close_to_ema_20", ema >= 0.001),
            ("trend_plus_di_14", plus - minus >= 2.0),
            ("momentum_macd_hist_12_26_9", macd >= 0.05),
            ("momentum_rsi_14", rsi >= 55.0),
        )
        if active
    )
    bear_quant = tuple(
        name
        for name, active in (
            ("trend_close_to_ema_20", ema <= -0.001),
            ("trend_minus_di_14", minus - plus >= 2.0),
            ("momentum_macd_hist_12_26_9", macd <= -0.05),
            ("momentum_rsi_14", rsi <= 45.0),
        )
        if active
    )
    bullish = bool(bull_structure or bull_breakout or bull_quant)
    bearish = bool(bear_structure or bear_breakout or bear_quant)
    reasons: list[ScanReason] = []
    for active, reason in (
        (bull_structure, ScanReason.M5_BULLISH_STRUCTURE_ACTIVATION),
        (bear_structure, ScanReason.M5_BEARISH_STRUCTURE_ACTIVATION),
        (bull_breakout, ScanReason.M5_BULLISH_BREAKOUT_ACTIVATION),
        (bear_breakout, ScanReason.M5_BEARISH_BREAKOUT_ACTIVATION),
        (bull_quant, ScanReason.M5_BULLISH_QUANT_ACTIVATION),
        (bear_quant, ScanReason.M5_BEARISH_QUANT_ACTIVATION),
    ):
        if active:
            reasons.append(reason)
    if not bullish and not bearish:
        result = CandidateResult.NO_SETUP
        direction = None
        reasons.append(ScanReason.NO_DIRECTIONAL_ACTIVATION)
    elif bullish and bearish:
        result = CandidateResult.CANDIDATE_CONFLICTED
        direction = CandidateDirection.CONFLICTED
    else:
        result = CandidateResult.CANDIDATE
        direction = CandidateDirection.BULLISH if bullish else CandidateDirection.BEARISH
    if (
        direction in {None, CandidateDirection.CONFLICTED}
        or context.structure is M15Structure.NEUTRAL
    ):
        reasons.append(ScanReason.M15_CONTEXT_NEUTRAL)
    else:
        supports = (direction is CandidateDirection.BULLISH) == (
            context.structure is M15Structure.BULLISH
        )
        reasons.append(
            ScanReason.M15_CONTEXT_SUPPORTS if supports else ScanReason.M15_CONTEXT_OPPOSES
        )
    if bullish and bearish:
        reasons.append(ScanReason.BIDIRECTIONAL_ACTIVATION)
    trigger_names = tuple(
        sorted(
            {
                *bull_structure,
                *bear_structure,
                *bull_breakout,
                *bear_breakout,
                *bull_quant,
                *bear_quant,
            }
        )
    )
    return context, M5CandidateScan.model_validate(
        common
        | {
            "feature_snapshot_id": snapshot.snapshot_id,
            "m15_context_id": context.context_id,
            "result": result,
            "direction": direction,
            "reason_codes": tuple(reasons),
            "triggers": tuple(_reference(name, values[name], snapshot) for name in trigger_names),
        }
    )


__all__ = ["SCANNER_REQUIRED_FEATURES", "scan_m5_candidate"]
