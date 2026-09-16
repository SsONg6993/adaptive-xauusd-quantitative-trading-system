"""Operator-friendly Streamlit UI for read-only AXQ inspection."""

from __future__ import annotations

import argparse
import importlib
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from axq.dashboard.contracts import ComponentState, ComponentStatus, RuntimeSnapshot
from axq.dashboard.mt5_reader import LiveMT5Snapshot, read_live_mt5_snapshot
from axq.dashboard.readers import (
    load_performance_snapshot,
    load_reasoning_snapshot,
    load_runtime_snapshot,
    read_ollama_status,
)
from axq.dashboard.shadow_controller import (
    ManagedShadowSnapshot,
    ShadowRuntimeController,
    default_managed_shadow_config,
)
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
from axq.orchestration.shadow_control import ManagedRuntimeStatus, ManagedShadowConfig


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--reasoning-db")
    parser.add_argument("--runtime-db")
    parser.add_argument("--metrics-json")
    parser.add_argument("--ollama-endpoint")
    parser.add_argument("--ollama-model")
    parser.add_argument("--mt5-terminal-path")
    parser.add_argument("--mt5-symbol")
    values, _ = parser.parse_known_args()
    return values


def _optional_path(value: str) -> Path | None:
    return Path(value) if value.strip() else None


def _technical_details(st: Any, label: str, payload: object) -> None:
    with st.expander(label, expanded=False):
        st.json(payload)


def _status_card(
    st: Any,
    title: str,
    status: ComponentStatus,
    *,
    display_status: str | None = None,
) -> None:
    with st.container(border=True):
        st.caption(title)
        st.subheader(display_status or status_label(status.state))
        st.write(status.detail)
        if status.as_of is not None:
            st.caption(f"Latest activity: {status.as_of}")


def _mt5_display_status(snapshot: LiveMT5Snapshot) -> str:
    if snapshot.component.detail == "Managed Shadow Runtime owns the MT5 connection":
        return "Managed by Shadow"
    if snapshot.component.detail == "Direct MT5 probe has not been requested":
        return "Not checked"
    return "Online" if snapshot.component.state.value == "ONLINE" else "Offline"


def _managed_runtime_owns_mt5(status: ManagedRuntimeStatus) -> bool:
    return status in {
        ManagedRuntimeStatus.STARTING,
        ManagedRuntimeStatus.RUNNING,
        ManagedRuntimeStatus.WAITING_FOR_MARKET,
        ManagedRuntimeStatus.STOPPING,
    }


def _managed_mt5_placeholder(symbol: str) -> LiveMT5Snapshot:
    observed_at = datetime.now(UTC)
    return LiveMT5Snapshot(
        component=ComponentStatus(
            component="MT5",
            state=ComponentState.AVAILABLE,
            detail="Managed Shadow Runtime owns the MT5 connection",
            as_of=observed_at.isoformat(),
        ),
        quote_component=ComponentStatus(
            component="Live quote",
            state=ComponentState.UNAVAILABLE,
            detail="Use persisted managed-runtime market facts while Shadow is active.",
        ),
        configured_symbol=symbol,
        resolved_broker_symbol=symbol,
        last_refreshed=observed_at,
    )


def _idle_mt5_placeholder(symbol: str) -> LiveMT5Snapshot:
    observed_at = datetime.now(UTC)
    return LiveMT5Snapshot(
        component=ComponentStatus(
            component="MT5",
            state=ComponentState.UNAVAILABLE,
            detail="Direct MT5 probe has not been requested",
        ),
        quote_component=ComponentStatus(
            component="Live quote",
            state=ComponentState.UNAVAILABLE,
            detail="Use CHECK MT5 CONNECTION for an explicit stopped-state probe.",
        ),
        configured_symbol=symbol,
        resolved_broker_symbol=symbol,
        last_refreshed=observed_at,
    )


def _account_metrics(st: Any, live_mt5: LiveMT5Snapshot) -> None:
    if live_mt5.account_login is None:
        st.info(LIVE_ACCOUNT_NOT_CONNECTED)
    columns = st.columns(5)
    columns[0].metric("Balance", display_value(live_mt5.balance))
    columns[1].metric("Equity", display_value(live_mt5.equity))
    columns[2].metric(
        "Open Positions",
        display_value(None if live_mt5.account_login is None else len(live_mt5.positions)),
    )
    columns[3].metric("Floating P/L", display_value(live_mt5.floating_pnl))
    columns[4].metric("Free Margin", display_value(live_mt5.free_margin))


def _decision_cards(st: Any, runtime: RuntimeSnapshot) -> None:
    proposal = runtime.latest_master
    columns = st.columns(3)
    columns[0].metric(
        "Latest Decision",
        NOT_AVAILABLE if proposal is None else proposal.decision.value,
    )
    columns[1].metric(
        "Confidence",
        NOT_AVAILABLE if proposal is None else f"{proposal.confidence:.0%}",
    )
    activity = runtime.component.as_of
    if proposal is not None:
        activity = proposal.as_of.isoformat()
    columns[2].metric("Latest Activity", display_value(activity))
    if proposal is not None:
        reasons = [reason.value.replace("_", " ").title() for reason in proposal.reason_codes]
        st.write("Why: " + (", ".join(reasons) if reasons else "No additional reason recorded"))
        _technical_details(
            st,
            "Technical details · decision",
            proposal.model_dump(mode="json"),
        )


def _shadow_runtime_controls(
    st: Any,
    controller: ShadowRuntimeController,
    config: ManagedShadowConfig,
    managed: ManagedShadowSnapshot,
    runtime: RuntimeSnapshot,
) -> ManagedShadowSnapshot:
    st.subheader("Shadow Runtime")
    controls = st.columns(2)
    with controls[0]:
        if st.button("START", type="primary", use_container_width=True):
            managed = controller.start(config, now=datetime.now(UTC))
    with controls[1]:
        if st.button("STOP", type="primary", use_container_width=True):
            managed = controller.stop(now=datetime.now(UTC))
    with st.expander("Advanced runtime control", expanded=False):
        st.warning("RESTART proceeds only after a confirmed graceful stop.")
        if st.button("RESTART", use_container_width=True):
            managed = controller.restart(config, now=datetime.now(UTC))

    status_columns = st.columns(4)
    status_columns[0].metric("Runtime state", managed.status.value.replace("_", " ").title())
    resolved = runtime.instrument_resolution
    status_columns[1].metric(
        "Resolved broker symbol",
        NOT_AVAILABLE if resolved is None else resolved.resolved_broker_symbol,
    )
    availability = runtime.market_availability
    status_columns[2].metric(
        "Market state",
        NOT_AVAILABLE
        if availability is None
        else availability.status.value.replace("_", " ").title(),
    )
    status_columns[3].metric(
        "Last completed M5",
        NOT_AVAILABLE
        if availability is None or availability.latest_completed_m5_at is None
        else availability.latest_completed_m5_at.isoformat(),
    )
    last_cycle = runtime.latest_shadow_cycle
    st.caption(
        "Last runtime cycle: "
        + (NOT_AVAILABLE if last_cycle is None else last_cycle.as_of.isoformat())
    )
    if managed.error:
        st.error(managed.error)
    _technical_details(
        st,
        "Technical details · Shadow Runtime controller",
        {
            "controller": managed.model_dump(mode="json"),
            "configuration": config.model_dump(mode="json"),
        },
    )
    return managed


def _overview(
    st: Any,
    runtime: RuntimeSnapshot,
    ollama: Any,
    live_mt5_reader: Callable[[], LiveMT5Snapshot],
    controller: ShadowRuntimeController,
    managed_config: ManagedShadowConfig,
    managed_status: ManagedShadowSnapshot,
) -> None:
    st.header("Overview")
    st.error("SHADOW MODE — NO ORDER SENT")
    managed_status = _shadow_runtime_controls(
        st, controller, managed_config, managed_status, runtime
    )
    if _managed_runtime_owns_mt5(managed_status.status):
        live_mt5 = _managed_mt5_placeholder(managed_config.gold_symbols[1])
    elif st.button("CHECK MT5 CONNECTION", use_container_width=True):
        live_mt5 = live_mt5_reader()
    else:
        live_mt5 = _idle_mt5_placeholder(managed_config.gold_symbols[1])
    st.caption("Live market observation through the shared AXQ decision kernel")
    now = datetime.now(UTC)

    status_columns = st.columns(3)
    resolved_symbol = (
        runtime.instrument_resolution.resolved_broker_symbol
        if runtime.instrument_resolution is not None
        else live_mt5.configured_symbol
    )
    status_columns[0].metric(
        "Symbol",
        display_value(resolved_symbol),
    )
    status_columns[1].metric("MT5", _mt5_display_status(live_mt5))
    status_columns[2].metric("AI", status_label(ollama.state))

    quote_columns = st.columns(3)
    quote_columns[0].metric("Bid", display_value(live_mt5.bid))
    quote_columns[1].metric("Ask", display_value(live_mt5.ask))
    quote_columns[2].metric("Spread", display_value(live_mt5.spread))

    context_columns = st.columns(4)
    context_columns[0].metric("Trading window", malaysia_trading_window(now))
    m15 = runtime.latest_m15_context
    m15_text = (
        "Waiting for live runtime"
        if m15 is None
        else f"{m15.structure.value.title()} · {m15.regime.value.replace('_', ' ').title()}"
    )
    context_columns[1].metric("M15 context", m15_text)
    cycle = runtime.latest_shadow_cycle
    scan = runtime.latest_candidate_scan
    proposal = runtime.latest_master
    if cycle is not None and (proposal is None or cycle.master_proposal_id != proposal.proposal_id):
        proposal = None
    scanner_text = "Waiting for live runtime"
    if scan is not None:
        scanner_text = scan.result.value.replace("_", " ").title()
    context_columns[2].metric("M5 scanner", scanner_text)
    context_columns[3].metric("Next completed M5 candle", next_m5_close_text(now))

    latest_activity = runtime.component.as_of or (
        None if live_mt5.last_refreshed is None else live_mt5.last_refreshed.isoformat()
    )
    st.caption(f"Latest activity: {display_value(latest_activity)}")
    availability = runtime.market_availability
    stale_live_quote = live_mt5.quote_component.state.value == "STALE"
    if stale_live_quote or (
        availability is not None and availability.status.value in {"STALE_QUOTE", "UNAVAILABLE"}
    ):
        st.warning("MARKET CLOSED / STALE QUOTE — WAITING FOR FRESH DATA")

    if not is_agent_room_setup(runtime):
        st.info("No agent discussion required.")
        _technical_details(
            st,
            "Technical details · overview sources",
            {
                "runtime": runtime.model_dump(mode="json"),
                "live_mt5": live_mt5.model_dump(mode="json"),
            },
        )
        return

    st.subheader("Agent Room")
    bundle = runtime.latest_evidence_bundle
    agent_labels = {
        "chart": "Chart Agent",
        "quant": "Quant Agent",
        "regime": "Regime Agent",
        "historical": "Historical / Memory Agent",
        "news": "News / Macro snapshot",
    }
    if bundle is None or proposal is None or bundle.bundle_id != proposal.bundle_id:
        st.info("Waiting for live runtime")
    else:
        agent_columns = st.columns(2)
        for index, evidence in enumerate(bundle.evidence):
            with agent_columns[index % 2].container(border=True):
                st.markdown(f"**{agent_labels[evidence.agent_name]}**")
                stance = (
                    "No stance" if evidence.direction is None else evidence.direction.value.title()
                )
                st.write(f"{stance} · {evidence.confidence:.0%} confidence")
                reason = evidence.rationale or evidence.hypothesis
                st.caption(operator_text(reason))

    st.markdown("**Agreement / conflict**")
    if proposal is None:
        st.write("Waiting for live runtime")
    else:
        st.write(
            f"Disagreement {proposal.disagreement:.0%} · Contradiction {proposal.contradiction:.0%}"
        )

    st.markdown("**Evidence-bound interaction**")
    assessment = runtime.latest_interaction_assessment
    if assessment is None:
        st.info("Interaction unavailable — no persisted interaction assessment exists.")
    elif not assessment.interaction_required:
        st.info("Interaction was not required; Master proceeded from aligned initial evidence.")
    elif runtime.latest_interaction_round is None:
        st.warning("Interaction unavailable — the persisted round is incomplete.")
    else:
        st.caption(
            "One deterministic round. Specialists restate only their original evidence; "
            "their trading opinions are unchanged."
        )
        labels = agent_labels | {"master": "Master"}
        for turn in runtime.latest_interaction_turns:
            with st.container(border=True):
                st.markdown(
                    f"**{labels.get(turn.speaker, turn.speaker.title())} → "
                    f"{labels.get(turn.recipient, turn.recipient.title())}**"
                )
                if turn.stance is not None and turn.confidence is not None:
                    st.caption(
                        f"Original stance retained: {turn.stance.value.title()} · "
                        f"{turn.confidence:.0%} confidence"
                    )
                st.write(operator_text(turn.rationale))
        resolution = runtime.latest_interaction_resolution
        if resolution is None:
            st.warning("Interaction unavailable — no terminal interaction record exists.")
        elif resolution.status.value != "COMPLETED":
            st.warning(
                "Interaction unavailable — Master used the original evidence only "
                f"({resolution.status.value.replace('_', ' ').title()})."
            )

    with st.container(border=True):
        st.markdown("**Master synthesis**")
        if proposal is None:
            st.write("Waiting for live runtime")
        else:
            reasons = [item.value.replace("_", " ").title() for item in proposal.reason_codes]
            st.subheader(f"{proposal.decision.value} · {proposal.confidence:.0%} confidence")
            st.write(", ".join(reasons))

    outcome_columns = st.columns(2)
    with outcome_columns[0].container(border=True):
        st.markdown("**Discipline outcome**")
        if runtime.latest_discipline is None:
            st.write("Waiting for live runtime")
        else:
            discipline = runtime.latest_discipline
            st.subheader(discipline.result.value.replace("_", " ").title())
            st.write(operator_text(discipline.rationale))
    with outcome_columns[1].container(border=True):
        st.markdown("**Risk outcome**")
        if runtime.latest_risk is None:
            st.write("Waiting for live runtime")
        else:
            risk = runtime.latest_risk
            st.subheader(risk.result.value.replace("_", " ").title())
            st.write(operator_text(risk.rationale))

    trade_plan = runtime.latest_trade_plan
    if proposal is not None and proposal.decision.value == "HOLD":
        with st.container(border=True):
            st.subheader("HOLD")
            reasons = [item.value.replace("_", " ").title() for item in proposal.reason_codes]
            st.write("Final reason: " + ", ".join(reasons))
    elif trade_plan is not None and cycle is not None and cycle.trade_plan_id == trade_plan.plan_id:
        st.subheader("Shadow trade plan")
        plan = st.columns(5)
        fields = (
            ("Entry", trade_plan.entry),
            ("Stop Loss", trade_plan.stop_loss),
            ("Take Profit", trade_plan.take_profit),
            ("Position size", trade_plan.position_size),
            ("R:R", trade_plan.risk_reward),
        )
        for column, (label, field) in zip(plan, fields, strict=True):
            column.metric(label, display_value(field.value))
            column.caption(field.reason)
        confidence = trade_plan.confidence.value
        st.write("Confidence: " + (NOT_AVAILABLE if confidence is None else f"{confidence:.0%}"))
        st.error("SHADOW MODE — NO ORDER SENT")
    else:
        st.info("Trade plan: Waiting for live runtime")

    _technical_details(
        st,
        "Technical details · Agent Room",
        {
            "runtime": runtime.model_dump(mode="json"),
            "live_mt5": live_mt5.model_dump(mode="json"),
        },
    )


def _live_monitor(
    st: Any,
    runtime: RuntimeSnapshot,
    live_mt5: LiveMT5Snapshot,
) -> None:
    st.header("Live Monitor")
    st.caption("Read-only view of the latest persisted runtime and account snapshot")
    first = st.columns(2)
    with first[0]:
        _status_card(st, "Runtime", runtime.component)
    with first[1]:
        _status_card(
            st,
            "MT5",
            live_mt5.component,
            display_status=_mt5_display_status(live_mt5),
        )
    _account_metrics(st, live_mt5)

    if live_mt5.account_login is not None:
        st.caption(
            f"Account: {live_mt5.account_login} · "
            f"Server: {display_value(live_mt5.server)} · "
            f"Last refresh: {live_mt5.last_refreshed.isoformat()}"
        )

    st.subheader(f"Live market · {live_mt5.configured_symbol}")
    if live_mt5.quote_component.state.value == "UNAVAILABLE":
        st.info(live_mt5.quote_component.detail)
    else:
        market = st.columns(4)
        market[0].metric("Bid", display_value(live_mt5.bid))
        market[1].metric("Ask", display_value(live_mt5.ask))
        market[2].metric("Spread", display_value(live_mt5.spread))
        market[3].metric(
            "Quote updated",
            display_value(
                None if live_mt5.quote_updated_at is None else live_mt5.quote_updated_at.isoformat()
            ),
        )

    st.subheader("Open positions")
    positions = live_mt5.positions
    if not positions:
        if live_mt5.account_login is None:
            st.info(LIVE_ACCOUNT_NOT_CONNECTED)
        else:
            st.info("No open positions")
    else:
        st.dataframe(
            [
                {
                    "Direction": item.direction,
                    "Entry": item.open_price,
                    "Current": item.current_price,
                    "Floating P/L": item.floating_pnl,
                    "Size (lots)": item.volume,
                    "Symbol": item.symbol,
                }
                for item in positions
            ],
            hide_index=True,
            use_container_width=True,
        )
    _technical_details(
        st,
        "Technical details · live MT5 snapshot",
        live_mt5.model_dump(mode="json"),
    )
    if runtime.state is not None:
        _technical_details(
            st,
            "Technical details · historical runtime snapshot",
            runtime.state.model_dump(mode="json"),
        )


def _reasoning(st: Any, snapshot: Any) -> None:
    st.header("AI Reasoning")
    st.caption("Recent offline explanations based on bounded AXQ evidence")
    _status_card(st, "AI reasoning history", snapshot.component)
    if not snapshot.attempts:
        st.info(NOT_AVAILABLE)
        return
    for view in snapshot.attempts:
        title = (
            f"{view.attempt.status.value.replace('_', ' ').title()} · "
            f"{view.attempt.completed_at.isoformat()}"
        )
        with st.container(border=True):
            st.subheader(title)
            if view.response is None:
                st.warning("This attempt did not produce a usable explanation.")
                if view.attempt.failure is not None:
                    st.write("See Technical details for the recorded failure.")
            else:
                output = view.response.output
                st.markdown("**Evidence used**")
                for evidence in reasoning_evidence(view.request):
                    st.markdown(
                        f"- **{evidence['Evidence type']}:** {evidence['Evidence summary']}"
                    )
                st.write(operator_text(output.explanation))
                st.markdown(f"**Hypothesis:** {operator_text(output.hypothesis)}")
                st.markdown(f"**Uncertainty:** {operator_text(uncertainty_text(output))}")
                st.markdown(
                    "**Suggested next investigation:** "
                    + operator_text(output.suggested_next_investigation)
                )
                st.caption(f"Evidence cited: {len(output.cited_evidence_ids)} record(s)")
            token_count = view.attempt.prompt_token_count
            if view.attempt.output_token_count is not None:
                token_count = (token_count or 0) + view.attempt.output_token_count
            duration = view.attempt.provider_total_duration_ns
            duration_text = (
                NOT_AVAILABLE if duration is None else f"{duration / 1_000_000_000:.1f}s"
            )
            st.caption(
                f"Usage: {display_value(token_count)} tokens · Provider duration: {duration_text}"
            )
            _technical_details(
                st,
                "Technical details",
                {
                    "attempt": view.attempt.model_dump(mode="json"),
                    "request": view.request.model_dump(mode="json"),
                    "response": (
                        None if view.response is None else view.response.model_dump(mode="json")
                    ),
                },
            )


def _performance(st: Any, snapshot: Any) -> None:
    st.header("Performance")
    _status_card(st, "Historical results", snapshot.component)
    st.markdown(
        "**Covered date range:** "
        f"{display_value(snapshot.range_start)} → {display_value(snapshot.range_end)}"
    )
    first = st.columns(4)
    first[0].metric("Completed Trades", display_value(snapshot.completed_trades))
    first[1].metric("Realized P/L", display_value(snapshot.realized_pnl))
    first[2].metric(
        "Win Rate",
        NOT_AVAILABLE if snapshot.win_rate is None else f"{snapshot.win_rate:.1%}",
    )
    first[3].metric("Expectancy", display_value(snapshot.expectancy_usd))
    second = st.columns(4)
    second[0].metric("Profit Factor", display_value(snapshot.profit_factor))
    second[1].metric("Max Drawdown", display_value(snapshot.max_drawdown))
    second[2].metric("Decision Cycles", display_value(snapshot.decision_cycles))
    second[3].metric("Data Rows", display_value(snapshot.rows))
    st.subheader("Equity curve")
    if snapshot.equity_curve is None:
        st.info(NOT_AVAILABLE)
    else:
        st.line_chart(snapshot.equity_curve)
    _technical_details(
        st,
        "Technical details · performance artifact",
        snapshot.model_dump(mode="json"),
    )


def _history(st: Any, reasoning: Any, runtime: Any) -> None:
    st.header("History / Audit")
    st.caption("Recent immutable reasoning and safety outcomes")
    st.subheader("AI reasoning attempts")
    if not reasoning.attempts:
        st.info(NOT_AVAILABLE)
    else:
        st.dataframe(
            [
                {
                    "Completed": item.attempt.completed_at.isoformat(),
                    "Result": item.attempt.status.value.replace("_", " ").title(),
                    "Issue": (
                        NOT_AVAILABLE
                        if item.attempt.failure is None
                        else item.attempt.failure.code.value.replace("_", " ").title()
                    ),
                }
                for item in reasoning.attempts
            ],
            hide_index=True,
            use_container_width=True,
        )
        _technical_details(
            st,
            "Technical details · reasoning history",
            [item.attempt.model_dump(mode="json") for item in reasoning.attempts],
        )

    st.subheader("Discipline Guard")
    if runtime.latest_discipline is None:
        st.info(NOT_AVAILABLE)
    else:
        outcome = runtime.latest_discipline
        with st.container(border=True):
            st.metric("Latest result", outcome.result.value.replace("_", " ").title())
            reasons = [item.value.replace("_", " ").title() for item in outcome.reason_codes]
            st.write("Reason: " + (", ".join(reasons) if reasons else "No rejection recorded"))
        _technical_details(
            st,
            "Technical details · Discipline Guard",
            outcome.model_dump(mode="json"),
        )

    st.subheader("Risk")
    if runtime.latest_risk is None:
        st.info(NOT_AVAILABLE)
    else:
        outcome = runtime.latest_risk
        with st.container(border=True):
            st.metric("Latest result", outcome.result.value.replace("_", " ").title())
            reasons = [item.value.replace("_", " ").title() for item in outcome.reason_codes]
            st.write("Reason: " + (", ".join(reasons) if reasons else "No rejection recorded"))
        _technical_details(
            st,
            "Technical details · Risk",
            outcome.model_dump(mode="json"),
        )


def main() -> None:
    st = importlib.import_module("streamlit")
    args = _arguments()
    st.set_page_config(page_title="AXQ Trading Monitor", page_icon="📈", layout="wide")
    st.title("AXQ Trading Monitor")
    st.caption("Read-only operator view")
    project_root = Path(__file__).resolve().parents[3]
    defaults = default_managed_shadow_config(project_root)

    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to", NAVIGATION_PAGES, label_visibility="collapsed")
        with st.expander("Advanced / Data Sources", expanded=False):
            st.caption("Technical configuration")
            reasoning_path = st.text_input(
                "Reasoning audit database",
                value=args.reasoning_db or "",
            )
            output_path = st.text_input(
                "Shadow Runtime output directory",
                value=str(
                    Path(args.runtime_db).parent
                    if args.runtime_db
                    else defaults.output_dir
                ),
            )
            metrics_path = st.text_input(
                "Historical metrics file",
                value=args.metrics_json or "",
            )
            ollama_endpoint = st.text_input(
                "AI service endpoint",
                value=args.ollama_endpoint or "",
            )
            ollama_model = st.text_input("AI model", value=args.ollama_model or "")
            mt5_terminal_path = st.text_input(
                "MT5 terminal path (optional)",
                value=args.mt5_terminal_path or str(defaults.terminal_path),
            )
            gold_symbols = st.text_input(
                "Gold symbol allowlist",
                value=",".join(defaults.gold_symbols),
            )
            default_broker_symbol = args.mt5_symbol or defaults.gold_symbols[1]
            mt5_symbol = st.text_input("Broker symbol", value=default_broker_symbol)
            poll_seconds = st.number_input(
                "Shadow poll interval (seconds)",
                min_value=0.25,
                max_value=60.0,
                value=defaults.poll_seconds,
            )

    managed_output = Path(output_path).resolve()
    runtime_path = (
        Path(args.runtime_db)
        if args.runtime_db
        else managed_output / "shadow-runtime.sqlite3"
    )
    managed_config = ManagedShadowConfig(
        project_root=project_root,
        python_executable=defaults.python_executable,
        terminal_path=Path(mt5_terminal_path),
        gold_symbols=tuple(gold_symbols.split(",")),
        output_dir=managed_output,
        poll_seconds=float(poll_seconds),
    )
    controller = ShadowRuntimeController(
        control_db=managed_output / "shadow-control.sqlite3"
    )

    recent_attempts = 10
    if page in {"AI Reasoning", "History / Audit"}:
        recent_attempts = st.slider("Recent activity to show", 1, 50, 10)

    reasoning = load_reasoning_snapshot(_optional_path(reasoning_path), limit=recent_attempts)
    runtime = load_runtime_snapshot(runtime_path)
    performance = load_performance_snapshot(_optional_path(metrics_path))
    ollama = read_ollama_status(
        ollama_endpoint or None,
        model_name=ollama_model or None,
    )

    if page == "Overview":
        def render_overview() -> None:
            current_runtime = load_runtime_snapshot(runtime_path)
            managed_status = controller.status(now=datetime.now(UTC))
            _overview(
                st,
                current_runtime,
                ollama,
                lambda: read_live_mt5_snapshot(
                    symbol=mt5_symbol,
                    terminal_path=mt5_terminal_path or None,
                ),
                controller,
                managed_config,
                managed_status,
            )

        st.fragment(run_every=2.0)(render_overview)()
    elif page == "Live Monitor":
        refresh_label = st.selectbox(
            "Auto-refresh",
            ("Off", "5 seconds", "15 seconds", "30 seconds", "60 seconds"),
            index=1,
        )
        refresh_seconds = {
            "Off": None,
            "5 seconds": 5,
            "15 seconds": 15,
            "30 seconds": 30,
            "60 seconds": 60,
        }[refresh_label]

        def render_live_monitor() -> None:
            live_mt5 = read_live_mt5_snapshot(
                symbol=mt5_symbol,
                terminal_path=mt5_terminal_path or None,
            )
            _live_monitor(st, runtime, live_mt5)

        st.fragment(run_every=refresh_seconds)(render_live_monitor)()
    elif page == "AI Reasoning":
        _reasoning(st, reasoning)
    elif page == "Performance":
        _performance(st, performance)
    else:
        _history(st, reasoning, runtime)


if __name__ == "__main__":
    main()
