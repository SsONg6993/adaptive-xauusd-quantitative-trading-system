"""Append-only SQLite ledger for position-action transport outcomes."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from axq.database import Database
from axq.execution_boundary import ExecutionResultStatus
from axq.position_actions.contracts import PositionActionIntent
from axq.position_actions.transport import (
    PositionActionTransportResult,
    PositionActionTransportTransition,
    PositionActionTransportTransitionType,
)

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


class SQLitePositionActionTransportLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        Database(self.path).migrate(_MIGRATIONS)

    def transitions(self) -> tuple[PositionActionTransportTransition, ...]:
        with Database(self.path).connect() as connection:
            rows = connection.execute(
                "SELECT transition_json FROM position_action_transport_transitions "
                "ORDER BY transition_sequence"
            ).fetchall()
        return tuple(
            PositionActionTransportTransition.model_validate_json(row[0]) for row in rows
        )

    def get(self, intent_id: str) -> PositionActionTransportResult | None:
        results = [
            item.result
            for item in self.transitions()
            if item.intent_id == intent_id and item.result is not None
        ]
        return results[-1] if results else None

    def reserve(self, intent: PositionActionIntent) -> bool:
        transition = PositionActionTransportTransition(
            transition_type=PositionActionTransportTransitionType.RESERVED,
            intent_id=intent.intent_id,
            intent=intent,
            available_at=intent.available_at,
        )
        try:
            self._append(transition)
        except sqlite3.IntegrityError:
            return False
        return True

    def record(self, result: PositionActionTransportResult) -> None:
        if not any(
            item.transition_type is PositionActionTransportTransitionType.RESERVED
            and item.intent_id == result.position_action_intent_id
            for item in self.transitions()
        ):
            raise ValueError("position-action intent must be reserved before recording")
        prior = self.get(result.position_action_intent_id)
        if prior is not None:
            if prior == result:
                return
            raise ValueError("position-action intent already has a different result")
        self._append(
            PositionActionTransportTransition(
                transition_type=PositionActionTransportTransitionType.RESULT_RECORDED,
                intent_id=result.position_action_intent_id,
                result=result,
                available_at=result.available_at,
            )
        )

    def sync(self) -> None:
        with Database(self.path).connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")

    def requires_reconciliation(self, intent_id: str) -> bool:
        reserved = any(
            item.transition_type is PositionActionTransportTransitionType.RESERVED
            and item.intent_id == intent_id
            for item in self.transitions()
        )
        result = self.get(intent_id)
        return reserved and (
            result is None or result.status is ExecutionResultStatus.UNKNOWN
        )

    def _append(self, transition: PositionActionTransportTransition) -> None:
        with Database(self.path).connect() as connection:
            connection.execute(
                "INSERT INTO position_action_transport_transitions("
                "transition_id, transition_type, intent_id, available_at, transition_json"
                ") VALUES (?, ?, ?, ?, ?)",
                (
                    transition.transition_id,
                    transition.transition_type.value,
                    transition.intent_id,
                    transition.available_at.isoformat(),
                    transition.model_dump_json(),
                ),
            )
