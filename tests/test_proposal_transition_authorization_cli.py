from __future__ import annotations

import json

from proposal_transition_authorization_test_support import persisted_authorization_fixture

from axq.reflection.__main__ import main
from axq.reflection.execution_adapter import canonical_record_bytes


def test_cli_record_show_history_summary_and_idempotent_retry(tmp_path, capsys) -> None:
    store_path, proposal, _, _, authorization = persisted_authorization_fixture(tmp_path)
    authorization_path = tmp_path / "proposal-transition-authorization.json"
    authorization_path.write_bytes(canonical_record_bytes(authorization))
    record_args = [
        "record-proposal-transition-authorization",
        "--store",
        str(store_path),
        "--authorization",
        str(authorization_path),
    ]

    assert main(record_args) == 0
    assert json.loads(capsys.readouterr().out) == {
        "appended": True,
        "authorization_id": authorization.authorization_id,
    }
    assert main(record_args) == 0
    assert json.loads(capsys.readouterr().out) == {
        "appended": False,
        "authorization_id": authorization.authorization_id,
    }

    assert (
        main(
            [
                "show-proposal-transition-authorization",
                "--store",
                str(store_path),
                "--authorization-id",
                authorization.authorization_id,
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["authorization_id"] == (
        authorization.authorization_id
    )

    assert (
        main(
            [
                "show-proposal-transition-authorization-history",
                "--store",
                str(store_path),
                "--proposal-id",
                proposal.proposal_id,
            ]
        )
        == 0
    )
    history = json.loads(capsys.readouterr().out)
    assert history["current_authorization_id"] == authorization.authorization_id
    assert history["authorization_ids"] == [authorization.authorization_id]

    assert main(["proposal-transition-authorization-summary", "--store", str(store_path)]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "authorization_count": 1,
        "authorized_proposal_count": 1,
        "current_transition_counts": {"CANDIDATE->VALIDATED": 1},
        "transition_counts": {"CANDIDATE->VALIDATED": 1},
    }


def test_authorization_cli_exposes_no_execution_or_final_oos_option(capsys) -> None:
    try:
        main(["record-proposal-transition-authorization", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    help_text = capsys.readouterr().out.lower()
    assert "final-oos" not in help_text
    assert "execute" not in help_text
    assert "transition-proposal" not in help_text
