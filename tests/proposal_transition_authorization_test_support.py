from __future__ import annotations

from datetime import timedelta

from paired_evaluation_review_test_support import persisted_review_fixture

from axq.reflection.paired_evaluation_review_store import SQLitePairedEvaluationReviewStore
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_transition_authorization_contracts import (
    ProposalTransitionAuthorization,
)


def persisted_authorization_fixture(path):
    store_path, proposal, result, review = persisted_review_fixture(path)
    SQLitePairedEvaluationReviewStore(store_path).append(review)
    authorization = ProposalTransitionAuthorization(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        candidate_id=result.candidate_id,
        plan_id=result.plan_id,
        paired_result_id=result.result_id,
        accepted_review_id=review.review_id,
        from_status=ProposalStatus.CANDIDATE,
        to_status=ProposalStatus.VALIDATED,
        operator_id="operator-controlled",
        action_id="proposal-authorization-action-001",
        reason_code="PAIRED_EVIDENCE_ACCEPTED",
        authorized_at=review.effective_at + timedelta(minutes=1),
    )
    return store_path, proposal, result, review, authorization
