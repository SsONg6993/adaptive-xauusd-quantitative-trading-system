"""Read-only live-shadow funnel around the existing Phase 6/7 semantic kernel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from axq.orchestration.contracts import DecisionCycle, DecisionPlan
from axq.runtime import RuntimeEvent
from axq.runtime.journal import JournalRecord, JournalSemantic, RuntimeJournal
from axq.runtime.scanner import scan_m5_candidate
from axq.runtime.shadow import (
    CandidateResult,
    M5CandidateScan,
    M15ContextSnapshot,
    ShadowCycleStage,
    ShadowRuntimeCycle,
)
from axq.runtime.shadow_sink import (
    JournalShadowExecutionSink,
    build_hypothetical_trade_plan,
)
from axq.tools import CausalFeatureSnapshot


class ShadowRunner(Protocol):
    pass


class ShadowOrchestrator(Protocol):
    @property
    def latest_plan(self) -> DecisionPlan: ...

    def process_event(
        self,
        event: RuntimeEvent,
        *,
        feature_snapshot: CausalFeatureSnapshot,
    ) -> DecisionCycle: ...


@dataclass(frozen=True)
class ShadowProcessOutcome:
    context: M15ContextSnapshot | None
    scan: M5CandidateScan
    shadow_cycle: ShadowRuntimeCycle
    decision_cycle: DecisionCycle | None


class LiveShadowRuntime:
    """Observe the scanner while every completed M5 follows the shared decision kernel."""

    def __init__(
        self,
        *,
        orchestrator: ShadowOrchestrator,
        runner: ShadowRunner,
        journal: RuntimeJournal,
        symbol: str,
        feature_manifest_id: str,
        resolved_broker_symbol: str,
        instrument_resolution_id: str,
        execution_sink: JournalShadowExecutionSink | None = None,
    ) -> None:
        self._orchestrator = orchestrator
        self._runner = runner
        self._journal = journal
        self._symbol = symbol
        self._feature_manifest_id = feature_manifest_id
        self._resolved_broker_symbol = resolved_broker_symbol
        self._instrument_resolution_id = instrument_resolution_id
        self._execution_sink = execution_sink

    def _append(self, value: object, event_id: str) -> None:
        self._journal.append(
            JournalRecord.from_semantic(
                cast(JournalSemantic, value),
                event_id=event_id,
            )
        )

    def process(
        self,
        event: RuntimeEvent,
        feature_snapshot: CausalFeatureSnapshot,
    ) -> ShadowProcessOutcome:
        context, scan = scan_m5_candidate(
            event,
            feature_snapshot,
            configured_symbol=self._symbol,
            resolved_broker_symbol=self._resolved_broker_symbol,
            instrument_resolution_id=self._instrument_resolution_id,
            expected_manifest_id=self._feature_manifest_id,
        )
        if context is not None:
            self._append(context, event.event_id)
        self._append(scan, event.event_id)
        decision_cycle = self._orchestrator.process_event(
            event,
            feature_snapshot=feature_snapshot,
        )
        if scan.result not in {
            CandidateResult.CANDIDATE,
            CandidateResult.CANDIDATE_CONFLICTED,
        }:
            shadow_cycle = ShadowRuntimeCycle.from_scan(scan)
            self._append(shadow_cycle, event.event_id)
            return ShadowProcessOutcome(context, scan, shadow_cycle, decision_cycle)

        plan = self._orchestrator.latest_plan
        trade_plan = None
        shadow_execution = None
        if plan.execution_intent is not None and self._execution_sink is not None:
            if plan.master is None:
                raise RuntimeError("execution intent requires its Master proposal")
            trade_plan = build_hypothetical_trade_plan(
                scan=scan,
                intent=plan.execution_intent,
                master_confidence=plan.master.confidence,
            )
            shadow_execution = self._execution_sink.record(trade_plan)
        if trade_plan is not None and shadow_execution is not None:
            stage = ShadowCycleStage.TRADE_PLAN
        elif plan.master is not None and plan.master.decision.value == "HOLD":
            stage = ShadowCycleStage.HOLD
        else:
            stage = ShadowCycleStage.SETUP_DETECTED
        shadow_cycle = ShadowRuntimeCycle(
            event_id=event.event_id,
            scan_id=scan.scan_id,
            m15_context_id=scan.m15_context_id,
            canonical_instrument=scan.canonical_instrument,
            resolved_broker_symbol=scan.resolved_broker_symbol,
            instrument_resolution_id=scan.instrument_resolution_id,
            stage=stage,
            as_of=event.event_time,
            evidence_bundle_id=(None if plan.master is None else plan.master.bundle_id),
            master_proposal_id=plan.master.proposal_id if plan.master else None,
            discipline_outcome_id=plan.discipline.outcome_id if plan.discipline else None,
            risk_outcome_id=plan.risk.outcome_id if plan.risk else None,
            execution_intent_id=(
                plan.execution_intent.intent_id if plan.execution_intent else None
            ),
            trade_plan_id=trade_plan.plan_id if trade_plan else None,
            shadow_execution_id=(shadow_execution.record_id if shadow_execution else None),
            interaction_resolution_id=plan.interaction_resolution_id,
        )
        self._append(shadow_cycle, event.event_id)
        return ShadowProcessOutcome(context, scan, shadow_cycle, decision_cycle)

    def record_availability(self, availability: object) -> None:
        from axq.runtime.shadow import ShadowMarketAvailability

        value = cast(ShadowMarketAvailability, availability)
        if (
            value.resolved_broker_symbol != self._resolved_broker_symbol
            or value.instrument_resolution_id != self._instrument_resolution_id
        ):
            raise ValueError("market availability does not match resolved instrument")
        self._append(value, event_id=value.availability_id)


__all__ = ["LiveShadowRuntime", "ShadowProcessOutcome"]
