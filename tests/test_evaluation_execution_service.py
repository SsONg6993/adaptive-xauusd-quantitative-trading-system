from __future__ import annotations

from datetime import timedelta

import pytest
from evaluation_execution_test_support import NOW, persist_controlled_plan

from axq.reflection.evaluation_contracts import MetricObservationStatus, MetricScope
from axq.reflection.execution_adapter import (
    CanonicalMetricSamplesAdapter,
    input_artifact_ref,
)
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationExecutionRequest,
    MetricSampleSeries,
)
from axq.reflection.execution_service import execute_evaluation_request
from axq.reflection.execution_store import SQLiteEvaluationExecutionStore


def _artifact() -> CanonicalMetricSampleArtifact:
    return CanonicalMetricSampleArtifact(
        scope=MetricScope.VALIDATION,
        available_at=NOW + timedelta(minutes=1),
        series=(
            MetricSampleSeries(
                metric_key="validation_expectancy",
                values=(-0.1, 0.3),
            ),
        ),
    )


def _request(plan, artifact, requested_at=NOW + timedelta(minutes=2)):
    return EvaluationExecutionRequest(
        plan_id=plan.plan_id,
        candidate_id=plan.candidate_id,
        evaluation_run_key="controlled-run",
        deterministic_seed=plan.deterministic_seed,
        environment_identity=plan.environment_identity,
        input_artifact_refs=(input_artifact_ref(artifact),),
        requested_at=requested_at,
    )


class CountingAdapter:
    def __init__(self) -> None:
        self.calls = 0
        self.delegate = CanonicalMetricSamplesAdapter()

    def execute(self, request, plan, artifacts):
        self.calls += 1
        return self.delegate.execute(request, plan, artifacts)


def test_service_builds_exact_result_and_explicitly_withholds_final_oos(tmp_path) -> None:
    path = tmp_path / "execution.sqlite3"
    _, candidate, plan = persist_controlled_plan(path)
    artifact = _artifact()
    outcome = execute_evaluation_request(
        path,
        _request(plan, artifact),
        (artifact,),
        started_at=NOW + timedelta(minutes=3),
        completed_at=NOW + timedelta(minutes=4),
    )

    assert outcome.reused is False
    assert outcome.result.plan_id == plan.plan_id
    assert outcome.result.candidate_id == candidate.candidate_id
    validation = next(
        item for item in outcome.result.observations if item.scope is MetricScope.VALIDATION
    )
    final_oos = next(
        item for item in outcome.result.observations if item.scope is MetricScope.FINAL_OOS
    )
    assert validation.value == pytest.approx(0.1)
    assert final_oos.scope is MetricScope.FINAL_OOS
    assert final_oos.status is MetricObservationStatus.UNAVAILABLE
    assert final_oos.reason_code == "FINAL_OOS_NOT_ACCESSED"
    assert outcome.audit.result_id == outcome.result.result_id


def test_later_retry_reuses_result_bytes_and_does_not_execute_adapter_twice(tmp_path) -> None:
    path = tmp_path / "execution.sqlite3"
    _, _, plan = persist_controlled_plan(path)
    artifact = _artifact()
    adapter = CountingAdapter()
    first = execute_evaluation_request(
        path,
        _request(plan, artifact),
        (artifact,),
        started_at=NOW + timedelta(minutes=3),
        completed_at=NOW + timedelta(minutes=4),
        adapter=adapter,
    )
    second = execute_evaluation_request(
        path,
        _request(plan, artifact, NOW + timedelta(days=1)),
        (artifact,),
        started_at=NOW + timedelta(days=1, minutes=3),
        completed_at=NOW + timedelta(days=1, minutes=4),
        adapter=adapter,
    )

    assert adapter.calls == 1
    assert second.reused is True
    assert second.request.request_id == first.request.request_id
    assert second.result.result_id == first.result.result_id
    assert second.audit.audit_id == first.audit.audit_id
    assert second.result_bytes == first.result_bytes


def test_digest_mismatch_fails_without_completed_audit(tmp_path) -> None:
    path = tmp_path / "execution.sqlite3"
    _, _, plan = persist_controlled_plan(path)
    artifact = _artifact()
    original = _request(plan, artifact)
    request = EvaluationExecutionRequest(
        **original.model_dump(exclude={"request_id", "input_artifact_refs"}),
        input_artifact_refs=(
            input_artifact_ref(artifact).model_copy(update={"sha256": "f" * 64}),
        ),
    )
    with pytest.raises(ValueError, match="digest"):
        execute_evaluation_request(
            path,
            request,
            (artifact,),
            started_at=NOW + timedelta(minutes=3),
            completed_at=NOW + timedelta(minutes=4),
        )
    assert SQLiteEvaluationExecutionStore(path).audits() == ()
