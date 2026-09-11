"""Append-only persistence for deterministic evaluation execution metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from axq.database import Database
from axq.reflection.contracts import ReflectionModel
from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import (
    EvaluationExecutionAudit,
    EvaluationExecutionRequest,
)
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


def _payload(record: ReflectionModel) -> str:
    return json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


class SQLiteEvaluationExecutionStore:
    """Persist immutable request and completed-audit facts."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)
        self._evaluations = SQLiteProposalEvaluationStore(self.path)

    def append_request(self, request: EvaluationExecutionRequest) -> bool:
        request = EvaluationExecutionRequest.model_validate(request.model_dump())
        plan = self._evaluations.plan(request.plan_id)
        candidate = self._evaluations.candidate(request.candidate_id)
        if plan is None or candidate is None:
            raise ValueError("execution request plan and candidate must be persisted")
        if plan.candidate_id != candidate.candidate_id:
            raise ValueError("execution request candidate linkage does not match plan")
        if request.deterministic_seed != plan.deterministic_seed:
            raise ValueError("execution request seed does not match plan")
        if request.environment_identity != plan.environment_identity:
            raise ValueError("execution request environment does not match plan")
        required_scopes = {
            metric.scope for metric in plan.metrics if metric.scope is not MetricScope.FINAL_OOS
        }
        if {item.scope for item in request.input_artifact_refs} != required_scopes:
            raise ValueError("execution request input scopes do not match plan")
        payload = _payload(request)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM evaluation_execution_requests WHERE request_id = ?",
                (request.request_id,),
            ).fetchone()
            if existing is not None:
                stored = EvaluationExecutionRequest.model_validate_json(existing["record_json"])
                if stored.request_id == request.request_id:
                    return False
                raise ValueError("execution request ID conflict")
            connection.execute(
                """
                INSERT INTO evaluation_execution_requests(
                    request_id, plan_id, candidate_id, evaluation_run_key, adapter_kind,
                    adapter_version, deterministic_seed, environment_identity, requested_at,
                    schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    request.plan_id,
                    request.candidate_id,
                    request.evaluation_run_key,
                    request.adapter_kind.value,
                    request.adapter_version,
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
                INSERT INTO evaluation_execution_input_refs(request_id, scope, semantic_id, sha256)
                VALUES (?, ?, ?, ?)
                """,
                (
                    (request.request_id, ref.scope.value, ref.semantic_id, ref.sha256)
                    for ref in request.input_artifact_refs
                ),
            )
        return True

    def request(self, request_id: str) -> EvaluationExecutionRequest | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM evaluation_execution_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return (
            None
            if row is None
            else EvaluationExecutionRequest.model_validate_json(row["record_json"])
        )

    def requests(self) -> tuple[EvaluationExecutionRequest, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM evaluation_execution_requests ORDER BY request_sequence"
            ).fetchall()
        return tuple(
            EvaluationExecutionRequest.model_validate_json(row["record_json"]) for row in rows
        )

    def append_audit(self, audit: EvaluationExecutionAudit) -> bool:
        audit = EvaluationExecutionAudit.model_validate(audit.model_dump())
        request = self.request(audit.request_id)
        result = self._evaluations.result(audit.result_id)
        if request is None or result is None:
            raise ValueError("execution audit request and result must be persisted")
        if (
            audit.plan_id != request.plan_id
            or audit.candidate_id != request.candidate_id
            or audit.evaluation_run_key != request.evaluation_run_key
            or audit.adapter_kind is not request.adapter_kind
            or audit.adapter_version != request.adapter_version
            or audit.deterministic_seed != request.deterministic_seed
            or audit.environment_identity != request.environment_identity
            or audit.input_artifact_refs != request.input_artifact_refs
        ):
            raise ValueError("execution audit does not exactly match request")
        if (
            result.plan_id != request.plan_id
            or result.candidate_id != request.candidate_id
            or result.evaluation_run_key != request.evaluation_run_key
        ):
            raise ValueError("execution audit result linkage does not match request")
        expected_digest = hashlib.sha256(canonical_record_bytes(result)).hexdigest()
        if audit.result_artifact_sha256 != expected_digest:
            raise ValueError("execution audit result artifact digest mismatch")
        payload = _payload(audit)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM evaluation_execution_audits WHERE request_id = ?",
                (audit.request_id,),
            ).fetchone()
            if existing is not None:
                stored = EvaluationExecutionAudit.model_validate_json(existing["record_json"])
                if stored.audit_id == audit.audit_id:
                    return False
                raise ValueError("completed execution audit already exists for request")
            connection.execute(
                """
                INSERT INTO evaluation_execution_audits(
                    audit_id, request_id, result_id, plan_id, candidate_id,
                    evaluation_run_key, adapter_kind, adapter_version, deterministic_seed,
                    environment_identity, result_artifact_sha256, status, started_at,
                    completed_at, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.audit_id,
                    audit.request_id,
                    audit.result_id,
                    audit.plan_id,
                    audit.candidate_id,
                    audit.evaluation_run_key,
                    audit.adapter_kind.value,
                    audit.adapter_version,
                    audit.deterministic_seed,
                    audit.environment_identity,
                    audit.result_artifact_sha256,
                    audit.status.value,
                    audit.started_at.isoformat(),
                    audit.completed_at.isoformat(),
                    audit.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def audit(self, request_id: str) -> EvaluationExecutionAudit | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM evaluation_execution_audits WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return (
            None
            if row is None
            else EvaluationExecutionAudit.model_validate_json(row["record_json"])
        )

    def audits(self) -> tuple[EvaluationExecutionAudit, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM evaluation_execution_audits ORDER BY audit_sequence"
            ).fetchall()
        return tuple(
            EvaluationExecutionAudit.model_validate_json(row["record_json"]) for row in rows
        )

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
