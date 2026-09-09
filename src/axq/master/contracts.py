"""Immutable contracts for deterministic specialist-evidence fusion."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.agents import AgentStatus, DirectionalBias
from axq.runtime.kernel import AGENT_ORDER
from axq.runtime.state import UTCDateTime
from axq.schemas import Signal
from axq.versioning import canonical_hash


class MasterModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class EvidenceDisposition(StrEnum):
    CONTRIBUTED = "CONTRIBUTED"
    DEGRADED_CONTRIBUTION = "DEGRADED_CONTRIBUTION"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    ABSTAINED = "ABSTAINED"
    ERROR = "ERROR"
    TERMINAL = "TERMINAL"
    ZERO_CONFIDENCE = "ZERO_CONFIDENCE"


class FusionReason(StrEnum):
    ACTIONABLE_BUY = "ACTIONABLE_BUY"
    ACTIONABLE_SELL = "ACTIONABLE_SELL"
    NO_READY_DIRECTIONAL_EVIDENCE = "NO_READY_DIRECTIONAL_EVIDENCE"
    BELOW_SCORE_THRESHOLD = "BELOW_SCORE_THRESHOLD"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    HIGH_UNCERTAINTY = "HIGH_UNCERTAINTY"
    HIGH_CONTRADICTION = "HIGH_CONTRADICTION"
    HIGH_DISAGREEMENT = "HIGH_DISAGREEMENT"


class SpecialistWeight(MasterModel):
    agent_name: str = Field(min_length=1)
    weight: float = Field(gt=0.0, le=10.0)


class FusionPolicy(MasterModel):
    policy_id: str = ""
    policy_version: str = Field(min_length=1)
    specialist_weights: tuple[SpecialistWeight, ...]
    degraded_weight_multiplier: float = Field(ge=0.0, le=1.0)
    minimum_actionable_score: float = Field(ge=0.0, le=1.0)
    minimum_actionable_confidence: float = Field(ge=0.0, le=1.0)
    maximum_actionable_uncertainty: float = Field(ge=0.0, le=1.0)
    maximum_actionable_contradiction: float = Field(ge=0.0, le=1.0)
    maximum_actionable_disagreement: float = Field(ge=0.0, le=1.0)
    minimum_ready_directional_agents: int = Field(ge=1, le=len(AGENT_ORDER))

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> FusionPolicy:
        names = tuple(item.agent_name for item in self.specialist_weights)
        if len(names) != len(set(names)):
            raise ValueError("specialist fusion weights must be unique")
        if set(names) != set(AGENT_ORDER):
            raise ValueError("fusion policy requires exactly the canonical specialists")
        by_name = {item.agent_name: item for item in self.specialist_weights}
        ordered = tuple(by_name[name] for name in AGENT_ORDER)
        object.__setattr__(self, "specialist_weights", ordered)
        identity = self.model_dump(mode="json", exclude={"policy_id"})
        expected = f"mfp-{canonical_hash(identity)[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match fusion policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class SpecialistContribution(MasterModel):
    agent_name: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    status: AgentStatus
    direction: DirectionalBias | None
    disposition: EvidenceDisposition
    configured_weight: float = Field(gt=0.0)
    applied_weight: float = Field(ge=0.0)
    effective_strength: float = Field(ge=0.0, le=10.0)
    signed_score: float = Field(ge=-10.0, le=10.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    internal_contradiction: float = Field(ge=0.0, le=1.0)


class MasterProposal(MasterModel):
    proposal_id: str = ""
    bundle_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    runtime_state_id: str = Field(min_length=1)
    as_of: UTCDateTime
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    decision: Signal
    actionable: bool
    confidence: float = Field(ge=0.0, le=1.0)
    net_score: float = Field(ge=-1.0, le=1.0)
    bullish_score: float = Field(ge=0.0, le=1.0)
    bearish_score: float = Field(ge=0.0, le=1.0)
    contradiction: float = Field(ge=0.0, le=1.0)
    disagreement: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    ready_directional_agents: int = Field(ge=0)
    contributing_evidence_ids: tuple[str, ...]
    contributions: tuple[SpecialistContribution, ...]
    reason_codes: tuple[FusionReason, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> MasterProposal:
        if tuple(item.agent_name for item in self.contributions) != AGENT_ORDER:
            raise ValueError("proposal contributions must use canonical specialist order")
        expected_contributors = tuple(
            item.evidence_id
            for item in self.contributions
            if item.disposition
            in {
                EvidenceDisposition.CONTRIBUTED,
                EvidenceDisposition.DEGRADED_CONTRIBUTION,
            }
        )
        if self.contributing_evidence_ids != expected_contributors:
            raise ValueError("contributing evidence IDs do not match contribution audit")
        if self.actionable != (self.decision is not Signal.HOLD):
            raise ValueError("only BUY or SELL proposals are actionable")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("fusion reason codes must be unique")
        action_reason = {
            Signal.BUY: FusionReason.ACTIONABLE_BUY,
            Signal.SELL: FusionReason.ACTIONABLE_SELL,
        }.get(self.decision)
        if action_reason is not None and self.reason_codes != (action_reason,):
            raise ValueError("actionable proposal requires exactly its action reason")
        if self.decision is Signal.HOLD and any(
            reason in {FusionReason.ACTIONABLE_BUY, FusionReason.ACTIONABLE_SELL}
            for reason in self.reason_codes
        ):
            raise ValueError("HOLD proposal cannot contain an actionable reason")
        identity = self.model_dump(mode="json", exclude={"proposal_id"})
        expected = f"mp-{canonical_hash(identity)[:20]}"
        if self.proposal_id and self.proposal_id != expected:
            raise ValueError("proposal_id does not match proposal content")
        object.__setattr__(self, "proposal_id", expected)
        return self
