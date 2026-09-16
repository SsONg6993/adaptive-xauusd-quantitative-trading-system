from __future__ import annotations

from datetime import UTC, datetime, timedelta

from axq.agents import AgentEvidence, AgentStatus, DirectionalBias, HypothesisStatus
from axq.discipline import DisciplineOutcome, DisciplineReason, DisciplineResult
from axq.execution_boundary import ExecutionIntent, ExecutionResult, ExecutionResultStatus
from axq.experience import (
    AgentContributionExperience,
    AttributionStatus,
    DecisionExperience,
    ExperienceType,
    PositionManagementExperience,
    RejectedDecisionExperience,
    RejectionLayer,
    RuntimeAnomalyExperience,
    TradeExperience,
)
from axq.experience.attribution import AttributionSources, OutcomeAttributionBuilder
from axq.master import MasterProposal, SpecialistContribution
from axq.position_actions import (
    PositionActionSafetyOutcome,
    PositionActionSafetyResult,
    PositionActionType,
)
from axq.position_management import PositionManagementOutcome, PositionManagementResult
from axq.replay_validation import ReplaySide
from axq.replay_validation.outcomes import (
    ReplayEventContext,
    ReplayFillOutcome,
    ReplayOutcomeArtifact,
    ReplayTradeOutcome,
)
from axq.risk_boundary import RiskOutcome, RiskReason, RiskResult
from axq.schemas import Signal

T0 = datetime(2026, 8, 10, 10, 0, tzinfo=UTC)


def _contribution(status: AgentStatus = AgentStatus.READY) -> SpecialistContribution:
    return SpecialistContribution.model_construct(
        agent_name="chart",
        evidence_id="ae-1",
        status=status,
        direction=DirectionalBias.BULLISH,
        uncertainty=0.2,
    )


def _master(decision: Signal = Signal.BUY) -> MasterProposal:
    return MasterProposal.model_construct(
        proposal_id="mp-1",
        bundle_id="bundle-1",
        event_id="ev-1",
        as_of=T0,
        decision=decision,
        actionable=decision is not Signal.HOLD,
        confidence=0.8 if decision is not Signal.HOLD else 0.0,
        disagreement=0.1,
        contradiction=0.2,
        contributions=(_contribution(),),
        contributing_evidence_ids=("ae-1",),
    )


def _discipline(result: DisciplineResult = DisciplineResult.PASS) -> DisciplineOutcome:
    return DisciplineOutcome.model_construct(
        outcome_id="do-1",
        master_proposal_id="mp-1",
        evidence_bundle_id="bundle-1",
        setup_id="setup-1",
        thesis_id="thesis-1",
        scenario_id="scenario-1",
        as_of=T0,
        available_at=T0,
        master_decision=Signal.BUY,
        result=result,
        reason_codes=(
            DisciplineReason.PASSED
            if result is DisciplineResult.PASS
            else DisciplineReason.DAILY_TRADE_CAP,
        ),
    )


def _risk(result: RiskResult = RiskResult.PASS) -> RiskOutcome:
    return RiskOutcome.model_construct(
        outcome_id="ro-1",
        master_proposal_id="mp-1",
        evidence_bundle_id="bundle-1",
        discipline_outcome_id="do-1",
        setup_id="setup-1",
        thesis_id="thesis-1",
        scenario_id="scenario-1",
        symbol="XAUUSD",
        as_of=T0,
        available_at=T0,
        master_decision=Signal.BUY,
        result=result,
        reason_codes=(
            RiskReason.PASSED if result is RiskResult.PASS else RiskReason.TOTAL_DRAWDOWN_LIMIT,
        ),
    )


def _intent() -> ExecutionIntent:
    return ExecutionIntent.model_construct(
        intent_id="xi-1",
        evidence_bundle_id="bundle-1",
        master_proposal_id="mp-1",
        discipline_outcome_id="do-1",
        risk_outcome_id="ro-1",
        setup_id="setup-1",
        thesis_id="thesis-1",
        scenario_id="scenario-1",
        symbol="XAUUSD",
        point_size=0.01,
        direction=Signal.BUY,
        approved_volume_lots=0.1,
        stop_loss_price=2499.0,
        as_of=T0,
        available_at=T0,
    )


def _result() -> ExecutionResult:
    return ExecutionResult.model_construct(
        result_id="xr-1",
        execution_intent_id="xi-1",
        evidence_bundle_id="bundle-1",
        master_proposal_id="mp-1",
        discipline_outcome_id="do-1",
        risk_outcome_id="ro-1",
        setup_id="setup-1",
        thesis_id="thesis-1",
        scenario_id="scenario-1",
        symbol="XAUUSD",
        direction=Signal.BUY,
        status=ExecutionResultStatus.FILLED,
        fill_price=2500.0,
        event_time=T0,
        observed_at=T0,
        available_at=T0,
    )


def _evidence(status: AgentStatus = AgentStatus.READY) -> AgentEvidence:
    return AgentEvidence.model_construct(
        evidence_id="ae-1",
        agent_name="chart",
        agent_version="1.0.0",
        feature_snapshot_id="fs-1",
        as_of=T0,
        available_at=T0,
        hypothesis_id="hyp-1",
        hypothesis="bullish continuation",
        hypothesis_status=HypothesisStatus.CONFIRMED,
        direction=DirectionalBias.BULLISH,
        status=status,
        confidence=0.8 if status is not AgentStatus.ERROR else 0.0,
        uncertainty=0.2,
        evidence_quality=0.9,
        evidence_for=(),
        evidence_against=(),
        tool_inputs=(),
    )


def _outcomes() -> ReplayOutcomeArtifact:
    return ReplayOutcomeArtifact(
        source_metrics_id="replay-1",
        input_sha256="a" * 64,
        entry_model="NEXT_M5_OPEN_V1",
        stop_model="CAUSAL_BAR_TOUCH_V1",
        spread_model="HALF_RECORDED_SPREAD_EACH_SIDE_V1",
        slippage_points=1.0,
        fills=(
            ReplayFillOutcome(
                replay_fill_id="rfill-1",
                execution_intent_id="xi-1",
                execution_result_id="xr-1",
                position_id="rpos-1",
                direction=ReplaySide.BUY,
                volume_lots=0.1,
                fill_price=2500.0,
                executed_at=T0,
            ),
        ),
        trades=(
            ReplayTradeOutcome(
                replay_trade_id="rtrade-1",
                source_execution_intent_id="xi-1",
                position_id="rpos-1",
                direction=ReplaySide.BUY,
                volume_lots=0.1,
                opened_at=T0,
                closed_at=T0 + timedelta(minutes=15),
                entry_price=2500.0,
                exit_price=2499.0,
                initial_stop_loss=2499.0,
                exit_reason="PROTECTIVE_STOP",
                mfe_points=0.0,
                mae_points=100.0,
            ),
        ),
        event_contexts=(
            ReplayEventContext(
                runtime_event_id="ev-1",
                available_at=T0,
                session="LONDON",
            ),
        ),
    )


def _sources(**updates: object) -> AttributionSources:
    values: dict[str, object] = {
        "masters": (_master(),),
        "disciplines": (_discipline(),),
        "risks": (_risk(),),
        "execution_intents": (_intent(),),
        "execution_results": (_result(),),
        "agent_evidence": (_evidence(),),
        "replay_outcomes": _outcomes(),
    }
    values.update(updates)
    return AttributionSources(**values)  # type: ignore[arg-type]


def _of_type(sources: AttributionSources, kind: ExperienceType) -> tuple[object, ...]:
    return OutcomeAttributionBuilder().build(sources).of_type(kind)


def test_completed_trade_becomes_exactly_linked_trade_experience() -> None:
    values = _of_type(_sources(), ExperienceType.TRADE)

    assert len(values) == 1
    trade = values[0]
    assert isinstance(trade, TradeExperience)
    assert trade.execution_intent_id == "xi-1"
    assert trade.execution_result_id == "xr-1"
    assert trade.realized_pnl == -10.0
    assert trade.r_outcome == -1.0
    assert trade.mfe_points == 0.0
    assert trade.session == "LONDON"
    assert trade.provenance.agent_evidence_ids == ("ae-1",)
    assert trade.attribution_status is AttributionStatus.COMPLETE


def test_master_hold_becomes_decision_experience() -> None:
    master = _master(Signal.HOLD)
    discipline = _discipline(DisciplineResult.NO_ACTION)
    risk = _risk(RiskResult.NO_ACTION)
    values = _of_type(
        _sources(
            masters=(master,),
            disciplines=(discipline,),
            risks=(risk,),
            execution_intents=(),
            execution_results=(),
            replay_outcomes=ReplayOutcomeArtifact(
                source_metrics_id="replay-1",
                input_sha256="a" * 64,
                entry_model="NEXT_M5_OPEN_V1",
                stop_model="CAUSAL_BAR_TOUCH_V1",
                spread_model="HALF_RECORDED_SPREAD_EACH_SIDE_V1",
                slippage_points=1.0,
            ),
        ),
        ExperienceType.DECISION,
    )

    assert len(values) == 1
    assert isinstance(values[0], DecisionExperience)
    assert values[0].decision is Signal.HOLD
    assert values[0].progressed_to == "MASTER_HOLD"


def test_discipline_and_risk_blocks_become_separate_rejected_experiences() -> None:
    discipline_values = _of_type(
        _sources(
            disciplines=(_discipline(DisciplineResult.REJECT),),
            risks=(_risk(RiskResult.NO_ACTION),),
            execution_intents=(),
            execution_results=(),
            replay_outcomes=ReplayOutcomeArtifact(
                source_metrics_id="replay-1",
                input_sha256="a" * 64,
                entry_model="NEXT_M5_OPEN_V1",
                stop_model="CAUSAL_BAR_TOUCH_V1",
                spread_model="HALF_RECORDED_SPREAD_EACH_SIDE_V1",
                slippage_points=1.0,
            ),
        ),
        ExperienceType.REJECTED_DECISION,
    )
    risk_values = _of_type(
        _sources(
            risks=(_risk(RiskResult.REJECT),),
            execution_intents=(),
            execution_results=(),
            replay_outcomes=ReplayOutcomeArtifact(
                source_metrics_id="replay-1",
                input_sha256="a" * 64,
                entry_model="NEXT_M5_OPEN_V1",
                stop_model="CAUSAL_BAR_TOUCH_V1",
                spread_model="HALF_RECORDED_SPREAD_EACH_SIDE_V1",
                slippage_points=1.0,
            ),
        ),
        ExperienceType.REJECTED_DECISION,
    )

    assert isinstance(discipline_values[0], RejectedDecisionExperience)
    assert discipline_values[0].rejection_layer is RejectionLayer.DISCIPLINE
    assert isinstance(risk_values[0], RejectedDecisionExperience)
    assert risk_values[0].rejection_layer is RejectionLayer.RISK


def test_position_management_becomes_position_experience() -> None:
    management = PositionManagementOutcome.model_construct(
        outcome_id="pmo-1",
        position_id="rpos-1",
        original_execution_intent_id="xi-1",
        original_execution_result_id="xr-1",
        setup_id="setup-1",
        thesis_id="thesis-1",
        scenario_id="scenario-1",
        current_thesis_lifecycle=HypothesisStatus.CONFIRMED,
        result=PositionManagementResult.HOLD_POSITION,
        reason_codes=("THESIS_STABLE",),
        as_of=T0,
        available_at=T0,
    )
    safety = PositionActionSafetyOutcome.model_construct(
        safety_outcome_id="pas-1",
        position_management_outcome_id="pmo-1",
        position_id="rpos-1",
        result=PositionActionSafetyResult.NO_ACTION,
        requested_action=PositionActionType.NO_ACTION,
        reason_codes=("NO_ACTION",),
        as_of=T0,
        available_at=T0,
    )
    values = _of_type(
        _sources(position_management=(management,), position_action_safety=(safety,)),
        ExperienceType.POSITION_MANAGEMENT,
    )

    assert isinstance(values[0], PositionManagementExperience)
    assert values[0].management_result == "HOLD_POSITION"
    assert values[0].position_action_safety_outcome_id == "pas-1"
    assert values[0].protection_reached_transport is False


def test_agent_evidence_becomes_contribution_and_error_anomaly() -> None:
    normal = _of_type(_sources(), ExperienceType.AGENT_CONTRIBUTION)
    errored = _sources(
        agent_evidence=(_evidence(AgentStatus.ERROR),),
        masters=(
            MasterProposal.model_construct(
                **(_master().model_dump() | {"contributions": (_contribution(AgentStatus.ERROR),)})
            ),
        ),
    )
    anomalies = _of_type(errored, ExperienceType.RUNTIME_ANOMALY)

    assert isinstance(normal[0], AgentContributionExperience)
    assert normal[0].confidence == 0.8
    assert normal[0].tool_result_ids == ()
    assert isinstance(anomalies[0], RuntimeAnomalyExperience)
    assert anomalies[0].anomaly_type == "AGENT_ERROR"


def test_missing_exact_execution_result_is_explicitly_incomplete() -> None:
    values = _of_type(
        _sources(execution_results=()),
        ExperienceType.TRADE,
    )

    assert isinstance(values[0], TradeExperience)
    assert values[0].attribution_status is AttributionStatus.INCOMPLETE
    assert values[0].missing_links == ("EXECUTION_RESULT:xr-1",)
