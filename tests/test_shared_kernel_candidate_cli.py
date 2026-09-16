from __future__ import annotations

import json

from shared_kernel_candidate_test_support import NOW, persisted_shared_kernel_inputs

from axq.reflection.__main__ import main
from axq.reflection.execution_adapter import canonical_record_bytes


def test_cli_runs_shows_and_summarizes_controlled_shared_kernel_candidate(
    tmp_path, capsys
) -> None:
    path, _, _, _, config, manifests, directories, request = persisted_shared_kernel_inputs(
        tmp_path
    )
    config_path = tmp_path / "config.json"
    request_path = tmp_path / "request.json"
    manifest_path = tmp_path / "validation-manifest.json"
    config_path.write_bytes(canonical_record_bytes(config))
    request_path.write_bytes(canonical_record_bytes(request))
    manifest_path.write_bytes(canonical_record_bytes(manifests[0]))
    output_dir = tmp_path / "cli-output"

    assert (
        main(
            [
                "run-shared-kernel-candidate",
                "--store",
                str(path),
                "--request",
                str(request_path),
                "--config",
                str(config_path),
                "--validation-manifest",
                str(manifest_path),
                "--validation-data-dir",
                str(directories[manifests[0].scope]),
                "--output-dir",
                str(output_dir),
                "--started-at",
                NOW.isoformat(),
                "--completed-at",
                NOW.isoformat(),
            ]
        )
        == 0
    )
    run_report = json.loads(capsys.readouterr().out)
    assert run_report["artifact_count"] == 1
    assert run_report["reused"] is False
    assert (output_dir / "validation-metric-samples.json").is_file()

    assert (
        main(
            [
                "show-shared-kernel-candidate",
                "--store",
                str(path),
                "--request-id",
                request.request_id,
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["request"]["request_id"] == request.request_id
    assert shown["audit"]["status"] == "COMPLETED"

    assert main(["shared-kernel-candidate-summary", "--store", str(path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "artifact_count": 1,
        "artifact_scope_counts": {"VALIDATION": 1},
        "audit_count": 1,
        "completed_request_count": 1,
        "engine_counts": {"SHARED_KERNEL_MASTER_FUSION_V1": 1},
        "request_count": 1,
        "status_counts": {"COMPLETED": 1},
    }
