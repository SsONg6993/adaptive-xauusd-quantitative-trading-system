from __future__ import annotations

import json
from datetime import timedelta

from paired_evaluation_test_support import NOW, persisted_paired_fixture

from axq.reflection.__main__ import main
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.paired_evaluation_contracts import PairedEvaluationRequest


def test_cli_run_show_summary_and_idempotent_reuse(tmp_path, capsys) -> None:
    store_path, _, _, _, _, baseline, candidate, request = persisted_paired_fixture(tmp_path)
    request_path = tmp_path / "paired-request.json"
    baseline_path = tmp_path / "baseline-validation.json"
    candidate_path = tmp_path / "candidate-validation.json"
    result_path = tmp_path / "paired-result.json"
    request_path.write_bytes(canonical_record_bytes(request))
    baseline_path.write_bytes(canonical_record_bytes(baseline))
    candidate_path.write_bytes(canonical_record_bytes(candidate))
    args = [
        "run-paired-evaluation",
        "--store",
        str(store_path),
        "--request",
        str(request_path),
        "--baseline-validation-input",
        str(baseline_path),
        "--candidate-validation-input",
        str(candidate_path),
        "--result-output",
        str(result_path),
        "--started-at",
        (NOW + timedelta(minutes=21)).isoformat(),
        "--completed-at",
        (NOW + timedelta(minutes=22)).isoformat(),
    ]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    first_bytes = result_path.read_bytes()
    assert first["reused"] is False
    assert first["criterion_status_counts"] == {"PASS": 1, "UNAVAILABLE": 1}

    later = PairedEvaluationRequest(
        **request.model_dump(exclude={"request_id", "requested_at"}),
        requested_at=NOW + timedelta(days=1),
    )
    request_path.write_bytes(canonical_record_bytes(later))
    assert main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["reused"] is True
    assert second["request_id"] == first["request_id"]
    assert second["result_id"] == first["result_id"]
    assert second["audit_id"] == first["audit_id"]
    assert result_path.read_bytes() == first_bytes

    assert main(
        [
            "show-paired-evaluation",
            "--store",
            str(store_path),
            "--request-id",
            request.request_id,
        ]
    ) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["result"]["result_id"] == first["result_id"]

    assert main(["paired-evaluation-summary", "--store", str(store_path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "audit_count": 1,
        "completed_request_count": 1,
        "criterion_status_counts": {"PASS": 1, "UNAVAILABLE": 1},
        "final_oos_not_accessed_count": 1,
        "metric_status_counts": {"AVAILABLE": 1, "UNAVAILABLE": 1},
        "request_count": 1,
        "result_count": 1,
    }


def test_cli_has_no_final_oos_input_option() -> None:
    try:
        main(["run-paired-evaluation", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
