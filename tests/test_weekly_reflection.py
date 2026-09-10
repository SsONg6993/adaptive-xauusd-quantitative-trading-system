from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from axq.experience import DecisionExperience, ExperienceProvenance
from axq.reflection import (
    DailyReflection,
    FindingCategory,
    FindingSignal,
    MetricFact,
    ReflectionFinding,
    ReflectionPolicy,
    SampleGuardStatus,
    WeeklyGuardKind,
    WeeklyReflectionPolicy,
)
from axq.reflection.weekly import build_weekly_reflection
from axq.schemas import Signal

START = datetime(2026, 8, 10, tzinfo=UTC)
DAILY_POLICY = ReflectionPolicy()
WEEKLY_POLICY = WeeklyReflectionPolicy(
    daily_policy_id=DAILY_POLICY.policy_id,
    min_pattern_days=2,
    min_pattern_experiences=3,
)


def _experience(index: int, day_offset: int) -> DecisionExperience:
    at = START + timedelta(days=day_offset, hours=12, minutes=index)
    return DecisionExperience(
        occurred_at=at,
        available_at=at,
        symbol="XAUUSD",
        outcome="HOLD",
        provenance=ExperienceProvenance(runtime_event_ids=(f"event-{day_offset}-{index}",)),
        master_proposal_id=f"proposal-{day_offset}-{index}",
        evidence_bundle_id=f"bundle-{day_offset}-{index}",
        decision=Signal.HOLD,
        actionable=False,
        master_confidence=0.0,
        disagreement=0.0,
        contradiction=0.0,
    )


def _finding(
    signal: FindingSignal,
    reason: str,
    sources: tuple[str, ...],
    value: float,
) -> ReflectionFinding:
    return ReflectionFinding(
        category=FindingCategory.DIRECTION_OUTCOME,
        signal=signal,
        reason_code=reason,
        scope="direction",
        scope_value="BUY",
        sample_size=len(sources),
        metrics=(MetricFact(name="average_r", value=value, unit="R"),),
        supporting_experience_ids=sources,
    )


def _daily(day_offset: int, experiences: tuple[DecisionExperience, ...]) -> DailyReflection:
    day_start = START + timedelta(days=day_offset)
    sources = tuple(item.experience_id for item in experiences)
    return DailyReflection(
        period_start=day_start,
        period_end=day_start + timedelta(days=1),
        available_at=day_start + timedelta(days=1),
        policy_id=DAILY_POLICY.policy_id,
        input_experience_ids=sources,
        findings=(
            _finding(FindingSignal.POSITIVE, "POSITIVE_AVERAGE_R", sources, 0.5 + day_offset),
            _finding(FindingSignal.NEGATIVE, "NEGATIVE_AVERAGE_R", sources, -0.5 - day_offset),
        ),
    )


def _week(days: int = 7) -> tuple[tuple[DailyReflection, ...], tuple[DecisionExperience, ...]]:
    experiences = tuple(
        _experience(index, day_offset)
        for day_offset in range(days)
        for index in range(3)
    )
    daily = tuple(
        _daily(
            day_offset,
            tuple(
                item
                for item in experiences
                if item.available_at.date()
                == (START + timedelta(days=day_offset)).date()
            ),
        )
        for day_offset in range(days)
    )
    return daily, experiences


def test_complete_week_builds_guarded_success_and_failure_patterns_deterministically() -> None:
    daily, experiences = _week()
    first = build_weekly_reflection(daily, experiences, START.date(), WEEKLY_POLICY)
    reordered = build_weekly_reflection(
        reversed(daily), reversed(experiences), START.date(), WEEKLY_POLICY
    )

    assert first == reordered
    assert first.present_daily_periods == tuple(
        START.date() + timedelta(days=index) for index in range(7)
    )
    assert first.missing_daily_periods == ()
    assert len(first.success_patterns) == 1
    assert len(first.failure_patterns) == 1
    success_metric = first.success_patterns[0].metrics[0]
    assert (
        success_metric.count,
        success_metric.minimum,
        success_metric.maximum,
        success_metric.mean,
    ) == (
        7,
        0.5,
        6.5,
        3.5,
    )
    assert all(guard.status is SampleGuardStatus.PASSED for guard in first.sample_guards)


def test_incomplete_week_records_five_missing_days_and_suppresses_patterns() -> None:
    daily, experiences = _week(days=2)
    reflection = build_weekly_reflection(daily, experiences, START.date(), WEEKLY_POLICY)
    completeness = next(
        guard
        for guard in reflection.sample_guards
        if guard.guard_kind is WeeklyGuardKind.WEEK_COMPLETENESS
    )

    assert reflection.present_daily_periods == (date(2026, 8, 10), date(2026, 8, 11))
    assert reflection.missing_daily_periods == tuple(date(2026, 8, day) for day in range(12, 17))
    assert completeness.status is SampleGuardStatus.INSUFFICIENT
    assert reflection.success_patterns == ()
    assert reflection.failure_patterns == ()


def test_completed_revision_supersedes_incomplete_week_without_mutating_it() -> None:
    partial_daily, partial_experiences = _week(days=2)
    incomplete = build_weekly_reflection(
        partial_daily, partial_experiences, START.date(), WEEKLY_POLICY
    )
    daily, experiences = _week()
    complete = build_weekly_reflection(
        daily,
        experiences,
        START.date(),
        WEEKLY_POLICY,
        supersedes_weekly_reflection_id=incomplete.reflection_id,
    )

    assert incomplete.missing_daily_periods
    assert complete.missing_daily_periods == ()
    assert complete.supersedes_weekly_reflection_id == incomplete.reflection_id
    assert complete.reflection_id != incomplete.reflection_id


def test_under_supported_pattern_emits_guards_without_pattern() -> None:
    daily, experiences = _week()
    strict = WeeklyReflectionPolicy(
        daily_policy_id=DAILY_POLICY.policy_id,
        min_pattern_days=7,
        min_pattern_experiences=22,
    )
    reflection = build_weekly_reflection(daily, experiences, START.date(), strict)

    assert reflection.success_patterns == ()
    assert reflection.failure_patterns == ()
    experience_guards = tuple(
        guard
        for guard in reflection.sample_guards
        if guard.guard_kind is WeeklyGuardKind.PATTERN_EXPERIENCE_SUPPORT
    )
    assert len(experience_guards) == 2
    assert all(guard.status is SampleGuardStatus.INSUFFICIENT for guard in experience_guards)


def test_exact_provenance_failure_and_duplicate_experience_fail_closed() -> None:
    daily, experiences = _week()
    broken_finding = _finding(
        FindingSignal.NEGATIVE,
        "NEGATIVE_AVERAGE_R",
        ("missing-experience",),
        -1.0,
    )
    broken = DailyReflection(
        **daily[0].model_dump(exclude={"reflection_id", "findings"}),
        findings=(broken_finding,),
    )

    with pytest.raises(ValueError, match="finding source is not a daily input"):
        build_weekly_reflection((broken, *daily[1:]), experiences, START.date(), WEEKLY_POLICY)
    with pytest.raises(ValueError, match="duplicate Experience identity"):
        build_weekly_reflection(daily, (*experiences, experiences[0]), START.date(), WEEKLY_POLICY)


def test_daily_revision_chain_selects_terminal_and_rejects_missing_or_branching_links() -> None:
    daily, experiences = _week()
    original = daily[0]
    revised = DailyReflection(
        **original.model_dump(exclude={"reflection_id", "supersedes_reflection_id"}),
        supersedes_reflection_id=original.reflection_id,
    )
    selected = build_weekly_reflection(
        (original, revised, *daily[1:]), experiences, START.date(), WEEKLY_POLICY
    )
    assert revised.reflection_id in selected.input_daily_reflection_ids
    assert original.reflection_id not in selected.input_daily_reflection_ids

    with pytest.raises(ValueError, match="missing daily predecessor"):
        build_weekly_reflection((revised, *daily[1:]), experiences, START.date(), WEEKLY_POLICY)
    branch = DailyReflection(
        **original.model_dump(
            exclude={"reflection_id", "supersedes_reflection_id", "available_at"}
        ),
        available_at=original.available_at + timedelta(seconds=1),
        supersedes_reflection_id=original.reflection_id,
    )
    with pytest.raises(ValueError, match="branched daily revision"):
        build_weekly_reflection(
            (original, revised, branch, *daily[1:]),
            experiences,
            START.date(),
            WEEKLY_POLICY,
        )


def test_non_monday_week_start_is_rejected() -> None:
    daily, experiences = _week()
    with pytest.raises(ValueError, match="Monday"):
        build_weekly_reflection(daily, experiences, START.date() + timedelta(days=1), WEEKLY_POLICY)
