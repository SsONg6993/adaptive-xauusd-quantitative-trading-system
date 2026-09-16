"""Concrete composition of existing deterministic Phase 7 decision boundaries."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from pydantic import BaseModel, ConfigDict

from axq.discipline import (
    DisciplineContext,
    DisciplinePolicy,
    DisciplineState,
    evaluate_discipline,
)
from axq.execution_boundary import ExecutionPolicy, ResumeReadiness, build_execution_intent
from axq.master import FusionPolicy, fuse_evidence
from axq.orchestration.contracts import DecisionPlan, OperatorControls
from axq.position_actions import (
    PositionActionContext,
    PositionActionPolicy,
    build_position_action_intent,
    evaluate_position_action_safety,
)
from axq.position_management import (
    PositionManagementContext,
    PositionManagementOutcome,
    PositionManagementPolicy,
    evaluate_position,
)
from axq.risk_boundary import RiskContext, RiskPolicy, evaluate_risk
from axq.runtime import RuntimeEvent, SharedRuntimeState
from axq.runtime.replay import SemanticTraceStep


class EntryDecisionInputs(BaseModel):
    """Causal contexts supplied by the runtime-specific context adapter."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    discipline_context: DisciplineContext
    discipline_state: DisciplineState
    risk_context: RiskContext


EntryContextProvider = Callable[
    [RuntimeEvent, SharedRuntimeState, SemanticTraceStep], EntryDecisionInputs
]
PositionContextProvider = Callable[
    [RuntimeEvent, SharedRuntimeState, SemanticTraceStep],
    tuple[PositionManagementContext, ...],
]
PositionActionContextProvider = Callable[
    [PositionManagementOutcome, SharedRuntimeState, ResumeReadiness | None],
    PositionActionContext,
]


class DeterministicDecisionProcessor:
    """Invoke Master → Discipline → Risk and existing-position boundaries in fixed order."""

    def __init__(
        self,
        *,
        fusion_policy: FusionPolicy,
        discipline_policy: DisciplinePolicy,
        risk_policy: RiskPolicy,
        execution_policy: ExecutionPolicy,
        position_management_policy: PositionManagementPolicy,
        position_action_policy: PositionActionPolicy,
        entry_context_provider: EntryContextProvider,
        position_context_provider: PositionContextProvider,
        position_action_context_provider: PositionActionContextProvider,
    ) -> None:
        self._fusion_policy = fusion_policy
        self._discipline_policy = discipline_policy
        self._risk_policy = risk_policy
        self._execution_policy = execution_policy
        self._position_management_policy = position_management_policy
        self._position_action_policy = position_action_policy
        self._entry_context_provider = entry_context_provider
        self._position_context_provider = position_context_provider
        self._position_action_context_provider = position_action_context_provider
        self._last_master_latency_ms = 0.0

    @property
    def last_master_latency_ms(self) -> float:
        return self._last_master_latency_ms

    def evaluate(
        self,
        event: RuntimeEvent,
        state: SharedRuntimeState,
        trace: SemanticTraceStep,
        readiness: ResumeReadiness | None,
        controls: OperatorControls,
    ) -> DecisionPlan:
        """Compose existing pure functions; adapters provide causal context only."""
        master_started = perf_counter()
        proposal = fuse_evidence(trace.bundle, self._fusion_policy)
        self._last_master_latency_ms = (perf_counter() - master_started) * 1_000.0
        inputs = self._entry_context_provider(event, state, trace)
        discipline = evaluate_discipline(
            proposal,
            inputs.discipline_context,
            inputs.discipline_state,
            self._discipline_policy,
        )
        risk_context = inputs.risk_context
        if controls.kill_switch and not risk_context.kill_switch_active:
            risk_context = type(risk_context).model_validate(
                risk_context.model_dump() | {"context_id": "", "kill_switch_active": True}
            )
        risk = evaluate_risk(proposal, discipline, risk_context, self._risk_policy)
        intent = build_execution_intent(
            proposal,
            discipline,
            risk,
            risk_context,
            self._execution_policy,
        )

        management = tuple(
            evaluate_position(context, self._position_management_policy)
            for context in self._position_context_provider(event, state, trace)
        )
        safety_values = []
        action_intents = []
        for outcome in management:
            action_context = self._position_action_context_provider(outcome, state, readiness)
            safety = evaluate_position_action_safety(
                action_context,
                self._position_action_policy,
            )
            action_intent = build_position_action_intent(action_context, safety)
            safety_values.append(safety)
            if action_intent is not None:
                action_intents.append(action_intent)
        return DecisionPlan(
            master=proposal,
            discipline=discipline,
            risk=risk,
            execution_intent=intent,
            position_management=management,
            position_action_safety=tuple(safety_values),
            position_action_intents=tuple(action_intents),
        )
