"""Governed, idempotent shared-kernel candidate execution service."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import CanonicalMetricSampleArtifact
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.shared_kernel_candidate_contracts import (
    FrozenSharedKernelCandidateConfig,
    SharedKernelCandidateAudit,
    SharedKernelCandidateRequest,
    SharedKernelMetricArtifactRef,
    SharedKernelReplayDataManifest,
)
from axq.reflection.shared_kernel_candidate_engine import (
    SharedKernelCandidateEngine,
    SharedKernelMasterFusionEngineV1,
)
from axq.reflection.shared_kernel_candidate_store import SQLiteSharedKernelCandidateStore
from axq.runtime.state import UTCDateTime


@dataclass(frozen=True)
class SharedKernelCandidateOutcome:
    request: SharedKernelCandidateRequest
    artifacts: tuple[CanonicalMetricSampleArtifact, ...]
    artifact_bytes: tuple[bytes, ...]
    audit: SharedKernelCandidateAudit
    reused: bool


def _output_refs(
    artifacts: tuple[CanonicalMetricSampleArtifact, ...],
) -> tuple[SharedKernelMetricArtifactRef, ...]:
    return tuple(
        SharedKernelMetricArtifactRef(
            scope=item.scope,
            semantic_id=item.artifact_id,
            sha256=hashlib.sha256(canonical_record_bytes(item)).hexdigest(),
        )
        for item in artifacts
    )


def execute_shared_kernel_candidate(
    store_path: str | Path,
    request: SharedKernelCandidateRequest,
    config: FrozenSharedKernelCandidateConfig,
    manifests: tuple[SharedKernelReplayDataManifest, ...],
    data_directories: Mapping[MetricScope, Path],
    output_directory: Path,
    *,
    started_at: UTCDateTime,
    completed_at: UTCDateTime,
    engine: SharedKernelCandidateEngine | None = None,
) -> SharedKernelCandidateOutcome:
    """Execute or recover one exact frozen candidate against the shared replay kernel."""
    store = SQLiteSharedKernelCandidateStore(store_path)
    store.append_config(config)
    for manifest in manifests:
        store.append_manifest(manifest)
    store.append_request(request)
    stored_request = store.request(request.request_id)
    if stored_request is None:
        raise ValueError("shared-kernel candidate request was not persisted")
    existing_audit = store.audit(stored_request.request_id)
    if existing_audit is not None:
        artifacts = store.artifacts(stored_request.request_id)
        payloads = tuple(canonical_record_bytes(item) for item in artifacts)
        if (
            _output_refs(artifacts) != existing_audit.output_artifact_refs
            or store.replay_refs(stored_request.request_id) != existing_audit.replay_result_refs
        ):
            raise ValueError("completed shared-kernel candidate output digest mismatch")
        return SharedKernelCandidateOutcome(
            request=stored_request,
            artifacts=artifacts,
            artifact_bytes=payloads,
            audit=existing_audit,
            reused=True,
        )
    proposals = SQLiteImprovementProposalStore(store_path)
    evaluations = SQLiteProposalEvaluationStore(store_path)
    proposal = proposals.proposal(stored_request.proposal_id)
    candidate = evaluations.candidate(stored_request.candidate_id)
    plan = evaluations.plan(stored_request.plan_id)
    stored_config = store.config(stored_request.config_ref.semantic_id)
    stored_manifests = tuple(
        store.manifest(item.semantic_id) for item in stored_request.data_manifest_refs
    )
    if (
        proposal is None
        or candidate is None
        or plan is None
        or stored_config is None
        or any(item is None for item in stored_manifests)
    ):
        raise ValueError("shared-kernel authoritative records are missing")
    if proposals.current_status(proposal.proposal_id) is not ProposalStatus.CANDIDATE:
        raise ValueError("shared-kernel execution requires current CANDIDATE status")
    selected = SharedKernelMasterFusionEngineV1() if engine is None else engine
    if (
        selected.kind is not stored_request.engine_kind
        or selected.version != stored_request.engine_version
    ):
        raise ValueError("shared-kernel candidate engine is not allowlisted by the request")
    typed_manifests = tuple(item for item in stored_manifests if item is not None)
    output = selected.execute(
        stored_request,
        proposal,
        candidate,
        plan,
        stored_config,
        typed_manifests,
        data_directories,
        output_directory,
    )
    store.append_outputs(stored_request.request_id, output.artifacts, output.replay_result_refs)
    audit = SharedKernelCandidateAudit(
        request_id=stored_request.request_id,
        proposal_id=stored_request.proposal_id,
        candidate_id=stored_request.candidate_id,
        plan_id=stored_request.plan_id,
        config_ref=stored_request.config_ref,
        data_manifest_refs=stored_request.data_manifest_refs,
        replay_result_refs=output.replay_result_refs,
        output_artifact_refs=_output_refs(output.artifacts),
        evaluation_run_key=stored_request.evaluation_run_key,
        engine_kind=stored_request.engine_kind,
        engine_version=stored_request.engine_version,
        deterministic_seed=stored_request.deterministic_seed,
        environment_identity=stored_request.environment_identity,
        started_at=started_at,
        completed_at=completed_at,
    )
    store.append_audit(audit)
    store.sync()
    return SharedKernelCandidateOutcome(
        request=stored_request,
        artifacts=output.artifacts,
        artifact_bytes=output.artifact_bytes,
        audit=audit,
        reused=False,
    )
