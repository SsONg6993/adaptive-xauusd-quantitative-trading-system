"""Idempotent orchestration for deterministic paired evaluation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from axq.reflection.evaluation_contracts import ProposalEvaluationPlan
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import CanonicalMetricSampleArtifact
from axq.reflection.paired_evaluation import PairedEvaluationOutput, compare_paired_evidence
from axq.reflection.paired_evaluation_contracts import (
    PairedEvaluationAudit,
    PairedEvaluationRequest,
    PairedEvaluationResult,
)
from axq.reflection.paired_evaluation_store import SQLitePairedEvaluationStore
from axq.runtime.state import UTCDateTime


class PairedEvaluationAdapter(Protocol):
    def execute(
        self,
        request: PairedEvaluationRequest,
        plan: ProposalEvaluationPlan,
        baseline_artifacts: tuple[CanonicalMetricSampleArtifact, ...],
        candidate_artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    ) -> PairedEvaluationOutput: ...


class CanonicalPairedEvaluationAdapter:
    def execute(
        self,
        request: PairedEvaluationRequest,
        plan: ProposalEvaluationPlan,
        baseline_artifacts: tuple[CanonicalMetricSampleArtifact, ...],
        candidate_artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    ) -> PairedEvaluationOutput:
        return compare_paired_evidence(request, plan, baseline_artifacts, candidate_artifacts)


@dataclass(frozen=True)
class PairedEvaluationServiceOutcome:
    request: PairedEvaluationRequest
    result: PairedEvaluationResult
    result_bytes: bytes
    audit: PairedEvaluationAudit
    reused: bool


def execute_paired_evaluation(
    store_path: str | Path,
    request: PairedEvaluationRequest,
    baseline_artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    candidate_artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    *,
    started_at: UTCDateTime,
    completed_at: UTCDateTime,
    adapter: PairedEvaluationAdapter | None = None,
) -> PairedEvaluationServiceOutcome:
    """Compare or recover one exact paired-evaluation request."""

    store = SQLitePairedEvaluationStore(store_path)
    store.append_request(request)
    stored_request = store.request(request.request_id)
    if stored_request is None:
        raise ValueError("paired evaluation request was not persisted")
    existing_audit = store.audit(stored_request.request_id)
    if existing_audit is not None:
        result = store.result(stored_request.request_id)
        if result is None:
            raise ValueError("completed paired evaluation result is missing")
        payload = canonical_record_bytes(result)
        if hashlib.sha256(payload).hexdigest() != existing_audit.result_sha256:
            raise ValueError("completed paired evaluation result digest mismatch")
        return PairedEvaluationServiceOutcome(
            request=stored_request,
            result=result,
            result_bytes=payload,
            audit=existing_audit,
            reused=True,
        )
    plan = SQLiteProposalEvaluationStore(store_path).plan(stored_request.plan_id)
    if plan is None:
        raise ValueError("paired evaluation plan is missing")
    selected = CanonicalPairedEvaluationAdapter() if adapter is None else adapter
    output = selected.execute(
        stored_request,
        plan,
        baseline_artifacts,
        candidate_artifacts,
    )
    store.append_result(output.result)
    digest = hashlib.sha256(output.result_bytes).hexdigest()
    audit = PairedEvaluationAudit(
        request_id=stored_request.request_id,
        result_id=output.result.result_id,
        proposal_id=stored_request.proposal_id,
        candidate_id=stored_request.candidate_id,
        plan_id=stored_request.plan_id,
        baseline_policy_set_id=stored_request.baseline_policy_set_id,
        candidate_config_id=stored_request.candidate_config_id,
        deterministic_seed=stored_request.deterministic_seed,
        environment_identity=stored_request.environment_identity,
        result_sha256=digest,
        started_at=started_at,
        completed_at=completed_at,
    )
    store.append_audit(audit)
    store.sync()
    return PairedEvaluationServiceOutcome(
        request=stored_request,
        result=output.result,
        result_bytes=output.result_bytes,
        audit=audit,
        reused=False,
    )
