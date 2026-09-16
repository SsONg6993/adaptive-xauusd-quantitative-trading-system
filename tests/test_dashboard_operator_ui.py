"""Operator-facing presentation constraints for the Streamlit dashboard."""

import ast
from pathlib import Path

from axq.dashboard.app import _idle_mt5_placeholder, _managed_runtime_owns_mt5
from axq.orchestration.shadow_control import ManagedRuntimeStatus

APP_PATH = Path("src/axq/dashboard/app.py")


def test_raw_json_is_confined_to_collapsed_technical_details() -> None:
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    json_functions: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "json"
            for child in ast.walk(node)
        ):
            json_functions.add(node.name)
    assert json_functions == {"_technical_details"}


def test_technical_configuration_is_collapsed_and_live_monitor_exists() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert 'st.expander("Advanced / Data Sources", expanded=False)' in text
    assert '"Live Monitor"' in text
    assert '"AI Reasoning"' in text
    assert '"History / Audit"' in text
    assert "LIVE_ACCOUNT_NOT_CONNECTED" in text


def test_live_mt5_is_explicit_configured_and_separate_from_runtime() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert "read_live_mt5_snapshot" in text
    assert 'parser.add_argument("--mt5-symbol")' in text
    assert 'st.text_input("Broker symbol"' in text
    assert '"MT5 terminal path (optional)"' in text
    assert "Auto-refresh" in text
    assert "st.fragment" in text
    assert "XAUUSD" not in text
    assert "_account_metrics(st, live_mt5)" in text


def test_reasoning_uses_typed_uncertainty_and_operator_evidence_projection() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert "uncertainty_text(output)" in text
    assert "reasoning_evidence(view.request)" in text
    assert "output.uncertainty.value" not in text
    assert "output.uncertainty_basis" not in text


def test_overview_is_shadow_first_and_hides_agent_room_without_setup() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    for label in (
        "SHADOW MODE",
        "Trading window",
        "M15 context",
        "M5 scanner",
        "Next completed M5 candle",
        "No agent discussion required.",
        "Agent Room",
        "Master synthesis",
        "SHADOW MODE — NO ORDER SENT",
    ):
        assert label in text
    assert "if not is_agent_room_setup(runtime):" in text


def test_agent_room_renders_persisted_evidence_bound_turns_only() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert "Evidence-bound interaction" in text
    assert "latest_interaction_turns" in text
    assert "Interaction was not required" in text
    assert "Interaction unavailable" in text


def test_overview_has_durable_shadow_process_controls_without_session_ownership() -> None:
    text = APP_PATH.read_text(encoding="utf-8")
    assert 'st.button("START"' in text
    assert 'st.button("STOP"' in text
    assert 'st.button("RESTART"' in text
    assert "Shadow Runtime" in text
    assert "ShadowRuntimeController" in text
    assert "session_state" not in text
    assert "DEMO" not in text
    assert "LIVE execution" not in text


def test_dashboard_yields_direct_mt5_ownership_while_shadow_is_active() -> None:
    active = {
        ManagedRuntimeStatus.STARTING,
        ManagedRuntimeStatus.RUNNING,
        ManagedRuntimeStatus.WAITING_FOR_MARKET,
        ManagedRuntimeStatus.STOPPING,
    }

    assert all(_managed_runtime_owns_mt5(status) for status in active)
    assert not _managed_runtime_owns_mt5(ManagedRuntimeStatus.STOPPED)
    assert not _managed_runtime_owns_mt5(ManagedRuntimeStatus.ERROR)


def test_dashboard_stopped_state_does_not_probe_mt5_without_operator_request() -> None:
    snapshot = _idle_mt5_placeholder("XAUUSD.sc")

    assert snapshot.configured_symbol == "XAUUSD.sc"
    assert snapshot.resolved_broker_symbol == "XAUUSD.sc"
    assert snapshot.component.detail == "Direct MT5 probe has not been requested"
    assert snapshot.last_refreshed is not None
