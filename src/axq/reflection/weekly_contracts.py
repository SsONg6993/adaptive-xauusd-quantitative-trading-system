"""Immutable contracts for deterministic weekly reflection and pattern lifecycle."""

from __future__ import annotations

from datetime import date, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from axq.reflection.contracts import (
    FindingCategory,
    FindingSignal,
    ReflectionModel,
    SampleGuardStatus,
)
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class PatternType(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class PatternSignalClass(StrEnum):
    POSITIVE = "POSITIVE"
    ADVERSE = "ADVERSE"


class KnowledgeStatus(StrEnum):
    OBSERVATION = "OBSERVATION"
    HYPOTHESIS = "HYPOTHESIS"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"


class TransitionActionKind(StrEnum):
    OPERATOR = "OPERATOR"
    EVALUATION = "EVALUATION"


class WeeklyGuardKind(StrEnum):
    WEEK_COMPLETENESS = "WEEK_COMPLETENESS"
    PATTERN_DAY_SUPPORT = "PATTERN_DAY_SUPPORT"
    PATTERN_EXPERIENCE_SUPPORT = "PATTERN_EXPERIENCE_SUPPORT"
    PROVENANCE_INTEGRITY = "PROVENANCE_INTEGRITY"


class WeeklyReflectionPolicy(ReflectionModel):
    policy_id: str = ""
    daily_policy_id: str = Field(min_length=1)
    required_daily_periods: Literal[7] = 7
    min_pattern_days: int = Field(default=2, ge=2, le=7)
    min_pattern_experiences: int = Field(default=3, ge=1)
    success_signals: tuple[FindingSignal, ...] = (FindingSignal.POSITIVE,)
    failure_signals: tuple[FindingSignal, ...] = (
        FindingSignal.NEGATIVE,
        FindingSignal.WARNING,
    )

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> WeeklyReflectionPolicy:
        success = tuple(sorted(set(self.success_signals), key=str))
        failure = tuple(sorted(set(self.failure_signals), key=str))
        if not success or not failure:
            raise ValueError("weekly pattern signal classes cannot be empty")
        if set(success) & set(failure):
            raise ValueError("success and failure signals must be disjoint")
        object.__setattr__(self, "success_signals", success)
        object.__setattr__(self, "failure_signals", failure)
        identity = self.model_dump(mode="json", exclude={"policy_id"})
        expected = f"weekly-reflection-policy-{canonical_hash(identity)[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match weekly policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class PatternMetricSummary(ReflectionModel):
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    count: int = Field(ge=1)
    minimum: FiniteFloat
    maximum: FiniteFloat
    mean: FiniteFloat

    @model_validator(mode="after")
    def validate_bounds(self) -> PatternMetricSummary:
        if self.minimum > self.maximum:
            raise ValueError("metric minimum cannot exceed maximum")
        if not self.minimum <= self.mean <= self.maximum:
            raise ValueError("metric mean must be within bounds")
        return self


class WeeklySampleGuard(ReflectionModel):
    guard_id: str = ""
    guard_kind: WeeklyGuardKind
    scope: str = Field(min_length=1)
    scope_value: str = Field(min_length=1)
    observed_samples: int = Field(ge=0)
    required_samples: int = Field(ge=1)
    status: SampleGuardStatus
    present_daily_periods: tuple[date, ...] = ()
    missing_daily_periods: tuple[date, ...] = ()
    supporting_daily_reflection_ids: tuple[str, ...] = ()
    supporting_finding_ids: tuple[str, ...] = ()
    supporting_experience_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> WeeklySampleGuard:
        for field_name in (
            "present_daily_periods",
            "missing_daily_periods",
            "supporting_daily_reflection_ids",
            "supporting_finding_ids",
            "supporting_experience_ids",
        ):
            object.__setattr__(self, field_name, tuple(sorted(set(getattr(self, field_name)))))
        if set(self.present_daily_periods) & set(self.missing_daily_periods):
            raise ValueError("present and missing daily periods must be disjoint")
        if (
            self.status is SampleGuardStatus.PASSED
            and self.observed_samples < self.required_samples
        ):
            raise ValueError("passed weekly guard does not meet required samples")
        if (
            self.status is SampleGuardStatus.INSUFFICIENT
            and self.observed_samples >= self.required_samples
        ):
            raise ValueError("insufficient weekly guard already meets required samples")
        if self.status is SampleGuardStatus.UNAVAILABLE and self.observed_samples != 0:
            raise ValueError("unavailable weekly guard must have zero observed samples")
        identity = self.model_dump(mode="json", exclude={"guard_id"})
        expected = f"weekly-sample-guard-{canonical_hash(identity)[:20]}"
        if self.guard_id and self.guard_id != expected:
            raise ValueError("guard_id does not match weekly guard content")
        object.__setattr__(self, "guard_id", expected)
        return self


class PatternBase(ReflectionModel):
    pattern_id: str = ""
    pattern_key: str = ""
    pattern_type: PatternType
    signal_class: PatternSignalClass
    category: FindingCategory
    source_signal: FindingSignal
    reason_code: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    scope_value: str = Field(min_length=1)
    week_start: UTCDateTime
    week_end: UTCDateTime
    sample_days: tuple[date, ...] = Field(min_length=1)
    sample_count: int = Field(ge=1)
    metrics: tuple[PatternMetricSummary, ...] = ()
    supporting_daily_reflection_ids: tuple[str, ...] = Field(min_length=1)
    supporting_finding_ids: tuple[str, ...] = Field(min_length=1)
    supporting_experience_ids: tuple[str, ...] = Field(min_length=1)
    knowledge_status: KnowledgeStatus = KnowledgeStatus.OBSERVATION

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> PatternBase:
        if self.knowledge_status is not KnowledgeStatus.OBSERVATION:
            raise ValueError("new weekly patterns must start as OBSERVATION")
        if self.week_end - self.week_start != timedelta(days=7):
            raise ValueError("pattern must span one ISO week")
        if self.pattern_type is PatternType.SUCCESS:
            if self.signal_class is not PatternSignalClass.POSITIVE:
                raise ValueError("success pattern requires POSITIVE signal class")
        elif self.signal_class is not PatternSignalClass.ADVERSE:
            raise ValueError("failure pattern requires ADVERSE signal class")
        for field_name in (
            "sample_days",
            "supporting_daily_reflection_ids",
            "supporting_finding_ids",
            "supporting_experience_ids",
        ):
            object.__setattr__(self, field_name, tuple(sorted(set(getattr(self, field_name)))))
        metrics = tuple(sorted(self.metrics, key=lambda item: (item.name, item.unit)))
        if len({(item.name, item.unit) for item in metrics}) != len(metrics):
            raise ValueError("pattern metrics must be unique by name and unit")
        object.__setattr__(self, "metrics", metrics)
        key_identity = {
            "pattern_type": self.pattern_type.value,
            "category": self.category.value,
            "signal_class": self.signal_class.value,
            "reason_code": self.reason_code,
            "scope": self.scope,
            "scope_value": self.scope_value,
        }
        expected_key = f"pattern-key-{canonical_hash(key_identity)[:20]}"
        if self.pattern_key and self.pattern_key != expected_key:
            raise ValueError("pattern_key does not match semantic pattern fields")
        object.__setattr__(self, "pattern_key", expected_key)
        identity = self.model_dump(mode="json", exclude={"pattern_id"})
        expected_id = f"weekly-pattern-{canonical_hash(identity)[:20]}"
        if self.pattern_id and self.pattern_id != expected_id:
            raise ValueError("pattern_id does not match pattern content")
        object.__setattr__(self, "pattern_id", expected_id)
        return self


class SuccessPattern(PatternBase):
    pattern_type: Literal[PatternType.SUCCESS] = PatternType.SUCCESS


class FailurePattern(PatternBase):
    pattern_type: Literal[PatternType.FAILURE] = PatternType.FAILURE


Pattern = SuccessPattern | FailurePattern


class WeeklyReflection(ReflectionModel):
    reflection_id: str = ""
    week_start: UTCDateTime
    week_end: UTCDateTime
    available_at: UTCDateTime
    weekly_policy_id: str = Field(min_length=1)
    daily_policy_id: str = Field(min_length=1)
    present_daily_periods: tuple[date, ...]
    missing_daily_periods: tuple[date, ...]
    input_daily_reflection_ids: tuple[str, ...]
    input_experience_ids: tuple[str, ...] = ()
    sample_guards: tuple[WeeklySampleGuard, ...] = ()
    success_patterns: tuple[SuccessPattern, ...] = ()
    failure_patterns: tuple[FailurePattern, ...] = ()
    supersedes_weekly_reflection_id: str | None = None

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> WeeklyReflection:
        if self.week_start.weekday() != 0 or any(
            (
                self.week_start.hour,
                self.week_start.minute,
                self.week_start.second,
                self.week_start.microsecond,
            )
        ):
            raise ValueError("week_start must be Monday 00:00 UTC")
        if self.week_end - self.week_start != timedelta(days=7):
            raise ValueError("weekly reflection must span seven days")
        expected_days = {self.week_start.date() + timedelta(days=index) for index in range(7)}
        present = tuple(sorted(set(self.present_daily_periods)))
        missing = tuple(sorted(set(self.missing_daily_periods)))
        if set(present) & set(missing) or set(present) | set(missing) != expected_days:
            raise ValueError("present and missing periods must partition the ISO week")
        if len(self.input_daily_reflection_ids) != len(present):
            raise ValueError("each present day requires one DailyReflection identity")
        daily_ids = tuple(sorted(set(self.input_daily_reflection_ids)))
        if len(daily_ids) != len(self.input_daily_reflection_ids):
            raise ValueError("weekly input DailyReflection identities must be unique")
        success = tuple(sorted(self.success_patterns, key=lambda item: item.pattern_id))
        failure = tuple(sorted(self.failure_patterns, key=lambda item: item.pattern_id))
        if missing and (success or failure):
            raise ValueError("incomplete week cannot contain patterns")
        for pattern in (*success, *failure):
            if pattern.week_start != self.week_start or pattern.week_end != self.week_end:
                raise ValueError("pattern interval must match weekly reflection")
        guards = tuple(sorted(self.sample_guards, key=lambda item: item.guard_id))
        completeness = tuple(
            guard for guard in guards if guard.guard_kind is WeeklyGuardKind.WEEK_COMPLETENESS
        )
        if len(completeness) != 1:
            raise ValueError("weekly reflection requires exactly one WEEK_COMPLETENESS guard")
        completeness_guard = completeness[0]
        expected_status = (
            SampleGuardStatus.PASSED if not missing else SampleGuardStatus.INSUFFICIENT
        )
        if (
            completeness_guard.present_daily_periods != present
            or completeness_guard.missing_daily_periods != missing
            or completeness_guard.observed_samples != len(present)
            or completeness_guard.required_samples != 7
            or completeness_guard.status is not expected_status
        ):
            raise ValueError("WEEK_COMPLETENESS guard periods must match weekly period lists")
        if not missing and self.available_at < self.week_end:
            raise ValueError("complete week cannot be available before week_end")
        object.__setattr__(self, "present_daily_periods", present)
        object.__setattr__(self, "missing_daily_periods", missing)
        object.__setattr__(self, "input_daily_reflection_ids", daily_ids)
        object.__setattr__(
            self,
            "input_experience_ids",
            tuple(sorted(set(self.input_experience_ids))),
        )
        object.__setattr__(self, "sample_guards", guards)
        object.__setattr__(self, "success_patterns", success)
        object.__setattr__(self, "failure_patterns", failure)
        identity = self.model_dump(mode="json", exclude={"reflection_id"})
        expected = f"weekly-reflection-{canonical_hash(identity)[:20]}"
        if self.reflection_id and self.reflection_id != expected:
            raise ValueError("reflection_id does not match weekly reflection content")
        object.__setattr__(self, "reflection_id", expected)
        return self


_ALLOWED_TRANSITIONS: dict[KnowledgeStatus, frozenset[KnowledgeStatus]] = {
    KnowledgeStatus.OBSERVATION: frozenset(
        {KnowledgeStatus.HYPOTHESIS, KnowledgeStatus.REJECTED, KnowledgeStatus.DEPRECATED}
    ),
    KnowledgeStatus.HYPOTHESIS: frozenset(
        {KnowledgeStatus.CANDIDATE, KnowledgeStatus.REJECTED, KnowledgeStatus.DEPRECATED}
    ),
    KnowledgeStatus.CANDIDATE: frozenset(
        {KnowledgeStatus.VALIDATED, KnowledgeStatus.REJECTED, KnowledgeStatus.DEPRECATED}
    ),
    KnowledgeStatus.VALIDATED: frozenset({KnowledgeStatus.DEPRECATED}),
    KnowledgeStatus.REJECTED: frozenset(),
    KnowledgeStatus.DEPRECATED: frozenset(),
}


class PatternStatusTransition(ReflectionModel):
    transition_id: str = ""
    pattern_id: str = Field(min_length=1)
    pattern_key: str = Field(min_length=1)
    from_status: KnowledgeStatus
    to_status: KnowledgeStatus
    effective_at: UTCDateTime
    action_kind: TransitionActionKind
    actor_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    supporting_evaluation_ids: tuple[str, ...] = ()
    previous_transition_id: str | None = None

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> PatternStatusTransition:
        if self.to_status not in _ALLOWED_TRANSITIONS[self.from_status]:
            raise ValueError("knowledge status transition is not allowed")
        object.__setattr__(
            self,
            "supporting_evaluation_ids",
            tuple(sorted(set(self.supporting_evaluation_ids))),
        )
        identity = self.model_dump(mode="json", exclude={"transition_id"})
        expected = f"pattern-transition-{canonical_hash(identity)[:20]}"
        if self.transition_id and self.transition_id != expected:
            raise ValueError("transition_id does not match transition content")
        object.__setattr__(self, "transition_id", expected)
        return self
