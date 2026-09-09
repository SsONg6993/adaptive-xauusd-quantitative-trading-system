from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.agents import AgentStatus, DirectionalBias, HypothesisRelationship
from axq.discipline import (
    DisciplineContext,
    DisciplineState,
    default_demo_discipline_policy,
    evaluate_discipline,
)
from axq.execution_boundary import (
    BrokerExecutionReport,
    DemoExecutionAdapter,
    ExecutionAccountMode,
    ExecutionMode,
    ExecutionObservation,
    ExecutionOrderType,
    ExecutionReason,
    ExecutionResult,
    ExecutionResultStatus,
    InMemoryExecutionLedger,
    TransportFailure,
    UnknownSubmissionState,
    build_execution_intent,
    default_execution_policy,
    execution_result_to_runtime_event,
)
from axq.master import EvidenceDisposition, FusionReason, MasterProposal, SpecialistContribution
from axq.risk_boundary import RiskContext, RiskOutcome, RiskReason, RiskResult
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    ExecutionStatus,
    ExposureState,
    FreshnessStatus,
    MarketState,
    OrderBookState,
    PositionBookState,
    RuntimeEventType,
    initial_runtime_state,
    reduce_state,
)
from axq.runtime.kernel import AGENT_ORDER
from axq.schemas import Signal

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _fresh(component: str) -> ComponentFreshness:
    return ComponentFreshness(
        component=component,
        status=FreshnessStatus.AVAILABLE,
        observed_at=T0,
        available_at=T0,
        stale_after_ms=15_000,
    )


def _proposal(signal: Signal = Signal.BUY) -> MasterProposal:
    direction = DirectionalBias.BULLISH if signal is Signal.BUY else DirectionalBias.BEARISH
    contributions = tuple(
        SpecialistContribution(
            agent_name=name,
            evidence_id=f"ae-{name}-execution",
            status=AgentStatus.READY,
            direction=direction if name == "chart" else None,
            disposition=(
                EvidenceDisposition.CONTRIBUTED
                if name == "chart"
                else EvidenceDisposition.CONTEXT_ONLY
            ),
            configured_weight=1.0,
            applied_weight=1.0 if name == "chart" else 0.0,
            effective_strength=0.8 if name == "chart" else 0.0,
            signed_score=(0.8 if signal is Signal.BUY else -0.8) if name == "chart" else 0.0,
            uncertainty=0.1,
            internal_contradiction=0.0,
        )
        for name in AGENT_ORDER
    )
    return MasterProposal(
        bundle_id="eb-execution",
        event_id="ev-execution",
        runtime_state_id="state-execution",
        as_of=T0,
        policy_id="mfp-execution",
        policy_version="1.0",
        decision=signal,
        actionable=True,
        confidence=0.8,
        net_score=0.8 if signal is Signal.BUY else -0.8,
        bullish_score=0.8 if signal is Signal.BUY else 0.0,
        bearish_score=0.8 if signal is Signal.SELL else 0.0,
        contradiction=0.0,
        disagreement=0.0,
        uncertainty=0.1,
        ready_directional_agents=1,
        contributing_evidence_ids=("ae-chart-execution",),
        contributions=contributions,
        reason_codes=(
            FusionReason.ACTIONABLE_BUY if signal is Signal.BUY else FusionReason.ACTIONABLE_SELL,
        ),
    )


def _discipline(proposal: MasterProposal):
    policy = default_demo_discipline_policy()
    return evaluate_discipline(
        proposal,
        DisciplineContext(
            as_of=T0,
            available_at=T0,
            trading_day=T0.date(),
            session_id="london",
            setup_id="setup-execution",
            thesis_id="thesis-execution",
            scenario_id="scenario-execution",
            thesis_relationship=HypothesisRelationship.NEW,
        ),
        DisciplineState(
            policy_id=policy.policy_id,
            as_of=T0,
            available_at=T0,
            trading_day=T0.date(),
            session_id="london",
            trades_today=0,
            trades_this_session=0,
            consecutive_losses=0,
        ),
        policy,
    )


def _risk_context(signal: Signal = Signal.BUY) -> RiskContext:
    stop = 2490.0 if signal is Signal.BUY else 2510.0
    return RiskContext(
        as_of=T0,
        available_at=T0,
        symbol="XAUUSD",
        account=AccountState(
            source="mt5",
            account_id="demo-account",
            as_of=T0,
            freshness=_fresh("account"),
            currency="USD",
            balance=10_000.0,
            equity=10_000.0,
            free_margin=9_000.0,
            used_margin=1_000.0,
            margin_level=1_000.0,
            floating_pnl=0.0,
            daily_realized_pnl=0.0,
            daily_unrealized_pnl=0.0,
            daily_drawdown=0.0,
            total_drawdown=0.0,
        ),
        market=MarketState(
            source="mt5",
            symbol="XAUUSD",
            as_of=T0,
            freshness=_fresh("market"),
            bid=2499.99,
            ask=2500.01,
            last=2500.0,
            spread_points=2.0,
        ),
        positions=PositionBookState(
            source="mt5", as_of=T0, freshness=_fresh("positions")
        ),
        orders=OrderBookState(source="mt5", as_of=T0, freshness=_fresh("orders")),
        exposure=ExposureState(
            as_of=T0,
            freshness=_fresh("exposure"),
            gross_lots=0.0,
            net_lots=0.0,
            gross_notional=0.0,
            net_notional=0.0,
        ),
        broker_constraints=BrokerConstraints(
            source="mt5",
            symbol="XAUUSD",
            as_of=T0,
            freshness=_fresh("broker_constraints"),
            trade_allowed=True,
            volume_min=0.01,
            volume_max=10.0,
            volume_step=0.01,
            point_size=0.01,
            tick_size=0.01,
            tick_value_loss=1.0,
            stops_level_points=10.0,
            freeze_level_points=0.0,
        ),
        entry_price=2500.0,
        stop_loss_price=stop,
        estimated_margin_required=100.0,
        estimated_slippage_points=1.0,
        daily_drawdown_fraction=0.0,
        total_drawdown_fraction=0.0,
        kill_switch_active=False,
    )


def _upstream(
    signal: Signal = Signal.BUY,
    result: RiskResult = RiskResult.PASS,
) -> tuple[MasterProposal, object, RiskContext, RiskOutcome]:
    proposal = _proposal(signal)
    discipline = _discipline(proposal)
    context = _risk_context(signal)
    passed = result is RiskResult.PASS
    risk = RiskOutcome(
        master_proposal_id=proposal.proposal_id,
        evidence_bundle_id=proposal.bundle_id,
        discipline_outcome_id=discipline.outcome_id,
        discipline_result=discipline.result,
        risk_policy_id="rp-execution",
        risk_policy_version="1.0",
        risk_context_id=context.context_id,
        setup_id=discipline.setup_id,
        thesis_id=discipline.thesis_id,
        scenario_id=discipline.scenario_id,
        symbol=context.symbol,
        as_of=T0,
        available_at=T0,
        master_decision=proposal.decision,
        result=result,
        eligible_for_execution=passed,
        reason_codes=(RiskReason.PASSED if passed else RiskReason.SPREAD_LIMIT,),
        risk_fraction=0.005,
        risk_budget_amount=50.0 if passed else None,
        stop_distance_points=1000.0 if passed else None,
        approved_volume_lots=0.05 if passed else None,
        projected_gross_lots=0.05 if passed else None,
        projected_net_lots=(0.05 if signal is Signal.BUY else -0.05) if passed else None,
        estimated_margin_required=100.0 if passed else None,
        rationale="fixture risk outcome",
    )
    return proposal, discipline, context, risk


def _policy(mode: ExecutionMode):
    policy = default_execution_policy()
    return type(policy).model_validate(
        policy.model_dump() | {"policy_id": "", "mode": mode}
    )


def _intent(mode: ExecutionMode = ExecutionMode.DEMO_ENABLED):
    proposal, discipline, context, risk = _upstream()
    intent = build_execution_intent(proposal, discipline, risk, context, _policy(mode))
    assert intent is not None
    return proposal, discipline, context, risk, intent


def _observation(**changes: object) -> ExecutionObservation:
    values: dict[str, object] = {
        "observed_at": T0 + timedelta(seconds=1),
        "available_at": T0 + timedelta(seconds=1),
        "account_mode": ExecutionAccountMode.DEMO,
        "broker_symbol": "XAUUSD",
        "market_price": 2500.0,
        "spread_points": 2.0,
        "estimated_slippage_points": 1.0,
    }
    return ExecutionObservation.model_validate(values | changes)


class ScriptedTransport:
    def __init__(
        self,
        report: BrokerExecutionReport | None = None,
        error: Exception | None = None,
    ) -> None:
        self.report = report
        self.error = error
        self.calls = 0

    def submit(self, intent, observation):
        self.calls += 1
        if self.error is not None:
            raise self.error
        assert self.report is not None
        return self.report


def _report(status: ExecutionResultStatus, **changes: object) -> BrokerExecutionReport:
    filled = {
        ExecutionResultStatus.PARTIALLY_FILLED: 0.02,
        ExecutionResultStatus.FILLED: 0.05,
    }.get(status, 0.0)
    values: dict[str, object] = {
        "status": status,
        "event_time": T0 + timedelta(seconds=2),
        "observed_at": T0 + timedelta(seconds=2),
        "available_at": T0 + timedelta(seconds=2),
        "broker_ticket": 123456 if status is not ExecutionResultStatus.FAILED else None,
        "transport_execution_id": "demo-order-1",
        "filled_volume_lots": filled,
        "fill_price": 2500.02 if filled else None,
        "broker_retcode": "10009",
        "broker_status": status.value,
        "message": "scripted broker result",
    }
    return BrokerExecutionReport.model_validate(values | changes)


def _adapter(
    mode: ExecutionMode,
    transport: ScriptedTransport,
    *,
    ledger: InMemoryExecutionLedger | None = None,
    observation: ExecutionObservation | None = None,
) -> DemoExecutionAdapter:
    observed = observation or _observation()
    return DemoExecutionAdapter(
        policy=_policy(mode),
        ledger=ledger or InMemoryExecutionLedger(),
        observation_provider=lambda intent: observed,
        transport=transport,
    )


def test_risk_non_pass_produces_no_execution_intent() -> None:
    proposal, discipline, context, risk = _upstream(result=RiskResult.REJECT)

    intent = build_execution_intent(
        proposal, discipline, risk, context, default_execution_policy()
    )

    assert intent is None


def test_risk_pass_produces_deterministic_provenance_bound_intent() -> None:
    proposal, discipline, context, risk, first = _intent()
    second = build_execution_intent(
        proposal, discipline, risk, context, _policy(ExecutionMode.DEMO_ENABLED)
    )

    assert second == first
    assert second is not None
    assert second.intent_id == first.intent_id
    assert second.evidence_bundle_id == proposal.bundle_id
    assert second.master_proposal_id == proposal.proposal_id
    assert second.discipline_outcome_id == discipline.outcome_id
    assert second.risk_outcome_id == risk.outcome_id
    assert second.risk_context_id == context.context_id
    assert second.direction is Signal.BUY
    assert second.approved_volume_lots == 0.05
    assert second.requested_entry_price == 2500.0
    assert second.stop_loss_price == 2490.0
    assert second.take_profit_price is None
    assert second.order_type is ExecutionOrderType.MARKET


def test_execution_intent_cannot_silently_increase_upstream_volume() -> None:
    *_, intent = _intent()

    with pytest.raises(ValidationError, match="intent_id"):
        type(intent).model_validate(
            intent.model_dump() | {"approved_volume_lots": 0.06}
        )


def test_execution_is_disabled_by_default_and_dry_run_never_submits() -> None:
    transport = ScriptedTransport(_report(ExecutionResultStatus.SUBMITTED))
    *_, disabled_intent = _intent(ExecutionMode.DISABLED)
    disabled = _adapter(ExecutionMode.DISABLED, transport).execute(disabled_intent)
    *_, dry_intent = _intent(ExecutionMode.DRY_RUN)
    dry = _adapter(ExecutionMode.DRY_RUN, transport).execute(dry_intent)

    assert default_execution_policy().mode is ExecutionMode.DISABLED
    assert disabled.status is ExecutionResultStatus.NO_ACTION
    assert disabled.reason_code is ExecutionReason.EXECUTION_DISABLED
    assert dry.status is ExecutionResultStatus.NO_ACTION
    assert dry.reason_code is ExecutionReason.DRY_RUN
    assert transport.calls == 0


@pytest.mark.parametrize(
    "status",
    [ExecutionResultStatus.SUBMITTED, ExecutionResultStatus.ACCEPTED],
)
def test_successful_submission_and_acceptance_are_explicit(
    status: ExecutionResultStatus,
) -> None:
    transport = ScriptedTransport(_report(status))
    *_, intent = _intent()

    result = _adapter(ExecutionMode.DEMO_ENABLED, transport).execute(intent)

    assert result.status is status
    assert result.broker_ticket == 123456
    assert result.requested_volume_lots == 0.05
    assert result.filled_volume_lots == 0.0
    assert result.remaining_volume_lots == 0.05


def test_full_and_partial_fills_preserve_remaining_volume() -> None:
    *_, intent = _intent()
    full = _adapter(
        ExecutionMode.DEMO_ENABLED,
        ScriptedTransport(_report(ExecutionResultStatus.FILLED)),
    ).execute(intent)
    partial = _adapter(
        ExecutionMode.DEMO_ENABLED,
        ScriptedTransport(_report(ExecutionResultStatus.PARTIALLY_FILLED)),
    ).execute(intent)

    assert full.filled_volume_lots == 0.05
    assert full.remaining_volume_lots == 0.0
    assert partial.filled_volume_lots == 0.02
    assert partial.remaining_volume_lots == 0.03


def test_broker_rejection_remains_an_execution_result() -> None:
    transport = ScriptedTransport(
        _report(
            ExecutionResultStatus.REJECTED,
            broker_retcode="10016",
            broker_status="INVALID_STOPS",
            message="broker rejected stops",
        )
    )
    *_, intent = _intent()

    result = _adapter(ExecutionMode.DEMO_ENABLED, transport).execute(intent)

    assert result.status is ExecutionResultStatus.REJECTED
    assert result.reason_code is ExecutionReason.BROKER_REJECTED
    assert result.broker_status == "INVALID_STOPS"


def test_failed_transport_and_unknown_submission_are_distinct() -> None:
    *_, intent = _intent()
    failed = _adapter(
        ExecutionMode.DEMO_ENABLED,
        ScriptedTransport(error=TransportFailure("connection unavailable")),
    ).execute(intent)
    unknown_transport = ScriptedTransport(
        error=UnknownSubmissionState("request sent; acknowledgement lost")
    )
    unknown = _adapter(ExecutionMode.DEMO_ENABLED, unknown_transport).execute(intent)

    assert failed.status is ExecutionResultStatus.FAILED
    assert failed.reason_code is ExecutionReason.TRANSPORT_FAILED
    assert unknown.status is ExecutionResultStatus.UNKNOWN
    assert unknown.reason_code is ExecutionReason.UNKNOWN_SUBMISSION


def test_duplicate_intent_is_idempotent_and_never_resubmitted() -> None:
    transport = ScriptedTransport(_report(ExecutionResultStatus.ACCEPTED))
    ledger = InMemoryExecutionLedger()
    adapter = _adapter(ExecutionMode.DEMO_ENABLED, transport, ledger=ledger)
    *_, intent = _intent()

    first = adapter.execute(intent)
    second = adapter.execute(intent)

    assert second == first
    assert second.result_id == first.result_id
    assert transport.calls == 1


def test_duplicate_protection_survives_adapter_restart_with_shared_ledger() -> None:
    transport = ScriptedTransport(_report(ExecutionResultStatus.SUBMITTED))
    ledger = InMemoryExecutionLedger()
    *_, intent = _intent()
    first = _adapter(ExecutionMode.DEMO_ENABLED, transport, ledger=ledger).execute(intent)
    restarted = _adapter(ExecutionMode.DEMO_ENABLED, transport, ledger=ledger)

    second = restarted.execute(intent)

    assert second == first
    assert transport.calls == 1


def test_unknown_submission_is_not_resubmitted_without_reconciliation() -> None:
    transport = ScriptedTransport(error=UnknownSubmissionState("acknowledgement lost"))
    ledger = InMemoryExecutionLedger()
    adapter = _adapter(ExecutionMode.DEMO_ENABLED, transport, ledger=ledger)
    *_, intent = _intent()

    first = adapter.execute(intent)
    second = adapter.execute(intent)

    assert first.status is ExecutionResultStatus.UNKNOWN
    assert second == first
    assert transport.calls == 1


def test_live_account_and_pre_submit_condition_changes_reject_safely() -> None:
    transport = ScriptedTransport(_report(ExecutionResultStatus.SUBMITTED))
    *_, intent = _intent()
    live = _adapter(
        ExecutionMode.DEMO_ENABLED,
        transport,
        observation=_observation(account_mode=ExecutionAccountMode.LIVE),
    ).execute(intent)
    spread = _adapter(
        ExecutionMode.DEMO_ENABLED,
        transport,
        observation=_observation(spread_points=60.0),
    ).execute(intent)
    slippage = _adapter(
        ExecutionMode.DEMO_ENABLED,
        transport,
        observation=_observation(estimated_slippage_points=11.0),
    ).execute(intent)
    moved = _adapter(
        ExecutionMode.DEMO_ENABLED,
        transport,
        observation=_observation(market_price=2500.2),
    ).execute(intent)

    assert live.reason_code is ExecutionReason.LIVE_ACCOUNT_BLOCKED
    assert spread.reason_code is ExecutionReason.SPREAD_LIMIT
    assert slippage.reason_code is ExecutionReason.SLIPPAGE_LIMIT
    assert moved.reason_code is ExecutionReason.PRICE_DEVIATION_LIMIT
    assert transport.calls == 0


def test_realized_slippage_and_ticket_provenance_are_retained() -> None:
    *_, intent = _intent()
    result = _adapter(
        ExecutionMode.DEMO_ENABLED,
        ScriptedTransport(_report(ExecutionResultStatus.FILLED)),
    ).execute(intent)

    assert result.execution_intent_id == intent.intent_id
    assert result.risk_outcome_id == intent.risk_outcome_id
    assert result.broker_ticket == 123456
    assert result.requested_price == 2500.0
    assert result.fill_price == 2500.02
    assert result.realized_slippage_points == 2.0
    assert result.actual_spread_points == 2.0


@pytest.mark.parametrize(
    ("result_status", "feedback_status"),
    [
        (ExecutionResultStatus.ACCEPTED, ExecutionStatus.ACCEPTED),
        (ExecutionResultStatus.PARTIALLY_FILLED, ExecutionStatus.PARTIALLY_FILLED),
        (ExecutionResultStatus.FILLED, ExecutionStatus.FILLED),
        (ExecutionResultStatus.REJECTED, ExecutionStatus.REJECTED),
        (ExecutionResultStatus.CANCELLED, ExecutionStatus.CANCELLED),
        (ExecutionResultStatus.EXPIRED, ExecutionStatus.EXPIRED),
        (ExecutionResultStatus.FAILED, ExecutionStatus.FAILED),
        (ExecutionResultStatus.UNKNOWN, ExecutionStatus.UNKNOWN),
    ],
)
def test_execution_result_converts_to_existing_runtime_feedback_path(
    result_status: ExecutionResultStatus,
    feedback_status: ExecutionStatus,
) -> None:
    *_, intent = _intent()
    if result_status is ExecutionResultStatus.UNKNOWN:
        transport = ScriptedTransport(error=UnknownSubmissionState("ack lost"))
    elif result_status is ExecutionResultStatus.FAILED:
        transport = ScriptedTransport(error=TransportFailure("not sent"))
    else:
        transport = ScriptedTransport(_report(result_status))
    result = _adapter(ExecutionMode.DEMO_ENABLED, transport).execute(intent)

    event = execution_result_to_runtime_event(
        result,
        source="execution-adapter",
        source_version="1.0",
        source_sequence=1,
    )

    assert event is not None
    assert event.event_type is RuntimeEventType.EXECUTION_FEEDBACK
    assert event.payload.status is feedback_status
    assert event.payload.instruction_id == intent.intent_id
    assert event.payload.spread_points == result.actual_spread_points
    state = reduce_state(
        initial_runtime_state("XAUUSD", at=T0 - timedelta(seconds=1)),
        event,
        now=event.available_at,
    )
    assert state.latest_execution_feedback == event.payload


def test_no_action_result_does_not_create_runtime_feedback_event() -> None:
    *_, intent = _intent(ExecutionMode.DISABLED)
    result = _adapter(
        ExecutionMode.DISABLED,
        ScriptedTransport(_report(ExecutionResultStatus.SUBMITTED)),
    ).execute(intent)

    assert execution_result_to_runtime_event(
        result,
        source="execution-adapter",
        source_version="1.0",
        source_sequence=1,
    ) is None


def test_master_discipline_and_risk_records_remain_immutable() -> None:
    proposal, discipline, context, risk = _upstream()
    before = (
        proposal.model_dump_json(),
        discipline.model_dump_json(),
        risk.model_dump_json(),
    )

    build_execution_intent(
        proposal, discipline, risk, context, _policy(ExecutionMode.DEMO_ENABLED)
    )

    assert before == (
        proposal.model_dump_json(),
        discipline.model_dump_json(),
        risk.model_dump_json(),
    )


def test_execution_contracts_exclude_models_bypasses_and_position_management() -> None:
    *_, intent = _intent()
    result = _adapter(
        ExecutionMode.DEMO_ENABLED,
        ScriptedTransport(_report(ExecutionResultStatus.ACCEPTED)),
    ).execute(intent)

    forbidden = (
        "model",
        "agent_evidence",
        "bypass_risk",
        "trailing_stop",
        "break_even",
        "scale_in",
    )
    for field in forbidden:
        with pytest.raises(ValidationError):
            type(intent).model_validate(intent.model_dump() | {field: True})
        with pytest.raises(ValidationError):
            ExecutionResult.model_validate(result.model_dump() | {field: True})


def test_serialized_intent_is_shared_by_live_and_future_replay_adapters() -> None:
    *_, intent = _intent()
    replay_input = type(intent).model_validate_json(intent.model_dump_json())

    assert replay_input == intent
    assert replay_input.intent_id == intent.intent_id
