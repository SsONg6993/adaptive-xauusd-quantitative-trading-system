"""Deterministic orchestration for governed candidate replay evaluation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from axq.reflection.candidate_replay_contracts import (
    CandidateReplayArtifactRef,
    CandidateReplayAudit,
    CandidateReplayRequest,
    ControlledReplayFixtureArtifact,
)
from axq.reflection.candidate_replay_engine import (
    CandidateReplayEngine,
    ControlledReplayFixtureEngine,
)
from axq.reflection.candidate_replay_store import SQLiteCandidateReplayStore
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import CanonicalMetricSampleArtifact
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.runtime.state import UTCDateTime


@dataclass(frozen=True)
class CandidateReplayOutcome:
    request: CandidateReplayRequest
    artifacts: tuple[CanonicalMetricSampleArtifact, ...]
    artifact_bytes: tuple[bytes, ...]
    audit: CandidateReplayAudit
    reused: bool


def _artifact_refs(
    artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    payloads: tuple[bytes, ...],
) -> tuple[CandidateReplayArtifactRef, ...]:
    return tuple(
        CandidateReplayArtifactRef(
            scope=artifact.scope,
            semantic_id=artifact.artifact_id,
            sha256=hashlib.sha256(payload).hexdigest(),
        )
        for artifact, payload in zip(artifacts, payloads, strict=True)
    )


def execute_candidate_replay(
    store_path: str | Path,
    request: CandidateReplayRequest,
    fixtures: tuple[ControlledReplayFixtureArtifact, ...],
    *,
    started_at: UTCDateTime,
    completed_at: UTCDateTime,
    engine: CandidateReplayEngine | None = None,
) -> CandidateReplayOutcome:
    """Execute or recover one exact governed candidate replay request."""

    replay_store = SQLiteCandidateReplayStore(store_path)
    replay_store.append_request(request)
    stored_request = replay_store.request(request.request_id)
    if stored_request is None:
        raise ValueError("candidate replay request was not persisted")
    existing_audit = replay_store.audit(stored_request.request_id)
    if existing_audit is not None:
        artifacts = replay_store.artifacts(stored_request.request_id)
        payloads = tuple(canonical_record_bytes(item) for item in artifacts)
        if _artifact_refs(artifacts, payloads) != existing_audit.output_artifact_refs:
            raise ValueError("completed candidate replay artifact digest mismatch")
        return CandidateReplayOutcome(
            request=stored_request,
            artifacts=artifacts,
            artifact_bytes=payloads,
            audit=existing_audit,
            reused=True,
        )
    proposal_store = SQLiteImprovementProposalStore(store_path)
    evaluation_store = SQLiteProposalEvaluationStore(store_path)
    proposal = proposal_store.proposal(stored_request.proposal_id)
    candidate = evaluation_store.candidate(stored_request.candidate_id)
    plan = evaluation_store.plan(stored_request.plan_id)
    if proposal is None or candidate is None or plan is None:
        raise ValueError("candidate replay authoritative records are missing")
    if proposal_store.current_status(proposal.proposal_id) is not ProposalStatus.CANDIDATE:
        raise ValueError("candidate replay execution requires current CANDIDATE status")
    selected_engine = ControlledReplayFixtureEngine() if engine is None else engine
    if (
        selected_engine.kind is not stored_request.engine_kind
        or selected_engine.version != stored_request.engine_version
    ):
        raise ValueError("candidate replay engine is not allowlisted by the request")
    output = selected_engine.execute(stored_request, proposal, candidate, plan, fixtures)
    replay_store.append_artifacts(stored_request.request_id, output.artifacts)
    audit = CandidateReplayAudit(
        request_id=stored_request.request_id,
        proposal_id=stored_request.proposal_id,
        candidate_id=stored_request.candidate_id,
        plan_id=stored_request.plan_id,
        evaluation_run_key=stored_request.evaluation_run_key,
        engine_kind=stored_request.engine_kind,
        engine_version=stored_request.engine_version,
        deterministic_seed=stored_request.deterministic_seed,
        environment_identity=stored_request.environment_identity,
        input_artifact_refs=stored_request.input_artifact_refs,
        output_artifact_refs=_artifact_refs(output.artifacts, output.artifact_bytes),
        started_at=started_at,
        completed_at=completed_at,
    )
    replay_store.append_audit(audit)
    replay_store.sync()
    return CandidateReplayOutcome(
        request=stored_request,
        artifacts=output.artifacts,
        artifact_bytes=output.artifact_bytes,
        audit=audit,
        reused=False,
    )
