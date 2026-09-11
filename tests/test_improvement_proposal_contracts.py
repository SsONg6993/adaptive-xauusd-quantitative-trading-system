from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.reflection import FindingCategory, PatternSignalClass, PatternType, SampleGuardStatus
from axq.reflection.proposal_contracts import (
    ImprovementProposal,
    ImprovementProposalPolicy,
    ProposalEvidenceGuard,
    ProposalGuardKind,
    ProposalStatus,
    ProposalStatusTransition,
    ProposalTargetComponent,
)
from axq.reflection.weekly_contracts import TransitionActionKind

START = datetime(2026, 8, 10, tzinfo=UTC)


def _guard() -> ProposalEvidenceGuard:
    return ProposalEvidenceGuard(
        guard_kind=ProposalGuardKind.PATTERN_RECURRENCE,
        observed_samples=2,
        required_samples=2,
        status=SampleGuardStatus.PASSED,
        supporting_pattern_ids=("pattern-2", "pattern-1"),
    )


def _proposal(**changes: object) -> ImprovementProposal:
    values: dict[str, object] = {
        "policy_id": ImprovementProposalPolicy().policy_id,
        "pattern_key": "pattern-key-1",
        "target_component": ProposalTargetComponent.MASTER_FUSION,
        "category": FindingCategory.DIRECTION_OUTCOME,
        "pattern_type": PatternType.FAILURE,
        "signal_class": PatternSignalClass.ADVERSE,
        "reason_code": "NEGATIVE_AVERAGE_R",
        "scope": "direction",
        "scope_value": "BUY",
        "rationale": "Repeated guarded adverse direction outcome requires evaluation.",
        "proposed_change": "Evaluate an offline evidence-fusion adjustment candidate.",
        "expected_benefit": "Reduce repeated adverse direction outcomes if validated.",
        "risks": ("Regime dependence", "Overfitting"),
        "validation_plan": (
            "Run a separately approved causal replay comparison.",
            "Preserve protected Final OOS and require explicit promotion.",
        ),
        "source_week_starts": (START, START + timedelta(days=7)),
        "available_at": START + timedelta(days=14),
        "supporting_weekly_reflection_ids": ("weekly-2", "weekly-1"),
        "supporting_pattern_ids": ("pattern-2", "pattern-1"),
        "supporting_daily_reflection_ids": ("daily-2", "daily-1"),
        "supporting_finding_ids": ("finding-2", "finding-1"),
        "supporting_experience_ids": ("experience-2", "experience-1"),
        "supporting_weekly_guard_ids": ("guard-2", "guard-1"),
        "evidence_guards": (_guard(),),
    }
    values.update(changes)
    return ImprovementProposal(**values)


def test_proposal_identity_is_order_invariant_and_key_is_stable_across_evidence() -> None:
    first = _proposal()
    reordered = _proposal(
        supporting_pattern_ids=("pattern-1", "pattern-2", "pattern-1"),
        risks=("Overfitting", "Regime dependence"),
    )
    revised = _proposal(
        supporting_pattern_ids=("pattern-1", "pattern-2", "pattern-3"),
        supporting_weekly_reflection_ids=("weekly-1", "weekly-2", "weekly-3"),
        source_week_starts=(START, START + timedelta(days=7), START + timedelta(days=14)),
        available_at=START + timedelta(days=21),
    )

    assert first == reordered
    assert first.proposal_key == revised.proposal_key
    assert first.proposal_id != revised.proposal_id
    assert first.status is ProposalStatus.OBSERVATION


def test_proposal_requires_passed_guards_exact_sources_and_aware_utc() -> None:
    insufficient = ProposalEvidenceGuard(
        guard_kind=ProposalGuardKind.PATTERN_RECURRENCE,
        observed_samples=1,
        required_samples=2,
        status=SampleGuardStatus.INSUFFICIENT,
        supporting_pattern_ids=("pattern-1",),
    )
    with pytest.raises(ValidationError, match="proposal evidence guards must pass"):
        _proposal(evidence_guards=(insufficient,))
    with pytest.raises(ValidationError, match="at least 2"):
        _proposal(
            supporting_pattern_ids=("pattern-1",),
            supporting_weekly_reflection_ids=("weekly-1",),
            source_week_starts=(START,),
        )
    with pytest.raises(ValidationError, match="timezone-aware"):
        _proposal(available_at=datetime(2026, 8, 24))


def test_models_are_strict_frozen_and_content_ids_reject_tampering() -> None:
    proposal = _proposal()
    with pytest.raises(ValidationError):
        proposal.rationale = "changed"
    with pytest.raises(ValidationError, match="proposal_id does not match"):
        _proposal(proposal_id="improvement-proposal-wrong")
    with pytest.raises(ValidationError):
        ImprovementProposalPolicy(extra_field=True)


def test_proposal_lifecycle_accepts_only_explicit_forward_edges() -> None:
    proposal = _proposal()
    first = ProposalStatusTransition(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        from_status=ProposalStatus.OBSERVATION,
        to_status=ProposalStatus.HYPOTHESIS,
        effective_at=proposal.available_at,
        action_kind=TransitionActionKind.OPERATOR,
        actor_id="operator-1",
        action_id="review-1",
        reason_code="EXPLICIT_REVIEW",
    )
    second = ProposalStatusTransition(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        from_status=ProposalStatus.HYPOTHESIS,
        to_status=ProposalStatus.CANDIDATE,
        effective_at=proposal.available_at + timedelta(seconds=1),
        action_kind=TransitionActionKind.EVALUATION,
        actor_id="evaluation-runner",
        action_id="evaluation-1",
        reason_code="EVALUATION_APPROVED",
        previous_transition_id=first.transition_id,
    )

    assert first.transition_id.startswith("proposal-transition-")
    assert second.previous_transition_id == first.transition_id
    with pytest.raises(ValidationError, match="proposal status transition is not allowed"):
        ProposalStatusTransition(
            **first.model_dump(exclude={"transition_id", "to_status"}),
            to_status=ProposalStatus.VALIDATED,
        )
