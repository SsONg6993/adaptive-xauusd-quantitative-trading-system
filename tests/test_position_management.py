from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.agents import (
    AgentEvidence,
    AgentInput,
    AgentMemory,
    AgentStatus,
    ContinuityStatus,
    DirectionalBias,
    EntryEligibility,
    HypothesisInvalidation,
    HypothesisRelationship,
    HypothesisStatus,
    ScenarioState,
    ScenarioStatus,
    ThesisState,
    transition_memory,
)
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
from axq.position_management import (
    MissingEvidenceBehavior,
    PositionManagementContext,
    PositionManagementOutcome,
    PositionManagementPolicy,
    PositionManagementReason,
    PositionManagementResult,
    default_demo_position_management_policy,
    evaluate_position,
)
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    FreshnessStatus,
    PositionSide,
    PositionState,
)
from axq.runtime.kernel import AGENT_ORDER, EvidenceBundle
from axq.schemas import Signal

T0 = datetime(2025, 1, 6, 12, 0, tzinfo=UTC)
AS_OF = T0 + timedelta(minutes=5)


def _fresh(component: str, *, at: datetime = AS_OF) -> ComponentFreshness:
    return ComponentFreshness(
        component=component,
        status=FreshnessStatus.AVAILABLE,
        observed_at=at,
        available_at=at,
        stale_after_ms=30_000,
    )


def _thesis(
    status: HypothesisStatus = HypothesisStatus.ACTIVE,
    *,
    scenario_status: ScenarioStatus | None = None,
    continuity: ContinuityStatus = ContinuityStatus.COMPLETE,
) -> ThesisState:
    scenario_status = scenario_status or (
        ScenarioStatus.CONFIRMED
        if status is HypothesisStatus.CONFIRMED
        else ScenarioStatus.INVALIDATED
        if status is HypothesisStatus.INVALIDATED
        else ScenarioStatus.EXPIRED
        if status is HypothesisStatus.EXPIRED
        else ScenarioStatus.WEAKENED
        if status is HypothesisStatus.WEAKENING
        else ScenarioStatus.WATCHING
    )
    eligibility = (
        EntryEligibility.ELIGIBLE
        if scenario_status is ScenarioStatus.CONFIRMED
        else EntryEligibility.INVALIDATED
        if scenario_status is ScenarioStatus.INVALIDATED
        else EntryEligibility.EXPIRED
        if scenario_status is ScenarioStatus.EXPIRED
        else EntryEligibility.WATCHING
    )
    scenario = ScenarioState(
        parent_thesis_id="thesis-position",
        name="continuation",
        status=scenario_status,
        confirmation_facts=("micro_break",),
        invalidation_facts=("structure_break",),
        matched_confirmation_facts=("micro_break",)
        if eligibility is EntryEligibility.ELIGIBLE
        else (),
        confirmation_progress=1.0 if eligibility is EntryEligibility.ELIGIBLE else 0.0,
        confidence=0.8,
        began_at=T0,
        updated_at=AS_OF,
        expires_at=AS_OF + timedelta(minutes=10),
        entry_eligibility=eligibility,
        evidence_ids=("ae-position",),
        tool_result_ids=("tr-position",),
    )
    invalidated = status is HypothesisStatus.INVALIDATED
    invalidation = HypothesisInvalidation(
        invalidated=invalidated,
        reason="structure broke" if invalidated else None,
    )
    relationship = (
        HypothesisRelationship.INVALIDATED
        if invalidated
        else HypothesisRelationship.EXPIRED
        if status is HypothesisStatus.EXPIRED
        else HypothesisRelationship.WEAKENED
        if status is HypothesisStatus.WEAKENING
        else HypothesisRelationship.UNCHANGED
    )
    memory = AgentMemory(
        agent_name="chart",
        agent_version="1.0.0",
        hypothesis_id="hyp-position",
        current_hypothesis="bullish continuation",
        current_confidence=0.8,
        running_uncertainty=0.2,
        hypothesis_status=status,
        relationship=relationship,
        began_at=T0,
        updated_at=AS_OF,
        supporting_evidence_history=("ae-position",),
        invalidation=invalidation,
        latest_evidence_id="ae-position",
        setup_id="setup-position",
        thesis_id="thesis-position",
    )
    expires_at = AS_OF if status is HypothesisStatus.EXPIRED else AS_OF + timedelta(minutes=10)
    return ThesisState(
        thesis_id="thesis-position",
        symbol="XAUUSD",
        agent_name="chart",
        agent_version="1.0.0",
        hypothesis_id="hyp-position",
        hypothesis="bullish continuation",
        direction=DirectionalBias.BULLISH,
        hypothesis_status=status,
        relationship=relationship,
        runtime_state_id="state-position",
        feature_snapshot_id="fs-position",
        began_at=T0,
        updated_at=AS_OF,
        expires_at=expires_at,
        m5_bars_observed=2,
        entry_eligibility=eligibility,
        scenarios=(scenario,),
        evidence_ids=("ae-position",),
        latest_evidence_id="ae-position",
        latest_evidence_as_of=AS_OF,
        latest_evidence_available_at=AS_OF,
        agent_memory=memory,
        last_event_id="event-position",
        last_event_time=AS_OF,
        last_observed_at=AS_OF,
        last_available_at=AS_OF,
        last_source_sequence=10,
        continuity_status=continuity,
    )


def _position(
    side: PositionSide = PositionSide.BUY,
    *,
    stop_loss: float | None = None,
    current_price: float | None = None,
) -> PositionState:
    return PositionState(
        source="mt5",
        broker_ticket=123,
        symbol="XAUUSD",
        side=side,
        volume_lots=0.05,
        opened_at=T0,
        open_price=2500.0,
        current_price=(2510.0 if side is PositionSide.BUY else 2490.0)
        if current_price is None
        else current_price,
        stop_loss=(2490.0 if side is PositionSide.BUY else 2510.0)
        if stop_loss is None
        else stop_loss,
        floating_pnl=50.0,
        setup_id="setup-position",
        thesis_id="thesis-position",
    )


def _evidence_bundle() -> EvidenceBundle:
    evidence = tuple(
        AgentEvidence(
            agent_name=name,
            agent_version="1.0.0",
            runtime_state_id="state-position",
            as_of=AS_OF,
            available_at=AS_OF,
            hypothesis_id=f"hyp-{name}",
            hypothesis=f"{name} current evidence",
            hypothesis_status=HypothesisStatus.ACTIVE,
            relationship=HypothesisRelationship.NEW,
            direction=DirectionalBias.BULLISH,
            confidence=0.7,
            uncertainty=0.2,
            evidence_quality=0.8,
            invalidation=HypothesisInvalidation(invalidated=False),
            freshness=FreshnessStatus.AVAILABLE,
            status=AgentStatus.READY,
        )
        for name in AGENT_ORDER
    )
    return EvidenceBundle(
        event_id="event-position",
        runtime_state_id="state-position",
        as_of=AS_OF,
        agent_inputs=tuple(
            AgentInput(runtime_state_id="state-position", as_of=AS_OF, tool_results=())
            for _ in AGENT_ORDER
        ),
        evidence=evidence,
        memories=tuple(transition_memory(None, item) for item in evidence),
    )


def _intent(thesis: ThesisState, side: PositionSide = PositionSide.BUY) -> ExecutionIntent:
    return ExecutionIntent(
        evidence_bundle_id="eb-position",
        master_proposal_id="mp-position",
        discipline_outcome_id="do-position",
        risk_outcome_id="ro-position",
        risk_context_id="rc-position",
        setup_id="setup-position",
        thesis_id=thesis.thesis_id,
        scenario_id=thesis.scenarios[0].scenario_id,
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
        reason="acknowledgement unknown" if unknown else None,
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


def _context(
    status: HypothesisStatus = HypothesisStatus.ACTIVE,
    *,
    side: PositionSide = PositionSide.BUY,
    scenario_status: ScenarioStatus | None = None,
    position: PositionState | None | object = ...,
    result_status: ExecutionResultStatus = ExecutionResultStatus.FILLED,
    readiness_status: ResumeStatus = ResumeStatus.SAFE,
    reconciliation_kind: ReconciliationKind = ReconciliationKind.MATCHED,
    position_freshness: ComponentFreshness | None = None,
    continuity: ContinuityStatus = ContinuityStatus.COMPLETE,
    include_thesis: bool = True,
    include_link: bool = True,
    include_evidence: bool = True,
    broker_changes: dict[str, object] | None = None,
) -> PositionManagementContext:
    thesis = _thesis(status, scenario_status=scenario_status, continuity=continuity)
    actual_position = _position(side) if position is ... else position
    if actual_position is None:
        reconciliation = _reconciliation(None, None, reconciliation_kind)
        return PositionManagementContext(
            runtime_state_id="state-position",
            as_of=AS_OF,
            available_at=AS_OF,
            position=None,
            account=AccountState(
                source="mt5",
                account_id="demo",
                as_of=AS_OF,
                freshness=_fresh("account"),
                balance=10_000.0,
                equity=10_050.0,
            ),
            position_freshness=position_freshness or _fresh("positions"),
            broker_constraints=_broker_constraints(broker_changes),
            reconciliation=reconciliation,
            resume_readiness=_readiness(readiness_status, reconciliation.report_id),
            intrabar_continuity=continuity,
        )
    assert isinstance(actual_position, PositionState)
    intent = _intent(thesis, side)
    result = _result(intent, result_status)
    link = BrokerIntentLink(
        intent_id=intent.intent_id,
        object_kind=BrokerObjectKind.POSITION,
        broker_object_id=actual_position.position_id,
        broker_ticket=actual_position.broker_ticket,
        transport_execution_id=result.transport_execution_id,
    )
    reconciliation = _reconciliation(intent, actual_position, reconciliation_kind)
    return PositionManagementContext(
        runtime_state_id="state-position",
        as_of=AS_OF,
        available_at=AS_OF,
        position=actual_position,
        original_execution_intent=intent,
        original_execution_result=result,
        broker_intent_link=link if include_link else None,
        thesis=thesis if include_thesis else None,
        evidence_bundle=_evidence_bundle() if include_evidence else None,
        account=AccountState(
            source="mt5",
            account_id="demo",
            as_of=AS_OF,
            freshness=_fresh("account"),
            balance=10_000.0,
            equity=10_050.0,
            floating_pnl=50.0,
        ),
        position_freshness=position_freshness or _fresh("positions"),
        broker_constraints=_broker_constraints(broker_changes),
        reconciliation=reconciliation,
        resume_readiness=_readiness(readiness_status, reconciliation.report_id),
        intrabar_continuity=continuity,
        unrealized_r_multiple=0.5,
        mfe_points=1200.0,
        mae_points=300.0,
    )


def _broker_constraints(changes: dict[str, object] | None = None) -> BrokerConstraints:
    values: dict[str, object] = {
        "source": "mt5",
        "symbol": "XAUUSD",
        "as_of": AS_OF,
        "freshness": _fresh("broker_constraints"),
        "trade_allowed": True,
        "point_size": 0.01,
        "stops_level_points": 10.0,
        "freeze_level_points": 5.0,
    }
    values.update(changes or {})
    return BrokerConstraints.model_validate(values)


def _reconciliation(
    intent: ExecutionIntent | None,
    position: PositionState | None,
    kind: ReconciliationKind,
) -> ReconciliationReport:
    if intent is None or position is None:
        findings: tuple[ReconciliationFinding, ...] = ()
    else:
        findings = (
            ReconciliationFinding(
                kind=kind,
                status=ResolutionStatus.RESOLVED
                if kind is ReconciliationKind.MATCHED
                else ResolutionStatus.RECONCILIATION_REQUIRED,
                intent_id=intent.intent_id if kind is not ReconciliationKind.BROKER_ONLY else None,
                broker_object_id=position.position_id,
                broker_ticket=position.broker_ticket,
                reason_code="EXACT_LINK_MATCH" if kind is ReconciliationKind.MATCHED else "ANOMALY",
            ),
        )
    status = (
        ResolutionStatus.RESOLVED
        if all(item.status is ResolutionStatus.RESOLVED for item in findings)
        else ResolutionStatus.RECONCILIATION_REQUIRED
    )
    return ReconciliationReport(
        snapshot_id="snapshot-position",
        as_of=AS_OF,
        available_at=AS_OF,
        status=status,
        findings=findings,
    )


def _readiness(status: ResumeStatus, report_id: str) -> ResumeReadiness:
    return ResumeReadiness(
        runtime_state_id="state-position",
        reconciliation_report_id=report_id,
        as_of=AS_OF,
        status=status,
        reason_codes=()
        if status is ResumeStatus.SAFE
        else (ResumeBlockReason.UNRESOLVED_EXECUTION_ANOMALY,),
    )


def test_no_open_position_is_no_action() -> None:
    outcome = evaluate_position(_context(position=None), default_demo_position_management_policy())
    assert outcome.result is PositionManagementResult.NO_ACTION
    assert outcome.reason_codes == (PositionManagementReason.NO_OPEN_POSITION,)
    assert not outcome.eligible_for_position_action


@pytest.mark.parametrize("status", [HypothesisStatus.ACTIVE, HypothesisStatus.CONFIRMED])
def test_stable_thesis_holds_without_modification(status: HypothesisStatus) -> None:
    outcome = evaluate_position(_context(status), default_demo_position_management_policy())
    assert outcome.result is PositionManagementResult.HOLD_POSITION
    assert outcome.requested_protective_stop_loss is None


def test_weakening_thesis_requests_broker_valid_break_even_protection() -> None:
    outcome = evaluate_position(
        _context(HypothesisStatus.WEAKENING), default_demo_position_management_policy()
    )
    assert outcome.result is PositionManagementResult.PROTECT_POSITION
    assert outcome.requested_protective_stop_loss == 2500.0
    assert outcome.eligible_for_position_action


def test_invalidated_thesis_requests_exit_without_transport() -> None:
    outcome = evaluate_position(
        _context(HypothesisStatus.INVALIDATED), default_demo_position_management_policy()
    )
    assert outcome.result is PositionManagementResult.EXIT_POSITION
    assert outcome.reason_codes == (PositionManagementReason.THESIS_INVALIDATED,)
    assert not hasattr(outcome, "broker_command")
    assert not hasattr(outcome, "reverse_direction")


def test_expired_thesis_obeys_explicit_policy() -> None:
    context = _context(HypothesisStatus.EXPIRED)
    exit_outcome = evaluate_position(context, default_demo_position_management_policy())
    policy = PositionManagementPolicy.model_validate(
        default_demo_position_management_policy().model_dump()
        | {"policy_id": "", "exit_on_thesis_expired": False}
    )
    hold_outcome = evaluate_position(context, policy)
    assert exit_outcome.result is PositionManagementResult.EXIT_POSITION
    assert hold_outcome.result is PositionManagementResult.HOLD_POSITION


def test_scenario_invalidation_requests_exit() -> None:
    outcome = evaluate_position(
        _context(HypothesisStatus.ACTIVE, scenario_status=ScenarioStatus.INVALIDATED),
        default_demo_position_management_policy(),
    )
    assert outcome.result is PositionManagementResult.EXIT_POSITION
    assert PositionManagementReason.SCENARIO_INVALIDATED in outcome.reason_codes


def test_missing_thesis_or_exact_link_fails_closed() -> None:
    policy = default_demo_position_management_policy()
    missing_thesis = evaluate_position(_context(include_thesis=False), policy)
    missing_link = evaluate_position(_context(include_link=False), policy)
    assert missing_thesis.result is PositionManagementResult.NO_ACTION
    assert PositionManagementReason.MISSING_THESIS_LINKAGE in missing_thesis.reason_codes
    assert missing_link.result is PositionManagementResult.NO_ACTION
    assert PositionManagementReason.MISSING_EXACT_EXECUTION_LINKAGE in missing_link.reason_codes


def test_stale_position_state_fails_closed() -> None:
    stale = ComponentFreshness(
        component="positions",
        status=FreshnessStatus.STALE,
        observed_at=T0,
        available_at=T0,
        stale_after_ms=30_000,
    )
    outcome = evaluate_position(
        _context(position_freshness=stale), default_demo_position_management_policy()
    )
    assert outcome.result is PositionManagementResult.NO_ACTION
    assert PositionManagementReason.POSITION_STATE_NOT_FRESH in outcome.reason_codes


@pytest.mark.parametrize("component", ["account", "broker_constraints"])
def test_stale_account_or_broker_constraints_fail_closed(component: str) -> None:
    context = _context()
    stale = ComponentFreshness(
        component=component,
        status=FreshnessStatus.STALE,
        observed_at=T0,
        available_at=T0,
        stale_after_ms=30_000,
    )
    changes: dict[str, object] = {"context_id": ""}
    if component == "account":
        changes["account"] = AccountState.model_validate(
            context.account.model_dump() | {"freshness": stale}
        )
        expected = PositionManagementReason.ACCOUNT_STATE_NOT_FRESH
    else:
        changes["broker_constraints"] = BrokerConstraints.model_validate(
            context.broker_constraints.model_dump() | {"freshness": stale}
        )
        expected = PositionManagementReason.BROKER_CONSTRAINTS_NOT_FRESH
    stale_context = PositionManagementContext.model_validate(context.model_dump() | changes)
    outcome = evaluate_position(stale_context, default_demo_position_management_policy())
    assert outcome.result is PositionManagementResult.NO_ACTION
    assert expected in outcome.reason_codes


def test_missing_intrabar_continuity_fails_closed() -> None:
    outcome = evaluate_position(
        _context(continuity=ContinuityStatus.MISSING_INTRABAR_DATA),
        default_demo_position_management_policy(),
    )
    assert outcome.result is PositionManagementResult.NO_ACTION
    assert PositionManagementReason.INTRABAR_CONTINUITY_MISSING in outcome.reason_codes


@pytest.mark.parametrize(
    ("readiness", "kind", "reason"),
    [
        (
            ResumeStatus.BLOCKED,
            ReconciliationKind.MATCHED,
            PositionManagementReason.RUNTIME_NOT_SAFE,
        ),
        (
            ResumeStatus.BLOCKED,
            ReconciliationKind.BROKER_ONLY,
            PositionManagementReason.RECONCILIATION_UNRESOLVED,
        ),
    ],
)
def test_unsafe_or_broker_only_recovery_blocks_management(
    readiness: ResumeStatus,
    kind: ReconciliationKind,
    reason: PositionManagementReason,
) -> None:
    outcome = evaluate_position(
        _context(readiness_status=readiness, reconciliation_kind=kind),
        default_demo_position_management_policy(),
    )
    assert outcome.result is PositionManagementResult.NO_ACTION
    assert reason in outcome.reason_codes


def test_unknown_submission_blocks_management_even_with_a_link() -> None:
    outcome = evaluate_position(
        _context(result_status=ExecutionResultStatus.UNKNOWN),
        default_demo_position_management_policy(),
    )
    assert outcome.result is PositionManagementResult.NO_ACTION
    assert PositionManagementReason.UNKNOWN_EXECUTION_STATE in outcome.reason_codes


def test_restart_reconciled_exact_linkage_allows_management() -> None:
    context = PositionManagementContext.model_validate_json(_context().model_dump_json())
    outcome = evaluate_position(context, default_demo_position_management_policy())
    assert context.original_execution_intent is not None
    assert context.position is not None
    assert outcome.result is PositionManagementResult.HOLD_POSITION
    assert outcome.original_execution_intent_id == context.original_execution_intent.intent_id
    assert outcome.position_id == context.position.position_id


@pytest.mark.parametrize(
    ("side", "existing_stop"),
    [(PositionSide.BUY, 2501.0), (PositionSide.SELL, 2499.0)],
)
def test_existing_stronger_stop_is_never_moved_back_to_break_even(
    side: PositionSide, existing_stop: float
) -> None:
    context = _context(
        HypothesisStatus.WEAKENING,
        side=side,
        position=_position(side, stop_loss=existing_stop),
    )
    outcome = evaluate_position(context, default_demo_position_management_policy())
    assert outcome.result is PositionManagementResult.HOLD_POSITION
    assert outcome.requested_protective_stop_loss is None
    assert PositionManagementReason.ALREADY_PROTECTED in outcome.reason_codes


def test_break_even_is_not_requested_when_broker_stop_or_freeze_distance_is_invalid() -> None:
    context = _context(
        HypothesisStatus.WEAKENING,
        position=_position(current_price=2500.05),
        broker_changes={"stops_level_points": 10.0, "freeze_level_points": 10.0},
    )
    outcome = evaluate_position(context, default_demo_position_management_policy())
    assert outcome.result is PositionManagementResult.HOLD_POSITION
    assert PositionManagementReason.BROKER_PROTECTION_CONSTRAINT in outcome.reason_codes


def test_protection_respects_minimum_age_and_maximum_stop_change() -> None:
    context = _context(HypothesisStatus.WEAKENING)
    base = default_demo_position_management_policy()
    too_young = PositionManagementPolicy.model_validate(
        base.model_dump() | {"policy_id": "", "minimum_position_age_seconds": 600.0}
    )
    young_outcome = evaluate_position(context, too_young)
    assert young_outcome.result is PositionManagementResult.HOLD_POSITION
    assert PositionManagementReason.POSITION_TOO_YOUNG_FOR_PROTECTION in young_outcome.reason_codes

    capped = PositionManagementPolicy.model_validate(
        base.model_dump() | {"policy_id": "", "max_protective_sl_change_points": 100.0}
    )
    capped_outcome = evaluate_position(context, capped)
    assert capped_outcome.result is PositionManagementResult.PROTECT_POSITION
    assert capped_outcome.requested_protective_stop_loss == 2491.0


def test_policy_context_and_outcome_identities_are_deterministic_and_content_bound() -> None:
    first_policy = default_demo_position_management_policy()
    second_policy = default_demo_position_management_policy()
    context = _context()
    restored = PositionManagementContext.model_validate_json(context.model_dump_json())
    first_outcome = evaluate_position(context, first_policy)
    second_outcome = evaluate_position(restored, second_policy)
    assert first_policy.policy_id == second_policy.policy_id
    assert context.context_id == restored.context_id
    assert first_outcome.outcome_id == second_outcome.outcome_id
    changed = PositionManagementPolicy.model_validate(
        first_policy.model_dump() | {"policy_id": "", "minimum_position_age_seconds": 600.0}
    )
    assert changed.policy_id != first_policy.policy_id


def test_naive_timestamps_and_forged_ids_are_rejected() -> None:
    context = _context()
    with pytest.raises(ValidationError, match="timezone-aware"):
        PositionManagementContext.model_validate(
            context.model_dump() | {"context_id": "", "as_of": AS_OF.replace(tzinfo=None)}
        )
    with pytest.raises(ValidationError, match="context_id"):
        PositionManagementContext.model_validate(
            context.model_dump() | {"context_id": "pmc-forged"}
        )


def test_context_rejects_mismatched_execution_and_position_provenance() -> None:
    context = _context()
    assert context.original_execution_intent is not None
    bad_intent = ExecutionIntent.model_validate(
        context.original_execution_intent.model_dump()
        | {"intent_id": "", "setup_id": "different-setup"}
    )
    with pytest.raises(ValidationError, match="setup"):
        PositionManagementContext.model_validate(
            context.model_dump() | {"context_id": "", "original_execution_intent": bad_intent}
        )


def test_evaluation_is_pure_and_has_no_scale_or_reversal_outcome() -> None:
    context = _context(HypothesisStatus.INVALIDATED)
    policy = default_demo_position_management_policy()
    before_context = context.model_dump_json()
    before_policy = policy.model_dump_json()
    outcome = evaluate_position(context, policy)
    assert context.model_dump_json() == before_context
    assert policy.model_dump_json() == before_policy
    assert outcome.result is PositionManagementResult.EXIT_POSITION
    assert set(PositionManagementResult) == {
        PositionManagementResult.NO_ACTION,
        PositionManagementResult.HOLD_POSITION,
        PositionManagementResult.PROTECT_POSITION,
        PositionManagementResult.EXIT_POSITION,
    }


def test_live_and_replay_callers_get_identical_outcomes_for_identical_canonical_input() -> None:
    context = _context(HypothesisStatus.WEAKENING)
    policy = default_demo_position_management_policy()
    live_outcome = evaluate_position(context, policy)
    replay_outcome = evaluate_position(
        PositionManagementContext.model_validate(context.model_dump()),
        PositionManagementPolicy.model_validate(policy.model_dump()),
    )
    assert live_outcome == replay_outcome


def test_direct_protection_outcome_cannot_increase_long_or_short_risk() -> None:
    for side, old_stop, unsafe_stop in (
        (PositionSide.BUY, 2490.0, 2489.0),
        (PositionSide.SELL, 2510.0, 2511.0),
    ):
        context = _context(side=side, position=_position(side, stop_loss=old_stop))
        valid = evaluate_position(
            _context(
                HypothesisStatus.WEAKENING,
                side=side,
                position=_position(side, stop_loss=old_stop),
            ),
            default_demo_position_management_policy(),
        )
        payload = valid.model_dump() | {
            "outcome_id": "",
            "position_management_context_id": context.context_id,
            "existing_stop_loss": old_stop,
            "requested_protective_stop_loss": unsafe_stop,
        }
        with pytest.raises(ValidationError, match="increase risk"):
            PositionManagementOutcome.model_validate(payload)


def test_missing_evidence_policy_is_explicit_and_cannot_authorize_action() -> None:
    policy = PositionManagementPolicy.model_validate(
        default_demo_position_management_policy().model_dump()
        | {
            "policy_id": "",
            "missing_evidence_behavior": MissingEvidenceBehavior.NO_ACTION,
        }
    )
    outcome = evaluate_position(_context(include_evidence=False), policy)
    assert outcome.result is PositionManagementResult.NO_ACTION
    assert PositionManagementReason.EVIDENCE_MISSING in outcome.reason_codes
    assert not outcome.eligible_for_position_action


def test_default_missing_evidence_behavior_holds_and_never_requests_protection() -> None:
    outcome = evaluate_position(
        _context(HypothesisStatus.WEAKENING, include_evidence=False),
        default_demo_position_management_policy(),
    )
    assert outcome.result is PositionManagementResult.HOLD_POSITION
    assert outcome.reason_codes == (PositionManagementReason.EVIDENCE_MISSING,)
    assert outcome.requested_protective_stop_loss is None
