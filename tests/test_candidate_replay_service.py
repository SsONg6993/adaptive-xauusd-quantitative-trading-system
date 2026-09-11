from __future__ import annotations

from datetime import timedelta

import pytest
from candidate_replay_test_support import NOW, persisted_candidate_replay

from axq.reflection.candidate_replay_contracts import (
    CandidateReplayArtifactRef,
    CandidateReplayEngineKind,
    CandidateReplayRequest,
)
from axq.reflection.candidate_replay_engine import ControlledReplayFixtureEngine
from axq.reflection.candidate_replay_service import execute_candidate_replay
from axq.reflection.candidate_replay_store import SQLiteCandidateReplayStore
from axq.reflection.evaluation_contracts import MetricObservationStatus, MetricScope
from axq.reflection.execution_adapter import input_artifact_ref
from axq.reflection.execution_contracts import EvaluationExecutionRequest
from axq.reflection.execution_service import execute_evaluation_request
from axq.reflection.proposal_contracts import ProposalStatus, ProposalStatusTransition
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.weekly_contracts import TransitionActionKind


class CountingEngine:
    kind = CandidateReplayEngineKind.CONTROLLED_REPLAY_FIXTURE_V1
    version = "1.0"

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = ControlledReplayFixtureEngine()

    def execute(self, request, proposal, candidate, plan, fixtures):
        self.calls += 1
        return self.delegate.execute(request, proposal, candidate, plan, fixtures)


class WrongVersionEngine(CountingEngine):
    version = "2.0"


def _reject_proposal(path, proposal) -> None:
    store = SQLiteImprovementProposalStore(path)
    history = store.transition_history(proposal.proposal_id)
    store.append_transition(
        ProposalStatusTransition(
            proposal_id=proposal.proposal_id,
            proposal_key=proposal.proposal_key,
            from_status=ProposalStatus.CANDIDATE,
            to_status=ProposalStatus.REJECTED,
            effective_at=NOW + timedelta(minutes=10),
            action_kind=TransitionActionKind.OPERATOR,
            actor_id="operator",
            action_id="reject-before-execution",
            reason_code="CONTROLLED_REVIEW",
            previous_transition_id=history[-1].transition_id,
        )
    )


def test_later_retry_reuses_artifacts_and_audit_without_running_engine_twice(tmp_path) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    proposal, _, _, fixtures, request = persisted_candidate_replay(path)
    engine = CountingEngine()
    first = execute_candidate_replay(
        path,
        request,
        fixtures,
        started_at=NOW + timedelta(minutes=4),
        completed_at=NOW + timedelta(minutes=5),
        engine=engine,
    )
    _reject_proposal(path, proposal)
    later_request = CandidateReplayRequest(
        **request.model_dump(exclude={"request_id", "requested_at"}),
        requested_at=NOW + timedelta(days=1),
    )
    second = execute_candidate_replay(
        path,
        later_request,
        tuple(reversed(fixtures)),
        started_at=NOW + timedelta(days=1, minutes=4),
        completed_at=NOW + timedelta(days=1, minutes=5),
        engine=engine,
    )

    assert engine.calls == 1
    assert second.reused is True
    assert second.request.request_id == first.request.request_id
    assert second.audit.audit_id == first.audit.audit_id
    assert [item.artifact_id for item in second.artifacts] == [
        item.artifact_id for item in first.artifacts
    ]
    assert second.artifact_bytes == first.artifact_bytes


def test_digest_failure_creates_no_completed_audit(tmp_path) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    _, _, _, fixtures, request = persisted_candidate_replay(path)
    invalid = CandidateReplayRequest(
        **request.model_dump(exclude={"request_id", "input_artifact_refs"}),
        input_artifact_refs=(
            CandidateReplayArtifactRef(
                scope=MetricScope.VALIDATION,
                semantic_id=fixtures[0].artifact_id,
                sha256="f" * 64,
            ),
        ),
    )
    with pytest.raises(ValueError, match="digest"):
        execute_candidate_replay(
            path,
            invalid,
            fixtures,
            started_at=NOW + timedelta(minutes=4),
            completed_at=NOW + timedelta(minutes=5),
        )
    assert SQLiteCandidateReplayStore(path).audits() == ()


def test_service_rejects_an_engine_outside_the_request_allowlist(tmp_path) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    _, _, _, fixtures, request = persisted_candidate_replay(path)
    with pytest.raises(ValueError, match="allowlisted"):
        execute_candidate_replay(
            path,
            request,
            fixtures,
            started_at=NOW + timedelta(minutes=4),
            completed_at=NOW + timedelta(minutes=5),
            engine=WrongVersionEngine(),
        )
    assert SQLiteCandidateReplayStore(path).audits() == ()


def test_registered_but_incomplete_request_cannot_execute_after_candidate_rejection(
    tmp_path,
) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    proposal, _, _, fixtures, request = persisted_candidate_replay(path)
    SQLiteCandidateReplayStore(path).append_request(request)
    _reject_proposal(path, proposal)
    with pytest.raises(ValueError, match="CANDIDATE"):
        execute_candidate_replay(
            path,
            request,
            fixtures,
            started_at=NOW + timedelta(minutes=11),
            completed_at=NOW + timedelta(minutes=12),
        )
    assert SQLiteCandidateReplayStore(path).audits() == ()


def test_generated_artifact_executes_unchanged_through_task6(tmp_path) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    proposal, candidate, plan, fixtures, replay_request = persisted_candidate_replay(path)
    replay = execute_candidate_replay(
        path,
        replay_request,
        fixtures,
        started_at=NOW + timedelta(minutes=4),
        completed_at=NOW + timedelta(minutes=5),
    )
    execution_request = EvaluationExecutionRequest(
        plan_id=plan.plan_id,
        candidate_id=candidate.candidate_id,
        evaluation_run_key="controlled-task6-consumption",
        deterministic_seed=plan.deterministic_seed,
        environment_identity=plan.environment_identity,
        input_artifact_refs=tuple(input_artifact_ref(item) for item in replay.artifacts),
        requested_at=NOW + timedelta(minutes=6),
    )
    result = execute_evaluation_request(
        path,
        execution_request,
        replay.artifacts,
        started_at=NOW + timedelta(minutes=7),
        completed_at=NOW + timedelta(minutes=8),
    ).result

    validation = next(item for item in result.observations if item.scope is MetricScope.VALIDATION)
    final_oos = next(item for item in result.observations if item.scope is MetricScope.FINAL_OOS)
    assert validation.value == pytest.approx(0.1)
    assert final_oos.status is MetricObservationStatus.UNAVAILABLE
    assert final_oos.reason_code == "FINAL_OOS_NOT_ACCESSED"
    assert result.plan_id == plan.plan_id
    assert result.candidate_id == candidate.candidate_id
    assert (
        SQLiteImprovementProposalStore(path).current_status(proposal.proposal_id)
        is ProposalStatus.CANDIDATE
    )
