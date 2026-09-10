"""Pure deterministic ISO-week reflection aggregation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime, timedelta

from axq.experience import Experience
from axq.reflection.contracts import DailyReflection, ReflectionFinding, SampleGuardStatus
from axq.reflection.weekly_contracts import (
    FailurePattern,
    PatternMetricSummary,
    PatternSignalClass,
    SuccessPattern,
    WeeklyGuardKind,
    WeeklyReflection,
    WeeklyReflectionPolicy,
    WeeklySampleGuard,
)


def _expected_dates(week_start: datetime) -> tuple[date, ...]:
    return tuple(week_start.date() + timedelta(days=index) for index in range(7))


def _terminal_daily(records: Sequence[DailyReflection]) -> DailyReflection:
    by_id = {record.reflection_id: record for record in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate DailyReflection identity")
    children: dict[str, str] = {}
    roots: list[str] = []
    for record in records:
        predecessor = record.supersedes_reflection_id
        if predecessor is None:
            roots.append(record.reflection_id)
            continue
        if predecessor not in by_id:
            raise ValueError("missing daily predecessor")
        if predecessor in children:
            raise ValueError("branched daily revision")
        children[predecessor] = record.reflection_id
    if len(roots) != 1:
        raise ValueError("daily revision chain must have exactly one root")
    visited: set[str] = set()
    current = roots[0]
    while current in children:
        if current in visited:
            raise ValueError("cyclic daily revision chain")
        visited.add(current)
        current = children[current]
    visited.add(current)
    if visited != set(by_id):
        raise ValueError("disconnected daily revision chain")
    return by_id[current]


def _select_daily(
    reflections: Iterable[DailyReflection],
    week_start: datetime,
    policy: WeeklyReflectionPolicy,
) -> tuple[DailyReflection, ...]:
    expected = set(_expected_dates(week_start))
    grouped: dict[date, list[DailyReflection]] = defaultdict(list)
    for reflection in reflections:
        if reflection.policy_id != policy.daily_policy_id:
            continue
        if reflection.period_start.date() in expected:
            grouped[reflection.period_start.date()].append(reflection)
    return tuple(_terminal_daily(grouped[day]) for day in sorted(grouped))


def _experience_index(experiences: Iterable[Experience]) -> dict[str, Experience]:
    result: dict[str, Experience] = {}
    for experience in experiences:
        if experience.experience_id in result:
            raise ValueError("duplicate Experience identity")
        result[experience.experience_id] = experience
    return result


def _validate_provenance(
    daily: Sequence[DailyReflection],
    experiences: dict[str, Experience],
) -> tuple[str, ...]:
    source_ids: set[str] = set()
    for reflection in daily:
        daily_ids = set(reflection.input_experience_ids)
        for finding in reflection.findings:
            if not set(finding.supporting_experience_ids) <= daily_ids:
                raise ValueError("finding source is not a daily input")
        for experience_id in daily_ids:
            experience = experiences.get(experience_id)
            if experience is None:
                raise ValueError("daily input Experience identity is unavailable")
            if not reflection.period_start <= experience.available_at < reflection.period_end:
                raise ValueError("Experience available_at is outside its DailyReflection period")
            source_ids.add(experience_id)
    return tuple(sorted(source_ids))


def _guard(
    kind: WeeklyGuardKind,
    scope: str,
    scope_value: str,
    observed: int,
    required: int,
    present: tuple[date, ...],
    missing: tuple[date, ...],
    daily_ids: tuple[str, ...],
    finding_ids: tuple[str, ...] = (),
    experience_ids: tuple[str, ...] = (),
    *,
    unavailable: bool = False,
) -> WeeklySampleGuard:
    status = (
        SampleGuardStatus.UNAVAILABLE
        if unavailable
        else SampleGuardStatus.PASSED
        if observed >= required
        else SampleGuardStatus.INSUFFICIENT
    )
    return WeeklySampleGuard(
        guard_kind=kind,
        scope=scope,
        scope_value=scope_value,
        observed_samples=observed,
        required_samples=required,
        status=status,
        present_daily_periods=present,
        missing_daily_periods=missing,
        supporting_daily_reflection_ids=daily_ids,
        supporting_finding_ids=finding_ids,
        supporting_experience_ids=experience_ids,
    )


def _metric_summaries(findings: Sequence[ReflectionFinding]) -> tuple[PatternMetricSummary, ...]:
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for finding in findings:
        for metric in finding.metrics:
            if metric.value is not None:
                values[(metric.name, metric.unit)].append(metric.value)
    return tuple(
        PatternMetricSummary(
            name=name,
            unit=unit,
            count=len(items),
            minimum=min(items),
            maximum=max(items),
            mean=sum(items) / len(items),
        )
        for (name, unit), items in sorted(values.items())
    )


def _patterns(
    daily: Sequence[DailyReflection],
    policy: WeeklyReflectionPolicy,
    week_start: datetime,
    week_end: datetime,
    present: tuple[date, ...],
) -> tuple[list[SuccessPattern], list[FailurePattern], list[WeeklySampleGuard]]:
    grouped: dict[
        tuple[str, ...], list[tuple[DailyReflection, ReflectionFinding]]
    ] = defaultdict(list)
    for reflection in daily:
        for finding in reflection.findings:
            if finding.signal in policy.success_signals:
                pattern_type = "SUCCESS"
                signal_class = PatternSignalClass.POSITIVE
            elif finding.signal in policy.failure_signals:
                pattern_type = "FAILURE"
                signal_class = PatternSignalClass.ADVERSE
            else:
                continue
            group_key = (
                pattern_type,
                finding.category.value,
                signal_class.value,
                finding.reason_code,
                finding.scope,
                finding.scope_value,
            )
            grouped[group_key].append((reflection, finding))
    success: list[SuccessPattern] = []
    failure: list[FailurePattern] = []
    guards: list[WeeklySampleGuard] = []
    for signature in sorted(grouped):
        pairs = grouped[signature]
        daily_ids = tuple(pair[0].reflection_id for pair in pairs)
        finding_ids = tuple(pair[1].finding_id for pair in pairs)
        experience_ids = tuple(
            sorted(
                {
                    experience_id
                    for _, finding in pairs
                    for experience_id in finding.supporting_experience_ids
                }
            )
        )
        sample_days = tuple(sorted({pair[0].period_start.date() for pair in pairs}))
        scope_value = "|".join(signature)
        day_guard = _guard(
            WeeklyGuardKind.PATTERN_DAY_SUPPORT,
            "pattern_signature",
            scope_value,
            len(sample_days),
            policy.min_pattern_days,
            present,
            (),
            daily_ids,
            finding_ids,
            experience_ids,
        )
        experience_guard = _guard(
            WeeklyGuardKind.PATTERN_EXPERIENCE_SUPPORT,
            "pattern_signature",
            scope_value,
            len(experience_ids),
            policy.min_pattern_experiences,
            present,
            (),
            daily_ids,
            finding_ids,
            experience_ids,
        )
        guards.extend((day_guard, experience_guard))
        if (
            day_guard.status is not SampleGuardStatus.PASSED
            or experience_guard.status is not SampleGuardStatus.PASSED
        ):
            continue
        metrics = _metric_summaries(tuple(pair[1] for pair in pairs))
        if signature[0] == "SUCCESS":
            success.append(
                SuccessPattern(
                    category=pairs[0][1].category,
                    signal_class=PatternSignalClass(signature[2]),
                    source_signal=pairs[0][1].signal,
                    reason_code=signature[3],
                    scope=signature[4],
                    scope_value=signature[5],
                    week_start=week_start,
                    week_end=week_end,
                    sample_days=sample_days,
                    sample_count=len(experience_ids),
                    metrics=metrics,
                    supporting_daily_reflection_ids=daily_ids,
                    supporting_finding_ids=finding_ids,
                    supporting_experience_ids=experience_ids,
                )
            )
        else:
            failure.append(
                FailurePattern(
                    category=pairs[0][1].category,
                    signal_class=PatternSignalClass(signature[2]),
                    source_signal=pairs[0][1].signal,
                    reason_code=signature[3],
                    scope=signature[4],
                    scope_value=signature[5],
                    week_start=week_start,
                    week_end=week_end,
                    sample_days=sample_days,
                    sample_count=len(experience_ids),
                    metrics=metrics,
                    supporting_daily_reflection_ids=daily_ids,
                    supporting_finding_ids=finding_ids,
                    supporting_experience_ids=experience_ids,
                )
            )
    return success, failure, guards


def build_weekly_reflection(
    daily_reflections: Iterable[DailyReflection],
    experiences: Iterable[Experience],
    week_start_date: date,
    policy: WeeklyReflectionPolicy,
    *,
    supersedes_weekly_reflection_id: str | None = None,
) -> WeeklyReflection:
    """Build one immutable weekly observation from exact causal source records."""

    if week_start_date.weekday() != 0:
        raise ValueError("week start must be Monday")
    week_start = datetime(
        week_start_date.year,
        week_start_date.month,
        week_start_date.day,
        tzinfo=UTC,
    )
    week_end = week_start + timedelta(days=7)
    daily = _select_daily(daily_reflections, week_start, policy)
    expected = _expected_dates(week_start)
    present = tuple(reflection.period_start.date() for reflection in daily)
    missing = tuple(day for day in expected if day not in set(present))
    daily_ids = tuple(reflection.reflection_id for reflection in daily)
    experience_ids = _validate_provenance(daily, _experience_index(experiences))
    completeness = _guard(
        WeeklyGuardKind.WEEK_COMPLETENESS,
        "week",
        f"{week_start_date.isocalendar().year}-W{week_start_date.isocalendar().week:02d}",
        len(present),
        7,
        present,
        missing,
        daily_ids,
    )
    provenance = _guard(
        WeeklyGuardKind.PROVENANCE_INTEGRITY,
        "week",
        "EXACT_SOURCE_LINKAGE",
        len(experience_ids),
        max(1, len(experience_ids)),
        present,
        missing,
        daily_ids,
        experience_ids=experience_ids,
        unavailable=not experience_ids,
    )
    success: list[SuccessPattern] = []
    failure: list[FailurePattern] = []
    pattern_guards: list[WeeklySampleGuard] = []
    if not missing:
        success, failure, pattern_guards = _patterns(
            daily, policy, week_start, week_end, present
        )
    available_at = max((reflection.available_at for reflection in daily), default=week_start)
    return WeeklyReflection(
        week_start=week_start,
        week_end=week_end,
        available_at=available_at,
        weekly_policy_id=policy.policy_id,
        daily_policy_id=policy.daily_policy_id,
        present_daily_periods=present,
        missing_daily_periods=missing,
        input_daily_reflection_ids=daily_ids,
        input_experience_ids=experience_ids,
        sample_guards=(completeness, provenance, *pattern_guards),
        success_patterns=tuple(success),
        failure_patterns=tuple(failure),
        supersedes_weekly_reflection_id=supersedes_weekly_reflection_id,
    )
