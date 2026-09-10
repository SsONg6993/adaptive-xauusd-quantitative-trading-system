"""Pure causal UTC-day aggregation for deterministic reflection."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, date, datetime, timedelta

from axq.agents import DirectionalBias
from axq.experience import (
    AgentContributionExperience,
    Experience,
    PositionManagementExperience,
    RejectedDecisionExperience,
    RuntimeAnomalyExperience,
    TradeExperience,
)
from axq.reflection.contracts import (
    DailyReflection,
    FindingCategory,
    FindingSignal,
    MetricFact,
    ReflectionFinding,
    ReflectionPolicy,
    SampleGuardRecord,
    SampleGuardStatus,
)
from axq.schemas import Signal


def _average(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _metric(name: str, value: float | None, unit: str) -> MetricFact:
    return MetricFact(name=name, value=value, unit=unit)


def _guard(
    category: FindingCategory,
    scope: str,
    scope_value: str,
    sources: Sequence[Experience],
    required: int,
    *,
    unavailable: bool = False,
) -> SampleGuardRecord:
    count = len(sources)
    status = (
        SampleGuardStatus.UNAVAILABLE
        if unavailable
        else SampleGuardStatus.PASSED
        if count >= required
        else SampleGuardStatus.INSUFFICIENT
    )
    return SampleGuardRecord(
        category=category,
        scope=scope,
        scope_value=scope_value,
        observed_samples=count,
        required_samples=required,
        status=status,
        supporting_experience_ids=tuple(item.experience_id for item in sources),
    )


def _outcome_finding(
    category: FindingCategory,
    scope: str,
    scope_value: str,
    trades: Sequence[TradeExperience],
    policy: ReflectionPolicy,
) -> ReflectionFinding:
    average_r = _average([float(item.r_outcome) for item in trades if item.r_outcome is not None])
    if average_r < policy.negative_average_r_threshold:
        signal = FindingSignal.NEGATIVE
        reason = "NEGATIVE_AVERAGE_R"
    elif average_r > policy.positive_average_r_threshold:
        signal = FindingSignal.POSITIVE
        reason = "POSITIVE_AVERAGE_R"
    else:
        signal = FindingSignal.NEUTRAL
        reason = "NEUTRAL_AVERAGE_R"
    return ReflectionFinding(
        category=category,
        signal=signal,
        reason_code=reason,
        scope=scope,
        scope_value=scope_value,
        sample_size=len(trades),
        metrics=(
            _metric("average_r", average_r, "R"),
            _metric("realized_pnl", sum(float(item.realized_pnl) for item in trades), "pnl"),
            _metric(
                "win_rate",
                sum(item.realized_pnl > 0 for item in trades) / len(trades),
                "ratio",
            ),
        ),
        supporting_experience_ids=tuple(item.experience_id for item in trades),
    )


def _grouped_trade_outcomes(
    trades: Sequence[TradeExperience],
    policy: ReflectionPolicy,
) -> tuple[list[ReflectionFinding], list[SampleGuardRecord]]:
    findings: list[ReflectionFinding] = []
    guards: list[SampleGuardRecord] = []
    definitions: tuple[
        tuple[
            FindingCategory,
            str,
            tuple[str, ...],
            Callable[[TradeExperience], str | None],
        ],
        ...,
    ] = (
        (
            FindingCategory.DIRECTION_OUTCOME,
            "direction",
            (Signal.BUY.value, Signal.SELL.value),
            lambda item: item.direction.value,
        ),
        (
            FindingCategory.SESSION_OUTCOME,
            "session",
            tuple(sorted({item.session for item in trades if item.session is not None})),
            lambda item: item.session,
        ),
        (
            FindingCategory.REGIME_OUTCOME,
            "regime",
            tuple(sorted({item.regime for item in trades if item.regime is not None})),
            lambda item: item.regime,
        ),
    )
    for category, scope, values, selector in definitions:
        if not values:
            guards.append(
                _guard(
                    category,
                    scope,
                    "UNAVAILABLE",
                    (),
                    policy.min_trade_group_samples,
                    unavailable=True,
                )
            )
            continue
        for value in values:
            group = tuple(
                item
                for item in trades
                if selector(item) == value and item.r_outcome is not None
            )
            guard = _guard(
                category,
                scope,
                str(value),
                group,
                policy.min_trade_group_samples,
            )
            guards.append(guard)
            if guard.status is SampleGuardStatus.PASSED:
                findings.append(
                    _outcome_finding(category, scope, str(value), group, policy)
                )
    return findings, guards


def _confidence_and_excursion(
    trades: Sequence[TradeExperience],
    policy: ReflectionPolicy,
) -> tuple[list[ReflectionFinding], list[SampleGuardRecord]]:
    findings: list[ReflectionFinding] = []
    guards: list[SampleGuardRecord] = []
    confidence_trades = tuple(item for item in trades if item.master_confidence is not None)
    confidence_guard = _guard(
        FindingCategory.CONFIDENCE_CALIBRATION,
        "day",
        "ALL",
        confidence_trades,
        policy.min_confidence_samples,
    )
    guards.append(confidence_guard)
    if confidence_guard.status is SampleGuardStatus.PASSED:
        mean_confidence = _average(
            [
                item.master_confidence
                for item in confidence_trades
                if item.master_confidence is not None
            ]
        )
        win_rate = sum(item.realized_pnl > 0 for item in confidence_trades) / len(
            confidence_trades
        )
        gap = abs(mean_confidence - win_rate)
        if gap >= policy.confidence_gap_threshold:
            findings.append(
                ReflectionFinding(
                    category=FindingCategory.CONFIDENCE_CALIBRATION,
                    signal=FindingSignal.WARNING,
                    reason_code="CONFIDENCE_OUTCOME_GAP",
                    scope="day",
                    scope_value="ALL",
                    sample_size=len(confidence_trades),
                    metrics=(
                        _metric("absolute_gap", gap, "ratio"),
                        _metric("average_master_confidence", mean_confidence, "ratio"),
                        _metric("win_rate", win_rate, "ratio"),
                    ),
                    supporting_experience_ids=tuple(
                        item.experience_id for item in confidence_trades
                    ),
                )
            )

    excursion_trades = tuple(
        item for item in trades if item.mfe_points is not None and item.mae_points is not None
    )
    excursion_guard = _guard(
        FindingCategory.EXCURSION_IMBALANCE,
        "day",
        "ALL",
        excursion_trades,
        policy.min_trade_group_samples,
    )
    guards.append(excursion_guard)
    if excursion_guard.status is SampleGuardStatus.PASSED:
        average_mfe = _average(
            [item.mfe_points for item in excursion_trades if item.mfe_points is not None]
        )
        average_mae = _average(
            [item.mae_points for item in excursion_trades if item.mae_points is not None]
        )
        ratio = average_mae / average_mfe if average_mfe > 0 else None
        dominates = (ratio is not None and ratio >= policy.adverse_favorable_ratio_threshold) or (
            ratio is None and average_mae > 0
        )
        if dominates:
            findings.append(
                ReflectionFinding(
                    category=FindingCategory.EXCURSION_IMBALANCE,
                    signal=FindingSignal.WARNING,
                    reason_code="ADVERSE_EXCURSION_DOMINATES",
                    scope="day",
                    scope_value="ALL",
                    sample_size=len(excursion_trades),
                    metrics=(
                        _metric("adverse_favorable_ratio", ratio, "ratio"),
                        _metric("average_mae_points", average_mae, "points"),
                        _metric("average_mfe_points", average_mfe, "points"),
                    ),
                    supporting_experience_ids=tuple(
                        item.experience_id for item in excursion_trades
                    ),
                )
            )
    return findings, guards


def _rejection_findings(
    rejections: Sequence[RejectedDecisionExperience],
    policy: ReflectionPolicy,
) -> tuple[list[ReflectionFinding], list[SampleGuardRecord]]:
    if not rejections:
        return [], [
            _guard(
                FindingCategory.REJECTION_ANOMALY,
                "rejection_reason",
                "UNAVAILABLE",
                (),
                policy.min_rejection_samples,
                unavailable=True,
            )
        ]
    grouped: dict[str, list[RejectedDecisionExperience]] = defaultdict(list)
    for item in rejections:
        for reason in item.reason_codes:
            grouped[f"{item.rejection_layer.value}:{reason}"].append(item)
    findings: list[ReflectionFinding] = []
    guards: list[SampleGuardRecord] = []
    for value in sorted(grouped):
        group = tuple(grouped[value])
        guard = _guard(
            FindingCategory.REJECTION_ANOMALY,
            "rejection_reason",
            value,
            group,
            policy.min_rejection_samples,
        )
        guards.append(guard)
        share = len(group) / len(rejections)
        if guard.status is SampleGuardStatus.PASSED and share >= policy.rejection_share_threshold:
            findings.append(
                ReflectionFinding(
                    category=FindingCategory.REJECTION_ANOMALY,
                    signal=FindingSignal.WARNING,
                    reason_code="CONCENTRATED_REJECTION_REASON",
                    scope="rejection_reason",
                    scope_value=value,
                    sample_size=len(group),
                    metrics=(
                        _metric("count", float(len(group)), "count"),
                        _metric("rejection_share", share, "ratio"),
                    ),
                    supporting_experience_ids=tuple(
                        item.experience_id for item in group
                    ),
                )
            )
    return findings, guards


def _agent_findings(
    trades: Sequence[TradeExperience],
    contributions: Sequence[AgentContributionExperience],
    policy: ReflectionPolicy,
) -> tuple[list[ReflectionFinding], list[SampleGuardRecord]]:
    trade_by_evidence = {
        evidence_id: trade
        for trade in trades
        for evidence_id in trade.specialist_evidence_ids
    }
    grouped: dict[str, list[tuple[AgentContributionExperience, TradeExperience]]] = (
        defaultdict(list)
    )
    for contribution in contributions:
        trade = trade_by_evidence.get(contribution.agent_evidence_id)
        expected = (
            DirectionalBias.BULLISH
            if trade is not None and trade.direction is Signal.BUY
            else DirectionalBias.BEARISH
        )
        if trade is not None and contribution.direction is expected:
            grouped[contribution.specialist].append((contribution, trade))
    if not grouped:
        return [], [
            _guard(
                FindingCategory.AGENT_RELIABILITY,
                "specialist",
                "UNAVAILABLE",
                (),
                policy.min_agent_samples,
                unavailable=True,
            )
        ]
    findings: list[ReflectionFinding] = []
    guards: list[SampleGuardRecord] = []
    for specialist in sorted(grouped):
        pairs = grouped[specialist]
        sources: tuple[Experience, ...] = tuple(pair[0] for pair in pairs)
        guard = _guard(
            FindingCategory.AGENT_RELIABILITY,
            "specialist",
            specialist,
            sources,
            policy.min_agent_samples,
        )
        guards.append(guard)
        if guard.status is not SampleGuardStatus.PASSED:
            continue
        win_rate = sum(pair[1].realized_pnl > 0 for pair in pairs) / len(pairs)
        if win_rate <= policy.weak_agent_win_rate_threshold:
            signal = FindingSignal.NEGATIVE
            reason = "WEAK_DIRECTIONAL_SUPPORT_OUTCOME"
        elif win_rate >= 1.0 - policy.weak_agent_win_rate_threshold:
            signal = FindingSignal.POSITIVE
            reason = "STRONG_DIRECTIONAL_SUPPORT_OUTCOME"
        else:
            signal = FindingSignal.NEUTRAL
            reason = "MIXED_DIRECTIONAL_SUPPORT_OUTCOME"
        findings.append(
            ReflectionFinding(
                category=FindingCategory.AGENT_RELIABILITY,
                signal=signal,
                reason_code=reason,
                scope="specialist",
                scope_value=specialist,
                sample_size=len(pairs),
                metrics=(
                    _metric(
                        "average_confidence",
                        _average(
                            [
                                float(pair[0].confidence)
                                for pair in pairs
                                if pair[0].confidence is not None
                            ]
                        )
                        if any(pair[0].confidence is not None for pair in pairs)
                        else None,
                        "ratio",
                    ),
                    _metric("supported_trade_win_rate", win_rate, "ratio"),
                ),
                supporting_experience_ids=tuple(
                    pair[0].experience_id for pair in pairs
                ),
            )
        )
    return findings, guards


def _management_and_runtime_findings(
    management: Sequence[PositionManagementExperience],
    anomalies: Sequence[RuntimeAnomalyExperience],
    policy: ReflectionPolicy,
) -> tuple[list[ReflectionFinding], list[SampleGuardRecord]]:
    findings: list[ReflectionFinding] = []
    guards: list[SampleGuardRecord] = []
    management_guard = _guard(
        FindingCategory.POSITION_MANAGEMENT_ANOMALY,
        "day",
        "ALL",
        management,
        policy.min_position_management_samples,
    )
    guards.append(management_guard)
    if management_guard.status is SampleGuardStatus.PASSED:
        protected = sum(item.management_result == "PROTECT_POSITION" for item in management)
        rate = protected / len(management)
        if rate <= policy.zero_protection_rate_threshold:
            findings.append(
                ReflectionFinding(
                    category=FindingCategory.POSITION_MANAGEMENT_ANOMALY,
                    signal=FindingSignal.WARNING,
                    reason_code="NO_PROTECTION_ACTIONS",
                    scope="day",
                    scope_value="ALL",
                    sample_size=len(management),
                    metrics=(
                        _metric("protection_count", float(protected), "count"),
                        _metric("protection_rate", rate, "ratio"),
                    ),
                    supporting_experience_ids=tuple(
                        item.experience_id for item in management
                    ),
                )
            )
    anomaly_guard = _guard(
        FindingCategory.RUNTIME_ANOMALY,
        "day",
        "ALL",
        anomalies,
        policy.min_runtime_anomaly_samples,
    )
    guards.append(anomaly_guard)
    if anomaly_guard.status is SampleGuardStatus.PASSED:
        findings.append(
            ReflectionFinding(
                category=FindingCategory.RUNTIME_ANOMALY,
                signal=FindingSignal.WARNING,
                reason_code="RUNTIME_ANOMALIES_OBSERVED",
                scope="day",
                scope_value="ALL",
                sample_size=len(anomalies),
                metrics=(_metric("count", float(len(anomalies)), "count"),),
                supporting_experience_ids=tuple(
                    item.experience_id for item in anomalies
                ),
            )
        )
    return findings, guards


def build_daily_reflection(
    experiences: Iterable[Experience],
    day: date,
    policy: ReflectionPolicy,
    *,
    supersedes_reflection_id: str | None = None,
) -> DailyReflection:
    """Build one immutable reflection from facts available during one UTC day."""

    start = datetime(day.year, day.month, day.day, tzinfo=UTC)
    end = start + timedelta(days=1)
    records = tuple(
        sorted(
            (
                item
                for item in experiences
                if start <= item.available_at < end
            ),
            key=lambda item: item.experience_id,
        )
    )
    trades = tuple(item for item in records if isinstance(item, TradeExperience))
    rejections = tuple(
        item for item in records if isinstance(item, RejectedDecisionExperience)
    )
    contributions = tuple(
        item for item in records if isinstance(item, AgentContributionExperience)
    )
    management = tuple(
        item for item in records if isinstance(item, PositionManagementExperience)
    )
    anomalies = tuple(
        item for item in records if isinstance(item, RuntimeAnomalyExperience)
    )
    findings: list[ReflectionFinding] = []
    guards: list[SampleGuardRecord] = []
    for produced_findings, produced_guards in (
        _grouped_trade_outcomes(trades, policy),
        _confidence_and_excursion(trades, policy),
        _rejection_findings(rejections, policy),
        _agent_findings(trades, contributions, policy),
        _management_and_runtime_findings(management, anomalies, policy),
    ):
        findings.extend(produced_findings)
        guards.extend(produced_guards)
    return DailyReflection(
        period_start=start,
        period_end=end,
        available_at=end,
        policy_id=policy.policy_id,
        input_experience_ids=tuple(item.experience_id for item in records),
        findings=tuple(findings),
        sample_guards=tuple(guards),
        supersedes_reflection_id=supersedes_reflection_id,
    )
