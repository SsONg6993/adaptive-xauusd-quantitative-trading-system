from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from axq.experience import DecisionExperience, ExperienceProvenance
from axq.experience.store import SQLiteExperienceStore
from axq.reflection import SQLiteReflectionStore
from axq.reflection.__main__ import main
from axq.schemas import Signal


def _experience_store(path: Path) -> None:
    SQLiteExperienceStore(path).append(_decision("1", 12))


def _decision(suffix: str, hour: int) -> DecisionExperience:
    at = datetime(2026, 8, 10, hour, tzinfo=UTC)
    return DecisionExperience(
            occurred_at=at,
            available_at=at,
            symbol="XAUUSD",
            outcome="HOLD",
            provenance=ExperienceProvenance(runtime_event_ids=(f"event-{suffix}",)),
            master_proposal_id=f"proposal-{suffix}",
            evidence_bundle_id=f"bundle-{suffix}",
            decision=Signal.HOLD,
            actionable=False,
            master_confidence=0.0,
            disagreement=0.0,
            contradiction=0.0,
        )


def test_build_range_is_deterministic_and_idempotent(tmp_path, capsys) -> None:
    experiences = tmp_path / "experiences.sqlite3"
    reflections = tmp_path / "reflections.sqlite3"
    _experience_store(experiences)
    args = [
        "build-daily-reflections",
        "--experience-store",
        str(experiences),
        "--reflection-store",
        str(reflections),
        "--start-date",
        "2026-08-10",
        "--through-date",
        "2026-08-11",
    ]

    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["created"] == 2
    assert first["reused"] == 0
    assert main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["created"] == 0
    assert second["reused"] == 2
    assert second["reflection_ids"] == first["reflection_ids"]


def test_show_and_report_emit_machine_readable_json(tmp_path, capsys) -> None:
    experiences = tmp_path / "experiences.sqlite3"
    reflections = tmp_path / "reflections.sqlite3"
    _experience_store(experiences)
    assert (
        main(
            [
                "build-daily-reflections",
                "--experience-store",
                str(experiences),
                "--reflection-store",
                str(reflections),
                "--start-date",
                "2026-08-10",
                "--through-date",
                "2026-08-10",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert (
        main(
            [
                "show-daily-reflection",
                "--store",
                str(reflections),
                "--date",
                "2026-08-10",
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["period_start"] == "2026-08-10T00:00:00Z"
    assert main(["report", "--store", str(reflections)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["days"] == 1
    assert report["finding_signal_counts"] == {}
    assert report["guard_status_counts"]["UNAVAILABLE"] > 0


def test_changed_input_creates_explicit_cli_supersession(tmp_path, capsys) -> None:
    experiences = tmp_path / "experiences.sqlite3"
    reflections = tmp_path / "reflections.sqlite3"
    _experience_store(experiences)
    args = [
        "build-daily-reflections",
        "--experience-store",
        str(experiences),
        "--reflection-store",
        str(reflections),
        "--start-date",
        "2026-08-10",
        "--through-date",
        "2026-08-10",
    ]
    assert main(args) == 0
    capsys.readouterr()
    store = SQLiteReflectionStore(reflections)
    first = store.reflections()[0]
    SQLiteExperienceStore(experiences).append(_decision("2", 13))

    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    latest = store.reflections()[-1]
    assert result["created"] == 1
    assert len(store.reflections()) == 2
    assert latest.supersedes_reflection_id == first.reflection_id


def test_build_rejects_reversed_date_range(tmp_path) -> None:
    experiences = tmp_path / "experiences.sqlite3"
    _experience_store(experiences)

    with pytest.raises(ValueError, match="cannot be before"):
        main(
            [
                "build-daily-reflections",
                "--experience-store",
                str(experiences),
                "--reflection-store",
                str(tmp_path / "reflections.sqlite3"),
                "--start-date",
                "2026-08-11",
                "--through-date",
                "2026-08-10",
            ]
        )
