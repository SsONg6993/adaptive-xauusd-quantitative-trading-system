"""Pure fail-closed position-action safety evaluation."""

from __future__ import annotations

import math
from datetime import datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

from axq.execution_boundary import (
    BrokerObjectKind,
    ExecutionResultStatus,
    ReconciliationKind,
    ResolutionStatus,
    ResumeStatus,
)
from axq.position_actions.contracts import (
    PositionActionContext,
    PositionActionIntent,
    PositionActionPolicy,
    PositionActionReason,
    PositionActionSafetyOutcome,
    PositionActionSafetyResult,
    PositionActionType,
)
from axq.position_management import PositionManagementResult
from axq.runtime import ComponentFreshness, FreshnessStatus, PositionSide
from axq.schemas import Signal


def default_position_action_policy() -> PositionActionPolicy:
    """Return conservative deterministic V1 safety defaults."""
    return PositionActionPolicy(
        policy_version="demo-v1",
        max_management_outcome_age_seconds=30.0,
        max_component_age_seconds=30.0,
        volume_tolerance_lots=1e-8,
        allow_add_protective_stop_when_missing=True,
        allow_risk_reducing_tick_normalization=True,
    )


def evaluate_position_action_safety(
    context: PositionActionContext,
    policy: PositionActionPolicy,
) -> PositionActionSafetyOutcome:
    """Revalidate a management request against current authoritative safety facts."""
    management = context.management_outcome
    if management.result in {
        PositionManagementResult.NO_ACTION,
        PositionManagementResult.HOLD_POSITION,
    }:
        return _outcome(
            context,
            policy,
            result=PositionActionSafetyResult.NO_ACTION,
            action=PositionActionType.NO_ACTION,
            reasons=(PositionActionReason.MANAGEMENT_DID_NOT_REQUEST_ACTION,),
            rationale="Position Management requested no transportable position action.",
        )

    action = (
        PositionActionType.MODIFY_PROTECTIVE_STOP
        if management.result is PositionManagementResult.PROTECT_POSITION
        else PositionActionType.CLOSE_POSITION
    )
    emergency, rejected = _common_safety_reasons(context, policy, action)
    if emergency:
        return _outcome(
            context,
            policy,
            result=PositionActionSafetyResult.EMERGENCY_BLOCK,
            action=action,
            reasons=emergency + rejected,
            rationale="Hard recovery or identity safety invariants block this position action.",
        )
    if rejected:
        return _outcome(
            context,
            policy,
            result=PositionActionSafetyResult.REJECT,
            action=action,
            reasons=rejected,
            rationale="Current authoritative state does not safely support this position action.",
        )

    position = context.position
    assert position is not None
    if action is PositionActionType.CLOSE_POSITION:
        return _outcome(
            context,
            policy,
            result=PositionActionSafetyResult.PASS,
            action=action,
            reasons=(PositionActionReason.CLOSE_POSITION_SAFE,),
            close_volume=position.volume_lots,
            rationale="The exact-linked authoritative position is safe for a full close intent.",
        )

    normalized, protection_reasons = _validate_protective_stop(context, policy)
    if protection_reasons:
        return _outcome(
            context,
            policy,
            result=PositionActionSafetyResult.REJECT,
            action=action,
            reasons=protection_reasons,
            rationale="The protective-stop request failed action-time broker safety checks.",
        )
    assert normalized is not None
    return _outcome(
        context,
        policy,
        result=PositionActionSafetyResult.PASS,
        action=action,
        reasons=(PositionActionReason.MODIFY_PROTECTIVE_STOP_SAFE,),
        normalized_stop=normalized,
        rationale="The exact-linked protective stop is monotonic and broker-valid.",
    )


def build_position_action_intent(
    context: PositionActionContext,
    safety: PositionActionSafetyOutcome,
) -> PositionActionIntent | None:
    """Create a transportable semantic intent only from the exact passed safety result."""
    if safety.result is not PositionActionSafetyResult.PASS:
        return None
    management = context.management_outcome
    position = context.position
    if (
        safety.context_id != context.context_id
        or safety.position_management_outcome_id != management.outcome_id
        or safety.policy_id != context.policy_id
        or position is None
        or safety.position_id != position.position_id
    ):
        raise ValueError("safety outcome does not bind this exact position-action context")
    intent = context.original_execution_intent
    result = context.original_execution_result
    return PositionActionIntent(
        policy_id=safety.policy_id,
        safety_outcome_id=safety.safety_outcome_id,
        position_management_outcome_id=management.outcome_id,
        position_id=position.position_id,
        broker_ticket=position.broker_ticket,
        original_execution_intent_id=intent.intent_id,
        original_execution_result_id=result.result_id,
        broker_intent_link_id=context.broker_intent_link.link_id,
        reconciliation_report_id=context.reconciliation.report_id,
        resume_readiness_id=context.resume_readiness.readiness_id,
        setup_id=intent.setup_id,
        thesis_id=intent.thesis_id,
        scenario_id=intent.scenario_id,
        action_type=safety.requested_action,
        symbol=position.symbol,
        position_side=position.side,
        current_volume_lots=position.volume_lots,
        requested_close_volume_lots=safety.requested_close_volume_lots,
        existing_stop_loss=position.stop_loss,
        requested_new_stop_loss=safety.normalized_protective_stop_loss,
        audit_reason_codes=safety.reason_codes,
        as_of=safety.as_of,
        available_at=safety.available_at,
    )


def _common_safety_reasons(
    context: PositionActionContext,
    policy: PositionActionPolicy,
    action: PositionActionType,
) -> tuple[tuple[PositionActionReason, ...], tuple[PositionActionReason, ...]]:
    emergency: list[PositionActionReason] = []
    rejected: list[PositionActionReason] = []
    management = context.management_outcome
    position = context.position
    intent = context.original_execution_intent
    result = context.original_execution_result
    link = context.broker_intent_link

    if context.policy_id != policy.policy_id:
        emergency.append(PositionActionReason.POLICY_MISMATCH)
    if context.kill_switch_active:
        emergency.append(PositionActionReason.KILL_SWITCH_ACTIVE)
    if context.resume_readiness.status is not ResumeStatus.SAFE:
        emergency.append(PositionActionReason.RUNTIME_NOT_SAFE)
    if context.reconciliation.status is not ResolutionStatus.RESOLVED:
        emergency.append(PositionActionReason.RECONCILIATION_UNRESOLVED)
    if result.status is ExecutionResultStatus.UNKNOWN:
        emergency.append(PositionActionReason.UNKNOWN_EXECUTION_STATE)

    if not _age_is_valid(
        management.available_at,
        context.as_of,
        policy.max_management_outcome_age_seconds,
    ):
        rejected.append(PositionActionReason.MANAGEMENT_OUTCOME_STALE)
    if not _state_is_fresh(
        context.account.freshness,
        context.account.as_of,
        context.as_of,
        policy.max_component_age_seconds,
    ):
        rejected.append(PositionActionReason.ACCOUNT_NOT_FRESH)
    if not _freshness_is_valid(
        context.position_freshness,
        context.as_of,
        policy.max_component_age_seconds,
    ):
        rejected.append(PositionActionReason.POSITION_NOT_FRESH)
    if not _state_is_fresh(
        context.broker_constraints.freshness,
        context.broker_constraints.as_of,
        context.as_of,
        policy.max_component_age_seconds,
    ):
        rejected.append(PositionActionReason.BROKER_CONSTRAINTS_NOT_FRESH)
    if not _age_is_valid(
        context.reconciliation.available_at,
        context.as_of,
        policy.max_component_age_seconds,
    ) or not _age_is_valid(
        context.resume_readiness.as_of,
        context.as_of,
        policy.max_component_age_seconds,
    ):
        rejected.append(PositionActionReason.RECONCILIATION_NOT_FRESH)
    if position is None:
        rejected.append(PositionActionReason.POSITION_MISSING)
        return tuple(dict.fromkeys(emergency)), tuple(dict.fromkeys(rejected))

    if management.position_id != position.position_id:
        rejected.append(PositionActionReason.POSITION_SNAPSHOT_CHANGED)
    if action is PositionActionType.MODIFY_PROTECTIVE_STOP and not _same_optional_price(
        management.existing_stop_loss,
        position.stop_loss,
    ):
        rejected.append(PositionActionReason.CURRENT_STOP_CHANGED)
    if link.object_kind is not BrokerObjectKind.POSITION:
        emergency.append(PositionActionReason.EXACT_LINKAGE_MISMATCH)
    if not (
        link.intent_id == intent.intent_id == result.execution_intent_id
        and link.transport_execution_id == result.transport_execution_id
    ):
        emergency.append(PositionActionReason.EXACT_LINKAGE_MISMATCH)
    if link.broker_object_id != position.position_id:
        rejected.append(PositionActionReason.POSITION_SNAPSHOT_CHANGED)

    tickets = (link.broker_ticket, result.broker_ticket, position.broker_ticket)
    known_tickets = tuple(item for item in tickets if item is not None)
    if known_tickets and (
        len(known_tickets) != len(tickets) or len(set(known_tickets)) != 1
    ):
        emergency.append(PositionActionReason.TICKET_MISMATCH)

    expected_side = PositionSide.BUY if intent.direction is Signal.BUY else PositionSide.SELL
    if not (
        management.position_side is position.side
        and result.direction is intent.direction
        and position.side is expected_side
    ):
        emergency.append(PositionActionReason.DIRECTION_MISMATCH)
    if not (
        management.setup_id == position.setup_id == intent.setup_id == result.setup_id
    ):
        emergency.append(PositionActionReason.SETUP_LINKAGE_MISMATCH)
    if not (
        management.thesis_id == position.thesis_id == intent.thesis_id == result.thesis_id
    ):
        emergency.append(PositionActionReason.THESIS_LINKAGE_MISMATCH)
    if not (management.scenario_id == intent.scenario_id == result.scenario_id):
        emergency.append(PositionActionReason.SCENARIO_LINKAGE_MISMATCH)
    if not (
        management.original_execution_intent_id == intent.intent_id
        and management.original_execution_result_id == result.result_id
    ):
        emergency.append(PositionActionReason.EXACT_LINKAGE_MISMATCH)
    if not (
        management.setup_id == intent.setup_id
        and management.thesis_id == intent.thesis_id
        and management.scenario_id == intent.scenario_id
    ):
        emergency.append(PositionActionReason.EXACT_LINKAGE_MISMATCH)

    if position.symbol != intent.symbol or result.symbol != intent.symbol:
        emergency.append(PositionActionReason.SYMBOL_MISMATCH)
    if (
        context.broker_constraints.symbol != position.symbol
        or context.market.symbol != position.symbol
    ):
        emergency.append(PositionActionReason.SYMBOL_MISMATCH)
    expected_volume = result.filled_volume_lots
    if expected_volume is None or not math.isclose(
        position.volume_lots,
        expected_volume,
        abs_tol=policy.volume_tolerance_lots,
        rel_tol=0.0,
    ):
        rejected.append(PositionActionReason.VOLUME_MISMATCH)

    matched = any(
        item.kind is ReconciliationKind.MATCHED
        and item.status is ResolutionStatus.RESOLVED
        and item.intent_id == intent.intent_id
        and item.broker_object_id == position.position_id
        and (item.broker_ticket is None or item.broker_ticket == position.broker_ticket)
        for item in context.reconciliation.findings
    )
    if not matched:
        rejected.append(PositionActionReason.RECONCILIATION_POSITION_STALE)
    if context.broker_constraints.trade_allowed is not True:
        rejected.append(PositionActionReason.BROKER_TRADING_DISABLED)
    if action is PositionActionType.MODIFY_PROTECTIVE_STOP and not _state_is_fresh(
        context.market.freshness,
        context.market.as_of,
        context.as_of,
        policy.max_component_age_seconds,
    ):
        rejected.append(PositionActionReason.MARKET_PRICE_NOT_FRESH)
    return tuple(dict.fromkeys(emergency)), tuple(dict.fromkeys(rejected))


def _validate_protective_stop(
    context: PositionActionContext,
    policy: PositionActionPolicy,
) -> tuple[float | None, tuple[PositionActionReason, ...]]:
    position = context.position
    assert position is not None
    management = context.management_outcome
    requested = management.requested_protective_stop_loss
    broker = context.broker_constraints
    reasons: list[PositionActionReason] = []
    if requested is None:
        return None, (PositionActionReason.SAFE_NORMALIZATION_IMPOSSIBLE,)
    if not _same_optional_price(management.existing_stop_loss, position.stop_loss):
        reasons.append(PositionActionReason.CURRENT_STOP_CHANGED)
    if position.stop_loss is None:
        if not policy.allow_add_protective_stop_when_missing:
            reasons.append(PositionActionReason.MISSING_STOP_NOT_ALLOWED)
        original = context.original_execution_intent.stop_loss_price
        reduces_original_risk = (
            position.side is PositionSide.BUY and requested >= original
        ) or (position.side is PositionSide.SELL and requested <= original)
        if not reduces_original_risk:
            reasons.append(PositionActionReason.PROTECTION_EXCEEDS_ORIGINAL_RISK)
    else:
        improves = (
            position.side is PositionSide.BUY and requested > position.stop_loss
        ) or (position.side is PositionSide.SELL and requested < position.stop_loss)
        if not improves:
            reasons.append(PositionActionReason.PROTECTION_NOT_RISK_REDUCING)
    if any(
        value is None
        for value in (
            broker.point_size,
            broker.tick_size,
            broker.stops_level_points,
            broker.freeze_level_points,
        )
    ):
        reasons.append(PositionActionReason.BROKER_CONSTRAINTS_UNAVAILABLE)
        return None, tuple(dict.fromkeys(reasons))
    assert broker.tick_size is not None
    normalized = _risk_reducing_normalize(
        requested,
        broker.tick_size,
        context.symbol_digits,
        position.side,
        enabled=policy.allow_risk_reducing_tick_normalization,
    )
    if normalized is None:
        reasons.append(PositionActionReason.SAFE_NORMALIZATION_IMPOSSIBLE)
        return None, tuple(dict.fromkeys(reasons))
    bid = context.market.bid
    ask = context.market.ask
    current = bid if position.side is PositionSide.BUY else ask
    if current is None:
        reasons.append(PositionActionReason.MARKET_PRICE_NOT_FRESH)
        return None, tuple(dict.fromkeys(reasons))
    direction_valid = (
        position.side is PositionSide.BUY and normalized < current
    ) or (position.side is PositionSide.SELL and normalized > current)
    if not direction_valid:
        reasons.append(PositionActionReason.BROKER_STOP_DIRECTION_INVALID)
    assert broker.point_size is not None
    assert broker.stops_level_points is not None
    assert broker.freeze_level_points is not None
    required_distance = (
        max(broker.stops_level_points, broker.freeze_level_points) * broker.point_size
    )
    actual_distance = (
        current - normalized
        if position.side is PositionSide.BUY
        else normalized - current
    )
    if actual_distance + 1e-12 < required_distance:
        reasons.append(PositionActionReason.BROKER_STOP_DISTANCE_VIOLATION)
    return normalized, tuple(dict.fromkeys(reasons))


def _risk_reducing_normalize(
    requested: float,
    tick_size: float,
    digits: int,
    side: PositionSide,
    *,
    enabled: bool,
) -> float | None:
    value = Decimal(str(requested))
    tick = Decimal(str(tick_size))
    quotient = value / tick
    integral = quotient.to_integral_value(
        rounding=ROUND_CEILING if side is PositionSide.BUY else ROUND_FLOOR
    )
    normalized = integral * tick
    places = Decimal(1).scaleb(-digits)
    normalized = normalized.quantize(places)
    if normalized % tick != 0:
        return None
    if not enabled and normalized != value.quantize(places):
        return None
    result = float(normalized)
    safe_direction = result >= requested if side is PositionSide.BUY else result <= requested
    return result if safe_direction and math.isfinite(result) else None


def _same_optional_price(first: float | None, second: float | None) -> bool:
    if first is None or second is None:
        return first is second
    return math.isclose(first, second, abs_tol=1e-10, rel_tol=0.0)


def _state_is_fresh(
    freshness: ComponentFreshness,
    state_as_of: datetime,
    evaluation_time: datetime,
    max_age_seconds: float,
) -> bool:
    return _freshness_is_valid(freshness, evaluation_time, max_age_seconds) and _age_is_valid(
        state_as_of,
        evaluation_time,
        max_age_seconds,
    )


def _freshness_is_valid(
    freshness: ComponentFreshness,
    evaluation_time: datetime,
    max_age_seconds: float,
) -> bool:
    return (
        freshness.status is FreshnessStatus.AVAILABLE
        and freshness.available_at is not None
        and _age_is_valid(freshness.available_at, evaluation_time, max_age_seconds)
    )


def _age_is_valid(value: datetime, evaluation_time: datetime, max_age_seconds: float) -> bool:
    age = (evaluation_time - value).total_seconds()
    return 0 <= age <= max_age_seconds


def _outcome(
    context: PositionActionContext,
    policy: PositionActionPolicy,
    *,
    result: PositionActionSafetyResult,
    action: PositionActionType,
    reasons: tuple[PositionActionReason, ...],
    rationale: str,
    normalized_stop: float | None = None,
    close_volume: float | None = None,
) -> PositionActionSafetyOutcome:
    return PositionActionSafetyOutcome(
        policy_id=policy.policy_id,
        context_id=context.context_id,
        position_management_outcome_id=context.management_outcome.outcome_id,
        position_id=context.position.position_id if context.position is not None else None,
        result=result,
        requested_action=action,
        reason_codes=tuple(dict.fromkeys(reasons)),
        eligible_for_intent=result is PositionActionSafetyResult.PASS,
        normalized_protective_stop_loss=normalized_stop,
        requested_close_volume_lots=close_volume,
        as_of=context.as_of,
        available_at=context.available_at,
        rationale=rationale,
    )
