from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_transition_authorization_contracts import (
    ProposalTransitionAuthorization,
)

NOW = datetime(2026, 1, 15, 13, 0, tzinfo=UTC)


def _authorization(**overrides: object) -> ProposalTransitionAuthorization:
    values: dict[str, object] = {
        "proposal_id": "proposal-1",
        "proposal_key": "proposal-key-1",
        "candidate_id": "candidate-1",
        "plan_id": "plan-1",
        "paired_result_id": "paired-result-1",
        "accepted_review_id": "review-1",
        "from_status": ProposalStatus.CANDIDATE,
        "to_status": ProposalStatus.VALIDATED,
        "operator_id": "operator-1",
        "action_id": "authorization-action-1",
        "reason_code": "PAIRED_EVIDENCE_ACCEPTED",
        "authorized_at": NOW,
    }
    values.update(overrides)
    return ProposalTransitionAuthorization(**values)


def test_authorization_identity_is_deterministic_and_includes_authorized_at() -> None:
    first = _authorization()
    assert _authorization().authorization_id == first.authorization_id
    assert _authorization(authorized_at=NOW + timedelta(seconds=1)).authorization_id != (
        first.authorization_id
    )


def test_authorization_is_frozen_strict_utc_and_candidate_to_validated_only() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        _authorization(authorized_at=datetime(2026, 1, 15, 13, 0))
    with pytest.raises(ValidationError, match="CANDIDATE to VALIDATED"):
        _authorization(to_status=ProposalStatus.REJECTED)

    authorization = _authorization()
    with pytest.raises(ValidationError):
        authorization.reason_code = "CHANGED"  # type: ignore[misc]
