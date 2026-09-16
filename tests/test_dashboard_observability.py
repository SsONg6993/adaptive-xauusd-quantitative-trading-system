"""Focused read-only observability projections for the Shadow Runtime dashboard."""

from __future__ import annotations

import inspect
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

from axq.agents import DirectionalBias
from axq.dashboard import readers
from axq.dashboard.contracts import ComponentState
from axq.dashboard.readers import load_runtime_observability
from axq.dashboard.views import activity_rows, current_cycle_rows
from axq.discipline import DisciplineResult
from axq.execution_boundary import (
    ReconciliationReport,
    RecoveryCheckpoint,
    ResolutionStatus,
    ResumeBlockReason,
    ResumeReadiness,
    ResumeStatus,
)
from axq.master import default_fusion_policy, fuse_evidence
from axq.risk_boundary import RiskOutcome, RiskReason, RiskResult
from axq.runtime.journal import SQLiteRuntimeJournal
from axq.runtime.shadow import (
    CandidateResult,
    LiveMarketStatus,
    M5CandidateScan,
    ScanReason,
    ShadowCycleStage,
    ShadowMarketAvailability,
    ShadowRuntimeCycle,
)
from axq.schemas import Signal
from tests.test_master_fusion import _bundle, _evidence
from tests.test_shadow_runtime import T0, _event


def _quiet_journal(path: Path) -> SQLiteRuntimeJournal:
    event = _event()
    scan = M5CandidateScan(
        event_id=event.event_id,
        symbol="XAUUSD",
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-observability",
        as_of=T0,
        available_at=T0,
        result=CandidateResult.OUTSIDE_WINDOW,
        reason_codes=(ScanReason.OUTSIDE_ACTIVE_WINDOW,),
    )
    cycle = ShadowRuntimeCycle.from_scan(scan)
    availability = ShadowMarketAvailability(
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-observability",
        observed_at=T0,
        available_at=T0,
        broker_tick_at=T0,
        status=LiveMarketStatus.BAR_READY,
        reason_code="BAR_READY",
    )
    readiness = ResumeReadiness(
        runtime_state_id="state-observability",
        reconciliation_report_id="report-observability",
        as_of=T0,
        status=ResumeStatus.SAFE,
        reason_codes=(),
    )
    journal = SQLiteRuntimeJournal(path)
    journal.append_semantic(readiness, event_id=None)
    journal.append_semantic(availability, event_id=None)
    journal.append_semantic(event, event_id=event.event_id)
    journal.append_semantic(scan, event_id=event.event_id)
    journal.append_semantic(cycle, event_id=event.event_id)
    return journal


def test_current_cycle_is_event_anchored_and_rendered_from_persisted_evidence(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    _quiet_journal(path)

    snapshot = load_runtime_observability(path)

    assert snapshot.component.state is ComponentState.AVAILABLE
    assert snapshot.current_cycle is not None
    assert snapshot.current_cycle.symbol == "XAUUSD"
    assert snapshot.current_cycle.completed_m5_timestamp == T0.isoformat()
    assert snapshot.current_cycle.trading_window_state == "Outside active window"
    assert snapshot.current_cycle.scanner_result == "Outside Window"
    assert snapshot.current_cycle.agents_invoked == ()
    assert snapshot.current_cycle.evidence_status == "Not required"
    assert snapshot.current_cycle.final_action == "NO ACTION"
    assert snapshot.current_cycle.execution_authorization == "Not required"
    rows = current_cycle_rows(snapshot.current_cycle)
    assert {row["Field"]: row["Value"] for row in rows}["Completed M5"].endswith("MYT")
    assert {row["Field"]: row["Value"] for row in rows}["Execution"] == "Not required"


def test_recent_activity_is_bounded_meaningful_and_chronological(tmp_path: Path) -> None:
    path = tmp_path / "runtime.sqlite3"
    _quiet_journal(path)

    snapshot = load_runtime_observability(path, activity_limit=3)

    assert len(snapshot.recent_activity) == 3
    assert tuple(item.journal_sequence for item in snapshot.recent_activity) == tuple(
        sorted(item.journal_sequence for item in snapshot.recent_activity)
    )
    assert snapshot.recent_activity[-1].label == "Cycle persisted"
    assert any(item.label == "New completed M5 accepted" for item in snapshot.recent_activity)
    assert activity_rows(snapshot.recent_activity)[-1]["Time"].endswith("MYT")


def test_repeated_waiting_states_collapse_and_keep_canonical_m5_detail(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    journal = _quiet_journal(path)
    for seconds in (1, 3, 5, 7):
        at = T0 + timedelta(seconds=seconds)
        journal.append_semantic(
            ShadowMarketAvailability(
                resolved_broker_symbol="XAUUSD.sc",
                instrument_resolution_id="rbi-observability",
                observed_at=at,
                available_at=at,
                broker_tick_at=T0,
                status=LiveMarketStatus.WAITING_FOR_NEXT_M5,
                reason_code="WAITING_FOR_NEXT_COMPLETED_M5",
            ),
            event_id=None,
        )

    snapshot = load_runtime_observability(path, activity_limit=50)
    waiting = [
        item for item in snapshot.recent_activity if item.label == "Waiting For Next M5"
    ]

    assert len(waiting) == 1
    assert waiting[0].detail == "last completed=2026-09-14 20:00 MYT"


def test_periodic_readiness_and_reconciliation_only_show_semantic_changes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    journal = _quiet_journal(path)
    reports: list[ReconciliationReport] = []
    for seconds in (1, 2, 3):
        at = T0 + timedelta(seconds=seconds)
        report = ReconciliationReport(
            snapshot_id=f"snapshot-{seconds}",
            as_of=at,
            available_at=at,
            status=ResolutionStatus.RESOLVED,
            findings=(),
        )
        reports.append(report)
        journal.append_semantic(report, event_id=None)
        journal.append_semantic(
            ResumeReadiness(
                runtime_state_id=f"state-{seconds}",
                reconciliation_report_id=report.report_id,
                as_of=at,
                status=ResumeStatus.SAFE,
                reason_codes=(),
            ),
            event_id=None,
        )

    blocked_at = T0 + timedelta(seconds=4)
    journal.append_semantic(
        ResumeReadiness(
            runtime_state_id="state-blocked-transition",
            reconciliation_report_id=reports[-1].report_id,
            as_of=blocked_at,
            status=ResumeStatus.BLOCKED,
            reason_codes=(ResumeBlockReason.RECONCILIATION_INCOMPLETE,),
        ),
        event_id=None,
    )
    safe_at = T0 + timedelta(seconds=5)
    journal.append_semantic(
        ResumeReadiness(
            runtime_state_id="state-safe-transition",
            reconciliation_report_id=reports[-1].report_id,
            as_of=safe_at,
            status=ResumeStatus.SAFE,
            reason_codes=(),
        ),
        event_id=None,
    )

    snapshot = load_runtime_observability(path, activity_limit=50)
    reconciliation = [
        item
        for item in snapshot.recent_activity
        if item.label == "Broker reconciliation RESOLVED"
    ]
    readiness = [
        item for item in snapshot.recent_activity if item.label.startswith("Runtime readiness")
    ]

    assert len(reconciliation) == 1
    assert reconciliation[0].detail == "no unresolved findings"
    assert [item.label for item in readiness] == [
        "Runtime readiness SAFE",
        "Runtime readiness BLOCKED",
        "Runtime readiness SAFE",
    ]
    assert readiness[1].reason_codes == ("RECONCILIATION_INCOMPLETE",)
    assert all("Startup recovery" not in item.label for item in readiness)


def test_first_readiness_after_recovery_checkpoint_is_real_startup_recovery(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    journal = _quiet_journal(path)
    checkpoint_at = T0 + timedelta(seconds=1)
    checkpoint = RecoveryCheckpoint(
        runtime_state_id="state-before-restart",
        source_cursors=(),
        reconciliation_report_id="report-before-restart",
        readiness_id="ready-before-restart",
        thesis_state_ids=(),
        available_at=checkpoint_at,
    )
    journal.append_semantic(checkpoint, event_id=None)
    startup_at = T0 + timedelta(seconds=2)
    journal.append_semantic(
        ResumeReadiness(
            runtime_state_id="state-after-restart",
            reconciliation_report_id="report-after-restart",
            as_of=startup_at,
            status=ResumeStatus.SAFE,
            reason_codes=(),
        ),
        event_id=None,
    )
    periodic_at = T0 + timedelta(seconds=3)
    journal.append_semantic(
        ResumeReadiness(
            runtime_state_id="state-periodic",
            reconciliation_report_id="report-periodic",
            as_of=periodic_at,
            status=ResumeStatus.SAFE,
            reason_codes=(),
        ),
        event_id=None,
    )

    snapshot = load_runtime_observability(path, activity_limit=50)

    assert sum(
        item.label == "Graceful stop checkpoint persisted"
        for item in snapshot.recent_activity
    ) == 1
    assert sum(
        item.label == "Startup recovery SAFE" for item in snapshot.recent_activity
    ) == 1
    assert sum(
        item.label == "Runtime readiness SAFE" for item in snapshot.recent_activity
    ) == 1


def test_activity_details_and_raw_technical_fields_come_from_canonical_records(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    _quiet_journal(path)

    snapshot = load_runtime_observability(path, activity_limit=50)
    m5 = next(
        item for item in snapshot.recent_activity if item.label == "New completed M5 accepted"
    )
    scan = next(
        item for item in snapshot.recent_activity if item.label == "M5 scanner: Outside Window"
    )
    cycle = next(item for item in snapshot.recent_activity if item.label == "Cycle persisted")

    assert m5.detail == "2026-09-14 20:00 MYT · seq=1"
    assert scan.detail == "trading window closed"
    assert scan.reason_codes == ("OUTSIDE_ACTIVE_WINDOW",)
    assert cycle.cycle_id is not None
    assert cycle.raw_persisted_timestamp == cycle.occurred_at


def test_hold_explanation_and_pipeline_use_exact_cycle_links(tmp_path: Path) -> None:
    path = tmp_path / "runtime.sqlite3"
    bundle = _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH, confidence=0.65),
            "quant": _evidence("quant", DirectionalBias.BEARISH, confidence=0.65),
        }
    )
    proposal = fuse_evidence(bundle, default_fusion_policy())
    assert proposal.decision.value == "HOLD"
    scan = M5CandidateScan(
        event_id=bundle.event_id,
        feature_snapshot_id="fs-observability",
        symbol="XAUUSD",
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-observability",
        as_of=T0,
        available_at=T0,
        result=CandidateResult.CANDIDATE,
        direction="BULLISH",
        reason_codes=(ScanReason.M5_BULLISH_QUANT_ACTIVATION,),
    )
    cycle = ShadowRuntimeCycle(
        event_id=bundle.event_id,
        scan_id=scan.scan_id,
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-observability",
        stage=ShadowCycleStage.HOLD,
        as_of=T0,
        evidence_bundle_id=bundle.bundle_id,
        master_proposal_id=proposal.proposal_id,
    )
    journal = SQLiteRuntimeJournal(path)
    for record in (scan, bundle, proposal, cycle):
        journal.append_semantic(record, event_id=bundle.event_id)

    snapshot = load_runtime_observability(path)

    assert snapshot.current_cycle is not None
    assert snapshot.current_cycle.master_decision == "HOLD"
    assert snapshot.current_cycle.evidence_status == "Created"
    assert snapshot.current_cycle.agents_invoked
    assert snapshot.decision_explanation is not None
    assert snapshot.decision_explanation.title == "WHY HOLD"
    assert snapshot.decision_explanation.result == "HOLD"
    assert any(point.startswith("✗ ") for point in snapshot.decision_explanation.points)
    stages = {stage.stage: stage.status for stage in snapshot.pipeline}
    assert stages["Agents"] == "COMPLETE"
    assert stages["Master"] == "HOLD"
    assert stages["Execution"] == "NOT REQUIRED"


def test_blocked_recovery_overrides_cycle_explanation_with_persisted_reason(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    journal = _quiet_journal(path)
    blocked = ResumeReadiness(
        runtime_state_id="state-blocked",
        reconciliation_report_id="report-blocked",
        as_of=T0,
        status=ResumeStatus.BLOCKED,
        reason_codes=(ResumeBlockReason.RECONCILIATION_INCOMPLETE,),
    )
    journal.append_semantic(blocked, event_id=None)

    snapshot = load_runtime_observability(path)

    assert snapshot.decision_explanation is not None
    assert snapshot.decision_explanation.title == "WHY BLOCKED"
    assert snapshot.decision_explanation.result == "No event decision permitted"
    assert snapshot.decision_explanation.points == ("✗ Reconciliation Incomplete",)
    assert {stage.stage: stage.status for stage in snapshot.pipeline}["Runtime State"] == (
        "BLOCKED"
    )
    assert {stage.stage: stage.status for stage in snapshot.pipeline}["Execution"] == "BLOCKED"


def test_risk_veto_is_explained_and_cannot_appear_as_final_action(tmp_path: Path) -> None:
    path = tmp_path / "runtime.sqlite3"
    bundle = _bundle(
        {
            "chart": _evidence("chart", DirectionalBias.BULLISH, confidence=0.90),
            "quant": _evidence("quant", DirectionalBias.BULLISH, confidence=0.85),
        }
    )
    proposal = fuse_evidence(bundle, default_fusion_policy())
    assert proposal.decision is Signal.BUY
    scan = M5CandidateScan(
        event_id=bundle.event_id,
        feature_snapshot_id="fs-risk-veto",
        symbol="XAUUSD",
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-observability",
        as_of=T0,
        available_at=T0,
        result=CandidateResult.CANDIDATE,
        direction="BULLISH",
        reason_codes=(ScanReason.M5_BULLISH_QUANT_ACTIVATION,),
    )
    risk = RiskOutcome(
        master_proposal_id=proposal.proposal_id,
        evidence_bundle_id=bundle.bundle_id,
        discipline_outcome_id="discipline-risk-veto",
        discipline_result=DisciplineResult.PASS,
        risk_policy_id="risk-policy-observability",
        risk_policy_version="1.0",
        risk_context_id="risk-context-observability",
        symbol="XAUUSD",
        as_of=T0,
        available_at=T0,
        master_decision=Signal.BUY,
        result=RiskResult.REJECT,
        eligible_for_execution=False,
        reason_codes=(RiskReason.MARKET_NOT_FRESH,),
        risk_fraction=0.01,
        rationale="Persisted market freshness veto.",
    )
    cycle = ShadowRuntimeCycle(
        event_id=bundle.event_id,
        scan_id=scan.scan_id,
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-observability",
        stage=ShadowCycleStage.HOLD,
        as_of=T0,
        evidence_bundle_id=bundle.bundle_id,
        master_proposal_id=proposal.proposal_id,
        risk_outcome_id=risk.outcome_id,
    )
    journal = SQLiteRuntimeJournal(path)
    for record in (scan, bundle, proposal, risk, cycle):
        journal.append_semantic(record, event_id=bundle.event_id)

    snapshot = load_runtime_observability(path)

    assert snapshot.current_cycle is not None
    assert snapshot.current_cycle.risk_outcome == "Reject"
    assert snapshot.current_cycle.final_action == "NO ACTION"
    assert snapshot.current_cycle.execution_authorization == "Not authorized — Risk veto"
    assert snapshot.decision_explanation is not None
    assert "✗ Risk: Market Not Fresh" in snapshot.decision_explanation.points


def test_missing_data_is_explicit_and_reader_never_mutates_runtime_database(
    tmp_path: Path,
) -> None:
    missing = load_runtime_observability(tmp_path / "missing.sqlite3")
    assert missing.component.state is ComponentState.UNAVAILABLE
    assert missing.current_cycle is None

    path = tmp_path / "runtime.sqlite3"
    _quiet_journal(path)
    before = sha256(path.read_bytes()).hexdigest()
    first = load_runtime_observability(path)
    second = load_runtime_observability(path)

    assert first == second
    assert sha256(path.read_bytes()).hexdigest() == before


def test_observability_queries_are_explicitly_bounded_and_do_not_invoke_services() -> None:
    event_source = inspect.getsource(readers._bounded_event_records)
    activity_source = inspect.getsource(readers._recent_observability_records)
    loader_source = inspect.getsource(load_runtime_observability)

    assert "LIMIT ?" in event_source
    assert "LIMIT ?" in activity_source
    assert "OllamaHTTPTransport" not in loader_source
    assert "read_live_mt5_snapshot" not in loader_source
    assert "process_event" not in loader_source
