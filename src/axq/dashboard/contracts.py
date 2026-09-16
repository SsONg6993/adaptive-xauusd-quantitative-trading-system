"""Typed read-only projections for the local operator dashboard."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from axq.discipline.contracts import DisciplineOutcome
from axq.execution_boundary.contracts import ExecutionIntent
from axq.interaction.contracts import (
    MasterConflictAssessment,
    SpecialistInteractionResolution,
    SpecialistInteractionRound,
    SpecialistInteractionTurn,
)
from axq.master.contracts import MasterProposal
from axq.mt5.symbols import ResolvedBrokerInstrument
from axq.reasoning.contracts import (
    LLMExecutionAttemptAudit,
    LLMRequestEnvelope,
    LLMStructuredResponseArtifact,
)
from axq.risk_boundary.contracts import RiskOutcome
from axq.runtime.journal import DecodedShadowRuntimeCycle
from axq.runtime.kernel import EvidenceBundle
from axq.runtime.shadow import (
    HypotheticalTradePlan,
    M5CandidateScan,
    M15ContextSnapshot,
    ShadowMarketAvailability,
)
from axq.runtime.state import SharedRuntimeState


class DashboardModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ComponentState(StrEnum):
    AVAILABLE = "AVAILABLE"
    ONLINE = "ONLINE"
    STALE = "STALE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class ComponentStatus(DashboardModel):
    component: str = Field(min_length=1)
    state: ComponentState
    detail: str = Field(min_length=1, max_length=500)
    source_path: str | None = None
    as_of: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class ReasoningAttemptView(DashboardModel):
    attempt: LLMExecutionAttemptAudit
    request: LLMRequestEnvelope
    response: LLMStructuredResponseArtifact | None = None


class ReasoningSnapshot(DashboardModel):
    component: ComponentStatus
    attempts: tuple[ReasoningAttemptView, ...] = ()


class RuntimeSnapshot(DashboardModel):
    component: ComponentStatus
    state: SharedRuntimeState | None = None
    latest_master: MasterProposal | None = None
    latest_evidence_bundle: EvidenceBundle | None = None
    latest_discipline: DisciplineOutcome | None = None
    latest_risk: RiskOutcome | None = None
    latest_execution_intent: ExecutionIntent | None = None
    latest_m15_context: M15ContextSnapshot | None = None
    latest_candidate_scan: M5CandidateScan | None = None
    latest_shadow_cycle: DecodedShadowRuntimeCycle | None = None
    latest_trade_plan: HypotheticalTradePlan | None = None
    instrument_resolution: ResolvedBrokerInstrument | None = None
    market_availability: ShadowMarketAvailability | None = None
    latest_interaction_assessment: MasterConflictAssessment | None = None
    latest_interaction_round: SpecialistInteractionRound | None = None
    latest_interaction_turns: tuple[SpecialistInteractionTurn, ...] = ()
    latest_interaction_resolution: SpecialistInteractionResolution | None = None


class PerformanceSnapshot(DashboardModel):
    component: ComponentStatus
    artifact_id: str | None = None
    range_start: str | None = None
    range_end: str | None = None
    rows: int | None = Field(default=None, ge=0)
    decision_cycles: int | None = Field(default=None, ge=0)
    completed_trades: int | None = Field(default=None, ge=0)
    realized_pnl: float | None = None
    win_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    average_r: float | None = None
    expectancy_usd: float | None = None
    profit_factor: float | None = Field(default=None, ge=0.0)
    max_drawdown: float | None = Field(default=None, ge=0.0)
    long_trades: int | None = Field(default=None, ge=0)
    short_trades: int | None = Field(default=None, ge=0)
    equity_curve: tuple[float, ...] | None = None


__all__ = [
    "ComponentState",
    "ComponentStatus",
    "DashboardModel",
    "PerformanceSnapshot",
    "ReasoningAttemptView",
    "ReasoningSnapshot",
    "RuntimeSnapshot",
]
