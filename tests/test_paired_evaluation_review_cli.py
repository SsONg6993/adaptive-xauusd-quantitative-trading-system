from __future__ import annotations

import json

from paired_evaluation_review_test_support import persisted_review_fixture

from axq.reflection.__main__ import main
from axq.reflection.execution_adapter import canonical_record_bytes


def test_cli_record_show_history_and_summary(tmp_path, capsys) -> None:
    store_path, _, result, review = persisted_review_fixture(tmp_path)
    review_path = tmp_path / "paired-review.json"
    review_path.write_bytes(canonical_record_bytes(review))
    record_args = [
        "record-paired-evaluation-review",
        "--store",
        str(store_path),
        "--review",
        str(review_path),
    ]

    assert main(record_args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first == {"appended": True, "review_id": review.review_id}
    assert main(record_args) == 0
    assert json.loads(capsys.readouterr().out) == {
        "appended": False,
        "review_id": review.review_id,
    }

    assert (
        main(
            [
                "show-paired-evaluation-review",
                "--store",
                str(store_path),
                "--review-id",
                review.review_id,
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["review_id"] == review.review_id

    assert (
        main(
            [
                "show-paired-evaluation-review-history",
                "--store",
                str(store_path),
                "--result-id",
                result.result_id,
            ]
        )
        == 0
    )
    history = json.loads(capsys.readouterr().out)
    assert history["current_review_id"] == review.review_id
    assert history["review_ids"] == [review.review_id]

    assert main(["paired-evaluation-review-summary", "--store", str(store_path)]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "current_decision_counts": {"ACCEPT_EVIDENCE": 1},
        "decision_counts": {"ACCEPT_EVIDENCE": 1},
        "review_count": 1,
        "reviewed_result_count": 1,
    }


def test_review_cli_exposes_no_final_oos_or_execution_option(capsys) -> None:
    try:
        main(["record-paired-evaluation-review", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    help_text = capsys.readouterr().out.lower()
    assert "final-oos" not in help_text
    assert "execute" not in help_text
