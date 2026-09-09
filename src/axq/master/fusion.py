"""Pure deterministic baseline for fusing a Phase 6 evidence bundle."""

from __future__ import annotations

from axq.agents import (
    AgentEvidence,
    AgentStatus,
    DirectionalBias,
    HypothesisStatus,
)
from axq.master.contracts import (
    EvidenceDisposition,
    FusionPolicy,
    FusionReason,
    MasterProposal,
    SpecialistContribution,
    SpecialistWeight,
)
from axq.runtime.kernel import AGENT_ORDER, EvidenceBundle
from axq.schemas import Signal


def default_fusion_policy() -> FusionPolicy:
    return FusionPolicy(
        policy_version="1.0.0",
        specialist_weights=tuple(
            SpecialistWeight(agent_name=name, weight=1.0) for name in AGENT_ORDER
        ),
        degraded_weight_multiplier=0.5,
        minimum_actionable_score=0.2,
        minimum_actionable_confidence=0.55,
        maximum_actionable_uncertainty=0.6,
        maximum_actionable_contradiction=0.6,
        maximum_actionable_disagreement=0.6,
        minimum_ready_directional_agents=1,
    )


def _internal_contradiction(evidence: AgentEvidence) -> float:
    supporting = sum(item.strength for item in evidence.evidence_for)
    opposing = sum(item.strength for item in evidence.evidence_against)
    total = supporting + opposing
    return opposing / total if total else 0.0


def _contribution(
    evidence: AgentEvidence,
    configured_weight: float,
    degraded_multiplier: float,
) -> SpecialistContribution:
    terminal = evidence.hypothesis_status in {
        HypothesisStatus.INVALIDATED,
        HypothesisStatus.EXPIRED,
    }
    if evidence.status is AgentStatus.ERROR:
        disposition = EvidenceDisposition.ERROR
        multiplier = 0.0
    elif evidence.status is AgentStatus.ABSTAINED:
        disposition = EvidenceDisposition.ABSTAINED
        multiplier = 0.0
    elif terminal or evidence.invalidation.invalidated:
        disposition = EvidenceDisposition.TERMINAL
        multiplier = 0.0
    elif evidence.direction in {None, DirectionalBias.NEUTRAL}:
        disposition = EvidenceDisposition.CONTEXT_ONLY
        multiplier = 0.0
    elif evidence.confidence == 0.0:
        disposition = EvidenceDisposition.ZERO_CONFIDENCE
        multiplier = 0.0
    elif evidence.status is AgentStatus.DEGRADED:
        disposition = EvidenceDisposition.DEGRADED_CONTRIBUTION
        multiplier = degraded_multiplier
    else:
        disposition = EvidenceDisposition.CONTRIBUTED
        multiplier = 1.0

    applied_weight = configured_weight * multiplier
    strength = applied_weight * evidence.confidence * (1.0 - evidence.uncertainty)
    sign = (
        1.0
        if evidence.direction is DirectionalBias.BULLISH
        else -1.0
        if evidence.direction is DirectionalBias.BEARISH
        else 0.0
    )
    return SpecialistContribution(
        agent_name=evidence.agent_name,
        evidence_id=evidence.evidence_id,
        status=evidence.status,
        direction=evidence.direction,
        disposition=disposition,
        configured_weight=configured_weight,
        applied_weight=applied_weight,
        effective_strength=strength,
        signed_score=sign * strength,
        uncertainty=evidence.uncertainty,
        internal_contradiction=_internal_contradiction(evidence),
    )


def _bounded(value: float) -> float:
    return min(1.0, max(0.0, value))


def fuse_evidence(bundle: EvidenceBundle, policy: FusionPolicy) -> MasterProposal:
    """Fuse one immutable bundle without state, wall-clock reads, or side effects."""
    weights = {item.agent_name: item.weight for item in policy.specialist_weights}
    contributions = tuple(
        _contribution(
            evidence,
            weights[evidence.agent_name],
            policy.degraded_weight_multiplier,
        )
        for evidence in bundle.evidence
    )
    directional = tuple(item for item in contributions if item.applied_weight > 0.0)
    total_weight = sum(item.applied_weight for item in directional)
    bullish_strength = sum(max(0.0, item.signed_score) for item in directional)
    bearish_strength = sum(max(0.0, -item.signed_score) for item in directional)
    bullish_score = bullish_strength / total_weight if total_weight else 0.0
    bearish_score = bearish_strength / total_weight if total_weight else 0.0
    net_score = bullish_score - bearish_score
    directional_strength = bullish_strength + bearish_strength
    disagreement = (
        2.0 * min(bullish_strength, bearish_strength) / directional_strength
        if directional_strength
        else 0.0
    )
    contradiction = (
        sum(
            item.effective_strength * item.internal_contradiction
            for item in directional
        )
        / directional_strength
        if directional_strength
        else 0.0
    )
    uncertainty = (
        sum(item.applied_weight * item.uncertainty for item in directional) / total_weight
        if total_weight
        else 1.0
    )
    confidence = max(bullish_score, bearish_score) * (1.0 - disagreement) * (
        1.0 - contradiction
    )
    ready_count = sum(
        item.disposition is EvidenceDisposition.CONTRIBUTED for item in contributions
    )

    reasons: list[FusionReason] = []
    if ready_count < policy.minimum_ready_directional_agents:
        reasons.append(FusionReason.NO_READY_DIRECTIONAL_EVIDENCE)
    if abs(net_score) < policy.minimum_actionable_score:
        reasons.append(FusionReason.BELOW_SCORE_THRESHOLD)
    if confidence < policy.minimum_actionable_confidence:
        reasons.append(FusionReason.LOW_CONFIDENCE)
    if uncertainty > policy.maximum_actionable_uncertainty:
        reasons.append(FusionReason.HIGH_UNCERTAINTY)
    if contradiction > policy.maximum_actionable_contradiction:
        reasons.append(FusionReason.HIGH_CONTRADICTION)
    if disagreement > policy.maximum_actionable_disagreement:
        reasons.append(FusionReason.HIGH_DISAGREEMENT)

    if reasons:
        decision = Signal.HOLD
    elif net_score > 0.0:
        decision = Signal.BUY
        reasons.append(FusionReason.ACTIONABLE_BUY)
    else:
        decision = Signal.SELL
        reasons.append(FusionReason.ACTIONABLE_SELL)

    return MasterProposal(
        bundle_id=bundle.bundle_id,
        event_id=bundle.event_id,
        runtime_state_id=bundle.runtime_state_id,
        as_of=bundle.as_of,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        decision=decision,
        actionable=decision is not Signal.HOLD,
        confidence=_bounded(confidence),
        net_score=max(-1.0, min(1.0, net_score)),
        bullish_score=_bounded(bullish_score),
        bearish_score=_bounded(bearish_score),
        contradiction=_bounded(contradiction),
        disagreement=_bounded(disagreement),
        uncertainty=_bounded(uncertainty),
        ready_directional_agents=ready_count,
        contributing_evidence_ids=tuple(item.evidence_id for item in directional),
        contributions=contributions,
        reason_codes=tuple(reasons),
    )
