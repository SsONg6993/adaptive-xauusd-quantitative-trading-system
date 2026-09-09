"""Typed append-only runtime journal for deterministic replay."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from enum import StrEnum
from pathlib import Path
from typing import Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.agents import AgentEvidence, AgentInput, AgentMemory, ScenarioState, ThesisState
from axq.position_actions.contracts import PositionActionIntent, PositionActionSafetyOutcome
from axq.position_management import PositionManagementOutcome
from axq.runtime.events import RuntimeEvent
from axq.runtime.kernel import EvidenceBundle
from axq.runtime.state import SharedRuntimeState, UTCDateTime
from axq.tools import CausalFeatureSnapshot, ToolResult
from axq.versioning import canonical_hash


class JournalRecordType(StrEnum):
    RUNTIME_EVENT = "RUNTIME_EVENT"
    RUNTIME_STATE = "RUNTIME_STATE"
    FEATURE_SNAPSHOT = "FEATURE_SNAPSHOT"
    TOOL_RESULT = "TOOL_RESULT"
    AGENT_INPUT = "AGENT_INPUT"
    AGENT_EVIDENCE = "AGENT_EVIDENCE"
    AGENT_MEMORY = "AGENT_MEMORY"
    EVIDENCE_BUNDLE = "EVIDENCE_BUNDLE"
    THESIS_STATE = "THESIS_STATE"
    SCENARIO_STATE = "SCENARIO_STATE"
    POSITION_MANAGEMENT_OUTCOME = "POSITION_MANAGEMENT_OUTCOME"
    POSITION_ACTION_SAFETY_OUTCOME = "POSITION_ACTION_SAFETY_OUTCOME"
    POSITION_ACTION_INTENT = "POSITION_ACTION_INTENT"
    OUTCOME = "OUTCOME"


class JournalOutcomeStatus(StrEnum):
    APPLIED = "APPLIED"
    DUPLICATE = "DUPLICATE"
    NO_OP = "NO_OP"
    REJECTED = "REJECTED"


class JournalOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    outcome_id: str = ""
    status: JournalOutcomeStatus
    reason_code: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def bind_identity(self) -> JournalOutcome:
        identity = self.model_dump(mode="json", exclude={"outcome_id"})
        expected = f"jo-{canonical_hash(identity)[:20]}"
        if self.outcome_id and self.outcome_id != expected:
            raise ValueError("outcome_id does not match outcome content")
        object.__setattr__(self, "outcome_id", expected)
        return self


JournalSemantic = (
    RuntimeEvent
    | SharedRuntimeState
    | CausalFeatureSnapshot
    | ToolResult
    | AgentInput
    | AgentEvidence
    | AgentMemory
    | EvidenceBundle
    | ThesisState
    | ScenarioState
    | PositionManagementOutcome
    | PositionActionSafetyOutcome
    | PositionActionIntent
    | JournalOutcome
)

_MODEL_BY_RECORD_TYPE: dict[JournalRecordType, type[BaseModel]] = {
    JournalRecordType.RUNTIME_EVENT: RuntimeEvent,
    JournalRecordType.RUNTIME_STATE: SharedRuntimeState,
    JournalRecordType.FEATURE_SNAPSHOT: CausalFeatureSnapshot,
    JournalRecordType.TOOL_RESULT: ToolResult,
    JournalRecordType.AGENT_INPUT: AgentInput,
    JournalRecordType.AGENT_EVIDENCE: AgentEvidence,
    JournalRecordType.AGENT_MEMORY: AgentMemory,
    JournalRecordType.EVIDENCE_BUNDLE: EvidenceBundle,
    JournalRecordType.THESIS_STATE: ThesisState,
    JournalRecordType.SCENARIO_STATE: ScenarioState,
    JournalRecordType.POSITION_MANAGEMENT_OUTCOME: PositionManagementOutcome,
    JournalRecordType.POSITION_ACTION_SAFETY_OUTCOME: PositionActionSafetyOutcome,
    JournalRecordType.POSITION_ACTION_INTENT: PositionActionIntent,
    JournalRecordType.OUTCOME: JournalOutcome,
}


def _record_type(value: JournalSemantic) -> JournalRecordType:
    types: tuple[tuple[type[BaseModel], JournalRecordType], ...] = (
        (RuntimeEvent, JournalRecordType.RUNTIME_EVENT),
        (SharedRuntimeState, JournalRecordType.RUNTIME_STATE),
        (CausalFeatureSnapshot, JournalRecordType.FEATURE_SNAPSHOT),
        (ToolResult, JournalRecordType.TOOL_RESULT),
        (AgentInput, JournalRecordType.AGENT_INPUT),
        (AgentEvidence, JournalRecordType.AGENT_EVIDENCE),
        (AgentMemory, JournalRecordType.AGENT_MEMORY),
        (EvidenceBundle, JournalRecordType.EVIDENCE_BUNDLE),
        (ThesisState, JournalRecordType.THESIS_STATE),
        (ScenarioState, JournalRecordType.SCENARIO_STATE),
        (PositionManagementOutcome, JournalRecordType.POSITION_MANAGEMENT_OUTCOME),
        (PositionActionSafetyOutcome, JournalRecordType.POSITION_ACTION_SAFETY_OUTCOME),
        (PositionActionIntent, JournalRecordType.POSITION_ACTION_INTENT),
        (JournalOutcome, JournalRecordType.OUTCOME),
    )
    for model_type, record_type in types:
        if isinstance(value, model_type):
            return record_type
    raise TypeError(f"unsupported journal semantic type: {type(value).__name__}")


def _semantic_id(value: JournalSemantic) -> str:
    fields = (
        "event_id",
        "state_id",
        "snapshot_id",
        "result_id",
        "input_id",
        "evidence_id",
        "memory_id",
        "bundle_id",
        "safety_outcome_id",
        "intent_id",
        "outcome_id",
    )
    for field in fields:
        candidate = getattr(value, field, None)
        if candidate:
            return str(candidate)
    raise ValueError(f"journal semantic object has no deterministic ID: {type(value).__name__}")


class JournalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    record_id: str = ""
    record_type: JournalRecordType
    semantic_id: str = Field(min_length=1)
    event_id: str | None = None
    parent_id: str | None = None
    previous_id: str | None = None
    event_time: UTCDateTime | None = None
    observed_at: UTCDateTime | None = None
    available_at: UTCDateTime
    source: str | None = None
    semantic_schema_version: str = Field(min_length=1)
    payload_json: str = Field(min_length=2)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> JournalRecord:
        model = _MODEL_BY_RECORD_TYPE[self.record_type]
        decoded = model.model_validate_json(self.payload_json)
        if _semantic_id(cast(JournalSemantic, decoded)) != self.semantic_id:
            raise ValueError("journal semantic ID does not match payload")
        if str(getattr(decoded, "schema_version", "")) != self.semantic_schema_version:
            raise ValueError("journal semantic schema version does not match payload")
        identity = self.model_dump(mode="json", exclude={"record_id"})
        expected = f"jr-{canonical_hash(identity)[:20]}"
        if self.record_id and self.record_id != expected:
            raise ValueError("record_id does not match journal record content")
        object.__setattr__(self, "record_id", expected)
        return self

    @classmethod
    def from_semantic(
        cls,
        value: JournalSemantic,
        *,
        event_id: str | None,
        parent_id: str | None = None,
        previous_id: str | None = None,
        available_at: UTCDateTime | None = None,
    ) -> JournalRecord:
        payload = json.dumps(
            value.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )
        event_time = getattr(value, "event_time", None)
        observed_at = getattr(value, "observed_at", None)
        causal_time = available_at or getattr(value, "available_at", None)
        if causal_time is None:
            causal_time = getattr(value, "as_of", None) or getattr(value, "updated_at", None)
        if causal_time is None:
            raise ValueError("journal record requires a causal availability timestamp")
        return cls(
            record_type=_record_type(value),
            semantic_id=_semantic_id(value),
            event_id=event_id,
            parent_id=parent_id,
            previous_id=previous_id,
            event_time=event_time,
            observed_at=observed_at,
            available_at=causal_time,
            source=getattr(value, "source", None),
            semantic_schema_version=str(value.schema_version),
            payload_json=payload,
        )

    def decode(self) -> BaseModel:
        return _MODEL_BY_RECORD_TYPE[self.record_type].model_validate_json(
            self.payload_json
        )


class JournalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sequence: int = Field(gt=0)
    record: JournalRecord


class RuntimeJournal(Protocol):
    def append(self, record: JournalRecord) -> JournalEntry: ...

    def records(self) -> tuple[JournalEntry, ...]: ...

    def sync(self) -> None: ...


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runtime_journal (
    journal_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    record_type TEXT NOT NULL,
    semantic_id TEXT NOT NULL,
    event_id TEXT,
    parent_id TEXT,
    previous_id TEXT,
    available_at TEXT NOT NULL,
    record_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_runtime_journal_event
    ON runtime_journal(event_id, journal_sequence);
CREATE INDEX IF NOT EXISTS ix_runtime_journal_semantic
    ON runtime_journal(record_type, semantic_id);
CREATE TRIGGER IF NOT EXISTS runtime_journal_no_update
BEFORE UPDATE ON runtime_journal BEGIN
    SELECT RAISE(ABORT, 'runtime_journal is append-only');
END;
CREATE TRIGGER IF NOT EXISTS runtime_journal_no_delete
BEFORE DELETE ON runtime_journal BEGIN
    SELECT RAISE(ABORT, 'runtime_journal is append-only');
END;
"""


class SQLiteRuntimeJournal:
    """Small additive SQLite implementation outside the pure decision kernel."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def append(self, record: JournalRecord) -> JournalEntry:
        payload = record.model_dump_json()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO runtime_journal(
                    record_id, record_type, semantic_id, event_id,
                    parent_id, previous_id, available_at, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.record_type.value,
                    record.semantic_id,
                    record.event_id,
                    record.parent_id,
                    record.previous_id,
                    record.available_at.isoformat(),
                    payload,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return a journal sequence")
            sequence = cursor.lastrowid
        return JournalEntry(sequence=sequence, record=record)

    def append_semantic(
        self,
        value: JournalSemantic,
        *,
        event_id: str | None,
        parent_id: str | None = None,
        previous_id: str | None = None,
        available_at: UTCDateTime | None = None,
    ) -> JournalEntry:
        return self.append(
            JournalRecord.from_semantic(
                value,
                event_id=event_id,
                parent_id=parent_id,
                previous_id=previous_id,
                available_at=available_at,
            )
        )

    def append_outcome(
        self,
        event: RuntimeEvent,
        outcome: JournalOutcome,
    ) -> JournalEntry:
        return self.append_semantic(
            outcome,
            event_id=event.event_id,
            parent_id=event.event_id,
            available_at=event.available_at,
        )

    def records(self) -> tuple[JournalEntry, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT journal_sequence, record_json FROM runtime_journal "
                "ORDER BY journal_sequence"
            ).fetchall()
        return tuple(
            JournalEntry(
                sequence=int(row["journal_sequence"]),
                record=JournalRecord.model_validate_json(row["record_json"]),
            )
            for row in rows
        )

    def events(self) -> Iterator[RuntimeEvent]:
        values: dict[str, RuntimeEvent] = {}
        for entry in self.records():
            if entry.record.record_type is JournalRecordType.RUNTIME_EVENT:
                event = RuntimeEvent.model_validate(entry.record.decode())
                values[event.event_id] = event
        return iter(sorted(values.values(), key=lambda event: event.ordering_key))

    def sync(self) -> None:
        """Flush committed WAL content without changing semantic journal history."""
        with self._connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")

    def feature_snapshots(self) -> dict[str, CausalFeatureSnapshot]:
        values: dict[str, CausalFeatureSnapshot] = {}
        for entry in self.records():
            record = entry.record
            if record.record_type is not JournalRecordType.FEATURE_SNAPSHOT:
                continue
            if record.event_id is None:
                raise ValueError("feature snapshot journal record has no event linkage")
            snapshot = CausalFeatureSnapshot.model_validate(record.decode())
            existing = values.get(record.event_id)
            if existing is not None and existing.snapshot_id != snapshot.snapshot_id:
                raise ValueError("event has conflicting journaled feature snapshots")
            values[record.event_id] = snapshot
        return values
