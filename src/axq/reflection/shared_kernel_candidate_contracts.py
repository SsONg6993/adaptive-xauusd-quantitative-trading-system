"""Immutable contracts for governed shared-kernel candidate evaluation."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from axq.master import FusionPolicy
from axq.reflection.contracts import ReflectionModel
from axq.reflection.evaluation_contracts import MetricScope, SemanticArtifactRef
from axq.reflection.proposal_contracts import ProposalTargetComponent
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash

SharedKernelCSVName = Literal[
    "xauusd_m5.csv",
    "xauusd_m15.csv",
    "xauusd_h1.csv",
    "xauusd_h4.csv",
]
_REQUIRED_FILES = frozenset(
    {"xauusd_m5.csv", "xauusd_m15.csv", "xauusd_h1.csv", "xauusd_h4.csv"}
)


class SharedKernelCandidateEngineKind(StrEnum):
    SHARED_KERNEL_MASTER_FUSION_V1 = "SHARED_KERNEL_MASTER_FUSION_V1"


class SharedKernelCandidateStatus(StrEnum):
    COMPLETED = "COMPLETED"


class SharedKernelCSVFileRef(ReflectionModel):
    file_name: SharedKernelCSVName
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(gt=0)


class SharedKernelDataManifestRef(SemanticArtifactRef):
    scope: MetricScope

    @model_validator(mode="after")
    def reject_final_oos(self) -> SharedKernelDataManifestRef:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS shared-kernel data is forbidden")
        return self


class SharedKernelReplayResultRef(SemanticArtifactRef):
    scope: MetricScope

    @model_validator(mode="after")
    def reject_final_oos(self) -> SharedKernelReplayResultRef:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS shared-kernel replay results are forbidden")
        return self


class SharedKernelMetricArtifactRef(SemanticArtifactRef):
    scope: MetricScope

    @model_validator(mode="after")
    def reject_final_oos(self) -> SharedKernelMetricArtifactRef:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS shared-kernel metric artifacts are forbidden")
        return self


class FrozenSharedKernelCandidateConfig(ReflectionModel):
    config_id: str = ""
    proposal_id: str = Field(min_length=1)
    proposal_key: str = Field(min_length=1)
    target_component: Literal[
        ProposalTargetComponent.MASTER_FUSION
    ] = ProposalTargetComponent.MASTER_FUSION
    base_policy_set_id: str = Field(min_length=1)
    source_identity: str = Field(min_length=1)
    fusion_policy: FusionPolicy

    @model_validator(mode="after")
    def bind_identity(self) -> FrozenSharedKernelCandidateConfig:
        identity = self.model_dump(mode="json", exclude={"config_id"})
        expected = f"frozen-shared-kernel-config-{canonical_hash(identity)[:20]}"
        if self.config_id and self.config_id != expected:
            raise ValueError("config_id does not match frozen candidate content")
        object.__setattr__(self, "config_id", expected)
        return self


class SharedKernelReplayDataManifest(ReflectionModel):
    manifest_id: str = ""
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    scope: MetricScope
    period_start: UTCDateTime
    period_end: UTCDateTime
    available_at: UTCDateTime
    m5_row_count: int = Field(gt=0)
    files: tuple[SharedKernelCSVFileRef, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> SharedKernelReplayDataManifest:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS shared-kernel data manifests are forbidden")
        if not self.period_start < self.period_end <= self.available_at:
            raise ValueError("data manifest UTC interval or availability is invalid")
        files = tuple(sorted(self.files, key=lambda item: item.file_name))
        if {item.file_name for item in files} != _REQUIRED_FILES:
            raise ValueError("data manifest requires exactly the four canonical CSV files")
        object.__setattr__(self, "files", files)
        identity = self.model_dump(mode="json", exclude={"manifest_id"})
        expected = f"shared-kernel-data-manifest-{canonical_hash(identity)[:20]}"
        if self.manifest_id and self.manifest_id != expected:
            raise ValueError("manifest_id does not match shared-kernel data content")
        object.__setattr__(self, "manifest_id", expected)
        return self


class SharedKernelCandidateRequest(ReflectionModel):
    request_id: str = ""
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    config_ref: SemanticArtifactRef
    data_manifest_refs: tuple[SharedKernelDataManifestRef, ...] = Field(min_length=1)
    evaluation_run_key: str = Field(min_length=1)
    engine_kind: Literal[
        SharedKernelCandidateEngineKind.SHARED_KERNEL_MASTER_FUSION_V1
    ] = SharedKernelCandidateEngineKind.SHARED_KERNEL_MASTER_FUSION_V1
    engine_version: Literal["1.0"] = "1.0"
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    requested_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> SharedKernelCandidateRequest:
        refs = tuple(sorted(self.data_manifest_refs, key=lambda item: item.scope.value))
        if len({item.scope for item in refs}) != len(refs):
            raise ValueError("shared-kernel data manifest scopes must be unique")
        object.__setattr__(self, "data_manifest_refs", refs)
        identity = self.model_dump(mode="json", exclude={"request_id", "requested_at"})
        expected = f"shared-kernel-candidate-request-{canonical_hash(identity)[:20]}"
        if self.request_id and self.request_id != expected:
            raise ValueError("request_id does not match shared-kernel candidate content")
        object.__setattr__(self, "request_id", expected)
        return self


class SharedKernelCandidateAudit(ReflectionModel):
    audit_id: str = ""
    request_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    config_ref: SemanticArtifactRef
    data_manifest_refs: tuple[SharedKernelDataManifestRef, ...] = Field(min_length=1)
    replay_result_refs: tuple[SharedKernelReplayResultRef, ...] = Field(min_length=1)
    output_artifact_refs: tuple[SharedKernelMetricArtifactRef, ...] = Field(min_length=1)
    evaluation_run_key: str = Field(min_length=1)
    engine_kind: Literal[
        SharedKernelCandidateEngineKind.SHARED_KERNEL_MASTER_FUSION_V1
    ] = SharedKernelCandidateEngineKind.SHARED_KERNEL_MASTER_FUSION_V1
    engine_version: Literal["1.0"] = "1.0"
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    status: Literal[
        SharedKernelCandidateStatus.COMPLETED
    ] = SharedKernelCandidateStatus.COMPLETED
    started_at: UTCDateTime
    completed_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> SharedKernelCandidateAudit:
        if self.completed_at < self.started_at:
            raise ValueError("shared-kernel candidate completion cannot predate start")
        for field_name in (
            "data_manifest_refs",
            "replay_result_refs",
            "output_artifact_refs",
        ):
            values = tuple(sorted(getattr(self, field_name), key=lambda item: item.scope.value))
            if len({item.scope for item in values}) != len(values):
                raise ValueError(f"{field_name} scopes must be unique")
            object.__setattr__(self, field_name, values)
        scopes = {item.scope for item in self.data_manifest_refs}
        if scopes != {item.scope for item in self.replay_result_refs} or scopes != {
            item.scope for item in self.output_artifact_refs
        }:
            raise ValueError("shared-kernel audit scopes must match")
        identity = self.model_dump(
            mode="json", exclude={"audit_id", "started_at", "completed_at"}
        )
        expected = f"shared-kernel-candidate-audit-{canonical_hash(identity)[:20]}"
        if self.audit_id and self.audit_id != expected:
            raise ValueError("audit_id does not match shared-kernel candidate content")
        object.__setattr__(self, "audit_id", expected)
        return self
