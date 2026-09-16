"""Deterministic runtime refresh and checkpoint builders for restart recovery."""

from __future__ import annotations

from typing import Protocol

from axq.execution_boundary.recovery_contracts import (
    BrokerRecoverySnapshot,
    ReconciliationReport,
    RecoveryCheckpoint,
    ResumeReadiness,
)
from axq.runtime import RuntimeEvent, RuntimeEventType, SharedRuntimeState
from axq.runtime.events import EventPayload


class SyncJournal(Protocol):
    def sync(self) -> None: ...


class CheckpointLedger(SyncJournal, Protocol):
    def append_checkpoint(self, checkpoint: RecoveryCheckpoint) -> None: ...


def broker_snapshot_runtime_events(
    snapshot: BrokerRecoverySnapshot,
    *,
    source_sequence_start: int,
) -> tuple[RuntimeEvent, ...]:
    payloads: tuple[tuple[RuntimeEventType, EventPayload], ...] = (
        (RuntimeEventType.TICK, snapshot.market),
        (RuntimeEventType.ACCOUNT_UPDATED, snapshot.account),
        (RuntimeEventType.POSITIONS_UPDATED, snapshot.positions),
        (RuntimeEventType.ORDERS_UPDATED, snapshot.orders),
        (RuntimeEventType.EXPOSURE_UPDATED, snapshot.exposure),
        (RuntimeEventType.BROKER_CONSTRAINTS_UPDATED, snapshot.broker_constraints),
    )
    return tuple(
        RuntimeEvent(
            event_type=event_type,
            event_time=snapshot.as_of,
            observed_at=snapshot.observed_at,
            available_at=snapshot.available_at,
            source=snapshot.source,
            source_version=snapshot.source_version,
            source_sequence=source_sequence_start + offset,
            symbol=snapshot.market.symbol,
            payload=payload,
        )
        for offset, (event_type, payload) in enumerate(payloads)
    )


def create_recovery_checkpoint(
    *,
    runtime_state: SharedRuntimeState,
    reconciliation: ReconciliationReport | None,
    readiness: ResumeReadiness | None,
    thesis_state_ids: tuple[str, ...],
    available_at: object,
) -> RecoveryCheckpoint:
    return RecoveryCheckpoint.model_validate(
        {
            "runtime_state_id": runtime_state.state_id,
            "source_cursors": runtime_state.source_cursors,
            "reconciliation_report_id": reconciliation.report_id if reconciliation else None,
            "readiness_id": readiness.readiness_id if readiness else None,
            "thesis_state_ids": tuple(sorted(thesis_state_ids)),
            "available_at": available_at,
        }
    )


def persist_graceful_shutdown(
    checkpoint: RecoveryCheckpoint,
    *,
    execution_ledger: CheckpointLedger,
    runtime_journal: SyncJournal,
) -> None:
    """Persist the recovery anchor, then flush both durable append-only stores."""
    execution_ledger.append_checkpoint(checkpoint)
    runtime_journal.sync()
    execution_ledger.sync()
