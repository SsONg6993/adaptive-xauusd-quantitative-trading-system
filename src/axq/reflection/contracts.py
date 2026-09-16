"""Immutable content-addressed contracts for deterministic daily reflection."""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class FindingCategory(StrEnum):
    DIRECTION_OUTCOME = "DIRECTION_OUTCOME"
    SESSION_OUTCOME = "SESSION_OUTCOME"
    REGIME_OUTCOME = "REGIME_OUTCOME"
    CONFIDENCE_CALIBRATION = "CONFIDENCE_CALIBRATION"
    EXCURSION_IMBALANCE = "EXCURSION_IMBALANCE"
    REJECTION_ANOMALY = "REJECTION_ANOMALY"
    AGENT_RELIABILITY = "AGENT_RELIABILITY"
    POSITION_MANAGEMENT_ANOMALY = "POSITION_MANAGEMENT_ANOMALY"
    RUNTIME_ANOMALY = "RUNTIME_ANOMALY"


class FindingSignal(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    WARNING = "WARNING"


class SampleGuardStatus(StrEnum):
    PASSED = "PASSED"
    INSUFFICIENT = "INSUFFICIENT"
    UNAVAILABLE = "UNAVAILABLE"


class ReflectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ReflectionPolicy(ReflectionModel):
    policy_id: str = ""
    min_trade_group_samples: int = Field(default=3, ge=1)
    min_confidence_samples: int = Field(default=5, ge=1)
    min_rejection_samples: int = Field(default=5, ge=1)
    min_agent_samples: int = Field(default=3, ge=1)
    min_position_management_samples: int = Field(default=3, ge=1)
    min_runtime_anomaly_samples: int = Field(default=1, ge=1)
    negative_average_r_threshold: FiniteFloat = 0.0
    positive_average_r_threshold: FiniteFloat = 0.0
    confidence_gap_threshold: FiniteFloat = Field(default=0.20, ge=0.0, le=1.0)
    adverse_favorable_ratio_threshold: FiniteFloat = Field(default=1.25, gt=0.0)
    rejection_share_threshold: FiniteFloat = Field(default=0.50, ge=0.0, le=1.0)
    weak_agent_win_rate_threshold: FiniteFloat = Field(default=0.40, ge=0.0, le=1.0)
    zero_protection_rate_threshold: FiniteFloat = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def bind_identity(self) -> ReflectionPolicy:
        if self.positive_average_r_threshold < self.negative_average_r_threshold:
            raise ValueError("positive R threshold cannot be below negative R threshold")
        identity = self.model_dump(mode="json", exclude={"policy_id"})
        expected = f"reflection-policy-{canonical_hash(identity)[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class MetricFact(ReflectionModel):
    name: str = Field(min_length=1)
    value: FiniteFloat | None
    unit: str = Field(min_length=1)


class SampleGuardRecord(ReflectionModel):
    guard_id: str = ""
    category: FindingCategory
    scope: str = Field(min_length=1)
    scope_value: str = Field(min_length=1)
    observed_samples: int = Field(ge=0)
    required_samples: int = Field(ge=1)
    status: SampleGuardStatus
    supporting_experience_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> SampleGuardRecord:
        sources = tuple(sorted(set(self.supporting_experience_ids)))
        object.__setattr__(self, "supporting_experience_ids", sources)
        if (
            self.status is SampleGuardStatus.PASSED
            and self.observed_samples < self.required_samples
        ):
            raise ValueError("passed sample guard does not meet required samples")
        if (
            self.status is SampleGuardStatus.INSUFFICIENT
            and self.observed_samples >= self.required_samples
        ):
            raise ValueError("insufficient sample guard already meets required samples")
        if self.status is SampleGuardStatus.UNAVAILABLE and self.observed_samples != 0:
            raise ValueError("unavailable sample guard must have zero observed samples")
        identity = self.model_dump(mode="json", exclude={"guard_id"})
        expected = f"sample-guard-{canonical_hash(identity)[:20]}"
        if self.guard_id and self.guard_id != expected:
            raise ValueError("guard_id does not match guard content")
        object.__setattr__(self, "guard_id", expected)
        return self


class ReflectionFinding(ReflectionModel):
    finding_id: str = ""
    category: FindingCategory
    signal: FindingSignal
    reason_code: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    scope_value: str = Field(min_length=1)
    sample_size: int = Field(ge=1)
    metrics: tuple[MetricFact, ...] = Field(min_length=1)
    supporting_experience_ids: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> ReflectionFinding:
        metrics = tuple(sorted(self.metrics, key=lambda item: (item.name, item.unit)))
        if len({(item.name, item.unit) for item in metrics}) != len(metrics):
            raise ValueError("finding metrics must be unique by name and unit")
        sources = tuple(sorted(set(self.supporting_experience_ids)))
        object.__setattr__(self, "metrics", metrics)
        object.__setattr__(self, "supporting_experience_ids", sources)
        identity = self.model_dump(mode="json", exclude={"finding_id"})
        expected = f"reflection-finding-{canonical_hash(identity)[:20]}"
        if self.finding_id and self.finding_id != expected:
            raise ValueError("finding_id does not match finding content")
        object.__setattr__(self, "finding_id", expected)
        return self


class DailyReflection(ReflectionModel):
    reflection_id: str = ""
    period_start: UTCDateTime
    period_end: UTCDateTime
    available_at: UTCDateTime
    policy_id: str = Field(min_length=1)
    input_experience_ids: tuple[str, ...] = ()
    findings: tuple[ReflectionFinding, ...] = ()
    sample_guards: tuple[SampleGuardRecord, ...] = ()
    supersedes_reflection_id: str | None = None

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> DailyReflection:
        if self.period_start.hour or self.period_start.minute or self.period_start.second:
            raise ValueError("reflection period must start at UTC midnight")
        if self.period_start.microsecond:
            raise ValueError("reflection period must start at UTC midnight")
        if self.period_end - self.period_start != timedelta(days=1):
            raise ValueError("reflection period must span one UTC calendar day")
        if self.available_at < self.period_end:
            raise ValueError("daily reflection cannot be available before period end")
        input_ids = tuple(sorted(set(self.input_experience_ids)))
        findings = tuple(sorted(self.findings, key=lambda item: item.finding_id))
        guards = tuple(sorted(self.sample_guards, key=lambda item: item.guard_id))
        if len({item.finding_id for item in findings}) != len(findings):
            raise ValueError("daily reflection contains duplicate findings")
        if len({item.guard_id for item in guards}) != len(guards):
            raise ValueError("daily reflection contains duplicate sample guards")
        object.__setattr__(self, "input_experience_ids", input_ids)
        object.__setattr__(self, "findings", findings)
        object.__setattr__(self, "sample_guards", guards)
        identity = self.model_dump(mode="json", exclude={"reflection_id"})
        expected = f"daily-reflection-{canonical_hash(identity)[:20]}"
        if self.reflection_id and self.reflection_id != expected:
            raise ValueError("reflection_id does not match reflection content")
        object.__setattr__(self, "reflection_id", expected)
        return self
