"""Immutable contracts for deterministic proposal-evaluation execution."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from axq.reflection.contracts import ReflectionModel
from axq.reflection.evaluation_contracts import MetricScope, SemanticArtifactRef
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class EvaluationAdapterKind(StrEnum):
    CANONICAL_METRIC_SAMPLES_V1 = "CANONICAL_METRIC_SAMPLES_V1"


class EvaluationExecutionStatus(StrEnum):
    COMPLETED = "COMPLETED"


class ExecutionInputArtifactRef(SemanticArtifactRef):
    scope: MetricScope

    @model_validator(mode="after")
    def reject_final_oos(self) -> ExecutionInputArtifactRef:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS execution input is forbidden")
        return self


class MetricSampleSeries(ReflectionModel):
    metric_key: str = Field(min_length=1)
    values: tuple[FiniteFloat, ...] = Field(min_length=1)


class CanonicalMetricSampleArtifact(ReflectionModel):
    artifact_id: str = ""
    scope: MetricScope
    available_at: UTCDateTime
    series: tuple[MetricSampleSeries, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> CanonicalMetricSampleArtifact:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS sample artifacts are forbidden")
        series = tuple(sorted(self.series, key=lambda item: item.metric_key))
        if len({item.metric_key for item in series}) != len(series):
            raise ValueError("sample series metric keys must be unique")
        object.__setattr__(self, "series", series)
        identity = self.model_dump(mode="json", exclude={"artifact_id"})
        expected = f"canonical-metric-samples-{canonical_hash(identity)[:20]}"
        if self.artifact_id and self.artifact_id != expected:
            raise ValueError("artifact_id does not match metric sample content")
        object.__setattr__(self, "artifact_id", expected)
        return self


class EvaluationExecutionRequest(ReflectionModel):
    request_id: str = ""
    plan_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    evaluation_run_key: str = Field(min_length=1)
    adapter_kind: Literal[
        EvaluationAdapterKind.CANONICAL_METRIC_SAMPLES_V1
    ] = EvaluationAdapterKind.CANONICAL_METRIC_SAMPLES_V1
    adapter_version: Literal["1.0"] = "1.0"
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    input_artifact_refs: tuple[ExecutionInputArtifactRef, ...] = Field(min_length=1)
    requested_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> EvaluationExecutionRequest:
        refs = tuple(sorted(self.input_artifact_refs, key=lambda item: item.scope.value))
        if len({item.scope for item in refs}) != len(refs):
            raise ValueError("execution request input scopes must be unique")
        object.__setattr__(self, "input_artifact_refs", refs)
        identity = self.model_dump(mode="json", exclude={"request_id", "requested_at"})
        expected = f"evaluation-execution-request-{canonical_hash(identity)[:20]}"
        if self.request_id and self.request_id != expected:
            raise ValueError("request_id does not match execution request content")
        object.__setattr__(self, "request_id", expected)
        return self


class EvaluationExecutionAudit(ReflectionModel):
    audit_id: str = ""
    request_id: str = Field(min_length=1)
    result_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    evaluation_run_key: str = Field(min_length=1)
    adapter_kind: Literal[
        EvaluationAdapterKind.CANONICAL_METRIC_SAMPLES_V1
    ] = EvaluationAdapterKind.CANONICAL_METRIC_SAMPLES_V1
    adapter_version: Literal["1.0"] = "1.0"
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    input_artifact_refs: tuple[ExecutionInputArtifactRef, ...] = Field(min_length=1)
    result_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal[EvaluationExecutionStatus.COMPLETED] = EvaluationExecutionStatus.COMPLETED
    started_at: UTCDateTime
    completed_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> EvaluationExecutionAudit:
        if self.completed_at < self.started_at:
            raise ValueError("execution completion cannot predate start")
        refs = tuple(sorted(self.input_artifact_refs, key=lambda item: item.scope.value))
        if len({item.scope for item in refs}) != len(refs):
            raise ValueError("execution audit input scopes must be unique")
        object.__setattr__(self, "input_artifact_refs", refs)
        identity = self.model_dump(
            mode="json",
            exclude={"audit_id", "started_at", "completed_at"},
        )
        expected = f"evaluation-execution-audit-{canonical_hash(identity)[:20]}"
        if self.audit_id and self.audit_id != expected:
            raise ValueError("audit_id does not match execution audit content")
        object.__setattr__(self, "audit_id", expected)
        return self
