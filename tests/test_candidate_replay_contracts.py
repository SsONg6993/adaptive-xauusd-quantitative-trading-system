from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.reflection.candidate_replay_contracts import (
    CandidateReplayArtifactRef,
    CandidateReplayAudit,
    CandidateReplayEngineKind,
    CandidateReplayRequest,
    ControlledMetricValue,
    ControlledReplayFixtureArtifact,
    ControlledReplayObservation,
)
from axq.reflection.evaluation_contracts import MetricScope

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=UTC)


def _fixture(scope: MetricScope = MetricScope.VALIDATION) -> ControlledReplayFixtureArtifact:
    return ControlledReplayFixtureArtifact(
        proposal_id="proposal-1",
        candidate_id="candidate-1",
        plan_id="plan-1",
        scope=scope,
        available_at=NOW + timedelta(minutes=2),
        observations=(
            ControlledReplayObservation(
                event_id="event-2",
                available_at=NOW + timedelta(minutes=2),
                metric_values=(ControlledMetricValue(metric_key="expectancy", value=0.3),),
            ),
            ControlledReplayObservation(
                event_id="event-1",
                available_at=NOW + timedelta(minutes=1),
                metric_values=(ControlledMetricValue(metric_key="expectancy", value=-0.1),),
            ),
        ),
    )


def _ref(fixture: ControlledReplayFixtureArtifact) -> CandidateReplayArtifactRef:
    return CandidateReplayArtifactRef(
        scope=fixture.scope,
        semantic_id=fixture.artifact_id,
        sha256="a" * 64,
    )


def _request(**changes: object) -> CandidateReplayRequest:
    values: dict[str, object] = {
        "proposal_id": "proposal-1",
        "candidate_id": "candidate-1",
        "plan_id": "plan-1",
        "evaluation_run_key": "controlled-run",
        "deterministic_seed": 1729,
        "environment_identity": "python-3.12-lock-controlled",
        "input_artifact_refs": (_ref(_fixture()),),
        "requested_at": NOW,
    }
    values.update(changes)
    return CandidateReplayRequest(**values)


def _audit(request: CandidateReplayRequest, **changes: object) -> CandidateReplayAudit:
    values: dict[str, object] = {
        "request_id": request.request_id,
        "proposal_id": request.proposal_id,
        "candidate_id": request.candidate_id,
        "plan_id": request.plan_id,
        "evaluation_run_key": request.evaluation_run_key,
        "engine_kind": request.engine_kind,
        "engine_version": request.engine_version,
        "deterministic_seed": request.deterministic_seed,
        "environment_identity": request.environment_identity,
        "input_artifact_refs": request.input_artifact_refs,
        "output_artifact_refs": (
            CandidateReplayArtifactRef(
                scope=MetricScope.VALIDATION,
                semantic_id="canonical-metric-samples-1",
                sha256="b" * 64,
            ),
        ),
        "started_at": NOW + timedelta(minutes=3),
        "completed_at": NOW + timedelta(minutes=4),
    }
    values.update(changes)
    return CandidateReplayAudit(**values)


def test_fixture_is_causally_normalized_content_addressed_and_immutable() -> None:
    fixture = _fixture()
    assert [item.event_id for item in fixture.observations] == ["event-1", "event-2"]
    assert fixture.artifact_id.startswith("controlled-replay-fixture-")
    with pytest.raises(ValidationError):
        fixture.scope = MetricScope.DEVELOPMENT  # type: ignore[misc]
    with pytest.raises(ValidationError, match="availability"):
        ControlledReplayFixtureArtifact.model_validate(
            fixture.model_dump(exclude={"artifact_id"}) | {"available_at": NOW}
        )


def test_contracts_reject_naive_time_final_oos_and_duplicate_values() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        _request(requested_at=datetime(2026, 9, 11, 12, 0))
    with pytest.raises(ValidationError, match="Final OOS"):
        _fixture(MetricScope.FINAL_OOS)
    with pytest.raises(ValidationError, match="Final OOS"):
        CandidateReplayArtifactRef(
            scope=MetricScope.FINAL_OOS,
            semantic_id="forbidden",
            sha256="a" * 64,
        )
    with pytest.raises(ValidationError, match="unique"):
        ControlledReplayObservation(
            event_id="event",
            available_at=NOW,
            metric_values=(
                ControlledMetricValue(metric_key="expectancy", value=0.1),
                ControlledMetricValue(metric_key="expectancy", value=0.2),
            ),
        )


def test_operational_times_do_not_change_request_or_audit_identity() -> None:
    request = _request()
    later_request = _request(requested_at=NOW + timedelta(days=1))
    assert request.request_id == later_request.request_id
    assert request.engine_kind is CandidateReplayEngineKind.CONTROLLED_REPLAY_FIXTURE_V1

    audit = _audit(request)
    later_audit = _audit(
        request,
        started_at=NOW + timedelta(days=1),
        completed_at=NOW + timedelta(days=1, minutes=1),
    )
    assert audit.audit_id == later_audit.audit_id


def test_semantic_input_change_changes_request_and_audit_identity() -> None:
    request = _request()
    changed = _request(
        input_artifact_refs=(
            _ref(_fixture()).model_copy(update={"sha256": "c" * 64}),
        )
    )
    assert changed.request_id != request.request_id
    assert _audit(changed).audit_id != _audit(request).audit_id
