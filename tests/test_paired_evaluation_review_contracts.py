from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.reflection.paired_evaluation_review_contracts import (
    PairedEvaluationReview,
    PairedEvaluationReviewDecision,
)

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def _review(**overrides: object) -> PairedEvaluationReview:
    values: dict[str, object] = {
        "result_id": "paired-result-1",
        "request_id": "paired-request-1",
        "proposal_id": "proposal-1",
        "candidate_id": "candidate-1",
        "plan_id": "plan-1",
        "decision": PairedEvaluationReviewDecision.ACCEPT_EVIDENCE,
        "operator_id": "operator-1",
        "action_id": "review-action-1",
        "reason_code": "EVIDENCE_ACCEPTED",
        "effective_at": NOW,
        "supporting_evaluation_result_ids": ("evaluation-b", "evaluation-a", "evaluation-a"),
        "supporting_paired_result_ids": ("paired-b", "paired-a", "paired-a"),
    }
    values.update(overrides)
    return PairedEvaluationReview(**values)


def test_review_identity_is_content_addressed_and_support_ids_are_normalized() -> None:
    first = _review()
    second = _review(
        supporting_evaluation_result_ids=("evaluation-a", "evaluation-b"),
        supporting_paired_result_ids=("paired-a", "paired-b"),
    )

    assert first.review_id == second.review_id
    assert first.supporting_evaluation_result_ids == ("evaluation-a", "evaluation-b")
    assert first.supporting_paired_result_ids == ("paired-a", "paired-b")
    later = _review(effective_at=NOW + timedelta(seconds=1))
    assert later.review_id != first.review_id


def test_review_requires_strict_utc_and_is_immutable() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        _review(effective_at=datetime(2026, 1, 15, 12, 0))

    review = _review()
    with pytest.raises(ValidationError):
        review.reason_code = "CHANGED"  # type: ignore[misc]
