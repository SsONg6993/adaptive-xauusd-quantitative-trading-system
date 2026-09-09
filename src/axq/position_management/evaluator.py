"""Pure deterministic evaluation for already-open positions."""

from __future__ import annotations

from datetime import datetime

from axq.agents import ContinuityStatus, HypothesisStatus, ScenarioStatus
from axq.execution_boundary import (
    ExecutionResultStatus,
    ReconciliationKind,
    ResolutionStatus,
    ResumeStatus,
)
from axq.position_management.contracts import (
    MissingEvidenceBehavior,
    PositionManagementContext,
    PositionManagementOutcome,
    PositionManagementPolicy,
    PositionManagementReason,
    PositionManagementResult,
)
from axq.runtime import ComponentFreshness, FreshnessStatus, PositionSide


def default_demo_position_management_policy() -> PositionManagementPolicy:
    """Return conservative deterministic demo defaults, not optimized strategy truth."""
    return PositionManagementPolicy(
        policy_version="demo-v1",
        exit_on_thesis_invalidated=True,
        exit_on_thesis_expired=True,
        exit_on_scenario_invalidated=True,
        protect_on_thesis_weakening=True,
        break_even_enabled=True,
        minimum_position_age_seconds=60.0,
        max_protective_sl_change_points=2_000.0,
        max_component_age_seconds=30.0,
        missing_evidence_behavior=MissingEvidenceBehavior.HOLD_POSITION,
    )


def evaluate_position(
    context: PositionManagementContext,
    policy: PositionManagementPolicy,
) -> PositionManagementOutcome:
    """Evaluate one open position without mutating state or invoking execution transport."""
    if context.position is None:
        return _outcome(
            context,
            policy,
            PositionManagementResult.NO_ACTION,
            (PositionManagementReason.NO_OPEN_POSITION,),
            "No authoritative open position is available for management.",
        )

    safety_reasons = _safety_reasons(context, policy)
    if safety_reasons:
        return _outcome(
            context,
            policy,
            PositionManagementResult.NO_ACTION,
            safety_reasons,
            "Position management is blocked until authoritative state and provenance are safe.",
        )

    if context.evidence_bundle is None:
        if policy.missing_evidence_behavior is MissingEvidenceBehavior.NO_ACTION:
            return _outcome(
                context,
                policy,
                PositionManagementResult.NO_ACTION,
                (PositionManagementReason.EVIDENCE_MISSING,),
                "Current evidence is absent and policy requires no autonomous position action.",
            )
        return _hold(context, policy, PositionManagementReason.EVIDENCE_MISSING)

    assert context.thesis is not None
    assert context.original_execution_intent is not None
    lifecycle = context.thesis.hypothesis_status
    if lifecycle is HypothesisStatus.INVALIDATED:
        if policy.exit_on_thesis_invalidated:
            return _outcome(
                context,
                policy,
                PositionManagementResult.EXIT_POSITION,
                (PositionManagementReason.THESIS_INVALIDATED,),
                "The originating thesis is invalidated.",
            )
        return _hold(context, policy, PositionManagementReason.THESIS_INVALIDATED)
    if lifecycle is HypothesisStatus.EXPIRED:
        if policy.exit_on_thesis_expired:
            return _outcome(
                context,
                policy,
                PositionManagementResult.EXIT_POSITION,
                (PositionManagementReason.THESIS_EXPIRED,),
                "The originating thesis expired under the configured policy.",
            )
        return _hold(context, policy, PositionManagementReason.THESIS_EXPIRED)
    scenario = next(
        (
            item
            for item in context.thesis.scenarios
            if item.scenario_id == context.original_execution_intent.scenario_id
        ),
        None,
    )
    if scenario is not None and scenario.status is ScenarioStatus.INVALIDATED:
        if policy.exit_on_scenario_invalidated:
            return _outcome(
                context,
                policy,
                PositionManagementResult.EXIT_POSITION,
                (PositionManagementReason.SCENARIO_INVALIDATED,),
                "The position's exact originating scenario is invalidated.",
            )
        return _hold(context, policy, PositionManagementReason.SCENARIO_INVALIDATED)
    if lifecycle is HypothesisStatus.WEAKENING:
        return _evaluate_protection(context, policy)
    if lifecycle is HypothesisStatus.CONFIRMED:
        return _hold(context, policy, PositionManagementReason.THESIS_CONFIRMED)
    return _hold(context, policy, PositionManagementReason.THESIS_ACTIVE)


def _safety_reasons(
    context: PositionManagementContext,
    policy: PositionManagementPolicy,
) -> tuple[PositionManagementReason, ...]:
    reasons: list[PositionManagementReason] = []
    position = context.position
    intent = context.original_execution_intent
    result = context.original_execution_result
    link = context.broker_intent_link
    thesis = context.thesis
    assert position is not None

    if context.resume_readiness.status is not ResumeStatus.SAFE:
        reasons.append(PositionManagementReason.RUNTIME_NOT_SAFE)
    if context.reconciliation.status is not ResolutionStatus.RESOLVED:
        reasons.append(PositionManagementReason.RECONCILIATION_UNRESOLVED)
    if not _is_fresh(context.account.freshness, context.account.as_of, context.as_of, policy):
        reasons.append(PositionManagementReason.ACCOUNT_STATE_NOT_FRESH)
    if not _is_fresh(context.position_freshness, context.as_of, context.as_of, policy):
        reasons.append(PositionManagementReason.POSITION_STATE_NOT_FRESH)
    if not _is_fresh(
        context.broker_constraints.freshness,
        context.broker_constraints.as_of,
        context.as_of,
        policy,
    ):
        reasons.append(PositionManagementReason.BROKER_CONSTRAINTS_NOT_FRESH)
    if context.intrabar_continuity is not ContinuityStatus.COMPLETE or (
        thesis is not None and thesis.continuity_status is not ContinuityStatus.COMPLETE
    ):
        reasons.append(PositionManagementReason.INTRABAR_CONTINUITY_MISSING)
    if thesis is None or position.thesis_id is None:
        reasons.append(PositionManagementReason.MISSING_THESIS_LINKAGE)
    if intent is None or result is None:
        reasons.append(PositionManagementReason.MISSING_EXECUTION_PROVENANCE)
    if link is None:
        reasons.append(PositionManagementReason.MISSING_EXACT_EXECUTION_LINKAGE)
    if result is not None and result.status is ExecutionResultStatus.UNKNOWN:
        reasons.append(PositionManagementReason.UNKNOWN_EXECUTION_STATE)

    if intent is not None and link is not None and result is not None:
        exact = (
            link.intent_id == intent.intent_id == result.execution_intent_id
            and link.broker_object_id == position.position_id
            and (
                link.broker_ticket is None
                or position.broker_ticket is None
                or link.broker_ticket == position.broker_ticket
            )
            and link.transport_execution_id == result.transport_execution_id
        )
        matched = any(
            finding.kind is ReconciliationKind.MATCHED
            and finding.intent_id == intent.intent_id
            and finding.broker_object_id == position.position_id
            for finding in context.reconciliation.findings
        )
        if not exact or not matched:
            reasons.append(PositionManagementReason.EXECUTION_PROVENANCE_MISMATCH)
        if intent.scenario_id is not None and (
            thesis is None
            or not any(item.scenario_id == intent.scenario_id for item in thesis.scenarios)
        ):
            reasons.append(PositionManagementReason.MISSING_SCENARIO_LINKAGE)
    return tuple(dict.fromkeys(reasons))


def _is_fresh(
    freshness: ComponentFreshness,
    state_as_of: datetime,
    evaluation_time: datetime,
    policy: PositionManagementPolicy,
) -> bool:
    if freshness.status is not FreshnessStatus.AVAILABLE or freshness.available_at is None:
        return False
    availability_age = (evaluation_time - freshness.available_at).total_seconds()
    state_age = (evaluation_time - state_as_of).total_seconds()
    return (
        0 <= availability_age <= policy.max_component_age_seconds
        and 0 <= state_age <= policy.max_component_age_seconds
    )


def _evaluate_protection(
    context: PositionManagementContext,
    policy: PositionManagementPolicy,
) -> PositionManagementOutcome:
    position = context.position
    assert position is not None
    if not policy.protect_on_thesis_weakening:
        return _hold(context, policy, PositionManagementReason.THESIS_WEAKENING)
    if not policy.break_even_enabled:
        return _hold(context, policy, PositionManagementReason.BREAK_EVEN_DISABLED)
    if (context.as_of - position.opened_at).total_seconds() < policy.minimum_position_age_seconds:
        return _hold(context, policy, PositionManagementReason.POSITION_TOO_YOUNG_FOR_PROTECTION)
    broker = context.broker_constraints
    if (
        broker.trade_allowed is not True
        or broker.point_size is None
        or broker.stops_level_points is None
        or broker.freeze_level_points is None
    ):
        return _hold(context, policy, PositionManagementReason.BROKER_PROTECTION_CONSTRAINT)
    if position.current_price is None:
        return _outcome(
            context,
            policy,
            PositionManagementResult.NO_ACTION,
            (PositionManagementReason.CURRENT_PRICE_UNAVAILABLE,),
            "Current price is unavailable, so no protective change can be assessed.",
        )

    old_stop = position.stop_loss
    entry = position.open_price
    if old_stop is not None and (
        (position.side is PositionSide.BUY and old_stop >= entry)
        or (position.side is PositionSide.SELL and old_stop <= entry)
    ):
        return _hold(context, policy, PositionManagementReason.ALREADY_PROTECTED)
    max_change = policy.max_protective_sl_change_points * broker.point_size
    if old_stop is None:
        candidate = entry
    elif position.side is PositionSide.BUY:
        candidate = min(entry, old_stop + max_change)
    else:
        candidate = max(entry, old_stop - max_change)
    if old_stop is not None and (
        (position.side is PositionSide.BUY and candidate <= old_stop)
        or (position.side is PositionSide.SELL and candidate >= old_stop)
    ):
        return _hold(context, policy, PositionManagementReason.PROTECTION_NOT_RISK_REDUCING)

    required_distance = (
        max(broker.stops_level_points, broker.freeze_level_points) * broker.point_size
    )
    broker_valid = (
        position.side is PositionSide.BUY
        and candidate <= position.current_price - required_distance
    ) or (
        position.side is PositionSide.SELL
        and candidate >= position.current_price + required_distance
    )
    if not broker_valid:
        return _hold(context, policy, PositionManagementReason.BROKER_PROTECTION_CONSTRAINT)
    return _outcome(
        context,
        policy,
        PositionManagementResult.PROTECT_POSITION,
        (PositionManagementReason.BREAK_EVEN_PROTECTION,),
        "A monotonic broker-valid protective stop is requested without changing the thesis.",
        requested_stop=candidate,
    )


def _hold(
    context: PositionManagementContext,
    policy: PositionManagementPolicy,
    reason: PositionManagementReason,
) -> PositionManagementOutcome:
    return _outcome(
        context,
        policy,
        PositionManagementResult.HOLD_POSITION,
        (reason,),
        "The open position remains unchanged and no modification intent is generated.",
    )


def _outcome(
    context: PositionManagementContext,
    policy: PositionManagementPolicy,
    result: PositionManagementResult,
    reasons: tuple[PositionManagementReason, ...],
    rationale: str,
    *,
    requested_stop: float | None = None,
) -> PositionManagementOutcome:
    position = context.position
    intent = context.original_execution_intent
    execution_result = context.original_execution_result
    thesis = context.thesis
    return PositionManagementOutcome(
        policy_id=policy.policy_id,
        position_management_context_id=context.context_id,
        position_id=position.position_id if position else None,
        original_execution_intent_id=intent.intent_id if intent else None,
        original_execution_result_id=execution_result.result_id if execution_result else None,
        setup_id=intent.setup_id if intent else position.setup_id if position else None,
        thesis_id=intent.thesis_id if intent else position.thesis_id if position else None,
        scenario_id=intent.scenario_id if intent else None,
        current_thesis_lifecycle=thesis.hypothesis_status if thesis else None,
        position_side=position.side if position else None,
        entry_price=position.open_price if position else None,
        existing_stop_loss=position.stop_loss if position else None,
        result=result,
        reason_codes=reasons,
        eligible_for_position_action=result
        in {PositionManagementResult.PROTECT_POSITION, PositionManagementResult.EXIT_POSITION},
        requested_protective_stop_loss=requested_stop,
        as_of=context.as_of,
        available_at=context.available_at,
        rationale=rationale,
    )
