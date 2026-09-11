from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest
from proposal_transition_authorization_test_support import persisted_authorization_fixture

from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.paired_evaluation_review_contracts import (
    PairedEvaluationReview,
    PairedEvaluationReviewDecision,
)
from axq.reflection.paired_evaluation_review_store import SQLitePairedEvaluationReviewStore
from axq.reflection.proposal_contracts import ProposalStatus, ProposalStatusTransition
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.proposal_transition_authorization_contracts import (
    ProposalTransitionAuthorization,
)
from axq.reflection.proposal_transition_authorization_store import (
    SQLiteProposalTransitionAuthorizationStore,
)
from axq.reflection.weekly_contracts import TransitionActionKind


def _successor(
    authorization: ProposalTransitionAuthorization,
    **overrides: object,
) -> ProposalTransitionAuthorization:
    values = authorization.model_dump(
        exclude={"authorization_id", "action_id", "authorized_at", "previous_authorization_id"}
    )
    values.update(
        {
            "action_id": "proposal-authorization-action-002",
            "authorized_at": authorization.authorized_at + timedelta(minutes=1),
            "previous_authorization_id": authorization.authorization_id,
        }
    )
    values.update(overrides)
    return ProposalTransitionAuthorization(**values)


def test_store_enforces_exact_eligibility_chain_idempotency_and_no_mutation(tmp_path) -> None:
    store_path, proposal, result, review, first = persisted_authorization_fixture(tmp_path)
    store = SQLiteProposalTransitionAuthorizationStore(store_path)
    proposal_store = SQLiteImprovementProposalStore(store_path)
    review_store = SQLitePairedEvaluationReviewStore(store_path)
    status_before = proposal_store.current_status(proposal.proposal_id)
    result_before = canonical_record_bytes(result)
    review_before = canonical_record_bytes(review)

    assert store.append(first) is True
    assert store.append(first) is False
    second = _successor(first)
    assert store.append(second) is True
    assert store.history(proposal.proposal_id) == (first, second)
    assert store.current(proposal.proposal_id) == second

    stale = _successor(
        first,
        action_id="proposal-authorization-action-stale",
        authorized_at=second.authorized_at + timedelta(minutes=1),
    )
    with pytest.raises(ValueError, match="current terminal authorization"):
        store.append(stale)

    assert proposal_store.current_status(proposal.proposal_id) is status_before
    persisted_result = store.paired_result(result.result_id)
    persisted_review = review_store.review(review.review_id)
    assert persisted_result is not None and persisted_review is not None
    assert canonical_record_bytes(persisted_result) == result_before
    assert canonical_record_bytes(persisted_review) == review_before


def test_store_requires_current_terminal_accept_review(tmp_path) -> None:
    store_path, _, result, review, authorization = persisted_authorization_fixture(tmp_path)
    review_store = SQLitePairedEvaluationReviewStore(store_path)
    defer = PairedEvaluationReview(
        **review.model_dump(
            exclude={
                "review_id",
                "decision",
                "action_id",
                "reason_code",
                "effective_at",
                "previous_review_id",
            }
        ),
        decision=PairedEvaluationReviewDecision.DEFER,
        action_id="paired-review-defer-after-accept",
        reason_code="MORE_EVIDENCE_REQUIRED",
        effective_at=authorization.authorized_at,
        previous_review_id=review.review_id,
    )
    review_store.append(defer)
    store = SQLiteProposalTransitionAuthorizationStore(store_path)

    with pytest.raises(ValueError, match="current terminal review"):
        store.append(authorization)
    defer_authorization = ProposalTransitionAuthorization(
        **authorization.model_dump(
            exclude={"authorization_id", "accepted_review_id", "authorized_at"}
        ),
        accepted_review_id=defer.review_id,
        authorized_at=defer.effective_at + timedelta(minutes=1),
    )
    with pytest.raises(ValueError, match="ACCEPT_EVIDENCE"):
        store.append(defer_authorization)
    assert store.paired_result(result.result_id) == result


def test_store_rejects_mismatched_linkage_and_predating_authorization(tmp_path) -> None:
    store_path, _, _, review, authorization = persisted_authorization_fixture(tmp_path)
    store = SQLiteProposalTransitionAuthorizationStore(store_path)
    mismatch = ProposalTransitionAuthorization(
        **authorization.model_dump(exclude={"authorization_id", "candidate_id"}),
        candidate_id="wrong-candidate",
    )
    with pytest.raises(ValueError, match="linkage"):
        store.append(mismatch)
    early = ProposalTransitionAuthorization(
        **authorization.model_dump(exclude={"authorization_id", "authorized_at"}),
        authorized_at=review.effective_at - timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="predate"):
        store.append(early)


def test_authorization_table_is_append_only(tmp_path) -> None:
    store_path, _, _, _, authorization = persisted_authorization_fixture(tmp_path)
    store = SQLiteProposalTransitionAuthorizationStore(store_path)
    store.append(authorization)
    with (
        pytest.raises(sqlite3.IntegrityError, match="append-only"),
        sqlite3.connect(store_path) as connection,
    ):
        connection.execute("UPDATE proposal_transition_authorizations SET reason_code = 'changed'")


def test_store_requires_proposal_to_still_be_candidate(tmp_path) -> None:
    store_path, proposal, _, _, authorization = persisted_authorization_fixture(tmp_path)
    proposal_store = SQLiteImprovementProposalStore(store_path)
    history = proposal_store.transition_history(proposal.proposal_id)
    proposal_store.append_transition(
        ProposalStatusTransition(
            proposal_id=proposal.proposal_id,
            proposal_key=proposal.proposal_key,
            from_status=ProposalStatus.CANDIDATE,
            to_status=ProposalStatus.VALIDATED,
            effective_at=authorization.authorized_at,
            action_kind=TransitionActionKind.OPERATOR,
            actor_id="external-operator",
            action_id="external-validation",
            reason_code="EXTERNAL_ACTION",
            previous_transition_id=history[-1].transition_id,
        )
    )

    with pytest.raises(ValueError, match="current CANDIDATE"):
        SQLiteProposalTransitionAuthorizationStore(store_path).append(authorization)


def test_first_authorization_requires_no_predecessor(tmp_path) -> None:
    store_path, _, _, _, authorization = persisted_authorization_fixture(tmp_path)
    invalid = ProposalTransitionAuthorization(
        **authorization.model_dump(
            exclude={"authorization_id", "previous_authorization_id"}
        ),
        previous_authorization_id="nonexistent-authorization",
    )

    with pytest.raises(ValueError, match="current terminal authorization"):
        SQLiteProposalTransitionAuthorizationStore(store_path).append(invalid)
