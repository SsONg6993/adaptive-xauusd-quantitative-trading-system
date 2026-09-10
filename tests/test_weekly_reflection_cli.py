from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from axq.experience import DecisionExperience, ExperienceProvenance
from axq.experience.store import SQLiteExperienceStore
from axq.reflection import (
    DailyReflection,
    FindingCategory,
    FindingSignal,
    MetricFact,
    ReflectionFinding,
    ReflectionPolicy,
)
from axq.reflection.__main__ import main
from axq.reflection.store import SQLiteReflectionStore
from axq.reflection.weekly_store import SQLiteWeeklyReflectionStore
from axq.schemas import Signal

START = datetime(2026, 8, 10, tzinfo=UTC)


def _sources(experience_path: Path, daily_path: Path, days: int) -> ReflectionPolicy:
    daily_policy = ReflectionPolicy()
    experience_store = SQLiteExperienceStore(experience_path)
    daily_store = SQLiteReflectionStore(daily_path)
    daily_store.append_policy(daily_policy)
    for index in range(days):
        at = START + timedelta(days=index, hours=12)
        experience = DecisionExperience(
            occurred_at=at,
            available_at=at,
            symbol="XAUUSD",
            outcome="HOLD",
            provenance=ExperienceProvenance(runtime_event_ids=(f"event-{index}",)),
            master_proposal_id=f"proposal-{index}",
            evidence_bundle_id=f"bundle-{index}",
            decision=Signal.HOLD,
            actionable=False,
            master_confidence=0.0,
            disagreement=0.0,
            contradiction=0.0,
        )
        experience_store.append(experience)
        finding = ReflectionFinding(
            category=FindingCategory.DIRECTION_OUTCOME,
            signal=FindingSignal.NEGATIVE,
            reason_code="NEGATIVE_AVERAGE_R",
            scope="direction",
            scope_value="BUY",
            sample_size=1,
            metrics=(MetricFact(name="average_r", value=-0.5, unit="R"),),
            supporting_experience_ids=(experience.experience_id,),
        )
        daily_store.append(
            DailyReflection(
                period_start=START + timedelta(days=index),
                period_end=START + timedelta(days=index + 1),
                available_at=START + timedelta(days=index + 1),
                policy_id=daily_policy.policy_id,
                input_experience_ids=(experience.experience_id,),
                findings=(finding,),
            )
        )
    return daily_policy


def _build_args(
    experiences: Path, daily: Path, weekly: Path, policy_id: str
) -> list[str]:
    return [
        "build-weekly-reflections",
        "--experience-store",
        str(experiences),
        "--daily-store",
        str(daily),
        "--weekly-store",
        str(weekly),
        "--daily-policy-id",
        policy_id,
        "--start-week",
        "2026-08-10",
        "--through-week",
        "2026-08-10",
    ]


def test_weekly_cli_builds_reuses_and_summarizes_incomplete_week(tmp_path, capsys) -> None:
    experiences = tmp_path / "experiences.sqlite3"
    daily = tmp_path / "daily.sqlite3"
    weekly = tmp_path / "weekly.sqlite3"
    policy = _sources(experiences, daily, 2)
    args = _build_args(experiences, daily, weekly, policy.policy_id)

    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert (first["created"], first["reused"]) == (1, 0)
    assert main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert (second["created"], second["reused"]) == (0, 1)
    assert second["reflection_ids"] == first["reflection_ids"]

    assert main(["weekly-summary", "--store", str(weekly)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["weeks"] == 1
    assert summary["incomplete_weeks"] == 1
    assert summary["failure_patterns"] == 0


def test_weekly_cli_show_and_explicit_transition_history(tmp_path, capsys) -> None:
    experiences = tmp_path / "experiences.sqlite3"
    daily = tmp_path / "daily.sqlite3"
    weekly = tmp_path / "weekly.sqlite3"
    policy = _sources(experiences, daily, 7)
    assert main(_build_args(experiences, daily, weekly, policy.policy_id)) == 0
    capsys.readouterr()
    store = SQLiteWeeklyReflectionStore(weekly)
    reflection = store.reflections()[0]
    pattern = reflection.failure_patterns[0]

    assert (
        main(
            [
                "show-weekly-reflection",
                "--store",
                str(weekly),
                "--week-start",
                "2026-08-10",
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["week_start"] == "2026-08-10T00:00:00Z"

    assert (
        main(
            [
                "transition-pattern",
                "--store",
                str(weekly),
                "--pattern-id",
                pattern.pattern_id,
                "--pattern-key",
                pattern.pattern_key,
                "--from-status",
                "OBSERVATION",
                "--to-status",
                "HYPOTHESIS",
                "--effective-at",
                "2026-08-17T00:00:00Z",
                "--action-kind",
                "OPERATOR",
                "--actor-id",
                "operator-1",
                "--action-id",
                "review-1",
                "--reason-code",
                "EXPLICIT_REVIEW",
            ]
        )
        == 0
    )
    transitioned = json.loads(capsys.readouterr().out)
    assert transitioned["current_status"] == "HYPOTHESIS"
    assert (
        main(
            [
                "show-pattern-history",
                "--store",
                str(weekly),
                "--pattern-id",
                pattern.pattern_id,
            ]
        )
        == 0
    )
    history = json.loads(capsys.readouterr().out)
    assert history["current_status"] == "HYPOTHESIS"
    assert len(history["transitions"]) == 1
