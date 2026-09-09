from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.execution_boundary import (
    BrokerIntentLink,
    BrokerObjectKind,
    ExecutionIntent,
    ExecutionMode,
    ExecutionOrderType,
    ExecutionReason,
    ExecutionResult,
    ExecutionResultStatus,
    ReconciliationFinding,
    ReconciliationKind,
    ReconciliationReport,
    ResolutionStatus,
    ResumeBlockReason,
    ResumeReadiness,
    ResumeStatus,
)
from axq.position_actions import (
    PositionActionContext,
    PositionActionIntent,
    PositionActionReason,
    PositionActionSafetyResult,
    PositionActionType,
    build_position_action_intent,
    default_position_action_policy,
    evaluate_position_action_safety,
)
from axq.position_actions.journal import append_position_action_chain
from axq.position_management import (
    PositionManagementOutcome,
    PositionManagementReason,
    PositionManagementResult,
)
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    FreshnessStatus,
    MarketState,
    PositionSide,
    PositionState,
)
from axq.runtime.journal import JournalRecordType, SQLiteRuntimeJournal
from axq.schemas import Signal

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)
AS_OF = T0 + timedelta(minutes=5)


def _fresh(component: str, at: datetime = AS_OF) -> ComponentFreshness:
    return ComponentFreshness(
        component=component,
        status=FreshnessStatus.AVAILABLE,
        observed_at=at,
        available_at=at,
        stale_after_ms=30_000,
    )


def _intent(side: PositionSide = PositionSide.BUY) -> ExecutionIntent:
    return ExecutionIntent(
        evidence_bundle_id="eb-position",
        master_proposal_id="mp-position",
        discipline_outcome_id="do-position",
        risk_outcome_id="ro-position",
        risk_context_id="rc-position",
        setup_id="setup-position",
        thesis_id="thesis-position",
        scenario_id="scenario-position",
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        broker_source="mt5",
        point_size=0.01,
        direction=Signal.BUY if side is PositionSide.BUY else Signal.SELL,
        approved_volume_lots=0.05,
        order_type=ExecutionOrderType.MARKET,
        requested_entry_price=2500.0,
        stop_loss_price=2490.0 if side is PositionSide.BUY else 2510.0,
        as_of=T0,
        available_at=T0,
        expires_at=T0 + timedelta(seconds=30),
        execution_policy_id="ep-position",
        execution_policy_version="demo-v1",
        execution_mode=ExecutionMode.DEMO_ENABLED,
    )


def _result(
    intent: ExecutionIntent,
    status: ExecutionResultStatus = ExecutionResultStatus.FILLED,
) -> ExecutionResult:
    unknown = status is ExecutionResultStatus.UNKNOWN
    return ExecutionResult(
        execution_intent_id=intent.intent_id,
        evidence_bundle_id=intent.evidence_bundle_id,
        master_proposal_id=intent.master_proposal_id,
        discipline_outcome_id=intent.discipline_outcome_id,
        risk_outcome_id=intent.risk_outcome_id,
        setup_id=intent.setup_id,
        thesis_id=intent.thesis_id,
        scenario_id=intent.scenario_id,
        symbol=intent.symbol,
        direction=intent.direction,
        status=status,
        reason_code=ExecutionReason.UNKNOWN_SUBMISSION if unknown else None,
        reason="unknown acknowledgement" if unknown else None,
        requested_volume_lots=0.05,
        filled_volume_lots=None if unknown else 0.05,
        remaining_volume_lots=None if unknown else 0.0,
        requested_price=2500.0,
        fill_price=None if unknown else 2500.0,
        broker_ticket=None if unknown else 123,
        transport_execution_id="transport-position",
        event_time=T0 + timedelta(seconds=1),
        observed_at=T0 + timedelta(seconds=1),
        available_at=T0 + timedelta(seconds=1),
    )


def _position(
    side: PositionSide = PositionSide.BUY,
    *,
    ticket: int = 123,
    symbol: str = "XAUUSD",
    volume: float = 0.05,
    stop: float | None | object = ...,
) -> PositionState:
    stop_loss = (2490.0 if side is PositionSide.BUY else 2510.0) if stop is ... else stop
    return PositionState(
        source="mt5",
        broker_ticket=ticket,
        symbol=symbol,
        side=side,
        volume_lots=volume,
        opened_at=T0,
        open_price=2500.0,
        current_price=2510.0 if side is PositionSide.BUY else 2490.0,
        stop_loss=stop_loss,
        floating_pnl=50.0,
        setup_id="setup-position",
        thesis_id="thesis-position",
    )


def _management(
    position: PositionState,
    intent: ExecutionIntent,
    result: ExecutionResult,
    management_result: PositionManagementResult,
    *,
    requested_stop: float | None = None,
    at: datetime = AS_OF,
) -> PositionManagementOutcome:
    reasons = {
        PositionManagementResult.HOLD_POSITION: (PositionManagementReason.THESIS_ACTIVE,),
        PositionManagementResult.NO_ACTION: (PositionManagementReason.EVIDENCE_MISSING,),
        PositionManagementResult.PROTECT_POSITION: (
            PositionManagementReason.BREAK_EVEN_PROTECTION,
        ),
        PositionManagementResult.EXIT_POSITION: (PositionManagementReason.THESIS_INVALIDATED,),
    }
    return PositionManagementOutcome(
        policy_id="pmp-position",
        position_management_context_id="pmc-position",
        position_id=position.position_id,
        original_execution_intent_id=intent.intent_id,
        original_execution_result_id=result.result_id,
        setup_id=intent.setup_id,
        thesis_id=intent.thesis_id,
        scenario_id=intent.scenario_id,
        position_side=position.side,
        entry_price=position.open_price,
        existing_stop_loss=position.stop_loss,
        result=management_result,
        reason_codes=reasons[management_result],
        eligible_for_position_action=management_result
        in {PositionManagementResult.PROTECT_POSITION, PositionManagementResult.EXIT_POSITION},
        requested_protective_stop_loss=requested_stop,
        as_of=at,
        available_at=at,
        rationale="deterministic test management outcome",
    )


def _context(
    management_result: PositionManagementResult = PositionManagementResult.PROTECT_POSITION,
    *,
    side: PositionSide = PositionSide.BUY,
    requested_stop: float | None = None,
    position: PositionState | None | object = ...,
    result_status: ExecutionResultStatus = ExecutionResultStatus.FILLED,
    readiness: ResumeStatus = ResumeStatus.SAFE,
    reconciliation_kind: ReconciliationKind = ReconciliationKind.MATCHED,
    at: datetime = AS_OF,
) -> PositionActionContext:
    intent = _intent(side)
    result = _result(intent, result_status)
    authoritative = _position(side) if position is ... else position
    management_position = authoritative if authoritative is not None else _position(side)
    assert isinstance(management_position, PositionState)
    default_stop = 2500.0
    management = _management(
        management_position,
        intent,
        result,
        management_result,
        requested_stop=(
            requested_stop
            if requested_stop is not None
            else default_stop
            if management_result is PositionManagementResult.PROTECT_POSITION
            else None
        ),
        at=at,
    )
    object_id = authoritative.position_id if authoritative is not None else management.position_id
    ticket = authoritative.broker_ticket if authoritative is not None else 123
    link = BrokerIntentLink(
        intent_id=intent.intent_id,
        object_kind=BrokerObjectKind.POSITION,
        broker_object_id=object_id,
        broker_ticket=ticket,
        transport_execution_id=result.transport_execution_id,
    )
    finding = ReconciliationFinding(
        kind=reconciliation_kind,
        status=(
            ResolutionStatus.RESOLVED
            if reconciliation_kind is ReconciliationKind.MATCHED
            else ResolutionStatus.RECONCILIATION_REQUIRED
        ),
        intent_id=(
            intent.intent_id
            if reconciliation_kind is not ReconciliationKind.BROKER_ONLY
            else None
        ),
        broker_object_id=object_id,
        broker_ticket=ticket,
        reason_code=(
            "EXACT_LINK_MATCH"
            if reconciliation_kind is ReconciliationKind.MATCHED
            else "UNRESOLVED_TEST_ANOMALY"
        ),
    )
    report = ReconciliationReport(
        snapshot_id="snapshot-position",
        as_of=at,
        available_at=at,
        status=(
            ResolutionStatus.RESOLVED
            if reconciliation_kind is ReconciliationKind.MATCHED
            else ResolutionStatus.RECONCILIATION_REQUIRED
        ),
        findings=(finding,),
    )
    readiness_reasons = (
        ()
        if readiness is ResumeStatus.SAFE
        else (ResumeBlockReason.UNRESOLVED_EXECUTION_ANOMALY,)
    )
    ready = ResumeReadiness(
        runtime_state_id="state-position",
        reconciliation_report_id=report.report_id,
        as_of=at,
        status=readiness,
        reason_codes=readiness_reasons,
    )
    policy = default_position_action_policy()
    return PositionActionContext(
        policy_id=policy.policy_id,
        management_outcome=management,
        position=authoritative,
        original_execution_intent=intent,
        original_execution_result=result,
        broker_intent_link=link,
        reconciliation=report,
        resume_readiness=ready,
        account=AccountState(
            source="mt5",
            account_id="demo",
            as_of=at,
            freshness=_fresh("account", at),
            currency="USD",
            balance=10_000.0,
            equity=10_050.0,
            free_margin=9_500.0,
            used_margin=500.0,
            floating_pnl=50.0,
        ),
        position_freshness=_fresh("positions", at),
        broker_constraints=BrokerConstraints(
            source="mt5",
            symbol="XAUUSD",
            as_of=at,
            freshness=_fresh("broker_constraints", at),
            trade_allowed=True,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point_size=0.01,
            tick_size=0.01,
            stops_level_points=20.0,
            freeze_level_points=10.0,
        ),
        market=MarketState(
            source="mt5",
            symbol="XAUUSD",
            as_of=at,
            freshness=_fresh("market", at),
            bid=2510.0 if side is PositionSide.BUY else 2489.8,
            ask=2510.2 if side is PositionSide.BUY else 2490.0,
            last=2510.1 if side is PositionSide.BUY else 2489.9,
            spread_points=20.0,
        ),
        symbol_digits=2,
        kill_switch_active=False,
        as_of=at,
        available_at=at,
    )


def _evaluate(context: PositionActionContext):
    policy = default_position_action_policy()
    safety = evaluate_position_action_safety(context, policy)
    return safety, build_position_action_intent(context, safety)


@pytest.mark.parametrize(
    "management_result",
    [PositionManagementResult.HOLD_POSITION, PositionManagementResult.NO_ACTION],
)
def test_non_actionable_management_maps_to_no_action_without_intent(
    management_result: PositionManagementResult,
) -> None:
    safety, intent = _evaluate(_context(management_result))
    assert safety.result is PositionActionSafetyResult.NO_ACTION
    assert safety.requested_action is PositionActionType.NO_ACTION
    assert intent is None


def test_safe_protection_creates_only_modify_stop_intent() -> None:
    context = _context(PositionManagementResult.PROTECT_POSITION)
    safety, intent = _evaluate(context)
    assert safety.result is PositionActionSafetyResult.PASS
    assert safety.requested_action is PositionActionType.MODIFY_PROTECTIVE_STOP
    assert isinstance(intent, PositionActionIntent)
    assert intent.action_type is PositionActionType.MODIFY_PROTECTIVE_STOP
    assert intent.requested_new_stop_loss == 2500.0
    assert intent.requested_close_volume_lots is None


def test_safe_exit_creates_full_close_not_opposing_entry() -> None:
    context = _context(PositionManagementResult.EXIT_POSITION)
    safety, intent = _evaluate(context)
    assert safety.result is PositionActionSafetyResult.PASS
    assert intent is not None
    assert intent.action_type is PositionActionType.CLOSE_POSITION
    assert intent.position_side is PositionSide.BUY
    assert intent.requested_close_volume_lots == context.position.volume_lots
    assert intent.requested_close_volume_lots <= intent.current_volume_lots
    assert not hasattr(intent, "order_type")
    assert not hasattr(intent, "requested_entry_price")


@pytest.mark.parametrize("unsafe_close_volume", [0.04, 0.06])
def test_position_action_intent_rejects_partial_or_excess_close(
    unsafe_close_volume: float,
) -> None:
    context = _context(PositionManagementResult.EXIT_POSITION)
    _, intent = _evaluate(context)
    assert intent is not None
    with pytest.raises(ValidationError, match="full close|exceed"):
        PositionActionIntent.model_validate(
            intent.model_dump()
            | {
                "intent_id": "",
                "requested_close_volume_lots": unsafe_close_volume,
            }
        )


@pytest.mark.parametrize(
    ("mutator", "reason"),
    [
        (
            lambda c: {"resume_readiness": ResumeReadiness(
                runtime_state_id="state-position",
                reconciliation_report_id=c.reconciliation.report_id,
                as_of=c.as_of,
                status=ResumeStatus.BLOCKED,
                reason_codes=(ResumeBlockReason.UNRESOLVED_EXECUTION_ANOMALY,),
            )},
            PositionActionReason.RUNTIME_NOT_SAFE,
        ),
        (
            lambda c: {"kill_switch_active": True},
            PositionActionReason.KILL_SWITCH_ACTIVE,
        ),
    ],
)
def test_hard_runtime_safety_states_emergency_block_without_intent(mutator, reason) -> None:
    context = _context(PositionManagementResult.EXIT_POSITION)
    changed = PositionActionContext.model_validate(
        context.model_dump() | {"context_id": ""} | mutator(context)
    )
    safety, intent = _evaluate(changed)
    assert safety.result is PositionActionSafetyResult.EMERGENCY_BLOCK
    assert reason in safety.reason_codes
    assert intent is None


@pytest.mark.parametrize(
    "kind",
    [ReconciliationKind.BROKER_ONLY, ReconciliationKind.LOCAL_ONLY, ReconciliationKind.CONFLICT],
)
def test_unresolved_reconciliation_anomaly_blocks_action(kind: ReconciliationKind) -> None:
    safety, intent = _evaluate(
        _context(PositionManagementResult.EXIT_POSITION, reconciliation_kind=kind)
    )
    assert safety.result is PositionActionSafetyResult.EMERGENCY_BLOCK
    assert PositionActionReason.RECONCILIATION_UNRESOLVED in safety.reason_codes
    assert intent is None


def test_unknown_execution_state_blocks_action() -> None:
    safety, intent = _evaluate(
        _context(
            PositionManagementResult.EXIT_POSITION,
            result_status=ExecutionResultStatus.UNKNOWN,
        )
    )
    assert safety.result is PositionActionSafetyResult.EMERGENCY_BLOCK
    assert PositionActionReason.UNKNOWN_EXECUTION_STATE in safety.reason_codes
    assert intent is None


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"broker_ticket": 999}, PositionActionReason.TICKET_MISMATCH),
        ({"symbol": "GOLD"}, PositionActionReason.SYMBOL_MISMATCH),
        ({"side": PositionSide.SELL}, PositionActionReason.DIRECTION_MISMATCH),
        ({"volume_lots": 0.04}, PositionActionReason.VOLUME_MISMATCH),
    ],
)
def test_authoritative_position_races_and_identity_mismatches_fail_closed(
    change: dict[str, object], reason: PositionActionReason
) -> None:
    context = _context(PositionManagementResult.EXIT_POSITION)
    assert context.position is not None
    changed_position = PositionState.model_validate(
        context.position.model_dump() | {"position_id": ""} | change
    )
    changed = PositionActionContext.model_validate(
        context.model_dump() | {"context_id": "", "position": changed_position}
    )
    safety, intent = _evaluate(changed)
    assert safety.result in {
        PositionActionSafetyResult.REJECT,
        PositionActionSafetyResult.EMERGENCY_BLOCK,
    }
    assert reason in safety.reason_codes
    assert intent is None


def test_missing_or_already_closed_position_never_creates_stale_close() -> None:
    safety, intent = _evaluate(_context(PositionManagementResult.EXIT_POSITION, position=None))
    assert safety.result is PositionActionSafetyResult.REJECT
    assert PositionActionReason.POSITION_MISSING in safety.reason_codes
    assert intent is None


def test_exact_linkage_is_required_and_approximate_similarity_is_irrelevant() -> None:
    context = _context(PositionManagementResult.EXIT_POSITION)
    bad_link = BrokerIntentLink(
        intent_id="xi-other",
        object_kind=BrokerObjectKind.POSITION,
        broker_object_id=context.broker_intent_link.broker_object_id,
        broker_ticket=context.broker_intent_link.broker_ticket,
        transport_execution_id=context.broker_intent_link.transport_execution_id,
    )
    changed = PositionActionContext.model_validate(
        context.model_dump() | {"context_id": "", "broker_intent_link": bad_link}
    )
    safety, intent = _evaluate(changed)
    assert safety.result is PositionActionSafetyResult.EMERGENCY_BLOCK
    assert PositionActionReason.EXACT_LINKAGE_MISMATCH in safety.reason_codes
    assert intent is None


@pytest.mark.parametrize(
    ("side", "old_stop", "requested"),
    [
        (PositionSide.BUY, 2490.0, 2489.0),
        (PositionSide.SELL, 2510.0, 2511.0),
    ],
)
def test_protective_stop_cannot_widen_long_or_short_risk(
    side: PositionSide, old_stop: float, requested: float
) -> None:
    with pytest.raises(ValidationError, match="increase risk"):
        _context(
            PositionManagementResult.PROTECT_POSITION,
            side=side,
            requested_stop=requested,
            position=_position(side, stop=old_stop),
        )


@pytest.mark.parametrize(
    ("side", "unsafe_stop"),
    [(PositionSide.BUY, 2489.0), (PositionSide.SELL, 2511.0)],
)
def test_position_action_intent_itself_rejects_wider_stop(
    side: PositionSide,
    unsafe_stop: float,
) -> None:
    context = _context(PositionManagementResult.PROTECT_POSITION, side=side)
    _, intent = _evaluate(context)
    assert intent is not None
    with pytest.raises(ValidationError, match="increase risk"):
        PositionActionIntent.model_validate(
            intent.model_dump()
            | {
                "intent_id": "",
                "requested_new_stop_loss": unsafe_stop,
            }
        )


def test_changed_stop_after_management_is_rejected_as_stale_authority() -> None:
    context = _context(PositionManagementResult.PROTECT_POSITION)
    assert context.position is not None
    changed_position = PositionState.model_validate(
        context.position.model_dump() | {"position_id": "", "stop_loss": 2495.0}
    )
    changed = PositionActionContext.model_validate(
        context.model_dump() | {"context_id": "", "position": changed_position}
    )
    safety, intent = _evaluate(changed)
    assert safety.result is PositionActionSafetyResult.REJECT
    assert PositionActionReason.CURRENT_STOP_CHANGED in safety.reason_codes
    assert intent is None


def test_new_stop_without_existing_stop_requires_policy_and_original_risk_reduction() -> None:
    context = _context(
        PositionManagementResult.PROTECT_POSITION,
        requested_stop=2495.0,
        position=_position(stop=None),
    )
    policy = default_position_action_policy().model_copy(
        update={"policy_id": "", "allow_add_protective_stop_when_missing": False}
    )
    policy = type(policy).model_validate(policy.model_dump())
    changed = PositionActionContext.model_validate(
        context.model_dump() | {"context_id": "", "policy_id": policy.policy_id}
    )
    safety = evaluate_position_action_safety(changed, policy)
    assert safety.result is PositionActionSafetyResult.REJECT
    assert PositionActionReason.MISSING_STOP_NOT_ALLOWED in safety.reason_codes


def test_stop_and_freeze_distance_and_stale_price_are_rejected() -> None:
    context = _context(PositionManagementResult.PROTECT_POSITION, requested_stop=2509.9)
    safety, _ = _evaluate(context)
    assert safety.result is PositionActionSafetyResult.REJECT
    assert PositionActionReason.BROKER_STOP_DISTANCE_VIOLATION in safety.reason_codes

    stale_at = AS_OF - timedelta(minutes=1)
    stale_market = MarketState.model_validate(
        context.market.model_dump()
        | {
            "as_of": stale_at,
            "freshness": _fresh("market", stale_at),
        }
    )
    stale_context = PositionActionContext.model_validate(
        context.model_dump() | {"context_id": "", "market": stale_market}
    )
    stale_safety, intent = _evaluate(stale_context)
    assert PositionActionReason.MARKET_PRICE_NOT_FRESH in stale_safety.reason_codes
    assert intent is None


def test_broker_unavailable_or_trade_disabled_rejects_action() -> None:
    context = _context(PositionManagementResult.PROTECT_POSITION)
    disabled = BrokerConstraints.model_validate(
        context.broker_constraints.model_dump() | {"trade_allowed": False}
    )
    changed = PositionActionContext.model_validate(
        context.model_dump() | {"context_id": "", "broker_constraints": disabled}
    )
    safety, intent = _evaluate(changed)
    assert safety.result is PositionActionSafetyResult.REJECT
    assert PositionActionReason.BROKER_TRADING_DISABLED in safety.reason_codes
    assert intent is None


@pytest.mark.parametrize(
    ("side", "requested", "expected"),
    [
        (PositionSide.BUY, 2500.001, 2500.01),
        (PositionSide.SELL, 2499.999, 2499.99),
    ],
)
def test_tick_normalization_only_tightens_risk(
    side: PositionSide, requested: float, expected: float
) -> None:
    context = _context(
        PositionManagementResult.PROTECT_POSITION,
        side=side,
        requested_stop=requested,
    )
    safety, intent = _evaluate(context)
    assert safety.result is PositionActionSafetyResult.PASS
    assert safety.normalized_protective_stop_loss == expected
    assert intent is not None and intent.requested_new_stop_loss == expected
    if side is PositionSide.BUY:
        assert expected >= requested
    else:
        assert expected <= requested


def test_stale_management_and_required_component_state_are_rejected() -> None:
    old = AS_OF - timedelta(minutes=2)
    context = _context(PositionManagementResult.EXIT_POSITION, at=old)
    current = PositionActionContext.model_validate(
        context.model_dump() | {"context_id": "", "as_of": AS_OF, "available_at": AS_OF}
    )
    safety, intent = _evaluate(current)
    assert safety.result is PositionActionSafetyResult.REJECT
    assert PositionActionReason.MANAGEMENT_OUTCOME_STALE in safety.reason_codes
    assert intent is None


def test_content_identities_are_deterministic_and_naive_time_is_rejected() -> None:
    first = _context(PositionManagementResult.PROTECT_POSITION)
    second = PositionActionContext.model_validate_json(first.model_dump_json())
    first_policy = default_position_action_policy()
    second_policy = default_position_action_policy()
    first_safety = evaluate_position_action_safety(first, first_policy)
    second_safety = evaluate_position_action_safety(second, second_policy)
    first_intent = build_position_action_intent(first, first_safety)
    second_intent = build_position_action_intent(second, second_safety)
    assert first_policy.policy_id == second_policy.policy_id
    assert first.context_id == second.context_id
    assert first_safety.safety_outcome_id == second_safety.safety_outcome_id
    assert first_intent is not None and second_intent is not None
    assert first_intent.intent_id == second_intent.intent_id
    with pytest.raises(ValidationError, match="timezone-aware"):
        PositionActionContext.model_validate(
            first.model_dump() | {"context_id": "", "as_of": AS_OF.replace(tzinfo=None)}
        )


def test_live_and_replay_canonical_inputs_have_identical_results_and_no_side_effects() -> None:
    context = _context(PositionManagementResult.EXIT_POSITION)
    policy = default_position_action_policy()
    before = context.model_dump_json()
    live = evaluate_position_action_safety(context, policy)
    replay_context = PositionActionContext.model_validate_json(before)
    replay_policy = type(policy).model_validate_json(policy.model_dump_json())
    replay = evaluate_position_action_safety(replay_context, replay_policy)
    assert live == replay
    assert build_position_action_intent(context, live) == build_position_action_intent(
        replay_context, replay
    )
    assert context.model_dump_json() == before


def test_append_only_management_chain_round_trip_and_duplicate_retry(tmp_path) -> None:
    context = _context(PositionManagementResult.PROTECT_POSITION)
    safety, intent = _evaluate(context)
    assert intent is not None
    journal = SQLiteRuntimeJournal(tmp_path / "runtime.sqlite3")
    first = append_position_action_chain(journal, context.management_outcome, safety, intent)
    second = append_position_action_chain(journal, context.management_outcome, safety, intent)
    assert first == second
    assert len(journal.records()) == 3
    assert [entry.record.record_type for entry in journal.records()] == [
        JournalRecordType.POSITION_MANAGEMENT_OUTCOME,
        JournalRecordType.POSITION_ACTION_SAFETY_OUTCOME,
        JournalRecordType.POSITION_ACTION_INTENT,
    ]
    assert [entry.record.decode() for entry in journal.records()] == [
        context.management_outcome,
        safety,
        intent,
    ]
    records = journal.records()
    assert records[1].record.previous_id == context.management_outcome.outcome_id
    assert records[2].record.previous_id == safety.safety_outcome_id
    with sqlite3.connect(journal.path) as connection, pytest.raises(
        sqlite3.IntegrityError, match="append-only"
    ):
        connection.execute("DELETE FROM runtime_journal")


def test_task7_has_no_broker_transport_or_exposure_increasing_actions() -> None:
    assert set(PositionActionType) == {
        PositionActionType.NO_ACTION,
        PositionActionType.MODIFY_PROTECTIVE_STOP,
        PositionActionType.CLOSE_POSITION,
    }
    import axq.position_actions as module

    assert not hasattr(module, "MetaTrader5")
    assert not hasattr(module, "ExecutionTransport")
