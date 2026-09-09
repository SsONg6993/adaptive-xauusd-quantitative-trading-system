"""Idempotent append-only journaling for the position-management action chain."""

from __future__ import annotations

from axq.position_actions.contracts import (
    PositionActionIntent,
    PositionActionSafetyOutcome,
    PositionActionSafetyResult,
)
from axq.position_management import PositionManagementOutcome
from axq.runtime.journal import JournalEntry, JournalRecord, RuntimeJournal


def append_position_action_chain(
    journal: RuntimeJournal,
    management: PositionManagementOutcome,
    safety: PositionActionSafetyOutcome,
    intent: PositionActionIntent | None,
) -> tuple[JournalEntry, ...]:
    """Append missing deterministic chain records and return their durable entries."""
    if safety.position_management_outcome_id != management.outcome_id:
        raise ValueError("safety outcome references a different management outcome")
    if (safety.result is PositionActionSafetyResult.PASS) != (intent is not None):
        raise ValueError("exactly passed safety outcomes require a position-action intent")
    if intent is not None and (
        intent.safety_outcome_id != safety.safety_outcome_id
        or intent.position_management_outcome_id != management.outcome_id
    ):
        raise ValueError("position-action intent does not continue this semantic chain")

    parent = management.position_id
    records = [
        JournalRecord.from_semantic(
            management,
            event_id=None,
            parent_id=parent,
            previous_id=management.original_execution_result_id,
        ),
        JournalRecord.from_semantic(
            safety,
            event_id=None,
            parent_id=parent,
            previous_id=management.outcome_id,
        ),
    ]
    if intent is not None:
        records.append(
            JournalRecord.from_semantic(
                intent,
                event_id=None,
                parent_id=parent,
                previous_id=safety.safety_outcome_id,
            )
        )

    existing_entries = journal.records()
    by_record_id = {entry.record.record_id: entry for entry in existing_entries}
    by_semantic_key = {
        (entry.record.record_type, entry.record.semantic_id): entry
        for entry in existing_entries
    }
    appended: list[JournalEntry] = []
    for record in records:
        existing = by_record_id.get(record.record_id)
        if existing is not None:
            appended.append(existing)
            continue
        semantic_key = (record.record_type, record.semantic_id)
        conflict = by_semantic_key.get(semantic_key)
        if conflict is not None:
            raise ValueError("journal contains conflicting linkage for deterministic semantic ID")
        entry = journal.append(record)
        appended.append(entry)
        by_record_id[record.record_id] = entry
        by_semantic_key[semantic_key] = entry
    return tuple(appended)
