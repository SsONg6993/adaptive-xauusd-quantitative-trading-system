from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.reflection import FindingCategory, FindingSignal, SampleGuardStatus
from axq.reflection.weekly_contracts import (
    FailurePattern,
    KnowledgeStatus,
    PatternMetricSummary,
    PatternSignalClass,
    PatternStatusTransition,
    PatternType,
    SuccessPattern,
    TransitionActionKind,
    WeeklyGuardKind,
    WeeklyReflection,
    WeeklyReflectionPolicy,
    WeeklySampleGuard,
)

START = datetime(2026, 8, 10, tzinfo=UTC)
END = START + timedelta(days=7)


def _pattern(
    *,
    week_start: datetime = START,
    evidence: str = "experience-1",
) -> FailurePattern:
    return FailurePattern(
        category=FindingCategory.DIRECTION_OUTCOME,
        signal_class=PatternSignalClass.ADVERSE,
        source_signal=FindingSignal.NEGATIVE,
        reason_code="NEGATIVE_AVERAGE_R",
        scope="direction",
        scope_value="BUY",
        week_start=week_start,
        week_end=week_start + timedelta(days=7),
        sample_days=(week_start.date(), week_start.date() + timedelta(days=1)),
        sample_count=3,
        metrics=(
            PatternMetricSummary(
                name="average_r", unit="R", count=2, minimum=-0.5, maximum=-0.1, mean=-0.3
            ),
        ),
        supporting_daily_reflection_ids=("daily-2", "daily-1"),
        supporting_finding_ids=("finding-2", "finding-1"),
        supporting_experience_ids=(evidence,),
    )


def _completeness(*, complete: bool) -> WeeklySampleGuard:
    present = tuple(START.date() + timedelta(days=index) for index in range(7 if complete else 2))
    missing = tuple(START.date() + timedelta(days=index) for index in range(2, 7))
    return WeeklySampleGuard(
        guard_kind=WeeklyGuardKind.WEEK_COMPLETENESS,
        scope="week",
        scope_value="2026-W33",
        observed_samples=len(present),
        required_samples=7,
        status=SampleGuardStatus.PASSED if complete else SampleGuardStatus.INSUFFICIENT,
        present_daily_periods=present,
        missing_daily_periods=() if complete else missing,
        supporting_daily_reflection_ids=tuple(f"daily-{index}" for index in range(len(present))),
    )


def test_pattern_key_uses_exact_six_field_semantics_but_observation_id_uses_week() -> None:
    first = _pattern()
    later = _pattern(week_start=START + timedelta(days=7), evidence="experience-2")

    assert first.pattern_key == later.pattern_key
    assert first.pattern_id != later.pattern_id
    assert first.pattern_type is PatternType.FAILURE
    assert first.knowledge_status is KnowledgeStatus.OBSERVATION
    assert first.supporting_daily_reflection_ids == ("daily-1", "daily-2")


def test_success_and_failure_patterns_cannot_start_promoted() -> None:
    success = SuccessPattern(
        category=FindingCategory.SESSION_OUTCOME,
        signal_class=PatternSignalClass.POSITIVE,
        source_signal=FindingSignal.POSITIVE,
        reason_code="POSITIVE_AVERAGE_R",
        scope="session",
        scope_value="LONDON",
        week_start=START,
        week_end=END,
        sample_days=(START.date(), START.date() + timedelta(days=1)),
        sample_count=3,
        metrics=(),
        supporting_daily_reflection_ids=("daily-1", "daily-2"),
        supporting_finding_ids=("finding-1", "finding-2"),
        supporting_experience_ids=("experience-1", "experience-2", "experience-3"),
    )
    assert success.pattern_type is PatternType.SUCCESS
    with pytest.raises(ValidationError, match="OBSERVATION"):
        FailurePattern.model_validate(
            _pattern().model_dump()
            | {"pattern_id": "", "knowledge_status": KnowledgeStatus.HYPOTHESIS}
        )


def test_weekly_contract_enforces_iso_week_and_suppresses_incomplete_patterns() -> None:
    policy = WeeklyReflectionPolicy(daily_policy_id="daily-policy-1")
    complete = WeeklyReflection(
        week_start=START,
        week_end=END,
        available_at=END,
        weekly_policy_id=policy.policy_id,
        daily_policy_id=policy.daily_policy_id,
        present_daily_periods=tuple(START.date() + timedelta(days=index) for index in range(7)),
        missing_daily_periods=(),
        input_daily_reflection_ids=tuple(f"daily-{index}" for index in range(7)),
        input_experience_ids=("experience-1",),
        sample_guards=(_completeness(complete=True),),
        failure_patterns=(_pattern(),),
    )
    assert complete.reflection_id.startswith("weekly-reflection-")

    with pytest.raises(ValidationError, match="guard periods must match"):
        WeeklyReflection.model_validate(
            complete.model_dump()
            | {
                "reflection_id": "",
                "sample_guards": (_completeness(complete=False),),
            }
        )
    with pytest.raises(ValidationError, match="complete week cannot be available"):
        WeeklyReflection.model_validate(
            complete.model_dump()
            | {"reflection_id": "", "available_at": START + timedelta(days=6)}
        )

    with pytest.raises(ValidationError, match="incomplete week cannot contain patterns"):
        WeeklyReflection(
            week_start=START,
            week_end=END,
            available_at=START + timedelta(days=3),
            weekly_policy_id=policy.policy_id,
            daily_policy_id=policy.daily_policy_id,
            present_daily_periods=(date(2026, 8, 10), date(2026, 8, 11)),
            missing_daily_periods=tuple(date(2026, 8, day) for day in range(12, 17)),
            input_daily_reflection_ids=("daily-1", "daily-2"),
            sample_guards=(_completeness(complete=False),),
            failure_patterns=(_pattern(),),
        )
    with pytest.raises(ValidationError, match="Monday"):
        WeeklyReflection.model_validate(
            complete.model_dump()
            | {
                "reflection_id": "",
                "week_start": START + timedelta(days=1),
                "week_end": END + timedelta(days=1),
            }
        )


def test_transition_is_explicit_utc_content_and_valid_forward_edge() -> None:
    pattern = _pattern()
    transition = PatternStatusTransition(
        pattern_id=pattern.pattern_id,
        pattern_key=pattern.pattern_key,
        from_status=KnowledgeStatus.OBSERVATION,
        to_status=KnowledgeStatus.HYPOTHESIS,
        effective_at=END,
        action_kind=TransitionActionKind.OPERATOR,
        actor_id="operator-1",
        action_id="review-2026-w33",
        reason_code="REPEATED_EVIDENCE_REVIEWED",
        supporting_evaluation_ids=("evaluation-2", "evaluation-1"),
    )
    restored = PatternStatusTransition.model_validate_json(transition.model_dump_json())

    assert transition == restored
    assert transition.transition_id.startswith("pattern-transition-")
    assert transition.supporting_evaluation_ids == ("evaluation-1", "evaluation-2")
    with pytest.raises(ValidationError, match="allowed"):
        PatternStatusTransition(
            **transition.model_dump(exclude={"transition_id", "to_status"}),
            to_status=KnowledgeStatus.VALIDATED,
        )
    with pytest.raises(ValidationError, match="timezone-aware"):
        PatternStatusTransition(
            **transition.model_dump(exclude={"transition_id", "effective_at"}),
            effective_at=datetime(2026, 8, 17),
        )


def test_weekly_policy_and_guards_are_content_addressed_and_frozen() -> None:
    policy = WeeklyReflectionPolicy(daily_policy_id="daily-policy-1")
    same = WeeklyReflectionPolicy.model_validate_json(policy.model_dump_json())
    guard = _completeness(complete=False)

    assert policy == same
    assert policy.policy_id.startswith("weekly-reflection-policy-")
    assert guard.guard_id.startswith("weekly-sample-guard-")
    assert guard.missing_daily_periods == tuple(date(2026, 8, day) for day in range(12, 17))
    with pytest.raises(ValidationError):
        policy.min_pattern_days = 4  # type: ignore[misc]
