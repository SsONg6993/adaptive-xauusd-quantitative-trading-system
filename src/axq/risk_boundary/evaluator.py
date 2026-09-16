"""Pure deterministic financial and safety veto evaluation."""

from __future__ import annotations

from datetime import datetime

from axq.discipline import DisciplineOutcome, DisciplineResult
from axq.master import MasterProposal
from axq.risk import calculate_volume_lots
from axq.risk_boundary.contracts import (
    RiskContext,
    RiskOutcome,
    RiskPolicy,
    RiskReason,
    RiskResult,
)
from axq.runtime import ComponentFreshness, FreshnessStatus
from axq.schemas import Signal


def default_demo_risk_policy() -> RiskPolicy:
    """Return conservative Demo safety defaults, not optimized trading truth."""
    return RiskPolicy(
        policy_version="demo-v1",
        risk_fraction_per_trade=0.005,
        max_daily_drawdown_fraction=0.02,
        emergency_daily_drawdown_fraction=0.04,
        max_total_drawdown_fraction=0.10,
        emergency_total_drawdown_fraction=0.15,
        minimum_margin_level=200.0,
        free_margin_buffer_fraction=0.10,
        max_open_positions=1,
        max_pending_orders=0,
        max_gross_lots=1.0,
        max_abs_net_lots=1.0,
        max_spread_points=50.0,
        max_slippage_points=10.0,
        max_component_age_seconds=15.0,
        minimum_stop_distance_points=10.0,
        max_approved_volume_lots=10.0,
        account_consistency_tolerance_fraction=0.05,
    )


def _outcome(
    proposal: MasterProposal,
    discipline: DisciplineOutcome,
    context: RiskContext,
    policy: RiskPolicy,
    *,
    result: RiskResult,
    reasons: tuple[RiskReason, ...],
    rationale: str,
    risk_budget_amount: float | None = None,
    stop_distance_points: float | None = None,
    approved_volume_lots: float | None = None,
    projected_gross_lots: float | None = None,
    projected_net_lots: float | None = None,
    estimated_margin_required: float | None = None,
) -> RiskOutcome:
    return RiskOutcome(
        master_proposal_id=proposal.proposal_id,
        evidence_bundle_id=proposal.bundle_id,
        discipline_outcome_id=discipline.outcome_id,
        discipline_result=discipline.result,
        risk_policy_id=policy.policy_id,
        risk_policy_version=policy.policy_version,
        risk_context_id=context.context_id,
        setup_id=discipline.setup_id,
        thesis_id=discipline.thesis_id,
        scenario_id=discipline.scenario_id,
        symbol=context.symbol,
        as_of=proposal.as_of,
        available_at=max(discipline.available_at, context.available_at),
        master_decision=proposal.decision,
        result=result,
        eligible_for_execution=result is RiskResult.PASS,
        reason_codes=reasons,
        risk_fraction=(
            policy.risk_fraction_per_trade if result is not RiskResult.NO_ACTION else 0.0
        ),
        risk_budget_amount=risk_budget_amount,
        stop_distance_points=stop_distance_points,
        approved_volume_lots=approved_volume_lots,
        projected_gross_lots=projected_gross_lots,
        projected_net_lots=projected_net_lots,
        estimated_margin_required=estimated_margin_required,
        rationale=rationale,
    )


def _is_fresh(
    freshness: ComponentFreshness,
    state_as_of: datetime,
    evaluation_time: datetime,
    max_age_seconds: float,
) -> bool:
    if freshness.status is not FreshnessStatus.AVAILABLE:
        return False
    if freshness.available_at is None:
        return False
    return (
        evaluation_time - freshness.available_at
    ).total_seconds() <= max_age_seconds and (
        evaluation_time - state_as_of
    ).total_seconds() <= max_age_seconds


def _deduplicate(reasons: list[RiskReason]) -> tuple[RiskReason, ...]:
    return tuple(dict.fromkeys(reasons))


def evaluate_risk(
    proposal: MasterProposal,
    discipline: DisciplineOutcome,
    context: RiskContext,
    policy: RiskPolicy,
) -> RiskOutcome:
    """Apply final financial safety vetoes without authorizing broker execution."""
    if discipline.master_proposal_id != proposal.proposal_id:
        raise ValueError("Discipline outcome does not belong to Master proposal")
    if discipline.evidence_bundle_id != proposal.bundle_id:
        raise ValueError("Discipline and Master evidence bundle identities differ")
    if discipline.as_of != proposal.as_of or context.as_of != proposal.as_of:
        raise ValueError("Risk inputs must share one causal as_of")
    if discipline.master_decision is not proposal.decision:
        raise ValueError("Discipline and Master decisions differ")

    if discipline.result is not DisciplineResult.PASS:
        return _outcome(
            proposal,
            discipline,
            context,
            policy,
            result=RiskResult.NO_ACTION,
            reasons=(RiskReason.DISCIPLINE_NOT_PASSED,),
            rationale="Only a Discipline PASS may enter financial Risk evaluation.",
        )

    if context.kill_switch_active:
        return _outcome(
            proposal,
            discipline,
            context,
            policy,
            result=RiskResult.EMERGENCY_STOP,
            reasons=(RiskReason.KILL_SWITCH,),
            rationale="The deterministic kill switch is active.",
        )

    account = context.account
    emergency_reasons: list[RiskReason] = []
    if context.daily_drawdown_fraction >= policy.emergency_daily_drawdown_fraction:
        emergency_reasons.append(RiskReason.EMERGENCY_DAILY_DRAWDOWN)
    if context.total_drawdown_fraction >= policy.emergency_total_drawdown_fraction:
        emergency_reasons.append(RiskReason.EMERGENCY_TOTAL_DRAWDOWN)
    if emergency_reasons:
        return _outcome(
            proposal,
            discipline,
            context,
            policy,
            result=RiskResult.EMERGENCY_STOP,
            reasons=_deduplicate(emergency_reasons),
            rationale="An emergency account drawdown threshold is reached.",
        )

    reasons: list[RiskReason] = []
    freshness_checks = (
        (
            account.freshness,
            account.as_of,
            RiskReason.ACCOUNT_NOT_FRESH,
        ),
        (
            context.market.freshness,
            context.market.as_of,
            RiskReason.MARKET_NOT_FRESH,
        ),
        (
            context.positions.freshness,
            context.positions.as_of,
            RiskReason.POSITION_BOOK_NOT_FRESH,
        ),
        (
            context.orders.freshness,
            context.orders.as_of,
            RiskReason.ORDER_BOOK_NOT_FRESH,
        ),
        (
            context.exposure.freshness,
            context.exposure.as_of,
            RiskReason.EXPOSURE_NOT_FRESH,
        ),
        (
            context.broker_constraints.freshness,
            context.broker_constraints.as_of,
            RiskReason.BROKER_CONSTRAINTS_NOT_FRESH,
        ),
    )
    for freshness, state_as_of, reason in freshness_checks:
        if not _is_fresh(
            freshness,
            state_as_of,
            proposal.as_of,
            policy.max_component_age_seconds,
        ):
            reasons.append(reason)

    required_account_values = (
        account.balance,
        account.equity,
        account.free_margin,
        account.used_margin,
        account.margin_level,
        account.daily_drawdown,
        account.total_drawdown,
    )
    if any(value is None for value in required_account_values):
        reasons.append(RiskReason.MISSING_ACCOUNT_VALUES)

    broker = context.broker_constraints
    required_broker_values = (
        broker.trade_allowed,
        broker.volume_min,
        broker.volume_max,
        broker.volume_step,
        broker.point_size,
        broker.tick_size,
        broker.tick_value_loss,
        broker.stops_level_points,
        broker.freeze_level_points,
    )
    if any(value is None for value in required_broker_values):
        reasons.append(RiskReason.MISSING_BROKER_VALUES)

    exposure = context.exposure
    if exposure.gross_lots is None or exposure.net_lots is None:
        reasons.append(RiskReason.MISSING_EXPOSURE_VALUES)
    if context.market.spread_points is None:
        reasons.append(RiskReason.SPREAD_UNAVAILABLE)
    if any(
        value is None
        for value in (
            context.entry_price,
            context.stop_loss_price,
            context.estimated_margin_required,
        )
    ):
        reasons.append(RiskReason.MISSING_SIZING_INPUTS)
    if context.estimated_slippage_points is None:
        reasons.append(RiskReason.SLIPPAGE_UNAVAILABLE)

    if reasons:
        return _outcome(
            proposal,
            discipline,
            context,
            policy,
            result=RiskResult.REJECT,
            reasons=_deduplicate(reasons),
            rationale="Required financial or broker state is unavailable or stale.",
        )

    assert account.balance is not None
    assert account.equity is not None
    assert account.free_margin is not None
    assert account.used_margin is not None
    assert account.margin_level is not None
    assert account.daily_drawdown is not None
    assert account.total_drawdown is not None
    assert broker.trade_allowed is not None
    assert broker.volume_min is not None
    assert broker.volume_max is not None
    assert broker.volume_step is not None
    assert broker.point_size is not None
    assert broker.tick_size is not None
    assert broker.tick_value_loss is not None
    assert broker.stops_level_points is not None
    assert broker.freeze_level_points is not None
    assert exposure.gross_lots is not None
    assert exposure.net_lots is not None
    assert context.market.spread_points is not None
    assert context.entry_price is not None
    assert context.stop_loss_price is not None
    assert context.estimated_margin_required is not None
    assert context.estimated_slippage_points is not None

    if account.balance <= 0 or account.equity <= 0:
        reasons.append(RiskReason.ACCOUNT_INCONSISTENT)
    account_difference = abs(account.free_margin + account.used_margin - account.equity)
    if account_difference > max(account.equity, 1.0) * (
        policy.account_consistency_tolerance_fraction
    ):
        reasons.append(RiskReason.ACCOUNT_INCONSISTENT)
    if account.free_margin < context.estimated_margin_required * (
        1.0 + policy.free_margin_buffer_fraction
    ):
        reasons.append(RiskReason.INSUFFICIENT_FREE_MARGIN)
    if account.margin_level < policy.minimum_margin_level:
        reasons.append(RiskReason.MARGIN_LEVEL_LIMIT)

    if context.daily_drawdown_fraction >= policy.max_daily_drawdown_fraction:
        reasons.append(RiskReason.DAILY_DRAWDOWN_LIMIT)
    if context.total_drawdown_fraction >= policy.max_total_drawdown_fraction:
        reasons.append(RiskReason.TOTAL_DRAWDOWN_LIMIT)
    if len(context.positions.positions) >= policy.max_open_positions:
        reasons.append(RiskReason.POSITION_LIMIT)
    if len(context.orders.orders) > policy.max_pending_orders:
        reasons.append(RiskReason.PENDING_ORDER_LIMIT)
    if context.market.spread_points > policy.max_spread_points:
        reasons.append(RiskReason.SPREAD_LIMIT)
    if context.estimated_slippage_points > policy.max_slippage_points:
        reasons.append(RiskReason.SLIPPAGE_LIMIT)
    if not broker.trade_allowed:
        reasons.append(RiskReason.BROKER_TRADING_DISABLED)

    stop_is_valid = (
        proposal.decision is Signal.BUY and context.stop_loss_price < context.entry_price
    ) or (
        proposal.decision is Signal.SELL and context.stop_loss_price > context.entry_price
    )
    if not stop_is_valid:
        reasons.append(RiskReason.INVALID_STOP_DIRECTION)
    stop_distance_price = abs(context.entry_price - context.stop_loss_price)
    stop_distance_points = stop_distance_price / broker.point_size
    if stop_distance_points < policy.minimum_stop_distance_points:
        reasons.append(RiskReason.MINIMUM_STOP_DISTANCE)
    if stop_distance_points < broker.stops_level_points:
        reasons.append(RiskReason.BROKER_STOP_LEVEL)
    if stop_distance_points < broker.freeze_level_points:
        reasons.append(RiskReason.BROKER_FREEZE_LEVEL)

    if reasons:
        return _outcome(
            proposal,
            discipline,
            context,
            policy,
            result=RiskResult.REJECT,
            reasons=_deduplicate(reasons),
            rationale="One or more deterministic financial safety limits rejected the proposal.",
        )

    volume = calculate_volume_lots(
        equity=account.equity,
        risk_fraction=policy.risk_fraction_per_trade,
        stop_distance_price=stop_distance_price,
        tick_size=broker.tick_size,
        tick_value_loss=broker.tick_value_loss,
        volume_min=broker.volume_min,
        volume_max=min(broker.volume_max, policy.max_approved_volume_lots),
        volume_step=broker.volume_step,
    )
    if volume == 0.0:
        return _outcome(
            proposal,
            discipline,
            context,
            policy,
            result=RiskResult.REJECT,
            reasons=(RiskReason.VOLUME_BELOW_MINIMUM,),
            rationale="Risk-budget sizing is below the broker minimum volume.",
        )

    signed_volume = volume if proposal.decision is Signal.BUY else -volume
    projected_gross_lots = exposure.gross_lots + volume
    projected_net_lots = exposure.net_lots + signed_volume
    if projected_gross_lots > policy.max_gross_lots:
        reasons.append(RiskReason.GROSS_EXPOSURE_LIMIT)
    if abs(projected_net_lots) > policy.max_abs_net_lots:
        reasons.append(RiskReason.NET_EXPOSURE_LIMIT)
    if reasons:
        return _outcome(
            proposal,
            discipline,
            context,
            policy,
            result=RiskResult.REJECT,
            reasons=_deduplicate(reasons),
            rationale="The sized proposal would exceed configured financial exposure.",
        )

    return _outcome(
        proposal,
        discipline,
        context,
        policy,
        result=RiskResult.PASS,
        reasons=(RiskReason.PASSED,),
        rationale="The proposal passed every configured deterministic financial safety veto.",
        risk_budget_amount=account.equity * policy.risk_fraction_per_trade,
        stop_distance_points=stop_distance_points,
        approved_volume_lots=volume,
        projected_gross_lots=projected_gross_lots,
        projected_net_lots=projected_net_lots,
        estimated_margin_required=context.estimated_margin_required,
    )
