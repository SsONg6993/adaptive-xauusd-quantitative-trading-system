from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.agents import (
    AbstentionReason,
    AgentEvidence,
    AgentInput,
    AgentStatus,
    AgentToolRequest,
    DirectionalBias,
    EvidencePolarity,
    EvidenceReference,
    HypothesisInvalidation,
    HypothesisRelationship,
    HypothesisStatus,
    ToolResultReference,
    transition_memory,
    validate_agent_output,
)
from axq.runtime import FreshnessStatus, initial_runtime_state
from axq.tools import (
    ToolCategory,
    ToolFact,
    ToolProvenance,
    ToolQuality,
    ToolResult,
    ToolStatus,
)

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)
STATE = initial_runtime_state("XAUUSD", at=T0)


def tool_result(
    *,
    status: ToolStatus = ToolStatus.AVAILABLE,
    freshness: FreshnessStatus = FreshnessStatus.AVAILABLE,
) -> ToolResult:
    has_fact = status in {ToolStatus.AVAILABLE, ToolStatus.STALE}
    return ToolResult(
        tool_name="momentum.core",
        tool_version="1.0.0",
        category=ToolCategory.MOMENTUM,
        as_of=T0,
        available_at=T0,
        runtime_state_id=STATE.state_id,
        input_snapshot_id="fs-test",
        freshness=freshness,
        status=status,
        facts=(ToolFact(name="momentum_rsi_14", value=57.25),) if has_fact else (),
        quality=ToolQuality(valid=has_fact),
        warnings=() if has_fact else ("tool input unavailable",),
        provenance=(
            ToolProvenance(
                source="phase2-feature-engine",
                source_version="2.0.0",
                source_identity="fm-test",
            ),
        ),
    )


def evidence(
    *,
    relationship: HypothesisRelationship = HypothesisRelationship.NEW,
    hypothesis_id: str = "hyp-1",
    previous_hypothesis_id: str | None = None,
    lifecycle: HypothesisStatus = HypothesisStatus.DEVELOPING,
    status: AgentStatus = AgentStatus.READY,
    direction: DirectionalBias | None = DirectionalBias.BULLISH,
    confidence: float = 0.6,
    uncertainty: float = 0.4,
    quality: float = 0.8,
    at: datetime = T0,
    result: ToolResult | None = None,
    invalidation: HypothesisInvalidation | None = None,
) -> AgentEvidence:
    source = result or tool_result()
    item = EvidenceReference(
        tool_name=source.tool_name,
        tool_result_id=source.result_id,
        fact_name="momentum_rsi_14",
        fact_value=57.25,
        polarity=EvidencePolarity.SUPPORTS,
        strength=0.7,
        freshness=source.freshness,
        quality_valid=source.quality.valid,
        explanation="RSI is above its midpoint",
    )
    return AgentEvidence(
        agent_name="chart",
        agent_version="1.0.0",
        runtime_state_id=STATE.state_id,
        feature_snapshot_id="fs-test",
        as_of=at,
        available_at=at,
        hypothesis_id=hypothesis_id,
        hypothesis="bullish_continuation",
        hypothesis_status=lifecycle,
        relationship=relationship,
        previous_hypothesis_id=previous_hypothesis_id,
        direction=direction,
        confidence=confidence,
        uncertainty=uncertainty,
        evidence_quality=quality,
        evidence_for=(item,),
        evidence_against=(),
        invalidation=invalidation or HypothesisInvalidation(invalidated=False),
        freshness=source.freshness,
        status=status,
        tool_inputs=(ToolResultReference.from_result(source),),
        rationale="Momentum supports continuation.",
    )


def test_agent_evidence_identity_is_deterministic_and_round_trips() -> None:
    first = evidence()
    second = evidence()

    assert first.evidence_id == second.evidence_id
    assert AgentEvidence.model_validate_json(first.model_dump_json()) == first


def test_agent_input_binds_tools_without_exposing_account_state() -> None:
    result = tool_result()

    agent_input = AgentInput.from_runtime(
        state=STATE,
        feature_snapshot_id="fs-test",
        tool_results=(result,),
        previous_memory=None,
    )
    serialized = agent_input.model_dump(mode="json")

    assert agent_input.runtime_state_id == STATE.state_id
    assert "account" not in serialized
    assert "balance" not in str(serialized).lower()
    assert agent_input.tool_health_status is AgentStatus.READY


@pytest.mark.parametrize(
    ("tool_status", "freshness", "expected"),
    [
        (ToolStatus.STALE, FreshnessStatus.STALE, AgentStatus.DEGRADED),
        (ToolStatus.UNAVAILABLE, FreshnessStatus.UNAVAILABLE, AgentStatus.ABSTAINED),
        (ToolStatus.INSUFFICIENT_DATA, FreshnessStatus.AVAILABLE, AgentStatus.ABSTAINED),
        (ToolStatus.ERROR, FreshnessStatus.UNAVAILABLE, AgentStatus.ERROR),
    ],
)
def test_agent_input_preserves_non_available_tool_semantics(
    tool_status: ToolStatus,
    freshness: FreshnessStatus,
    expected: AgentStatus,
) -> None:
    result = tool_result(status=tool_status, freshness=freshness)
    agent_input = AgentInput.from_runtime(
        state=STATE,
        feature_snapshot_id="fs-test",
        tool_results=(result,),
        previous_memory=None,
    )
    assert agent_input.tool_health_status is expected


def test_evidence_provenance_is_checked_against_exact_tool_fact() -> None:
    result = tool_result()
    agent_input = AgentInput.from_runtime(
        state=STATE,
        feature_snapshot_id="fs-test",
        tool_results=(result,),
        previous_memory=None,
    )
    current = evidence(result=result)

    validate_agent_output(agent_input, current)

    tampered = current.model_dump(mode="python", exclude={"evidence_id"})
    tampered["evidence_for"][0]["fact_value"] = 99.0
    wrong = AgentEvidence.model_validate(tampered)
    with pytest.raises(ValueError, match="fact value"):
        validate_agent_output(agent_input, wrong)


def test_confidence_cannot_exceed_evidence_quality() -> None:
    with pytest.raises(ValidationError, match="evidence quality"):
        evidence(confidence=0.9, uncertainty=0.1, quality=0.4)
    with pytest.raises(ValidationError):
        evidence(confidence=1.1)
    with pytest.raises(ValidationError):
        evidence(uncertainty=-0.1)


def test_degraded_evidence_cannot_claim_high_confidence() -> None:
    stale = tool_result(status=ToolStatus.STALE, freshness=FreshnessStatus.STALE)
    with pytest.raises(ValidationError, match="degraded confidence"):
        evidence(
            result=stale,
            status=AgentStatus.DEGRADED,
            confidence=0.8,
            quality=0.8,
        )


def test_abstention_is_explicit_and_has_no_direction() -> None:
    abstained = AgentEvidence(
        agent_name="regime",
        agent_version="1.0.0",
        runtime_state_id=STATE.state_id,
        feature_snapshot_id="fs-test",
        as_of=T0,
        available_at=T0,
        hypothesis_id="hyp-none",
        hypothesis="no_meaningful_hypothesis",
        hypothesis_status=HypothesisStatus.ABSTAINED,
        relationship=HypothesisRelationship.NEW,
        direction=None,
        confidence=0.0,
        uncertainty=1.0,
        evidence_quality=0.0,
        invalidation=HypothesisInvalidation(invalidated=False),
        freshness=FreshnessStatus.UNAVAILABLE,
        status=AgentStatus.ABSTAINED,
        abstention_reason=AbstentionReason.INSUFFICIENT_DATA,
    )

    assert abstained.direction is None
    assert abstained.abstention_reason is AbstentionReason.INSUFFICIENT_DATA
    with pytest.raises(ValidationError, match="abstention reason"):
        evidence(
            status=AgentStatus.ABSTAINED,
            direction=None,
            confidence=0.0,
            lifecycle=HypothesisStatus.ABSTAINED,
        )


def test_previous_hypothesis_relationship_is_structurally_validated() -> None:
    with pytest.raises(ValidationError, match="previous_hypothesis_id"):
        evidence(relationship=HypothesisRelationship.STRENGTHENED)
    with pytest.raises(ValidationError, match="new hypothesis_id"):
        evidence(
            relationship=HypothesisRelationship.REVERSED,
            previous_hypothesis_id="hyp-1",
            hypothesis_id="hyp-1",
        )


def test_memory_transition_tracks_previous_state_and_confirmation_count() -> None:
    first = evidence()
    memory = transition_memory(None, first)
    strengthened = evidence(
        relationship=HypothesisRelationship.STRENGTHENED,
        previous_hypothesis_id="hyp-1",
        lifecycle=HypothesisStatus.CONFIRMED,
        confidence=0.7,
        quality=0.8,
        at=T0 + timedelta(minutes=5),
    )

    updated = transition_memory(memory, strengthened)

    assert updated.previous_hypothesis == "bullish_continuation"
    assert updated.previous_evidence_id == first.evidence_id
    assert updated.latest_evidence_id == strengthened.evidence_id
    assert updated.confirmation_count == 1
    assert updated.relationship is HypothesisRelationship.STRENGTHENED
    assert type(updated).model_validate_json(updated.model_dump_json()) == updated


def test_invalid_hypothesis_lifecycle_transition_is_rejected() -> None:
    memory = transition_memory(None, evidence())
    invalidated = evidence(
        lifecycle=HypothesisStatus.INVALIDATED,
        relationship=HypothesisRelationship.INVALIDATED,
        previous_hypothesis_id="hyp-1",
        at=T0 + timedelta(minutes=5),
        invalidation=HypothesisInvalidation(
            invalidated=True,
            reason="structure broke",
        ),
    )
    memory = transition_memory(memory, invalidated)

    unchanged = evidence(
        lifecycle=HypothesisStatus.ACTIVE,
        relationship=HypothesisRelationship.UNCHANGED,
        previous_hypothesis_id="hyp-1",
        at=T0 + timedelta(minutes=10),
    )
    with pytest.raises(ValueError, match="lifecycle transition"):
        transition_memory(memory, unchanged)


def test_terminal_hypothesis_can_start_a_distinct_new_hypothesis() -> None:
    memory = transition_memory(None, evidence())
    invalidated = evidence(
        lifecycle=HypothesisStatus.INVALIDATED,
        relationship=HypothesisRelationship.INVALIDATED,
        previous_hypothesis_id="hyp-1",
        at=T0 + timedelta(minutes=5),
        invalidation=HypothesisInvalidation(
            invalidated=True,
            reason="structure broke",
        ),
    )
    terminal = transition_memory(memory, invalidated)
    replacement = evidence(
        hypothesis_id="hyp-2",
        relationship=HypothesisRelationship.NEW,
        previous_hypothesis_id=None,
        lifecycle=HypothesisStatus.DEVELOPING,
        at=T0 + timedelta(minutes=10),
    )

    restarted = transition_memory(terminal, replacement)

    assert restarted.hypothesis_id == "hyp-2"
    assert restarted.began_at == T0 + timedelta(minutes=10)
    assert restarted.previous_hypothesis == terminal.current_hypothesis


def test_tool_requests_are_typed_and_bounded() -> None:
    request = AgentToolRequest(
        tool_name="structure.core",
        requested_facts=("structure_bos_up", "structure_distance_resistance_atr"),
        reason="confirm breakout quality",
    )
    body = evidence().model_dump(mode="python", exclude={"evidence_id"})
    body["tool_requests"] = (request,) * 9

    with pytest.raises(ValidationError):
        AgentEvidence.model_validate(body)


def test_agent_evidence_has_no_execution_authorization_fields() -> None:
    body = evidence().model_dump(mode="python", exclude={"evidence_id"})
    body["approved_volume_lots"] = 0.1
    with pytest.raises(ValidationError):
        AgentEvidence.model_validate(body)


def test_live_replay_equivalent_agent_inputs_have_same_identity() -> None:
    result = tool_result()
    live = AgentInput.from_runtime(
        state=STATE,
        feature_snapshot_id="fs-test",
        tool_results=(result,),
        previous_memory=None,
    )
    replay = AgentInput.model_validate_json(live.model_dump_json())

    assert evidence().evidence_id == evidence().evidence_id
    assert live == replay
