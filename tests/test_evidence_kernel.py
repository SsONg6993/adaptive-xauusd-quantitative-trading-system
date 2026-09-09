from __future__ import annotations

from datetime import UTC, datetime

import pytest

from axq.agents import (
    AgentInput,
    AgentStatus,
    ChartAgent,
    DirectionalBias,
    EntryEligibility,
    HistoricalSimilarityAgent,
    HypothesisRelationship,
    HypothesisStatus,
    MarketRegimeAgent,
    NewsMacroAgent,
    QuantitativeAgent,
    ScenarioDefinition,
    ScenarioPolicy,
    update_scenario,
)
from axq.runtime import (
    ComponentFreshness,
    FreshnessStatus,
    MarketState,
    RuntimeEvent,
    RuntimeEventType,
    initial_runtime_state,
)
from axq.runtime.kernel import EvidenceKernel
from axq.tools import (
    CausalFeatureSnapshot,
    FeatureFactTool,
    ToolCatalog,
    ToolCategory,
    ToolFact,
    ToolProvenance,
    ToolQuality,
    ToolResult,
    ToolStatus,
)

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)
STATE_ID = "state-specialist-test"
SNAPSHOT_ID = "fs-specialist-test"


def _result(
    category: ToolCategory,
    facts: dict[str, bool | int | float | str],
    *,
    name: str | None = None,
    status: ToolStatus = ToolStatus.AVAILABLE,
    freshness: FreshnessStatus = FreshnessStatus.AVAILABLE,
    sample_size: int | None = None,
) -> ToolResult:
    valid = status in {ToolStatus.AVAILABLE, ToolStatus.STALE}
    return ToolResult(
        tool_name=name or f"{category.value}.core",
        tool_version="1.0.0",
        category=category,
        as_of=T0,
        available_at=T0,
        runtime_state_id=STATE_ID,
        input_snapshot_id=SNAPSHOT_ID,
        freshness=freshness,
        status=status,
        facts=tuple(ToolFact(name=key, value=value) for key, value in facts.items()),
        quality=ToolQuality(valid=valid, sample_size=sample_size),
        warnings=() if valid else ("capability unavailable",),
        provenance=(
            ToolProvenance(
                source="deterministic-fixture",
                source_version="1.0.0",
                source_identity="fixture-v1",
            ),
        ),
    )


def _input(*results: ToolResult, previous_memory=None) -> AgentInput:
    return AgentInput(
        runtime_state_id=STATE_ID,
        feature_snapshot_id=SNAPSHOT_ID,
        as_of=T0,
        tool_results=results,
        previous_memory=previous_memory,
    )


@pytest.mark.parametrize(
    ("facts", "hypothesis", "direction"),
    [
        (
            {"h4_structure_bias": 1.0, "h1_structure_bias": 1.0, "structure_bos_up": True},
            "bullish_continuation",
            DirectionalBias.BULLISH,
        ),
        (
            {"h4_structure_bias": -1.0, "h1_structure_bias": -1.0, "structure_bos_down": True},
            "bearish_continuation",
            DirectionalBias.BEARISH,
        ),
    ],
)
def test_chart_agent_interprets_directional_structure(
    facts: dict[str, bool | int | float | str],
    hypothesis: str,
    direction: DirectionalBias,
) -> None:
    evidence, _ = ChartAgent().observe(_input(_result(ToolCategory.STRUCTURE, facts)))

    assert evidence.hypothesis == hypothesis
    assert evidence.direction is direction
    assert evidence.status is AgentStatus.READY
    assert evidence.evidence_for


def test_chart_agent_represents_hierarchical_mtf_conflict_as_uncertainty() -> None:
    facts = {
        "h4_structure_bias": -1.0,
        "h1_structure_bias": -1.0,
        "m15_structure_bias": 1.0,
        "m5_structure_bias": 1.0,
    }
    evidence, _ = ChartAgent().observe(_input(_result(ToolCategory.STRUCTURE, facts)))

    assert evidence.hypothesis == "structure_unclear"
    assert evidence.status is AgentStatus.DEGRADED
    assert evidence.confidence <= 0.5
    assert evidence.evidence_for and evidence.evidence_against


def test_chart_agent_abstains_when_structure_is_unavailable() -> None:
    unavailable = _result(
        ToolCategory.STRUCTURE,
        {},
        status=ToolStatus.UNAVAILABLE,
        freshness=FreshnessStatus.UNAVAILABLE,
    )
    evidence, _ = ChartAgent().observe(_input(unavailable))

    assert evidence.status is AgentStatus.ABSTAINED
    assert evidence.direction is None
    assert evidence.confidence == 0.0


@pytest.mark.parametrize(
    ("facts", "hypothesis", "direction"),
    [
        (
            {
                "trend_close_to_ema_20": 0.004,
                "trend_plus_di_14": 31.0,
                "trend_minus_di_14": 16.0,
                "momentum_macd_hist_12_26_9": 0.8,
                "momentum_rsi_14": 61.0,
            },
            "bullish_quantitative_tendency",
            DirectionalBias.BULLISH,
        ),
        (
            {
                "trend_close_to_ema_20": 0.012,
                "momentum_macd_hist_12_26_9": 0.7,
                "momentum_rsi_14": 76.0,
                "statistics_zscore_20": 2.8,
            },
            "bullish_but_overextended",
            DirectionalBias.BULLISH,
        ),
        (
            {
                "trend_close_to_ema_20": 0.0001,
                "momentum_macd_hist_12_26_9": -0.01,
                "momentum_rsi_14": 50.5,
            },
            "quantitatively_mixed",
            DirectionalBias.NEUTRAL,
        ),
    ],
)
def test_quant_agent_separates_tendency_extension_and_mixed_conditions(
    facts: dict[str, bool | int | float | str],
    hypothesis: str,
    direction: DirectionalBias,
) -> None:
    results = (
        _result(ToolCategory.TREND, facts, name="trend.core"),
        _result(ToolCategory.MOMENTUM, facts, name="momentum.core"),
        _result(ToolCategory.STATISTICS, facts, name="statistics.core"),
    )
    evidence, _ = QuantitativeAgent().observe(_input(*results))

    assert evidence.hypothesis == hypothesis
    assert evidence.direction is direction
    if "overextended" in hypothesis:
        assert evidence.evidence_against


def test_quant_agent_operates_when_optional_predictive_model_is_absent() -> None:
    trend = _result(
        ToolCategory.TREND,
        {"trend_close_to_ema_20": 0.004, "trend_plus_di_14": 30.0, "trend_minus_di_14": 15.0},
    )
    missing_ml = _result(
        ToolCategory.PREDICTIVE_MODEL,
        {},
        status=ToolStatus.UNAVAILABLE,
        freshness=FreshnessStatus.UNAVAILABLE,
    )
    evidence, _ = QuantitativeAgent().observe(_input(trend, missing_ml))

    assert evidence.hypothesis == "bullish_quantitative_tendency"
    assert evidence.status is AgentStatus.DEGRADED
    assert evidence.confidence > 0.0


def test_optional_predictive_evidence_cannot_override_stronger_quant_facts() -> None:
    trend = _result(
        ToolCategory.TREND,
        {
            "trend_close_to_ema_20": -0.006,
            "trend_plus_di_14": 14.0,
            "trend_minus_di_14": 32.0,
        },
    )
    predictive = _result(
        ToolCategory.PREDICTIVE_MODEL,
        {"class_probability_up": 0.9, "class_probability_down": 0.1},
    )

    evidence, _ = QuantitativeAgent().observe(_input(trend, predictive))

    assert evidence.hypothesis == "bearish_quantitative_tendency"
    assert any(
        item.fact_name == "class_probability_up"
        for item in evidence.evidence_against
    )


@pytest.mark.parametrize(
    ("facts", "sample_size", "hypothesis", "status"),
    [
        (
            {"similarity_score": 0.91, "regime_match": True, "forward_up_rate": 0.68},
            180,
            "historical_continuation_bias",
            AgentStatus.READY,
        ),
        (
            {"similarity_score": 0.51, "regime_match": True, "forward_up_rate": 0.62},
            180,
            "historically_mixed",
            AgentStatus.DEGRADED,
        ),
        (
            {"similarity_score": 0.9, "regime_match": True, "forward_up_rate": 0.68},
            12,
            "insufficient_comparable_cases",
            AgentStatus.ABSTAINED,
        ),
        (
            {
                "similarity_score": 0.88,
                "regime_match": True,
                "forward_up_rate": 0.64,
                "forward_return_mean": -0.001,
            },
            160,
            "historically_mixed",
            AgentStatus.DEGRADED,
        ),
    ],
)
def test_historical_agent_interprets_quality_sample_and_distribution_conflict(
    facts: dict[str, bool | int | float | str],
    sample_size: int,
    hypothesis: str,
    status: AgentStatus,
) -> None:
    result = _result(ToolCategory.SIMILARITY, facts, sample_size=sample_size)
    evidence, _ = HistoricalSimilarityAgent().observe(_input(result))

    assert evidence.hypothesis == hypothesis
    assert evidence.status is status


@pytest.mark.parametrize(
    ("facts", "hypothesis"),
    [
        ({"trend_adx_14": 31.0, "statistics_efficiency_ratio_20": 0.58}, "TRENDING"),
        ({"trend_adx_14": 15.0, "statistics_efficiency_ratio_20": 0.18}, "RANGING"),
        ({"volatility_expansion": 1.6, "trend_adx_14": 22.0}, "VOLATILITY_EXPANSION"),
        ({"trend_adx_14": 23.0, "statistics_efficiency_ratio_20": 0.31}, "TRANSITION"),
    ],
)
def test_regime_agent_emits_context_without_forced_direction(
    facts: dict[str, bool | int | float | str],
    hypothesis: str,
) -> None:
    evidence, _ = MarketRegimeAgent().observe(
        _input(_result(ToolCategory.VOLATILITY, facts))
    )

    assert evidence.hypothesis == hypothesis
    assert evidence.direction is None


@pytest.mark.parametrize(
    ("facts", "status", "freshness", "hypothesis", "agent_status"),
    [
        (
            {"event_risk_level": "normal"},
            ToolStatus.AVAILABLE,
            FreshnessStatus.AVAILABLE,
            "NORMAL_EVENT_RISK",
            AgentStatus.READY,
        ),
        (
            {"event_risk_level": "high", "minutes_to_event": 12},
            ToolStatus.AVAILABLE,
            FreshnessStatus.AVAILABLE,
            "HIGH_EVENT_RISK",
            AgentStatus.READY,
        ),
        (
            {"event_risk_level": "normal"},
            ToolStatus.STALE,
            FreshnessStatus.STALE,
            "CONTEXT_STALE",
            AgentStatus.DEGRADED,
        ),
        (
            {},
            ToolStatus.UNAVAILABLE,
            FreshnessStatus.UNAVAILABLE,
            "NO_VALID_CONTEXT",
            AgentStatus.ABSTAINED,
        ),
    ],
)
def test_news_agent_handles_available_risk_stale_and_unavailable_context(
    facts: dict[str, bool | int | float | str],
    status: ToolStatus,
    freshness: FreshnessStatus,
    hypothesis: str,
    agent_status: AgentStatus,
) -> None:
    evidence, _ = NewsMacroAgent().observe(
        _input(
            _result(
                ToolCategory.SLOW_CONTEXT,
                facts,
                status=status,
                freshness=freshness,
            )
        )
    )

    assert evidence.hypothesis == hypothesis
    assert evidence.status is agent_status
    assert evidence.direction is None


def test_specialist_preserves_provenance_and_is_deterministic() -> None:
    agent_input = _input(
        _result(ToolCategory.STRUCTURE, {"structure_bos_up": True})
    )
    first, _ = ChartAgent().observe(agent_input)
    second, _ = ChartAgent().observe(agent_input)

    assert first.evidence_id == second.evidence_id
    assert first.tool_inputs[0].provenance[0].source_identity == "fixture-v1"
    assert first.evidence_for[0].fact_value is True


def test_previous_memory_produces_an_explicit_continuation_relationship() -> None:
    agent = ChartAgent()
    structure = _result(
        ToolCategory.STRUCTURE,
        {
            "h4_structure_bias": 1.0,
            "h1_structure_bias": 1.0,
            "structure_bos_up": True,
        },
    )
    first, memory = agent.observe(
        _input(structure)
    )
    second, updated = agent.observe(
        _input(
            structure,
            previous_memory=memory,
        )
    )

    assert first.relationship is HypothesisRelationship.NEW
    assert second.relationship is HypothesisRelationship.UNCHANGED
    assert second.hypothesis_status is HypothesisStatus.CONFIRMED
    assert updated.previous_evidence_id == first.evidence_id


@pytest.mark.parametrize(
    ("fact_name", "relationship", "lifecycle"),
    [
        (
            "hypothesis_invalidated",
            HypothesisRelationship.INVALIDATED,
            HypothesisStatus.INVALIDATED,
        ),
        (
            "hypothesis_expired",
            HypothesisRelationship.EXPIRED,
            HypothesisStatus.EXPIRED,
        ),
    ],
)
def test_validated_terminal_facts_close_existing_specialist_memory(
    fact_name: str,
    relationship: HypothesisRelationship,
    lifecycle: HypothesisStatus,
) -> None:
    agent = ChartAgent()
    _, memory = agent.observe(
        _input(_result(ToolCategory.STRUCTURE, {"structure_bos_up": True}))
    )
    terminal, updated = agent.observe(
        _input(
            _result(ToolCategory.STRUCTURE, {fact_name: True}),
            previous_memory=memory,
        )
    )

    assert terminal.relationship is relationship
    assert terminal.hypothesis_status is lifecycle
    assert updated.hypothesis_status is lifecycle


def test_specialist_input_and_evidence_do_not_leak_account_or_execution_authority() -> None:
    agent_input = _input(_result(ToolCategory.STRUCTURE, {"structure_bos_up": True}))
    evidence, _ = ChartAgent().observe(agent_input)
    serialized = {
        "input": agent_input.model_dump(mode="json"),
        "evidence": evidence.model_dump(mode="json"),
    }

    text = str(serialized).lower()
    assert "balance" not in text
    assert "equity" not in text
    assert "risk_approved" not in text
    assert "order_authorized" not in text


def test_agent_rejects_a_tool_outside_its_access_boundary() -> None:
    with pytest.raises(ValueError, match="tool category"):
        ChartAgent().observe(
            _input(_result(ToolCategory.SLOW_CONTEXT, {"event_risk_level": "high"}))
        )


def _kernel_fixture() -> tuple[EvidenceKernel, RuntimeEvent, CausalFeatureSnapshot]:
    state = initial_runtime_state("XAUUSD", at=T0)
    freshness = ComponentFreshness(
        component="market",
        status=FreshnessStatus.AVAILABLE,
        observed_at=T0,
        available_at=T0,
        stale_after_ms=300_000,
    )
    market = MarketState(
        source="mt5",
        symbol="XAUUSD",
        as_of=T0,
        freshness=freshness,
        bid=2500.0,
        ask=2500.2,
        last=2500.1,
        spread_points=20.0,
        base_timeframe="M5",
        completed_timeframes=("M5",),
        feature_manifest_id="fm-test",
    )
    event = RuntimeEvent(
        event_type=RuntimeEventType.M5_CLOSED,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
        source="mt5",
        source_version="1.0.0",
        source_sequence=1,
        symbol="XAUUSD",
        payload=market,
    )
    values = {
        "h4_structure_bias": 1.0,
        "h1_structure_bias": 1.0,
        "structure_bos_up": True,
        "trend_close_to_ema_20": 0.004,
        "trend_adx_14": 31.0,
        "statistics_efficiency_ratio_20": 0.58,
    }
    snapshot = CausalFeatureSnapshot.from_mapping(
        symbol="XAUUSD",
        base_timeframe="M5",
        as_of=T0,
        available_at=T0,
        feature_manifest_id="fm-test",
        completed_timeframes=("M5",),
        values=values,
        source="phase2-feature-engine",
        source_version="2.0.0",
    )
    tools = (
        FeatureFactTool(
            name="structure.core",
            category=ToolCategory.STRUCTURE,
            feature_names=("h4_structure_bias", "h1_structure_bias", "structure_bos_up"),
        ),
        FeatureFactTool(
            name="trend.core",
            category=ToolCategory.TREND,
            feature_names=("trend_close_to_ema_20", "trend_adx_14"),
        ),
        FeatureFactTool(
            name="statistics.core",
            category=ToolCategory.STATISTICS,
            feature_names=("statistics_efficiency_ratio_20",),
        ),
    )
    kernel = EvidenceKernel(
        initial_state=state,
        catalog=ToolCatalog(tools),
        tool_access={
            "chart": ("structure.core",),
            "quant": ("trend.core",),
            "historical": (),
            "regime": ("trend.core", "statistics.core"),
            "news": (),
        },
    )
    return kernel, event, snapshot


def test_kernel_bundle_is_deterministic_and_optional_absence_does_not_block() -> None:
    first_kernel, event, snapshot = _kernel_fixture()
    second_kernel, _, _ = _kernel_fixture()

    first = first_kernel.process(event, feature_snapshot=snapshot)
    second = second_kernel.process(event, feature_snapshot=snapshot)

    assert first.bundle_id == second.bundle_id
    assert first.by_agent("quant").status is not AgentStatus.ERROR
    assert first.by_agent("historical").status is AgentStatus.ABSTAINED
    assert first.by_agent("news").status is AgentStatus.ABSTAINED
    assert tuple(item.agent_name for item in first.evidence) == (
        "chart",
        "quant",
        "historical",
        "regime",
        "news",
    )


def test_kernel_duplicate_event_is_idempotent_for_agent_memory() -> None:
    kernel, event, snapshot = _kernel_fixture()

    first = kernel.process(event, feature_snapshot=snapshot)
    duplicate = kernel.process(event, feature_snapshot=snapshot)

    assert duplicate == first


def test_kernel_chart_evidence_is_compatible_with_task5_thesis_creation() -> None:
    kernel, event, snapshot = _kernel_fixture()
    bundle = kernel.process(event, feature_snapshot=snapshot)

    thesis = update_scenario(
        event,
        bundle.input_for("chart"),
        bundle.by_agent("chart"),
        None,
        policy=ScenarioPolicy(ttl_seconds=900, max_m5_bars=3),
        scenario_definitions=(
            ScenarioDefinition(
                name="continuation",
                confirmation_facts=("structure_bos_up",),
            ),
        ),
    )

    assert thesis is not None
    assert thesis.entry_eligibility is EntryEligibility.WATCHING
