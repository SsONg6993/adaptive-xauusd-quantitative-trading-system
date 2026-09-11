"""Append-only SQLite persistence for deterministic paired evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

from axq.database import Database
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.paired_evaluation_contracts import (
    PairedEvaluationAudit,
    PairedEvaluationRequest,
    PairedEvaluationResult,
)
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.shared_kernel_candidate_store import SQLiteSharedKernelCandidateStore
from axq.replay_validation import default_shared_kernel_policy_set
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


def _payload(record: BaseModel) -> str:
    return canonical_record_bytes(record).decode("ascii")


class SQLitePairedEvaluationStore:
    """Persist exact comparison requests, results, and terminal audits."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)
        self._evaluations = SQLiteProposalEvaluationStore(self.path)
        self._proposals = SQLiteImprovementProposalStore(self.path)
        self._shared = SQLiteSharedKernelCandidateStore(self.path)

    def append_request(self, request: PairedEvaluationRequest) -> bool:
        request = PairedEvaluationRequest.model_validate(request.model_dump())
        existing = self.request(request.request_id)
        if existing is not None:
            return False
        proposal = self._proposals.proposal(request.proposal_id)
        candidate = self._evaluations.candidate(request.candidate_id)
        plan = self._evaluations.plan(request.plan_id)
        config = self._shared.config(request.candidate_config_id)
        if proposal is None or candidate is None or plan is None or config is None:
            raise ValueError("paired evaluation authoritative records are missing")
        if self._proposals.current_status(proposal.proposal_id) is not ProposalStatus.CANDIDATE:
            raise ValueError("paired evaluation requires current CANDIDATE status")
        baseline = default_shared_kernel_policy_set()
        if (
            plan.proposal_id != proposal.proposal_id
            or candidate.proposal_id != proposal.proposal_id
            or plan.candidate_id != candidate.candidate_id
            or request.candidate_id != candidate.candidate_id
            or request.plan_id != plan.plan_id
            or request.baseline_policy_set_id != baseline.policy_set_id
            or config.base_policy_set_id != baseline.policy_set_id
            or config.proposal_id != proposal.proposal_id
            or config.proposal_key != proposal.proposal_key
            or config.target_component is not candidate.target_component
            or candidate.config_identity != config.config_id
            or candidate.source_identity != config.source_identity
            or not any(
                ref.semantic_id == config.config_id
                and ref.sha256
                == hashlib.sha256(canonical_record_bytes(config)).hexdigest()
                for ref in candidate.artifact_refs
            )
            or request.deterministic_seed != plan.deterministic_seed
            or request.environment_identity != plan.environment_identity
        ):
            raise ValueError("paired evaluation authoritative linkage mismatch")
        for ref in (*request.baseline_artifact_refs, *request.candidate_artifact_refs):
            manifest = self._shared.manifest(ref.manifest_ref.semantic_id)
            if (
                manifest is None
                or manifest.proposal_id != request.proposal_id
                or manifest.candidate_id != request.candidate_id
                or manifest.plan_id != request.plan_id
                or hashlib.sha256(canonical_record_bytes(manifest)).hexdigest()
                != ref.manifest_ref.sha256
            ):
                raise ValueError("paired evaluation authoritative manifest linkage mismatch")
        payload = _payload(request)
        with self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO paired_evaluation_requests(
                    request_id, proposal_id, candidate_id, plan_id, baseline_policy_set_id,
                    candidate_config_id, evaluation_run_key, adapter_kind, adapter_version,
                    deterministic_seed, environment_identity, requested_at, schema_version,
                    payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    request.proposal_id,
                    request.candidate_id,
                    request.plan_id,
                    request.baseline_policy_set_id,
                    request.candidate_config_id,
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
            for side, refs in (
                ("BASELINE", request.baseline_artifact_refs),
                ("CANDIDATE", request.candidate_artifact_refs),
            ):
                connection.executemany(
                    """
                    INSERT INTO paired_evaluation_input_refs(
                        request_id, side, scope, artifact_id, artifact_sha256, manifest_id,
                        manifest_sha256, policy_identity, deterministic_seed, environment_identity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (
                            request.request_id,
                            side,
                            ref.scope.value,
                            ref.semantic_id,
                            ref.sha256,
                            ref.manifest_ref.semantic_id,
                            ref.manifest_ref.sha256,
                            ref.policy_identity,
                            ref.deterministic_seed,
                            ref.environment_identity,
                        )
                        for ref in refs
                    ),
                )
        return True

    def request(self, request_id: str) -> PairedEvaluationRequest | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM paired_evaluation_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return (
            None
            if row is None
            else PairedEvaluationRequest.model_validate_json(row["record_json"])
        )

    def requests(self) -> tuple[PairedEvaluationRequest, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM paired_evaluation_requests ORDER BY request_sequence"
            ).fetchall()
        return tuple(
            PairedEvaluationRequest.model_validate_json(row["record_json"])
            for row in rows
        )

    def append_result(self, result: PairedEvaluationResult) -> bool:
        result = PairedEvaluationResult.model_validate(result.model_dump())
        request = self.request(result.request_id)
        plan = self._evaluations.plan(result.plan_id)
        if request is None or plan is None:
            raise ValueError("paired evaluation result authorities are missing")
        if (
            result.proposal_id != request.proposal_id
            or result.candidate_id != request.candidate_id
            or result.plan_id != request.plan_id
            or {item.metric_key for item in result.metric_comparisons}
            != {item.metric_key for item in plan.metrics}
            or {item.criterion_id for item in result.criterion_outcomes}
            != {item.criterion_id for item in plan.criteria}
        ):
            raise ValueError("paired evaluation result linkage mismatch")
        existing = self.result(request.request_id)
        if existing is not None:
            if existing == result:
                return False
            raise ValueError("completed paired evaluation result already exists")
        payload = _payload(result)
        with self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO paired_evaluation_results(
                    result_id, request_id, available_at, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.result_id,
                    result.request_id,
                    result.available_at.isoformat(),
                    result.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def result(self, request_id: str) -> PairedEvaluationResult | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM paired_evaluation_results WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return (
            None
            if row is None
            else PairedEvaluationResult.model_validate_json(row["record_json"])
        )

    def results(self) -> tuple[PairedEvaluationResult, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM paired_evaluation_results ORDER BY result_sequence"
            ).fetchall()
        return tuple(PairedEvaluationResult.model_validate_json(row["record_json"]) for row in rows)

    def append_audit(self, audit: PairedEvaluationAudit) -> bool:
        audit = PairedEvaluationAudit.model_validate(audit.model_dump())
        request = self.request(audit.request_id)
        result = self.result(audit.request_id)
        if request is None or result is None:
            raise ValueError("paired evaluation audit authorities are missing")
        expected_digest = hashlib.sha256(canonical_record_bytes(result)).hexdigest()
        if (
            audit.result_id != result.result_id
            or audit.proposal_id != request.proposal_id
            or audit.candidate_id != request.candidate_id
            or audit.plan_id != request.plan_id
            or audit.baseline_policy_set_id != request.baseline_policy_set_id
            or audit.candidate_config_id != request.candidate_config_id
            or audit.deterministic_seed != request.deterministic_seed
            or audit.environment_identity != request.environment_identity
            or audit.result_sha256 != expected_digest
        ):
            raise ValueError("paired evaluation audit linkage mismatch")
        existing = self.audit(request.request_id)
        if existing is not None:
            if existing == audit:
                return False
            raise ValueError("completed paired evaluation audit already exists")
        payload = _payload(audit)
        with self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO paired_evaluation_audits(
                    audit_id, request_id, result_id, status, started_at, completed_at,
                    schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.audit_id,
                    audit.request_id,
                    audit.result_id,
                    audit.status.value,
                    audit.started_at.isoformat(),
                    audit.completed_at.isoformat(),
                    audit.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def audit(self, request_id: str) -> PairedEvaluationAudit | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM paired_evaluation_audits WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return (
            None
            if row is None
            else PairedEvaluationAudit.model_validate_json(row["record_json"])
        )

    def audits(self) -> tuple[PairedEvaluationAudit, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM paired_evaluation_audits ORDER BY audit_sequence"
            ).fetchall()
        return tuple(PairedEvaluationAudit.model_validate_json(row["record_json"]) for row in rows)

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
