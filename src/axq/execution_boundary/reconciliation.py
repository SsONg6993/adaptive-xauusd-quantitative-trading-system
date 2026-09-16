"""Deterministic exact-linkage comparison of local and broker execution state."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Protocol

from axq.execution_boundary.contracts import ExecutionResult, ExecutionResultStatus
from axq.execution_boundary.recovery_contracts import (
    BrokerRecoverySnapshot,
    ReconciliationFinding,
    ReconciliationKind,
    ReconciliationReport,
    ResolutionStatus,
)
from axq.runtime import OrderState, PositionSide, PositionState
from axq.schemas import Signal


class ReconciliationLedger(Protocol):
    def latest_results(self) -> tuple[ExecutionResult, ...]: ...
    def append_reconciliation(self, report: ReconciliationReport) -> None: ...


def reconcile_execution_state(
    ledger: ReconciliationLedger,
    snapshot: BrokerRecoverySnapshot,
    *,
    as_of: datetime,
    prior_report: ReconciliationReport | None = None,
) -> ReconciliationReport:
    objects: dict[str, PositionState | OrderState] = {
        item.position_id: item for item in snapshot.positions.positions
    } | {item.order_id: item for item in snapshot.orders.orders}
    consumed: set[str] = set()
    findings: list[ReconciliationFinding] = []
    links_by_intent = {link.intent_id: link for link in snapshot.intent_links}

    for result in ledger.latest_results():
        if result.status in {
            ExecutionResultStatus.NO_ACTION,
            ExecutionResultStatus.REJECTED,
            ExecutionResultStatus.CANCELLED,
            ExecutionResultStatus.EXPIRED,
            ExecutionResultStatus.FAILED,
        }:
            continue
        link = links_by_intent.get(result.execution_intent_id)
        candidate = objects.get(link.broker_object_id) if link else None
        if candidate is None and result.broker_ticket is not None:
            candidate = next(
                (item for item in objects.values() if item.broker_ticket == result.broker_ticket),
                None,
            )
        if candidate is None:
            kind = (
                ReconciliationKind.UNKNOWN
                if result.status in {ExecutionResultStatus.UNKNOWN, ExecutionResultStatus.SUBMITTED}
                else ReconciliationKind.LOCAL_ONLY
            )
            findings.append(_finding(kind, result, None, "NO_EXACT_BROKER_EVIDENCE"))
            continue
        consumed.add(_object_id(candidate))
        reason = _conflict_reason(result, candidate, link.broker_ticket if link else None)
        findings.append(
            _finding(
                ReconciliationKind.CONFLICT if reason else ReconciliationKind.MATCHED,
                result,
                candidate,
                reason or "EXACT_LINK_MATCH",
            )
        )

    for object_id in sorted(set(objects) - consumed):
        item = objects[object_id]
        findings.append(
            ReconciliationFinding(
                kind=ReconciliationKind.BROKER_ONLY,
                status=ResolutionStatus.RECONCILIATION_REQUIRED,
                broker_object_id=object_id,
                broker_ticket=item.broker_ticket,
                reason_code="UNCLASSIFIED_BROKER_OBJECT",
            )
        )
    findings.sort(
        key=lambda item: (item.intent_id or "", item.broker_object_id or "", item.kind.value)
    )
    status = (
        ResolutionStatus.RESOLVED
        if all(item.status is ResolutionStatus.RESOLVED for item in findings)
        else ResolutionStatus.RECONCILIATION_REQUIRED
    )
    report = ReconciliationReport(
        snapshot_id=snapshot.snapshot_id,
        as_of=as_of,
        available_at=snapshot.available_at,
        status=status,
        findings=tuple(findings),
        supersedes_report_id=prior_report.report_id if prior_report else None,
    )
    ledger.append_reconciliation(report)
    return report


def _object_id(item: PositionState | OrderState) -> str:
    return item.position_id if isinstance(item, PositionState) else item.order_id


def _finding(
    kind: ReconciliationKind,
    result: ExecutionResult,
    item: PositionState | OrderState | None,
    reason: str,
) -> ReconciliationFinding:
    return ReconciliationFinding(
        kind=kind,
        status=(
            ResolutionStatus.RESOLVED
            if kind is ReconciliationKind.MATCHED
            else ResolutionStatus.RECONCILIATION_REQUIRED
        ),
        intent_id=result.execution_intent_id,
        broker_object_id=_object_id(item) if item else None,
        broker_ticket=item.broker_ticket if item else result.broker_ticket,
        reason_code=reason,
    )


def _conflict_reason(
    result: ExecutionResult,
    item: PositionState | OrderState,
    linked_ticket: int | None,
) -> str | None:
    if result.broker_ticket is not None and item.broker_ticket != result.broker_ticket:
        return "TICKET_MISMATCH"
    if linked_ticket is not None and item.broker_ticket != linked_ticket:
        return "TICKET_MISMATCH"
    if isinstance(item, PositionState):
        direction = Signal.BUY if item.side is PositionSide.BUY else Signal.SELL
    else:
        direction = Signal.BUY if item.order_type.value.startswith("BUY") else Signal.SELL
    if direction is not result.direction:
        return "DIRECTION_MISMATCH"
    expected = result.filled_volume_lots or result.requested_volume_lots
    if not math.isclose(item.volume_lots, expected, abs_tol=1e-8):
        return "VOLUME_MISMATCH"
    return None
