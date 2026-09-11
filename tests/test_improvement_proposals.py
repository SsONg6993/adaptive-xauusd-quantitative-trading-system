from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.experience import DecisionExperience, ExperienceProvenance
from axq.reflection import (
    DailyReflection,
    FindingCategory,
    FindingSignal,
    KnowledgeStatus,
    MetricFact,
    ReflectionFinding,
    ReflectionPolicy,
    WeeklyReflectionPolicy,
)
from axq.reflection.proposal_contracts import (
    ImprovementProposalPolicy,
    ProposalStatus,
    ProposalTargetComponent,
)
from axq.reflection.proposals import build_improvement_proposals
from axq.reflection.weekly import build_weekly_reflection
from axq.schemas import Signal

START = datetime(2026, 8, 10, tzinfo=UTC)
DAILY_POLICY = ReflectionPolicy()
WEEKLY_POLICY = WeeklyReflectionPolicy(
    daily_policy_id=DAILY_POLICY.policy_id,
    min_pattern_days=2,
    min_pattern_experiences=3,
)


def _sources() -> tuple[tuple[DailyReflection, ...], tuple[DecisionExperience, ...]]:
    experiences: list[DecisionExperience] = []
    daily: list[DailyReflection] = []
    for day in range(14):
        day_start = START + timedelta(days=day)
        day_experiences = tuple(
            DecisionExperience(
                occurred_at=day_start + timedelta(hours=12, minutes=index),
                available_at=day_start + timedelta(hours=12, minutes=index),
                symbol="XAUUSD",
                outcome="HOLD",
                provenance=ExperienceProvenance(runtime_event_ids=(f"event-{day}-{index}",)),
                master_proposal_id=f"master-{day}-{index}",
                evidence_bundle_id=f"bundle-{day}-{index}",
                decision=Signal.HOLD,
                actionable=False,
                master_confidence=0.0,
                disagreement=0.0,
                contradiction=0.0,
            )
            for index in range(3)
        )
        experiences.extend(day_experiences)
        experience_ids = tuple(item.experience_id for item in day_experiences)
        daily.append(
            DailyReflection(
                period_start=day_start,
                period_end=day_start + timedelta(days=1),
                available_at=day_start + timedelta(days=1),
                policy_id=DAILY_POLICY.policy_id,
                input_experience_ids=experience_ids,
                findings=(
                    ReflectionFinding(
                        category=FindingCategory.DIRECTION_OUTCOME,
                        signal=FindingSignal.NEGATIVE,
                        reason_code="NEGATIVE_AVERAGE_R",
                        scope="direction",
                        scope_value="BUY",
                        sample_size=3,
                        metrics=(MetricFact(name="average_r", value=-0.5, unit="R"),),
                        supporting_experience_ids=experience_ids,
                    ),
                    ReflectionFinding(
                        category=FindingCategory.AGENT_RELIABILITY,
                        signal=FindingSignal.WARNING,
                        reason_code="WEAK_DIRECTIONAL_SUPPORT_OUTCOME",
                        scope="specialist",
                        scope_value="quant",
                        sample_size=3,
                        metrics=(MetricFact(name="win_rate", value=0.25, unit="ratio"),),
                        supporting_experience_ids=experience_ids,
                    ),
                ),
            )
        )
    return tuple(daily), tuple(experiences)


def _weeks(
    daily: tuple[DailyReflection, ...], experiences: tuple[DecisionExperience, ...]
) -> tuple[object, object]:
    first = build_weekly_reflection(daily, experiences, START.date(), WEEKLY_POLICY)
    second = build_weekly_reflection(
        daily,
        experiences,
        (START + timedelta(days=7)).date(),
        WEEKLY_POLICY,
    )
    return first, second


def test_recurring_guarded_patterns_build_one_deterministic_proposal_per_key() -> None:
    daily, experiences = _sources()
    first, second = _weeks(daily, experiences)
    policy = ImprovementProposalPolicy()

    result = build_improvement_proposals(
        (second, first), reversed(daily), reversed(experiences), policy
    )
    repeated = build_improvement_proposals(
        (first, second), daily, experiences, policy
    )

    assert result == repeated
    assert len(result.proposals) == 2
    assert result.eligible_pattern_keys == 2
    assert result.insufficient_pattern_keys == 0
    assert {item.target_component for item in result.proposals} == {
        ProposalTargetComponent.MASTER_FUSION,
        ProposalTargetComponent.SPECIALIST_AGENT,
    }
    assert all(item.status is ProposalStatus.OBSERVATION for item in result.proposals)
    assert all(len(item.supporting_pattern_ids) == 2 for item in result.proposals)
    assert all(len(item.supporting_weekly_reflection_ids) == 2 for item in result.proposals)
    assert all(len(item.evidence_guards) == 3 for item in result.proposals)


def test_single_week_pattern_is_reported_insufficient_without_proposal() -> None:
    daily, experiences = _sources()
    first, _ = _weeks(daily, experiences)

    result = build_improvement_proposals((first,), daily, experiences, ImprovementProposalPolicy())

    assert result.proposals == ()
    assert result.assessed_pattern_keys == 2
    assert result.insufficient_pattern_keys == 2
    assert {item.reason_codes for item in result.assessments} == {
        ("INSUFFICIENT_PATTERN_RECURRENCE",)
    }


def test_missing_exact_experience_fails_closed() -> None:
    daily, experiences = _sources()
    first, second = _weeks(daily, experiences)

    with pytest.raises(ValueError, match="supporting Experience identity is unavailable"):
        build_improvement_proposals(
            (first, second), daily, experiences[:-1], ImprovementProposalPolicy()
        )


def test_rejected_pattern_status_excludes_only_that_pattern_key() -> None:
    daily, experiences = _sources()
    first, second = _weeks(daily, experiences)
    rejected_key = first.failure_patterns[0].pattern_key
    statuses = {
        pattern.pattern_id: (
            KnowledgeStatus.REJECTED
            if pattern.pattern_key == rejected_key
            else KnowledgeStatus.OBSERVATION
        )
        for reflection in (first, second)
        for pattern in (*reflection.success_patterns, *reflection.failure_patterns)
    }

    result = build_improvement_proposals(
        (first, second), daily, experiences, ImprovementProposalPolicy(), statuses
    )

    assert len(result.proposals) == 1
    rejected = next(item for item in result.assessments if item.pattern_key == rejected_key)
    assert rejected.reason_codes == ("INACTIVE_PATTERN_STATUS",)
