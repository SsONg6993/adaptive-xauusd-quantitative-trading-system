from __future__ import annotations

import json
from datetime import timedelta

from candidate_replay_test_support import NOW, persisted_candidate_replay

from axq.reflection.__main__ import main
from axq.reflection.candidate_replay_contracts import CandidateReplayRequest
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_store import SQLiteImprovementProposalStore


def _write_inputs(tmp_path):
    store_path = tmp_path / "candidate-replay.sqlite3"
    proposal, _, _, fixtures, request = persisted_candidate_replay(store_path)
    request_path = tmp_path / "candidate-replay-request.json"
    validation_path = tmp_path / "validation-fixture.json"
    request_path.write_bytes(canonical_record_bytes(request))
    validation_path.write_bytes(canonical_record_bytes(fixtures[0]))
    return store_path, proposal, request, request_path, validation_path


def test_cli_runs_reuses_shows_and_summarizes_controlled_replay(tmp_path, capsys) -> None:
    store, proposal, request, request_path, validation_path = _write_inputs(tmp_path)
    output_dir = tmp_path / "outputs"
    args = [
        "run-candidate-replay",
        "--store",
        str(store),
        "--request",
        str(request_path),
        "--validation-input",
        str(validation_path),
        "--output-dir",
        str(output_dir),
        "--started-at",
        (NOW + timedelta(minutes=4)).isoformat(),
        "--completed-at",
        (NOW + timedelta(minutes=5)).isoformat(),
    ]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    artifact_path = output_dir / "validation-metric-samples.json"
    first_bytes = artifact_path.read_bytes()
    assert first["reused"] is False
    assert first["artifact_count"] == 1

    later = CandidateReplayRequest(
        **request.model_dump(exclude={"request_id", "requested_at"}),
        requested_at=NOW + timedelta(days=1),
    )
    request_path.write_bytes(canonical_record_bytes(later))
    retry = args[:-4] + [
        "--started-at",
        (NOW + timedelta(days=1, minutes=4)).isoformat(),
        "--completed-at",
        (NOW + timedelta(days=1, minutes=5)).isoformat(),
    ]
    assert main(retry) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["reused"] is True
    assert second["request_id"] == first["request_id"]
    assert second["audit_id"] == first["audit_id"]
    assert second["artifact_ids"] == first["artifact_ids"]
    assert artifact_path.read_bytes() == first_bytes

    assert main(
        [
            "show-candidate-replay",
            "--store",
            str(store),
            "--request-id",
            request.request_id,
        ]
    ) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["request"]["request_id"] == request.request_id
    assert shown["audit"]["output_artifact_refs"][0]["semantic_id"] == (
        shown["artifacts"][0]["artifact_id"]
    )

    assert main(["candidate-replay-summary", "--store", str(store)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "artifact_count": 1,
        "artifact_scope_counts": {"VALIDATION": 1},
        "audit_count": 1,
        "completed_request_count": 1,
        "engine_counts": {"CONTROLLED_REPLAY_FIXTURE_V1": 1},
        "request_count": 1,
        "status_counts": {"COMPLETED": 1},
    }
    assert SQLiteImprovementProposalStore(store).current_status(proposal.proposal_id) is (
        ProposalStatus.CANDIDATE
    )


def test_cli_has_no_final_oos_input_option(capsys) -> None:
    try:
        main(["run-candidate-replay", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "final-oos" not in capsys.readouterr().out.lower()
