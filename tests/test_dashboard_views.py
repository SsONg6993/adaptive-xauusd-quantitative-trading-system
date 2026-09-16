"""Safe display-projection tests for the Streamlit dashboard."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from axq.dashboard.contracts import ComponentState
from axq.dashboard.views import (
    LIVE_ACCOUNT_NOT_CONNECTED,
    NAVIGATION_PAGES,
    NOT_AVAILABLE,
    display_value,
    is_agent_room_setup,
    malaysia_trading_window,
    next_m5_close_text,
    operator_text,
    reasoning_evidence,
    status_label,
    uncertainty_text,
)
from axq.reasoning.contracts import (
    ReflectionExplanation,
    UncertaintyAssessment,
    UncertaintyLevel,
)
from tests.reasoning_test_support import request_envelope


def test_missing_values_are_visibly_rendered() -> None:
    assert display_value(None) == NOT_AVAILABLE
    assert display_value(0) == 0
    assert display_value("") == NOT_AVAILABLE


def test_every_component_state_has_an_operator_label() -> None:
    assert {item: status_label(item) for item in ComponentState} == {
        ComponentState.AVAILABLE: "Ready",
        ComponentState.ONLINE: "Online",
        ComponentState.STALE: "Data is old",
        ComponentState.NOT_CONFIGURED: "Not connected",
        ComponentState.UNAVAILABLE: "No data",
        ComponentState.ERROR: "Error",
    }


def test_operator_navigation_and_live_account_copy_are_explicit() -> None:
    assert NAVIGATION_PAGES == (
        "Overview",
        "Live Monitor",
        "AI Reasoning",
        "Performance",
        "History / Audit",
    )
    assert LIVE_ACCOUNT_NOT_CONNECTED == "MT5 account data is not connected yet"


def test_uncertainty_assessment_renders_level_and_basis() -> None:
    output = ReflectionExplanation(
        explanation="Losses clustered during one measured session.",
        cited_evidence_ids=("context-weekly-summary",),
        hypothesis="The weakness may be session-dependent.",
        uncertainty=UncertaintyAssessment(
            level=UncertaintyLevel.MEDIUM,
            basis="Only two complete weeks support this observation.",
        ),
        suggested_next_investigation="Compare another complete month.",
    )

    assert uncertainty_text(output) == (
        "Medium — Only two complete weeks support this observation."
    )


def test_reasoning_evidence_projection_excludes_technical_identifiers() -> None:
    request = request_envelope()

    evidence = reasoning_evidence(request)

    assert evidence == (
        {
            "Evidence summary": "London-session losses repeated in two complete weeks.",
            "Evidence type": "Weekly Finding Summary",
        },
    )
    rendered = repr(evidence)
    assert request.source_references[0].source_id not in rendered
    assert request.source_references[0].source_digest not in rendered
    assert request.context[0].context_id not in rendered
    assert request.context[0].content_digest not in rendered
    assert "aaaaaaaa" not in rendered


def test_operator_reasoning_text_redacts_technical_identifiers() -> None:
    rendered = operator_text(
        "Review weekly-reflection-aaaaaaaaaaaaaaaaaaaa and source_digest "
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa."
    )

    assert "weekly-reflection" not in rendered
    assert "source_digest" not in rendered
    assert "aaaaaaaa" not in rendered
    assert "technical reference hidden" in rendered


def test_shadow_overview_opens_agent_room_only_for_actionable_or_conflicted_setup() -> None:
    no_runtime = SimpleNamespace(latest_master=None)
    quiet_hold = SimpleNamespace(
        latest_master=SimpleNamespace(actionable=False, reason_codes=("LOW_CONFIDENCE",))
    )
    conflicted_hold = SimpleNamespace(
        latest_master=SimpleNamespace(
            actionable=False,
            reason_codes=("HIGH_DISAGREEMENT",),
        )
    )
    actionable = SimpleNamespace(latest_master=SimpleNamespace(actionable=True))

    assert is_agent_room_setup(no_runtime) is False
    assert is_agent_room_setup(quiet_hold) is False
    assert is_agent_room_setup(conflicted_hold) is True
    assert is_agent_room_setup(actionable) is True


def test_malaysia_trading_window_uses_20_to_23_local_time() -> None:
    assert malaysia_trading_window(datetime(2026, 9, 12, 12, 0, tzinfo=UTC)) == (
        "Open · closes at 23:00 Malaysia time"
    )
    assert malaysia_trading_window(datetime(2026, 9, 12, 15, 0, tzinfo=UTC)) == (
        "Closed · opens at 20:00 Malaysia time"
    )


def test_next_m5_close_countdown_uses_next_completed_bar_boundary() -> None:
    assert next_m5_close_text(datetime(2026, 9, 12, 12, 3, 20, tzinfo=UTC)) == "1m 40s"
    assert next_m5_close_text(datetime(2026, 9, 12, 12, 5, 0, tzinfo=UTC)) == "5m 00s"
