"""Immutable contracts for governed deterministic candidate replay."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from axq.reflection.contracts import ReflectionModel
from axq.reflection.evaluation_contracts import MetricScope, SemanticArtifactRef
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class CandidateReplayEngineKind(StrEnum):
    CONTROLLED_REPLAY_FIXTURE_V1 = "CONTROLLED_REPLAY_FIXTURE_V1"


class CandidateReplayStatus(StrEnum):
    COMPLETED = "COMPLETED"


class CandidateReplayArtifactRef(SemanticArtifactRef):
    scope: MetricScope

    @model_validator(mode="after")
    def reject_final_oos(self) -> CandidateReplayArtifactRef:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS candidate replay artifacts are forbidden")
        return self


class ControlledMetricValue(ReflectionModel):
    metric_key: str = Field(min_length=1)
    value: FiniteFloat


class ControlledReplayObservation(ReflectionModel):
    event_id: str = Field(min_length=1)
    available_at: UTCDateTime
    metric_values: tuple[ControlledMetricValue, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def normalize_values(self) -> ControlledReplayObservation:
        values = tuple(sorted(self.metric_values, key=lambda item: item.metric_key))
        if len({item.metric_key for item in values}) != len(values):
            raise ValueError("controlled replay metric keys must be unique")
        object.__setattr__(self, "metric_values", values)
        return self


class ControlledReplayFixtureArtifact(ReflectionModel):
    artifact_id: str = ""
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    scope: MetricScope
    available_at: UTCDateTime
    observations: tuple[ControlledReplayObservation, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> ControlledReplayFixtureArtifact:
        if self.scope is MetricScope.FINAL_OOS:
            raise ValueError("Final OOS controlled replay fixtures are forbidden")
        observations = tuple(
            sorted(self.observations, key=lambda item: (item.available_at, item.event_id))
        )
        if len({item.event_id for item in observations}) != len(observations):
            raise ValueError("controlled replay event IDs must be unique")
        if observations[-1].available_at > self.available_at:
            raise ValueError("fixture availability cannot predate an observation")
        object.__setattr__(self, "observations", observations)
        identity = self.model_dump(mode="json", exclude={"artifact_id"})
        expected = f"controlled-replay-fixture-{canonical_hash(identity)[:20]}"
        if self.artifact_id and self.artifact_id != expected:
            raise ValueError("artifact_id does not match controlled replay fixture content")
        object.__setattr__(self, "artifact_id", expected)
        return self


class CandidateReplayRequest(ReflectionModel):
    request_id: str = ""
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    evaluation_run_key: str = Field(min_length=1)
    engine_kind: Literal[
        CandidateReplayEngineKind.CONTROLLED_REPLAY_FIXTURE_V1
    ] = CandidateReplayEngineKind.CONTROLLED_REPLAY_FIXTURE_V1
    engine_version: Literal["1.0"] = "1.0"
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    input_artifact_refs: tuple[CandidateReplayArtifactRef, ...] = Field(min_length=1)
    requested_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> CandidateReplayRequest:
        refs = tuple(sorted(self.input_artifact_refs, key=lambda item: item.scope.value))
        if len({item.scope for item in refs}) != len(refs):
            raise ValueError("candidate replay input scopes must be unique")
        object.__setattr__(self, "input_artifact_refs", refs)
        identity = self.model_dump(mode="json", exclude={"request_id", "requested_at"})
        expected = f"candidate-replay-request-{canonical_hash(identity)[:20]}"
        if self.request_id and self.request_id != expected:
            raise ValueError("request_id does not match candidate replay content")
        object.__setattr__(self, "request_id", expected)
        return self


class CandidateReplayAudit(ReflectionModel):
    audit_id: str = ""
    request_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    evaluation_run_key: str = Field(min_length=1)
    engine_kind: Literal[
        CandidateReplayEngineKind.CONTROLLED_REPLAY_FIXTURE_V1
    ] = CandidateReplayEngineKind.CONTROLLED_REPLAY_FIXTURE_V1
    engine_version: Literal["1.0"] = "1.0"
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    input_artifact_refs: tuple[CandidateReplayArtifactRef, ...] = Field(min_length=1)
    output_artifact_refs: tuple[CandidateReplayArtifactRef, ...] = Field(min_length=1)
    status: Literal[CandidateReplayStatus.COMPLETED] = CandidateReplayStatus.COMPLETED
    started_at: UTCDateTime
    completed_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> CandidateReplayAudit:
        if self.completed_at < self.started_at:
            raise ValueError("candidate replay completion cannot predate start")
        inputs = tuple(sorted(self.input_artifact_refs, key=lambda item: item.scope.value))
        outputs = tuple(sorted(self.output_artifact_refs, key=lambda item: item.scope.value))
        if len({item.scope for item in inputs}) != len(inputs):
            raise ValueError("candidate replay audit input scopes must be unique")
        if len({item.scope for item in outputs}) != len(outputs):
            raise ValueError("candidate replay audit output scopes must be unique")
        if {item.scope for item in inputs} != {item.scope for item in outputs}:
            raise ValueError("candidate replay input and output scopes must match")
        object.__setattr__(self, "input_artifact_refs", inputs)
        object.__setattr__(self, "output_artifact_refs", outputs)
        identity = self.model_dump(
            mode="json",
            exclude={"audit_id", "started_at", "completed_at"},
        )
        expected = f"candidate-replay-audit-{canonical_hash(identity)[:20]}"
        if self.audit_id and self.audit_id != expected:
            raise ValueError("audit_id does not match candidate replay content")
        object.__setattr__(self, "audit_id", expected)
        return self
