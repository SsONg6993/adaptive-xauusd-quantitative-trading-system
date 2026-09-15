"""Pure deterministic construction of one evidence-bound interaction round."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from axq.agents import AgentEvidence, DirectionalBias
from axq.interaction.contracts import (
    InteractionResolutionStatus,
    InteractionTurnType,
    MasterConflictAssessment,
    SpecialistInteractionResolution,
    SpecialistInteractionRound,
    SpecialistInteractionSession,
    SpecialistInteractionTurn,
)
from axq.master import EvidenceDisposition, FusionPolicy, FusionReason, MasterProposal
from axq.runtime.kernel import AGENT_ORDER, EvidenceBundle
from axq.runtime.state import UTCDateTime


class SpecialistRebuttal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stance: DirectionalBias
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1, max_length=420)
    cited_evidence_ids: tuple[str, ...] = Field(min_length=1)


class SpecialistResponder(Protocol):
    def respond(
        self,
        *,
        evidence: AgentEvidence,
        challenge: SpecialistInteractionTurn,
    ) -> SpecialistRebuttal | object: ...


class DeterministicEvidenceBoundResponder:
    def respond(
        self,
        *,
        evidence: AgentEvidence,
        challenge: SpecialistInteractionTurn,
    ) -> SpecialistRebuttal:
        del challenge
        if evidence.direction not in {DirectionalBias.BULLISH, DirectionalBias.BEARISH}:
            raise ValueError("evidence-bound responder requires directional evidence")
        rationale = evidence.rationale or evidence.hypothesis
        limitation = (
            "Recorded counterevidence remains acknowledged."
            if evidence.evidence_against
            else f"Recorded uncertainty remains {evidence.uncertainty:.0%}."
        )
        return SpecialistRebuttal(
            stance=evidence.direction,
            confidence=evidence.confidence,
            rationale=f"{rationale} {limitation} Stance and confidence are unchanged.",
            cited_evidence_ids=(evidence.evidence_id,),
        )


def _selected_specialists(proposal: MasterProposal) -> tuple[str, ...]:
    eligible = [
        item
        for item in proposal.contributions
        if item.direction in {DirectionalBias.BULLISH, DirectionalBias.BEARISH}
        and item.disposition
        in {EvidenceDisposition.CONTRIBUTED, EvidenceDisposition.DEGRADED_CONTRIBUTION}
        and item.applied_weight > 0.0
    ]
    by_direction = {
        direction: sorted(
            (item for item in eligible if item.direction is direction),
            key=lambda item: (-item.effective_strength, AGENT_ORDER.index(item.agent_name)),
        )
        for direction in (DirectionalBias.BULLISH, DirectionalBias.BEARISH)
    }
    selected = [by_direction[DirectionalBias.BULLISH][0], by_direction[DirectionalBias.BEARISH][0]]
    selected_ids = {item.evidence_id for item in selected}
    remaining = sorted(
        (item for item in eligible if item.evidence_id not in selected_ids),
        key=lambda item: (-item.effective_strength, AGENT_ORDER.index(item.agent_name)),
    )
    selected.extend(remaining[:1])
    names = {item.agent_name for item in selected}
    return tuple(name for name in AGENT_ORDER if name in names)


def build_evidence_bound_interaction(
    *,
    bundle: EvidenceBundle,
    proposal: MasterProposal,
    policy: FusionPolicy,
    scan_id: str,
    available_at: UTCDateTime,
    responder: SpecialistResponder | None = None,
) -> SpecialistInteractionSession:
    """Build explanatory turns without changing or replacing AgentEvidence."""
    contributions = tuple(
        item
        for item in proposal.contributions
        if item.disposition
        in {EvidenceDisposition.CONTRIBUTED, EvidenceDisposition.DEGRADED_CONTRIBUTION}
        and item.applied_weight > 0.0
    )
    bullish = tuple(
        item.evidence_id for item in contributions if item.direction is DirectionalBias.BULLISH
    )
    bearish = tuple(
        item.evidence_id for item in contributions if item.direction is DirectionalBias.BEARISH
    )
    required = bool(bullish and bearish) and (
        FusionReason.HIGH_DISAGREEMENT in proposal.reason_codes
    )
    participants = _selected_specialists(proposal) if required else ()
    assessment = MasterConflictAssessment(
        event_id=bundle.event_id,
        scan_id=scan_id,
        evidence_bundle_id=bundle.bundle_id,
        master_proposal_id=proposal.proposal_id,
        fusion_policy_id=policy.policy_id,
        fusion_policy_version=policy.policy_version,
        initial_evidence_ids=tuple(item.evidence_id for item in bundle.evidence),
        bullish_evidence_ids=bullish,
        bearish_evidence_ids=bearish,
        measured_disagreement=proposal.disagreement,
        disagreement_threshold=policy.maximum_actionable_disagreement,
        interaction_required=required,
        selected_specialists=participants,
        as_of=proposal.as_of,
        available_at=available_at,
    )
    if not required:
        return SpecialistInteractionSession(assessment=assessment)

    round_value = SpecialistInteractionRound(
        assessment_id=assessment.assessment_id,
        event_id=bundle.event_id,
        scan_id=scan_id,
        evidence_bundle_id=bundle.bundle_id,
        initial_evidence_ids=assessment.initial_evidence_ids,
        participating_specialists=participants,
        as_of=proposal.as_of,
        available_at=available_at,
    )
    actual_responder = responder or DeterministicEvidenceBoundResponder()
    turns: list[SpecialistInteractionTurn] = []
    status = InteractionResolutionStatus.COMPLETED
    failure_reason: str | None = None
    for participant in participants:
        evidence = bundle.by_agent(participant)
        conflicts = bearish if evidence.direction is DirectionalBias.BULLISH else bullish
        challenge = SpecialistInteractionTurn(
            round_id=round_value.round_id,
            turn_index=len(turns),
            speaker="master",
            recipient=participant,
            turn_type=InteractionTurnType.MASTER_CHALLENGE,
            original_evidence_id=evidence.evidence_id,
            conflicting_evidence_ids=conflicts,
            rationale=(
                "Opposing directional evidence is material. Restate only the recorded "
                "evidence for your stance and acknowledge its recorded limitations."
            ),
            cited_evidence_ids=(evidence.evidence_id, *conflicts),
            as_of=proposal.as_of,
            available_at=available_at,
        )
        turns.append(challenge)
        try:
            raw = actual_responder.respond(evidence=evidence, challenge=challenge)
            reply = SpecialistRebuttal.model_validate(raw)
            if reply.stance is not evidence.direction:
                raise ValueError("rebuttal cannot reverse direction")
            if reply.confidence != evidence.confidence:
                raise ValueError("rebuttal must preserve original confidence")
            if reply.cited_evidence_ids != (evidence.evidence_id,):
                raise ValueError("rebuttal may cite only original evidence")
            turns.append(
                SpecialistInteractionTurn(
                    round_id=round_value.round_id,
                    turn_index=len(turns),
                    speaker=participant,
                    recipient="master",
                    turn_type=InteractionTurnType.SPECIALIST_REBUTTAL,
                    original_evidence_id=evidence.evidence_id,
                    conflicting_evidence_ids=conflicts,
                    stance=reply.stance,
                    confidence=reply.confidence,
                    rationale=reply.rationale,
                    cited_evidence_ids=reply.cited_evidence_ids,
                    predecessor_turn_id=challenge.turn_id,
                    as_of=proposal.as_of,
                    available_at=available_at,
                )
            )
        except TimeoutError:
            status = InteractionResolutionStatus.TIMED_OUT
            failure_reason = "BOUNDED_INTERACTION_TIMEOUT"
            break
        except Exception:
            status = InteractionResolutionStatus.MALFORMED
            failure_reason = "INVALID_EVIDENCE_BOUND_REBUTTAL"
            break

    resolution = SpecialistInteractionResolution(
        round_id=round_value.round_id,
        assessment_id=assessment.assessment_id,
        event_id=bundle.event_id,
        master_proposal_id=proposal.proposal_id,
        ordered_turn_ids=tuple(item.turn_id for item in turns),
        status=status,
        failure_reason=failure_reason,
        as_of=proposal.as_of,
        available_at=available_at,
    )
    return SpecialistInteractionSession(
        assessment=assessment,
        round=round_value,
        turns=tuple(turns),
        resolution=resolution,
    )
