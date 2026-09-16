from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from axq.execution_boundary import ExecutionIntent, ExecutionMode, ExecutionOrderType
from axq.runtime.journal import JournalRecord, JournalRecordType, SQLiteRuntimeJournal
from axq.runtime.shadow import (
    CandidateDirection,
    CandidateResult,
    M5CandidateScan,
    PlanFieldStatus,
    ScanReason,
    ShadowCycleStage,
    ShadowRuntimeCycle,
)
from axq.runtime.shadow_sink import JournalShadowExecutionSink, build_hypothetical_trade_plan
from axq.schemas import Signal
from axq.versioning import canonical_hash

T0 = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)

PRESERVED_INTERACTION_V1_PAYLOAD = {
    "as_of": "2026-09-14T11:30:00Z",
    "canonical_instrument": "XAUUSD",
    "cycle_id": "scycle-03d3c2acb8ab10687716",
    "discipline_outcome_id": None,
    "event_id": "ev-b24b98433525634f530f",
    "evidence_bundle_id": None,
    "execution_intent_id": None,
    "instrument_resolution_id": "rbi-37a1de1c2c819b71302d",
    "interaction_resolution_id": None,
    "m15_context_id": None,
    "master_proposal_id": None,
    "resolved_broker_symbol": "XAUUSD",
    "risk_outcome_id": None,
    "scan_id": "scan-eb72a17a67bb9259d2fd",
    "schema_version": "1.0",
    "shadow_execution_id": None,
    "stage": "QUIET",
    "trade_plan_id": None,
}
PRESERVED_INTERACTION_V1_RECORD = {
    "available_at": "2026-09-14T11:30:00Z",
    "event_id": "ev-b24b98433525634f530f",
    "event_time": None,
    "observed_at": None,
    "parent_id": None,
    "payload_json": json.dumps(
        PRESERVED_INTERACTION_V1_PAYLOAD,
        sort_keys=True,
        separators=(",", ":"),
    ),
    "previous_id": None,
    "record_id": "jr-c5d2689d8135cfef116d",
    "record_type": "SHADOW_RUNTIME_CYCLE",
    "schema_version": "1.0",
    "semantic_id": "scan-eb72a17a67bb9259d2fd",
    "semantic_schema_version": "1.0",
    "source": None,
}
PRESERVED_INTERACTION_V1_RECORD_JSON = json.dumps(
    PRESERVED_INTERACTION_V1_RECORD,
    sort_keys=True,
    separators=(",", ":"),
)


def insert_preserved_interaction_v1_record(path: Path) -> None:
    record = PRESERVED_INTERACTION_V1_RECORD
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO runtime_journal(
                record_id, record_type, semantic_id, event_id,
                parent_id, previous_id, available_at, record_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["record_id"],
                record["record_type"],
                record["semantic_id"],
                record["event_id"],
                record["parent_id"],
                record["previous_id"],
                record["available_at"],
                PRESERVED_INTERACTION_V1_RECORD_JSON,
            ),
        )


def _scan() -> M5CandidateScan:
    return M5CandidateScan(
        event_id="ev-shadow",
        feature_snapshot_id="fs-shadow",
        m15_context_id="m15ctx-shadow",
        symbol="XAUUSD",
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        as_of=T0,
        available_at=T0,
        result=CandidateResult.CANDIDATE,
        direction=CandidateDirection.BULLISH,
        reason_codes=(
            ScanReason.M5_BULLISH_QUANT_ACTIVATION,
            ScanReason.M15_CONTEXT_SUPPORTS,
        ),
    )


def _intent() -> ExecutionIntent:
    return ExecutionIntent(
        evidence_bundle_id="eb-shadow",
        master_proposal_id="mp-shadow",
        discipline_outcome_id="do-shadow",
        risk_outcome_id="ro-shadow",
        risk_context_id="rc-shadow",
        setup_id="setup-shadow",
        thesis_id="thesis-shadow",
        scenario_id="scenario-shadow",
        symbol="XAUUSD",
        broker_symbol="XAUUSD.sc",
        broker_source="mt5",
        point_size=0.01,
        direction=Signal.BUY,
        approved_volume_lots=0.05,
        order_type=ExecutionOrderType.MARKET,
        requested_entry_price=2500.2,
        stop_loss_price=2490.2,
        as_of=T0,
        available_at=T0,
        expires_at=T0 + timedelta(seconds=30),
        execution_policy_id="ep-shadow",
        execution_policy_version="shadow-v1",
        execution_mode=ExecutionMode.DRY_RUN,
    )


def test_quiet_cycle_contains_no_agent_or_trade_references() -> None:
    scan = M5CandidateScan(
        event_id="ev-quiet",
        feature_snapshot_id="fs-quiet",
        m15_context_id="m15ctx-quiet",
        symbol="XAUUSD",
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-shadow",
        as_of=T0,
        available_at=T0,
        result=CandidateResult.NO_SETUP,
        reason_codes=(
            ScanReason.NO_DIRECTIONAL_ACTIVATION,
            ScanReason.M15_CONTEXT_NEUTRAL,
        ),
    )

    cycle = ShadowRuntimeCycle.from_scan(scan)

    assert cycle.stage is ShadowCycleStage.QUIET
    assert cycle.evidence_bundle_id is None
    assert cycle.master_proposal_id is None
    assert cycle.trade_plan_id is None
    assert cycle.schema_version == "2.0"


def test_legacy_v1_shadow_cycle_decodes_without_rewriting_identity() -> None:
    identity = {
        "schema_version": "1.0",
        "event_id": "ev-legacy",
        "scan_id": "scan-legacy",
        "m15_context_id": None,
        "canonical_instrument": "XAUUSD",
        "resolved_broker_symbol": "XAUUSD.sc",
        "instrument_resolution_id": "rbi-legacy",
        "stage": "QUIET",
        "as_of": T0.isoformat().replace("+00:00", "Z"),
        "evidence_bundle_id": None,
        "master_proposal_id": None,
        "discipline_outcome_id": None,
        "risk_outcome_id": None,
        "execution_intent_id": None,
        "trade_plan_id": None,
        "shadow_execution_id": None,
    }
    cycle_id = f"scycle-{canonical_hash(identity)[:20]}"
    payload = {"cycle_id": cycle_id, **identity}
    record = JournalRecord(
        record_type=JournalRecordType.SHADOW_RUNTIME_CYCLE,
        semantic_id="scan-legacy",
        event_id="ev-legacy",
        available_at=T0,
        semantic_schema_version="1.0",
        payload_json=json.dumps(payload, sort_keys=True, separators=(",", ":")),
    )

    decoded = record.decode()

    decoded_payload = decoded.model_dump()
    assert decoded_payload["cycle_id"] == cycle_id
    assert decoded_payload["schema_version"] == "1.0"
    assert record.semantic_id == "scan-legacy"


def test_preserved_interaction_bearing_v1_cycle_decodes_exact_identity() -> None:
    record = JournalRecord.model_validate_json(PRESERVED_INTERACTION_V1_RECORD_JSON)

    decoded = record.decode()

    assert record.record_id == "jr-c5d2689d8135cfef116d"
    assert decoded.cycle_id == "scycle-03d3c2acb8ab10687716"
    assert decoded.model_dump()["interaction_resolution_id"] is None


def test_corrupt_interaction_bearing_v1_cycle_still_rejects_extra_fields() -> None:
    corrupt = dict(PRESERVED_INTERACTION_V1_RECORD)
    payload = dict(PRESERVED_INTERACTION_V1_PAYLOAD)
    payload["unexpected_field"] = "must-fail"
    corrupt["payload_json"] = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    with pytest.raises(ValueError, match="unexpected_field"):
        JournalRecord.model_validate(corrupt)


def test_unknown_shadow_cycle_schema_version_fails_closed() -> None:
    payload = {
        "schema_version": "9.9",
        "cycle_id": "scycle-unknown",
        "event_id": "ev-unknown",
        "scan_id": "scan-unknown",
        "canonical_instrument": "XAUUSD",
        "resolved_broker_symbol": "XAUUSD.sc",
        "instrument_resolution_id": "rbi-unknown",
        "stage": "QUIET",
        "as_of": T0.isoformat().replace("+00:00", "Z"),
    }

    try:
        JournalRecord(
            record_type=JournalRecordType.SHADOW_RUNTIME_CYCLE,
            semantic_id="scycle-unknown",
            event_id="ev-unknown",
            available_at=T0,
            semantic_schema_version="9.9",
            payload_json=json.dumps(payload),
        )
    except ValueError as error:
        assert "unsupported journal semantic schema version" in str(error)
    else:
        raise AssertionError("unknown semantic versions must fail closed")


def test_mixed_v1_v2_shadow_cycles_decode_in_append_order(tmp_path) -> None:
    legacy_record = JournalRecord.model_validate_json(PRESERVED_INTERACTION_V1_RECORD_JSON)
    current_cycle = ShadowRuntimeCycle(
        event_id="ev-current-mixed",
        scan_id="scan-current-mixed",
        canonical_instrument="XAUUSD",
        resolved_broker_symbol="XAUUSD.sc",
        instrument_resolution_id="rbi-current",
        stage=ShadowCycleStage.QUIET,
        as_of=T0 + timedelta(minutes=5),
    )
    journal = SQLiteRuntimeJournal(tmp_path / "mixed-shadow.sqlite3")
    journal.append(legacy_record)
    journal.append_semantic(current_cycle, event_id=current_cycle.event_id)

    first_read = tuple(entry.record.decode() for entry in journal.records())
    second_read = tuple(entry.record.decode() for entry in journal.records())

    assert tuple(item.schema_version for item in first_read) == ("1.0", "2.0")
    assert tuple(item.model_dump_json() for item in first_read) == tuple(
        item.model_dump_json() for item in second_read
    )


def test_shadow_sink_records_plan_once_without_broker_fields(tmp_path) -> None:
    scan = _scan()
    intent = _intent()
    plan = build_hypothetical_trade_plan(
        scan=scan,
        intent=intent,
        master_confidence=0.72,
    )
    journal = SQLiteRuntimeJournal(tmp_path / "shadow.sqlite3")
    sink = JournalShadowExecutionSink(journal)

    first = sink.record(plan)
    second = sink.record(plan)

    assert first == second
    assert first.broker_mutation is False
    assert plan.canonical_instrument == "XAUUSD"
    assert plan.resolved_broker_symbol == "XAUUSD.sc"
    assert first.resolved_broker_symbol == "XAUUSD.sc"
    assert plan.entry.status is PlanFieldStatus.AVAILABLE
    assert plan.stop_loss.status is PlanFieldStatus.AVAILABLE
    assert plan.position_size.status is PlanFieldStatus.AVAILABLE
    assert plan.take_profit.status is PlanFieldStatus.UNAVAILABLE
    assert plan.risk_reward.status is PlanFieldStatus.UNAVAILABLE
    assert [item.record.record_type for item in journal.records()] == [
        JournalRecordType.HYPOTHETICAL_TRADE_PLAN,
        JournalRecordType.SHADOW_EXECUTION,
    ]
