"""Strict content-addressed contracts for Phase 8 outcome experiences."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.agents import AgentStatus, DirectionalBias, HypothesisStatus
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.schemas import Signal
from axq.versioning import canonical_hash


class ExperienceType(StrEnum):
    DECISION = "DECISION"
    TRADE = "TRADE"
    REJECTED_DECISION = "REJECTED_DECISION"
    POSITION_MANAGEMENT = "POSITION_MANAGEMENT"
    RUNTIME_ANOMALY = "RUNTIME_ANOMALY"
    AGENT_CONTRIBUTION = "AGENT_CONTRIBUTION"
    COUNTERFACTUAL = "COUNTERFACTUAL"


class AttributionStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class RejectionLayer(StrEnum):
    DISCIPLINE = "DISCIPLINE"
    RISK = "RISK"
    POSITION_ACTION_SAFETY = "POSITION_ACTION_SAFETY"


class ExperienceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ExperienceProvenance(ExperienceModel):
    runtime_event_ids: tuple[str, ...] = ()
    evidence_bundle_ids: tuple[str, ...] = ()
    agent_evidence_ids: tuple[str, ...] = ()
    thesis_ids: tuple[str, ...] = ()
    scenario_ids: tuple[str, ...] = ()
    master_proposal_ids: tuple[str, ...] = ()
    discipline_outcome_ids: tuple[str, ...] = ()
    risk_outcome_ids: tuple[str, ...] = ()
    execution_intent_ids: tuple[str, ...] = ()
    execution_result_ids: tuple[str, ...] = ()
    position_management_outcome_ids: tuple[str, ...] = ()
    position_action_safety_outcome_ids: tuple[str, ...] = ()
    position_action_intent_ids: tuple[str, ...] = ()
    position_action_transport_result_ids: tuple[str, ...] = ()
    replay_fill_ids: tuple[str, ...] = ()
    replay_trade_ids: tuple[str, ...] = ()
    feature_snapshot_ids: tuple[str, ...] = ()
    tool_result_ids: tuple[str, ...] = ()
    reconciliation_report_ids: tuple[str, ...] = ()
    resume_readiness_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def normalize_and_require_source(self) -> ExperienceProvenance:
        populated = False
        for name in type(self).model_fields:
            if name == "schema_version":
                continue
            values = tuple(sorted(set(getattr(self, name))))
            if values:
                populated = True
            object.__setattr__(self, name, values)
        if not populated:
            raise ValueError("experience provenance requires at least one semantic source ID")
        return self

    def source_links(self) -> tuple[tuple[str, str], ...]:
        links: list[tuple[str, str]] = []
        for name in type(self).model_fields:
            if name == "schema_version":
                continue
            links.extend((name, value) for value in getattr(self, name))
        return tuple(sorted(links))


class SpecialistDecisionFact(ExperienceModel):
    specialist: str = Field(min_length=1)
    agent_evidence_id: str = Field(min_length=1)
    status: AgentStatus
    direction: DirectionalBias | None = None
    confidence: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    uncertainty: FiniteFloat = Field(ge=0.0, le=1.0)
    evidence_quality: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)


class ExperienceBase(ExperienceModel):
    experience_id: str = ""
    experience_type: ExperienceType
    occurred_at: UTCDateTime
    available_at: UTCDateTime
    symbol: str | None = Field(default=None, min_length=1)
    setup_id: str | None = None
    thesis_id: str | None = None
    scenario_id: str | None = None
    regime: str | None = None
    session: str | None = None
    specialist: str | None = None
    outcome: str = Field(min_length=1)
    attribution_status: AttributionStatus = AttributionStatus.COMPLETE
    missing_links: tuple[str, ...] = ()
    provenance: ExperienceProvenance

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ExperienceBase:
        if self.available_at < self.occurred_at:
            raise ValueError("experience availability cannot precede occurrence")
        missing = tuple(sorted(set(self.missing_links)))
        object.__setattr__(self, "missing_links", missing)
        if self.attribution_status is AttributionStatus.COMPLETE and missing:
            raise ValueError("complete attribution cannot declare missing links")
        if self.attribution_status is AttributionStatus.INCOMPLETE and not missing:
            raise ValueError("incomplete attribution requires missing links")
        identity = self.model_dump(mode="json", exclude={"experience_id"})
        prefix = self.experience_type.value.lower().replace("_", "-")
        expected = f"exp-{prefix}-{canonical_hash(identity)[:20]}"
        if self.experience_id and self.experience_id != expected:
            raise ValueError("experience_id does not match experience content")
        object.__setattr__(self, "experience_id", expected)
        return self


class ActualExperience(ExperienceBase):
    simulated: Literal[False] = False


class DecisionExperience(ActualExperience):
    experience_type: Literal[ExperienceType.DECISION] = ExperienceType.DECISION
    master_proposal_id: str = Field(min_length=1)
    evidence_bundle_id: str = Field(min_length=1)
    decision: Signal
    actionable: bool
    master_confidence: FiniteFloat = Field(ge=0.0, le=1.0)
    disagreement: FiniteFloat = Field(ge=0.0, le=1.0)
    contradiction: FiniteFloat = Field(ge=0.0, le=1.0)
    specialists: tuple[SpecialistDecisionFact, ...] = ()
    discipline_outcome_id: str | None = None
    discipline_result: str | None = None
    risk_outcome_id: str | None = None
    risk_result: str | None = None
    execution_intent_id: str | None = None
    progressed_to: str = Field(min_length=1, default="MASTER")


class TradeExperience(ActualExperience):
    experience_type: Literal[ExperienceType.TRADE] = ExperienceType.TRADE
    replay_trade_id: str = Field(min_length=1)
    execution_intent_id: str = Field(min_length=1)
    execution_result_id: str | None = Field(default=None, min_length=1)
    replay_fill_id: str | None = Field(default=None, min_length=1)
    position_id: str = Field(min_length=1)
    direction: Signal
    entry_time: UTCDateTime
    exit_time: UTCDateTime
    entry_price: FiniteFloat = Field(gt=0.0)
    exit_price: FiniteFloat = Field(gt=0.0)
    volume_lots: FiniteFloat = Field(gt=0.0)
    realized_pnl: FiniteFloat
    r_outcome: FiniteFloat | None = None
    mfe_points: FiniteFloat | None = Field(default=None, ge=0.0)
    mae_points: FiniteFloat | None = Field(default=None, ge=0.0)
    holding_seconds: FiniteFloat = Field(ge=0.0)
    exit_cause: str = Field(min_length=1)
    stop_triggered: bool
    explicit_position_exit: bool
    source_position_action_intent_id: str | None = None
    master_confidence: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    disagreement: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    contradiction: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    specialist_evidence_ids: tuple[str, ...] = ()
    drawdown_contribution: FiniteFloat | None = None

    @model_validator(mode="after")
    def validate_trade(self) -> TradeExperience:
        if self.direction is Signal.HOLD:
            raise ValueError("trade direction cannot be HOLD")
        if self.exit_time < self.entry_time:
            raise ValueError("trade exit cannot precede entry")
        if self.stop_triggered == self.explicit_position_exit:
            raise ValueError("trade requires exactly one actual exit classification")
        return self


class RejectedDecisionExperience(ActualExperience):
    experience_type: Literal[ExperienceType.REJECTED_DECISION] = (
        ExperienceType.REJECTED_DECISION
    )
    rejection_layer: RejectionLayer
    source_proposal_id: str = Field(min_length=1)
    source_outcome_id: str = Field(min_length=1)
    reason_codes: tuple[str, ...] = Field(min_length=1)
    master_confidence: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    relevant_safety_state_ids: tuple[str, ...] = ()


class PositionManagementExperience(ActualExperience):
    experience_type: Literal[ExperienceType.POSITION_MANAGEMENT] = (
        ExperienceType.POSITION_MANAGEMENT
    )
    position_management_outcome_id: str = Field(min_length=1)
    position_id: str | None = Field(default=None, min_length=1)
    original_execution_intent_id: str | None = Field(default=None, min_length=1)
    original_execution_result_id: str | None = Field(default=None, min_length=1)
    management_result: str = Field(min_length=1)
    reason_codes: tuple[str, ...] = Field(min_length=1)
    current_thesis_lifecycle: HypothesisStatus | None = None
    position_action_safety_outcome_id: str | None = None
    position_action_intent_id: str | None = None
    position_action_transport_result_id: str | None = None
    protection_reached_transport: bool | None = None
    mfe_points: FiniteFloat | None = Field(default=None, ge=0.0)
    mae_points: FiniteFloat | None = Field(default=None, ge=0.0)
    r_outcome: FiniteFloat | None = None


class RuntimeAnomalyExperience(ActualExperience):
    experience_type: Literal[ExperienceType.RUNTIME_ANOMALY] = ExperienceType.RUNTIME_ANOMALY
    anomaly_type: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    source_semantic_id: str = Field(min_length=1)
    reason_codes: tuple[str, ...] = Field(min_length=1)
    resolution_status: str | None = None


class AgentContributionExperience(ActualExperience):
    experience_type: Literal[ExperienceType.AGENT_CONTRIBUTION] = (
        ExperienceType.AGENT_CONTRIBUTION
    )
    specialist: str = Field(min_length=1)
    agent_evidence_id: str = Field(min_length=1)
    hypothesis_id: str | None = None
    hypothesis: str | None = None
    direction: DirectionalBias | None = None
    lifecycle: HypothesisStatus | None = None
    status: AgentStatus
    confidence: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    uncertainty: FiniteFloat = Field(ge=0.0, le=1.0)
    evidence_quality: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    evidence_for_count: int | None = Field(default=None, ge=0)
    evidence_against_count: int | None = Field(default=None, ge=0)
    tool_result_ids: tuple[str, ...] = ()
    master_proposal_id: str = Field(min_length=1)
    master_decision: Signal
    downstream_outcome: str | None = None


class CounterfactualExperience(ExperienceBase):
    experience_type: Literal[ExperienceType.COUNTERFACTUAL] = ExperienceType.COUNTERFACTUAL
    simulated: Literal[True] = True
    symbol: str = Field(min_length=1)
    source_proposal_id: str = Field(min_length=1)
    counterfactual_method: str = Field(min_length=1)
    counterfactual_method_version: str = Field(min_length=1)
    assumptions: tuple[str, ...] = Field(min_length=1)
    confidence: FiniteFloat = Field(ge=0.0, le=1.0)
    simulated_outcome: FiniteFloat


type Experience = Annotated[
    DecisionExperience
    | TradeExperience
    | RejectedDecisionExperience
    | PositionManagementExperience
    | RuntimeAnomalyExperience
    | AgentContributionExperience
    | CounterfactualExperience,
    Field(discriminator="experience_type"),
]


EXPERIENCE_MODELS: dict[ExperienceType, type[ExperienceBase]] = {
    ExperienceType.DECISION: DecisionExperience,
    ExperienceType.TRADE: TradeExperience,
    ExperienceType.REJECTED_DECISION: RejectedDecisionExperience,
    ExperienceType.POSITION_MANAGEMENT: PositionManagementExperience,
    ExperienceType.RUNTIME_ANOMALY: RuntimeAnomalyExperience,
    ExperienceType.AGENT_CONTRIBUTION: AgentContributionExperience,
    ExperienceType.COUNTERFACTUAL: CounterfactualExperience,
}
