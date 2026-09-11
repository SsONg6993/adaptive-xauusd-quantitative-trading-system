"""Append-only persistence for shared-kernel candidate evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

from axq.database import Database
from axq.reflection.evaluation_contracts import CandidateKind, MetricScope, SemanticArtifactRef
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import CanonicalMetricSampleArtifact
from axq.reflection.proposal_contracts import ProposalStatus, ProposalTargetComponent
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.shared_kernel_candidate_contracts import (
    FrozenSharedKernelCandidateConfig,
    SharedKernelCandidateAudit,
    SharedKernelCandidateRequest,
    SharedKernelMetricArtifactRef,
    SharedKernelReplayDataManifest,
    SharedKernelReplayResultRef,
)
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


def _payload(record: BaseModel) -> str:
    return canonical_record_bytes(record).decode("ascii")


class SQLiteSharedKernelCandidateStore:
    """Persist frozen configs, manifests, requests, outputs, and terminal audits."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)
        self._evaluations = SQLiteProposalEvaluationStore(self.path)
        self._proposals = SQLiteImprovementProposalStore(self.path)

    def append_config(self, config: FrozenSharedKernelCandidateConfig) -> bool:
        config = FrozenSharedKernelCandidateConfig.model_validate(config.model_dump())
        payload = _payload(config)
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT record_json FROM shared_kernel_candidate_configs WHERE config_id = ?",
                (config.config_id,),
            ).fetchone()
            if row is not None:
                if str(row["record_json"]) == payload:
                    return False
                raise ValueError("shared-kernel candidate config ID conflict")
            connection.execute(
                """
                INSERT INTO shared_kernel_candidate_configs(
                    config_id, proposal_id, target_component, schema_version,
                    payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    config.config_id,
                    config.proposal_id,
                    config.target_component.value,
                    config.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def config(self, config_id: str) -> FrozenSharedKernelCandidateConfig | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM shared_kernel_candidate_configs WHERE config_id = ?",
                (config_id,),
            ).fetchone()
        return (
            None
            if row is None
            else FrozenSharedKernelCandidateConfig.model_validate_json(row["record_json"])
        )

    def append_manifest(self, manifest: SharedKernelReplayDataManifest) -> bool:
        manifest = SharedKernelReplayDataManifest.model_validate(manifest.model_dump())
        payload = _payload(manifest)
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT record_json FROM shared_kernel_data_manifests WHERE manifest_id = ?",
                (manifest.manifest_id,),
            ).fetchone()
            if row is not None:
                if str(row["record_json"]) == payload:
                    return False
                raise ValueError("shared-kernel data manifest ID conflict")
            connection.execute(
                """
                INSERT INTO shared_kernel_data_manifests(
                    manifest_id, proposal_id, candidate_id, plan_id, scope, available_at,
                    schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.manifest_id,
                    manifest.proposal_id,
                    manifest.candidate_id,
                    manifest.plan_id,
                    manifest.scope.value,
                    manifest.available_at.isoformat(),
                    manifest.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def manifest(self, manifest_id: str) -> SharedKernelReplayDataManifest | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM shared_kernel_data_manifests WHERE manifest_id = ?",
                (manifest_id,),
            ).fetchone()
        return (
            None
            if row is None
            else SharedKernelReplayDataManifest.model_validate_json(row["record_json"])
        )

    def append_request(self, request: SharedKernelCandidateRequest) -> bool:
        request = SharedKernelCandidateRequest.model_validate(request.model_dump())
        if self.request(request.request_id) is not None:
            return False
        proposal = self._proposals.proposal(request.proposal_id)
        candidate = self._evaluations.candidate(request.candidate_id)
        plan = self._evaluations.plan(request.plan_id)
        config = self.config(request.config_ref.semantic_id)
        manifests = tuple(self.manifest(item.semantic_id) for item in request.data_manifest_refs)
        if (
            proposal is None
            or candidate is None
            or plan is None
            or config is None
            or any(item is None for item in manifests)
        ):
            raise ValueError("shared-kernel authoritative records must be persisted")
        if self._proposals.current_status(proposal.proposal_id) is not ProposalStatus.CANDIDATE:
            raise ValueError("shared-kernel execution requires current CANDIDATE status")
        config_ref = SemanticArtifactRef(
            semantic_id=config.config_id,
            sha256=hashlib.sha256(canonical_record_bytes(config)).hexdigest(),
        )
        required_scopes = {
            item.scope for item in plan.metrics if item.scope is not MetricScope.FINAL_OOS
        }
        typed_manifests = tuple(item for item in manifests if item is not None)
        if (
            candidate.candidate_kind is not CandidateKind.CONFIGURATION
            or candidate.target_component is not ProposalTargetComponent.MASTER_FUSION
            or candidate.config_identity != config.config_id
            or candidate.source_identity != config.source_identity
            or config.proposal_id != proposal.proposal_id
            or request.config_ref != config_ref
            or config_ref not in candidate.artifact_refs
            or plan.proposal_id != proposal.proposal_id
            or plan.candidate_id != candidate.candidate_id
            or request.plan_id != plan.plan_id
            or request.deterministic_seed != plan.deterministic_seed
            or request.environment_identity != plan.environment_identity
            or {item.scope for item in request.data_manifest_refs} != required_scopes
        ):
            raise ValueError("shared-kernel authoritative linkage mismatch")
        by_scope = {item.scope: item for item in typed_manifests}
        for reference in request.data_manifest_refs:
            manifest = by_scope[reference.scope]
            if (
                manifest.proposal_id != request.proposal_id
                or manifest.candidate_id != request.candidate_id
                or manifest.plan_id != request.plan_id
                or reference.sha256
                != hashlib.sha256(canonical_record_bytes(manifest)).hexdigest()
            ):
                raise ValueError("shared-kernel data manifest linkage mismatch")
        payload = _payload(request)
        with self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO shared_kernel_candidate_requests(
                    request_id, proposal_id, candidate_id, plan_id, config_id,
                    evaluation_run_key, engine_kind, engine_version, deterministic_seed,
                    environment_identity, requested_at, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    request.proposal_id,
                    request.candidate_id,
                    request.plan_id,
                    request.config_ref.semantic_id,
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
                INSERT INTO shared_kernel_candidate_input_refs(
                    request_id, scope, manifest_id, sha256
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    (request.request_id, item.scope.value, item.semantic_id, item.sha256)
                    for item in request.data_manifest_refs
                ),
            )
        return True

    def request(self, request_id: str) -> SharedKernelCandidateRequest | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM shared_kernel_candidate_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return (
            None
            if row is None
            else SharedKernelCandidateRequest.model_validate_json(row["record_json"])
        )

    def requests(self) -> tuple[SharedKernelCandidateRequest, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM shared_kernel_candidate_requests ORDER BY request_sequence"
            ).fetchall()
        return tuple(
            SharedKernelCandidateRequest.model_validate_json(row["record_json"])
            for row in rows
        )

    def append_outputs(
        self,
        request_id: str,
        artifacts: tuple[CanonicalMetricSampleArtifact, ...],
        replay_refs: tuple[SharedKernelReplayResultRef, ...],
    ) -> bool:
        request = self.request(request_id)
        if request is None:
            raise ValueError("shared-kernel request must precede outputs")
        artifacts = tuple(sorted(artifacts, key=lambda item: item.scope.value))
        replay_refs = tuple(sorted(replay_refs, key=lambda item: item.scope.value))
        scopes = {item.scope for item in request.data_manifest_refs}
        if (
            len({item.scope for item in artifacts}) != len(artifacts)
            or len({item.scope for item in replay_refs}) != len(replay_refs)
            or {item.scope for item in artifacts} != scopes
            or {item.scope for item in replay_refs} != scopes
        ):
            raise ValueError("shared-kernel output scopes do not match request")
        plan = self._evaluations.plan(request.plan_id)
        if plan is None:
            raise ValueError("shared-kernel plan is missing")
        inserted = False
        with self._database.transaction() as connection:
            for replay_ref in replay_refs:
                row = connection.execute(
                    """
                    SELECT semantic_id, sha256 FROM shared_kernel_candidate_replay_results
                    WHERE request_id = ? AND scope = ?
                    """,
                    (request_id, replay_ref.scope.value),
                ).fetchone()
                if row is None:
                    connection.execute(
                        """
                        INSERT INTO shared_kernel_candidate_replay_results(
                            request_id, scope, semantic_id, sha256
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            request_id,
                            replay_ref.scope.value,
                            replay_ref.semantic_id,
                            replay_ref.sha256,
                        ),
                    )
                    inserted = True
                elif (
                    row["semantic_id"] != replay_ref.semantic_id
                    or row["sha256"] != replay_ref.sha256
                ):
                    raise ValueError("shared-kernel request has conflicting replay result")
            for artifact in artifacts:
                expected_keys = {
                    item.metric_key for item in plan.metrics if item.scope is artifact.scope
                }
                if {item.metric_key for item in artifact.series} != expected_keys:
                    raise ValueError("shared-kernel artifact metrics do not match plan")
                payload = _payload(artifact)
                digest = hashlib.sha256(canonical_record_bytes(artifact)).hexdigest()
                existing = connection.execute(
                    """
                    SELECT record_json FROM shared_kernel_candidate_artifacts
                    WHERE artifact_id = ?
                    """,
                    (artifact.artifact_id,),
                ).fetchone()
                if existing is None:
                    connection.execute(
                        """
                        INSERT INTO shared_kernel_candidate_artifacts(
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
                    raise ValueError("shared-kernel artifact ID conflict")
                link = connection.execute(
                    """
                    SELECT artifact_id, sha256 FROM shared_kernel_candidate_output_refs
                    WHERE request_id = ? AND scope = ?
                    """,
                    (request_id, artifact.scope.value),
                ).fetchone()
                if link is None:
                    connection.execute(
                        """
                        INSERT INTO shared_kernel_candidate_output_refs(
                            request_id, scope, artifact_id, sha256
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (request_id, artifact.scope.value, artifact.artifact_id, digest),
                    )
                    inserted = True
                elif link["artifact_id"] != artifact.artifact_id or link["sha256"] != digest:
                    raise ValueError("shared-kernel request has conflicting artifact")
        return inserted

    def artifacts(self, request_id: str) -> tuple[CanonicalMetricSampleArtifact, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT artifact.record_json
                FROM shared_kernel_candidate_output_refs AS output
                JOIN shared_kernel_candidate_artifacts AS artifact
                  ON artifact.artifact_id = output.artifact_id
                WHERE output.request_id = ? ORDER BY output.scope
                """,
                (request_id,),
            ).fetchall()
        return tuple(
            CanonicalMetricSampleArtifact.model_validate_json(row["record_json"])
            for row in rows
        )

    def replay_refs(self, request_id: str) -> tuple[SharedKernelReplayResultRef, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT scope, semantic_id, sha256
                FROM shared_kernel_candidate_replay_results
                WHERE request_id = ? ORDER BY scope
                """,
                (request_id,),
            ).fetchall()
        return tuple(
            SharedKernelReplayResultRef(
                scope=MetricScope(row["scope"]),
                semantic_id=row["semantic_id"],
                sha256=row["sha256"],
            )
            for row in rows
        )

    def append_audit(self, audit: SharedKernelCandidateAudit) -> bool:
        audit = SharedKernelCandidateAudit.model_validate(audit.model_dump())
        request = self.request(audit.request_id)
        artifacts = self.artifacts(audit.request_id)
        replay_refs = self.replay_refs(audit.request_id)
        if request is None or not artifacts or not replay_refs:
            raise ValueError("shared-kernel request and outputs must precede audit")
        output_refs = tuple(
            SharedKernelMetricArtifactRef(
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
            or audit.config_ref != request.config_ref
            or audit.data_manifest_refs != request.data_manifest_refs
            or audit.replay_result_refs != replay_refs
            or audit.output_artifact_refs != output_refs
            or audit.evaluation_run_key != request.evaluation_run_key
            or audit.engine_kind is not request.engine_kind
            or audit.engine_version != request.engine_version
            or audit.deterministic_seed != request.deterministic_seed
            or audit.environment_identity != request.environment_identity
        ):
            raise ValueError("shared-kernel audit does not exactly match request and outputs")
        payload = _payload(audit)
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT record_json FROM shared_kernel_candidate_audits WHERE request_id = ?",
                (audit.request_id,),
            ).fetchone()
            if row is not None:
                stored = SharedKernelCandidateAudit.model_validate_json(row["record_json"])
                if stored.audit_id == audit.audit_id:
                    return False
                raise ValueError("completed shared-kernel candidate audit already exists")
            connection.execute(
                """
                INSERT INTO shared_kernel_candidate_audits(
                    audit_id, request_id, status, started_at, completed_at,
                    schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.audit_id,
                    audit.request_id,
                    audit.status.value,
                    audit.started_at.isoformat(),
                    audit.completed_at.isoformat(),
                    audit.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def audit(self, request_id: str) -> SharedKernelCandidateAudit | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM shared_kernel_candidate_audits WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        return (
            None
            if row is None
            else SharedKernelCandidateAudit.model_validate_json(row["record_json"])
        )

    def audits(self) -> tuple[SharedKernelCandidateAudit, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM shared_kernel_candidate_audits ORDER BY audit_sequence"
            ).fetchall()
        return tuple(
            SharedKernelCandidateAudit.model_validate_json(row["record_json"])
            for row in rows
        )

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
