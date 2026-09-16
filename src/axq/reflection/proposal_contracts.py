"""Immutable contracts for advisory improvement proposals."""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from axq.reflection.contracts import FindingCategory, ReflectionModel, SampleGuardStatus
from axq.reflection.weekly_contracts import (
    PatternSignalClass,
    PatternType,
    TransitionActionKind,
)
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class ProposalTargetComponent(StrEnum):
    MASTER_FUSION = "MASTER_FUSION"
    DISCIPLINE_GUARD = "DISCIPLINE_GUARD"
    RISK_BOUNDARY = "RISK_BOUNDARY"
    POSITION_MANAGEMENT = "POSITION_MANAGEMENT"
    SPECIALIST_AGENT = "SPECIALIST_AGENT"
    RUNTIME_ORCHESTRATION = "RUNTIME_ORCHESTRATION"


class ProposalStatus(StrEnum):
    OBSERVATION = "OBSERVATION"
    HYPOTHESIS = "HYPOTHESIS"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"


class ProposalGuardKind(StrEnum):
    PATTERN_RECURRENCE = "PATTERN_RECURRENCE"
    WEEKLY_GUARDS = "WEEKLY_GUARDS"
    EXACT_PROVENANCE = "EXACT_PROVENANCE"


class ImprovementProposalPolicy(ReflectionModel):
    policy_id: str = ""
    minimum_complete_week_observations: int = Field(default=2, ge=2)
    template_version: Literal["ADVISORY_V1"] = "ADVISORY_V1"

    @model_validator(mode="after")
    def bind_identity(self) -> ImprovementProposalPolicy:
        identity = self.model_dump(mode="json", exclude={"policy_id"})
        expected = f"improvement-proposal-policy-{canonical_hash(identity)[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match improvement proposal policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class ProposalEvidenceGuard(ReflectionModel):
    guard_id: str = ""
    guard_kind: ProposalGuardKind
    observed_samples: int = Field(ge=0)
    required_samples: int = Field(ge=1)
    status: SampleGuardStatus
    supporting_weekly_reflection_ids: tuple[str, ...] = ()
    supporting_pattern_ids: tuple[str, ...] = ()
    supporting_daily_reflection_ids: tuple[str, ...] = ()
    supporting_finding_ids: tuple[str, ...] = ()
    supporting_experience_ids: tuple[str, ...] = ()
    supporting_weekly_guard_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> ProposalEvidenceGuard:
        for field_name in (
            "supporting_weekly_reflection_ids",
            "supporting_pattern_ids",
            "supporting_daily_reflection_ids",
            "supporting_finding_ids",
            "supporting_experience_ids",
            "supporting_weekly_guard_ids",
        ):
            object.__setattr__(self, field_name, tuple(sorted(set(getattr(self, field_name)))))
        if (
            self.status is SampleGuardStatus.PASSED
            and self.observed_samples < self.required_samples
        ):
            raise ValueError("passed proposal guard does not meet required samples")
        if (
            self.status is SampleGuardStatus.INSUFFICIENT
            and self.observed_samples >= self.required_samples
        ):
            raise ValueError("insufficient proposal guard already meets required samples")
        if self.status is SampleGuardStatus.UNAVAILABLE and self.observed_samples != 0:
            raise ValueError("unavailable proposal guard must have zero observed samples")
        identity = self.model_dump(mode="json", exclude={"guard_id"})
        expected = f"proposal-evidence-guard-{canonical_hash(identity)[:20]}"
        if self.guard_id and self.guard_id != expected:
            raise ValueError("guard_id does not match proposal evidence guard content")
        object.__setattr__(self, "guard_id", expected)
        return self


class ImprovementProposal(ReflectionModel):
    proposal_id: str = ""
    proposal_key: str = ""
    policy_id: str = Field(min_length=1)
    pattern_key: str = Field(min_length=1)
    target_component: ProposalTargetComponent
    category: FindingCategory
    pattern_type: PatternType
    signal_class: PatternSignalClass
    reason_code: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    scope_value: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    proposed_change: str = Field(min_length=1)
    expected_benefit: str = Field(min_length=1)
    risks: tuple[str, ...] = Field(min_length=1)
    validation_plan: tuple[str, ...] = Field(min_length=1)
    source_week_starts: tuple[UTCDateTime, ...] = Field(min_length=2)
    available_at: UTCDateTime
    supporting_weekly_reflection_ids: tuple[str, ...] = Field(min_length=2)
    supporting_pattern_ids: tuple[str, ...] = Field(min_length=2)
    supporting_daily_reflection_ids: tuple[str, ...] = Field(min_length=1)
    supporting_finding_ids: tuple[str, ...] = Field(min_length=1)
    supporting_experience_ids: tuple[str, ...] = Field(min_length=1)
    supporting_weekly_guard_ids: tuple[str, ...] = Field(min_length=1)
    evidence_guards: tuple[ProposalEvidenceGuard, ...] = Field(min_length=1)
    status: Literal[ProposalStatus.OBSERVATION] = ProposalStatus.OBSERVATION
    supersedes_proposal_id: str | None = None

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> ImprovementProposal:
        for field_name in (
            "risks",
            "validation_plan",
            "source_week_starts",
            "supporting_weekly_reflection_ids",
            "supporting_pattern_ids",
            "supporting_daily_reflection_ids",
            "supporting_finding_ids",
            "supporting_experience_ids",
            "supporting_weekly_guard_ids",
        ):
            normalized = tuple(sorted(set(getattr(self, field_name))))
            object.__setattr__(self, field_name, normalized)
        guards = tuple(sorted(set(self.evidence_guards), key=lambda item: item.guard_id))
        object.__setattr__(self, "evidence_guards", guards)
        if len(self.source_week_starts) < 2 or len(self.supporting_pattern_ids) < 2:
            raise ValueError("proposal requires at least two weekly pattern observations")
        if len(self.supporting_weekly_reflection_ids) < 2:
            raise ValueError("proposal requires at least two weekly pattern observations")
        if any(guard.status is not SampleGuardStatus.PASSED for guard in guards):
            raise ValueError("proposal evidence guards must pass")
        if self.available_at < max(self.source_week_starts) + timedelta(days=7):
            raise ValueError("proposal cannot be available before its latest complete source week")
        key_identity = {
            "policy_id": self.policy_id,
            "target_component": self.target_component.value,
            "pattern_key": self.pattern_key,
        }
        expected_key = f"improvement-proposal-key-{canonical_hash(key_identity)[:20]}"
        if self.proposal_key and self.proposal_key != expected_key:
            raise ValueError("proposal_key does not match stable advisory subject")
        object.__setattr__(self, "proposal_key", expected_key)
        identity = self.model_dump(mode="json", exclude={"proposal_id"})
        expected_id = f"improvement-proposal-{canonical_hash(identity)[:20]}"
        if self.proposal_id and self.proposal_id != expected_id:
            raise ValueError("proposal_id does not match proposal content")
        object.__setattr__(self, "proposal_id", expected_id)
        return self


_ALLOWED_TRANSITIONS: dict[ProposalStatus, frozenset[ProposalStatus]] = {
    ProposalStatus.OBSERVATION: frozenset(
        {ProposalStatus.HYPOTHESIS, ProposalStatus.REJECTED, ProposalStatus.DEPRECATED}
    ),
    ProposalStatus.HYPOTHESIS: frozenset(
        {ProposalStatus.CANDIDATE, ProposalStatus.REJECTED, ProposalStatus.DEPRECATED}
    ),
    ProposalStatus.CANDIDATE: frozenset(
        {ProposalStatus.VALIDATED, ProposalStatus.REJECTED, ProposalStatus.DEPRECATED}
    ),
    ProposalStatus.VALIDATED: frozenset({ProposalStatus.DEPRECATED}),
    ProposalStatus.REJECTED: frozenset(),
    ProposalStatus.DEPRECATED: frozenset(),
}


class ProposalStatusTransition(ReflectionModel):
    transition_id: str = ""
    proposal_id: str = Field(min_length=1)
    proposal_key: str = Field(min_length=1)
    from_status: ProposalStatus
    to_status: ProposalStatus
    effective_at: UTCDateTime
    action_kind: TransitionActionKind
    actor_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    supporting_evaluation_ids: tuple[str, ...] = ()
    previous_transition_id: str | None = None

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> ProposalStatusTransition:
        if self.to_status not in _ALLOWED_TRANSITIONS[self.from_status]:
            raise ValueError("proposal status transition is not allowed")
        object.__setattr__(
            self,
            "supporting_evaluation_ids",
            tuple(sorted(set(self.supporting_evaluation_ids))),
        )
        identity = self.model_dump(mode="json", exclude={"transition_id"})
        expected = f"proposal-transition-{canonical_hash(identity)[:20]}"
        if self.transition_id and self.transition_id != expected:
            raise ValueError("transition_id does not match proposal transition content")
        object.__setattr__(self, "transition_id", expected)
        return self
