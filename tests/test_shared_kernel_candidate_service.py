from __future__ import annotations

from datetime import timedelta

from shared_kernel_candidate_test_support import NOW, persisted_shared_kernel_inputs

from axq.reflection.evaluation_contracts import MetricObservationStatus, MetricScope
from axq.reflection.execution_adapter import input_artifact_ref
from axq.reflection.execution_contracts import EvaluationExecutionRequest
from axq.reflection.execution_service import execute_evaluation_request
from axq.reflection.shared_kernel_candidate_contracts import SharedKernelCandidateRequest
from axq.reflection.shared_kernel_candidate_engine import SharedKernelMasterFusionEngineV1
from axq.reflection.shared_kernel_candidate_service import execute_shared_kernel_candidate


class CountingSharedKernelEngine:
    kind = SharedKernelMasterFusionEngineV1.kind
    version = SharedKernelMasterFusionEngineV1.version

    def __init__(self) -> None:
        self.calls = 0
        self.delegate = SharedKernelMasterFusionEngineV1()

    def execute(self, *args, **kwargs):
        self.calls += 1
        return self.delegate.execute(*args, **kwargs)


def test_completed_retry_reuses_exact_artifacts_without_rerunning_kernel(tmp_path) -> None:
    path, _, _, _, config, manifests, directories, request = persisted_shared_kernel_inputs(
        tmp_path
    )
    engine = CountingSharedKernelEngine()
    first = execute_shared_kernel_candidate(
        path,
        request,
        config,
        manifests,
        directories,
        tmp_path / "runs",
        started_at=NOW + timedelta(minutes=11),
        completed_at=NOW + timedelta(minutes=12),
        engine=engine,
    )
    later_request = SharedKernelCandidateRequest(
        **request.model_dump(exclude={"request_id", "requested_at"}),
        requested_at=NOW + timedelta(days=1),
    )
    second = execute_shared_kernel_candidate(
        path,
        later_request,
        config,
        tuple(reversed(manifests)),
        directories,
        tmp_path / "runs-not-used",
        started_at=NOW + timedelta(days=1, minutes=11),
        completed_at=NOW + timedelta(days=1, minutes=12),
        engine=engine,
    )

    assert engine.calls == 1
    assert second.reused is True
    assert second.request.request_id == first.request.request_id
    assert second.audit.audit_id == first.audit.audit_id
    assert second.artifact_bytes == first.artifact_bytes


def test_shared_kernel_output_executes_unchanged_through_task6(tmp_path) -> None:
    (
        path,
        _,
        candidate,
        plan,
        config,
        manifests,
        directories,
        request,
    ) = persisted_shared_kernel_inputs(tmp_path, include_development=True)
    replay = execute_shared_kernel_candidate(
        path,
        request,
        config,
        manifests,
        directories,
        tmp_path / "runs",
        started_at=NOW + timedelta(minutes=11),
        completed_at=NOW + timedelta(minutes=12),
    )
    execution_request = EvaluationExecutionRequest(
        plan_id=plan.plan_id,
        candidate_id=candidate.candidate_id,
        evaluation_run_key="shared-kernel-task6-consumption",
        deterministic_seed=plan.deterministic_seed,
        environment_identity=plan.environment_identity,
        input_artifact_refs=tuple(input_artifact_ref(item) for item in replay.artifacts),
        requested_at=NOW + timedelta(minutes=13),
    )
    result = execute_evaluation_request(
        path,
        execution_request,
        replay.artifacts,
        started_at=NOW + timedelta(minutes=14),
        completed_at=NOW + timedelta(minutes=15),
    ).result

    validation = next(item for item in result.observations if item.scope is MetricScope.VALIDATION)
    development = next(
        item for item in result.observations if item.scope is MetricScope.DEVELOPMENT
    )
    final_oos = next(item for item in result.observations if item.scope is MetricScope.FINAL_OOS)
    assert development.status is MetricObservationStatus.AVAILABLE
    assert validation.status is MetricObservationStatus.AVAILABLE
    assert final_oos.status is MetricObservationStatus.UNAVAILABLE
    assert final_oos.reason_code == "FINAL_OOS_NOT_ACCESSED"
