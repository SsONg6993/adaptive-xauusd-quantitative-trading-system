"""Deterministic composition service for the completed Phase 6/7 boundaries."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol, cast

from axq.agents import AgentMemory, ContinuityStatus, ThesisState
from axq.execution_boundary import (
    BrokerRecoverySnapshot,
    ExecutionAdapter,
    ExecutionResult,
    ReconciliationReport,
    ResumeReadiness,
    ResumeStatus,
    broker_snapshot_runtime_events,
    create_recovery_checkpoint,
    evaluate_resume_readiness,
    execution_result_to_runtime_event,
    reconcile_execution_state,
)
from axq.execution_boundary.persistence import SQLiteExecutionLedger
from axq.mt5 import MT5Gateway
from axq.orchestration.config import RuntimeConfig
from axq.orchestration.contracts import (
    DecisionCycle,
    DecisionPlan,
    OperatorControls,
    RuntimeMode,
    RuntimeRunSummary,
    RuntimeStatus,
    StartupPhase,
)
from axq.position_actions import PositionActionIntent
from axq.position_actions.persistence import SQLitePositionActionTransportLedger
from axq.position_actions.transport import (
    PositionActionTransportResult,
    position_action_result_to_runtime_event,
)
from axq.runtime import EventSource, RuntimeEvent, SharedRuntimeState
from axq.runtime.journal import (
    JournalRecord,
    JournalRecordType,
    JournalSemantic,
    RuntimeJournal,
)
from axq.runtime.replay import SemanticTraceStep
from axq.tools import CausalFeatureSnapshot


class BrokerSnapshotProvider(Protocol):
    def capture(self) -> BrokerRecoverySnapshot: ...


class PositionActionAdapter(Protocol):
    def execute(self, intent: PositionActionIntent) -> PositionActionTransportResult: ...


class DecisionCycleProcessor(Protocol):
    def evaluate(
        self,
        event: RuntimeEvent,
        state: SharedRuntimeState,
        trace: SemanticTraceStep,
        readiness: ResumeReadiness | None,
        controls: OperatorControls,
    ) -> DecisionPlan: ...


class RuntimeRunner(Protocol):
    @property
    def state(self) -> SharedRuntimeState: ...

    @property
    def thesis(self) -> ThesisState | None: ...

    def process(
        self,
        event: RuntimeEvent,
        feature_snapshot: CausalFeatureSnapshot | None,
    ) -> SemanticTraceStep: ...

    def restore_runtime(
        self,
        state: SharedRuntimeState,
        memories: tuple[AgentMemory, ...] = (),
    ) -> None: ...

    def restore_thesis(self, thesis: ThesisState) -> None: ...


class RuntimeOrchestrator:
    """Own ordering and gates while delegating every trading semantic decision."""

    def __init__(
        self,
        *,
        config: RuntimeConfig,
        runner: RuntimeRunner,
        processor: DecisionCycleProcessor,
        journal: RuntimeJournal,
        execution_ledger: SQLiteExecutionLedger,
        position_action_ledger: SQLitePositionActionTransportLedger,
        clock: Callable[[], datetime],
        gateway: MT5Gateway | None = None,
        snapshot_provider: BrokerSnapshotProvider | None = None,
        entry_adapter: ExecutionAdapter | None = None,
        position_action_adapter: PositionActionAdapter | None = None,
        feature_provider: (
            Callable[[RuntimeEvent, SharedRuntimeState], CausalFeatureSnapshot | None] | None
        ) = None,
        continuity_status: ContinuityStatus = ContinuityStatus.COMPLETE,
        startup_backfill: Callable[[], ContinuityStatus] | None = None,
    ) -> None:
        self.config = config
        self.runner = runner
        self.processor = processor
        self.journal = journal
        self.execution_ledger = execution_ledger
        self.position_action_ledger = position_action_ledger
        self._clock = clock
        self._gateway = gateway
        self._snapshot_provider = snapshot_provider
        self._entry_adapter = entry_adapter
        self._position_action_adapter = position_action_adapter
        self._feature_provider = feature_provider
        self._continuity_status = continuity_status
        self._startup_backfill = startup_backfill
        self._controls = OperatorControls()
        self._phase = StartupPhase.CREATED
        self._readiness: ResumeReadiness | None = None
        self._reconciliation: ReconciliationReport | None = None
        self._cycles: list[DecisionCycle] = []
        self._source_sequence = 1_000_000
        self._last_event_id: str | None = None
        self._last_error: str | None = None
        self._last_snapshot_at: datetime | None = None
        self._latest_plan = DecisionPlan()
        self._latest_execution_result_id: str | None = None

    @property
    def status(self) -> RuntimeStatus:
        thesis = self.runner.thesis
        freshness = self.runner.state.component_freshness
        safe = (
            self._phase is StartupPhase.SAFE
            and self.config.mode is RuntimeMode.DEMO
            and self._readiness is not None
            and self._readiness.status is ResumeStatus.SAFE
            and not self._controls.pause_new_entries
            and not self._mutation_blocked()
        )
        return RuntimeStatus(
            mode=self.config.mode,
            startup_phase=self._phase,
            as_of=self.runner.state.as_of,
            accepting_events=self._phase is StartupPhase.SAFE,
            safe_to_process_new_trades=safe,
            resume_status=self._readiness.status.value if self._readiness else None,
            current_event_id=self._last_event_id,
            current_thesis_state_id=thesis.state_id if thesis else None,
            current_scenario_state_ids=(
                tuple(item.state_id for item in thesis.scenarios) if thesis else ()
            ),
            latest_master_proposal_id=(
                self._latest_plan.master.proposal_id if self._latest_plan.master else None
            ),
            latest_discipline_outcome_id=(
                self._latest_plan.discipline.outcome_id
                if self._latest_plan.discipline
                else None
            ),
            latest_risk_outcome_id=(
                self._latest_plan.risk.outcome_id if self._latest_plan.risk else None
            ),
            latest_execution_result_id=self._latest_execution_result_id,
            open_position_count=len(self.runner.state.positions.positions),
            component_freshness=tuple(sorted(freshness, key=lambda item: item.component)),
            last_error=self._last_error,
        )

    def set_operator_controls(self, controls: OperatorControls) -> None:
        if self._controls.kill_switch and not controls.kill_switch:
            raise ValueError("kill switch cannot be cleared by replacing controls")
        self._controls = controls

    def resume_new_entries(self) -> None:
        """Lift an entry pause only while all non-bypassable gates remain safe."""
        if (
            self._phase is not StartupPhase.SAFE
            or self._readiness is None
            or self._readiness.status is not ResumeStatus.SAFE
            or self._controls.execution_disabled
            or self._controls.kill_switch
        ):
            raise RuntimeError("entries cannot resume while runtime safety is unresolved")
        self._controls = self._controls.model_copy(update={"pause_new_entries": False})

    def startup(self) -> RuntimeStatus:
        if self._phase is not StartupPhase.CREATED:
            return self.status
        self._phase = StartupPhase.OPENING_STORES
        try:
            self._phase = StartupPhase.RESTORING
            self._restore_thesis()
            if self._startup_backfill is not None:
                self._continuity_status = self._startup_backfill()
            if self.config.mode in {RuntimeMode.DISABLED, RuntimeMode.REPLAY}:
                self._phase = StartupPhase.SAFE
                return self.status
            if self._gateway is None or self._snapshot_provider is None:
                raise RuntimeError("broker gateway and snapshot provider are required")
            self._phase = StartupPhase.CONNECTING
            self._gateway.connect()
            self._phase = StartupPhase.SNAPSHOTTING
            self._refresh_broker()
            if self._phase is not StartupPhase.BLOCKED:
                self._phase = StartupPhase.SAFE
        except Exception as error:
            self._last_error = str(error) or type(error).__name__
            self._phase = StartupPhase.BLOCKED
        return self.status

    def _restore_thesis(self) -> None:
        latest: ThesisState | None = None
        latest_state: SharedRuntimeState | None = None
        memories: dict[str, AgentMemory] = {}
        for entry in self.journal.records():
            if entry.record.record_type is JournalRecordType.THESIS_STATE:
                latest = ThesisState.model_validate(entry.record.decode())
            elif entry.record.record_type is JournalRecordType.RUNTIME_STATE:
                latest_state = SharedRuntimeState.model_validate(entry.record.decode())
            elif entry.record.record_type is JournalRecordType.AGENT_MEMORY:
                memory = AgentMemory.model_validate(entry.record.decode())
                memories[memory.agent_name] = memory
        if latest_state is not None:
            self.runner.restore_runtime(
                latest_state,
                tuple(memories[name] for name in sorted(memories)),
            )
            if latest_state.source_cursors:
                self._source_sequence = max(
                    item.source_sequence for item in latest_state.source_cursors
                ) + 1
        if latest is not None:
            self.runner.restore_thesis(latest)

    def _refresh_broker(self) -> None:
        if self._snapshot_provider is None:
            raise RuntimeError("broker snapshot provider is unavailable")
        snapshot = self._snapshot_provider.capture()
        self._last_snapshot_at = snapshot.available_at
        for event in broker_snapshot_runtime_events(
            snapshot, source_sequence_start=self._source_sequence
        ):
            self._source_sequence += 1
            self.runner.process(event, None)
            self._last_event_id = event.event_id
        self._phase = StartupPhase.RECONCILING
        self._reconciliation = reconcile_execution_state(
            self.execution_ledger,
            snapshot,
            as_of=snapshot.available_at,
            prior_report=self._reconciliation or self.execution_ledger.latest_reconciliation(),
        )
        self._append_semantic(self._reconciliation, event_id=None)
        self._phase = StartupPhase.VALIDATING
        theses = (self.runner.thesis,) if self.runner.thesis is not None else ()
        self._readiness = evaluate_resume_readiness(
            self.runner.state,
            self._reconciliation,
            theses,
            as_of=snapshot.available_at,
            continuity_status=self._continuity_status,
        )
        self._append_semantic(self._readiness, event_id=None)
        if self._position_action_anomaly() or self._readiness.status is not ResumeStatus.SAFE:
            self._block("startup recovery/readiness is unsafe")

    def _position_action_anomaly(self) -> bool:
        intent_ids = {item.intent_id for item in self.position_action_ledger.transitions()}
        return any(
            self.position_action_ledger.requires_reconciliation(intent_id)
            for intent_id in intent_ids
        )

    def process_event(self, event: RuntimeEvent) -> DecisionCycle:
        if self._phase is not StartupPhase.SAFE:
            raise RuntimeError("startup recovery must be SAFE before event decisions")
        feature = (
            self._feature_provider(event, self.runner.state)
            if self._feature_provider is not None
            else None
        )
        trace = self.runner.process(event, feature)
        self._last_event_id = event.event_id
        try:
            plan = self.processor.evaluate(
                event, self.runner.state, trace, self._readiness, self._controls
            )
        except Exception as error:
            self._last_error = str(error) or type(error).__name__
            plan = DecisionPlan()
        self._latest_plan = plan
        self._journal_plan(event, plan)
        execution_results: list[ExecutionResult] = []
        action_results: list[PositionActionTransportResult] = []
        if plan.execution_intent is not None and self._can_mutate_entry():
            if self._entry_adapter is None:
                self._block("entry adapter is unavailable")
            elif self._revalidate_before_mutation():
                try:
                    result = self._entry_adapter.execute(plan.execution_intent)
                except Exception as error:
                    self._block(str(error) or type(error).__name__)
                else:
                    execution_results.append(result)
                    self._latest_execution_result_id = result.result_id
                    self._append_semantic(result, event_id=event.event_id)
                    self._apply_execution_feedback(result)
                    self._refresh_after_transport()
        if plan.position_action_intents and self._can_mutate_position():
            if self._position_action_adapter is None:
                self._block("position-action adapter is unavailable")
            else:
                for intent in plan.position_action_intents:
                    if not self._revalidate_before_mutation():
                        break
                    try:
                        action_result = self._position_action_adapter.execute(intent)
                    except Exception as error:
                        self._block(str(error) or type(error).__name__)
                        break
                    action_results.append(action_result)
                    self._append_semantic(action_result, event_id=event.event_id)
                    self._apply_position_feedback(action_result)
                    self._refresh_after_transport()
        cycle = DecisionCycle(
            event_id=event.event_id,
            event_type=event.event_type,
            available_at=event.available_at,
            master_result=plan.master.decision.value if plan.master else None,
            discipline_result=plan.discipline.result.value if plan.discipline else None,
            risk_result=plan.risk.result.value if plan.risk else None,
            execution_intent_ids=(
                (plan.execution_intent.intent_id,) if plan.execution_intent else ()
            ),
            execution_result_ids=tuple(item.result_id for item in execution_results),
            position_management_actions=tuple(
                item.result.value for item in plan.position_management
            ),
            position_action_intent_ids=tuple(
                item.intent_id for item in plan.position_action_intents
            ),
            position_action_result_ids=tuple(item.result_id for item in action_results),
        )
        self._cycles.append(cycle)
        return cycle

    def run_source(self, source: EventSource) -> RuntimeRunSummary:
        for event in source.events():
            if self._controls.shutdown_requested:
                break
            self.refresh_snapshot_if_due()
            self.process_event(event)
        return RuntimeRunSummary.from_cycles(tuple(self._cycles))

    def refresh_snapshot_if_due(self) -> bool:
        """Perform at most one read-only refresh when the bounded cadence elapsed."""
        if self.config.mode not in {RuntimeMode.SHADOW, RuntimeMode.DEMO}:
            return False
        now = self._clock()
        if self._last_snapshot_at is not None:
            elapsed_ms = (now - self._last_snapshot_at).total_seconds() * 1_000
            if elapsed_ms < self.config.snapshot_interval_ms:
                return False
        try:
            self._refresh_broker()
        except Exception as error:
            self._block(str(error) or type(error).__name__)
            return False
        if self._phase is not StartupPhase.BLOCKED:
            self._phase = StartupPhase.SAFE
        return True

    def _journal_plan(self, event: RuntimeEvent, plan: DecisionPlan) -> None:
        values = (
            plan.master,
            plan.discipline,
            plan.risk,
            plan.execution_intent,
            *plan.position_management,
            *plan.position_action_safety,
            *plan.position_action_intents,
        )
        for value in values:
            if value is not None:
                self._append_semantic(cast(JournalSemantic, value), event_id=event.event_id)

    def _append_semantic(self, value: JournalSemantic, *, event_id: str | None) -> None:
        self.journal.append(JournalRecord.from_semantic(value, event_id=event_id))

    def _can_mutate_entry(self) -> bool:
        return (
            self.config.mode is RuntimeMode.DEMO
            and not self._controls.pause_new_entries
            and not self._mutation_blocked()
        )

    def _can_mutate_position(self) -> bool:
        return self.config.mode is RuntimeMode.DEMO and not self._mutation_blocked()

    def _mutation_blocked(self) -> bool:
        return (
            self._controls.execution_disabled
            or self._controls.kill_switch
            or self._controls.shutdown_requested
        )

    def _revalidate_before_mutation(self) -> bool:
        try:
            self._refresh_broker()
        except Exception as error:
            self._block(str(error) or type(error).__name__)
            return False
        if self._phase is StartupPhase.BLOCKED:
            return False
        self._phase = StartupPhase.SAFE
        return self._readiness is not None and self._readiness.status is ResumeStatus.SAFE

    def _refresh_after_transport(self) -> None:
        if self._snapshot_provider is not None:
            try:
                self._refresh_broker()
            except Exception as error:
                self._block(str(error) or type(error).__name__)
                return
            if self._phase is not StartupPhase.BLOCKED:
                self._phase = StartupPhase.SAFE

    def _apply_execution_feedback(self, result: ExecutionResult) -> None:
        event = execution_result_to_runtime_event(
            result,
            source="execution-transport",
            source_version="1.0",
            source_sequence=self._source_sequence,
        )
        self._source_sequence += 1
        if event is not None:
            self.runner.process(event, None)
            self._last_event_id = event.event_id

    def _apply_position_feedback(self, result: PositionActionTransportResult) -> None:
        event = position_action_result_to_runtime_event(
            result,
            source="position-action-transport",
            source_version="1.0",
            source_sequence=self._source_sequence,
        )
        self._source_sequence += 1
        if event is not None:
            self.runner.process(event, None)
            self._last_event_id = event.event_id

    def _block(self, reason: str) -> None:
        self._last_error = reason
        self._phase = StartupPhase.BLOCKED

    def shutdown(self) -> RuntimeStatus:
        self._phase = StartupPhase.STOPPING
        checkpoint = create_recovery_checkpoint(
            runtime_state=self.runner.state,
            reconciliation=self._reconciliation,
            readiness=self._readiness,
            thesis_state_ids=(
                (self.runner.thesis.state_id,) if self.runner.thesis is not None else ()
            ),
            available_at=self._clock(),
        )
        self.execution_ledger.append_checkpoint(checkpoint)
        self._append_semantic(checkpoint, event_id=self._last_event_id)
        self.journal.sync()
        self.execution_ledger.sync()
        self.position_action_ledger.sync()
        if self._gateway is not None:
            self._gateway.close()
        self._phase = StartupPhase.STOPPED
        return self.status
