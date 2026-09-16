"""Persistent specialist memory and deterministic lifecycle transitions."""

from __future__ import annotations

from pydantic import Field, model_validator

from axq.agents.contracts import (
    AgentEvidence,
    AgentModel,
    AgentToolRequest,
    HypothesisInvalidation,
    HypothesisRelationship,
    HypothesisStatus,
)
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class AgentMemory(AgentModel):
    memory_id: str = ""
    agent_name: str = Field(min_length=1)
    agent_version: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    current_hypothesis: str = Field(min_length=1, max_length=200)
    previous_hypothesis: str | None = None
    current_confidence: float = Field(ge=0.0, le=1.0)
    previous_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    running_uncertainty: float = Field(ge=0.0, le=1.0)
    hypothesis_status: HypothesisStatus
    relationship: HypothesisRelationship
    began_at: UTCDateTime
    updated_at: UTCDateTime
    supporting_evidence_history: tuple[str, ...]
    invalidation: HypothesisInvalidation
    recent_tool_requests: tuple[AgentToolRequest, ...] = Field(default=(), max_length=8)
    previous_evidence_id: str | None = None
    latest_evidence_id: str = Field(min_length=1)
    confirmation_count: int = Field(default=0, ge=0)
    setup_id: str | None = None
    thesis_id: str | None = None

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> AgentMemory:
        if self.updated_at < self.began_at:
            raise ValueError("memory update cannot precede hypothesis start")
        if (
            self.hypothesis_status is HypothesisStatus.INVALIDATED
            and not self.invalidation.invalidated
        ):
            raise ValueError("invalidated memory requires invalidation details")
        identity = self.model_dump(mode="json", exclude={"memory_id"})
        expected = f"am-{canonical_hash(identity)[:20]}"
        if self.memory_id and self.memory_id != expected:
            raise ValueError("memory_id does not match memory content")
        object.__setattr__(self, "memory_id", expected)
        return self


_ALLOWED_TRANSITIONS: dict[HypothesisStatus, set[HypothesisStatus]] = {
    HypothesisStatus.NONE: {
        HypothesisStatus.NONE,
        HypothesisStatus.DEVELOPING,
        HypothesisStatus.ABSTAINED,
    },
    HypothesisStatus.DEVELOPING: {
        HypothesisStatus.DEVELOPING,
        HypothesisStatus.ACTIVE,
        HypothesisStatus.CONFIRMED,
        HypothesisStatus.WEAKENING,
        HypothesisStatus.INVALIDATED,
        HypothesisStatus.EXPIRED,
        HypothesisStatus.ABSTAINED,
    },
    HypothesisStatus.ACTIVE: {
        HypothesisStatus.ACTIVE,
        HypothesisStatus.CONFIRMED,
        HypothesisStatus.WEAKENING,
        HypothesisStatus.INVALIDATED,
        HypothesisStatus.EXPIRED,
    },
    HypothesisStatus.CONFIRMED: {
        HypothesisStatus.CONFIRMED,
        HypothesisStatus.WEAKENING,
        HypothesisStatus.INVALIDATED,
        HypothesisStatus.EXPIRED,
    },
    HypothesisStatus.WEAKENING: {
        HypothesisStatus.WEAKENING,
        HypothesisStatus.ACTIVE,
        HypothesisStatus.CONFIRMED,
        HypothesisStatus.INVALIDATED,
        HypothesisStatus.EXPIRED,
    },
    HypothesisStatus.INVALIDATED: {HypothesisStatus.INVALIDATED},
    HypothesisStatus.EXPIRED: {HypothesisStatus.EXPIRED},
    HypothesisStatus.ABSTAINED: {
        HypothesisStatus.ABSTAINED,
        HypothesisStatus.DEVELOPING,
    },
}


def transition_memory(
    previous: AgentMemory | None,
    evidence: AgentEvidence,
) -> AgentMemory:
    """Apply one validated evidence result to persistent structured memory."""
    if previous is None:
        if evidence.relationship is not HypothesisRelationship.NEW:
            raise ValueError("initial memory requires a NEW hypothesis relationship")
        began_at = evidence.as_of
        previous_hypothesis = None
        previous_confidence = None
        previous_evidence_id = None
        history: tuple[str, ...] = ()
        confirmation_count = 0
    else:
        if previous.agent_name != evidence.agent_name:
            raise ValueError("evidence agent does not match previous memory")
        if evidence.as_of < previous.updated_at:
            raise ValueError("agent evidence cannot move memory backwards")
        starts_new = evidence.relationship is HypothesisRelationship.NEW
        reverses = evidence.relationship is HypothesisRelationship.REVERSED
        if starts_new:
            if previous.hypothesis_status not in {
                HypothesisStatus.INVALIDATED,
                HypothesisStatus.EXPIRED,
                HypothesisStatus.ABSTAINED,
            }:
                raise ValueError("new hypothesis requires terminal previous lifecycle")
            if evidence.hypothesis_id == previous.hypothesis_id:
                raise ValueError("new hypothesis must use a distinct hypothesis_id")
        elif not reverses:
            if evidence.previous_hypothesis_id != previous.hypothesis_id:
                raise ValueError("evidence does not reference previous memory hypothesis")
            if evidence.hypothesis_status not in _ALLOWED_TRANSITIONS[previous.hypothesis_status]:
                raise ValueError("invalid hypothesis lifecycle transition")
        elif evidence.previous_hypothesis_id != previous.hypothesis_id:
            raise ValueError("reversal does not reference previous memory hypothesis")
        began_at = (
            evidence.as_of
            if starts_new or reverses
            else previous.began_at
        )
        previous_hypothesis = previous.current_hypothesis
        previous_confidence = previous.current_confidence
        previous_evidence_id = previous.latest_evidence_id
        history = previous.supporting_evidence_history
        confirmation_count = previous.confirmation_count

    if evidence.hypothesis_status is HypothesisStatus.CONFIRMED:
        confirmation_count += 1
    elif evidence.hypothesis_status not in {
        HypothesisStatus.ACTIVE,
        HypothesisStatus.WEAKENING,
    }:
        confirmation_count = 0

    return AgentMemory(
        agent_name=evidence.agent_name,
        agent_version=evidence.agent_version,
        hypothesis_id=evidence.hypothesis_id,
        current_hypothesis=evidence.hypothesis,
        previous_hypothesis=previous_hypothesis,
        current_confidence=evidence.confidence,
        previous_confidence=previous_confidence,
        running_uncertainty=evidence.uncertainty,
        hypothesis_status=evidence.hypothesis_status,
        relationship=evidence.relationship,
        began_at=began_at,
        updated_at=evidence.as_of,
        supporting_evidence_history=history + (evidence.evidence_id,),
        invalidation=evidence.invalidation,
        recent_tool_requests=evidence.tool_requests,
        previous_evidence_id=previous_evidence_id,
        latest_evidence_id=evidence.evidence_id,
        confirmation_count=confirmation_count,
        setup_id=evidence.setup_id,
        thesis_id=evidence.thesis_id,
    )
