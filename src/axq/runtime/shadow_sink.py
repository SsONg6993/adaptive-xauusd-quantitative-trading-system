"""Append-only, non-mutating shadow execution projection."""

from __future__ import annotations

from typing import Literal, cast

from axq.execution_boundary import ExecutionIntent
from axq.runtime.journal import JournalRecord, RuntimeJournal
from axq.runtime.shadow import (
    HypotheticalPlanField,
    HypotheticalTradePlan,
    M5CandidateScan,
    PlanFieldStatus,
    ShadowExecutionRecord,
)


def _available(value: float, reason: str, *provenance: str) -> HypotheticalPlanField:
    return HypotheticalPlanField(
        status=PlanFieldStatus.AVAILABLE,
        value=value,
        reason=reason,
        provenance_ids=tuple(provenance),
    )


def _unavailable(reason: str) -> HypotheticalPlanField:
    return HypotheticalPlanField(status=PlanFieldStatus.UNAVAILABLE, reason=reason)


def build_hypothetical_trade_plan(
    *,
    scan: M5CandidateScan,
    intent: ExecutionIntent,
    master_confidence: float,
) -> HypotheticalTradePlan:
    """Project exact existing decision facts without inventing target values."""

    return HypotheticalTradePlan(
        event_id=scan.event_id,
        scan_id=scan.scan_id,
        execution_intent_id=intent.intent_id,
        master_proposal_id=intent.master_proposal_id,
        discipline_outcome_id=intent.discipline_outcome_id,
        risk_outcome_id=intent.risk_outcome_id,
        symbol=intent.symbol,
        canonical_instrument=scan.canonical_instrument,
        resolved_broker_symbol=scan.resolved_broker_symbol,
        instrument_resolution_id=scan.instrument_resolution_id,
        direction=cast(Literal["BUY", "SELL"], intent.direction.value),
        as_of=intent.as_of,
        confidence=_available(
            master_confidence,
            "Recorded Master proposal confidence.",
            intent.master_proposal_id,
        ),
        entry=_available(
            intent.requested_entry_price,
            "Recorded execution-intent entry price.",
            intent.intent_id,
        ),
        stop_loss=_available(
            intent.stop_loss_price,
            "Recorded deterministic Risk stop.",
            intent.risk_outcome_id,
            intent.intent_id,
        ),
        take_profit=_unavailable(
            "The current execution contract has no deterministic take-profit policy."
        ),
        position_size=_available(
            intent.approved_volume_lots,
            "Recorded deterministic Risk-approved volume.",
            intent.risk_outcome_id,
            intent.intent_id,
        ),
        risk_reward=_unavailable("Risk/reward is unavailable because no take-profit value exists."),
    )


class JournalShadowExecutionSink:
    """Record what would be submitted; this class has no broker dependency."""

    def __init__(self, journal: RuntimeJournal) -> None:
        self._journal = journal

    def record(self, plan: HypotheticalTradePlan) -> ShadowExecutionRecord:
        record = ShadowExecutionRecord(
            event_id=plan.event_id,
            scan_id=plan.scan_id,
            plan_id=plan.plan_id,
            execution_intent_id=plan.execution_intent_id,
            symbol=plan.symbol,
            canonical_instrument=plan.canonical_instrument,
            resolved_broker_symbol=plan.resolved_broker_symbol,
            instrument_resolution_id=plan.instrument_resolution_id,
            direction=plan.direction,
            as_of=plan.as_of,
        )
        existing = {entry.record.record_id for entry in self._journal.records()}
        plan_record = JournalRecord.from_semantic(plan, event_id=plan.event_id)
        if plan_record.record_id not in existing:
            self._journal.append(plan_record)
            existing.add(plan_record.record_id)
        execution_record = JournalRecord.from_semantic(record, event_id=plan.event_id)
        if execution_record.record_id not in existing:
            self._journal.append(execution_record)
        return record


__all__ = ["JournalShadowExecutionSink", "build_hypothetical_trade_plan"]
