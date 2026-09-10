from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from axq.agents import AgentStatus, DirectionalBias, HypothesisStatus
from axq.experience import (
    AgentContributionExperience,
    ExperienceProvenance,
    PositionManagementExperience,
    RejectedDecisionExperience,
    RejectionLayer,
    RuntimeAnomalyExperience,
    TradeExperience,
)
from axq.reflection import (
    FindingCategory,
    FindingSignal,
    ReflectionPolicy,
    SampleGuardStatus,
    build_daily_reflection,
)
from axq.schemas import Signal

DAY = date(2026, 8, 10)
START = datetime(2026, 8, 10, tzinfo=UTC)


def _provenance(index: int) -> ExperienceProvenance:
    return ExperienceProvenance(runtime_event_ids=(f"ev-{index}",))


def _trade(
    index: int,
    *,
    direction: Signal = Signal.BUY,
    r_outcome: float = -1.0,
    available_at: datetime | None = None,
    session: str | None = "LONDON",
    regime: str | None = "TREND",
    confidence: float | None = 0.8,
    mfe: float | None = 10.0,
    mae: float | None = 20.0,
) -> TradeExperience:
    at = available_at or START + timedelta(hours=index)
    won = r_outcome > 0
    evidence_id = f"ae-{index}"
    return TradeExperience(
        occurred_at=at,
        available_at=at,
        symbol="XAUUSD",
        session=session,
        regime=regime,
        outcome="POSITION_ACTION_CLOSE",
        provenance=ExperienceProvenance(
            runtime_event_ids=(f"ev-{index}",),
            agent_evidence_ids=(evidence_id,),
        ),
        replay_trade_id=f"trade-{index}",
        execution_intent_id=f"intent-{index}",
        execution_result_id=f"result-{index}",
        replay_fill_id=f"fill-{index}",
        position_id=f"position-{index}",
        direction=direction,
        entry_time=at - timedelta(minutes=15),
        exit_time=at,
        entry_price=2500.0,
        exit_price=2501.0 if won else 2499.0,
        volume_lots=0.1,
        realized_pnl=10.0 if won else -10.0,
        r_outcome=r_outcome,
        mfe_points=mfe,
        mae_points=mae,
        holding_seconds=900.0,
        exit_cause="POSITION_ACTION_CLOSE",
        stop_triggered=False,
        explicit_position_exit=True,
        master_confidence=confidence,
        specialist_evidence_ids=(evidence_id,),
    )


def _rejection(index: int, reason: str = "DAILY_TRADE_CAP") -> RejectedDecisionExperience:
    at = START + timedelta(hours=index)
    return RejectedDecisionExperience(
        occurred_at=at,
        available_at=at,
        symbol="XAUUSD",
        outcome="DISCIPLINE",
        provenance=_provenance(index),
        rejection_layer=RejectionLayer.DISCIPLINE,
        source_proposal_id=f"proposal-{index}",
        source_outcome_id=f"discipline-{index}",
        reason_codes=(reason,),
        master_confidence=0.7,
    )


def _agent(index: int) -> AgentContributionExperience:
    at = START + timedelta(hours=index)
    return AgentContributionExperience(
        occurred_at=at,
        available_at=at,
        symbol="XAUUSD",
        specialist="chart",
        outcome="BUY",
        provenance=ExperienceProvenance(
            runtime_event_ids=(f"ev-{index}",),
            agent_evidence_ids=(f"ae-{index}",),
        ),
        agent_evidence_id=f"ae-{index}",
        hypothesis_id=f"hyp-{index}",
        hypothesis="long continuation",
        direction=DirectionalBias.BULLISH,
        lifecycle=HypothesisStatus.CONFIRMED,
        status=AgentStatus.READY,
        confidence=0.8,
        uncertainty=0.2,
        evidence_quality=0.8,
        evidence_for_count=2,
        evidence_against_count=0,
        master_proposal_id=f"proposal-{index}",
        master_decision=Signal.BUY,
        downstream_outcome="TRADE_COMPLETED",
    )


def _management(index: int) -> PositionManagementExperience:
    at = START + timedelta(hours=index)
    return PositionManagementExperience(
        occurred_at=at,
        available_at=at,
        symbol="XAUUSD",
        outcome="HOLD_POSITION",
        provenance=_provenance(index + 100),
        position_management_outcome_id=f"pm-{index}",
        position_id=f"position-{index}",
        original_execution_intent_id=f"intent-{index}",
        original_execution_result_id=f"result-{index}",
        management_result="HOLD_POSITION",
        reason_codes=("THESIS_STABLE",),
        current_thesis_lifecycle=HypothesisStatus.ACTIVE,
        protection_reached_transport=False,
    )


def _findings(reflection: object, category: FindingCategory) -> tuple[object, ...]:
    return tuple(
        finding
        for finding in reflection.findings  # type: ignore[attr-defined]
        if finding.category is category
    )


def test_daily_aggregation_uses_available_at_utc_and_measures_group_outcomes() -> None:
    records = (
        _trade(1, direction=Signal.BUY, r_outcome=-1.0, session="LONDON"),
        _trade(2, direction=Signal.BUY, r_outcome=-0.5, session="LONDON"),
        _trade(3, direction=Signal.SELL, r_outcome=1.0, session="NEW_YORK"),
        _trade(4, direction=Signal.SELL, r_outcome=0.5, session="NEW_YORK"),
        _trade(5, available_at=START - timedelta(seconds=1)),
        _trade(6, available_at=START + timedelta(days=1)),
    )
    reflection = build_daily_reflection(
        records,
        DAY,
        ReflectionPolicy(min_trade_group_samples=2),
    )

    assert len(reflection.input_experience_ids) == 4
    direction = _findings(reflection, FindingCategory.DIRECTION_OUTCOME)
    assert {(item.scope_value, item.signal) for item in direction} == {
        ("BUY", FindingSignal.NEGATIVE),
        ("SELL", FindingSignal.POSITIVE),
    }
    sessions = _findings(reflection, FindingCategory.SESSION_OUTCOME)
    assert {(item.scope_value, item.signal) for item in sessions} == {
        ("LONDON", FindingSignal.NEGATIVE),
        ("NEW_YORK", FindingSignal.POSITIVE),
    }


def test_minimum_sample_guards_are_explicit_and_unavailable_is_not_zero() -> None:
    reflection = build_daily_reflection(
        (_trade(1, regime=None),),
        DAY,
        ReflectionPolicy(min_trade_group_samples=3),
    )

    assert _findings(reflection, FindingCategory.DIRECTION_OUTCOME) == ()
    buy_guard = next(
        guard
        for guard in reflection.sample_guards
        if guard.category is FindingCategory.DIRECTION_OUTCOME
        and guard.scope_value == "BUY"
    )
    regime_guard = next(
        guard
        for guard in reflection.sample_guards
        if guard.category is FindingCategory.REGIME_OUTCOME
    )
    assert buy_guard.status is SampleGuardStatus.INSUFFICIENT
    assert buy_guard.observed_samples == 1
    assert regime_guard.status is SampleGuardStatus.UNAVAILABLE
    assert regime_guard.observed_samples == 0


def test_daily_aggregation_detects_confidence_excursion_and_rejection_patterns() -> None:
    trades = tuple(
        _trade(index, r_outcome=1.0 if index == 1 else -1.0, confidence=0.9)
        for index in range(1, 6)
    )
    rejections = tuple(_rejection(index + 6) for index in range(5))
    reflection = build_daily_reflection(
        (*trades, *rejections),
        DAY,
        ReflectionPolicy(
            min_trade_group_samples=3,
            min_confidence_samples=5,
            min_rejection_samples=5,
        ),
    )

    confidence = _findings(reflection, FindingCategory.CONFIDENCE_CALIBRATION)
    excursion = _findings(reflection, FindingCategory.EXCURSION_IMBALANCE)
    rejection = _findings(reflection, FindingCategory.REJECTION_ANOMALY)
    assert confidence[0].signal is FindingSignal.WARNING
    assert {metric.name: metric.value for metric in confidence[0].metrics} == {
        "absolute_gap": 0.7,
        "average_master_confidence": 0.9,
        "win_rate": 0.2,
    }
    assert excursion[0].reason_code == "ADVERSE_EXCURSION_DOMINATES"
    assert rejection[0].scope_value == "DISCIPLINE:DAILY_TRADE_CAP"


def test_agent_position_and_runtime_anomaly_findings_use_exact_daily_sources() -> None:
    trades = tuple(_trade(index, r_outcome=-1.0) for index in range(1, 4))
    agents = tuple(_agent(index) for index in range(1, 4))
    management = tuple(_management(index) for index in range(1, 4))
    anomaly = RuntimeAnomalyExperience(
        occurred_at=START + timedelta(hours=8),
        available_at=START + timedelta(hours=8),
        symbol="XAUUSD",
        outcome="AGENT_ERROR",
        provenance=_provenance(999),
        anomaly_type="AGENT_ERROR",
        severity="ERROR",
        source_semantic_id="ae-error",
        reason_codes=("AGENT_ERROR",),
    )
    reflection = build_daily_reflection(
        (*trades, *agents, *management, anomaly),
        DAY,
        ReflectionPolicy(),
    )

    agent = _findings(reflection, FindingCategory.AGENT_RELIABILITY)
    position = _findings(reflection, FindingCategory.POSITION_MANAGEMENT_ANOMALY)
    runtime = _findings(reflection, FindingCategory.RUNTIME_ANOMALY)
    assert agent[0].scope_value == "chart"
    assert agent[0].signal is FindingSignal.NEGATIVE
    assert agent[0].sample_size == 3
    assert position[0].reason_code == "NO_PROTECTION_ACTIONS"
    assert runtime[0].reason_code == "RUNTIME_ANOMALIES_OBSERVED"
