from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.reflection.evaluation_contracts import (
    MetricObservation,
    MetricObservationStatus,
    MetricScope,
    SemanticArtifactRef,
)
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationAdapterKind,
    EvaluationExecutionAudit,
    EvaluationExecutionRequest,
    EvaluationExecutionStatus,
    ExecutionInputArtifactRef,
    MetricSampleSeries,
)

NOW = datetime(2026, 9, 11, 9, 0, tzinfo=UTC)


def _input_ref(scope: MetricScope = MetricScope.VALIDATION) -> ExecutionInputArtifactRef:
    return ExecutionInputArtifactRef(
        scope=scope,
        semantic_id="validation-samples-v1",
        sha256="a" * 64,
    )


def _request(**changes: object) -> EvaluationExecutionRequest:
    values: dict[str, object] = {
        "plan_id": "proposal-evaluation-plan-1",
        "candidate_id": "evaluation-candidate-1",
        "evaluation_run_key": "controlled-fixture-v1",
        "adapter_kind": EvaluationAdapterKind.CANONICAL_METRIC_SAMPLES_V1,
        "adapter_version": "1.0",
        "deterministic_seed": 1729,
        "environment_identity": "python-3.12-lock-a",
        "input_artifact_refs": (_input_ref(),),
        "requested_at": NOW,
    }
    values.update(changes)
    return EvaluationExecutionRequest(**values)


def _audit(request: EvaluationExecutionRequest, **changes: object) -> EvaluationExecutionAudit:
    values: dict[str, object] = {
        "request_id": request.request_id,
        "result_id": "proposal-evaluation-result-1",
        "plan_id": request.plan_id,
        "candidate_id": request.candidate_id,
        "evaluation_run_key": request.evaluation_run_key,
        "adapter_kind": request.adapter_kind,
        "adapter_version": request.adapter_version,
        "deterministic_seed": request.deterministic_seed,
        "environment_identity": request.environment_identity,
        "input_artifact_refs": request.input_artifact_refs,
        "result_artifact_sha256": "b" * 64,
        "status": EvaluationExecutionStatus.COMPLETED,
        "started_at": NOW,
        "completed_at": NOW + timedelta(seconds=1),
    }
    values.update(changes)
    return EvaluationExecutionAudit(**values)


def test_request_identity_excludes_requested_at_but_requires_strict_utc() -> None:
    first = _request()
    retried = _request(requested_at=NOW + timedelta(days=1))

    assert first.request_id == retried.request_id
    assert first.requested_at != retried.requested_at
    with pytest.raises(ValidationError, match="timezone-aware"):
        _request(requested_at=datetime(2026, 9, 11, 9, 0))
    with pytest.raises(ValidationError, match="request_id does not match"):
        _request(request_id="evaluation-execution-request-tampered")


def test_audit_identity_excludes_operational_timestamps() -> None:
    request = _request()
    first = _audit(request)
    retried = _audit(
        request,
        started_at=NOW + timedelta(days=1),
        completed_at=NOW + timedelta(days=1, seconds=2),
    )

    assert first.audit_id == retried.audit_id
    assert first.started_at != retried.started_at
    with pytest.raises(ValidationError, match="completion"):
        _audit(request, completed_at=NOW - timedelta(seconds=1))


def test_metric_sample_artifact_is_order_invariant_and_rejects_duplicate_keys() -> None:
    first = CanonicalMetricSampleArtifact(
        scope=MetricScope.VALIDATION,
        available_at=NOW,
        series=(
            MetricSampleSeries(metric_key="drawdown", values=(0.2, 0.1)),
            MetricSampleSeries(metric_key="expectancy", values=(0.1, 0.3)),
        ),
    )
    reordered = CanonicalMetricSampleArtifact(
        scope=MetricScope.VALIDATION,
        available_at=NOW,
        series=tuple(reversed(first.series)),
    )

    assert first == reordered
    assert first.artifact_id.startswith("canonical-metric-samples-")
    with pytest.raises(ValidationError, match="series metric keys must be unique"):
        CanonicalMetricSampleArtifact(
            scope=MetricScope.VALIDATION,
            available_at=NOW,
            series=(first.series[0], first.series[0]),
        )


def test_execution_inputs_reject_final_oos_and_bad_digest() -> None:
    with pytest.raises(ValidationError, match="Final OOS"):
        _input_ref(MetricScope.FINAL_OOS)
    with pytest.raises(ValidationError):
        ExecutionInputArtifactRef(
            scope=MetricScope.VALIDATION,
            semantic_id="validation-samples-v1",
            sha256="not-a-digest",
        )


def test_unavailable_observation_requires_explicit_reason_and_zero_samples() -> None:
    evidence = SemanticArtifactRef(semantic_id="withheld", sha256="c" * 64)
    unavailable = MetricObservation(
        metric_key="final_oos_expectancy",
        scope=MetricScope.FINAL_OOS,
        status=MetricObservationStatus.UNAVAILABLE,
        value=None,
        sample_count=0,
        evidence_refs=(evidence,),
        available_at=NOW,
        reason_code="FINAL_OOS_NOT_ACCESSED",
    )
    assert unavailable.reason_code == "FINAL_OOS_NOT_ACCESSED"
    with pytest.raises(ValidationError, match="reason code"):
        MetricObservation(
            **unavailable.model_dump(exclude={"observation_id", "reason_code"})
        )
    with pytest.raises(ValidationError, match="zero samples"):
        MetricObservation(
            **unavailable.model_dump(exclude={"observation_id", "sample_count"}),
            sample_count=1,
        )
    with pytest.raises(ValidationError, match="cannot have a reason"):
        MetricObservation(
            metric_key="validation_expectancy",
            scope=MetricScope.VALIDATION,
            status=MetricObservationStatus.AVAILABLE,
            value=0.2,
            sample_count=20,
            evidence_refs=(evidence,),
            available_at=NOW,
            reason_code="NOT_ALLOWED",
        )
