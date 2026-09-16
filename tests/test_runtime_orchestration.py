from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from axq.agents import ContinuityStatus
from axq.execution_boundary import (
    BrokerRecoverySnapshot,
    ExecutionIntent,
    ExecutionMode,
    ExecutionOrderType,
    ExecutionReason,
    ExecutionResult,
    ExecutionResultStatus,
    ResumeBlockReason,
    ResumeStatus,
    SQLiteExecutionLedger,
    default_execution_policy,
)
from axq.orchestration import (
    DecisionCycle,
    DecisionPlan,
    DeterministicDecisionProcessor,
    OperatorControls,
    RuntimeConfig,
    RuntimeMode,
    RuntimeOrchestrator,
    RuntimeRunSummary,
    RuntimeStatus,
    StartupPhase,
    build_mt5_gateway,
    load_runtime_config,
)
from axq.position_actions import (
    PositionActionIntent,
    PositionActionReason,
    PositionActionType,
)
from axq.position_actions.persistence import SQLitePositionActionTransportLedger
from axq.position_actions.transport import PositionActionTransportResult
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    ExposureState,
    FreshnessStatus,
    MarketState,
    OrderBookState,
    PositionBookState,
    PositionSide,
    ReplayClock,
    RuntimeEvent,
    RuntimeEventType,
    initial_runtime_state,
    reduce_state,
)
from axq.runtime.journal import JournalRecord, JournalRecordType, SQLiteRuntimeJournal
from axq.runtime.kernel import AGENT_ORDER, EvidenceKernel
from axq.runtime.replay import RuntimeStreamRunner
from axq.schemas import Signal
from axq.tools import ToolCatalog

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _fresh(component: str, at: datetime = T0) -> ComponentFreshness:
    return ComponentFreshness(
        component=component,
        status=FreshnessStatus.AVAILABLE,
        observed_at=at,
        available_at=at,
        stale_after_ms=30_000,
    )


def _snapshot(at: datetime = T0) -> BrokerRecoverySnapshot:
    return BrokerRecoverySnapshot(
        source="mt5-fixture",
        source_version="1.0",
        as_of=at,
        observed_at=at,
        available_at=at,
        account=AccountState(
            source="mt5",
            account_id="demo",
            as_of=at,
            freshness=_fresh("account", at),
            balance=10_000.0,
            equity=10_000.0,
            free_margin=9_000.0,
            used_margin=1_000.0,
        ),
        market=MarketState(
            source="mt5",
            symbol="XAUUSD",
            as_of=at,
            freshness=_fresh("market", at),
            bid=2499.99,
            ask=2500.01,
            last=2500.0,
            spread_points=2.0,
        ),
        positions=PositionBookState(
            source="mt5", as_of=at, freshness=_fresh("positions", at)
        ),
        orders=OrderBookState(source="mt5", as_of=at, freshness=_fresh("orders", at)),
        exposure=ExposureState(
            as_of=at,
            freshness=_fresh("exposure", at),
            gross_lots=0.0,
            net_lots=0.0,
            gross_notional=0.0,
            net_notional=0.0,
        ),
        broker_constraints=BrokerConstraints(
            source="mt5",
            symbol="XAUUSD",
            as_of=at,
            freshness=_fresh("broker_constraints", at),
            trade_allowed=True,
            volume_min=0.01,
            volume_max=10.0,
            volume_step=0.01,
            point_size=0.01,
            tick_size=0.01,
            tick_value_loss=1.0,
        ),
    )


def _intent() -> ExecutionIntent:
    policy = type(default_execution_policy()).model_validate(
        default_execution_policy().model_dump()
        | {"policy_id": "", "mode": ExecutionMode.DEMO_ENABLED}
    )
    return ExecutionIntent(
        evidence_bundle_id="eb-orchestration",
        master_proposal_id="mp-orchestration",
        discipline_outcome_id="do-orchestration",
        risk_outcome_id="ro-orchestration",
        risk_context_id="rc-orchestration",
        setup_id="setup-orchestration",
        thesis_id="thesis-orchestration",
        scenario_id="scenario-orchestration",
        symbol="XAUUSD",
        broker_symbol="GOLD.a",
        broker_source="mt5",
        point_size=0.01,
        direction=Signal.BUY,
        approved_volume_lots=0.01,
        order_type=ExecutionOrderType.MARKET,
        requested_entry_price=2500.0,
        stop_loss_price=2490.0,
        as_of=T0,
        available_at=T0,
        expires_at=T0 + timedelta(seconds=15),
        execution_policy_id=policy.policy_id,
        execution_policy_version=policy.policy_version,
        execution_mode=policy.mode,
    )


def _unknown_result(intent: ExecutionIntent) -> ExecutionResult:
    return ExecutionResult(
        execution_intent_id=intent.intent_id,
        evidence_bundle_id=intent.evidence_bundle_id,
        master_proposal_id=intent.master_proposal_id,
        discipline_outcome_id=intent.discipline_outcome_id,
        risk_outcome_id=intent.risk_outcome_id,
        setup_id=intent.setup_id,
        thesis_id=intent.thesis_id,
        scenario_id=intent.scenario_id,
        symbol=intent.symbol,
        direction=intent.direction,
        status=ExecutionResultStatus.UNKNOWN,
        reason_code=ExecutionReason.UNKNOWN_SUBMISSION,
        reason="acknowledgement unavailable",
        requested_volume_lots=intent.approved_volume_lots,
        filled_volume_lots=None,
        remaining_volume_lots=None,
        requested_price=intent.requested_entry_price,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
    )


class FakeGateway:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.connected = 0
        self.closed = 0

    def connect(self) -> None:
        self.connected += 1
        if self.fail:
            raise RuntimeError("broker unavailable")

    def close(self) -> None:
        self.closed += 1


class FakeSnapshotProvider:
    def __init__(self, snapshot: BrokerRecoverySnapshot) -> None:
        self.snapshot = snapshot
        self.calls = 0

    def capture(self) -> BrokerRecoverySnapshot:
        self.calls += 1
        if self.snapshot.market.freshness.status is FreshnessStatus.STALE:
            return self.snapshot
        return _snapshot(self.snapshot.as_of + timedelta(seconds=self.calls - 1))


class FakeRunner:
    def __init__(self) -> None:
        self._state = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
        self._thesis = None
        self.processed: list[str] = []
        self.broker_refreshed: list[RuntimeEvent] = []

    @property
    def state(self):
        return self._state

    @property
    def thesis(self):
        return self._thesis

    def process(self, event: RuntimeEvent, feature_snapshot=None):
        self._state = reduce_state(self._state, event, now=event.available_at)
        self.processed.append(event.event_id)
        return SimpleNamespace(
            event_id=event.event_id,
            thesis_state_id=None,
            scenario_state_ids=(),
            bundle=SimpleNamespace(bundle_id=f"eb-{event.event_id}"),
        )

    def reduce_broker_refresh(self, event: RuntimeEvent):
        self._state = reduce_state(self._state, event, now=event.available_at)
        self.broker_refreshed.append(event)
        return self._state

    def restore_thesis(self, thesis) -> None:
        self._thesis = thesis

    def restore_runtime(self, state, memories=()) -> None:
        self._state = state


class FakeProcessor:
    def __init__(self, plan: DecisionPlan | None = None) -> None:
        self.plan = plan or DecisionPlan()
        self.calls: list[str] = []

    def evaluate(self, event, state, trace, readiness, controls):
        self.calls.append(event.event_id)
        return self.plan


class FakeEntryAdapter:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, intent: ExecutionIntent) -> ExecutionResult:
        self.calls += 1
        return ExecutionResult(
            execution_intent_id=intent.intent_id,
            evidence_bundle_id=intent.evidence_bundle_id,
            master_proposal_id=intent.master_proposal_id,
            discipline_outcome_id=intent.discipline_outcome_id,
            risk_outcome_id=intent.risk_outcome_id,
            setup_id=intent.setup_id,
            thesis_id=intent.thesis_id,
            scenario_id=intent.scenario_id,
            symbol=intent.symbol,
            direction=intent.direction,
            status=ExecutionResultStatus.REJECTED,
            reason_code=ExecutionReason.BROKER_REJECTED,
            reason="fake rejection",
            requested_volume_lots=intent.approved_volume_lots,
            filled_volume_lots=0.0,
            remaining_volume_lots=intent.approved_volume_lots,
            requested_price=intent.requested_entry_price,
            event_time=T0 + timedelta(seconds=2),
            observed_at=T0 + timedelta(seconds=2),
            available_at=T0 + timedelta(seconds=2),
        )


def _position_action_intent() -> PositionActionIntent:
    return PositionActionIntent(
        policy_id="pap-orchestration",
        safety_outcome_id="pas-orchestration",
        position_management_outcome_id="pmo-orchestration",
        position_id="pos-exact",
        broker_ticket=123,
        original_execution_intent_id="xi-orchestration",
        original_execution_result_id="xe-orchestration",
        broker_intent_link_id="bil-orchestration",
        reconciliation_report_id="rr-orchestration",
        resume_readiness_id="ready-orchestration",
        setup_id="setup-orchestration",
        thesis_id="thesis-orchestration",
        scenario_id="scenario-orchestration",
        action_type=PositionActionType.CLOSE_POSITION,
        symbol="XAUUSD",
        position_side=PositionSide.BUY,
        current_volume_lots=0.05,
        requested_close_volume_lots=0.05,
        existing_stop_loss=2490.0,
        audit_reason_codes=(PositionActionReason.CLOSE_POSITION_SAFE,),
        as_of=T0,
        available_at=T0,
    )


class FakePositionActionAdapter:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, intent: PositionActionIntent) -> PositionActionTransportResult:
        self.calls += 1
        return PositionActionTransportResult(
            position_action_intent_id=intent.intent_id,
            action_type=intent.action_type,
            position_id=intent.position_id,
            broker_ticket=intent.broker_ticket,
            symbol=intent.symbol,
            position_side=intent.position_side,
            status=ExecutionResultStatus.FILLED,
            requested_volume_lots=intent.requested_close_volume_lots,
            executed_volume_lots=intent.requested_close_volume_lots,
            fill_price=2500.0,
            transport_execution_id="mt5-deal-456",
            broker_retcode="10009",
            broker_status="done",
            event_time=T0 + timedelta(seconds=2),
            observed_at=T0 + timedelta(seconds=2),
            available_at=T0 + timedelta(seconds=2),
        )


def _market_event(sequence: int = 100) -> RuntimeEvent:
    at = T0 + timedelta(seconds=1)
    return RuntimeEvent(
        event_type=RuntimeEventType.M5_CLOSED,
        event_time=at,
        observed_at=at,
        available_at=at,
        source="fixture",
        source_version="1",
        source_sequence=sequence,
        symbol="XAUUSD",
        payload=_snapshot(at).market,
    )


def _service(
    tmp_path: Path,
    mode: RuntimeMode,
    *,
    plan: DecisionPlan | None = None,
    action_adapter: FakePositionActionAdapter | None = None,
    snapshot: BrokerRecoverySnapshot | None = None,
    clock: Callable[[], datetime] | None = None,
):
    config = RuntimeConfig(
        mode=mode,
        symbol="XAUUSD",
        broker_symbol="GOLD.a",
        runtime_journal_path=tmp_path / "runtime.sqlite3",
        execution_ledger_path=tmp_path / "execution.sqlite3",
        position_action_ledger_path=tmp_path / "actions.sqlite3",
    )
    gateway = FakeGateway()
    entry = FakeEntryAdapter()
    processor = FakeProcessor(plan)
    service = RuntimeOrchestrator(
        config=config,
        runner=FakeRunner(),
        processor=processor,
        journal=SQLiteRuntimeJournal(config.runtime_journal_path),
        execution_ledger=SQLiteExecutionLedger(config.execution_ledger_path),
        position_action_ledger=SQLitePositionActionTransportLedger(
            config.position_action_ledger_path
        ),
        gateway=gateway,
        snapshot_provider=FakeSnapshotProvider(snapshot or _snapshot()),
        entry_adapter=entry,
        position_action_adapter=action_adapter,
        clock=clock or (lambda: T0),
    )
    return service, gateway, entry, processor


def test_runtime_config_is_strict_non_mutating_and_has_no_live_mode(tmp_path: Path) -> None:
    config = RuntimeConfig(
        symbol="XAUUSD",
        broker_symbol="GOLD.a",
        runtime_journal_path=tmp_path / "runtime.sqlite3",
        execution_ledger_path=tmp_path / "execution.sqlite3",
        position_action_ledger_path=tmp_path / "actions.sqlite3",
    )

    assert config.mode is RuntimeMode.DISABLED
    assert set(RuntimeMode) == {
        RuntimeMode.DISABLED,
        RuntimeMode.REPLAY,
        RuntimeMode.SHADOW,
        RuntimeMode.DEMO,
    }
    with pytest.raises(ValidationError):
        RuntimeConfig.model_validate(config.model_dump() | {"unknown": True})


def test_operator_controls_only_become_more_conservative() -> None:
    controls = OperatorControls()
    paused = controls.pause("operator review")
    disabled = paused.disable_execution("transport review")
    killed = disabled.activate_kill_switch("emergency")

    assert paused.pause_new_entries
    assert disabled.execution_disabled
    assert killed.kill_switch
    with pytest.raises(ValueError, match="cannot be cleared"):
        killed.clear_kill_switch()


def test_runtime_status_rejects_naive_time_and_is_content_addressed() -> None:
    status = RuntimeStatus(
        mode=RuntimeMode.REPLAY,
        startup_phase=StartupPhase.SAFE,
        as_of=T0,
        accepting_events=True,
        safe_to_process_new_trades=True,
    )
    assert status.status_id.startswith("rts-")
    assert status == RuntimeStatus.model_validate(status.model_dump())
    with pytest.raises(ValidationError):
        RuntimeStatus(
            mode=RuntimeMode.REPLAY,
            startup_phase=StartupPhase.SAFE,
            as_of=datetime(2025, 1, 6, 12, 0),
            accepting_events=True,
            safe_to_process_new_trades=True,
        )


def test_summary_is_deterministic_and_counts_existing_results() -> None:
    cycles = (
        DecisionCycle(
            event_id="ev-a",
            event_type=RuntimeEventType.M5_CLOSED,
            available_at=T0,
            master_result="BUY",
            discipline_result="PASS",
            risk_result="PASS",
            execution_intent_ids=("ei-a",),
        ),
        DecisionCycle(
            event_id="ev-b",
            event_type=RuntimeEventType.TICK,
            available_at=T0,
            master_result="HOLD",
            discipline_result="NO_ACTION",
            risk_result="NO_ACTION",
            position_management_actions=("HOLD_POSITION",),
        ),
    )
    first = RuntimeRunSummary.from_cycles(cycles)
    second = RuntimeRunSummary.from_cycles(cycles)

    assert first.summary_id == second.summary_id
    assert {item.name: item.count for item in first.master_counts} == {
        "BUY": 1,
        "HOLD": 1,
    }
    assert first.execution_intent_count == 1
    assert {
        item.name: item.count for item in first.position_management_counts
    } == {"HOLD_POSITION": 1}


def test_explicit_terminal_path_is_forwarded_without_entering_config_identity(
    tmp_path: Path,
) -> None:
    terminal = tmp_path / "terminal64.exe"
    config = RuntimeConfig(
        mode=RuntimeMode.SHADOW,
        symbol="XAUUSD",
        broker_symbol="GOLD.a",
        runtime_journal_path=tmp_path / "runtime.sqlite3",
        execution_ledger_path=tmp_path / "execution.sqlite3",
        position_action_ledger_path=tmp_path / "actions.sqlite3",
        mt5_terminal_path=terminal,
    )
    gateway = build_mt5_gateway(config)

    assert gateway.terminal_path == terminal
    assert "config_id" not in type(config).model_fields


def test_checked_in_runtime_config_is_strict_and_disabled() -> None:
    config = load_runtime_config("configs/runtime/demo.yaml")
    assert config.mode is RuntimeMode.DISABLED
    assert config.symbol == "XAUUSD"
    assert config.mt5_terminal_path is None


def test_runtime_journal_supports_execution_and_recovery_semantics() -> None:
    intent_record = JournalRecord.from_semantic(_intent(), event_id="ev-parent")
    assert intent_record.record_type is JournalRecordType.EXECUTION_INTENT
    assert intent_record.decode() == _intent()


def test_concrete_decision_processor_is_exposed_as_shared_composition_boundary() -> None:
    assert DeterministicDecisionProcessor.__doc__


@pytest.mark.parametrize("mode", [RuntimeMode.DISABLED, RuntimeMode.REPLAY])
def test_offline_startup_never_connects_broker(tmp_path: Path, mode: RuntimeMode) -> None:
    service, gateway, _, _ = _service(tmp_path, mode)
    status = service.startup()
    assert status.startup_phase is StartupPhase.SAFE
    assert gateway.connected == 0
    assert not status.safe_to_process_new_trades


def test_shadow_startup_reduces_snapshot_and_is_safe_but_non_mutating(tmp_path: Path) -> None:
    service, gateway, entry, processor = _service(
        tmp_path, RuntimeMode.SHADOW, plan=DecisionPlan(execution_intent=_intent())
    )
    status = service.startup()
    cycle = service.process_event(_market_event())

    assert status.resume_status == ResumeStatus.SAFE.value
    assert gateway.connected == 1
    assert tuple(event.event_type for event in service.runner.broker_refreshed) == (
        RuntimeEventType.TICK,
        RuntimeEventType.ACCOUNT_UPDATED,
        RuntimeEventType.POSITIONS_UPDATED,
        RuntimeEventType.ORDERS_UPDATED,
        RuntimeEventType.EXPOSURE_UPDATED,
        RuntimeEventType.BROKER_CONSTRAINTS_UPDATED,
    )
    assert service.runner.processed == [_market_event().event_id]
    assert processor.calls
    assert cycle.execution_intent_ids == (_intent().intent_id,)
    assert entry.calls == 0


def test_refresh_sequence_advances_past_accepted_market_event(tmp_path: Path) -> None:
    now = [T0]
    service, _, _, _ = _service(
        tmp_path,
        RuntimeMode.SHADOW,
        clock=lambda: now[0],
    )
    assert service.startup().startup_phase is StartupPhase.SAFE
    event = _market_event(sequence=1_000_600).model_copy(
        update={"source": "mt5-fixture"}
    )

    service.process_event(event)
    now[0] = T0 + timedelta(seconds=6)

    assert service.refresh_snapshot_if_due() is True
    assert service.status.startup_phase is StartupPhase.SAFE
    assert service.runner.broker_refreshed[-1].source_sequence == 1_000_606


def test_created_event_submitted_after_newer_refresh_is_rejected(tmp_path: Path) -> None:
    now = [T0 + timedelta(seconds=1)]
    service, _, _, _ = _service(
        tmp_path,
        RuntimeMode.SHADOW,
        snapshot=_snapshot(T0 + timedelta(seconds=1)),
        clock=lambda: now[0],
    )
    assert service.startup().startup_phase is StartupPhase.SAFE
    created_event = _market_event(sequence=1_000_600)
    now[0] = T0 + timedelta(seconds=7)
    assert service.refresh_snapshot_if_due() is True

    with pytest.raises(ValueError, match="event violates global event order"):
        service.process_event(created_event)


def test_real_runner_stale_startup_refresh_never_enters_scenario_path(
    tmp_path: Path,
) -> None:
    config = RuntimeConfig(
        mode=RuntimeMode.SHADOW,
        symbol="XAUUSD",
        broker_symbol="GOLD.a",
        runtime_journal_path=tmp_path / "runtime.sqlite3",
        execution_ledger_path=tmp_path / "execution.sqlite3",
        position_action_ledger_path=tmp_path / "actions.sqlite3",
    )
    journal = SQLiteRuntimeJournal(config.runtime_journal_path)
    scenario_events: list[RuntimeEventType] = []

    def scenario_transition(event, bundle, previous):
        del bundle, previous
        scenario_events.append(event.event_type)
        return None

    runner = RuntimeStreamRunner(
        EvidenceKernel(
            initial_state=initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1)),
            catalog=ToolCatalog(()),
            tool_access={name: () for name in AGENT_ORDER},
        ),
        ReplayClock(T0),
        journal=journal,
        scenario_transition=scenario_transition,
    )
    snapshot = _snapshot()
    stale_at = T0 - timedelta(days=2)
    stale_snapshot = snapshot.model_copy(
        update={
            "market": snapshot.market.model_copy(
                update={
                    "as_of": stale_at,
                    "freshness": ComponentFreshness(
                        component="market",
                        status=FreshnessStatus.STALE,
                        observed_at=stale_at,
                        available_at=T0,
                        stale_after_ms=30_000,
                    ),
                }
            )
        }
    )
    processor = FakeProcessor()
    service = RuntimeOrchestrator(
        config=config,
        runner=runner,
        processor=processor,
        journal=journal,
        execution_ledger=SQLiteExecutionLedger(config.execution_ledger_path),
        position_action_ledger=SQLitePositionActionTransportLedger(
            config.position_action_ledger_path
        ),
        gateway=FakeGateway(),
        snapshot_provider=FakeSnapshotProvider(stale_snapshot),
        clock=lambda: T0,
    )

    status = service.startup()

    assert status.startup_phase is StartupPhase.SAFE
    assert status.accepting_events is True
    assert status.safe_to_process_new_trades is False
    assert status.resume_status == ResumeStatus.BLOCKED.value
    assert scenario_events == []
    assert processor.calls == []
    assert runner.steps == ()
    types = tuple(item.record.record_type for item in journal.records())
    assert types.count(JournalRecordType.RUNTIME_EVENT) == 6
    assert types.count(JournalRecordType.RUNTIME_STATE) == 6
    assert types.count(JournalRecordType.OUTCOME) == 6


def test_shadow_stale_market_is_healthy_waiting_while_demo_remains_blocked(
    tmp_path: Path,
) -> None:
    snapshot = _snapshot()
    stale_market = snapshot.market.model_copy(
        update={
            "as_of": T0 - timedelta(days=2),
            "freshness": ComponentFreshness(
                component="market",
                status=FreshnessStatus.STALE,
                observed_at=T0 - timedelta(days=2),
                available_at=T0,
                stale_after_ms=30_000,
            ),
        }
    )
    stale_snapshot = snapshot.model_copy(update={"market": stale_market})
    shadow, _, _, shadow_processor = _service(
        tmp_path / "shadow",
        RuntimeMode.SHADOW,
        snapshot=stale_snapshot,
    )
    demo, _, _, _ = _service(
        tmp_path / "demo",
        RuntimeMode.DEMO,
        snapshot=stale_snapshot,
    )

    shadow_status = shadow.startup()
    demo_status = demo.startup()

    assert shadow_status.startup_phase is StartupPhase.SAFE
    assert shadow_status.accepting_events is True
    assert shadow_status.safe_to_process_new_trades is False
    assert shadow_status.resume_status == ResumeStatus.BLOCKED.value
    assert shadow_status.last_error is None
    assert shadow_processor.calls == []
    assert shadow._readiness is not None
    assert shadow._readiness.reason_codes == (ResumeBlockReason.MARKET_NOT_FRESH,)
    assert demo_status.startup_phase is StartupPhase.BLOCKED


def test_shadow_flat_recovery_can_accept_event_that_supersedes_expired_thesis(
    tmp_path: Path,
) -> None:
    service, _, entry, processor = _service(tmp_path, RuntimeMode.SHADOW)
    service.runner._thesis = SimpleNamespace(
        continuity_status=ContinuityStatus.COMPLETE,
        expires_at=T0 - timedelta(seconds=1),
        state_id="thesis-state-expired",
        scenarios=(),
    )

    status = service.startup()

    assert status.startup_phase is StartupPhase.SAFE
    assert status.resume_status == ResumeStatus.BLOCKED.value
    assert service._readiness is not None
    assert service._readiness.reason_codes == (ResumeBlockReason.THESIS_EXPIRED,)
    service.process_event(_market_event())
    assert processor.calls == [_market_event().event_id]
    assert entry.calls == 0


def test_demo_runs_entry_then_reduces_canonical_feedback(tmp_path: Path) -> None:
    service, _, entry, _ = _service(
        tmp_path, RuntimeMode.DEMO, plan=DecisionPlan(execution_intent=_intent())
    )
    service.startup()
    cycle = service.process_event(_market_event())

    assert entry.calls == 1
    assert len(cycle.execution_result_ids) == 1
    assert service.runner.processed[-1] != _market_event().event_id


def test_operator_pause_and_kill_switch_block_demo_mutation(tmp_path: Path) -> None:
    for controls in (
        OperatorControls().pause("review"),
        OperatorControls().activate_kill_switch("emergency"),
    ):
        service, _, entry, _ = _service(
            tmp_path / str(len(controls.reason_codes)),
            RuntimeMode.DEMO,
            plan=DecisionPlan(execution_intent=_intent()),
        )
        service.set_operator_controls(controls)
        service.startup()
        service.process_event(_market_event())
        assert entry.calls == 0


def test_entry_pause_does_not_block_existing_position_safety_action(tmp_path: Path) -> None:
    adapter = FakePositionActionAdapter()
    service, _, _, _ = _service(
        tmp_path,
        RuntimeMode.DEMO,
        plan=DecisionPlan(position_action_intents=(_position_action_intent(),)),
        action_adapter=adapter,
    )
    service.set_operator_controls(OperatorControls().pause("pause entries only"))
    service.startup()

    cycle = service.process_event(_market_event())

    assert adapter.calls == 1
    assert len(cycle.position_action_result_ids) == 1


def test_broker_unavailable_fails_closed_without_decision(tmp_path: Path) -> None:
    service, gateway, _, processor = _service(tmp_path, RuntimeMode.DEMO)
    gateway.fail = True
    status = service.startup()
    assert status.startup_phase is StartupPhase.BLOCKED
    assert not status.safe_to_process_new_trades
    assert processor.calls == []
    with pytest.raises(RuntimeError, match="startup recovery"):
        service.process_event(_market_event())


def test_unknown_submission_blocks_startup_and_is_never_resent(tmp_path: Path) -> None:
    service, _, entry, processor = _service(
        tmp_path, RuntimeMode.DEMO, plan=DecisionPlan(execution_intent=_intent())
    )
    intent = _intent()
    assert service.execution_ledger.reserve(intent)
    service.execution_ledger.record(_unknown_result(intent))

    status = service.startup()

    assert status.startup_phase is StartupPhase.BLOCKED
    assert status.resume_status == ResumeStatus.BLOCKED.value
    assert entry.calls == 0
    assert processor.calls == []


def test_graceful_shutdown_flushes_all_stores_and_closes_gateway(tmp_path: Path) -> None:
    service, gateway, _, _ = _service(tmp_path, RuntimeMode.SHADOW)
    service.startup()
    status = service.shutdown()
    assert status.startup_phase is StartupPhase.STOPPED
    assert gateway.closed == 1
    assert service.execution_ledger.latest_checkpoint() is not None


def test_replay_and_shadow_share_decision_cycle_identity(tmp_path: Path) -> None:
    replay, _, _, _ = _service(tmp_path / "replay", RuntimeMode.REPLAY)
    shadow, _, _, _ = _service(tmp_path / "shadow", RuntimeMode.SHADOW)
    replay.startup()
    shadow.startup()
    assert replay.process_event(_market_event()).cycle_id == shadow.process_event(
        _market_event()
    ).cycle_id
