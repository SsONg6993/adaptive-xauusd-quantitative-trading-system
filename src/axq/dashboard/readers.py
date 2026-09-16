"""Explicit-path, read-only readers for persisted AXQ artifacts."""

from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol, cast
from zoneinfo import ZoneInfo

from axq.agents import AgentEvidence, ScenarioState, ThesisState
from axq.dashboard.contracts import (
    ComponentState,
    ComponentStatus,
    CurrentCycleView,
    DecisionExplanationView,
    PerformanceSnapshot,
    PipelineStageView,
    ReasoningAttemptView,
    ReasoningSnapshot,
    RuntimeActivityView,
    RuntimeComputeSnapshot,
    RuntimeObservabilitySnapshot,
    RuntimeSnapshot,
)
from axq.discipline.contracts import DisciplineOutcome
from axq.execution_boundary import (
    ReconciliationReport,
    RecoveryCheckpoint,
    ResumeReadiness,
    ResumeStatus,
)
from axq.execution_boundary.contracts import ExecutionIntent
from axq.interaction.contracts import (
    MasterConflictAssessment,
    SpecialistInteractionImpact,
    SpecialistInteractionResolution,
    SpecialistInteractionRound,
    SpecialistInteractionTurn,
)
from axq.master.contracts import MasterProposal
from axq.mt5.symbols import ResolvedBrokerInstrument
from axq.reasoning.contracts import (
    LLMExecutionAttemptAudit,
    LLMRequestEnvelope,
    LLMStructuredResponseArtifact,
)
from axq.reasoning.ollama import (
    OllamaHTTPTransport,
    validate_loopback_ollama_url,
)
from axq.risk_boundary.contracts import RiskOutcome
from axq.runtime import RuntimeEvent, RuntimeEventType
from axq.runtime.journal import (
    DecodedShadowRuntimeCycle,
    JournalOutcome,
    JournalOutcomeStatus,
    JournalRecord,
    JournalRecordType,
)
from axq.runtime.kernel import BROKER_REFRESH_EVENT_TYPES, EvidenceBundle
from axq.runtime.shadow import (
    CandidateResult,
    HypotheticalTradePlan,
    LiveMarketStatus,
    M5CandidateScan,
    M15ContextSnapshot,
    ScanReason,
    ShadowCycleStage,
    ShadowExecutionRecord,
    ShadowMarketAvailability,
)
from axq.runtime.state import SharedRuntimeState

_MAX_JSON_BYTES = 32 * 1024 * 1024
_OLLAMA_RESPONSE_LIMIT = 1024 * 1024
_NOT_AVAILABLE = "Not available"
_MAX_CYCLE_RECORDS = 256
_MAX_ACTIVITY_SCAN = 1_200
_MALAYSIA = ZoneInfo("Asia/Kuala_Lumpur")


class StatusTransport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        payload: object,
        timeout_seconds: float,
        response_byte_limit: int,
    ) -> bytes: ...


def _not_configured(component: str) -> ComponentStatus:
    return ComponentStatus(
        component=component,
        state=ComponentState.NOT_CONFIGURED,
        detail="Not available yet — no explicit path or endpoint was configured.",
    )


def _unavailable(component: str, path: Path) -> ComponentStatus:
    return ComponentStatus(
        component=component,
        state=ComponentState.UNAVAILABLE,
        detail="Not available yet — the configured source does not exist.",
        source_path=str(path),
    )


def _error(component: str, detail: str, path: Path | None = None) -> ComponentStatus:
    return ComponentStatus(
        component=component,
        state=ComponentState.ERROR,
        detail=detail,
        source_path=None if path is None else str(path),
    )


@contextmanager
def _readonly_connection(path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        yield connection
    finally:
        connection.close()


def _has_table(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def load_reasoning_snapshot(
    path: str | Path | None,
    *,
    limit: int = 10,
) -> ReasoningSnapshot:
    """Load recent Task 1 attempts without initializing its writable store."""

    if limit < 1 or limit > 100:
        raise ValueError("reasoning attempt limit must be between 1 and 100")
    if path is None or not str(path).strip():
        return ReasoningSnapshot(component=_not_configured("Reasoning"))
    source = Path(path)
    if not source.is_file():
        return ReasoningSnapshot(component=_unavailable("Reasoning", source))
    try:
        with _readonly_connection(source) as connection:
            required = {
                "llm_reasoning_requests",
                "llm_reasoning_responses",
                "llm_reasoning_attempts",
            }
            if not all(_has_table(connection, table) for table in required):
                return ReasoningSnapshot(
                    component=_error(
                        "Reasoning",
                        "Configured database has no reasoning schema.",
                        source,
                    )
                )
            rows = connection.execute(
                "SELECT record_json FROM llm_reasoning_attempts "
                "ORDER BY attempt_sequence DESC LIMIT ?",
                (limit,),
            ).fetchall()
            views: list[ReasoningAttemptView] = []
            for row in rows:
                attempt = LLMExecutionAttemptAudit.model_validate_json(str(row["record_json"]))
                request_row = connection.execute(
                    "SELECT record_json FROM llm_reasoning_requests WHERE request_id = ?",
                    (attempt.request_id,),
                ).fetchone()
                if request_row is None:
                    raise ValueError("reasoning attempt has no exact request")
                request = LLMRequestEnvelope.model_validate_json(str(request_row["record_json"]))
                response = None
                if attempt.response_id is not None:
                    response_row = connection.execute(
                        "SELECT record_json FROM llm_reasoning_responses WHERE response_id = ?",
                        (attempt.response_id,),
                    ).fetchone()
                    if response_row is None:
                        raise ValueError("reasoning attempt has no exact response")
                    response = LLMStructuredResponseArtifact.model_validate_json(
                        str(response_row["record_json"])
                    )
                    if response.request_id != request.request_id:
                        raise ValueError("reasoning response/request linkage is invalid")
                views.append(
                    ReasoningAttemptView(attempt=attempt, request=request, response=response)
                )
        count = len(views)
        detail = f"{count} reasoning attempt{'s' if count != 1 else ''} available"
        return ReasoningSnapshot(
            component=ComponentStatus(
                component="Reasoning",
                state=ComponentState.AVAILABLE,
                detail=detail,
                source_path=str(source),
                as_of=None if not views else views[0].attempt.completed_at.isoformat(),
            ),
            attempts=tuple(views),
        )
    except (OSError, sqlite3.Error, ValueError) as error:
        return ReasoningSnapshot(
            component=_error("Reasoning", f"Unable to read reasoning audit: {error}", source)
        )


def _latest_journal_record(
    connection: sqlite3.Connection,
    record_type: JournalRecordType,
) -> JournalRecord | None:
    row = connection.execute(
        "SELECT record_json FROM runtime_journal WHERE record_type = ? "
        "ORDER BY journal_sequence DESC LIMIT 1",
        (record_type.value,),
    ).fetchone()
    return None if row is None else JournalRecord.model_validate_json(str(row["record_json"]))


def _journal_record_for_event(
    connection: sqlite3.Connection,
    record_type: JournalRecordType,
    event_id: str,
) -> JournalRecord | None:
    row = connection.execute(
        "SELECT record_json FROM runtime_journal "
        "WHERE record_type = ? AND event_id = ? "
        "ORDER BY journal_sequence DESC LIMIT 1",
        (record_type.value, event_id),
    ).fetchone()
    return None if row is None else JournalRecord.model_validate_json(str(row["record_json"]))


def _journal_records_for_event(
    connection: sqlite3.Connection,
    record_type: JournalRecordType,
    event_id: str,
) -> tuple[JournalRecord, ...]:
    rows = connection.execute(
        "SELECT record_json FROM runtime_journal "
        "WHERE record_type = ? AND event_id = ? ORDER BY journal_sequence",
        (record_type.value, event_id),
    ).fetchall()
    return tuple(JournalRecord.model_validate_json(str(row["record_json"])) for row in rows)


def load_runtime_snapshot(
    path: str | Path | None,
    *,
    now: datetime | None = None,
    stale_after: timedelta = timedelta(minutes=5),
) -> RuntimeSnapshot:
    """Load the latest canonical runtime records from an explicit journal path."""

    if path is None or not str(path).strip():
        return RuntimeSnapshot(component=_not_configured("Runtime / MT5"))
    source = Path(path)
    if not source.is_file():
        return RuntimeSnapshot(component=_unavailable("Runtime / MT5", source))
    try:
        with _readonly_connection(source) as connection:
            if not _has_table(connection, "runtime_journal"):
                return RuntimeSnapshot(
                    component=_error(
                        "Runtime / MT5",
                        "Configured database has no runtime journal.",
                        source,
                    )
                )
            records = {
                kind: _latest_journal_record(connection, kind)
                for kind in (
                    JournalRecordType.RUNTIME_STATE,
                    JournalRecordType.MASTER_PROPOSAL,
                    JournalRecordType.DISCIPLINE_OUTCOME,
                    JournalRecordType.RISK_OUTCOME,
                    JournalRecordType.EXECUTION_INTENT,
                    JournalRecordType.M15_CONTEXT,
                    JournalRecordType.M5_CANDIDATE_SCAN,
                    JournalRecordType.SHADOW_RUNTIME_CYCLE,
                    JournalRecordType.HYPOTHETICAL_TRADE_PLAN,
                    JournalRecordType.INSTRUMENT_RESOLUTION,
                    JournalRecordType.SHADOW_MARKET_AVAILABILITY,
                )
            }
            master_record = records[JournalRecordType.MASTER_PROPOSAL]
            master = None if master_record is None else cast(MasterProposal, master_record.decode())
            evidence_record = (
                None
                if master is None
                else _journal_record_for_event(
                    connection,
                    JournalRecordType.EVIDENCE_BUNDLE,
                    master.event_id,
                )
            )
            assessment = None
            interaction_round = None
            interaction_turns: tuple[SpecialistInteractionTurn, ...] = ()
            interaction_resolution = None
            interaction_impact = None
            if master is not None:
                assessment_records = _journal_records_for_event(
                    connection,
                    JournalRecordType.MASTER_CONFLICT_ASSESSMENT,
                    master.event_id,
                )
                assessments = tuple(
                    cast(MasterConflictAssessment, item.decode())
                    for item in assessment_records
                )
                assessment = next(
                    (
                        item
                        for item in reversed(assessments)
                        if item.master_proposal_id == master.proposal_id
                    ),
                    None,
                )
                if assessment is not None and assessment.interaction_required:
                    round_records = _journal_records_for_event(
                        connection,
                        JournalRecordType.SPECIALIST_INTERACTION_ROUND,
                        master.event_id,
                    )
                    interaction_round = next(
                        (
                            cast(SpecialistInteractionRound, item.decode())
                            for item in reversed(round_records)
                            if cast(SpecialistInteractionRound, item.decode()).assessment_id
                            == assessment.assessment_id
                        ),
                        None,
                    )
                    if interaction_round is not None:
                        turn_records = _journal_records_for_event(
                            connection,
                            JournalRecordType.SPECIALIST_INTERACTION_TURN,
                            master.event_id,
                        )
                        interaction_turns = tuple(
                            sorted(
                                (
                                    cast(SpecialistInteractionTurn, item.decode())
                                    for item in turn_records
                                    if cast(SpecialistInteractionTurn, item.decode()).round_id
                                    == interaction_round.round_id
                                ),
                                key=lambda item: item.turn_index,
                            )
                        )
                        resolution_records = _journal_records_for_event(
                            connection,
                            JournalRecordType.SPECIALIST_INTERACTION_RESOLUTION,
                            master.event_id,
                        )
                        interaction_resolution = next(
                            (
                                cast(SpecialistInteractionResolution, item.decode())
                                for item in reversed(resolution_records)
                                if cast(
                                    SpecialistInteractionResolution, item.decode()
                                ).round_id
                                == interaction_round.round_id
                            ),
                            None,
                        )
                        if interaction_resolution is not None:
                            impact_records = _journal_records_for_event(
                                connection,
                                JournalRecordType.SPECIALIST_INTERACTION_IMPACT,
                                master.event_id,
                            )
                            interaction_impact = next(
                                (
                                    cast(SpecialistInteractionImpact, item.decode())
                                    for item in reversed(impact_records)
                                    if cast(
                                        SpecialistInteractionImpact, item.decode()
                                    ).resolution_id
                                    == interaction_resolution.resolution_id
                                ),
                                None,
                            )
        state_record = records[JournalRecordType.RUNTIME_STATE]
        state = None if state_record is None else cast(SharedRuntimeState, state_record.decode())
        latest_available = max(
            (item.available_at for item in records.values() if item is not None),
            default=None,
        )
        if latest_available is None:
            component_state = ComponentState.AVAILABLE
            detail = "Runtime journal is readable, but current state is not available yet."
        else:
            current = now or datetime.now(UTC)
            if current.tzinfo is None or current.utcoffset() is None:
                raise ValueError("runtime dashboard clock must be timezone-aware")
            if current.astimezone(UTC) - latest_available.astimezone(UTC) > stale_after:
                component_state = ComponentState.STALE
                detail = "Persisted runtime data is available but stale."
            else:
                component_state = ComponentState.ONLINE
                detail = "Persisted runtime data is current."
        discipline_record = records[JournalRecordType.DISCIPLINE_OUTCOME]
        risk_record = records[JournalRecordType.RISK_OUTCOME]
        intent_record = records[JournalRecordType.EXECUTION_INTENT]
        context_record = records[JournalRecordType.M15_CONTEXT]
        scan_record = records[JournalRecordType.M5_CANDIDATE_SCAN]
        shadow_cycle_record = records[JournalRecordType.SHADOW_RUNTIME_CYCLE]
        trade_plan_record = records[JournalRecordType.HYPOTHETICAL_TRADE_PLAN]
        resolution_record = records[JournalRecordType.INSTRUMENT_RESOLUTION]
        availability_record = records[JournalRecordType.SHADOW_MARKET_AVAILABILITY]
        intent = None if intent_record is None else cast(ExecutionIntent, intent_record.decode())
        if master is None or (
            intent is not None and intent.master_proposal_id != master.proposal_id
        ):
            intent = None
        evidence_bundle = (
            None if evidence_record is None else cast(EvidenceBundle, evidence_record.decode())
        )
        if master is None or (
            evidence_bundle is not None and evidence_bundle.bundle_id != master.bundle_id
        ):
            evidence_bundle = None
        return RuntimeSnapshot(
            component=ComponentStatus(
                component="Runtime / MT5",
                state=component_state,
                detail=detail,
                source_path=str(source),
                as_of=None if latest_available is None else latest_available.isoformat(),
            ),
            state=state,
            latest_master=master,
            latest_evidence_bundle=evidence_bundle,
            latest_discipline=(
                None
                if discipline_record is None
                else cast(DisciplineOutcome, discipline_record.decode())
            ),
            latest_risk=(None if risk_record is None else cast(RiskOutcome, risk_record.decode())),
            latest_execution_intent=intent,
            latest_m15_context=(
                None
                if context_record is None
                else cast(M15ContextSnapshot, context_record.decode())
            ),
            latest_candidate_scan=(
                None if scan_record is None else cast(M5CandidateScan, scan_record.decode())
            ),
            latest_shadow_cycle=(
                None
                if shadow_cycle_record is None
                else cast(DecodedShadowRuntimeCycle, shadow_cycle_record.decode())
            ),
            latest_trade_plan=(
                None
                if trade_plan_record is None
                else cast(HypotheticalTradePlan, trade_plan_record.decode())
            ),
            instrument_resolution=(
                None
                if resolution_record is None
                else cast(ResolvedBrokerInstrument, resolution_record.decode())
            ),
            market_availability=(
                None
                if availability_record is None
                else cast(ShadowMarketAvailability, availability_record.decode())
            ),
            latest_interaction_assessment=assessment,
            latest_interaction_round=interaction_round,
            latest_interaction_turns=interaction_turns,
            latest_interaction_resolution=interaction_resolution,
            latest_interaction_impact=interaction_impact,
        )
    except (OSError, sqlite3.Error, ValueError) as error:
        return RuntimeSnapshot(
            component=_error("Runtime / MT5", f"Unable to read runtime journal: {error}", source)
        )


def _bounded_event_records(
    connection: sqlite3.Connection,
    event_id: str,
) -> tuple[tuple[int, JournalRecord], ...]:
    rows = connection.execute(
        "SELECT journal_sequence, record_json FROM runtime_journal "
        "WHERE event_id = ? ORDER BY journal_sequence LIMIT ?",
        (event_id, _MAX_CYCLE_RECORDS),
    ).fetchall()
    return tuple(
        (
            int(row["journal_sequence"]),
            JournalRecord.model_validate_json(str(row["record_json"])),
        )
        for row in rows
    )


def _recent_observability_records(
    connection: sqlite3.Connection,
    scan_limit: int,
) -> tuple[tuple[int, JournalRecord], ...]:
    relevant = (
        JournalRecordType.RUNTIME_EVENT,
        JournalRecordType.OUTCOME,
        JournalRecordType.RECONCILIATION_REPORT,
        JournalRecordType.RESUME_READINESS,
        JournalRecordType.RECOVERY_CHECKPOINT,
        JournalRecordType.M15_CONTEXT,
        JournalRecordType.M5_CANDIDATE_SCAN,
        JournalRecordType.THESIS_STATE,
        JournalRecordType.SCENARIO_STATE,
        JournalRecordType.AGENT_EVIDENCE,
        JournalRecordType.EVIDENCE_BUNDLE,
        JournalRecordType.MASTER_PROPOSAL,
        JournalRecordType.DISCIPLINE_OUTCOME,
        JournalRecordType.RISK_OUTCOME,
        JournalRecordType.EXECUTION_INTENT,
        JournalRecordType.HYPOTHETICAL_TRADE_PLAN,
        JournalRecordType.SHADOW_EXECUTION,
        JournalRecordType.SHADOW_RUNTIME_CYCLE,
        JournalRecordType.SHADOW_MARKET_AVAILABILITY,
        JournalRecordType.MASTER_CONFLICT_ASSESSMENT,
        JournalRecordType.SPECIALIST_INTERACTION_ROUND,
        JournalRecordType.SPECIALIST_INTERACTION_RESOLUTION,
        JournalRecordType.SPECIALIST_INTERACTION_IMPACT,
    )
    placeholders = ",".join("?" for _ in relevant)
    rows = connection.execute(
        "SELECT journal_sequence, record_json FROM runtime_journal "
        f"WHERE record_type IN ({placeholders}) "
        "ORDER BY journal_sequence DESC LIMIT ?",
        (*tuple(item.value for item in relevant), scan_limit),
    ).fetchall()
    return tuple(
        (
            int(row["journal_sequence"]),
            JournalRecord.model_validate_json(str(row["record_json"])),
        )
        for row in rows
    )


def _record_by_semantic_id(
    records: tuple[tuple[int, JournalRecord], ...],
    record_type: JournalRecordType,
    semantic_id: str | None,
) -> tuple[int, JournalRecord] | None:
    if semantic_id is None:
        return None
    identity_fields = (
        "scan_id",
        "cycle_id",
        "context_id",
        "bundle_id",
        "proposal_id",
        "outcome_id",
        "intent_id",
        "plan_id",
        "record_id",
    )
    for item in reversed(records):
        record = item[1]
        if record.record_type is not record_type:
            continue
        if record.semantic_id == semantic_id:
            return item
        decoded = record.decode()
        if any(getattr(decoded, field, None) == semantic_id for field in identity_fields):
            return item
    return None


def _latest_decoded(
    records: tuple[tuple[int, JournalRecord], ...],
    record_type: JournalRecordType,
) -> object | None:
    record = next(
        (item[1] for item in reversed(records) if item[1].record_type is record_type),
        None,
    )
    return None if record is None else record.decode()


def _malaysia_minute(value: datetime) -> str:
    return value.astimezone(_MALAYSIA).strftime("%Y-%m-%d %H:%M MYT")


def _activity_view(
    sequence: int,
    record: JournalRecord,
    *,
    label: str,
    detail: str | None = None,
    cycle_id: str | None = None,
    reason_codes: tuple[str, ...] = (),
    grouped_record_count: int = 1,
) -> RuntimeActivityView:
    return RuntimeActivityView(
        occurred_at=record.available_at.isoformat(),
        label=label,
        detail=detail,
        journal_sequence=sequence,
        record_type=record.record_type.value,
        event_id=record.event_id,
        semantic_id=record.semantic_id,
        cycle_id=cycle_id,
        reason_codes=reason_codes,
        raw_persisted_timestamp=record.available_at.isoformat(),
        grouped_record_count=grouped_record_count,
    )


def _activity_from_record(
    sequence: int,
    record: JournalRecord,
    *,
    readiness_label: str | None = None,
    broker_detail: str | None = None,
    last_completed_m5: datetime | None = None,
) -> RuntimeActivityView | None:
    decoded = record.decode()
    label: str | None = None
    detail: str | None = None
    cycle_id: str | None = None
    reason_codes: tuple[str, ...] = ()
    if isinstance(decoded, RuntimeEvent):
        if decoded.event_type is RuntimeEventType.M5_CLOSED:
            label = "New completed M5 accepted"
            detail = f"{_malaysia_minute(decoded.event_time)} · seq={decoded.source_sequence}"
        elif decoded.event_type in BROKER_REFRESH_EVENT_TYPES:
            return None
    elif isinstance(decoded, JournalOutcome):
        if decoded.status is JournalOutcomeStatus.REJECTED:
            label = "Runtime event rejected"
            detail = decoded.reason_code.replace("_", " ").title()
            reason_codes = (decoded.reason_code,)
    elif isinstance(decoded, ReconciliationReport):
        label = f"Broker reconciliation {decoded.status.value}"
        reason_codes = tuple(item.reason_code for item in decoded.findings)
        detail = broker_detail or (
            " · ".join(reason_codes) if reason_codes else "no unresolved findings"
        )
    elif isinstance(decoded, ResumeReadiness):
        label = f"{readiness_label or 'Runtime readiness'} {decoded.status.value}"
        reason_codes = tuple(item.value for item in decoded.reason_codes)
        detail = " · ".join(reason_codes) or "reconciliation resolved"
    elif isinstance(decoded, RecoveryCheckpoint):
        label = "Graceful stop checkpoint persisted"
        detail = f"runtime state={decoded.runtime_state_id}"
    elif isinstance(decoded, M15ContextSnapshot):
        label = "M15 context changed"
        detail = f"{decoded.structure.value.title()} / {decoded.regime.value.title()}"
    elif isinstance(decoded, M5CandidateScan):
        label = f"M5 scanner: {decoded.result.value.replace('_', ' ').title()}"
        reason_codes = tuple(item.value for item in decoded.reason_codes)
        detail = (
            "trading window closed"
            if ScanReason.OUTSIDE_ACTIVE_WINDOW in decoded.reason_codes
            else " · ".join(reason_codes)
        )
    elif isinstance(decoded, ThesisState):
        label = "Thesis updated"
        detail = f"{decoded.hypothesis} / {decoded.hypothesis_status.value.title()}"
    elif isinstance(decoded, ScenarioState):
        label = "Scenario updated"
        detail = f"{decoded.name} / {decoded.status.value.title()}"
    elif isinstance(decoded, AgentEvidence):
        return None
    elif isinstance(decoded, MasterConflictAssessment):
        label = (
            "Agent discussion triggered"
            if decoded.interaction_required
            else "Agent discussion not required"
        )
        detail = (
            f"disagreement={decoded.measured_disagreement:.0%} · "
            f"threshold={decoded.disagreement_threshold:.0%}"
        )
    elif isinstance(decoded, SpecialistInteractionRound):
        label = "Bounded agent discussion started"
        detail = "participants=" + ", ".join(decoded.participating_specialists)
    elif isinstance(decoded, SpecialistInteractionResolution):
        label = f"Agent discussion {decoded.status.value.replace('_', ' ').title()}"
        detail = decoded.failure_reason or "one evidence-bound round completed"
    elif isinstance(decoded, SpecialistInteractionImpact):
        label = "Master discussion impact measured"
        detail = (
            f"confidence delta={decoded.confidence_delta:+.1%} · "
            f"stance changed={'yes' if decoded.stance_changed else 'no'}"
        )
    elif isinstance(decoded, EvidenceBundle):
        label = "Evidence bundle created"
        agents = ", ".join(item.agent_name.title() for item in decoded.evidence)
        detail = f"agents={agents}" if agents else "Not available"
    elif isinstance(decoded, MasterProposal):
        label = f"Master decision: {decoded.decision.value}"
        detail = f"confidence={decoded.confidence:.0%}"
        reason_codes = tuple(item.value for item in decoded.reason_codes)
    elif isinstance(decoded, DisciplineOutcome):
        label = f"Discipline Guard: {decoded.result.value.replace('_', ' ').title()}"
        reason_codes = tuple(item.value for item in decoded.reason_codes)
        detail = "reason=" + ",".join(reason_codes)
    elif isinstance(decoded, RiskOutcome):
        label = (
            "Risk veto"
            if decoded.result.value in {"REJECT", "EMERGENCY_STOP"}
            else f"Risk: {decoded.result.value.replace('_', ' ').title()}"
        )
        reason_codes = tuple(item.value for item in decoded.reason_codes)
        detail = "reason=" + ",".join(reason_codes)
    elif isinstance(decoded, ExecutionIntent):
        label = "Hypothetical execution authorized"
        detail = "Shadow mode only"
    elif isinstance(decoded, HypotheticalTradePlan):
        label = "Hypothetical trade plan created"
        detail = decoded.direction
    elif isinstance(decoded, ShadowExecutionRecord):
        label = "Shadow execution recorded"
        detail = "No broker mutation"
    elif record.record_type is JournalRecordType.SHADOW_RUNTIME_CYCLE:
        label = "Cycle persisted"
        cycle = cast(DecodedShadowRuntimeCycle, decoded)
        detail = str(cycle.stage.value).replace("_", " ").title()
        cycle_id = cycle.cycle_id
    elif isinstance(decoded, ShadowMarketAvailability):
        label = decoded.status.value.replace("_", " ").title()
        reason_codes = (decoded.reason_code,)
        if decoded.status is LiveMarketStatus.WAITING_FOR_NEXT_M5:
            detail = (
                "Not available"
                if last_completed_m5 is None
                else f"last completed={_malaysia_minute(last_completed_m5)}"
            )
        elif decoded.reason_code:
            detail = f"reason={decoded.reason_code}"
    if label is None:
        return None
    return _activity_view(
        sequence,
        record,
        label=label,
        detail=detail,
        cycle_id=cycle_id,
        reason_codes=reason_codes,
    )


def _semantic_state_key(decoded: object) -> tuple[str, str] | None:
    category: str | None = None
    payload: object = None
    if isinstance(decoded, ResumeReadiness):
        category = "readiness"
        payload = (decoded.status.value, tuple(item.value for item in decoded.reason_codes))
    elif isinstance(decoded, ReconciliationReport):
        category = "reconciliation"
        payload = (
            decoded.status.value,
            tuple(
                (item.kind.value, item.status.value, item.reason_code)
                for item in decoded.findings
            ),
        )
    elif isinstance(decoded, ShadowMarketAvailability):
        category = "market_availability"
        payload = (decoded.status.value, decoded.reason_code)
    elif isinstance(decoded, M15ContextSnapshot):
        category = "m15_context"
        payload = (decoded.structure.value, decoded.regime.value)
    elif isinstance(decoded, ThesisState):
        category = "thesis"
        payload = (
            decoded.hypothesis,
            decoded.hypothesis_status.value,
            tuple((item.name, item.status.value) for item in decoded.scenarios),
        )
    elif isinstance(decoded, ScenarioState):
        category = f"scenario:{decoded.name}"
        payload = (decoded.status.value, decoded.entry_eligibility.value)
    if category is None:
        return None
    return category, json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _broker_payload_signature(event: RuntimeEvent) -> str:
    payload = event.payload.model_dump(
        mode="json",
        exclude={"as_of", "freshness"},
    )
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _number_text(value: object) -> str:
    return f"{float(value):g}" if isinstance(value, (int, float)) else "Not available"


def _broker_batch_detail(events: tuple[RuntimeEvent, ...]) -> str | None:
    details: list[str] = []
    for event in events:
        if event.event_type is RuntimeEventType.POSITIONS_UPDATED:
            details.append(f"positions={len(getattr(event.payload, 'positions', ())) }")
        elif event.event_type is RuntimeEventType.ORDERS_UPDATED:
            details.append(f"orders={len(getattr(event.payload, 'orders', ())) }")
        elif event.event_type is RuntimeEventType.EXPOSURE_UPDATED:
            details.append(f"exposure={_number_text(getattr(event.payload, 'gross_lots', None))}")
    return " · ".join(details) or None


def _activity_feed(
    records_descending: tuple[tuple[int, JournalRecord], ...],
    limit: int,
    *,
    latest_completed_m5: datetime | None = None,
) -> tuple[RuntimeActivityView, ...]:
    ascending = tuple(reversed(records_descending))
    broker_batches: dict[str, list[tuple[int, JournalRecord, RuntimeEvent]]] = {}
    agent_groups: dict[str, list[tuple[int, JournalRecord, AgentEvidence]]] = {}
    broker_details: dict[str, str | None] = {}
    candidates: list[RuntimeActivityView] = []

    for sequence, record in ascending:
        decoded = record.decode()
        if isinstance(decoded, RuntimeEvent) and decoded.event_type in BROKER_REFRESH_EVENT_TYPES:
            broker_batches.setdefault(record.available_at.isoformat(), []).append(
                (sequence, record, decoded)
            )
        elif isinstance(decoded, AgentEvidence):
            key = record.event_id or record.available_at.isoformat()
            agent_groups.setdefault(key, []).append((sequence, record, decoded))

    previous_broker_signature: tuple[tuple[str, str], ...] | None = None
    for timestamp, batch in broker_batches.items():
        events = tuple(item[2] for item in batch)
        semantic_events = tuple(
            event for event in events if event.event_type is not RuntimeEventType.TICK
        )
        if not semantic_events:
            continue
        broker_signature = tuple(
            sorted(
                (event.event_type.value, _broker_payload_signature(event))
                for event in semantic_events
            )
        )
        detail = _broker_batch_detail(semantic_events)
        broker_details[timestamp] = detail
        if (
            previous_broker_signature is not None
            and broker_signature != previous_broker_signature
        ):
            sequence, record, _ = batch[-1]
            candidates.append(
                _activity_view(
                    sequence,
                    record,
                    label="Broker state changed",
                    detail=detail,
                    grouped_record_count=len(semantic_events),
                )
            )
        previous_broker_signature = broker_signature

    for group in agent_groups.values():
        names = tuple(dict.fromkeys(item[2].agent_name.title() for item in group))
        sequence, record, _ = group[0]
        candidates.append(
            _activity_view(
                sequence,
                record,
                label="Specialist evidence recorded",
                detail="agents=" + ", ".join(names),
                grouped_record_count=len(group),
            )
        )

    state_signatures: dict[str, str] = {}
    startup_pending = False
    last_completed = latest_completed_m5
    for sequence, record in ascending:
        decoded = record.decode()
        if isinstance(decoded, RuntimeEvent) and decoded.event_type in BROKER_REFRESH_EVENT_TYPES:
            continue
        if isinstance(decoded, AgentEvidence):
            continue
        if isinstance(decoded, RuntimeEvent) and decoded.event_type is RuntimeEventType.M5_CLOSED:
            last_completed = decoded.event_time
        if isinstance(decoded, RecoveryCheckpoint):
            startup_pending = True
        state_key = _semantic_state_key(decoded)
        readiness_label: str | None = None
        if isinstance(decoded, ResumeReadiness) and startup_pending:
            readiness_label = "Startup recovery"
            startup_pending = False
        if state_key is not None:
            category, state_signature = state_key
            if state_signatures.get(category) == state_signature and readiness_label is None:
                continue
            state_signatures[category] = state_signature
        item = _activity_from_record(
            sequence,
            record,
            readiness_label=readiness_label,
            broker_detail=broker_details.get(record.available_at.isoformat()),
            last_completed_m5=last_completed,
        )
        if item is None:
            continue
        candidates.append(item)
    candidates.sort(key=lambda item: item.journal_sequence)
    return tuple(candidates[-limit:])


def _human_codes(values: object) -> tuple[str, ...]:
    return tuple(
        getattr(item, "value", str(item)).replace("_", " ").title()
        for item in cast(tuple[object, ...], values)
    )


def _build_observability(
    *,
    sequence: int,
    cycle: DecodedShadowRuntimeCycle,
    records: tuple[tuple[int, JournalRecord], ...],
    readiness: ResumeReadiness | None,
    availability: ShadowMarketAvailability | None,
) -> tuple[CurrentCycleView, DecisionExplanationView, tuple[PipelineStageView, ...]]:
    m5_event = next(
        (
            decoded
            for _, record in reversed(records)
            if isinstance((decoded := record.decode()), RuntimeEvent)
            and decoded.event_type is RuntimeEventType.M5_CLOSED
        ),
        None,
    )
    scan_entry = _record_by_semantic_id(
        records, JournalRecordType.M5_CANDIDATE_SCAN, cycle.scan_id
    )
    scan = None if scan_entry is None else cast(M5CandidateScan, scan_entry[1].decode())
    context_entry = _record_by_semantic_id(
        records, JournalRecordType.M15_CONTEXT, cycle.m15_context_id
    )
    context = (
        None if context_entry is None else cast(M15ContextSnapshot, context_entry[1].decode())
    )
    bundle_entry = _record_by_semantic_id(
        records, JournalRecordType.EVIDENCE_BUNDLE, cycle.evidence_bundle_id
    )
    bundle = None if bundle_entry is None else cast(EvidenceBundle, bundle_entry[1].decode())
    master_entry = _record_by_semantic_id(
        records, JournalRecordType.MASTER_PROPOSAL, cycle.master_proposal_id
    )
    master = None if master_entry is None else cast(MasterProposal, master_entry[1].decode())
    discipline_entry = _record_by_semantic_id(
        records, JournalRecordType.DISCIPLINE_OUTCOME, cycle.discipline_outcome_id
    )
    discipline = (
        None
        if discipline_entry is None
        else cast(DisciplineOutcome, discipline_entry[1].decode())
    )
    risk_entry = _record_by_semantic_id(
        records, JournalRecordType.RISK_OUTCOME, cycle.risk_outcome_id
    )
    risk = None if risk_entry is None else cast(RiskOutcome, risk_entry[1].decode())
    intent_entry = _record_by_semantic_id(
        records, JournalRecordType.EXECUTION_INTENT, cycle.execution_intent_id
    )
    intent = None if intent_entry is None else cast(ExecutionIntent, intent_entry[1].decode())
    thesis = cast(ThesisState | None, _latest_decoded(records, JournalRecordType.THESIS_STATE))
    scenario = None
    if thesis is not None and thesis.scenarios:
        scenario = next(
            (item for item in thesis.scenarios if item.entry_eligibility.value == "ELIGIBLE"),
            thesis.scenarios[0],
        )
    outside_window = bool(
        scan is not None and ScanReason.OUTSIDE_ACTIVE_WINDOW in scan.reason_codes
    )
    reason_codes: tuple[str, ...] = ()
    if master is not None:
        reason_codes += tuple(item.value for item in master.reason_codes)
    if discipline is not None:
        reason_codes += tuple(item.value for item in discipline.reason_codes)
    if risk is not None:
        reason_codes += tuple(item.value for item in risk.reason_codes)

    final_action = "NO ACTION"
    if master is not None:
        final_action = master.decision.value
    if discipline is not None and discipline.result.value in {"REJECT", "PAUSE"}:
        final_action = "NO ACTION"
    if risk is not None and risk.result.value in {"REJECT", "EMERGENCY_STOP"}:
        final_action = "NO ACTION"
    if cycle.trade_plan_id is not None and intent is not None:
        final_action = intent.direction.value
    authorization = "Not required"
    if intent is not None:
        authorization = "Authorized hypothetically — Shadow mode only"
    elif risk is not None and risk.result.value in {"REJECT", "EMERGENCY_STOP"}:
        authorization = "Not authorized — Risk veto"
    elif discipline is not None and discipline.result.value in {"REJECT", "PAUSE"}:
        authorization = "Not authorized — Discipline Guard"
    elif cycle.stage is ShadowCycleStage.SETUP_DETECTED:
        authorization = "Not available"

    current = CurrentCycleView(
        cycle_timestamp=cycle.as_of.isoformat(),
        symbol=cycle.canonical_instrument,
        completed_m5_timestamp=(
            _NOT_AVAILABLE
            if m5_event is None
            else (m5_event.event_time or m5_event.available_at).isoformat()
        ),
        trading_window_state=("Outside active window" if outside_window else _NOT_AVAILABLE),
        m15_context=(
            _NOT_AVAILABLE
            if context is None
            else f"{context.structure.value.title()} / {context.regime.value.title()}"
        ),
        scanner_result=(
            _NOT_AVAILABLE
            if scan is None
            else scan.result.value.replace("_", " ").title()
        ),
        scenario=(
            _NOT_AVAILABLE
            if scenario is None
            else f"{scenario.name} / {scenario.status.value.title()}"
        ),
        thesis=(
            _NOT_AVAILABLE
            if thesis is None
            else f"{thesis.hypothesis} / {thesis.hypothesis_status.value.title()}"
        ),
        agents_invoked=(
            () if bundle is None else tuple(item.agent_name.title() for item in bundle.evidence)
        ),
        evidence_status=("Created" if bundle is not None else "Not required"),
        master_decision=(_NOT_AVAILABLE if master is None else master.decision.value),
        decision_confidence=(
            _NOT_AVAILABLE if master is None else f"{master.confidence:.0%}"
        ),
        discipline_outcome=(
            "Not required"
            if discipline is None
            else discipline.result.value.replace("_", " ").title()
        ),
        risk_outcome=(
            "Not required" if risk is None else risk.result.value.replace("_", " ").title()
        ),
        final_action=final_action,
        execution_authorization=authorization,
        persistence_status="Yes",
        journal_sequence=sequence,
        event_id=cycle.event_id,
        cycle_id=cycle.cycle_id,
        scan_id=cycle.scan_id,
        evidence_bundle_id=cycle.evidence_bundle_id,
        thesis_id=None if thesis is None else thesis.thesis_id,
        scenario_id=None if scenario is None else scenario.scenario_id,
        decision_id=None if master is None else master.proposal_id,
        raw_reason_codes=reason_codes,
    )

    points: list[str] = []
    if readiness is not None:
        if readiness.status is ResumeStatus.BLOCKED:
            points.extend(f"✗ {item}" for item in _human_codes(readiness.reason_codes))
            explanation = DecisionExplanationView(
                title="WHY BLOCKED",
                result="No event decision permitted",
                points=tuple(points),
            )
        elif readiness.status is ResumeStatus.SAFE:
            points.append("✓ Broker reconciliation SAFE")
            if availability is not None and availability.status in {
                LiveMarketStatus.BAR_READY,
                LiveMarketStatus.WAITING_FOR_NEXT_M5,
            }:
                points.append("✓ Market data current")
            explanation = None
        else:
            explanation = None
    else:
        explanation = None
    if explanation is None:
        if outside_window:
            points.append("✗ Trading window closed")
        if scan is not None and scan.result in {
            CandidateResult.NO_SETUP,
            CandidateResult.OUTSIDE_WINDOW,
        }:
            points.append(f"✗ M5 scanner: {scan.result.value.replace('_', ' ').title()}")
        if bundle is None:
            points.append("— Specialist evidence not required")
        if master is not None and master.decision.value == "HOLD":
            points.extend(f"✗ {item}" for item in _human_codes(master.reason_codes))
        if discipline is not None and discipline.result.value in {"REJECT", "PAUSE"}:
            points.extend(f"✗ Discipline: {item}" for item in _human_codes(discipline.reason_codes))
        if risk is not None and risk.result.value in {"REJECT", "EMERGENCY_STOP"}:
            points.extend(f"✗ Risk: {item}" for item in _human_codes(risk.reason_codes))
        if intent is not None:
            points.append("— Execution disabled by Shadow mode")
        title = "WHY NO ACTION"
        if master is not None and master.decision.value == "HOLD":
            title = "WHY HOLD"
        explanation = DecisionExplanationView(
            title=title,
            result=final_action,
            points=tuple(points) or ("— No persisted reason evidence available",),
        )

    quiet = cycle.stage is ShadowCycleStage.QUIET
    pipeline: tuple[PipelineStageView, ...] = (
        PipelineStageView(stage="Market Data", status="COMPLETE"),
        PipelineStageView(
            stage="Runtime State",
            status=(
                "COMPLETE"
                if _latest_decoded(records, JournalRecordType.RUNTIME_STATE) is not None
                else "NOT AVAILABLE"
            ),
        ),
        PipelineStageView(stage="Scanner", status="COMPLETE" if scan else "NOT AVAILABLE"),
        PipelineStageView(
            stage="Scenario",
            status=(
                "COMPLETE"
                if scenario is not None
                else ("SKIPPED" if quiet else "NOT AVAILABLE")
            ),
        ),
        PipelineStageView(
            stage="Agents", status="COMPLETE" if bundle is not None else "NOT REQUIRED"
        ),
        PipelineStageView(
            stage="Evidence", status="COMPLETE" if bundle is not None else "NOT REQUIRED"
        ),
        PipelineStageView(
            stage="Master",
            status=(master.decision.value if master is not None else "NOT REQUIRED"),
        ),
        PipelineStageView(
            stage="Discipline",
            status=(
                discipline.result.value if discipline is not None else "NOT REQUIRED"
            ),
        ),
        PipelineStageView(
            stage="Risk", status=risk.result.value if risk is not None else "NOT REQUIRED"
        ),
        PipelineStageView(
            stage="Execution",
            status="SHADOW ONLY" if intent is not None else "NOT REQUIRED",
        ),
    )
    if readiness is not None and readiness.status is ResumeStatus.BLOCKED:
        pipeline = (
            PipelineStageView(
                stage="Market Data",
                status=(
                    "COMPLETE"
                    if availability is not None
                    and availability.status
                    in {LiveMarketStatus.BAR_READY, LiveMarketStatus.WAITING_FOR_NEXT_M5}
                    else "NOT AVAILABLE"
                ),
            ),
            PipelineStageView(stage="Runtime State", status="BLOCKED"),
            *tuple(
                PipelineStageView(stage=stage, status="BLOCKED")
                for stage in (
                    "Scanner",
                    "Scenario",
                    "Agents",
                    "Evidence",
                    "Master",
                    "Discipline",
                    "Risk",
                    "Execution",
                )
            ),
        )
    return current, explanation, pipeline


def load_runtime_observability(
    path: str | Path | None,
    *,
    activity_limit: int = 30,
) -> RuntimeObservabilitySnapshot:
    """Read one cycle-anchored projection and a bounded semantic activity window."""

    if activity_limit < 1 or activity_limit > 50:
        raise ValueError("runtime activity limit must be between 1 and 50")
    if path is None or not str(path).strip():
        return RuntimeObservabilitySnapshot(component=_not_configured("Runtime observability"))
    source = Path(path)
    if not source.is_file():
        return RuntimeObservabilitySnapshot(
            component=_unavailable("Runtime observability", source)
        )
    try:
        with _readonly_connection(source) as connection:
            if not _has_table(connection, "runtime_journal"):
                return RuntimeObservabilitySnapshot(
                    component=_error(
                        "Runtime observability",
                        "Configured database has no runtime journal.",
                        source,
                    )
                )
            cycle_row = connection.execute(
                "SELECT journal_sequence, record_json FROM runtime_journal "
                "WHERE record_type = ? ORDER BY journal_sequence DESC LIMIT 1",
                (JournalRecordType.SHADOW_RUNTIME_CYCLE.value,),
            ).fetchone()
            readiness_record = _latest_journal_record(
                connection, JournalRecordType.RESUME_READINESS
            )
            availability_record = _latest_journal_record(
                connection, JournalRecordType.SHADOW_MARKET_AVAILABILITY
            )
            activity_records = _recent_observability_records(
                connection,
                min(_MAX_ACTIVITY_SCAN, max(activity_limit * 40, activity_limit)),
            )
            activity = _activity_feed(activity_records, activity_limit)
            if cycle_row is None:
                return RuntimeObservabilitySnapshot(
                    component=ComponentStatus(
                        component="Runtime observability",
                        state=ComponentState.AVAILABLE,
                        detail="Runtime journal is readable; no completed cycle is available.",
                        source_path=str(source),
                    ),
                    recent_activity=activity,
                )
            cycle_record = JournalRecord.model_validate_json(str(cycle_row["record_json"]))
            cycle = cast(DecodedShadowRuntimeCycle, cycle_record.decode())
            records = _bounded_event_records(connection, cycle.event_id)
            readiness = (
                None
                if readiness_record is None
                else cast(ResumeReadiness, readiness_record.decode())
            )
            availability = (
                None
                if availability_record is None
                else cast(ShadowMarketAvailability, availability_record.decode())
            )
            current, explanation, pipeline = _build_observability(
                sequence=int(cycle_row["journal_sequence"]),
                cycle=cycle,
                records=records,
                readiness=readiness,
                availability=availability,
            )
        return RuntimeObservabilitySnapshot(
            component=ComponentStatus(
                component="Runtime observability",
                state=ComponentState.AVAILABLE,
                detail="Latest persisted Shadow cycle and bounded activity are available.",
                source_path=str(source),
                as_of=current.cycle_timestamp,
            ),
            current_cycle=current,
            recent_activity=activity,
            decision_explanation=explanation,
            pipeline=pipeline,
        )
    except (OSError, sqlite3.Error, ValueError) as error:
        return RuntimeObservabilitySnapshot(
            component=_error(
                "Runtime observability",
                f"Unable to read runtime observability: {error}",
                source,
            )
        )


def load_runtime_performance(path: str | Path | None) -> RuntimeComputeSnapshot:
    """Read the replace-in-place operational telemetry snapshot."""

    if path is None or not str(path).strip():
        return RuntimeComputeSnapshot(component=_not_configured("Runtime performance"))
    source = Path(path)
    if not source.is_file():
        return RuntimeComputeSnapshot(component=_unavailable("Runtime performance", source))
    try:
        if source.stat().st_size > 256 * 1024:
            raise ValueError("runtime performance snapshot exceeds size limit")
        from axq.orchestration.performance import RuntimePerformanceSnapshot

        metrics = RuntimePerformanceSnapshot.model_validate_json(
            source.read_text(encoding="utf-8")
        )
        return RuntimeComputeSnapshot(
            component=ComponentStatus(
                component="Runtime performance",
                state=ComponentState.AVAILABLE,
                detail="Latest lightweight Shadow Runtime telemetry is available.",
                source_path=str(source),
                as_of=metrics.observed_at.isoformat(),
            ),
            metrics=metrics,
        )
    except (OSError, ValueError) as error:
        return RuntimeComputeSnapshot(
            component=_error(
                "Runtime performance",
                f"Unable to read runtime performance telemetry: {error}",
                source,
            )
        )


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("artifact section must be an object")
    return cast(dict[str, object], value)


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return number if math.isfinite(number) else None
    return None


def load_performance_snapshot(path: str | Path | None) -> PerformanceSnapshot:
    """Load only recorded Phase 7 replay metrics from an explicit JSON artifact."""

    if path is None or not str(path).strip():
        return PerformanceSnapshot(component=_not_configured("Performance"))
    source = Path(path)
    if not source.is_file():
        return PerformanceSnapshot(component=_unavailable("Performance", source))
    try:
        raw = source.read_bytes()
        if len(raw) > _MAX_JSON_BYTES:
            raise ValueError("performance artifact exceeds dashboard size limit")
        payload = _mapping(json.loads(raw))
        input_data = _mapping(payload.get("input", {}))
        decisions = _mapping(payload.get("decisions", {}))
        trades = _mapping(payload.get("trades", {}))
        curve_value = payload.get("equity_curve")
        equity_curve = None
        if isinstance(curve_value, list) and curve_value:
            converted = tuple(_optional_float(item) for item in curve_value)
            if all(item is not None for item in converted):
                equity_curve = cast(tuple[float, ...], converted)
        return PerformanceSnapshot(
            component=ComponentStatus(
                component="Performance",
                state=ComponentState.AVAILABLE,
                detail="Persisted replay metrics are available.",
                source_path=str(source),
                as_of=str(input_data.get("end")) if input_data.get("end") is not None else None,
            ),
            artifact_id=(
                str(payload["artifact_id"]) if payload.get("artifact_id") is not None else None
            ),
            range_start=(str(input_data["start"]) if input_data.get("start") is not None else None),
            range_end=(str(input_data["end"]) if input_data.get("end") is not None else None),
            rows=_optional_int(input_data.get("rows")),
            decision_cycles=_optional_int(decisions.get("cycles")),
            completed_trades=_optional_int(trades.get("completed")),
            realized_pnl=_optional_float(trades.get("realized_pnl")),
            win_rate=_optional_float(trades.get("win_rate")),
            average_r=_optional_float(trades.get("average_r")),
            expectancy_usd=_optional_float(trades.get("expectancy_usd")),
            profit_factor=_optional_float(trades.get("profit_factor")),
            max_drawdown=_optional_float(trades.get("max_drawdown")),
            long_trades=_optional_int(trades.get("long")),
            short_trades=_optional_int(trades.get("short")),
            equity_curve=equity_curve,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        return PerformanceSnapshot(
            component=_error("Performance", f"Unable to read replay metrics: {error}", source)
        )


def read_ollama_status(
    endpoint: str | None,
    *,
    model_name: str | None,
    timeout_seconds: float = 2.0,
    transport: StatusTransport | None = None,
) -> ComponentStatus:
    """Perform GET-only loopback health/model inspection; never generate text."""

    if endpoint is None or not endpoint.strip():
        return _not_configured("Ollama")
    try:
        normalized = validate_loopback_ollama_url(endpoint)
        actual_transport = transport or cast(StatusTransport, OllamaHTTPTransport(normalized))
        version_body = actual_transport.request(
            "GET",
            "/api/version",
            payload=None,
            timeout_seconds=timeout_seconds,
            response_byte_limit=_OLLAMA_RESPONSE_LIMIT,
        )
        tags_body = actual_transport.request(
            "GET",
            "/api/tags",
            payload=None,
            timeout_seconds=timeout_seconds,
            response_byte_limit=_OLLAMA_RESPONSE_LIMIT,
        )
        version_data = _mapping(json.loads(version_body))
        tags_data = _mapping(json.loads(tags_body))
        models = tags_data.get("models")
        if not isinstance(models, list):
            raise ValueError("Ollama model list is invalid")
        selected = next(
            (
                _mapping(item)
                for item in models
                if isinstance(item, dict) and item.get("name") == model_name
            ),
            None,
        )
        if model_name is not None and selected is None:
            return ComponentStatus(
                component="Ollama",
                state=ComponentState.UNAVAILABLE,
                detail=f"Ollama is online, but model {model_name!r} is not available.",
                metadata={"server_version": str(version_data.get("version", "unknown"))},
            )
        metadata = {"server_version": str(version_data.get("version", "unknown"))}
        if selected is not None:
            metadata["model_name"] = str(selected.get("name", model_name))
            metadata["model_digest"] = str(selected.get("digest", "unknown"))
        return ComponentStatus(
            component="Ollama",
            state=ComponentState.ONLINE,
            detail="Loopback Ollama endpoint is online.",
            metadata=metadata,
        )
    except Exception as error:  # safe dashboard boundary: report, never raise into Streamlit
        return _error("Ollama", f"Ollama status unavailable: {error}")


__all__ = [
    "load_performance_snapshot",
    "load_reasoning_snapshot",
    "load_runtime_observability",
    "load_runtime_performance",
    "load_runtime_snapshot",
    "read_ollama_status",
]
