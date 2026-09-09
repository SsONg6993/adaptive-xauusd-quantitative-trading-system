from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.agents import (
    AgentEvidence,
    AgentInput,
    AgentStatus,
    DirectionalBias,
    EntryEligibility,
    EvidencePolarity,
    EvidenceReference,
    HypothesisInvalidation,
    HypothesisRelationship,
    HypothesisStatus,
    ScenarioDefinition,
    ScenarioPolicy,
    ScenarioStatus,
    ThesisState,
    ToolResultReference,
    update_scenario,
)
from axq.runtime import (
    ComponentFreshness,
    FreshnessStatus,
    MarketState,
    RuntimeEvent,
    RuntimeEventType,
)
from axq.tools import ToolCategory, ToolFact, ToolQuality, ToolResult, ToolStatus

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)
POLICY = ScenarioPolicy(ttl_seconds=900, max_m5_bars=3, max_scenarios=3)
SCENARIOS = (
    ScenarioDefinition(
        name="immediate_continuation",
        confirmation_facts=("micro_break",),
        invalidation_facts=("invalidation_break",),
    ),
    ScenarioDefinition(
        name="retest_then_continue",
        confirmation_facts=("retest_held", "micro_break"),
        invalidation_facts=("invalidation_break",),
    ),
)


def _market(at: datetime) -> MarketState:
    freshness = ComponentFreshness(
        component="market",
        status=FreshnessStatus.AVAILABLE,
        observed_at=at,
        available_at=at,
        stale_after_ms=5_000,
    )
    return MarketState(
        source="mt5",
        symbol="XAUUSD",
        as_of=at,
        freshness=freshness,
        bid=2500.0,
        ask=2500.2,
        last=2500.1,
        spread_points=20.0,
        base_timeframe="M5",
        completed_timeframes=("M5",),
        feature_manifest_id="fm-test",
    )


def _event(
    event_type: RuntimeEventType,
    *,
    at: datetime,
    sequence: int,
    event_time: datetime | None = None,
) -> RuntimeEvent:
    market_time = event_time or at
    return RuntimeEvent(
        event_type=event_type,
        event_time=market_time,
        observed_at=at,
        available_at=at,
        source="mt5",
        source_version="1.0",
        source_sequence=sequence,
        symbol="XAUUSD",
        payload=_market(market_time),
    )


def _agent_pair(
    event: RuntimeEvent,
    *,
    fact_name: str = "m5_structure",
    fact_value: bool | float | str = True,
    hypothesis_id: str = "hyp-a",
    hypothesis: str = "bullish_continuation",
    relationship: HypothesisRelationship = HypothesisRelationship.NEW,
    lifecycle: HypothesisStatus = HypothesisStatus.DEVELOPING,
    previous_hypothesis_id: str | None = None,
    invalidated: bool = False,
    thesis_id: str | None = None,
) -> tuple[AgentInput, AgentEvidence]:
    runtime_state_id = f"state-{event.source_sequence}"
    result = ToolResult(
        tool_name="structure.core",
        tool_version="1.0.0",
        category=ToolCategory.STRUCTURE,
        as_of=event.available_at,
        available_at=event.available_at,
        runtime_state_id=runtime_state_id,
        input_snapshot_id="fs-test",
        freshness=FreshnessStatus.AVAILABLE,
        status=ToolStatus.AVAILABLE,
        facts=(ToolFact(name=fact_name, value=fact_value),),
        quality=ToolQuality(valid=True),
    )
    agent_input = AgentInput(
        runtime_state_id=runtime_state_id,
        feature_snapshot_id="fs-test",
        as_of=event.available_at,
        tool_results=(result,),
    )
    reference = EvidenceReference(
        tool_name=result.tool_name,
        tool_result_id=result.result_id,
        fact_name=fact_name,
        fact_value=fact_value,
        polarity=EvidencePolarity.SUPPORTS,
        strength=0.8,
        freshness=result.freshness,
        quality_valid=True,
    )
    evidence = AgentEvidence(
        agent_name="chart",
        agent_version="1.0.0",
        runtime_state_id=runtime_state_id,
        feature_snapshot_id="fs-test",
        as_of=event.available_at,
        available_at=event.available_at,
        hypothesis_id=hypothesis_id,
        hypothesis=hypothesis,
        hypothesis_status=lifecycle,
        relationship=relationship,
        previous_hypothesis_id=previous_hypothesis_id,
        direction=DirectionalBias.BULLISH,
        confidence=0.7,
        uncertainty=0.3,
        evidence_quality=0.8,
        evidence_for=(reference,),
        invalidation=HypothesisInvalidation(
            invalidated=invalidated,
            reason="invalidation level broke" if invalidated else None,
            tool_result_id=result.result_id if invalidated else None,
            fact_name=fact_name if invalidated else None,
        ),
        freshness=FreshnessStatus.AVAILABLE,
        status=AgentStatus.READY,
        tool_inputs=(ToolResultReference.from_result(result),),
        thesis_id=thesis_id,
    )
    return agent_input, evidence


def _create() -> ThesisState:
    event = _event(RuntimeEventType.M5_CLOSED, at=T0, sequence=1)
    agent_input, evidence = _agent_pair(event)
    result = update_scenario(
        event,
        agent_input,
        evidence,
        None,
        policy=POLICY,
        scenario_definitions=SCENARIOS,
    )
    assert result is not None
    return result


def _update(
    previous: ThesisState,
    *,
    event_type: RuntimeEventType,
    relationship: HypothesisRelationship,
    lifecycle: HypothesisStatus,
    fact_name: str,
    minutes: int,
    sequence: int,
    invalidated: bool = False,
    hypothesis_id: str = "hyp-a",
    hypothesis: str = "bullish_continuation",
    event_time: datetime | None = None,
) -> ThesisState:
    event = _event(
        event_type,
        at=T0 + timedelta(minutes=minutes),
        sequence=sequence,
        event_time=event_time,
    )
    agent_input, evidence = _agent_pair(
        event,
        fact_name=fact_name,
        hypothesis_id=hypothesis_id,
        hypothesis=hypothesis,
        relationship=relationship,
        lifecycle=lifecycle,
        previous_hypothesis_id=previous.hypothesis_id,
        invalidated=invalidated,
        thesis_id=previous.thesis_id,
    )
    result = update_scenario(event, agent_input, evidence, previous, policy=POLICY)
    assert result is not None
    return result


def test_m5_can_create_deterministic_serializable_thesis_and_scenarios() -> None:
    first = _create()
    second = _create()

    assert first.thesis_id == second.thesis_id
    assert first.state_id == second.state_id
    assert first.hypothesis_status is HypothesisStatus.DEVELOPING
    assert first.entry_eligibility is EntryEligibility.WATCHING
    assert first.latest_evidence_as_of == T0
    assert first.latest_evidence_available_at == T0
    assert len(first.scenarios) == 2
    assert first.scenarios[0].scenario_id == second.scenarios[0].scenario_id
    assert ThesisState.model_validate_json(first.model_dump_json()) == first


@pytest.mark.parametrize("event_type", [RuntimeEventType.TICK, RuntimeEventType.M1_CLOSED])
def test_intrabar_event_without_active_m5_thesis_is_noop(
    event_type: RuntimeEventType,
) -> None:
    event = _event(event_type, at=T0, sequence=1)
    agent_input, evidence = _agent_pair(event)

    assert update_scenario(event, agent_input, evidence, None, policy=POLICY) is None


@pytest.mark.parametrize(
    ("relationship", "lifecycle", "expected"),
    [
        (HypothesisRelationship.STRENGTHENED, HypothesisStatus.ACTIVE, ScenarioStatus.STRENGTHENED),
        (HypothesisRelationship.WEAKENED, HypothesisStatus.WEAKENING, ScenarioStatus.WEAKENED),
    ],
)
def test_intrabar_evidence_updates_existing_thesis(
    relationship: HypothesisRelationship,
    lifecycle: HypothesisStatus,
    expected: ScenarioStatus,
) -> None:
    updated = _update(
        _create(),
        event_type=RuntimeEventType.TICK,
        relationship=relationship,
        lifecycle=lifecycle,
        fact_name="retest_held",
        minutes=1,
        sequence=2,
    )
    assert updated.hypothesis_status is lifecycle
    assert expected in {scenario.status for scenario in updated.scenarios}


def test_intrabar_confirmation_makes_satisfied_branch_only_eligible() -> None:
    updated = _update(
        _create(),
        event_type=RuntimeEventType.M1_CLOSED,
        relationship=HypothesisRelationship.STRENGTHENED,
        lifecycle=HypothesisStatus.CONFIRMED,
        fact_name="micro_break",
        minutes=1,
        sequence=2,
    )

    assert updated.entry_eligibility is EntryEligibility.ELIGIBLE
    assert updated.scenarios[0].status is ScenarioStatus.CONFIRMED
    assert updated.scenarios[0].entry_eligibility is EntryEligibility.ELIGIBLE
    assert updated.scenarios[1].entry_eligibility is EntryEligibility.WATCHING
    assert "approved_volume_lots" not in updated.model_dump(mode="json")


def test_intrabar_invalidation_is_terminal() -> None:
    invalidated = _update(
        _create(),
        event_type=RuntimeEventType.TICK,
        relationship=HypothesisRelationship.INVALIDATED,
        lifecycle=HypothesisStatus.INVALIDATED,
        fact_name="invalidation_break",
        minutes=1,
        sequence=2,
        invalidated=True,
    )
    assert invalidated.hypothesis_status is HypothesisStatus.INVALIDATED
    assert invalidated.entry_eligibility is EntryEligibility.INVALIDATED
    assert all(item.status is ScenarioStatus.INVALIDATED for item in invalidated.scenarios)

    later = _event(RuntimeEventType.TICK, at=T0 + timedelta(minutes=2), sequence=3)
    agent_input, evidence = _agent_pair(
        later,
        fact_name="micro_break",
        relationship=HypothesisRelationship.STRENGTHENED,
        lifecycle=HypothesisStatus.CONFIRMED,
        previous_hypothesis_id=invalidated.hypothesis_id,
        thesis_id=invalidated.thesis_id,
    )
    assert update_scenario(later, agent_input, evidence, invalidated, policy=POLICY) is invalidated


def test_ttl_expiry_uses_event_availability_and_cannot_be_revived_intrabar() -> None:
    previous = _create()
    later = _event(RuntimeEventType.TICK, at=T0 + timedelta(minutes=16), sequence=2)
    agent_input, evidence = _agent_pair(
        later,
        fact_name="micro_break",
        relationship=HypothesisRelationship.STRENGTHENED,
        lifecycle=HypothesisStatus.CONFIRMED,
        previous_hypothesis_id=previous.hypothesis_id,
        thesis_id=previous.thesis_id,
    )

    expired = update_scenario(later, agent_input, evidence, previous, policy=POLICY)

    assert expired is not None
    assert expired.hypothesis_status is HypothesisStatus.EXPIRED
    assert expired.entry_eligibility is EntryEligibility.EXPIRED
    assert all(item.status is ScenarioStatus.EXPIRED for item in expired.scenarios)

    revival_event = _event(
        RuntimeEventType.TICK,
        at=T0 + timedelta(minutes=17),
        sequence=3,
    )
    revival_input, revival_evidence = _agent_pair(
        revival_event,
        fact_name="micro_break",
        relationship=HypothesisRelationship.STRENGTHENED,
        lifecycle=HypothesisStatus.CONFIRMED,
        previous_hypothesis_id=expired.hypothesis_id,
        thesis_id=expired.thesis_id,
    )
    assert (
        update_scenario(
            revival_event,
            revival_input,
            revival_evidence,
            expired,
            policy=POLICY,
        )
        is expired
    )


def test_explicit_intrabar_expiry_evidence_is_terminal() -> None:
    expired = _update(
        _create(),
        event_type=RuntimeEventType.M1_CLOSED,
        relationship=HypothesisRelationship.EXPIRED,
        lifecycle=HypothesisStatus.EXPIRED,
        fact_name="session_changed",
        minutes=1,
        sequence=2,
    )

    assert expired.hypothesis_status is HypothesisStatus.EXPIRED
    assert expired.entry_eligibility is EntryEligibility.EXPIRED
    assert all(item.status is ScenarioStatus.EXPIRED for item in expired.scenarios)


def test_new_m5_can_supersede_an_expired_thesis_with_a_distinct_identity() -> None:
    previous = _create()
    new_event = _event(
        RuntimeEventType.M5_CLOSED,
        at=T0 + timedelta(minutes=20),
        sequence=2,
    )
    agent_input, evidence = _agent_pair(
        new_event,
        hypothesis_id="hyp-b",
        hypothesis="fresh_m5_thesis",
        relationship=HypothesisRelationship.NEW,
        lifecycle=HypothesisStatus.DEVELOPING,
    )

    current = update_scenario(
        new_event,
        agent_input,
        evidence,
        previous,
        policy=POLICY,
        scenario_definitions=SCENARIOS,
    )

    assert current is not None
    assert current.thesis_id != previous.thesis_id
    assert current.supersedes_thesis_id == previous.thesis_id
    assert current.began_at == new_event.available_at


def test_m5_same_thesis_preserves_id_and_reversal_requires_distinct_id() -> None:
    previous = _create()
    continued = _update(
        previous,
        event_type=RuntimeEventType.M5_CLOSED,
        relationship=HypothesisRelationship.UNCHANGED,
        lifecycle=HypothesisStatus.ACTIVE,
        fact_name="m5_structure",
        minutes=5,
        sequence=2,
    )
    assert continued.thesis_id == previous.thesis_id

    reverse_event = _event(RuntimeEventType.M5_CLOSED, at=T0 + timedelta(minutes=10), sequence=3)
    reverse_input, reverse_evidence = _agent_pair(
        reverse_event,
        hypothesis_id="hyp-b",
        hypothesis="bearish_reversal",
        relationship=HypothesisRelationship.REVERSED,
        lifecycle=HypothesisStatus.DEVELOPING,
        previous_hypothesis_id=continued.hypothesis_id,
        thesis_id=None,
    )
    reversed_state = update_scenario(
        reverse_event,
        reverse_input,
        reverse_evidence,
        continued,
        policy=POLICY,
        scenario_definitions=SCENARIOS,
    )
    assert reversed_state is not None
    assert reversed_state.thesis_id != continued.thesis_id
    assert reversed_state.supersedes_thesis_id == continued.thesis_id


def test_intrabar_unrelated_thesis_is_rejected() -> None:
    previous = _create()
    event = _event(RuntimeEventType.TICK, at=T0 + timedelta(minutes=1), sequence=2)
    agent_input, evidence = _agent_pair(
        event,
        hypothesis_id="hyp-other",
        relationship=HypothesisRelationship.STRENGTHENED,
        lifecycle=HypothesisStatus.ACTIVE,
        previous_hypothesis_id="hyp-other",
        thesis_id="thesis-other",
    )
    with pytest.raises(ValueError, match="unrelated thesis"):
        update_scenario(event, agent_input, evidence, previous, policy=POLICY)


def test_scenario_count_is_bounded() -> None:
    definitions = tuple(
        ScenarioDefinition(name=f"branch-{index}", confirmation_facts=(f"fact-{index}",))
        for index in range(4)
    )
    event = _event(RuntimeEventType.M5_CLOSED, at=T0, sequence=1)
    agent_input, current = _agent_pair(event)
    with pytest.raises(ValueError, match="scenario"):
        update_scenario(
            event,
            agent_input,
            current,
            None,
            policy=POLICY,
            scenario_definitions=definitions,
        )


def test_delayed_older_market_time_is_accepted_at_later_availability() -> None:
    previous = _create()
    updated = _update(
        previous,
        event_type=RuntimeEventType.TICK,
        relationship=HypothesisRelationship.STRENGTHENED,
        lifecycle=HypothesisStatus.ACTIVE,
        fact_name="retest_held",
        minutes=2,
        sequence=2,
        event_time=T0 - timedelta(minutes=1),
    )
    assert updated.updated_at == T0 + timedelta(minutes=2)
    assert updated.latest_evidence_as_of == T0 + timedelta(minutes=2)
    assert updated.latest_evidence_available_at == T0 + timedelta(minutes=2)


def test_tampered_evidence_provenance_is_rejected() -> None:
    previous = _create()
    event = _event(RuntimeEventType.TICK, at=T0 + timedelta(minutes=1), sequence=2)
    agent_input, current = _agent_pair(
        event,
        fact_name="micro_break",
        relationship=HypothesisRelationship.STRENGTHENED,
        lifecycle=HypothesisStatus.CONFIRMED,
        previous_hypothesis_id=previous.hypothesis_id,
        thesis_id=previous.thesis_id,
    )
    body = current.model_dump(mode="python", exclude={"evidence_id"})
    body["evidence_for"][0]["fact_value"] = False
    tampered = AgentEvidence.model_validate(body)

    with pytest.raises(ValueError, match="fact value"):
        update_scenario(event, agent_input, tampered, previous, policy=POLICY)


def test_live_replay_equivalent_transitions_have_same_identity_without_clock() -> None:
    live = _create()
    replay = _create()
    assert live.state_id == replay.state_id
    assert live.expires_at == T0 + timedelta(seconds=POLICY.ttl_seconds)


def test_scenario_schema_rejects_execution_authorization() -> None:
    body = _create().model_dump(mode="python", exclude={"state_id"})
    body["risk_approved"] = True
    with pytest.raises(ValidationError):
        ThesisState.model_validate(body)
