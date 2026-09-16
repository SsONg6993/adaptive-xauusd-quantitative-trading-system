"""Append-only persistence for governed candidate replay evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from axq.database import Database
from axq.reflection.candidate_replay_contracts import (
    CandidateReplayArtifactRef,
    CandidateReplayAudit,
    CandidateReplayRequest,
)
from axq.reflection.contracts import ReflectionModel
from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import CanonicalMetricSampleArtifact
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


def _payload(record: ReflectionModel) -> str:
    return json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


class SQLiteCandidateReplayStore:
    """Persist exact candidate replay requests, outputs, and terminal audits."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)
        self._evaluations = SQLiteProposalEvaluationStore(self.path)
        self._proposals = SQLiteImprovementProposalStore(self.path)

    def append_request(self, request: CandidateReplayRequest) -> bool:
        request = CandidateReplayRequest.model_validate(request.model_dump())
        existing_request = self.request(request.request_id)
        if existing_request is not None:
            return False
        proposal = self._proposals.proposal(request.proposal_id)
        candidate = self._evaluations.candidate(request.candidate_id)
        plan = self._evaluations.plan(request.plan_id)
        if proposal is None or candidate is None or plan is None:
            raise ValueError("candidate replay proposal, candidate, and plan must be persisted")
        if self._proposals.current_status(proposal.proposal_id) is not ProposalStatus.CANDIDATE:
            raise ValueError("candidate replay requires current CANDIDATE proposal status")
        if (
            candidate.proposal_id != proposal.proposal_id
            or plan.proposal_id != proposal.proposal_id
            or plan.candidate_id != candidate.candidate_id
        ):
            raise ValueError("candidate replay authoritative linkage mismatch")
        if request.deterministic_seed != plan.deterministic_seed:
            raise ValueError("candidate replay seed does not match plan")
        if request.environment_identity != plan.environment_identity:
            raise ValueError("candidate replay environment does not match plan")
        required_scopes = {
            item.scope for item in plan.metrics if item.scope is not MetricScope.FINAL_OOS
        }
        if {item.scope for item in request.input_artifact_refs} != required_scopes:
            raise ValueError("candidate replay input scopes do not match plan")
        payload = _payload(request)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM candidate_replay_requests WHERE request_id = ?",
                (request.request_id,),
            ).fetchone()
            if existing is not None:
                stored = CandidateReplayRequest.model_validate_json(existing["record_json"])
                if stored.request_id == request.request_id:
                    return False
                raise ValueError("candidate replay request ID conflict")
            connection.execute(
                """
                INSERT INTO candidate_replay_requests(
                    request_id, proposal_id, candidate_id, plan_id, evaluation_run_key,
                    engine_kind, engine_version, deterministic_seed, environment_identity,
                    requested_at, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    request.proposal_id,
                    request.candidate_id,
                    request.plan_id,
                    request.evaluation_run_key,
                    request.engine_kind.value,
                    request.engine_version,
                    request.deterministic_seed,
                    request.environment_identity,
                    request.requested_at.isoformat(),
                    request.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
            connection.executemany(
                """
                INSERT INTO candidate_replay_input_refs(request_id, scope, semantic_id, sha256)
                VALUES (?, ?, ?, ?)
                """,
                (
                    (request.request_id, item.scope.value, item.semantic_id, item.sha256)
                    for item in request.input_artifact_refs
                ),
            )
        return True

    def request(self, request_id: str) -> CandidateReplayRequest | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM candidate_replay_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return (
            None
            if row is None
            else CandidateReplayRequest.model_validate_json(row["record_json"])
        )

    def requests(self) -> tuple[CandidateReplayRequest, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM candidate_replay_requests ORDER BY request_sequence"
            ).fetchall()
        return tuple(CandidateReplayRequest.model_validate_json(row["record_json"]) for row in rows)

    def append_artifacts(
        self,
        request_id: str,
        artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    ) -> bool:
        request = self.request(request_id)
        if request is None:
            raise ValueError("candidate replay request must be persisted before artifacts")
        artifacts = tuple(sorted(artifacts, key=lambda item: item.scope.value))
        if len({item.scope for item in artifacts}) != len(artifacts):
            raise ValueError("candidate replay output scopes must be unique")
        if {item.scope for item in artifacts} != {
            item.scope for item in request.input_artifact_refs
        }:
            raise ValueError("candidate replay output scopes do not match request")
        plan = self._evaluations.plan(request.plan_id)
        if plan is None:
            raise ValueError("candidate replay plan is missing")
        for artifact in artifacts:
            expected_keys = {
                item.metric_key for item in plan.metrics if item.scope is artifact.scope
            }
            if {item.metric_key for item in artifact.series} != expected_keys:
                raise ValueError("candidate replay output metric keys do not match plan")
        inserted = False
        with self._database.transaction() as connection:
            for artifact in artifacts:
                payload = _payload(artifact)
                digest = hashlib.sha256(canonical_record_bytes(artifact)).hexdigest()
                existing = connection.execute(
                    "SELECT record_json FROM candidate_replay_artifacts WHERE artifact_id = ?",
                    (artifact.artifact_id,),
                ).fetchone()
                if existing is None:
                    connection.execute(
                        """
                        INSERT INTO candidate_replay_artifacts(
                            artifact_id, scope, sha256, available_at, schema_version,
                            payload_hash, record_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            artifact.artifact_id,
                            artifact.scope.value,
                            digest,
                            artifact.available_at.isoformat(),
                            artifact.schema_version,
                            canonical_hash(json.loads(payload)),
                            payload,
                        ),
                    )
                elif str(existing["record_json"]) != payload:
                    raise ValueError("candidate replay artifact ID conflict")
                link = connection.execute(
                    """
                    SELECT artifact_id, sha256 FROM candidate_replay_output_refs
                    WHERE request_id = ? AND scope = ?
                    """,
                    (request_id, artifact.scope.value),
                ).fetchone()
                if link is None:
                    connection.execute(
                        """
                        INSERT INTO candidate_replay_output_refs(
                            request_id, scope, artifact_id, sha256
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (request_id, artifact.scope.value, artifact.artifact_id, digest),
                    )
                    inserted = True
                elif link["artifact_id"] != artifact.artifact_id or link["sha256"] != digest:
                    raise ValueError("candidate replay request already has conflicting output")
        return inserted

    def artifacts(self, request_id: str) -> tuple[CanonicalMetricSampleArtifact, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT artifact.record_json
                FROM candidate_replay_output_refs AS output
                JOIN candidate_replay_artifacts AS artifact
                  ON artifact.artifact_id = output.artifact_id
                WHERE output.request_id = ? ORDER BY output.scope
                """,
                (request_id,),
            ).fetchall()
        return tuple(
            CanonicalMetricSampleArtifact.model_validate_json(row["record_json"]) for row in rows
        )

    def append_audit(self, audit: CandidateReplayAudit) -> bool:
        audit = CandidateReplayAudit.model_validate(audit.model_dump())
        request = self.request(audit.request_id)
        artifacts = self.artifacts(audit.request_id)
        if request is None or not artifacts:
            raise ValueError("candidate replay request and outputs must precede audit")
        expected_outputs = tuple(
            CandidateReplayArtifactRef(
                scope=item.scope,
                semantic_id=item.artifact_id,
                sha256=hashlib.sha256(canonical_record_bytes(item)).hexdigest(),
            )
            for item in artifacts
        )
        if (
            audit.proposal_id != request.proposal_id
            or audit.candidate_id != request.candidate_id
            or audit.plan_id != request.plan_id
            or audit.evaluation_run_key != request.evaluation_run_key
            or audit.engine_kind is not request.engine_kind
            or audit.engine_version != request.engine_version
            or audit.deterministic_seed != request.deterministic_seed
            or audit.environment_identity != request.environment_identity
            or audit.input_artifact_refs != request.input_artifact_refs
            or audit.output_artifact_refs != expected_outputs
        ):
            raise ValueError("candidate replay audit does not exactly match request and outputs")
        payload = _payload(audit)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM candidate_replay_audits WHERE request_id = ?",
                (audit.request_id,),
            ).fetchone()
            if existing is not None:
                stored = CandidateReplayAudit.model_validate_json(existing["record_json"])
                if stored.audit_id == audit.audit_id:
                    return False
                raise ValueError("completed candidate replay audit already exists")
            connection.execute(
                """
                INSERT INTO candidate_replay_audits(
                    audit_id, request_id, proposal_id, candidate_id, plan_id,
                    evaluation_run_key, engine_kind, engine_version, deterministic_seed,
                    environment_identity, status, started_at, completed_at, schema_version,
                    payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.audit_id,
                    audit.request_id,
                    audit.proposal_id,
                    audit.candidate_id,
                    audit.plan_id,
                    audit.evaluation_run_key,
                    audit.engine_kind.value,
                    audit.engine_version,
                    audit.deterministic_seed,
                    audit.environment_identity,
                    audit.status.value,
                    audit.started_at.isoformat(),
                    audit.completed_at.isoformat(),
                    audit.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def audit(self, request_id: str) -> CandidateReplayAudit | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM candidate_replay_audits WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return None if row is None else CandidateReplayAudit.model_validate_json(row["record_json"])

    def audits(self) -> tuple[CandidateReplayAudit, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM candidate_replay_audits ORDER BY audit_sequence"
            ).fetchall()
        return tuple(CandidateReplayAudit.model_validate_json(row["record_json"]) for row in rows)

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
