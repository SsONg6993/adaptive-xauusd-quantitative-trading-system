from __future__ import annotations

import hashlib
import sqlite3
from datetime import timedelta

import pytest
from evaluation_execution_test_support import NOW, persist_controlled_plan

from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_adapter import (
    CanonicalMetricSamplesAdapter,
    input_artifact_ref,
)
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationExecutionAudit,
    EvaluationExecutionRequest,
    EvaluationExecutionStatus,
    MetricSampleSeries,
)
from axq.reflection.execution_store import SQLiteEvaluationExecutionStore


def _artifact() -> CanonicalMetricSampleArtifact:
    return CanonicalMetricSampleArtifact(
        scope=MetricScope.VALIDATION,
        available_at=NOW + timedelta(minutes=1),
        series=(
            MetricSampleSeries(
                metric_key="validation_expectancy",
                values=(0.1, 0.3),
            ),
        ),
    )


def _request(plan, artifact, **changes: object) -> EvaluationExecutionRequest:
    values: dict[str, object] = {
        "plan_id": plan.plan_id,
        "candidate_id": plan.candidate_id,
        "evaluation_run_key": "controlled-run",
        "deterministic_seed": plan.deterministic_seed,
        "environment_identity": plan.environment_identity,
        "input_artifact_refs": (input_artifact_ref(artifact),),
        "requested_at": NOW + timedelta(minutes=2),
    }
    values.update(changes)
    return EvaluationExecutionRequest(**values)


def test_store_requires_exact_persisted_plan_candidate_and_scope_linkage(tmp_path) -> None:
    path = tmp_path / "execution.sqlite3"
    _, _, plan = persist_controlled_plan(path)
    artifact = _artifact()
    request = _request(plan, artifact)
    store = SQLiteEvaluationExecutionStore(path)

    assert store.append_request(request) is True
    later = _request(plan, artifact, requested_at=request.requested_at + timedelta(days=1))
    assert later.request_id == request.request_id
    assert store.append_request(later) is False
    assert store.request(request.request_id) == request
    with pytest.raises(ValueError, match="seed"):
        store.append_request(_request(plan, artifact, deterministic_seed=99))


def test_store_requires_exact_result_and_reuses_later_timestamp_audit(tmp_path) -> None:
    path = tmp_path / "execution.sqlite3"
    _, _, plan = persist_controlled_plan(path)
    artifact = _artifact()
    request = _request(plan, artifact)
    execution_store = SQLiteEvaluationExecutionStore(path)
    execution_store.append_request(request)
    output = CanonicalMetricSamplesAdapter().execute(request, plan, (artifact,))
    SQLiteProposalEvaluationStore(path).append_result(output.result)
    digest = hashlib.sha256(output.result_bytes).hexdigest()
    audit = EvaluationExecutionAudit(
        request_id=request.request_id,
        result_id=output.result.result_id,
        plan_id=plan.plan_id,
        candidate_id=plan.candidate_id,
        evaluation_run_key=request.evaluation_run_key,
        adapter_kind=request.adapter_kind,
        adapter_version=request.adapter_version,
        deterministic_seed=request.deterministic_seed,
        environment_identity=request.environment_identity,
        input_artifact_refs=request.input_artifact_refs,
        result_artifact_sha256=digest,
        status=EvaluationExecutionStatus.COMPLETED,
        started_at=NOW + timedelta(minutes=3),
        completed_at=NOW + timedelta(minutes=4),
    )

    assert execution_store.append_audit(audit) is True
    later = EvaluationExecutionAudit(
        **audit.model_dump(exclude={"audit_id", "started_at", "completed_at"}),
        started_at=NOW + timedelta(days=1),
        completed_at=NOW + timedelta(days=1, minutes=1),
    )
    assert later.audit_id == audit.audit_id
    assert execution_store.append_audit(later) is False
    assert execution_store.audit(request.request_id) == audit


def test_execution_tables_are_append_only(tmp_path) -> None:
    path = tmp_path / "execution.sqlite3"
    _, _, plan = persist_controlled_plan(path)
    artifact = _artifact()
    request = _request(plan, artifact)
    store = SQLiteEvaluationExecutionStore(path)
    store.append_request(request)
    output = CanonicalMetricSamplesAdapter().execute(request, plan, (artifact,))
    SQLiteProposalEvaluationStore(path).append_result(output.result)
    store.append_audit(
        EvaluationExecutionAudit(
            request_id=request.request_id,
            result_id=output.result.result_id,
            plan_id=plan.plan_id,
            candidate_id=plan.candidate_id,
            evaluation_run_key=request.evaluation_run_key,
            adapter_kind=request.adapter_kind,
            adapter_version=request.adapter_version,
            deterministic_seed=request.deterministic_seed,
            environment_identity=request.environment_identity,
            input_artifact_refs=request.input_artifact_refs,
            result_artifact_sha256=hashlib.sha256(output.result_bytes).hexdigest(),
            started_at=NOW + timedelta(minutes=3),
            completed_at=NOW + timedelta(minutes=4),
        )
    )
    tables = (
        "evaluation_execution_requests",
        "evaluation_execution_input_refs",
        "evaluation_execution_audits",
    )
    with sqlite3.connect(path) as connection:
        for table in tables:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"DELETE FROM {table}")
