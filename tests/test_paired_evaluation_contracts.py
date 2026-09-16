from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.reflection.evaluation_contracts import CriterionRole, MetricScope
from axq.reflection.paired_evaluation_contracts import (
    PairedArtifactRef,
    PairedCriterionOutcome,
    PairedCriterionStatus,
    PairedEvaluationAudit,
    PairedEvaluationRequest,
    PairedEvaluationResult,
    PairedMetricComparison,
    PairedMetricStatus,
    PairedParityCheck,
    PairedParityStatus,
)
from axq.reflection.shared_kernel_candidate_contracts import SharedKernelDataManifestRef

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=UTC)


def test_paired_contracts_are_exported_from_reflection_package() -> None:
    from axq.reflection import PairedEvaluationRequest as ExportedRequest

    assert ExportedRequest is PairedEvaluationRequest


def _manifest(scope: MetricScope) -> SharedKernelDataManifestRef:
    return SharedKernelDataManifestRef(
        scope=scope,
        semantic_id=f"manifest-{scope.value.lower()}",
        sha256=("a" if scope is MetricScope.DEVELOPMENT else "b") * 64,
    )


def _artifact(scope: MetricScope, policy: str, marker: str) -> PairedArtifactRef:
    return PairedArtifactRef(
        scope=scope,
        semantic_id=f"artifact-{marker}-{scope.value.lower()}",
        sha256=marker * 64,
        manifest_ref=_manifest(scope),
        policy_identity=policy,
        deterministic_seed=1729,
        environment_identity="python-lock-v1",
    )


def _request(requested_at: datetime = NOW) -> PairedEvaluationRequest:
    baseline = "shared-kernel-policy-baseline"
    candidate = "frozen-shared-kernel-config-candidate"
    return PairedEvaluationRequest(
        proposal_id="proposal-1",
        candidate_id="candidate-1",
        plan_id="plan-1",
        baseline_policy_set_id=baseline,
        candidate_config_id=candidate,
        baseline_artifact_refs=(_artifact(MetricScope.VALIDATION, baseline, "c"),),
        candidate_artifact_refs=(_artifact(MetricScope.VALIDATION, candidate, "d"),),
        evaluation_run_key="paired-controlled-v1",
        deterministic_seed=1729,
        environment_identity="python-lock-v1",
        requested_at=requested_at,
    )


def test_request_identity_excludes_operational_timestamp_and_is_immutable() -> None:
    first = _request()
    later = _request(NOW + timedelta(days=1))

    assert first.request_id == later.request_id
    with pytest.raises(ValidationError):
        first.environment_identity = "changed"  # type: ignore[misc]


def test_request_rejects_naive_time_and_final_oos_input() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        _request(datetime(2026, 9, 11, 12, 0))
    with pytest.raises(ValidationError, match="Final OOS"):
        forbidden_manifest = _manifest(MetricScope.VALIDATION).model_copy(
            update={"scope": MetricScope.FINAL_OOS}
        )
        PairedArtifactRef(
            scope=MetricScope.FINAL_OOS,
            semantic_id="forbidden",
            sha256="f" * 64,
            manifest_ref=forbidden_manifest,
            policy_identity="forbidden",
            deterministic_seed=1729,
            environment_identity="python-lock-v1",
        )


def test_metric_comparison_requires_canonical_decimal_and_consistent_availability() -> None:
    available = PairedMetricComparison(
        metric_id="metric-1",
        metric_key="validation_expectancy",
        scope=MetricScope.VALIDATION,
        status=PairedMetricStatus.AVAILABLE,
        baseline_value="0.1",
        candidate_value="0.3",
        delta="0.2",
        baseline_sample_count=2,
        candidate_sample_count=2,
        baseline_artifact_ref=_artifact(
            MetricScope.VALIDATION, "shared-kernel-policy-baseline", "c"
        ),
        candidate_artifact_ref=_artifact(
            MetricScope.VALIDATION, "frozen-shared-kernel-config-candidate", "d"
        ),
    )
    assert available.delta == "0.2"

    with pytest.raises(ValidationError, match="canonical decimal"):
        PairedMetricComparison(**(available.model_dump() | {"delta": "0.200"}))


def test_result_and_audit_have_content_identity_with_audit_times_excluded() -> None:
    request = _request()
    parity = PairedParityCheck(
        check_key="EXACT_MANIFEST_PARITY",
        status=PairedParityStatus.PASS,
    )
    comparison = PairedMetricComparison(
        metric_id="metric-1",
        metric_key="validation_expectancy",
        scope=MetricScope.VALIDATION,
        status=PairedMetricStatus.UNAVAILABLE,
        baseline_value=None,
        candidate_value=None,
        delta=None,
        baseline_sample_count=0,
        candidate_sample_count=0,
        reason_code="PAIR_EVIDENCE_UNAVAILABLE",
    )
    outcome = PairedCriterionOutcome(
        criterion_id="criterion-1",
        metric_key=comparison.metric_key,
        role=CriterionRole.DECISION,
        status=PairedCriterionStatus.UNAVAILABLE,
        comparison_id=comparison.comparison_id,
        reason_code="PAIR_EVIDENCE_UNAVAILABLE",
    )
    result = PairedEvaluationResult(
        request_id=request.request_id,
        proposal_id=request.proposal_id,
        candidate_id=request.candidate_id,
        plan_id=request.plan_id,
        available_at=NOW,
        parity_checks=(parity,),
        metric_comparisons=(comparison,),
        criterion_outcomes=(outcome,),
    )
    kwargs = dict(
        request_id=request.request_id,
        result_id=result.result_id,
        proposal_id=request.proposal_id,
        candidate_id=request.candidate_id,
        plan_id=request.plan_id,
        baseline_policy_set_id=request.baseline_policy_set_id,
        candidate_config_id=request.candidate_config_id,
        deterministic_seed=request.deterministic_seed,
        environment_identity=request.environment_identity,
        result_sha256="f" * 64,
    )
    first = PairedEvaluationAudit(
        **kwargs,
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=1),
    )
    later = PairedEvaluationAudit(
        **kwargs,
        started_at=NOW + timedelta(days=1),
        completed_at=NOW + timedelta(days=1, seconds=1),
    )

    assert first.audit_id == later.audit_id
