"""Immutable contracts for deterministic paired baseline/candidate comparison."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from axq.reflection.contracts import ReflectionModel
from axq.reflection.evaluation_contracts import CriterionRole, MetricScope, SemanticArtifactRef
from axq.reflection.shared_kernel_candidate_contracts import SharedKernelDataManifestRef
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class PairedEvaluationAdapterKind(StrEnum):
    CANONICAL_PAIRED_METRICS_V1 = "CANONICAL_PAIRED_METRICS_V1"


class PairedMetricStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class PairedCriterionStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"


class PairedParityStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class PairedEvaluationStatus(StrEnum):
    COMPLETED = "COMPLETED"


def canonical_decimal(value: Decimal | float | int | str) -> str:
    """Return one finite, non-exponent decimal representation."""

    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("value is not a decimal") from exc
    if not number.is_finite():
        raise ValueError("canonical decimal must be finite")
    if number == 0:
        return "0"
    return format(number.normalize(), "f")


class PairedArtifactRef(SemanticArtifactRef):
    scope: MetricScope
    manifest_ref: SharedKernelDataManifestRef
    policy_identity: str = Field(min_length=1)
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_scope(self) -> PairedArtifactRef:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS paired artifacts are forbidden")
        if self.manifest_ref.scope is not self.scope:
            raise ValueError("paired artifact and manifest scopes must match")
        return self


class PairedEvaluationRequest(ReflectionModel):
    request_id: str = ""
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    baseline_policy_set_id: str = Field(min_length=1)
    candidate_config_id: str = Field(min_length=1)
    baseline_artifact_refs: tuple[PairedArtifactRef, ...] = Field(min_length=1)
    candidate_artifact_refs: tuple[PairedArtifactRef, ...] = Field(min_length=1)
    evaluation_run_key: str = Field(min_length=1)
    adapter_kind: Literal[
        PairedEvaluationAdapterKind.CANONICAL_PAIRED_METRICS_V1
    ] = PairedEvaluationAdapterKind.CANONICAL_PAIRED_METRICS_V1
    adapter_version: Literal["1.0"] = "1.0"
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    requested_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> PairedEvaluationRequest:
        for field_name in ("baseline_artifact_refs", "candidate_artifact_refs"):
            refs = tuple(sorted(getattr(self, field_name), key=lambda item: item.scope.value))
            if len({item.scope for item in refs}) != len(refs):
                raise ValueError(f"{field_name} scopes must be unique")
            object.__setattr__(self, field_name, refs)
        identity = self.model_dump(mode="json", exclude={"request_id", "requested_at"})
        expected = f"paired-evaluation-request-{canonical_hash(identity)[:20]}"
        if self.request_id and self.request_id != expected:
            raise ValueError("request_id does not match paired evaluation content")
        object.__setattr__(self, "request_id", expected)
        return self


class PairedParityCheck(ReflectionModel):
    check_id: str = ""
    check_key: str = Field(min_length=1)
    status: PairedParityStatus
    reason_code: str | None = None

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PairedParityCheck:
        if self.status is PairedParityStatus.PASS and self.reason_code is not None:
            raise ValueError("passed parity check cannot have a reason code")
        if self.status is PairedParityStatus.FAIL and not self.reason_code:
            raise ValueError("failed parity check requires a reason code")
        identity = self.model_dump(mode="json", exclude={"check_id"})
        expected = f"paired-parity-check-{canonical_hash(identity)[:20]}"
        if self.check_id and self.check_id != expected:
            raise ValueError("check_id does not match parity content")
        object.__setattr__(self, "check_id", expected)
        return self


class PairedMetricComparison(ReflectionModel):
    comparison_id: str = ""
    metric_id: str = Field(min_length=1)
    metric_key: str = Field(min_length=1)
    scope: MetricScope
    status: PairedMetricStatus
    baseline_value: str | None
    candidate_value: str | None
    delta: str | None
    baseline_sample_count: int = Field(ge=0)
    candidate_sample_count: int = Field(ge=0)
    baseline_artifact_ref: PairedArtifactRef | None = None
    candidate_artifact_ref: PairedArtifactRef | None = None
    reason_code: str | None = None

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PairedMetricComparison:
        for field_name in ("baseline_value", "candidate_value", "delta"):
            value = getattr(self, field_name)
            if value is not None and canonical_decimal(value) != value:
                raise ValueError(f"{field_name} must be a canonical decimal")
        if self.status is PairedMetricStatus.AVAILABLE:
            if (
                self.scope is MetricScope.FINAL_OOS
                or self.baseline_value is None
                or self.candidate_value is None
                or self.delta is None
                or self.baseline_sample_count < 1
                or self.candidate_sample_count < 1
                or self.baseline_artifact_ref is None
                or self.candidate_artifact_ref is None
                or self.reason_code is not None
            ):
                raise ValueError("available paired metric requires complete evidence")
        elif not self.reason_code or self.delta is not None:
            raise ValueError("unavailable paired metric requires a reason and no delta")
        identity = self.model_dump(mode="json", exclude={"comparison_id"})
        expected = f"paired-metric-comparison-{canonical_hash(identity)[:20]}"
        if self.comparison_id and self.comparison_id != expected:
            raise ValueError("comparison_id does not match paired metric content")
        object.__setattr__(self, "comparison_id", expected)
        return self


class PairedCriterionOutcome(ReflectionModel):
    outcome_id: str = ""
    criterion_id: str = Field(min_length=1)
    metric_key: str = Field(min_length=1)
    role: CriterionRole
    status: PairedCriterionStatus
    comparison_id: str = Field(min_length=1)
    reason_code: str | None = None

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PairedCriterionOutcome:
        if self.status is PairedCriterionStatus.UNAVAILABLE and not self.reason_code:
            raise ValueError("unavailable paired criterion requires a reason")
        if self.status is not PairedCriterionStatus.UNAVAILABLE and self.reason_code is not None:
            raise ValueError("available paired criterion cannot have a reason code")
        identity = self.model_dump(mode="json", exclude={"outcome_id"})
        expected = f"paired-criterion-outcome-{canonical_hash(identity)[:20]}"
        if self.outcome_id and self.outcome_id != expected:
            raise ValueError("outcome_id does not match paired criterion content")
        object.__setattr__(self, "outcome_id", expected)
        return self


class PairedEvaluationResult(ReflectionModel):
    result_id: str = ""
    request_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    available_at: UTCDateTime
    parity_checks: tuple[PairedParityCheck, ...] = Field(min_length=1)
    metric_comparisons: tuple[PairedMetricComparison, ...] = Field(min_length=1)
    criterion_outcomes: tuple[PairedCriterionOutcome, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> PairedEvaluationResult:
        checks = tuple(sorted(self.parity_checks, key=lambda item: item.check_key))
        comparisons = tuple(sorted(self.metric_comparisons, key=lambda item: item.metric_key))
        outcomes = tuple(sorted(self.criterion_outcomes, key=lambda item: item.criterion_id))
        if len({item.check_key for item in checks}) != len(checks):
            raise ValueError("paired parity check keys must be unique")
        if len({item.metric_key for item in comparisons}) != len(comparisons):
            raise ValueError("paired metric keys must be unique")
        if len({item.criterion_id for item in outcomes}) != len(outcomes):
            raise ValueError("paired criterion IDs must be unique")
        object.__setattr__(self, "parity_checks", checks)
        object.__setattr__(self, "metric_comparisons", comparisons)
        object.__setattr__(self, "criterion_outcomes", outcomes)
        identity = self.model_dump(mode="json", exclude={"result_id"})
        expected = f"paired-evaluation-result-{canonical_hash(identity)[:20]}"
        if self.result_id and self.result_id != expected:
            raise ValueError("result_id does not match paired evaluation content")
        object.__setattr__(self, "result_id", expected)
        return self


class PairedEvaluationAudit(ReflectionModel):
    audit_id: str = ""
    request_id: str = Field(min_length=1)
    result_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    baseline_policy_set_id: str = Field(min_length=1)
    candidate_config_id: str = Field(min_length=1)
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    result_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal[PairedEvaluationStatus.COMPLETED] = PairedEvaluationStatus.COMPLETED
    started_at: UTCDateTime
    completed_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PairedEvaluationAudit:
        if self.completed_at < self.started_at:
            raise ValueError("paired evaluation completion cannot predate start")
        identity = self.model_dump(
            mode="json", exclude={"audit_id", "started_at", "completed_at"}
        )
        expected = f"paired-evaluation-audit-{canonical_hash(identity)[:20]}"
        if self.audit_id and self.audit_id != expected:
            raise ValueError("audit_id does not match paired evaluation content")
        object.__setattr__(self, "audit_id", expected)
        return self
