"""Pure display helpers shared by Streamlit views and tests."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from axq.dashboard.contracts import (
    ComponentState,
    CurrentCycleView,
    RuntimeActivityView,
    RuntimeSnapshot,
)
from axq.reasoning.contracts import LLMRequestEnvelope, ReflectionExplanation

NOT_AVAILABLE = "Not available yet"
LIVE_ACCOUNT_NOT_CONNECTED = "MT5 account data is not connected yet"
NAVIGATION_PAGES = (
    "Overview",
    "Live Monitor",
    "AI Reasoning",
    "Performance",
    "History / Audit",
)

_STATUS_LABELS = {
    ComponentState.AVAILABLE: "Ready",
    ComponentState.ONLINE: "Online",
    ComponentState.STALE: "Data is old",
    ComponentState.NOT_CONFIGURED: "Not connected",
    ComponentState.UNAVAILABLE: "No data",
    ComponentState.ERROR: "Error",
}

_SUMMARY_FIELDS = (
    "summary",
    "explanation",
    "description",
    "rationale",
    "observation",
    "finding",
)
_TECHNICAL_REFERENCE = re.compile(
    r"\b(?:context|experience|finding|proposal|reflection|source)[-_][A-Za-z0-9_-]+\b"
    r"|\b[0-9a-fA-F]{32,}\b"
    r"|\b(?:content_digest|context_id|finding_ids?|schema_version|source_digest|source_id)\b"
    r"|\b([A-Za-z0-9])\1{7,}\b",
    re.IGNORECASE,
)
_MALAYSIA = ZoneInfo("Asia/Kuala_Lumpur")
_CONFLICT_REASONS = {"HIGH_CONTRADICTION", "HIGH_DISAGREEMENT"}


def display_value(value: object) -> object:
    """Keep known zero values while making missing values explicit."""

    return NOT_AVAILABLE if value is None or value == "" else value


def status_label(state: ComponentState) -> str:
    return _STATUS_LABELS[state]


def is_agent_room_setup(runtime: RuntimeSnapshot) -> bool:
    """Expand only when the latest persisted shadow cycle entered agent analysis."""

    cycle = getattr(runtime, "latest_shadow_cycle", None)
    scan = getattr(runtime, "latest_candidate_scan", None)
    if cycle is not None and scan is not None and cycle.scan_id == scan.scan_id:
        return str(cycle.stage.value) != "QUIET"
    proposal = runtime.latest_master
    if proposal is None:
        return False
    if bool(proposal.actionable):
        return True
    reasons = {
        getattr(reason, "value", str(reason)) for reason in getattr(proposal, "reason_codes", ())
    }
    return bool(reasons & _CONFLICT_REASONS)


def malaysia_trading_window(now: datetime) -> str:
    """Describe the approved 20:00–23:00 Malaysia operator window."""

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("dashboard time must be timezone-aware")
    local = now.astimezone(_MALAYSIA)
    if 20 <= local.hour < 23:
        return "Open · closes at 23:00 Malaysia time"
    return "Closed · opens at 20:00 Malaysia time"


def next_m5_close_text(now: datetime) -> str:
    """Return a display-only countdown to the next completed M5 boundary."""

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("dashboard time must be timezone-aware")
    utc_now = now.astimezone(UTC)
    boundary = utc_now.replace(second=0, microsecond=0)
    minutes = 5 - (boundary.minute % 5)
    boundary += timedelta(minutes=minutes)
    remaining = max(0, int((boundary - utc_now).total_seconds()))
    return f"{remaining // 60}m {remaining % 60:02d}s"


def malaysia_timestamp(value: str) -> str:
    """Render a persisted ISO timestamp in the operator's Malaysia timezone."""

    if value == "Not available":
        return value
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "Not available"
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return NOT_AVAILABLE
    return parsed.astimezone(_MALAYSIA).strftime("%Y-%m-%d %H:%M:%S MYT")


def current_cycle_rows(cycle: CurrentCycleView) -> tuple[dict[str, str], ...]:
    """Return concise operator rows without inferring absent cycle evidence."""

    agents = ", ".join(cycle.agents_invoked) if cycle.agents_invoked else "Not required"
    return (
        {"Field": "Time", "Value": malaysia_timestamp(cycle.cycle_timestamp)},
        {"Field": "Symbol", "Value": cycle.symbol},
        {"Field": "Completed M5", "Value": malaysia_timestamp(cycle.completed_m5_timestamp)},
        {"Field": "Trading window", "Value": cycle.trading_window_state},
        {"Field": "M15 Context", "Value": cycle.m15_context},
        {"Field": "M5 Scanner", "Value": cycle.scanner_result},
        {"Field": "Scenario", "Value": cycle.scenario},
        {"Field": "Thesis", "Value": cycle.thesis},
        {"Field": "Agents Invoked", "Value": agents},
        {"Field": "Evidence", "Value": cycle.evidence_status},
        {"Field": "Master Decision", "Value": cycle.master_decision},
        {"Field": "Confidence", "Value": cycle.decision_confidence},
        {"Field": "Discipline Guard", "Value": cycle.discipline_outcome},
        {"Field": "Risk", "Value": cycle.risk_outcome},
        {"Field": "Final Action", "Value": cycle.final_action},
        {"Field": "Execution", "Value": cycle.execution_authorization},
        {"Field": "Cycle Persisted", "Value": cycle.persistence_status},
    )


def activity_rows(items: tuple[RuntimeActivityView, ...]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "Time": malaysia_timestamp(item.occurred_at),
            "Activity": item.label,
            "Detail": item.detail or "",
        }
        for item in items
    )


def uncertainty_text(output: ReflectionExplanation) -> str:
    """Render the typed uncertainty assessment without exposing internals."""

    return f"{output.uncertainty.level.value.title()} — {output.uncertainty.basis}"


def _safe_summary(value: object, *, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return operator_text(value)
    if isinstance(value, Mapping):
        for field in _SUMMARY_FIELDS:
            candidate = value.get(field)
            if isinstance(candidate, str) and candidate.strip():
                return _safe_summary(candidate, fallback=fallback)
    return fallback


def operator_text(value: str) -> str:
    """Hide technical provenance tokens from normal operator-facing prose."""

    return _TECHNICAL_REFERENCE.sub("[technical reference hidden]", value.strip())


def reasoning_evidence(request: LLMRequestEnvelope) -> tuple[dict[str, str], ...]:
    """Project bounded context into operator-safe evidence cards."""

    return tuple(
        {
            "Evidence summary": _safe_summary(
                item.content,
                fallback="Evidence record is available for review.",
            ),
            "Evidence type": item.context_kind.replace("_", " ").title(),
        }
        for item in request.context
    )


__all__ = [
    "LIVE_ACCOUNT_NOT_CONNECTED",
    "NAVIGATION_PAGES",
    "NOT_AVAILABLE",
    "display_value",
    "is_agent_room_setup",
    "malaysia_trading_window",
    "next_m5_close_text",
    "operator_text",
    "reasoning_evidence",
    "status_label",
    "uncertainty_text",
]
