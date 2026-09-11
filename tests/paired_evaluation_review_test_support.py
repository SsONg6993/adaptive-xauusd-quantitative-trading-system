from __future__ import annotations

from datetime import timedelta

from paired_evaluation_test_support import NOW, persisted_paired_fixture

from axq.reflection.paired_evaluation_review_contracts import (
    PairedEvaluationReview,
    PairedEvaluationReviewDecision,
)
from axq.reflection.paired_evaluation_service import execute_paired_evaluation


def persisted_review_fixture(path):
    store_path, proposal, candidate, plan, _, baseline, candidate_artifact, request = (
        persisted_paired_fixture(path)
    )
    outcome = execute_paired_evaluation(
        store_path,
        request,
        (baseline,),
        (candidate_artifact,),
        started_at=NOW + timedelta(minutes=21),
        completed_at=NOW + timedelta(minutes=22),
    )
    review = PairedEvaluationReview(
        result_id=outcome.result.result_id,
        request_id=request.request_id,
        proposal_id=proposal.proposal_id,
        candidate_id=candidate.candidate_id,
        plan_id=plan.plan_id,
        decision=PairedEvaluationReviewDecision.ACCEPT_EVIDENCE,
        operator_id="operator-controlled",
        action_id="paired-review-action-001",
        reason_code="CONTROLLED_EVIDENCE_ACCEPTED",
        effective_at=NOW + timedelta(minutes=23),
    )
    return store_path, proposal, outcome.result, review
