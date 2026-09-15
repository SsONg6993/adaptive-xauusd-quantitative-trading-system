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

from axq.dashboard.contracts import (
    ComponentState,
    ComponentStatus,
    PerformanceSnapshot,
    ReasoningAttemptView,
    ReasoningSnapshot,
    RuntimeSnapshot,
)
from axq.discipline.contracts import DisciplineOutcome
from axq.execution_boundary.contracts import ExecutionIntent
from axq.interaction.contracts import (
    MasterConflictAssessment,
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
from axq.runtime.journal import JournalRecord, JournalRecordType
from axq.runtime.kernel import EvidenceBundle
from axq.runtime.shadow import (
    HypotheticalTradePlan,
    M5CandidateScan,
    M15ContextSnapshot,
    ShadowMarketAvailability,
    ShadowRuntimeCycle,
)
from axq.runtime.state import SharedRuntimeState

_MAX_JSON_BYTES = 32 * 1024 * 1024
_OLLAMA_RESPONSE_LIMIT = 1024 * 1024


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
                else cast(ShadowRuntimeCycle, shadow_cycle_record.decode())
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
        )
    except (OSError, sqlite3.Error, ValueError) as error:
        return RuntimeSnapshot(
            component=_error("Runtime / MT5", f"Unable to read runtime journal: {error}", source)
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
    "load_runtime_snapshot",
    "read_ollama_status",
]
