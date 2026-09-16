"""Immutable permission records for a governed proposal transition."""

from __future__ import annotations

from pydantic import Field, model_validator

from axq.reflection.contracts import ReflectionModel
from axq.reflection.proposal_contracts import ProposalStatus
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class ProposalTransitionAuthorization(ReflectionModel):
    """Operator permission to request, but not apply, one proposal transition."""

    authorization_id: str = ""
    proposal_id: str = Field(min_length=1)
    proposal_key: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    paired_result_id: str = Field(min_length=1)
    accepted_review_id: str = Field(min_length=1)
    from_status: ProposalStatus
    to_status: ProposalStatus
    operator_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    authorized_at: UTCDateTime
    previous_authorization_id: str | None = None

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ProposalTransitionAuthorization:
        if (
            self.from_status is not ProposalStatus.CANDIDATE
            or self.to_status is not ProposalStatus.VALIDATED
        ):
            raise ValueError("V1 authorization permits only CANDIDATE to VALIDATED")
        identity = self.model_dump(mode="json", exclude={"authorization_id"})
        expected = f"proposal-transition-authorization-{canonical_hash(identity)[:20]}"
        if self.authorization_id and self.authorization_id != expected:
            raise ValueError("authorization_id does not match authorization content")
        object.__setattr__(self, "authorization_id", expected)
        return self
