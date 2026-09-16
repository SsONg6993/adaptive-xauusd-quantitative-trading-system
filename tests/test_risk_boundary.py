from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.agents import AgentStatus, DirectionalBias, HypothesisRelationship
from axq.discipline import (
    DisciplineContext,
    DisciplineOutcome,
    DisciplineState,
    default_demo_discipline_policy,
    evaluate_discipline,
)
from axq.master import EvidenceDisposition, FusionReason, MasterProposal, SpecialistContribution
from axq.risk_boundary import (
    RiskContext,
    RiskOutcome,
    RiskReason,
    RiskResult,
    default_demo_risk_policy,
    evaluate_risk,
)
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    ExposureState,
    FreshnessStatus,
    MarketState,
    OrderBookState,
    OrderState,
    OrderType,
    PositionBookState,
    PositionSide,
    PositionState,
)
from axq.runtime.kernel import AGENT_ORDER
from axq.schemas import Signal

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)


def _fresh(component: str, status: FreshnessStatus = FreshnessStatus.AVAILABLE):
    if status in {FreshnessStatus.UNKNOWN, FreshnessStatus.UNAVAILABLE}:
        return ComponentFreshness(
            component=component,
            status=status,
            reason="not synchronized" if status is FreshnessStatus.UNAVAILABLE else None,
        )
    return ComponentFreshness(
        component=component,
        status=status,
        observed_at=T0,
        available_at=T0,
        stale_after_ms=15_000,
    )


def _proposal(signal: Signal = Signal.BUY) -> MasterProposal:
    direction = DirectionalBias.BULLISH if signal is Signal.BUY else DirectionalBias.BEARISH
    contributions = tuple(
        SpecialistContribution(
            agent_name=name,
            evidence_id=f"ae-{name}",
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
        bundle_id="eb-risk",
        event_id="ev-risk",
        runtime_state_id="state-risk",
        as_of=T0,
        policy_id="mfp-risk",
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
        contributing_evidence_ids=("ae-chart",),
        contributions=contributions,
        reason_codes=(
            FusionReason.ACTIONABLE_BUY if signal is Signal.BUY else FusionReason.ACTIONABLE_SELL,
        ),
    )


def _discipline(proposal: MasterProposal, *, reject: bool = False) -> DisciplineOutcome:
    policy = default_demo_discipline_policy()
    state = DisciplineState(
        policy_id=policy.policy_id,
        as_of=T0,
        available_at=T0,
        trading_day=T0.date(),
        session_id="london",
        trades_today=0,
        trades_this_session=0,
        consecutive_losses=0,
        recently_executed_setup_ids=("setup-risk",) if reject else (),
    )
    context = DisciplineContext(
        as_of=T0,
        available_at=T0,
        trading_day=T0.date(),
        session_id="london",
        setup_id="setup-risk",
        thesis_id="thesis-risk",
        scenario_id="scenario-risk",
        thesis_relationship=HypothesisRelationship.NEW,
    )
    return evaluate_discipline(proposal, context, state, policy)


def _account(
    *,
    status: FreshnessStatus = FreshnessStatus.AVAILABLE,
    **changes: object,
) -> AccountState:
    known: dict[str, object] = {
        "currency": "USD",
        "balance": 10_000.0,
        "equity": 10_000.0,
        "free_margin": 9_000.0,
        "used_margin": 1_000.0,
        "margin_level": 1_000.0,
        "floating_pnl": 0.0,
        "daily_realized_pnl": 0.0,
        "daily_unrealized_pnl": 0.0,
        "daily_drawdown": 0.0,
        "total_drawdown": 0.0,
    }
    if status in {FreshnessStatus.UNKNOWN, FreshnessStatus.UNAVAILABLE}:
        known = {}
    return AccountState(
        source="mt5",
        account_id="demo-account",
        as_of=T0,
        freshness=_fresh("account", status),
        **(known | changes),
    )


def _market(**changes: object) -> MarketState:
    values: dict[str, object] = {
        "source": "mt5",
        "symbol": "XAUUSD",
        "as_of": T0,
        "freshness": _fresh("market"),
        "bid": 2499.99,
        "ask": 2500.01,
        "last": 2500.0,
        "spread_points": 2.0,
    }
    return MarketState.model_validate(values | changes)


def _positions(*positions: PositionState, **changes: object) -> PositionBookState:
    values: dict[str, object] = {
        "source": "mt5",
        "as_of": T0,
        "freshness": _fresh("positions"),
        "positions": positions,
    }
    return PositionBookState.model_validate(values | changes)


def _orders(*orders: OrderState, **changes: object) -> OrderBookState:
    values: dict[str, object] = {
        "source": "mt5",
        "as_of": T0,
        "freshness": _fresh("orders"),
        "orders": orders,
    }
    return OrderBookState.model_validate(values | changes)


def _exposure(**changes: object) -> ExposureState:
    values: dict[str, object] = {
        "as_of": T0,
        "freshness": _fresh("exposure"),
        "gross_lots": 0.0,
        "net_lots": 0.0,
        "gross_notional": 0.0,
        "net_notional": 0.0,
    }
    return ExposureState.model_validate(values | changes)


def _broker(**changes: object) -> BrokerConstraints:
    values: dict[str, object] = {
        "source": "mt5",
        "symbol": "XAUUSD",
        "as_of": T0,
        "freshness": _fresh("broker_constraints"),
        "trade_allowed": True,
        "volume_min": 0.01,
        "volume_max": 10.0,
        "volume_step": 0.01,
        "point_size": 0.01,
        "tick_size": 0.01,
        "tick_value_loss": 1.0,
        "stops_level_points": 10.0,
        "freeze_level_points": 0.0,
    }
    return BrokerConstraints.model_validate(values | changes)


def _context(**changes: object) -> RiskContext:
    values: dict[str, object] = {
        "as_of": T0,
        "available_at": T0,
        "symbol": "XAUUSD",
        "account": _account(),
        "market": _market(),
        "positions": _positions(),
        "orders": _orders(),
        "exposure": _exposure(),
        "broker_constraints": _broker(),
        "entry_price": 2500.0,
        "stop_loss_price": 2490.0,
        "estimated_margin_required": 100.0,
        "estimated_slippage_points": 1.0,
        "daily_drawdown_fraction": 0.0,
        "total_drawdown_fraction": 0.0,
        "kill_switch_active": False,
    }
    return RiskContext.model_validate(values | changes)


def _evaluate(
    *,
    proposal: MasterProposal | None = None,
    discipline: DisciplineOutcome | None = None,
    context: RiskContext | None = None,
):
    proposal = proposal or _proposal()
    discipline = discipline or _discipline(proposal)
    return evaluate_risk(proposal, discipline, context or _context(), default_demo_risk_policy())


def test_non_pass_discipline_produces_no_action() -> None:
    proposal = _proposal()
    outcome = _evaluate(proposal=proposal, discipline=_discipline(proposal, reject=True))

    assert outcome.result is RiskResult.NO_ACTION
    assert outcome.eligible_for_execution is False


def test_valid_account_and_risk_state_passes_with_deterministic_sizing() -> None:
    outcome = _evaluate()

    assert outcome.result is RiskResult.PASS
    assert outcome.approved_volume_lots == 0.05
    assert outcome.risk_budget_amount == 50.0
    assert outcome.stop_distance_points == 1000.0
    assert outcome.eligible_for_execution is True


@pytest.mark.parametrize("status", [FreshnessStatus.STALE, FreshnessStatus.UNKNOWN])
def test_stale_or_unknown_account_fails_safely(status: FreshnessStatus) -> None:
    outcome = _evaluate(context=_context(account=_account(status=status)))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.ACCOUNT_NOT_FRESH in outcome.reason_codes


def test_available_account_with_unknown_financial_values_is_rejected() -> None:
    account = _account(balance=None, equity=None, free_margin=None, margin_level=None)
    outcome = _evaluate(context=_context(account=account))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.MISSING_ACCOUNT_VALUES in outcome.reason_codes


def test_stale_market_and_corrupt_account_fail_closed() -> None:
    stale_market = _market(freshness=_fresh("market", FreshnessStatus.STALE))
    corrupt_account = _account(free_margin=8_000.0, used_margin=1_000.0)

    stale = _evaluate(context=_context(market=stale_market))
    corrupt = _evaluate(context=_context(account=corrupt_account))

    assert RiskReason.MARKET_NOT_FRESH in stale.reason_codes
    assert RiskReason.ACCOUNT_INCONSISTENT in corrupt.reason_codes


def test_insufficient_free_margin_is_rejected() -> None:
    outcome = _evaluate(context=_context(account=_account(free_margin=100.0)))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.INSUFFICIENT_FREE_MARGIN in outcome.reason_codes


def test_margin_level_violation_is_rejected() -> None:
    outcome = _evaluate(context=_context(account=_account(margin_level=150.0)))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.MARGIN_LEVEL_LIMIT in outcome.reason_codes


@pytest.mark.parametrize(
    ("account", "reason"),
    [
        (_account(daily_drawdown=250.0), RiskReason.DAILY_DRAWDOWN_LIMIT),
        (_account(total_drawdown=1_100.0), RiskReason.TOTAL_DRAWDOWN_LIMIT),
    ],
)
def test_non_emergency_drawdown_limits_reject(
    account: AccountState, reason: RiskReason
) -> None:
    fractions = (
        {"daily_drawdown_fraction": 0.025}
        if reason is RiskReason.DAILY_DRAWDOWN_LIMIT
        else {"total_drawdown_fraction": 0.11}
    )
    outcome = _evaluate(context=_context(account=account, **fractions))

    assert outcome.result is RiskResult.REJECT
    assert reason in outcome.reason_codes


@pytest.mark.parametrize(
    "changes",
    [
        {
            "account": _account(daily_drawdown=500.0),
            "daily_drawdown_fraction": 0.05,
        },
        {
            "account": _account(total_drawdown=1_600.0),
            "total_drawdown_fraction": 0.16,
        },
        {"kill_switch_active": True},
    ],
)
def test_emergency_thresholds_and_kill_switch_stop_explicitly(
    changes: dict[str, object],
) -> None:
    outcome = _evaluate(context=_context(**changes))

    assert outcome.result is RiskResult.EMERGENCY_STOP
    assert outcome.eligible_for_execution is False


def test_projected_exposure_limit_is_rejected() -> None:
    context = _context(exposure=_exposure(gross_lots=0.98, net_lots=0.98))
    outcome = _evaluate(context=context)

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.GROSS_EXPOSURE_LIMIT in outcome.reason_codes


def test_projected_net_exposure_limit_is_independently_enforced() -> None:
    policy = default_demo_risk_policy()
    net_limited = type(policy).model_validate(
        policy.model_dump() | {"policy_id": "", "max_gross_lots": 2.0}
    )
    proposal = _proposal()
    outcome = evaluate_risk(
        proposal,
        _discipline(proposal),
        _context(exposure=_exposure(gross_lots=0.98, net_lots=0.98)),
        net_limited,
    )

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.GROSS_EXPOSURE_LIMIT not in outcome.reason_codes
    assert RiskReason.NET_EXPOSURE_LIMIT in outcome.reason_codes


def test_maximum_open_financial_positions_is_rejected() -> None:
    position = PositionState(
        source="mt5",
        broker_ticket=123,
        symbol="XAUUSD",
        side=PositionSide.SELL,
        volume_lots=0.1,
        opened_at=T0 - timedelta(minutes=5),
        open_price=2501.0,
    )
    outcome = _evaluate(context=_context(positions=_positions(position)))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.POSITION_LIMIT in outcome.reason_codes


def test_pending_order_limit_is_a_financial_commitment_veto() -> None:
    order = OrderState(
        source="mt5",
        broker_ticket=456,
        symbol="XAUUSD",
        order_type=OrderType.BUY_STOP,
        volume_lots=0.1,
        created_at=T0 - timedelta(minutes=5),
        price=2505.0,
    )
    outcome = _evaluate(context=_context(orders=_orders(order)))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.PENDING_ORDER_LIMIT in outcome.reason_codes


def test_spread_and_slippage_limits_reject() -> None:
    spread = _evaluate(context=_context(market=_market(spread_points=60.0)))
    slippage = _evaluate(context=_context(estimated_slippage_points=20.0))

    assert RiskReason.SPREAD_LIMIT in spread.reason_codes
    assert RiskReason.SLIPPAGE_LIMIT in slippage.reason_codes


def test_unavailable_broker_constraints_fail_safely() -> None:
    broker = _broker(
        freshness=_fresh("broker_constraints", FreshnessStatus.UNAVAILABLE),
        trade_allowed=None,
        volume_min=None,
        volume_max=None,
        volume_step=None,
        point_size=None,
        tick_size=None,
        tick_value_loss=None,
        stops_level_points=None,
        freeze_level_points=None,
    )
    outcome = _evaluate(context=_context(broker_constraints=broker))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.BROKER_CONSTRAINTS_NOT_FRESH in outcome.reason_codes


def test_invalid_stop_side_and_broker_minimum_stop_are_rejected() -> None:
    invalid_side = _evaluate(context=_context(stop_loss_price=2501.0))
    below_minimum = _evaluate(context=_context(stop_loss_price=2499.95))

    assert RiskReason.INVALID_STOP_DIRECTION in invalid_side.reason_codes
    assert RiskReason.BROKER_STOP_LEVEL in below_minimum.reason_codes


def test_broker_trade_and_freeze_constraints_are_hard_vetoes() -> None:
    disabled = _evaluate(context=_context(broker_constraints=_broker(trade_allowed=False)))
    frozen = _evaluate(
        context=_context(
            stop_loss_price=2499.8,
            broker_constraints=_broker(stops_level_points=10.0, freeze_level_points=25.0),
        )
    )

    assert RiskReason.BROKER_TRADING_DISABLED in disabled.reason_codes
    assert RiskReason.BROKER_FREEZE_LEVEL in frozen.reason_codes


def test_lot_step_and_policy_maximum_are_normalized_down() -> None:
    stepped = _evaluate(
        context=_context(
            stop_loss_price=2497.0,
            broker_constraints=_broker(volume_step=0.05),
        )
    )
    policy = default_demo_risk_policy()
    capped_policy = type(policy).model_validate(
        policy.model_dump() | {"policy_id": "", "max_approved_volume_lots": 0.03}
    )
    proposal = _proposal()
    capped = evaluate_risk(proposal, _discipline(proposal), _context(), capped_policy)
    broker_capped = _evaluate(context=_context(broker_constraints=_broker(volume_max=0.03)))

    assert stepped.approved_volume_lots == 0.15
    assert capped.approved_volume_lots == 0.03
    assert broker_capped.approved_volume_lots == 0.03


def test_volume_below_broker_minimum_is_rejected_not_guessed() -> None:
    policy = default_demo_risk_policy()
    tiny_policy = type(policy).model_validate(
        policy.model_dump() | {"policy_id": "", "risk_fraction_per_trade": 0.0001}
    )
    proposal = _proposal()
    outcome = evaluate_risk(proposal, _discipline(proposal), _context(), tiny_policy)

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.VOLUME_BELOW_MINIMUM in outcome.reason_codes


@pytest.mark.parametrize("missing", ["entry_price", "stop_loss_price", "estimated_margin_required"])
def test_missing_sizing_inputs_are_journalable_rejections(missing: str) -> None:
    outcome = _evaluate(context=_context(**{missing: None}))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.MISSING_SIZING_INPUTS in outcome.reason_codes


def test_missing_slippage_fact_is_not_guessed() -> None:
    outcome = _evaluate(context=_context(estimated_slippage_points=None))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.SLIPPAGE_UNAVAILABLE in outcome.reason_codes


def test_policy_and_outcome_identities_are_content_addressed() -> None:
    policy = default_demo_risk_policy()
    same = type(policy).model_validate_json(policy.model_dump_json())
    changed = type(policy).model_validate(
        policy.model_dump() | {"policy_id": "", "max_spread_points": 51.0}
    )
    first = _evaluate()
    second = _evaluate()

    assert same.policy_id == policy.policy_id
    assert changed.policy_id != policy.policy_id
    assert second.outcome_id == first.outcome_id


def test_live_and_replay_equivalent_inputs_have_identical_outcomes() -> None:
    proposal = _proposal()
    discipline = _discipline(proposal)
    context = _context()
    policy = default_demo_risk_policy()
    live = evaluate_risk(proposal, discipline, context, policy)
    replay = evaluate_risk(
        MasterProposal.model_validate_json(proposal.model_dump_json()),
        DisciplineOutcome.model_validate_json(discipline.model_dump_json()),
        RiskContext.model_validate_json(context.model_dump_json()),
        type(policy).model_validate_json(policy.model_dump_json()),
    )

    assert replay == live
    assert replay.outcome_id == live.outcome_id


def test_master_and_discipline_are_not_mutated() -> None:
    proposal = _proposal()
    discipline = _discipline(proposal)
    before_proposal = proposal.model_dump_json()
    before_discipline = discipline.model_dump_json()

    evaluate_risk(proposal, discipline, _context(), default_demo_risk_policy())

    assert proposal.model_dump_json() == before_proposal
    assert discipline.model_dump_json() == before_discipline


def test_risk_contracts_reject_execution_agent_and_model_fields() -> None:
    context = _context()
    outcome = _evaluate()

    for forbidden in ("broker_order", "execution_authorization", "agent_evidence", "model"):
        with pytest.raises(ValidationError):
            RiskContext.model_validate(context.model_dump() | {forbidden: "forbidden"})
        with pytest.raises(ValidationError):
            RiskOutcome.model_validate(outcome.model_dump() | {forbidden: "forbidden"})


def test_restart_state_that_is_not_fresh_fails_closed() -> None:
    old = T0 - timedelta(minutes=5)
    freshness = ComponentFreshness(
        component="account",
        status=FreshnessStatus.AVAILABLE,
        observed_at=old,
        available_at=old,
        stale_after_ms=15_000,
    )
    account = AccountState.model_validate(_account().model_dump() | {"freshness": freshness})
    outcome = _evaluate(context=_context(account=account))

    assert outcome.result is RiskResult.REJECT
    assert RiskReason.ACCOUNT_NOT_FRESH in outcome.reason_codes


def test_future_component_availability_is_rejected_by_the_context_contract() -> None:
    future_freshness = ComponentFreshness(
        component="account",
        status=FreshnessStatus.AVAILABLE,
        observed_at=T0,
        available_at=T0 + timedelta(seconds=1),
        stale_after_ms=15_000,
    )
    account = AccountState.model_validate(
        _account().model_dump() | {"freshness": future_freshness}
    )

    with pytest.raises(ValidationError, match="future availability"):
        _context(account=account)
