from __future__ import annotations

import hashlib
import sqlite3
from datetime import timedelta

import pytest
from candidate_replay_test_support import NOW, persisted_candidate_replay

from axq.reflection.candidate_replay_contracts import (
    CandidateReplayArtifactRef,
    CandidateReplayAudit,
    CandidateReplayRequest,
)
from axq.reflection.candidate_replay_engine import ControlledReplayFixtureEngine
from axq.reflection.candidate_replay_store import SQLiteCandidateReplayStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.proposal_contracts import (
    ProposalStatus,
    ProposalStatusTransition,
)
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.weekly_contracts import TransitionActionKind


def _outputs(proposal, candidate, plan, fixtures, request):
    return ControlledReplayFixtureEngine().execute(
        request,
        proposal,
        candidate,
        plan,
        fixtures,
    )


def _output_refs(output):
    return tuple(
        CandidateReplayArtifactRef(
            scope=artifact.scope,
            semantic_id=artifact.artifact_id,
            sha256=hashlib.sha256(payload).hexdigest(),
        )
        for artifact, payload in zip(output.artifacts, output.artifact_bytes, strict=True)
    )


def _audit(request, output, **changes):
    values = {
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
        "output_artifact_refs": _output_refs(output),
        "started_at": NOW + timedelta(minutes=4),
        "completed_at": NOW + timedelta(minutes=5),
    }
    values.update(changes)
    return CandidateReplayAudit(**values)


def test_store_validates_exact_authoritative_linkage_and_reuses_later_request(tmp_path) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    _, _, plan, _, request = persisted_candidate_replay(path)
    store = SQLiteCandidateReplayStore(path)
    assert store.append_request(request) is True
    later = CandidateReplayRequest(
        **request.model_dump(exclude={"request_id", "requested_at"}),
        requested_at=request.requested_at + timedelta(days=1),
    )
    assert later.request_id == request.request_id
    assert store.append_request(later) is False
    assert store.request(request.request_id) == request
    with pytest.raises(ValueError, match="seed"):
        store.append_request(
            CandidateReplayRequest(
                **request.model_dump(exclude={"request_id", "deterministic_seed"}),
                deterministic_seed=plan.deterministic_seed + 1,
            )
        )


def test_store_persists_canonical_outputs_and_completed_audit_idempotently(tmp_path) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    proposal, candidate, plan, fixtures, request = persisted_candidate_replay(path)
    output = _outputs(proposal, candidate, plan, fixtures, request)
    store = SQLiteCandidateReplayStore(path)
    store.append_request(request)
    assert store.append_artifacts(request.request_id, output.artifacts) is True
    assert store.artifacts(request.request_id) == output.artifacts
    audit = _audit(request, output)
    assert store.append_audit(audit) is True
    later = CandidateReplayAudit(
        **audit.model_dump(exclude={"audit_id", "started_at", "completed_at"}),
        started_at=NOW + timedelta(days=1),
        completed_at=NOW + timedelta(days=1, minutes=1),
    )
    assert store.append_audit(later) is False
    assert store.audit(request.request_id) == audit
    assert all(
        ref.sha256 == hashlib.sha256(canonical_record_bytes(artifact)).hexdigest()
        for ref, artifact in zip(audit.output_artifact_refs, output.artifacts, strict=True)
    )


def test_new_replay_requires_candidate_but_existing_request_remains_recoverable(tmp_path) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    proposal, _, _, _, request = persisted_candidate_replay(path)
    store = SQLiteCandidateReplayStore(path)
    store.append_request(request)
    proposal_store = SQLiteImprovementProposalStore(path)
    history = proposal_store.transition_history(proposal.proposal_id)
    proposal_store.append_transition(
        ProposalStatusTransition(
            proposal_id=proposal.proposal_id,
            proposal_key=proposal.proposal_key,
            from_status=ProposalStatus.CANDIDATE,
            to_status=ProposalStatus.REJECTED,
            effective_at=NOW + timedelta(minutes=10),
            action_kind=TransitionActionKind.OPERATOR,
            actor_id="operator",
            action_id="reject-after-registration",
            reason_code="CONTROLLED_REVIEW",
            previous_transition_id=history[-1].transition_id,
        )
    )
    assert store.append_request(request) is False
    with pytest.raises(ValueError, match="CANDIDATE"):
        store.append_request(
            CandidateReplayRequest(
                **request.model_dump(exclude={"request_id", "evaluation_run_key"}),
                evaluation_run_key="new-run-after-rejection",
            )
        )


def test_candidate_replay_tables_are_append_only(tmp_path) -> None:
    path = tmp_path / "candidate-replay.sqlite3"
    proposal, candidate, plan, fixtures, request = persisted_candidate_replay(path)
    output = _outputs(proposal, candidate, plan, fixtures, request)
    store = SQLiteCandidateReplayStore(path)
    store.append_request(request)
    store.append_artifacts(request.request_id, output.artifacts)
    store.append_audit(_audit(request, output))
    tables = (
        "candidate_replay_requests",
        "candidate_replay_input_refs",
        "candidate_replay_artifacts",
        "candidate_replay_output_refs",
        "candidate_replay_audits",
    )
    with sqlite3.connect(path) as connection:
        for table in tables:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"DELETE FROM {table}")
