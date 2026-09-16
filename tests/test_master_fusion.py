from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from axq.agents import (
    AbstentionReason,
    AgentEvidence,
    AgentInput,
    AgentStatus,
    DirectionalBias,
    EvidencePolarity,
    EvidenceReference,
    HypothesisInvalidation,
    HypothesisRelationship,
    HypothesisStatus,
    transition_memory,
)
from axq.master import (
    EvidenceDisposition,
    FusionReason,
    MasterProposal,
    SpecialistWeight,
    default_fusion_policy,
    fuse_evidence,
)
from axq.runtime import FreshnessStatus
from axq.runtime.kernel import AGENT_ORDER, EvidenceBundle
from axq.schemas import Signal

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)
STATE_ID = "state-master-test"


def _reference(polarity: EvidencePolarity, strength: float) -> EvidenceReference:
    return EvidenceReference(
        tool_name="fixture.fact",
        tool_result_id=f"tool-{polarity.value.lower()}-{strength}",
        fact_name=f"{polarity.value.lower()}_fact",
        fact_value=strength,
        polarity=polarity,
        strength=strength,
        freshness=FreshnessStatus.AVAILABLE,
        quality_valid=True,
    )


def _evidence(
    agent_name: str,
    direction: DirectionalBias | None,
    *,
    status: AgentStatus = AgentStatus.READY,
    confidence: float = 0.8,
    uncertainty: float = 0.1,
    support_strength: float | None = None,
    contradiction_strength: float | None = None,
) -> AgentEvidence:
    abstained = status is AgentStatus.ABSTAINED
    failed = status is AgentStatus.ERROR
    effective_confidence = 0.0 if abstained or failed else confidence
    evidence_for = (
        (_reference(EvidencePolarity.SUPPORTS, support_strength),)
        if support_strength is not None
        else ()
    )
    evidence_against = (
        (_reference(EvidencePolarity.CONTRADICTS, contradiction_strength),)
        if contradiction_strength is not None
        else ()
    )
    return AgentEvidence(
        agent_name=agent_name,
        agent_version="1.0.0",
        runtime_state_id=STATE_ID,
        as_of=T0,
        available_at=T0,
        hypothesis_id=f"hyp-{agent_name}",
        hypothesis=f"{agent_name} fixture hypothesis",
        hypothesis_status=(
            HypothesisStatus.ABSTAINED
            if abstained
            else HypothesisStatus.NONE
            if failed
            else HypothesisStatus.ACTIVE
        ),
        relationship=HypothesisRelationship.NEW,
        direction=None if abstained or failed else direction,
        confidence=effective_confidence,
        uncertainty=uncertainty,
        evidence_quality=0.0 if abstained or failed else 0.9,
        evidence_for=evidence_for,
        evidence_against=evidence_against,
        invalidation=HypothesisInvalidation(invalidated=False),
        freshness=(
            FreshnessStatus.UNAVAILABLE
            if abstained or failed
            else FreshnessStatus.STALE
            if status is AgentStatus.DEGRADED
            else FreshnessStatus.AVAILABLE
        ),
        status=status,
        abstention_reason=(AbstentionReason.INSUFFICIENT_DATA if abstained else None),
    )


def _bundle(
    overrides: dict[str, AgentEvidence],
) -> EvidenceBundle:
    evidence = tuple(
        overrides.get(name, _evidence(name, None, confidence=0.4))
        for name in AGENT_ORDER
    )
    inputs = tuple(
        AgentInput(runtime_state_id=STATE_ID, as_of=T0, tool_results=())
        for _ in AGENT_ORDER
    )
    memories = tuple(transition_memory(None, item) for item in evidence)
    return EvidenceBundle(
        event_id="ev-master-test",
        runtime_state_id=STATE_ID,
        as_of=T0,
        agent_inputs=inputs,
        evidence=evidence,
        memories=memories,
    )


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        (DirectionalBias.BULLISH, Signal.BUY),
        (DirectionalBias.BEARISH, Signal.SELL),
    ],
)
def test_aligned_ready_directional_evidence_is_actionable(
    direction: DirectionalBias,
    expected: Signal,
) -> None:
    bundle = _bundle(
        {
            "chart": _evidence("chart", direction, confidence=0.85),
            "quant": _evidence("quant", direction, confidence=0.75),
        }
    )

    proposal = fuse_evidence(bundle, default_fusion_policy())

    assert proposal.decision is expected
    assert proposal.actionable is True
    assert proposal.confidence >= 0.55
    assert proposal.net_score > 0 if expected is Signal.BUY else proposal.net_score < 0


def test_balanced_opposing_specialists_hold_with_high_disagreement() -> None:
    bundle = _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH, confidence=0.8),
            "quant": _evidence("quant", DirectionalBias.BEARISH, confidence=0.8),
        }
    )

    proposal = fuse_evidence(bundle, default_fusion_policy())

    assert proposal.decision is Signal.HOLD
    assert proposal.disagreement == pytest.approx(1.0)
    assert FusionReason.HIGH_DISAGREEMENT in proposal.reason_codes


def test_internal_counterevidence_is_distinct_from_cross_agent_disagreement() -> None:
    bundle = _bundle(
        {
            "chart": _evidence(
                "chart",
                DirectionalBias.BULLISH,
                confidence=0.8,
                support_strength=0.2,
                contradiction_strength=0.8,
            ),
            "quant": _evidence(
                "quant",
                DirectionalBias.BULLISH,
                confidence=0.8,
                support_strength=0.2,
                contradiction_strength=0.8,
            ),
        }
    )

    proposal = fuse_evidence(bundle, default_fusion_policy())

    assert proposal.decision is Signal.HOLD
    assert proposal.contradiction == pytest.approx(0.8)
    assert proposal.disagreement == pytest.approx(0.0)
    assert FusionReason.HIGH_CONTRADICTION in proposal.reason_codes


def test_degraded_abstained_and_error_evidence_have_explicit_dispositions() -> None:
    bundle = _bundle(
        {
            "chart": _evidence(
                "chart",
                DirectionalBias.BULLISH,
                status=AgentStatus.DEGRADED,
                confidence=0.5,
            ),
            "quant": _evidence("quant", None, status=AgentStatus.ABSTAINED),
            "historical": _evidence("historical", None, status=AgentStatus.ERROR),
        }
    )

    proposal = fuse_evidence(bundle, default_fusion_policy())
    by_agent = {item.agent_name: item for item in proposal.contributions}

    assert proposal.decision is Signal.HOLD
    assert by_agent["chart"].disposition is EvidenceDisposition.DEGRADED_CONTRIBUTION
    assert by_agent["quant"].disposition is EvidenceDisposition.ABSTAINED
    assert by_agent["historical"].disposition is EvidenceDisposition.ERROR
    assert by_agent["regime"].disposition is EvidenceDisposition.CONTEXT_ONLY
    assert FusionReason.NO_READY_DIRECTIONAL_EVIDENCE in proposal.reason_codes


def test_policy_identity_is_content_addressed_and_weight_order_stable() -> None:
    policy = default_fusion_policy()
    reversed_policy = policy.model_copy(
        update={
            "policy_id": "",
            "specialist_weights": tuple(reversed(policy.specialist_weights)),
        }
    )
    reversed_policy = type(policy).model_validate(reversed_policy.model_dump())
    assert reversed_policy.policy_id == policy.policy_id


def test_live_and_replay_equivalent_bundles_produce_identical_proposal() -> None:
    bundle = _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH),
            "quant": _evidence("quant", DirectionalBias.BULLISH),
        }
    )
    replayed_bundle = EvidenceBundle.model_validate_json(bundle.model_dump_json())
    policy = default_fusion_policy()

    live_proposal = fuse_evidence(bundle, policy)
    replay_proposal = fuse_evidence(replayed_bundle, policy)

    assert replay_proposal == live_proposal
    assert replay_proposal.proposal_id == live_proposal.proposal_id


def test_policy_change_changes_proposal_identity() -> None:
    bundle = _bundle({"chart": _evidence("chart", DirectionalBias.BULLISH)})
    policy = default_fusion_policy()
    changed = policy.model_copy(
        update={
            "policy_id": "",
            "specialist_weights": tuple(
                SpecialistWeight(agent_name=item.agent_name, weight=1.5)
                if item.agent_name == "chart"
                else item
                for item in policy.specialist_weights
            ),
        }
    )
    changed = type(policy).model_validate(changed.model_dump())

    assert fuse_evidence(bundle, changed).proposal_id != fuse_evidence(bundle, policy).proposal_id


def test_master_proposal_schema_rejects_sizing_or_execution_fields() -> None:
    bundle = _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH),
            "quant": _evidence("quant", DirectionalBias.BULLISH),
        }
    )
    proposal = fuse_evidence(bundle, default_fusion_policy())

    with pytest.raises(ValidationError):
        MasterProposal.model_validate(proposal.model_dump() | {"volume_lots": 0.1})
