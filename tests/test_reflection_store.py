from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from axq.reflection import DailyReflection, ReflectionPolicy
from axq.reflection.store import SQLiteReflectionStore

START = datetime(2026, 8, 10, tzinfo=UTC)


def _reflection(
    policy: ReflectionPolicy,
    *,
    sources: tuple[str, ...] = ("experience-1",),
    supersedes: str | None = None,
) -> DailyReflection:
    return DailyReflection(
        period_start=START,
        period_end=START + timedelta(days=1),
        available_at=START + timedelta(days=1),
        policy_id=policy.policy_id,
        input_experience_ids=sources,
        supersedes_reflection_id=supersedes,
    )


def test_policy_and_reflection_append_are_idempotent(tmp_path) -> None:
    store = SQLiteReflectionStore(tmp_path / "reflections.sqlite3")
    policy = ReflectionPolicy()
    reflection = _reflection(policy)

    assert store.append_policy(policy) is True
    assert store.append_policy(policy) is False
    assert store.append(reflection) is True
    assert store.append(reflection) is False
    assert store.latest(START, policy.policy_id) == reflection
    assert store.reflections() == (reflection,)


def test_changed_same_day_requires_explicit_latest_supersession(tmp_path) -> None:
    store = SQLiteReflectionStore(tmp_path / "reflections.sqlite3")
    policy = ReflectionPolicy()
    store.append_policy(policy)
    original = _reflection(policy)
    store.append(original)
    revised_without_link = _reflection(policy, sources=("experience-1", "experience-2"))

    with pytest.raises(ValueError, match="supersede latest"):
        store.append(revised_without_link)

    revised = _reflection(
        policy,
        sources=("experience-1", "experience-2"),
        supersedes=original.reflection_id,
    )
    assert store.append(revised) is True
    assert store.latest(START, policy.policy_id) == revised
    assert store.reflections() == (original, revised)
    assert store.by_experience_id("experience-2") == (revised,)


def test_first_reflection_cannot_claim_supersession_and_policy_must_exist(tmp_path) -> None:
    store = SQLiteReflectionStore(tmp_path / "reflections.sqlite3")
    policy = ReflectionPolicy()
    linked = _reflection(policy, supersedes="daily-reflection-missing")

    with pytest.raises(ValueError, match="policy is not persisted"):
        store.append(linked)

    store.append_policy(policy)
    with pytest.raises(ValueError, match="first reflection cannot supersede"):
        store.append(linked)


def test_reflection_tables_reject_update_and_delete(tmp_path) -> None:
    path = tmp_path / "reflections.sqlite3"
    store = SQLiteReflectionStore(path)
    policy = ReflectionPolicy()
    reflection = _reflection(policy)
    store.append_policy(policy)
    store.append(reflection)

    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE daily_reflections SET policy_id = 'changed' WHERE reflection_id = ?",
                (reflection.reflection_id,),
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "DELETE FROM daily_reflections WHERE reflection_id = ?",
                (reflection.reflection_id,),
            )


def test_reopened_store_preserves_canonical_json(tmp_path) -> None:
    path = tmp_path / "reflections.sqlite3"
    policy = ReflectionPolicy()
    reflection = _reflection(policy)
    store = SQLiteReflectionStore(path)
    store.append_policy(policy)
    store.append(reflection)
    store.sync()

    reopened = SQLiteReflectionStore(path)
    assert reopened.policy(policy.policy_id) == policy
    assert reopened.reflections() == (reflection,)
