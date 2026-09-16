from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, timedelta

import pytest

from axq.reflection import FindingCategory, FindingSignal, SampleGuardStatus
from axq.reflection.weekly_contracts import (
    FailurePattern,
    KnowledgeStatus,
    PatternSignalClass,
    PatternStatusTransition,
    TransitionActionKind,
    WeeklyGuardKind,
    WeeklyReflection,
    WeeklyReflectionPolicy,
    WeeklySampleGuard,
)
from axq.reflection.weekly_store import SQLiteWeeklyReflectionStore

START = datetime(2026, 8, 10, tzinfo=UTC)


def _pattern() -> FailurePattern:
    return FailurePattern(
        category=FindingCategory.DIRECTION_OUTCOME,
        signal_class=PatternSignalClass.ADVERSE,
        source_signal=FindingSignal.NEGATIVE,
        reason_code="NEGATIVE_AVERAGE_R",
        scope="direction",
        scope_value="BUY",
        week_start=START,
        week_end=START + timedelta(days=7),
        sample_days=(date(2026, 8, 10), date(2026, 8, 11)),
        sample_count=3,
        supporting_daily_reflection_ids=("daily-1", "daily-2"),
        supporting_finding_ids=("finding-1", "finding-2"),
        supporting_experience_ids=("experience-1", "experience-2", "experience-3"),
    )


def _reflection(
    policy: WeeklyReflectionPolicy,
    *,
    sources: tuple[str, ...] = ("experience-1", "experience-2", "experience-3"),
    supersedes: str | None = None,
) -> WeeklyReflection:
    dates = tuple(START.date() + timedelta(days=index) for index in range(7))
    guard = WeeklySampleGuard(
        guard_kind=WeeklyGuardKind.WEEK_COMPLETENESS,
        scope="week",
        scope_value="2026-W33",
        observed_samples=7,
        required_samples=7,
        status=SampleGuardStatus.PASSED,
        present_daily_periods=dates,
        supporting_daily_reflection_ids=tuple(f"daily-{index}" for index in range(7)),
    )
    return WeeklyReflection(
        week_start=START,
        week_end=START + timedelta(days=7),
        available_at=START + timedelta(days=7),
        weekly_policy_id=policy.policy_id,
        daily_policy_id=policy.daily_policy_id,
        present_daily_periods=dates,
        missing_daily_periods=(),
        input_daily_reflection_ids=tuple(f"daily-{index}" for index in range(7)),
        input_experience_ids=sources,
        sample_guards=(guard,),
        failure_patterns=(_pattern(),),
        supersedes_weekly_reflection_id=supersedes,
    )


def _transition(
    pattern: FailurePattern,
    from_status: KnowledgeStatus,
    to_status: KnowledgeStatus,
    index: int,
    previous: str | None = None,
) -> PatternStatusTransition:
    return PatternStatusTransition(
        pattern_id=pattern.pattern_id,
        pattern_key=pattern.pattern_key,
        from_status=from_status,
        to_status=to_status,
        effective_at=START + timedelta(days=7, minutes=index),
        action_kind=TransitionActionKind.OPERATOR,
        actor_id="operator-1",
        action_id=f"action-{index}",
        reason_code="EXPLICIT_REVIEW",
        previous_transition_id=previous,
    )


def test_weekly_store_is_idempotent_and_indexes_exact_sources(tmp_path) -> None:
    store = SQLiteWeeklyReflectionStore(tmp_path / "weekly.sqlite3")
    policy = WeeklyReflectionPolicy(daily_policy_id="daily-policy-1")
    reflection = _reflection(policy)

    assert store.append_policy(policy) is True
    assert store.append_policy(policy) is False
    assert store.append(reflection) is True
    assert store.append(reflection) is False
    assert store.latest(START, policy.policy_id) == reflection
    assert store.reflections() == (reflection,)
    assert store.by_experience_id("experience-2") == (reflection,)
    assert store.pattern(reflection.failure_patterns[0].pattern_id) == _pattern()


def test_changed_week_requires_explicit_latest_supersession(tmp_path) -> None:
    store = SQLiteWeeklyReflectionStore(tmp_path / "weekly.sqlite3")
    policy = WeeklyReflectionPolicy(daily_policy_id="daily-policy-1")
    store.append_policy(policy)
    original = _reflection(policy)
    store.append(original)

    with pytest.raises(ValueError, match="supersede latest"):
        store.append(_reflection(policy, sources=(*original.input_experience_ids, "experience-4")))
    revised = _reflection(
        policy,
        sources=(*original.input_experience_ids, "experience-4"),
        supersedes=original.reflection_id,
    )
    assert store.append(revised) is True
    assert store.latest(START, policy.policy_id) == revised
    assert store.reflections() == (original, revised)


def test_lifecycle_replays_only_explicit_linear_forward_transitions(tmp_path) -> None:
    store = SQLiteWeeklyReflectionStore(tmp_path / "weekly.sqlite3")
    policy = WeeklyReflectionPolicy(daily_policy_id="daily-policy-1")
    reflection = _reflection(policy)
    pattern = reflection.failure_patterns[0]
    store.append_policy(policy)
    store.append(reflection)
    transitions: list[PatternStatusTransition] = []
    previous: str | None = None
    edges = (
        (KnowledgeStatus.OBSERVATION, KnowledgeStatus.HYPOTHESIS),
        (KnowledgeStatus.HYPOTHESIS, KnowledgeStatus.CANDIDATE),
        (KnowledgeStatus.CANDIDATE, KnowledgeStatus.VALIDATED),
        (KnowledgeStatus.VALIDATED, KnowledgeStatus.DEPRECATED),
    )
    for index, (source, target) in enumerate(edges, start=1):
        transition = _transition(pattern, source, target, index, previous)
        assert store.append_transition(transition) is True
        assert store.append_transition(transition) is False
        transitions.append(transition)
        previous = transition.transition_id

    assert store.transition_history(pattern.pattern_id) == tuple(transitions)
    assert store.current_status(pattern.pattern_id) is KnowledgeStatus.DEPRECATED


def test_lifecycle_fails_closed_on_unknown_stale_or_wrong_link(tmp_path) -> None:
    store = SQLiteWeeklyReflectionStore(tmp_path / "weekly.sqlite3")
    policy = WeeklyReflectionPolicy(daily_policy_id="daily-policy-1")
    reflection = _reflection(policy)
    pattern = reflection.failure_patterns[0]
    store.append_policy(policy)
    store.append(reflection)
    first = _transition(pattern, KnowledgeStatus.OBSERVATION, KnowledgeStatus.HYPOTHESIS, 1)
    store.append_transition(first)

    with pytest.raises(ValueError, match="current status"):
        store.append_transition(
            _transition(
                pattern,
                KnowledgeStatus.OBSERVATION,
                KnowledgeStatus.REJECTED,
                2,
                first.transition_id,
            )
        )
    with pytest.raises(ValueError, match="previous transition"):
        store.append_transition(
            _transition(pattern, KnowledgeStatus.HYPOTHESIS, KnowledgeStatus.CANDIDATE, 2)
        )
    unknown = first.model_copy(update={"pattern_id": "weekly-pattern-unknown"})
    with pytest.raises(ValueError, match="pattern is not persisted"):
        store.append_transition(unknown)


def test_weekly_tables_are_append_only(tmp_path) -> None:
    path = tmp_path / "weekly.sqlite3"
    store = SQLiteWeeklyReflectionStore(path)
    policy = WeeklyReflectionPolicy(daily_policy_id="daily-policy-1")
    reflection = _reflection(policy)
    store.append_policy(policy)
    store.append(reflection)

    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE weekly_reflections SET daily_policy_id = 'changed' WHERE reflection_id = ?",
                (reflection.reflection_id,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "DELETE FROM weekly_patterns WHERE pattern_id = ?",
                (reflection.failure_patterns[0].pattern_id,),
            )
