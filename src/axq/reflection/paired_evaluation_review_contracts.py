"""Immutable contracts for governed human review of paired evidence."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from axq.reflection.contracts import ReflectionModel
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class PairedEvaluationReviewDecision(StrEnum):
    """Evidence-only decisions available to an operator."""

    ACCEPT_EVIDENCE = "ACCEPT_EVIDENCE"
    REJECT_EVIDENCE = "REJECT_EVIDENCE"
    DEFER = "DEFER"


class PairedEvaluationReview(ReflectionModel):
    """One immutable node in a paired-result review chain."""

    review_id: str = ""
    result_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    decision: PairedEvaluationReviewDecision
    operator_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    effective_at: UTCDateTime
    supporting_evaluation_result_ids: tuple[str, ...] = ()
    supporting_paired_result_ids: tuple[str, ...] = ()
    previous_review_id: str | None = None

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> PairedEvaluationReview:
        evaluation_ids = tuple(sorted(set(self.supporting_evaluation_result_ids)))
        paired_ids = tuple(sorted(set(self.supporting_paired_result_ids)))
        if any(not item for item in (*evaluation_ids, *paired_ids)):
            raise ValueError("supporting result IDs cannot be empty")
        object.__setattr__(self, "supporting_evaluation_result_ids", evaluation_ids)
        object.__setattr__(self, "supporting_paired_result_ids", paired_ids)
        identity = self.model_dump(mode="json", exclude={"review_id"})
        expected = f"paired-evaluation-review-{canonical_hash(identity)[:20]}"
        if self.review_id and self.review_id != expected:
            raise ValueError("review_id does not match review content")
        object.__setattr__(self, "review_id", expected)
        return self
