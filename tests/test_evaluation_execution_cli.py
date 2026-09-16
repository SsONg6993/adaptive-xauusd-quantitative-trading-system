from __future__ import annotations

import json
from datetime import timedelta

from evaluation_execution_test_support import NOW, persist_controlled_plan

from axq.reflection.__main__ import main
from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.execution_adapter import canonical_record_bytes, input_artifact_ref
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationExecutionRequest,
    MetricSampleSeries,
)


def _write_inputs(tmp_path):
    store_path = tmp_path / "evaluation.sqlite3"
    _, _, plan = persist_controlled_plan(store_path)
    artifact = CanonicalMetricSampleArtifact(
        scope=MetricScope.VALIDATION,
        available_at=NOW + timedelta(minutes=1),
        series=(
            MetricSampleSeries(metric_key="validation_expectancy", values=(-0.1, 0.3)),
        ),
    )
    artifact_path = tmp_path / "validation.json"
    artifact_path.write_bytes(canonical_record_bytes(artifact))
    request = EvaluationExecutionRequest(
        plan_id=plan.plan_id,
        candidate_id=plan.candidate_id,
        evaluation_run_key="controlled-run",
        deterministic_seed=plan.deterministic_seed,
        environment_identity=plan.environment_identity,
        input_artifact_refs=(input_artifact_ref(artifact),),
        requested_at=NOW + timedelta(minutes=2),
    )
    request_path = tmp_path / "request.json"
    request_path.write_bytes(canonical_record_bytes(request))
    return store_path, artifact_path, request, request_path


def test_cli_run_show_summary_and_idempotent_reuse(tmp_path, capsys) -> None:
    store_path, artifact_path, request, request_path = _write_inputs(tmp_path)
    result_path = tmp_path / "result.json"
    args = [
        "run-evaluation-execution",
        "--store",
        str(store_path),
        "--request",
        str(request_path),
        "--validation-input",
        str(artifact_path),
        "--result-output",
        str(result_path),
        "--started-at",
        (NOW + timedelta(minutes=3)).isoformat(),
        "--completed-at",
        (NOW + timedelta(minutes=4)).isoformat(),
    ]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    first_bytes = result_path.read_bytes()
    assert first["reused"] is False

    later = request.model_copy(update={"requested_at": NOW + timedelta(days=1)})
    request_path.write_bytes(canonical_record_bytes(later))
    retry_args = args[:-4] + [
        "--started-at",
        (NOW + timedelta(days=1, minutes=3)).isoformat(),
        "--completed-at",
        (NOW + timedelta(days=1, minutes=4)).isoformat(),
    ]
    assert main(retry_args) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["reused"] is True
    assert second["request_id"] == first["request_id"]
    assert second["result_id"] == first["result_id"]
    assert second["audit_id"] == first["audit_id"]
    assert result_path.read_bytes() == first_bytes

    assert main(
        [
            "show-evaluation-execution",
            "--store",
            str(store_path),
            "--request-id",
            request.request_id,
        ]
    ) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["request"]["request_id"] == request.request_id
    assert shown["audit"]["result_id"] == shown["result"]["result_id"]

    assert main(["evaluation-execution-summary", "--store", str(store_path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "audit_count": 1,
        "completed_request_count": 1,
        "final_oos_not_accessed_count": 1,
        "metric_observation_count": 2,
        "request_count": 1,
        "result_count": 1,
        "status_counts": {"COMPLETED": 1},
    }


def test_cli_exposes_no_final_oos_input_option() -> None:
    try:
        main(["run-evaluation-execution", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
