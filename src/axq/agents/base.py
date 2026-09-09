"""Small shared specialist input and output-validation boundary."""

from __future__ import annotations

from typing import Protocol

from pydantic import Field, model_validator

from axq.agents.contracts import AgentEvidence, AgentModel, AgentStatus, ToolResultReference
from axq.agents.state import AgentMemory, transition_memory
from axq.runtime import SharedRuntimeState
from axq.runtime.state import UTCDateTime
from axq.tools import ToolResult, ToolStatus
from axq.versioning import canonical_hash


class AgentReasoningBudget(AgentModel):
    latency_budget_ms: int = Field(gt=0)
    timeout_ms: int = Field(gt=0)
    token_budget: int | None = Field(default=None, gt=0)
    output_character_budget: int = Field(gt=0)

    @model_validator(mode="after")
    def timeout_within_latency(self) -> AgentReasoningBudget:
        if self.timeout_ms > self.latency_budget_ms:
            raise ValueError("reasoning timeout cannot exceed latency budget")
        return self


class AgentInput(AgentModel):
    input_id: str = ""
    runtime_state_id: str = Field(min_length=1)
    feature_snapshot_id: str | None = None
    as_of: UTCDateTime
    tool_results: tuple[ToolResult, ...]
    previous_memory: AgentMemory | None = None
    setup_id: str | None = None
    thesis_id: str | None = None
    reasoning_budget: AgentReasoningBudget | None = None

    @classmethod
    def from_runtime(
        cls,
        *,
        state: SharedRuntimeState,
        feature_snapshot_id: str | None,
        tool_results: tuple[ToolResult, ...],
        previous_memory: AgentMemory | None,
        setup_id: str | None = None,
        thesis_id: str | None = None,
        reasoning_budget: AgentReasoningBudget | None = None,
    ) -> AgentInput:
        return cls(
            runtime_state_id=state.state_id,
            feature_snapshot_id=feature_snapshot_id,
            as_of=state.as_of,
            tool_results=tool_results,
            previous_memory=previous_memory,
            setup_id=setup_id,
            thesis_id=thesis_id,
            reasoning_budget=reasoning_budget,
        )

    @model_validator(mode="after")
    def validate_bindings_and_identity(self) -> AgentInput:
        valid_snapshots = {self.runtime_state_id, self.feature_snapshot_id}
        for result in self.tool_results:
            if result.runtime_state_id != self.runtime_state_id:
                raise ValueError("tool result runtime state does not match agent input")
            if result.input_snapshot_id not in valid_snapshots:
                raise ValueError("tool result snapshot does not match agent input")
            if result.available_at > self.as_of:
                raise ValueError("tool result is not yet available to agent input")
        ids = [result.result_id for result in self.tool_results]
        if len(ids) != len(set(ids)):
            raise ValueError("agent input cannot contain duplicate tool results")
        identity = self.model_dump(mode="json", exclude={"input_id"})
        expected = f"ai-{canonical_hash(identity)[:20]}"
        if self.input_id and self.input_id != expected:
            raise ValueError("input_id does not match agent input content")
        object.__setattr__(self, "input_id", expected)
        return self

    @property
    def tool_health_status(self) -> AgentStatus:
        statuses = {result.status for result in self.tool_results}
        if ToolStatus.ERROR in statuses:
            return AgentStatus.ERROR
        if statuses & {ToolStatus.UNAVAILABLE, ToolStatus.INSUFFICIENT_DATA}:
            return AgentStatus.ABSTAINED
        if ToolStatus.STALE in statuses:
            return AgentStatus.DEGRADED
        return AgentStatus.READY


class SpecialistAgent(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def observe(self, agent_input: AgentInput) -> tuple[AgentEvidence, AgentMemory]:
        """Interpret supplied facts without recomputing tools or authorizing execution."""


def validate_agent_output(agent_input: AgentInput, evidence: AgentEvidence) -> None:
    """Verify evidence references exact causal tool facts from its input."""
    if evidence.runtime_state_id != agent_input.runtime_state_id:
        raise ValueError("agent evidence runtime state does not match input")
    if evidence.feature_snapshot_id != agent_input.feature_snapshot_id:
        raise ValueError("agent evidence feature snapshot does not match input")
    if evidence.available_at > agent_input.as_of:
        raise ValueError("agent evidence is not yet causally available")
    results = {result.result_id: result for result in agent_input.tool_results}
    for reference in evidence.tool_inputs:
        result = results.get(reference.tool_result_id)
        if result is None or ToolResultReference.from_result(result) != reference:
            raise ValueError("agent evidence references an unknown or altered tool result")
    for item in evidence.evidence_for + evidence.evidence_against:
        result = results.get(item.tool_result_id)
        if result is None or result.tool_name != item.tool_name:
            raise ValueError("agent evidence references an unknown tool result")
        fact = next((fact for fact in result.facts if fact.name == item.fact_name), None)
        if fact is None:
            raise ValueError("agent evidence references an unknown fact")
        if fact.value != item.fact_value:
            raise ValueError("agent evidence fact value does not match tool result")
        if result.freshness is not item.freshness:
            raise ValueError("agent evidence freshness does not match tool result")
        if result.quality.valid is not item.quality_valid:
            raise ValueError("agent evidence quality does not match tool result")


def transition_agent(
    agent_input: AgentInput,
    evidence: AgentEvidence,
) -> AgentMemory:
    """Validate an agent output before applying its deterministic memory transition."""
    validate_agent_output(agent_input, evidence)
    return transition_memory(agent_input.previous_memory, evidence)
