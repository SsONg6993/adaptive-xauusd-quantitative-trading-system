from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import pytest

from axq.features import default_registry
from axq.runtime import (
    ComponentFreshness,
    FreshnessStatus,
    MarketState,
    RuntimeEvent,
    RuntimeEventType,
    SharedRuntimeState,
    SlowContextState,
    initial_runtime_state,
    reduce_state,
)
from axq.tools import (
    CausalFeatureSnapshot,
    FeatureFactTool,
    HistoricalSimilarityTool,
    OptionalPredictiveModelTool,
    PredictiveModelEvidenceProvider,
    SimilarityEvidence,
    SimilarityEvidenceProvider,
    SlowContextFactTool,
    ToolCatalog,
    ToolCategory,
    ToolFact,
    ToolInput,
    ToolResult,
    ToolStatus,
)

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)
MANIFEST_ID = "fm-phase2-test"


def _freshness(status: FreshnessStatus, at: datetime) -> ComponentFreshness:
    return ComponentFreshness(
        component="market",
        status=status,
        observed_at=at,
        available_at=at,
        stale_after_ms=5_000,
        reason=None if status is FreshnessStatus.AVAILABLE else "source heartbeat unavailable",
    )


def _state(
    *,
    at: datetime = T0,
    completed: tuple[str, ...] = ("M5",),
    freshness: FreshnessStatus = FreshnessStatus.AVAILABLE,
) -> SharedRuntimeState:
    initial = initial_runtime_state("XAUUSD", at=at - timedelta(seconds=1))
    market = MarketState(
        source="mt5",
        symbol="XAUUSD",
        as_of=at,
        freshness=_freshness(freshness, at),
        bid=2500.0,
        ask=2500.2,
        last=2500.1,
        spread_points=20.0,
        base_timeframe="M5",
        completed_timeframes=completed,
        feature_manifest_id=MANIFEST_ID,
        market_data_version="broker-sample-v1",
    )
    event = RuntimeEvent(
        event_type=RuntimeEventType.M5_CLOSED,
        event_time=at,
        observed_at=at,
        available_at=at,
        source="mt5",
        source_version="1.0",
        source_sequence=1,
        symbol="XAUUSD",
        payload=market,
    )
    return reduce_state(initial, event, now=at)


def _snapshot(
    values: dict[str, bool | int | float | str | None],
    *,
    at: datetime = T0,
    completed: tuple[str, ...] = ("M5",),
) -> CausalFeatureSnapshot:
    return CausalFeatureSnapshot.from_mapping(
        symbol="XAUUSD",
        base_timeframe="M5",
        as_of=at,
        available_at=at,
        feature_manifest_id=MANIFEST_ID,
        completed_timeframes=completed,
        values=values,
        source="phase2-feature-engine",
        source_version="2.0.0",
    )


def _input(
    values: dict[str, bool | int | float | str | None] | None,
    *,
    state: SharedRuntimeState | None = None,
) -> ToolInput:
    return ToolInput(
        state=state or _state(),
        feature_snapshot=None if values is None else _snapshot(values),
    )


def test_tool_result_identity_binds_causal_inputs_and_round_trips() -> None:
    tool = FeatureFactTool(
        name="momentum.core",
        category=ToolCategory.MOMENTUM,
        feature_names=("momentum_rsi_14",),
    )
    tool_input = _input({"momentum_rsi_14": 57.25})

    first = tool.evaluate(tool_input)
    second = tool.evaluate(tool_input)

    assert first.result_id == second.result_id
    assert first.runtime_state_id == tool_input.state.state_id
    assert first.input_snapshot_id == tool_input.feature_snapshot.snapshot_id
    assert first.available_at == T0
    assert ToolResult.model_validate_json(first.model_dump_json()) == first


def test_feature_tool_reports_unavailable_insufficient_and_stale_separately() -> None:
    tool = FeatureFactTool(
        name="volatility.core",
        category=ToolCategory.VOLATILITY,
        feature_names=("vol_atr_14",),
    )

    assert tool.evaluate(_input(None)).status is ToolStatus.UNAVAILABLE
    assert tool.evaluate(_input({})).status is ToolStatus.INSUFFICIENT_DATA

    stale = tool.evaluate(
        _input({"vol_atr_14": 3.2}, state=_state(freshness=FreshnessStatus.STALE))
    )
    assert stale.status is ToolStatus.STALE
    assert stale.facts == (ToolFact(name="vol_atr_14", value=3.2),)


def test_feature_tool_reuses_phase2_causal_indicator_output_exactly() -> None:
    x = np.arange(60, dtype=float)
    close = 2500.0 + np.sin(x / 3.0) + x * 0.02
    candles = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-06", periods=60, freq="5min", tz="UTC"),
            "open": close - 0.1,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "tick_volume": 100 + x,
            "spread": 20.0,
        }
    )
    computed = default_registry().compute(candles, enabled_groups=["momentum"])
    phase2_value = float(computed.iloc[-1]["momentum_rsi_14"])
    tool = FeatureFactTool(
        name="momentum.core",
        category=ToolCategory.MOMENTUM,
        feature_names=("momentum_rsi_14",),
    )

    result = tool.evaluate(_input({"momentum_rsi_14": phase2_value}))

    assert result.status is ToolStatus.AVAILABLE
    assert result.facts[0].value == pytest.approx(phase2_value)
    assert result.provenance[0].source == "phase2-feature-engine"


def test_higher_timeframe_fact_requires_completed_and_available_snapshot() -> None:
    tool = FeatureFactTool(
        name="trend.h1",
        category=ToolCategory.TREND,
        feature_names=("trend_ema_20_h1",),
        required_timeframe="H1",
    )
    value = {"trend_ema_20_h1": 2501.0}

    incomplete = tool.evaluate(_input(value))
    assert incomplete.status is ToolStatus.UNAVAILABLE

    future_snapshot = _snapshot(value, at=T0 + timedelta(minutes=5), completed=("M5", "H1"))
    not_yet_available = tool.evaluate(
        ToolInput(state=_state(completed=("M5", "H1")), feature_snapshot=future_snapshot)
    )
    assert not_yet_available.status is ToolStatus.UNAVAILABLE

    available_state = _state(at=T0 + timedelta(minutes=5), completed=("M5", "H1"))
    available = tool.evaluate(
        ToolInput(state=available_state, feature_snapshot=future_snapshot)
    )
    assert available.status is ToolStatus.AVAILABLE


def test_live_replay_equivalent_input_produces_same_tool_identity() -> None:
    tool = FeatureFactTool(
        name="structure.core",
        category=ToolCategory.STRUCTURE,
        feature_names=("structure_bos_up", "structure_distance_resistance_atr"),
    )
    live = _input({"structure_bos_up": True, "structure_distance_resistance_atr": 0.62})
    replay = ToolInput.model_validate_json(live.model_dump_json())

    assert tool.evaluate(live).result_id == tool.evaluate(replay).result_id


class _FailingProvider(PredictiveModelEvidenceProvider):
    model_id = "qm-failing"
    feature_manifest_id = MANIFEST_ID
    maximum_data_age_ms = 60_000

    def probabilities(self, feature_values: dict[str, Any]) -> dict[str, float]:
        del feature_values
        raise RuntimeError("inference failed")


class _WorkingProvider(PredictiveModelEvidenceProvider):
    model_id = "qm-test"
    feature_manifest_id = MANIFEST_ID
    maximum_data_age_ms = 60_000

    def probabilities(self, feature_values: dict[str, Any]) -> dict[str, float]:
        del feature_values
        return {"DOWN": 0.2, "NEUTRAL": 0.3, "UP": 0.5}


class _ExplodingTool:
    name = "statistics.exploding"
    version = "1.0.0"
    category = ToolCategory.STATISTICS

    def evaluate(self, tool_input: ToolInput) -> ToolResult:
        del tool_input
        raise RuntimeError("calculation failed")


class _SimilarityProvider(SimilarityEvidenceProvider):
    provider_name = "local-neighbor-index"
    provider_version = "1.0.0"

    def __init__(self) -> None:
        self.calls = 0

    def find_similar(self, snapshot: CausalFeatureSnapshot) -> SimilarityEvidence:
        self.calls += 1
        assert snapshot.feature_manifest_id == MANIFEST_ID
        return SimilarityEvidence(
            similarity_score=0.91,
            sample_size=184,
            regime_match=True,
            session_match=False,
            forward_up_rate=0.57,
            forward_return_mean=0.0012,
            mfe_mean_atr=0.83,
            mae_mean_atr=0.41,
            source_identity="neighbors-fixture-v1",
        )


def test_optional_predictive_model_absence_and_failure_are_explicit() -> None:
    tool_input = _input({"pa_body": 0.2})

    assert OptionalPredictiveModelTool(None).evaluate(tool_input).status is ToolStatus.UNAVAILABLE
    failed = OptionalPredictiveModelTool(_FailingProvider()).evaluate(tool_input)
    assert failed.status is ToolStatus.ERROR
    assert failed.facts == ()

    stale = OptionalPredictiveModelTool(_WorkingProvider()).evaluate(
        _input({"pa_body": 0.2}, state=_state(freshness=FreshnessStatus.STALE))
    )
    assert stale.status is ToolStatus.STALE


def test_catalog_isolates_tool_error_from_other_factual_results() -> None:
    working = FeatureFactTool(
        name="momentum.core",
        category=ToolCategory.MOMENTUM,
        feature_names=("momentum_rsi_14",),
    )
    catalog = ToolCatalog((working, _ExplodingTool()))

    results = catalog.evaluate(
        ("momentum.core", "statistics.exploding"),
        _input({"momentum_rsi_14": 55.0}),
    )

    assert tuple(result.status for result in results) == (
        ToolStatus.AVAILABLE,
        ToolStatus.ERROR,
    )
    assert results[1].facts == ()


def test_predictive_tool_emits_probabilities_not_trade_decisions() -> None:
    result = OptionalPredictiveModelTool(_WorkingProvider()).evaluate(
        _input({"pa_body": 0.2})
    )

    assert result.status is ToolStatus.AVAILABLE
    assert {fact.name for fact in result.facts} == {
        "class_probability_down",
        "class_probability_neutral",
        "class_probability_up",
    }
    assert not any(fact.value in {"BUY", "SELL", "ENTER"} for fact in result.facts)
    with pytest.raises(ValueError, match="trading decision"):
        ToolFact(name="signal", value="BUY")
    with pytest.raises(ValueError, match="trading decision"):
        ToolFact(name="trade_signal", value=0.8)


def test_slow_context_tool_uses_reducer_availability_cursor() -> None:
    state = _state()
    available_at = T0 + timedelta(minutes=2)
    context = SlowContextState(
        provider="calendar",
        context_version="calendar-v1",
        effective_at=T0 - timedelta(hours=1),
        expires_at=T0 + timedelta(hours=1),
        content_hash="calendar-sha256",
    )
    event = RuntimeEvent(
        event_type=RuntimeEventType.SLOW_CONTEXT_UPDATED,
        event_time=context.effective_at,
        observed_at=T0 + timedelta(minutes=1),
        available_at=available_at,
        source="calendar",
        source_version="local-v1",
        source_sequence=1,
        symbol="XAUUSD",
        payload=context,
    )
    updated = reduce_state(state, event, now=available_at)

    result = SlowContextFactTool("calendar").evaluate(ToolInput(state=updated))

    assert result.status is ToolStatus.AVAILABLE
    assert result.available_at == available_at
    assert {fact.name: fact.value for fact in result.facts} == {
        "context_version": "calendar-v1",
        "content_hash": "calendar-sha256",
    }


def test_historical_similarity_is_optional_factual_evidence() -> None:
    tool_input = _input({"trend_adx_14": 27.4})
    assert HistoricalSimilarityTool(None).evaluate(tool_input).status is ToolStatus.UNAVAILABLE

    result = HistoricalSimilarityTool(_SimilarityProvider()).evaluate(tool_input)

    assert result.status is ToolStatus.AVAILABLE
    assert {fact.name: fact.value for fact in result.facts} == {
        "similarity_score": 0.91,
        "regime_match": True,
        "session_match": False,
        "forward_up_rate": 0.57,
        "forward_return_mean": 0.0012,
        "mfe_mean_atr": 0.83,
        "mae_mean_atr": 0.41,
    }
    assert result.quality.sample_size == 184


def test_historical_similarity_rejects_snapshot_state_incompatibility() -> None:
    provider = _SimilarityProvider()
    state = _state()
    mismatched_snapshot = CausalFeatureSnapshot.from_mapping(
        symbol="XAUUSD",
        base_timeframe="M5",
        as_of=T0,
        available_at=T0,
        feature_manifest_id="different-manifest",
        completed_timeframes=("M5",),
        values={"trend_adx_14": 27.4},
        source="phase2-feature-engine",
        source_version="2.0.0",
    )

    manifest_result = HistoricalSimilarityTool(provider).evaluate(
        ToolInput(state=state, feature_snapshot=mismatched_snapshot)
    )
    timeframe_result = HistoricalSimilarityTool(provider).evaluate(
        ToolInput(
            state=state,
            feature_snapshot=_snapshot(
                {"trend_adx_14": 27.4}, completed=("M5", "H1")
            ),
        )
    )
    assert manifest_result.status is ToolStatus.ERROR
    assert timeframe_result.status is ToolStatus.UNAVAILABLE
    assert provider.calls == 0
