"""Strict orchestration-only contracts for the shared Phase 7 runtime."""

from __future__ import annotations

from collections import Counter
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.discipline import DisciplineOutcome
from axq.execution_boundary import ExecutionIntent
from axq.master import MasterProposal
from axq.position_actions import PositionActionIntent, PositionActionSafetyOutcome
from axq.position_management import PositionManagementOutcome
from axq.risk_boundary import RiskOutcome
from axq.runtime import ComponentFreshness, RuntimeEventType
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class RuntimeMode(StrEnum):
    DISABLED = "DISABLED"
    REPLAY = "REPLAY"
    SHADOW = "SHADOW"
    DEMO = "DEMO"


class StartupPhase(StrEnum):
    CREATED = "CREATED"
    OPENING_STORES = "OPENING_STORES"
    RESTORING = "RESTORING"
    CONNECTING = "CONNECTING"
    SNAPSHOTTING = "SNAPSHOTTING"
    RECONCILING = "RECONCILING"
    VALIDATING = "VALIDATING"
    SAFE = "SAFE"
    BLOCKED = "BLOCKED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class OperatorControls(BaseModel):
    """Monotonic operator gates: callers cannot use this contract to bypass safety."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    pause_new_entries: bool = False
    execution_disabled: bool = False
    kill_switch: bool = False
    shutdown_requested: bool = False
    reason_codes: tuple[str, ...] = ()

    def _tighten(self, reason: str, **updates: bool) -> OperatorControls:
        reasons = tuple(dict.fromkeys((*self.reason_codes, reason)))
        return self.model_copy(update=updates | {"reason_codes": reasons})

    def pause(self, reason: str) -> OperatorControls:
        return self._tighten(reason, pause_new_entries=True)

    def disable_execution(self, reason: str) -> OperatorControls:
        return self._tighten(reason, execution_disabled=True)

    def activate_kill_switch(self, reason: str) -> OperatorControls:
        return self._tighten(
            reason,
            pause_new_entries=True,
            execution_disabled=True,
            kill_switch=True,
        )

    def request_shutdown(self, reason: str) -> OperatorControls:
        return self._tighten(reason, pause_new_entries=True, shutdown_requested=True)

    def clear_kill_switch(self) -> OperatorControls:
        raise ValueError("kill switch cannot be cleared through runtime orchestration")


class RuntimeStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    status_id: str = ""
    mode: RuntimeMode
    startup_phase: StartupPhase
    as_of: UTCDateTime
    accepting_events: bool
    safe_to_process_new_trades: bool
    resume_status: str | None = None
    current_event_id: str | None = None
    current_thesis_state_id: str | None = None
    current_scenario_state_ids: tuple[str, ...] = ()
    latest_master_proposal_id: str | None = None
    latest_discipline_outcome_id: str | None = None
    latest_risk_outcome_id: str | None = None
    latest_execution_result_id: str | None = None
    open_position_count: int = Field(default=0, ge=0)
    component_freshness: tuple[ComponentFreshness, ...] = ()
    last_error: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def bind_identity(self) -> RuntimeStatus:
        if self.safe_to_process_new_trades and self.startup_phase is not StartupPhase.SAFE:
            raise ValueError("new trades require SAFE startup phase")
        identity = self.model_dump(mode="json", exclude={"status_id"})
        expected = f"rts-{canonical_hash(identity)[:20]}"
        if self.status_id and self.status_id != expected:
            raise ValueError("status_id does not match runtime status content")
        object.__setattr__(self, "status_id", expected)
        return self


class DecisionPlan(BaseModel):
    """Existing semantic outputs assembled by an injected decision-cycle processor."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    master: MasterProposal | None = None
    discipline: DisciplineOutcome | None = None
    risk: RiskOutcome | None = None
    execution_intent: ExecutionIntent | None = None
    position_management: tuple[PositionManagementOutcome, ...] = ()
    position_action_safety: tuple[PositionActionSafetyOutcome, ...] = ()
    position_action_intents: tuple[PositionActionIntent, ...] = ()
    interaction_resolution_id: str | None = None


class DecisionCycle(BaseModel):
    """Auditable classifications emitted by the existing decision boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    cycle_id: str = ""
    event_id: str = Field(min_length=1)
    event_type: RuntimeEventType
    available_at: UTCDateTime
    master_result: str | None = None
    discipline_result: str | None = None
    risk_result: str | None = None
    execution_intent_ids: tuple[str, ...] = ()
    execution_result_ids: tuple[str, ...] = ()
    position_management_actions: tuple[str, ...] = ()
    position_action_intent_ids: tuple[str, ...] = ()
    position_action_result_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def bind_identity(self) -> DecisionCycle:
        identity = self.model_dump(mode="json", exclude={"cycle_id"})
        expected = f"cycle-{canonical_hash(identity)[:20]}"
        if self.cycle_id and self.cycle_id != expected:
            raise ValueError("cycle_id does not match decision cycle content")
        object.__setattr__(self, "cycle_id", expected)
        return self


class OutcomeCount(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(min_length=1)
    count: int = Field(gt=0)


class RuntimeRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    summary_id: str = ""
    cycle_ids: tuple[str, ...]
    master_counts: tuple[OutcomeCount, ...]
    discipline_counts: tuple[OutcomeCount, ...]
    risk_counts: tuple[OutcomeCount, ...]
    execution_intent_count: int = Field(ge=0)
    execution_result_count: int = Field(ge=0)
    position_management_counts: tuple[OutcomeCount, ...]
    position_action_intent_count: int = Field(ge=0)
    position_action_result_count: int = Field(ge=0)

    @classmethod
    def from_cycles(cls, cycles: tuple[DecisionCycle, ...]) -> RuntimeRunSummary:
        def counts(values: list[str]) -> tuple[OutcomeCount, ...]:
            return tuple(
                OutcomeCount(name=name, count=count)
                for name, count in sorted(Counter(values).items())
            )

        return cls(
            cycle_ids=tuple(item.cycle_id for item in cycles),
            master_counts=counts([item.master_result for item in cycles if item.master_result]),
            discipline_counts=counts(
                [item.discipline_result for item in cycles if item.discipline_result]
            ),
            risk_counts=counts([item.risk_result for item in cycles if item.risk_result]),
            execution_intent_count=sum(len(item.execution_intent_ids) for item in cycles),
            execution_result_count=sum(len(item.execution_result_ids) for item in cycles),
            position_management_counts=counts(
                [value for item in cycles for value in item.position_management_actions]
            ),
            position_action_intent_count=sum(
                len(item.position_action_intent_ids) for item in cycles
            ),
            position_action_result_count=sum(
                len(item.position_action_result_ids) for item in cycles
            ),
        )

    @model_validator(mode="after")
    def bind_identity(self) -> RuntimeRunSummary:
        identity = self.model_dump(mode="json", exclude={"summary_id"})
        expected = f"rrs-{canonical_hash(identity)[:20]}"
        if self.summary_id and self.summary_id != expected:
            raise ValueError("summary_id does not match run summary content")
        object.__setattr__(self, "summary_id", expected)
        return self
