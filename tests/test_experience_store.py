from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from axq.experience import DecisionExperience, ExperienceProvenance, ExperienceType
from axq.experience.store import SQLiteExperienceStore
from axq.schemas import Signal

T0 = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def _decision(*, offset: int = 0, proposal_id: str = "mp-1") -> DecisionExperience:
    at = T0 + timedelta(minutes=offset)
    return DecisionExperience(
        occurred_at=at,
        available_at=at,
        symbol="XAUUSD",
        outcome="HOLD",
        provenance=ExperienceProvenance(
            runtime_event_ids=(f"ev-{offset}",),
            evidence_bundle_ids=(f"bundle-{offset}",),
            master_proposal_ids=(proposal_id,),
        ),
        master_proposal_id=proposal_id,
        evidence_bundle_id=f"bundle-{offset}",
        decision=Signal.HOLD,
        actionable=False,
        master_confidence=0.0,
        disagreement=0.0,
        contradiction=0.0,
    )


def test_duplicate_semantic_insert_is_idempotent(tmp_path) -> None:
    store = SQLiteExperienceStore(tmp_path / "experiences.sqlite3")
    experience = _decision()

    assert store.append(experience) is True
    assert store.append(experience) is False
    assert store.counts() == {ExperienceType.DECISION: 1}
    assert store.experiences() == (experience,)


def test_conflicting_same_id_content_fails_closed(tmp_path) -> None:
    store = SQLiteExperienceStore(tmp_path / "experiences.sqlite3")
    original = _decision()
    assert store.append(original)
    payload = dict(original.__dict__) | {"outcome": "BUY"}
    conflicting = DecisionExperience.model_construct(**payload)

    with pytest.raises(ValueError, match="different content"):
        store.append(conflicting)


def test_store_orders_by_semantic_time_and_indexes_source_ids(tmp_path) -> None:
    store = SQLiteExperienceStore(tmp_path / "experiences.sqlite3")
    later = _decision(offset=5, proposal_id="mp-later")
    earlier = _decision(offset=0, proposal_id="mp-earlier")
    store.append_many((later, earlier))

    assert store.experiences() == (earlier, later)
    assert store.by_source_id("mp-later") == (later,)


def test_sqlite_update_and_delete_are_rejected(tmp_path) -> None:
    path = tmp_path / "experiences.sqlite3"
    store = SQLiteExperienceStore(path)
    store.append(_decision())

    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE experience_records SET outcome = 'BUY' WHERE experience_sequence = 1"
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM experience_records WHERE experience_sequence = 1")


def test_store_preserves_payload_across_reopen(tmp_path) -> None:
    path = tmp_path / "experiences.sqlite3"
    expected = _decision()
    SQLiteExperienceStore(path).append(expected)

    reopened = SQLiteExperienceStore(path)
    assert reopened.experiences(ExperienceType.DECISION) == (expected,)
