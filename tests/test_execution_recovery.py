from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.agents import ContinuityStatus
from axq.execution_boundary import (
    BrokerIntentLink,
    BrokerObjectKind,
    BrokerRecoverySnapshot,
    DemoExecutionAdapter,
    ExecutionIntent,
    ExecutionMode,
    ExecutionObservation,
    ExecutionOrderType,
    ExecutionReason,
    ExecutionResult,
    ExecutionResultStatus,
    ReconciliationKind,
    ResolutionStatus,
    ResumeBlockReason,
    ResumeStatus,
    SQLiteExecutionLedger,
    UnknownSubmissionState,
    broker_snapshot_runtime_events,
    create_recovery_checkpoint,
    default_execution_policy,
    evaluate_resume_readiness,
    persist_graceful_shutdown,
    reconcile_execution_state,
)
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
    PositionState,
    RuntimeEventType,
    initial_runtime_state,
    reduce_state,
)
from axq.runtime.journal import SQLiteRuntimeJournal
from axq.schemas import Signal

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _fresh(component: str, *, status: FreshnessStatus = FreshnessStatus.AVAILABLE):
    return ComponentFreshness(
        component=component,
        status=status,
        observed_at=T0 if status is not FreshnessStatus.UNKNOWN else None,
        available_at=T0 if status is not FreshnessStatus.UNKNOWN else None,
        stale_after_ms=30_000 if status is not FreshnessStatus.UNKNOWN else None,
    )


def _intent() -> ExecutionIntent:
    policy = type(default_execution_policy()).model_validate(
        default_execution_policy().model_dump()
        | {"policy_id": "", "mode": ExecutionMode.DEMO_ENABLED}
    )
    return ExecutionIntent(
        evidence_bundle_id="eb-recovery",
        master_proposal_id="mp-recovery",
        discipline_outcome_id="do-recovery",
        risk_outcome_id="ro-recovery",
        risk_context_id="rc-recovery",
        setup_id="setup-recovery",
        thesis_id="thesis-recovery",
        scenario_id="scenario-recovery",
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        broker_source="mt5",
        point_size=0.01,
        direction=Signal.BUY,
        approved_volume_lots=0.05,
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


def _result(status: ExecutionResultStatus) -> ExecutionResult:
    intent = _intent()
    unknown = status is ExecutionResultStatus.UNKNOWN
    filled = 0.05 if status is ExecutionResultStatus.FILLED else 0.0
    reason = (
        ExecutionReason.UNKNOWN_SUBMISSION
        if unknown
        else ExecutionReason.BROKER_REJECTED
        if status is ExecutionResultStatus.REJECTED
        else None
    )
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
        status=status,
        reason_code=reason,
        reason="ack lost" if unknown else "rejected" if reason else None,
        requested_volume_lots=0.05,
        filled_volume_lots=None if unknown else filled,
        remaining_volume_lots=None if unknown else round(0.05 - filled, 10),
        requested_price=2500.0,
        fill_price=2500.0 if filled else None,
        broker_ticket=None if unknown else 123,
        transport_execution_id="transport-1",
        event_time=T0 + timedelta(seconds=1),
        observed_at=T0 + timedelta(seconds=1),
        available_at=T0 + timedelta(seconds=1),
    )


def _snapshot(
    *,
    positions: tuple[PositionState, ...] = (),
    links: tuple[BrokerIntentLink, ...] = (),
    stale_component: str | None = None,
) -> BrokerRecoverySnapshot:
    def freshness(name: str) -> ComponentFreshness:
        status = FreshnessStatus.STALE if stale_component == name else FreshnessStatus.AVAILABLE
        return _fresh(name, status=status)

    return BrokerRecoverySnapshot(
        source="mt5-fixture",
        source_version="1.0",
        as_of=T0,
        observed_at=T0,
        available_at=T0,
        account=AccountState(
            source="mt5",
            account_id="demo",
            as_of=T0,
            freshness=freshness("account"),
            balance=10_000,
            equity=10_000,
            free_margin=9_000,
            used_margin=1_000,
        ),
        market=MarketState(
            source="mt5",
            symbol="XAUUSD",
            as_of=T0,
            freshness=freshness("market"),
            bid=2499.99,
            ask=2500.01,
            last=2500.0,
            spread_points=2.0,
        ),
        positions=PositionBookState(
            source="mt5",
            as_of=T0,
            freshness=freshness("positions"),
            positions=positions,
        ),
        orders=OrderBookState(source="mt5", as_of=T0, freshness=freshness("orders")),
        exposure=ExposureState(
            as_of=T0,
            freshness=freshness("exposure"),
            gross_lots=0.05 if positions else 0.0,
            net_lots=0.05 if positions else 0.0,
            gross_notional=125.0 if positions else 0.0,
            net_notional=125.0 if positions else 0.0,
        ),
        broker_constraints=BrokerConstraints(
            source="mt5",
            symbol="XAUUSD",
            as_of=T0,
            freshness=freshness("broker_constraints"),
            trade_allowed=True,
            volume_min=0.01,
            volume_max=10.0,
            volume_step=0.01,
            point_size=0.01,
            tick_size=0.01,
            tick_value_loss=1.0,
        ),
        intent_links=links,
    )


def _position(*, ticket: int = 123, side: PositionSide = PositionSide.BUY, volume: float = 0.05):
    return PositionState(
        source="mt5",
        broker_ticket=ticket,
        symbol="XAUUSD",
        side=side,
        volume_lots=volume,
        opened_at=T0,
        open_price=2500.0,
        stop_loss=2490.0,
        setup_id="setup-recovery",
        thesis_id="thesis-recovery",
    )


def _link(position: PositionState, *, ticket: int | None = 123) -> BrokerIntentLink:
    return BrokerIntentLink(
        intent_id=_intent().intent_id,
        object_kind=BrokerObjectKind.POSITION,
        broker_object_id=position.position_id,
        broker_ticket=ticket,
        transport_execution_id="transport-1",
    )


def test_runtime_refresh_uses_canonical_exposure_and_constraint_events() -> None:
    snapshot = _snapshot()
    events = broker_snapshot_runtime_events(snapshot, source_sequence_start=10)
    assert tuple(event.event_type for event in events) == (
        RuntimeEventType.TICK,
        RuntimeEventType.ACCOUNT_UPDATED,
        RuntimeEventType.POSITIONS_UPDATED,
        RuntimeEventType.ORDERS_UPDATED,
        RuntimeEventType.EXPOSURE_UPDATED,
        RuntimeEventType.BROKER_CONSTRAINTS_UPDATED,
    )
    state = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    for event in events:
        state = reduce_state(state, event, now=event.available_at)
    assert state.exposure == snapshot.exposure
    assert state.broker_constraints == snapshot.broker_constraints


@pytest.mark.parametrize(
    "terminal_status",
    [ExecutionResultStatus.FILLED, ExecutionResultStatus.REJECTED],
)
def test_durable_terminal_result_survives_reopen_and_blocks_resubmit(
    terminal_status, tmp_path
) -> None:
    path = tmp_path / "execution.sqlite3"
    intent = _intent()
    first = SQLiteExecutionLedger(path)
    assert first.reserve(intent)
    first.record(_result(terminal_status))
    reopened = SQLiteExecutionLedger(path)
    assert reopened.get(intent.intent_id).status is terminal_status
    assert not reopened.reserve(intent)


def test_unknown_is_durable_and_adapter_never_resubmits(tmp_path) -> None:
    path = tmp_path / "execution.sqlite3"
    intent = _intent()
    policy = type(default_execution_policy()).model_validate(
        default_execution_policy().model_dump()
        | {"policy_id": "", "mode": ExecutionMode.DEMO_ENABLED}
    )
    calls = 0

    class Transport:
        def submit(self, intent, observation):
            nonlocal calls
            calls += 1
            raise UnknownSubmissionState("ack lost")

    def observation(_intent):
        return ExecutionObservation(
            observed_at=T0,
            available_at=T0,
            account_mode="DEMO",
            broker_symbol="XAUUSD",
            market_price=2500.0,
            spread_points=2.0,
            estimated_slippage_points=1.0,
        )

    DemoExecutionAdapter(
        policy=policy,
        ledger=SQLiteExecutionLedger(path),
        observation_provider=observation,
        transport=Transport(),
    ).execute(intent)
    result = DemoExecutionAdapter(
        policy=policy,
        ledger=SQLiteExecutionLedger(path),
        observation_provider=observation,
        transport=Transport(),
    ).execute(intent)
    assert result.status is ExecutionResultStatus.UNKNOWN
    assert calls == 1
    assert SQLiteExecutionLedger(path).requires_reconciliation(intent.intent_id)


def test_execution_storage_is_append_only(tmp_path) -> None:
    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    ledger.reserve(_intent())
    connection = sqlite3.connect(ledger.path)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute("UPDATE execution_transitions SET intent_id = 'changed'")
    connection.close()


def test_unknown_exact_broker_link_resolves_by_appending_superseding_report(tmp_path) -> None:
    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    ledger.reserve(_intent())
    ledger.record(_result(ExecutionResultStatus.UNKNOWN))
    unresolved = reconcile_execution_state(ledger, _snapshot(), as_of=T0)
    position = _position()
    resolved = reconcile_execution_state(
        ledger,
        _snapshot(positions=(position,), links=(_link(position),)),
        as_of=T0 + timedelta(seconds=1),
        prior_report=unresolved,
    )
    assert unresolved.status is ResolutionStatus.RECONCILIATION_REQUIRED
    with pytest.raises(ValueError, match="supersede"):
        reconcile_execution_state(
            ledger,
            _snapshot(positions=(position,), links=(_link(position),)),
            as_of=T0 + timedelta(seconds=1),
        )
    assert resolved.status is ResolutionStatus.RESOLVED
    assert resolved.supersedes_report_id == unresolved.report_id
    assert ledger.latest_reconciliation().report_id == resolved.report_id
    assert len(ledger.reconciliations()) == 2
    assert not ledger.requires_reconciliation(_intent().intent_id)


def test_unknown_without_exact_link_remains_unknown_and_similar_values_do_not_match(
    tmp_path,
) -> None:
    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    ledger.reserve(_intent())
    ledger.record(_result(ExecutionResultStatus.UNKNOWN))
    report = reconcile_execution_state(
        ledger, _snapshot(positions=(_position(ticket=999),)), as_of=T0
    )
    assert {finding.kind for finding in report.findings} == {
        ReconciliationKind.UNKNOWN,
        ReconciliationKind.BROKER_ONLY,
    }
    assert report.status is ResolutionStatus.RECONCILIATION_REQUIRED


@pytest.mark.parametrize(
    ("position", "link_ticket", "reason"),
    [
        (_position(ticket=999), 999, "TICKET_MISMATCH"),
        (_position(side=PositionSide.SELL), 123, "DIRECTION_MISMATCH"),
        (_position(volume=0.04), 123, "VOLUME_MISMATCH"),
    ],
)
def test_exact_link_conflicts_are_explicit(position, link_ticket, reason, tmp_path) -> None:
    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    ledger.reserve(_intent())
    ledger.record(_result(ExecutionResultStatus.FILLED))
    report = reconcile_execution_state(
        ledger,
        _snapshot(positions=(position,), links=(_link(position, ticket=link_ticket),)),
        as_of=T0,
    )
    finding = report.findings[0]
    assert finding.kind is ReconciliationKind.CONFLICT
    assert finding.reason_code == reason


def test_local_only_and_broker_only_are_distinct_anomalies(tmp_path) -> None:
    local = SQLiteExecutionLedger(tmp_path / "local.sqlite3")
    local.reserve(_intent())
    local.record(_result(ExecutionResultStatus.FILLED))
    assert (
        reconcile_execution_state(local, _snapshot(), as_of=T0).findings[0].kind
        is ReconciliationKind.LOCAL_ONLY
    )
    empty = SQLiteExecutionLedger(tmp_path / "empty.sqlite3")
    position = _position(ticket=888)
    report = reconcile_execution_state(empty, _snapshot(positions=(position,)), as_of=T0)
    assert report.findings[0].kind is ReconciliationKind.BROKER_ONLY


@pytest.mark.parametrize(
    ("stale_component", "expected_reason"),
    [
        ("account", ResumeBlockReason.ACCOUNT_NOT_FRESH),
        ("broker_constraints", ResumeBlockReason.BROKER_CONSTRAINTS_NOT_FRESH),
    ],
)
def test_safe_resume_requires_fresh_state_and_resolved_reconciliation(
    stale_component, expected_reason, tmp_path
) -> None:
    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    resolved = reconcile_execution_state(ledger, _snapshot(), as_of=T0)
    events = broker_snapshot_runtime_events(_snapshot(), source_sequence_start=1)
    state = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    for event in events:
        state = reduce_state(state, event, now=event.available_at)
    safe = evaluate_resume_readiness(state, resolved, (), as_of=T0)
    stale_snapshot = _snapshot(stale_component=stale_component)
    stale_state = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    for event in broker_snapshot_runtime_events(stale_snapshot, source_sequence_start=1):
        stale_state = reduce_state(stale_state, event, now=event.available_at)
    stale = evaluate_resume_readiness(
        stale_state,
        reconcile_execution_state(
            ledger, stale_snapshot, as_of=T0, prior_report=resolved
        ),
        (),
        as_of=T0,
    )
    assert safe.status is ResumeStatus.SAFE
    assert stale.status is ResumeStatus.BLOCKED
    assert expected_reason in stale.reason_codes


def test_unresolved_anomaly_and_missing_continuity_block_resume(tmp_path) -> None:
    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    position = _position(ticket=888)
    report = reconcile_execution_state(ledger, _snapshot(positions=(position,)), as_of=T0)
    state = initial_runtime_state("XAUUSD", at=T0)
    blocked = evaluate_resume_readiness(
        state,
        report,
        (),
        as_of=T0,
        continuity_status=ContinuityStatus.MISSING_INTRABAR_DATA,
    )
    assert blocked.status is ResumeStatus.BLOCKED
    assert ResumeBlockReason.UNRESOLVED_EXECUTION_ANOMALY in blocked.reason_codes
    assert ResumeBlockReason.MISSING_INTRABAR_CONTINUITY in blocked.reason_codes


def test_expired_thesis_blocks_resume_without_mutating_or_reviving_it(tmp_path) -> None:
    @dataclass(frozen=True)
    class ThesisFixture:
        continuity_status: ContinuityStatus
        expires_at: datetime

    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    snapshot = _snapshot()
    report = reconcile_execution_state(ledger, snapshot, as_of=T0)
    state = initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1))
    for event in broker_snapshot_runtime_events(snapshot, source_sequence_start=1):
        state = reduce_state(state, event, now=event.available_at)
    thesis = ThesisFixture(ContinuityStatus.COMPLETE, T0 - timedelta(seconds=1))
    before = thesis
    readiness = evaluate_resume_readiness(state, report, (thesis,), as_of=T0)
    assert readiness.status is ResumeStatus.BLOCKED
    assert ResumeBlockReason.THESIS_EXPIRED in readiness.reason_codes
    assert thesis == before


def test_checkpoint_is_deterministic_anchor_but_transitions_recover_without_it(tmp_path) -> None:
    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    ledger.reserve(_intent())
    checkpoint = create_recovery_checkpoint(
        runtime_state=initial_runtime_state("XAUUSD", at=T0),
        reconciliation=None,
        readiness=None,
        thesis_state_ids=("thesis-state-1",),
        available_at=T0,
    )
    assert checkpoint == create_recovery_checkpoint(
        runtime_state=initial_runtime_state("XAUUSD", at=T0),
        reconciliation=None,
        readiness=None,
        thesis_state_ids=("thesis-state-1",),
        available_at=T0,
    )
    ledger.append_checkpoint(checkpoint)
    ledger.sync()
    assert SQLiteExecutionLedger(ledger.path).latest_checkpoint() == checkpoint
    assert SQLiteExecutionLedger(ledger.path).is_reserved(_intent().intent_id)


def test_graceful_shutdown_persists_checkpoint_and_flushes_both_ledgers(tmp_path) -> None:
    ledger = SQLiteExecutionLedger(tmp_path / "execution.sqlite3")
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    checkpoint = create_recovery_checkpoint(
        runtime_state=initial_runtime_state("XAUUSD", at=T0),
        reconciliation=None,
        readiness=None,
        thesis_state_ids=("thesis-state-1",),
        available_at=T0,
    )
    persist_graceful_shutdown(
        checkpoint, execution_ledger=ledger, runtime_journal=journal
    )
    assert SQLiteExecutionLedger(ledger.path).latest_checkpoint() == checkpoint


def test_recovery_contracts_reject_naive_timestamps() -> None:
    snapshot = _snapshot().model_dump()
    snapshot["available_at"] = datetime(2025, 1, 6, 12, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        BrokerRecoverySnapshot.model_validate(snapshot)
