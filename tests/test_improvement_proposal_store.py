from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

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
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.weekly_contracts import TransitionActionKind

START = datetime(2026, 8, 10, tzinfo=UTC)


def _proposal(
    policy: ImprovementProposalPolicy,
    *,
    third_source: bool = False,
    supersedes: str | None = None,
) -> ImprovementProposal:
    pattern_ids = ("pattern-1", "pattern-2", "pattern-3") if third_source else (
        "pattern-1",
        "pattern-2",
    )
    weekly_ids = ("weekly-1", "weekly-2", "weekly-3") if third_source else (
        "weekly-1",
        "weekly-2",
    )
    weeks = (START, START + timedelta(days=7), START + timedelta(days=14)) if third_source else (
        START,
        START + timedelta(days=7),
    )
    guard = ProposalEvidenceGuard(
        guard_kind=ProposalGuardKind.PATTERN_RECURRENCE,
        observed_samples=len(pattern_ids),
        required_samples=2,
        status=SampleGuardStatus.PASSED,
        supporting_weekly_reflection_ids=weekly_ids,
        supporting_pattern_ids=pattern_ids,
    )
    return ImprovementProposal(
        policy_id=policy.policy_id,
        pattern_key="pattern-key-1",
        target_component=ProposalTargetComponent.MASTER_FUSION,
        category=FindingCategory.DIRECTION_OUTCOME,
        pattern_type=PatternType.FAILURE,
        signal_class=PatternSignalClass.ADVERSE,
        reason_code="NEGATIVE_AVERAGE_R",
        scope="direction",
        scope_value="BUY",
        rationale="Repeated guarded adverse evidence requires evaluation.",
        proposed_change="Evaluate an offline evidence-fusion candidate.",
        expected_benefit="Test whether adverse outcomes can be reduced.",
        risks=("Overfitting",),
        validation_plan=("Run separately approved causal validation.",),
        source_week_starts=weeks,
        available_at=max(weeks) + timedelta(days=7),
        supporting_weekly_reflection_ids=weekly_ids,
        supporting_pattern_ids=pattern_ids,
        supporting_daily_reflection_ids=("daily-1", "daily-2"),
        supporting_finding_ids=("finding-1", "finding-2"),
        supporting_experience_ids=("experience-1", "experience-2"),
        supporting_weekly_guard_ids=("weekly-guard-1", "weekly-guard-2"),
        evidence_guards=(guard,),
        supersedes_proposal_id=supersedes,
    )


def _transition(
    proposal: ImprovementProposal,
    source: ProposalStatus,
    target: ProposalStatus,
    index: int,
    previous: str | None = None,
) -> ProposalStatusTransition:
    return ProposalStatusTransition(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        from_status=source,
        to_status=target,
        effective_at=proposal.available_at + timedelta(minutes=index),
        action_kind=TransitionActionKind.OPERATOR,
        actor_id="operator-1",
        action_id=f"review-{index}",
        reason_code="EXPLICIT_REVIEW",
        previous_transition_id=previous,
    )


def test_store_is_idempotent_and_indexes_exact_sources(tmp_path) -> None:
    store = SQLiteImprovementProposalStore(tmp_path / "proposals.sqlite3")
    policy = ImprovementProposalPolicy()
    proposal = _proposal(policy)

    assert store.append_policy(policy) is True
    assert store.append_policy(policy) is False
    assert store.append(proposal) is True
    assert store.append(proposal) is False
    assert store.proposals() == (proposal,)
    assert store.latest(proposal.proposal_key, policy.policy_id) == proposal
    assert store.by_source_id("pattern-1", "WEEKLY_PATTERN") == (proposal,)


def test_changed_evidence_requires_explicit_latest_supersession(tmp_path) -> None:
    store = SQLiteImprovementProposalStore(tmp_path / "proposals.sqlite3")
    policy = ImprovementProposalPolicy()
    original = _proposal(policy)
    store.append_policy(policy)
    store.append(original)

    with pytest.raises(ValueError, match="supersede latest"):
        store.append(_proposal(policy, third_source=True))
    revised = _proposal(policy, third_source=True, supersedes=original.proposal_id)
    assert revised.proposal_key == original.proposal_key
    assert revised.proposal_id != original.proposal_id
    assert store.append(revised) is True
    assert store.latest(revised.proposal_key, policy.policy_id) == revised
    assert store.current_status(revised.proposal_id) is ProposalStatus.OBSERVATION


def test_lifecycle_replays_explicit_linear_chain_without_deployment_state(tmp_path) -> None:
    store = SQLiteImprovementProposalStore(tmp_path / "proposals.sqlite3")
    policy = ImprovementProposalPolicy()
    proposal = _proposal(policy)
    store.append_policy(policy)
    store.append(proposal)
    history: list[ProposalStatusTransition] = []
    previous: str | None = None
    for index, (source, target) in enumerate(
        (
            (ProposalStatus.OBSERVATION, ProposalStatus.HYPOTHESIS),
            (ProposalStatus.HYPOTHESIS, ProposalStatus.CANDIDATE),
            (ProposalStatus.CANDIDATE, ProposalStatus.VALIDATED),
            (ProposalStatus.VALIDATED, ProposalStatus.DEPRECATED),
        ),
        start=1,
    ):
        transition = _transition(proposal, source, target, index, previous)
        assert store.append_transition(transition) is True
        assert store.append_transition(transition) is False
        history.append(transition)
        previous = transition.transition_id

    assert store.transition_history(proposal.proposal_id) == tuple(history)
    assert store.current_status(proposal.proposal_id) is ProposalStatus.DEPRECATED


def test_lifecycle_rejects_stale_status_wrong_predecessor_and_unknown_proposal(tmp_path) -> None:
    store = SQLiteImprovementProposalStore(tmp_path / "proposals.sqlite3")
    policy = ImprovementProposalPolicy()
    proposal = _proposal(policy)
    store.append_policy(policy)
    store.append(proposal)
    first = _transition(
        proposal, ProposalStatus.OBSERVATION, ProposalStatus.HYPOTHESIS, 1
    )
    store.append_transition(first)

    with pytest.raises(ValueError, match="current status"):
        store.append_transition(
            _transition(
                proposal,
                ProposalStatus.OBSERVATION,
                ProposalStatus.REJECTED,
                2,
                first.transition_id,
            )
        )
    with pytest.raises(ValueError, match="previous transition"):
        store.append_transition(
            _transition(proposal, ProposalStatus.HYPOTHESIS, ProposalStatus.CANDIDATE, 2)
        )
    unknown = first.model_copy(update={"proposal_id": "improvement-proposal-unknown"})
    with pytest.raises(ValueError, match="proposal is not persisted"):
        store.append_transition(unknown)


def test_all_proposal_tables_are_append_only(tmp_path) -> None:
    path = tmp_path / "proposals.sqlite3"
    store = SQLiteImprovementProposalStore(path)
    policy = ImprovementProposalPolicy()
    proposal = _proposal(policy)
    store.append_policy(policy)
    store.append(proposal)

    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE improvement_proposals SET target_component = 'RISK_BOUNDARY' "
                "WHERE proposal_id = ?",
                (proposal.proposal_id,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "DELETE FROM proposal_evidence_guards WHERE proposal_id = ?",
                (proposal.proposal_id,),
            )
