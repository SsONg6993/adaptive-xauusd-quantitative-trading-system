"""Immutable contracts for one bounded, evidence-bound specialist interaction."""

from __future__ import annotations

from collections import Counter
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.agents import DirectionalBias
from axq.runtime.kernel import AGENT_ORDER
from axq.runtime.state import UTCDateTime
from axq.schemas import Signal
from axq.versioning import canonical_hash


class InteractionConflictType(StrEnum):
    DIRECTIONAL_DISAGREEMENT = "DIRECTIONAL_DISAGREEMENT"


class InteractionTurnType(StrEnum):
    MASTER_CHALLENGE = "MASTER_CHALLENGE"
    SPECIALIST_REBUTTAL = "SPECIALIST_REBUTTAL"


class InteractionResolutionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    UNAVAILABLE = "UNAVAILABLE"
    MALFORMED = "MALFORMED"
    TIMED_OUT = "TIMED_OUT"


class InteractionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


def _bind_id(value: BaseModel, field: str, prefix: str) -> str:
    identity = value.model_dump(mode="json", exclude={field, "available_at"})
    return f"{prefix}-{canonical_hash(identity)[:20]}"


class MasterConflictAssessment(InteractionModel):
    assessment_id: str = ""
    event_id: str = Field(min_length=1)
    scan_id: str = Field(min_length=1)
    evidence_bundle_id: str = Field(min_length=1)
    master_proposal_id: str = Field(min_length=1)
    fusion_policy_id: str = Field(min_length=1)
    fusion_policy_version: str = Field(min_length=1)
    initial_evidence_ids: tuple[str, ...]
    conflict_type: InteractionConflictType = InteractionConflictType.DIRECTIONAL_DISAGREEMENT
    bullish_evidence_ids: tuple[str, ...] = ()
    bearish_evidence_ids: tuple[str, ...] = ()
    measured_disagreement: float = Field(ge=0.0, le=1.0)
    disagreement_threshold: float = Field(ge=0.0, le=1.0)
    interaction_required: bool
    selected_specialists: tuple[str, ...] = Field(default=(), max_length=3)
    as_of: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind(self) -> MasterConflictAssessment:
        if len(set(self.initial_evidence_ids)) != len(self.initial_evidence_ids):
            raise ValueError("initial evidence IDs must be unique")
        if any(name not in AGENT_ORDER for name in self.selected_specialists):
            raise ValueError("selected specialists must be canonical")
        if (
            tuple(sorted(self.selected_specialists, key=AGENT_ORDER.index))
            != self.selected_specialists
        ):
            raise ValueError("selected specialists must use canonical order")
        expected_required = bool(self.bullish_evidence_ids and self.bearish_evidence_ids) and (
            self.measured_disagreement > self.disagreement_threshold
        )
        if self.interaction_required != expected_required:
            raise ValueError("interaction trigger must exactly match directional disagreement")
        if self.interaction_required != bool(self.selected_specialists):
            raise ValueError("selected specialists must exist exactly when interaction is required")
        expected = _bind_id(self, "assessment_id", "mca")
        if self.assessment_id and self.assessment_id != expected:
            raise ValueError("assessment_id does not match content")
        object.__setattr__(self, "assessment_id", expected)
        return self


class SpecialistInteractionRound(InteractionModel):
    round_id: str = ""
    assessment_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    scan_id: str = Field(min_length=1)
    evidence_bundle_id: str = Field(min_length=1)
    initial_evidence_ids: tuple[str, ...]
    participating_specialists: tuple[str, ...] = Field(min_length=2, max_length=3)
    maximum_rebuttals: Literal[3] = 3
    interaction_policy_version: Literal["EVIDENCE_BOUND_ONE_ROUND_V1"] = (
        "EVIDENCE_BOUND_ONE_ROUND_V1"
    )
    as_of: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind(self) -> SpecialistInteractionRound:
        if tuple(sorted(self.participating_specialists, key=AGENT_ORDER.index)) != (
            self.participating_specialists
        ):
            raise ValueError("participants must use canonical order")
        expected = _bind_id(self, "round_id", "sir")
        if self.round_id and self.round_id != expected:
            raise ValueError("round_id does not match content")
        object.__setattr__(self, "round_id", expected)
        return self


class SpecialistInteractionTurn(InteractionModel):
    turn_id: str = ""
    round_id: str = Field(min_length=1)
    turn_index: int = Field(ge=0, le=5)
    speaker: str = Field(min_length=1)
    recipient: str = Field(min_length=1)
    turn_type: InteractionTurnType
    original_evidence_id: str = Field(min_length=1)
    conflicting_evidence_ids: tuple[str, ...] = ()
    stance: DirectionalBias | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: str = Field(min_length=1, max_length=420)
    cited_evidence_ids: tuple[str, ...] = Field(min_length=1)
    predecessor_turn_id: str | None = None
    reasoning_mode: Literal["DETERMINISTIC_EVIDENCE_BOUND"] = (
        "DETERMINISTIC_EVIDENCE_BOUND"
    )
    reasoning_version: Literal["1.0.0"] = "1.0.0"
    as_of: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind(self) -> SpecialistInteractionTurn:
        if self.turn_type is InteractionTurnType.MASTER_CHALLENGE:
            if self.speaker != "master" or self.recipient not in AGENT_ORDER:
                raise ValueError("Master challenges must target one specialist")
            if self.stance is not None or self.confidence is not None:
                raise ValueError("Master challenges cannot carry a stance or confidence")
            if self.predecessor_turn_id is not None:
                raise ValueError("Master challenge starts its participant exchange")
        else:
            if self.speaker not in AGENT_ORDER or self.recipient != "master":
                raise ValueError("specialist rebuttals must return directly to Master")
            if self.stance not in {DirectionalBias.BULLISH, DirectionalBias.BEARISH}:
                raise ValueError("rebuttal must preserve a directional stance")
            if self.confidence is None or self.predecessor_turn_id is None:
                raise ValueError("rebuttal requires confidence and its challenge predecessor")
            if self.cited_evidence_ids != (self.original_evidence_id,):
                raise ValueError("rebuttal may cite only its original AgentEvidence")
        expected = _bind_id(self, "turn_id", "sit")
        if self.turn_id and self.turn_id != expected:
            raise ValueError("turn_id does not match content")
        object.__setattr__(self, "turn_id", expected)
        return self


class SpecialistInteractionResolution(InteractionModel):
    resolution_id: str = ""
    round_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    master_proposal_id: str = Field(min_length=1)
    ordered_turn_ids: tuple[str, ...] = ()
    status: InteractionResolutionStatus
    failure_reason: str | None = Field(default=None, max_length=300)
    unresolved_conflict: Literal[True] = True
    as_of: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind(self) -> SpecialistInteractionResolution:
        failed = self.status is not InteractionResolutionStatus.COMPLETED
        if failed != (self.failure_reason is not None):
            raise ValueError("failed interaction resolution requires exactly one safe reason")
        expected = _bind_id(self, "resolution_id", "sires")
        if self.resolution_id and self.resolution_id != expected:
            raise ValueError("resolution_id does not match content")
        object.__setattr__(self, "resolution_id", expected)
        return self


class SpecialistInteractionImpact(InteractionModel):
    """Auditable before/after measurement; it does not authorize decision mutation."""

    impact_id: str = ""
    discussion_id: str = Field(min_length=1)
    resolution_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    master_before_id: str = Field(min_length=1)
    master_after_id: str = Field(min_length=1)
    confidence_before: float = Field(ge=0.0, le=1.0)
    confidence_after: float = Field(ge=0.0, le=1.0)
    confidence_delta: float = Field(ge=-1.0, le=1.0)
    stance_before: Signal
    stance_after: Signal
    stance_changed: bool
    final_reason: str = Field(min_length=1, max_length=300)
    as_of: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind(self) -> SpecialistInteractionImpact:
        expected_delta = self.confidence_after - self.confidence_before
        if abs(self.confidence_delta - expected_delta) > 1e-12:
            raise ValueError("interaction confidence delta does not match before/after values")
        if self.stance_changed != (self.stance_before is not self.stance_after):
            raise ValueError("interaction stance-change flag does not match before/after values")
        expected = _bind_id(self, "impact_id", "sii")
        if self.impact_id and self.impact_id != expected:
            raise ValueError("impact_id does not match content")
        object.__setattr__(self, "impact_id", expected)
        return self


class SpecialistInteractionSession(InteractionModel):
    assessment: MasterConflictAssessment
    round: SpecialistInteractionRound | None = None
    turns: tuple[SpecialistInteractionTurn, ...] = ()
    resolution: SpecialistInteractionResolution | None = None

    @model_validator(mode="after")
    def validate_bounded_linear_round(self) -> SpecialistInteractionSession:
        if self.round is None:
            if self.turns or self.resolution is not None or self.assessment.interaction_required:
                raise ValueError("skipped interaction cannot contain a round or turns")
            return self
        if not self.assessment.interaction_required:
            raise ValueError("interaction round requires a material conflict assessment")
        if self.round.assessment_id != self.assessment.assessment_id:
            raise ValueError("interaction round does not match its assessment")
        challenges = Counter(
            item.recipient
            for item in self.turns
            if item.turn_type is InteractionTurnType.MASTER_CHALLENGE
        )
        rebuttals = Counter(
            item.speaker
            for item in self.turns
            if item.turn_type is InteractionTurnType.SPECIALIST_REBUTTAL
        )
        if any(count > 1 for count in (*challenges.values(), *rebuttals.values())):
            raise ValueError("each participant permits one challenge and one rebuttal only")
        if set(challenges) - set(self.round.participating_specialists) or set(rebuttals) - set(
            self.round.participating_specialists
        ):
            raise ValueError("turn speaker or recipient is not a round participant")
        if tuple(item.turn_index for item in self.turns) != tuple(range(len(self.turns))):
            raise ValueError("interaction turns must form one chronological sequence")
        if self.resolution is None or self.resolution.round_id != self.round.round_id:
            raise ValueError("interaction round requires its exact terminal resolution")
        if self.resolution.ordered_turn_ids != tuple(item.turn_id for item in self.turns):
            raise ValueError("interaction resolution must preserve exact turn order")
        return self
