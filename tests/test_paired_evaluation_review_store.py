from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest
from paired_evaluation_review_test_support import persisted_review_fixture

from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.paired_evaluation_review_contracts import (
    PairedEvaluationReview,
    PairedEvaluationReviewDecision,
)
from axq.reflection.paired_evaluation_review_store import SQLitePairedEvaluationReviewStore
from axq.reflection.proposal_store import SQLiteImprovementProposalStore


def test_store_enforces_linear_chain_idempotency_and_immutable_authorities(tmp_path) -> None:
    store_path, proposal, result, first = persisted_review_fixture(tmp_path)
    store = SQLitePairedEvaluationReviewStore(store_path)
    result_before = canonical_record_bytes(result)
    status_before = SQLiteImprovementProposalStore(store_path).current_status(proposal.proposal_id)

    assert store.append(first) is True
    assert store.append(first) is False
    second = PairedEvaluationReview(
        **first.model_dump(
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
        action_id="paired-review-action-002",
        reason_code="MORE_EVIDENCE_REQUIRED",
        effective_at=first.effective_at + timedelta(minutes=1),
        previous_review_id=first.review_id,
    )
    assert store.append(second) is True
    assert store.history(result.result_id) == (first, second)
    assert store.current(result.result_id) == second

    stale = PairedEvaluationReview(
        **first.model_dump(
            exclude={
                "review_id",
                "decision",
                "action_id",
                "reason_code",
                "effective_at",
                "previous_review_id",
            }
        ),
        decision=PairedEvaluationReviewDecision.REJECT_EVIDENCE,
        action_id="paired-review-action-stale",
        reason_code="STALE_FORK",
        effective_at=second.effective_at + timedelta(minutes=1),
        previous_review_id=first.review_id,
    )
    with pytest.raises(ValueError, match="current terminal"):
        store.append(stale)

    third = PairedEvaluationReview(
        **first.model_dump(
            exclude={
                "review_id",
                "decision",
                "action_id",
                "reason_code",
                "effective_at",
                "previous_review_id",
            }
        ),
        decision=PairedEvaluationReviewDecision.REJECT_EVIDENCE,
        action_id="paired-review-action-003",
        reason_code="CONTROLLED_EVIDENCE_REJECTED",
        effective_at=second.effective_at + timedelta(minutes=1),
        previous_review_id=second.review_id,
    )
    assert store.append(third) is True
    assert store.history(result.result_id) == (first, second, third)
    assert store.current(result.result_id) == third

    paired_after = store.paired_result(result.result_id)
    assert paired_after is not None
    assert canonical_record_bytes(paired_after) == result_before
    assert (
        SQLiteImprovementProposalStore(store_path).current_status(proposal.proposal_id)
        == status_before
    )


def test_store_rejects_wrong_linkage_time_and_missing_support(tmp_path) -> None:
    store_path, _, result, first = persisted_review_fixture(tmp_path)
    store = SQLitePairedEvaluationReviewStore(store_path)
    wrong = PairedEvaluationReview(
        **first.model_dump(exclude={"review_id", "request_id"}),
        request_id="wrong-request",
    )
    with pytest.raises(ValueError, match="linkage"):
        store.append(wrong)
    early = PairedEvaluationReview(
        **first.model_dump(exclude={"review_id", "effective_at"}),
        effective_at=result.available_at - timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="availability"):
        store.append(early)
    missing_support = PairedEvaluationReview(
        **first.model_dump(exclude={"review_id", "supporting_paired_result_ids"}),
        supporting_paired_result_ids=("missing-result",),
    )
    with pytest.raises(ValueError, match="supporting paired"):
        store.append(missing_support)


def test_review_table_is_sql_append_only(tmp_path) -> None:
    store_path, _, _, review = persisted_review_fixture(tmp_path)
    store = SQLitePairedEvaluationReviewStore(store_path)
    store.append(review)
    with (
        pytest.raises(sqlite3.IntegrityError, match="append-only"),
        sqlite3.connect(store_path) as connection,
    ):
        connection.execute("UPDATE paired_evaluation_reviews SET reason_code = 'changed'")


def test_first_review_requires_no_parent_and_history_replay_fails_closed(tmp_path) -> None:
    store_path, _, result, review = persisted_review_fixture(tmp_path)
    store = SQLitePairedEvaluationReviewStore(store_path)
    invalid_first = PairedEvaluationReview(
        **review.model_dump(exclude={"review_id", "previous_review_id"}),
        previous_review_id="nonexistent-parent",
    )
    with pytest.raises(ValueError, match="current terminal"):
        store.append(invalid_first)

    assert store.append(review) is True
    with sqlite3.connect(store_path) as connection:
        connection.execute("DROP TRIGGER paired_evaluation_reviews_no_update")
        connection.execute(
            """
            UPDATE paired_evaluation_reviews
            SET record_json = json_set(record_json, '$.previous_review_id', 'fork')
            """
        )
    with pytest.raises(ValueError, match="review_id|invalid predecessor"):
        store.history(result.result_id)
