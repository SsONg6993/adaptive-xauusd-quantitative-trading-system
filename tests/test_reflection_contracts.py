from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.reflection import (
    DailyReflection,
    FindingCategory,
    FindingSignal,
    MetricFact,
    ReflectionFinding,
    ReflectionPolicy,
    SampleGuardRecord,
    SampleGuardStatus,
)

START = datetime(2026, 8, 10, tzinfo=UTC)
END = START + timedelta(days=1)


def _guard() -> SampleGuardRecord:
    return SampleGuardRecord(
        category=FindingCategory.DIRECTION_OUTCOME,
        scope="direction",
        scope_value="BUY",
        observed_samples=3,
        required_samples=3,
        status=SampleGuardStatus.PASSED,
        supporting_experience_ids=("exp-2", "exp-1", "exp-1"),
    )


def _finding() -> ReflectionFinding:
    return ReflectionFinding(
        category=FindingCategory.DIRECTION_OUTCOME,
        signal=FindingSignal.NEGATIVE,
        reason_code="NEGATIVE_AVERAGE_R",
        scope="direction",
        scope_value="BUY",
        sample_size=3,
        metrics=(
            MetricFact(name="average_r", value=-0.2, unit="R"),
            MetricFact(name="win_rate", value=0.3, unit="ratio"),
        ),
        supporting_experience_ids=("exp-2", "exp-1"),
    )


def test_policy_and_nested_contracts_have_stable_content_identities() -> None:
    first = ReflectionPolicy()
    second = ReflectionPolicy.model_validate_json(first.model_dump_json())
    guard = _guard()
    finding = _finding()

    assert first.policy_id == second.policy_id
    assert first.policy_id.startswith("reflection-policy-")
    assert guard.guard_id.startswith("sample-guard-")
    assert finding.finding_id.startswith("reflection-finding-")
    assert guard.supporting_experience_ids == ("exp-1", "exp-2")
    assert finding.supporting_experience_ids == ("exp-1", "exp-2")


def test_daily_reflection_normalizes_children_and_binds_supersession() -> None:
    policy = ReflectionPolicy()
    first = DailyReflection(
        period_start=START,
        period_end=END,
        available_at=END,
        policy_id=policy.policy_id,
        input_experience_ids=("exp-2", "exp-1", "exp-1"),
        findings=(_finding(),),
        sample_guards=(_guard(),),
    )
    restored = DailyReflection.model_validate_json(first.model_dump_json())
    revised = DailyReflection(
        period_start=START,
        period_end=END,
        available_at=END,
        policy_id=policy.policy_id,
        input_experience_ids=("exp-1", "exp-2", "exp-3"),
        findings=(_finding(),),
        sample_guards=(_guard(),),
        supersedes_reflection_id=first.reflection_id,
    )

    assert first == restored
    assert first.input_experience_ids == ("exp-1", "exp-2")
    assert first.reflection_id.startswith("daily-reflection-")
    assert revised.reflection_id != first.reflection_id
    assert revised.supersedes_reflection_id == first.reflection_id


def test_contracts_reject_naive_or_non_daily_periods_and_are_frozen() -> None:
    policy = ReflectionPolicy()
    body = {
        "period_start": datetime(2026, 8, 10),
        "period_end": datetime(2026, 8, 11),
        "available_at": datetime(2026, 8, 11),
        "policy_id": policy.policy_id,
        "input_experience_ids": ("exp-1",),
    }
    with pytest.raises(ValidationError, match="timezone-aware"):
        DailyReflection(**body)
    with pytest.raises(ValidationError, match="one UTC calendar day"):
        DailyReflection(
            period_start=START,
            period_end=END + timedelta(hours=1),
            available_at=END + timedelta(hours=1),
            policy_id=policy.policy_id,
            input_experience_ids=("exp-1",),
        )
    with pytest.raises(ValidationError):
        ReflectionPolicy(min_trade_group_samples=0)
    with pytest.raises(ValidationError):
        policy.min_trade_group_samples = 99  # type: ignore[misc]


def test_metric_fact_preserves_unavailable_separately_from_numeric_zero() -> None:
    unavailable = MetricFact(name="average_r", value=None, unit="R")
    zero = MetricFact(name="average_r", value=0.0, unit="R")

    assert unavailable.value is None
    assert zero.value == 0.0
    assert unavailable != zero
