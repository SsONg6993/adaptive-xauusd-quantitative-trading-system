"""Pure construction of provenance-bound execution intents."""

from __future__ import annotations

from datetime import timedelta

from axq.discipline import DisciplineOutcome, DisciplineResult
from axq.execution_boundary.contracts import (
    ExecutionIntent,
    ExecutionMode,
    ExecutionOrderType,
    ExecutionPolicy,
)
from axq.master import MasterProposal
from axq.risk_boundary import RiskContext, RiskOutcome, RiskResult


def default_execution_policy() -> ExecutionPolicy:
    """Return the conservative, execution-disabled baseline policy."""
    return ExecutionPolicy(
        policy_version="demo-v1",
        mode=ExecutionMode.DISABLED,
        intent_ttl_seconds=15,
        max_observation_latency_seconds=2.0,
        max_actual_spread_points=50.0,
        max_pre_submit_slippage_points=10.0,
        max_price_deviation_points=10.0,
    )


def build_execution_intent(
    proposal: MasterProposal,
    discipline: DisciplineOutcome,
    risk: RiskOutcome,
    context: RiskContext,
    policy: ExecutionPolicy,
) -> ExecutionIntent | None:
    """Carry a fully linked Risk PASS into execution without changing it."""
    _validate_upstream_links(proposal, discipline, risk, context)
    if risk.result is not RiskResult.PASS or not risk.eligible_for_execution:
        return None
    if discipline.result is not DisciplineResult.PASS or not discipline.eligible_for_risk:
        raise ValueError("Risk PASS must be downstream of a Discipline PASS")
    if not proposal.actionable:
        raise ValueError("Risk PASS must be downstream of an actionable Master proposal")
    if risk.approved_volume_lots is None:
        raise ValueError("Risk PASS is missing approved volume")
    if context.entry_price is None or context.stop_loss_price is None:
        raise ValueError("Risk PASS execution requires approved entry and stop prices")
    if context.broker_constraints.point_size is None:
        raise ValueError("Risk PASS execution requires broker point size")
    if risk.setup_id is None or risk.thesis_id is None:
        raise ValueError("Risk PASS execution requires setup and thesis identity")

    return ExecutionIntent(
        evidence_bundle_id=risk.evidence_bundle_id,
        master_proposal_id=risk.master_proposal_id,
        discipline_outcome_id=risk.discipline_outcome_id,
        risk_outcome_id=risk.outcome_id,
        risk_context_id=risk.risk_context_id,
        setup_id=risk.setup_id,
        thesis_id=risk.thesis_id,
        scenario_id=risk.scenario_id,
        symbol=risk.symbol,
        broker_symbol=context.broker_constraints.symbol,
        broker_source=context.broker_constraints.source,
        point_size=context.broker_constraints.point_size,
        direction=risk.master_decision,
        approved_volume_lots=risk.approved_volume_lots,
        order_type=ExecutionOrderType.MARKET,
        requested_entry_price=context.entry_price,
        stop_loss_price=context.stop_loss_price,
        take_profit_price=None,
        as_of=risk.as_of,
        available_at=risk.available_at,
        expires_at=risk.available_at + timedelta(seconds=policy.intent_ttl_seconds),
        execution_policy_id=policy.policy_id,
        execution_policy_version=policy.policy_version,
        execution_mode=policy.mode,
    )


def _validate_upstream_links(
    proposal: MasterProposal,
    discipline: DisciplineOutcome,
    risk: RiskOutcome,
    context: RiskContext,
) -> None:
    if discipline.master_proposal_id != proposal.proposal_id:
        raise ValueError("Discipline outcome does not bind the supplied Master proposal")
    if discipline.evidence_bundle_id != proposal.bundle_id:
        raise ValueError("Discipline and Master evidence bundle IDs differ")
    if risk.master_proposal_id != proposal.proposal_id:
        raise ValueError("Risk outcome does not bind the supplied Master proposal")
    if risk.evidence_bundle_id != proposal.bundle_id:
        raise ValueError("Risk and Master evidence bundle IDs differ")
    if risk.discipline_outcome_id != discipline.outcome_id:
        raise ValueError("Risk outcome does not bind the supplied Discipline outcome")
    if risk.risk_context_id != context.context_id:
        raise ValueError("Risk outcome does not bind the supplied Risk context")
    if risk.master_decision is not proposal.decision:
        raise ValueError("Risk direction differs from the Master proposal")
    if discipline.master_decision is not proposal.decision:
        raise ValueError("Discipline direction differs from the Master proposal")
    if risk.symbol != context.symbol:
        raise ValueError("Risk outcome and context symbols differ")
    if (risk.setup_id, risk.thesis_id, risk.scenario_id) != (
        discipline.setup_id,
        discipline.thesis_id,
        discipline.scenario_id,
    ):
        raise ValueError("Risk setup/thesis/scenario provenance differs from Discipline")
    if not (risk.available_at <= risk.as_of and context.available_at <= risk.as_of):
        raise ValueError("execution inputs violate causal availability")
