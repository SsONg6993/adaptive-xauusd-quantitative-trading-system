"""Deterministic orchestration for one preregistered evaluation request."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from axq.reflection.evaluation_contracts import (
    ProposalEvaluationPlan,
    ProposalEvaluationResult,
)
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import (
    CanonicalMetricSamplesAdapter,
    EvaluationAdapterOutput,
    canonical_record_bytes,
)
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationExecutionAudit,
    EvaluationExecutionRequest,
)
from axq.reflection.execution_store import SQLiteEvaluationExecutionStore
from axq.runtime.state import UTCDateTime


class EvaluationAdapterProtocol(Protocol):
    def execute(
        self,
        request: EvaluationExecutionRequest,
        plan: ProposalEvaluationPlan,
        artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    ) -> EvaluationAdapterOutput: ...


@dataclass(frozen=True)
class EvaluationExecutionOutcome:
    request: EvaluationExecutionRequest
    result: ProposalEvaluationResult
    result_bytes: bytes
    audit: EvaluationExecutionAudit
    reused: bool


def execute_evaluation_request(
    store_path: str | Path,
    request: EvaluationExecutionRequest,
    artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    *,
    started_at: UTCDateTime,
    completed_at: UTCDateTime,
    adapter: EvaluationAdapterProtocol | None = None,
) -> EvaluationExecutionOutcome:
    """Execute or recover one exact deterministic evaluation request."""

    evaluation_store = SQLiteProposalEvaluationStore(store_path)
    execution_store = SQLiteEvaluationExecutionStore(store_path)
    execution_store.append_request(request)
    stored_request = execution_store.request(request.request_id)
    if stored_request is None:
        raise ValueError("execution request was not persisted")
    existing_audit = execution_store.audit(request.request_id)
    if existing_audit is not None:
        result = evaluation_store.result(existing_audit.result_id)
        if result is None:
            raise ValueError("completed execution audit result is missing")
        result_bytes = canonical_record_bytes(result)
        if hashlib.sha256(result_bytes).hexdigest() != existing_audit.result_artifact_sha256:
            raise ValueError("completed execution result artifact digest mismatch")
        return EvaluationExecutionOutcome(
            request=stored_request,
            result=result,
            result_bytes=result_bytes,
            audit=existing_audit,
            reused=True,
        )
    plan = evaluation_store.plan(request.plan_id)
    candidate = evaluation_store.candidate(request.candidate_id)
    if plan is None or candidate is None:
        raise ValueError("execution plan and candidate must be persisted")
    if plan.candidate_id != candidate.candidate_id:
        raise ValueError("execution candidate linkage does not match plan")
    selected_adapter = CanonicalMetricSamplesAdapter() if adapter is None else adapter
    output = selected_adapter.execute(stored_request, plan, artifacts)
    evaluation_store.append_result(output.result)
    result_digest = hashlib.sha256(output.result_bytes).hexdigest()
    audit = EvaluationExecutionAudit(
        request_id=stored_request.request_id,
        result_id=output.result.result_id,
        plan_id=stored_request.plan_id,
        candidate_id=stored_request.candidate_id,
        evaluation_run_key=stored_request.evaluation_run_key,
        adapter_kind=stored_request.adapter_kind,
        adapter_version=stored_request.adapter_version,
        deterministic_seed=stored_request.deterministic_seed,
        environment_identity=stored_request.environment_identity,
        input_artifact_refs=stored_request.input_artifact_refs,
        result_artifact_sha256=result_digest,
        started_at=started_at,
        completed_at=completed_at,
    )
    execution_store.append_audit(audit)
    execution_store.sync()
    evaluation_store.sync()
    return EvaluationExecutionOutcome(
        request=stored_request,
        result=output.result,
        result_bytes=output.result_bytes,
        audit=audit,
        reused=False,
    )
