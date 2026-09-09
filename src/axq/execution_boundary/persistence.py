"""Append-only SQLite execution ledger and recovery anchors."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from axq.database import Database
from axq.execution_boundary.contracts import ExecutionIntent, ExecutionResult, ExecutionResultStatus
from axq.execution_boundary.recovery_contracts import (
    ExecutionTransition,
    ExecutionTransitionType,
    ReconciliationReport,
    RecoveryCheckpoint,
    ResolutionStatus,
)

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


class SQLiteExecutionLedger:
    """Durable projection reconstructed only from immutable transitions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        Database(self.path).migrate(_MIGRATIONS)

    def _connect(self) -> sqlite3.Connection:
        return Database(self.path).connect()

    def transitions(self) -> tuple[ExecutionTransition, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT transition_json FROM execution_transitions ORDER BY transition_sequence"
            ).fetchall()
        return tuple(ExecutionTransition.model_validate_json(row[0]) for row in rows)

    def is_reserved(self, intent_id: str) -> bool:
        return any(
            item.transition_type is ExecutionTransitionType.RESERVED and item.intent_id == intent_id
            for item in self.transitions()
        )

    def reserve(self, intent: ExecutionIntent) -> bool:
        transition = ExecutionTransition(
            transition_type=ExecutionTransitionType.RESERVED,
            intent_id=intent.intent_id,
            intent=intent,
            available_at=intent.available_at,
        )
        try:
            self._append_transition(transition)
        except sqlite3.IntegrityError:
            return False
        return True

    def record(self, result: ExecutionResult) -> None:
        if not self.is_reserved(result.execution_intent_id):
            raise ValueError("execution intent must be reserved before recording")
        prior = self.get(result.execution_intent_id)
        if prior is not None:
            if prior == result:
                return
            raise ValueError("execution intent already has a different result")
        self._append_transition(
            ExecutionTransition(
                transition_type=ExecutionTransitionType.RESULT_RECORDED,
                intent_id=result.execution_intent_id,
                result=result,
                available_at=result.available_at,
            )
        )

    def get(self, intent_id: str) -> ExecutionResult | None:
        values = [
            item.result
            for item in self.transitions()
            if item.intent_id == intent_id and item.result is not None
        ]
        return values[-1] if values else None

    def intents(self) -> tuple[ExecutionIntent, ...]:
        return tuple(item.intent for item in self.transitions() if item.intent is not None)

    def latest_results(self) -> tuple[ExecutionResult, ...]:
        by_intent: dict[str, ExecutionResult] = {}
        for transition in self.transitions():
            if transition.result is not None:
                by_intent[transition.result.execution_intent_id] = transition.result
        return tuple(by_intent[key] for key in sorted(by_intent))

    def append_reconciliation(self, report: ReconciliationReport) -> None:
        previous = self.latest_reconciliation()
        if previous is None and report.supersedes_report_id is not None:
            raise ValueError("first reconciliation cannot supersede an absent report")
        if previous is not None and report.supersedes_report_id != previous.report_id:
            raise ValueError("new reconciliation must supersede the latest report")
        self._append_transition(
            ExecutionTransition(
                transition_type=ExecutionTransitionType.RECONCILIATION_RECORDED,
                reconciliation=report,
                available_at=report.available_at,
            )
        )

    def reconciliations(self) -> tuple[ReconciliationReport, ...]:
        return tuple(
            item.reconciliation for item in self.transitions() if item.reconciliation is not None
        )

    def latest_reconciliation(self) -> ReconciliationReport | None:
        values = self.reconciliations()
        return values[-1] if values else None

    def requires_reconciliation(self, intent_id: str) -> bool:
        result = self.get(intent_id)
        if result is None:
            return self.is_reserved(intent_id)
        if result.status is not ExecutionResultStatus.UNKNOWN:
            return False
        latest = self.latest_reconciliation()
        if latest is None or latest.status is ResolutionStatus.RECONCILIATION_REQUIRED:
            return True
        return not any(item.intent_id == intent_id for item in latest.findings)

    def append_checkpoint(self, checkpoint: RecoveryCheckpoint) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO recovery_checkpoints("
                "checkpoint_id, available_at, checkpoint_json) VALUES (?, ?, ?)",
                (
                    checkpoint.checkpoint_id,
                    checkpoint.available_at.isoformat(),
                    checkpoint.model_dump_json(),
                ),
            )

    def latest_checkpoint(self) -> RecoveryCheckpoint | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT checkpoint_json FROM recovery_checkpoints "
                "ORDER BY checkpoint_sequence DESC LIMIT 1"
            ).fetchone()
        return RecoveryCheckpoint.model_validate_json(row[0]) if row else None

    def sync(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")

    def _append_transition(self, transition: ExecutionTransition) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO execution_transitions(transition_id, transition_type, intent_id, "
                "available_at, transition_json) VALUES (?, ?, ?, ?, ?)",
                (
                    transition.transition_id,
                    transition.transition_type.value,
                    transition.intent_id,
                    transition.available_at.isoformat(),
                    transition.model_dump_json(),
                ),
            )
