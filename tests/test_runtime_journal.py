from __future__ import annotations

from datetime import UTC, datetime, timedelta

from axq.runtime import (
    ComponentFreshness,
    FreshnessStatus,
    MarketState,
    RuntimeEvent,
    RuntimeEventType,
    initial_runtime_state,
)
from axq.runtime.journal import (
    JournalOutcome,
    JournalOutcomeStatus,
    JournalRecordType,
    SQLiteRuntimeJournal,
)
from axq.tools import CausalFeatureSnapshot

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _event(at: datetime, sequence: int) -> RuntimeEvent:
    freshness = ComponentFreshness(
        component="market",
        status=FreshnessStatus.AVAILABLE,
        observed_at=at,
        available_at=at,
        stale_after_ms=300_000,
    )
    market = MarketState(
        source="mt5",
        symbol="XAUUSD",
        as_of=at,
        freshness=freshness,
        bid=2500.0 + sequence,
        ask=2500.2 + sequence,
        last=2500.1 + sequence,
        spread_points=20.0,
        base_timeframe="M5",
        completed_timeframes=("M5",),
        feature_manifest_id="fm-test",
    )
    return RuntimeEvent(
        event_type=RuntimeEventType.M5_CLOSED,
        event_time=at,
        observed_at=at,
        available_at=at,
        source="mt5",
        source_version="1.0.0",
        source_sequence=sequence,
        symbol="XAUUSD",
        payload=market,
    )


def _snapshot(event: RuntimeEvent) -> CausalFeatureSnapshot:
    return CausalFeatureSnapshot.from_mapping(
        symbol="XAUUSD",
        base_timeframe="M5",
        as_of=event.available_at,
        available_at=event.available_at,
        feature_manifest_id="fm-test",
        completed_timeframes=("M5",),
        values={"structure_bos_up": True},
        source="phase2-feature-engine",
        source_version="2.0.0",
    )


def test_journal_round_trip_preserves_typed_semantic_identity(tmp_path) -> None:
    event = _event(T0, 1)
    snapshot = _snapshot(event)
    state = initial_runtime_state("XAUUSD", at=T0)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")

    journal.append_semantic(event, event_id=event.event_id)
    journal.append_semantic(snapshot, event_id=event.event_id)
    journal.append_semantic(state, event_id=event.event_id)
    records = journal.records()

    assert [entry.sequence for entry in records] == [1, 2, 3]
    assert records[0].record.decode() == event
    assert records[1].record.decode() == snapshot
    assert records[2].record.decode() == state
    assert records[0].record.semantic_id == event.event_id
    assert records[0].record.record_id != event.event_id


def test_journal_is_append_only_and_keeps_deterministic_order(tmp_path) -> None:
    first = _event(T0, 1)
    second = _event(T0 + timedelta(minutes=5), 2)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")

    first_entry = journal.append_semantic(first, event_id=first.event_id)
    journal.append_semantic(second, event_id=second.event_id)

    assert journal.records()[0] == first_entry
    assert tuple(journal.events()) == (first, second)


def test_journal_replay_orders_events_by_causal_availability(tmp_path) -> None:
    earlier = _event(T0, 1)
    later = _event(T0 + timedelta(minutes=5), 2)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    journal.append_semantic(later, event_id=later.event_id)
    journal.append_semantic(earlier, event_id=earlier.event_id)

    assert tuple(item.event_id for item in journal.events()) == (
        earlier.event_id,
        later.event_id,
    )


def test_rejection_outcome_is_structured_and_does_not_replace_event(tmp_path) -> None:
    event = _event(T0, 1)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    journal.append_semantic(event, event_id=event.event_id)
    outcome = JournalOutcome(
        status=JournalOutcomeStatus.REJECTED,
        reason_code="SOURCE_SEQUENCE_COLLISION",
        message="source sequence collision",
    )

    journal.append_outcome(event, outcome)
    records = journal.records()

    assert records[0].record.record_type is JournalRecordType.RUNTIME_EVENT
    assert records[1].record.record_type is JournalRecordType.OUTCOME
    assert records[1].record.decode() == outcome
    assert tuple(journal.events()) == ()


def test_feature_snapshots_can_be_recovered_by_event_without_mutation(tmp_path) -> None:
    event = _event(T0, 1)
    snapshot = _snapshot(event)
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    journal.append_semantic(snapshot, event_id=event.event_id)

    recovered = journal.feature_snapshots()

    assert recovered == {event.event_id: snapshot}
    assert recovered[event.event_id].snapshot_id == snapshot.snapshot_id
