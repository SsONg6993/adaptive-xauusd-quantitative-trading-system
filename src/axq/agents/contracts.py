"""Strict, replay-safe specialist-agent evidence contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.runtime import FreshnessStatus
from axq.runtime.state import UTCDateTime
from axq.tools import ToolProvenance, ToolResult, ToolStatus
from axq.tools.contracts import FactScalar
from axq.versioning import canonical_hash


class AgentStatus(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    ABSTAINED = "ABSTAINED"
    ERROR = "ERROR"


class DirectionalBias(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class HypothesisStatus(StrEnum):
    NONE = "NONE"
    DEVELOPING = "DEVELOPING"
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    WEAKENING = "WEAKENING"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    ABSTAINED = "ABSTAINED"


class HypothesisRelationship(StrEnum):
    NEW = "NEW"
    UNCHANGED = "UNCHANGED"
    STRENGTHENED = "STRENGTHENED"
    WEAKENED = "WEAKENED"
    REVERSED = "REVERSED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


class EvidencePolarity(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXT = "CONTEXT"


class AbstentionReason(StrEnum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    TOOL_FAILURE = "TOOL_FAILURE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    UNSUPPORTED_REGIME = "UNSUPPORTED_REGIME"
    LOW_EVIDENCE_QUALITY = "LOW_EVIDENCE_QUALITY"
    NO_MEANINGFUL_HYPOTHESIS = "NO_MEANINGFUL_HYPOTHESIS"


class ReasoningMode(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    LOCAL_LLM_ASSISTED = "LOCAL_LLM_ASSISTED"
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"


class AgentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ToolResultReference(AgentModel):
    tool_name: str = Field(min_length=1)
    tool_result_id: str = Field(min_length=1)
    status: ToolStatus
    freshness: FreshnessStatus
    quality_valid: bool
    available_at: UTCDateTime
    provenance: tuple[ToolProvenance, ...] = ()

    @classmethod
    def from_result(cls, result: ToolResult) -> ToolResultReference:
        return cls(
            tool_name=result.tool_name,
            tool_result_id=result.result_id,
            status=result.status,
            freshness=result.freshness,
            quality_valid=result.quality.valid,
            available_at=result.available_at,
            provenance=result.provenance,
        )


class EvidenceReference(AgentModel):
    tool_name: str = Field(min_length=1)
    tool_result_id: str = Field(min_length=1)
    fact_name: str = Field(min_length=1)
    fact_value: FactScalar
    polarity: EvidencePolarity
    strength: float = Field(ge=0.0, le=1.0)
    freshness: FreshnessStatus
    quality_valid: bool
    explanation: str | None = Field(default=None, max_length=300)


class HypothesisInvalidation(AgentModel):
    invalidated: bool
    reason: str | None = Field(default=None, max_length=300)
    tool_result_id: str | None = None
    fact_name: str | None = None

    @model_validator(mode="after")
    def require_reason(self) -> HypothesisInvalidation:
        if self.invalidated and not self.reason:
            raise ValueError("invalidated hypothesis requires a reason")
        if not self.invalidated and any(
            value is not None for value in (self.reason, self.tool_result_id, self.fact_name)
        ):
            raise ValueError("non-invalidated hypothesis cannot contain invalidation details")
        return self


class AgentToolRequest(AgentModel):
    tool_name: str = Field(min_length=1)
    requested_facts: tuple[str, ...] = Field(min_length=1, max_length=8)
    reason: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_facts(self) -> AgentToolRequest:
        if len(set(self.requested_facts)) != len(self.requested_facts):
            raise ValueError("requested facts must be unique")
        return self


class ReasoningRecord(AgentModel):
    mode: ReasoningMode = ReasoningMode.DETERMINISTIC
    component_version: str = "deterministic-v1"
    fallback_reason: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_fallback(self) -> ReasoningRecord:
        if self.mode is ReasoningMode.DETERMINISTIC_FALLBACK and not self.fallback_reason:
            raise ValueError("deterministic fallback requires a reason")
        return self


class AgentEvidence(AgentModel):
    evidence_id: str = ""
    agent_name: str = Field(min_length=1)
    agent_version: str = Field(min_length=1)
    runtime_state_id: str = Field(min_length=1)
    feature_snapshot_id: str | None = None
    as_of: UTCDateTime
    available_at: UTCDateTime
    hypothesis_id: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1, max_length=200)
    hypothesis_status: HypothesisStatus
    relationship: HypothesisRelationship
    previous_hypothesis_id: str | None = None
    direction: DirectionalBias | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    evidence_quality: float = Field(ge=0.0, le=1.0)
    evidence_for: tuple[EvidenceReference, ...] = ()
    evidence_against: tuple[EvidenceReference, ...] = ()
    invalidation: HypothesisInvalidation
    freshness: FreshnessStatus
    status: AgentStatus
    tool_inputs: tuple[ToolResultReference, ...] = ()
    tool_requests: tuple[AgentToolRequest, ...] = Field(default=(), max_length=8)
    abstention_reason: AbstentionReason | None = None
    setup_id: str | None = None
    thesis_id: str | None = None
    rationale: str | None = Field(default=None, max_length=500)
    reasoning: ReasoningRecord = ReasoningRecord()

    @model_validator(mode="after")
    def validate_semantics_and_identity(self) -> AgentEvidence:
        if self.available_at > self.as_of:
            raise ValueError("agent evidence cannot be available after its as_of time")
        if self.confidence > self.evidence_quality:
            raise ValueError("confidence cannot exceed evidence quality")
        if self.status is AgentStatus.DEGRADED and self.confidence > 0.5:
            raise ValueError("degraded confidence cannot exceed 0.5")
        if self.status in {AgentStatus.ABSTAINED, AgentStatus.ERROR} and self.confidence != 0.0:
            raise ValueError("abstained or error evidence must have zero confidence")
        if self.relationship is HypothesisRelationship.NEW:
            if self.previous_hypothesis_id is not None:
                raise ValueError("new hypothesis cannot reference previous_hypothesis_id")
        elif self.previous_hypothesis_id is None:
            raise ValueError("relationship requires previous_hypothesis_id")
        if (
            self.relationship is HypothesisRelationship.REVERSED
            and self.hypothesis_id == self.previous_hypothesis_id
        ):
            raise ValueError("reversed evidence requires a new hypothesis_id")
        if self.relationship not in {
            HypothesisRelationship.NEW,
            HypothesisRelationship.REVERSED,
        } and self.hypothesis_id != self.previous_hypothesis_id:
            raise ValueError("continued relationship must retain hypothesis_id")
        if self.status is AgentStatus.ABSTAINED:
            if self.abstention_reason is None:
                raise ValueError("abstained evidence requires an abstention reason")
            if self.direction is not None:
                raise ValueError("abstained evidence cannot contain direction")
            if self.hypothesis_status is not HypothesisStatus.ABSTAINED:
                raise ValueError("abstained evidence requires ABSTAINED hypothesis status")
        elif self.abstention_reason is not None:
            raise ValueError("abstention reason is only valid for abstained evidence")
        if self.hypothesis_status is HypothesisStatus.INVALIDATED:
            if not self.invalidation.invalidated:
                raise ValueError("INVALIDATED status requires invalidation details")
        elif self.invalidation.invalidated:
            raise ValueError("invalidation details require INVALIDATED status")
        if (
            self.relationship is HypothesisRelationship.INVALIDATED
            and self.hypothesis_status is not HypothesisStatus.INVALIDATED
        ):
            raise ValueError("INVALIDATED relationship requires INVALIDATED status")
        if (
            self.relationship is HypothesisRelationship.EXPIRED
            and self.hypothesis_status is not HypothesisStatus.EXPIRED
        ):
            raise ValueError("EXPIRED relationship requires EXPIRED status")
        if self.status is AgentStatus.READY and any(
            item.status is not ToolStatus.AVAILABLE for item in self.tool_inputs
        ):
            raise ValueError("READY evidence requires available tool inputs")
        identity = self.model_dump(mode="json", exclude={"evidence_id"})
        expected = f"ae-{canonical_hash(identity)[:20]}"
        if self.evidence_id and self.evidence_id != expected:
            raise ValueError("evidence_id does not match evidence content")
        object.__setattr__(self, "evidence_id", expected)
        return self
