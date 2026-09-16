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
    WeeklyReflectionPolicy,
)
from axq.reflection.__main__ import main
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.store import SQLiteReflectionStore
from axq.reflection.weekly import build_weekly_reflection
from axq.reflection.weekly_store import SQLiteWeeklyReflectionStore
from axq.schemas import Signal

START = datetime(2026, 8, 10, tzinfo=UTC)


def _source_stores(root: Path) -> tuple[Path, Path, Path]:
    experience_path = root / "experiences.sqlite3"
    daily_path = root / "daily.sqlite3"
    weekly_path = root / "weekly.sqlite3"
    experience_store = SQLiteExperienceStore(experience_path)
    daily_store = SQLiteReflectionStore(daily_path)
    weekly_store = SQLiteWeeklyReflectionStore(weekly_path)
    daily_policy = ReflectionPolicy()
    weekly_policy = WeeklyReflectionPolicy(
        daily_policy_id=daily_policy.policy_id,
        min_pattern_days=2,
        min_pattern_experiences=2,
    )
    daily_store.append_policy(daily_policy)
    weekly_store.append_policy(weekly_policy)
    experiences: list[DecisionExperience] = []
    daily: list[DailyReflection] = []
    for day in range(14):
        day_start = START + timedelta(days=day)
        experience = DecisionExperience(
            occurred_at=day_start + timedelta(hours=12),
            available_at=day_start + timedelta(hours=12),
            symbol="XAUUSD",
            outcome="HOLD",
            provenance=ExperienceProvenance(runtime_event_ids=(f"event-{day}",)),
            master_proposal_id=f"master-{day}",
            evidence_bundle_id=f"bundle-{day}",
            decision=Signal.HOLD,
            actionable=False,
            master_confidence=0.0,
            disagreement=0.0,
            contradiction=0.0,
        )
        experience_store.append(experience)
        experiences.append(experience)
        daily_record = DailyReflection(
            period_start=day_start,
            period_end=day_start + timedelta(days=1),
            available_at=day_start + timedelta(days=1),
            policy_id=daily_policy.policy_id,
            input_experience_ids=(experience.experience_id,),
            findings=(
                ReflectionFinding(
                    category=FindingCategory.DIRECTION_OUTCOME,
                    signal=FindingSignal.NEGATIVE,
                    reason_code="NEGATIVE_AVERAGE_R",
                    scope="direction",
                    scope_value="BUY",
                    sample_size=1,
                    metrics=(MetricFact(name="average_r", value=-0.5, unit="R"),),
                    supporting_experience_ids=(experience.experience_id,),
                ),
            ),
        )
        daily_store.append(daily_record)
        daily.append(daily_record)
    for offset in (0, 7):
        weekly_store.append(
            build_weekly_reflection(
                daily,
                experiences,
                (START + timedelta(days=offset)).date(),
                weekly_policy,
            )
        )
    return experience_path, daily_path, weekly_path


def _build_args(root: Path, proposal_path: Path) -> list[str]:
    experience_path, daily_path, weekly_path = _source_stores(root)
    return [
        "build-improvement-proposals",
        "--experience-store",
        str(experience_path),
        "--daily-store",
        str(daily_path),
        "--weekly-store",
        str(weekly_path),
        "--proposal-store",
        str(proposal_path),
    ]


def test_proposal_cli_builds_reuses_shows_and_summarizes(tmp_path, capsys) -> None:
    proposal_path = tmp_path / "proposals.sqlite3"
    args = _build_args(tmp_path, proposal_path)

    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert (first["assessed_pattern_keys"], first["eligible_pattern_keys"]) == (1, 1)
    assert (first["created"], first["reused"], first["superseded"]) == (1, 0, 0)
    assert main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert (second["created"], second["reused"], second["superseded"]) == (0, 1, 0)
    assert second["proposal_ids"] == first["proposal_ids"]

    proposal_id = first["proposal_ids"][0]
    assert (
        main(
            [
                "show-improvement-proposal",
                "--store",
                str(proposal_path),
                "--proposal-id",
                proposal_id,
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["status"] == "OBSERVATION"
    assert len(shown["supporting_pattern_ids"]) == 2

    assert main(["proposal-summary", "--store", str(proposal_path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["proposals"] == 1
    assert summary["status_counts"] == {"OBSERVATION": 1}
    assert summary["superseding_proposals"] == 0
    assert summary["transitions"] == 0


def test_proposal_cli_requires_explicit_transition_and_shows_history(tmp_path, capsys) -> None:
    proposal_path = tmp_path / "proposals.sqlite3"
    assert main(_build_args(tmp_path, proposal_path)) == 0
    created = json.loads(capsys.readouterr().out)
    proposal = SQLiteImprovementProposalStore(proposal_path).proposal(created["proposal_ids"][0])
    assert proposal is not None

    assert main(
        [
            "transition-proposal",
            "--store",
            str(proposal_path),
            "--proposal-id",
            proposal.proposal_id,
            "--proposal-key",
            proposal.proposal_key,
            "--from-status",
            "OBSERVATION",
            "--to-status",
            "HYPOTHESIS",
            "--effective-at",
            proposal.available_at.isoformat(),
            "--action-kind",
            "OPERATOR",
            "--actor-id",
            "operator-1",
            "--action-id",
            "review-1",
            "--reason-code",
            "EXPLICIT_REVIEW",
        ]
    ) == 0
    transitioned = json.loads(capsys.readouterr().out)
    assert transitioned["current_status"] == "HYPOTHESIS"

    assert (
        main(
            [
                "show-proposal-history",
                "--store",
                str(proposal_path),
                "--proposal-id",
                proposal.proposal_id,
            ]
        )
        == 0
    )
    history = json.loads(capsys.readouterr().out)
    assert history["current_status"] == "HYPOTHESIS"
    assert len(history["transitions"]) == 1
