"""Shared deterministic specialist-evidence kernel for live and replay."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.agents import (
    AgentEvidence,
    AgentInput,
    AgentMemory,
    ChartAgent,
    HistoricalSimilarityAgent,
    MarketRegimeAgent,
    NewsMacroAgent,
    QuantitativeAgent,
    SpecialistAgent,
)
from axq.runtime.events import RuntimeEvent
from axq.runtime.reducer import reduce_state
from axq.runtime.state import SharedRuntimeState, UTCDateTime
from axq.tools import CausalFeatureSnapshot, ToolCatalog, ToolInput
from axq.versioning import canonical_hash

AGENT_ORDER = ("chart", "quant", "historical", "regime", "news")


class EvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    bundle_id: str = ""
    event_id: str = Field(min_length=1)
    runtime_state_id: str = Field(min_length=1)
    as_of: UTCDateTime
    agent_inputs: tuple[AgentInput, ...]
    evidence: tuple[AgentEvidence, ...]
    memories: tuple[AgentMemory, ...]

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> EvidenceBundle:
        input_ids = tuple(item.runtime_state_id for item in self.agent_inputs)
        evidence_agents = tuple(item.agent_name for item in self.evidence)
        memory_agents = tuple(item.agent_name for item in self.memories)
        if not (
            len(self.agent_inputs) == len(self.evidence) == len(self.memories)
            and evidence_agents == memory_agents
        ):
            raise ValueError("bundle agent inputs, evidence, and memories must align")
        if evidence_agents != AGENT_ORDER:
            raise ValueError("bundle specialists must use canonical agent order")
        if any(value != self.runtime_state_id for value in input_ids):
            raise ValueError("bundle input references a different runtime state")
        if any(item.runtime_state_id != self.runtime_state_id for item in self.evidence):
            raise ValueError("bundle evidence references a different runtime state")
        identity = self.model_dump(mode="json", exclude={"bundle_id"})
        expected = f"eb-{canonical_hash(identity)[:20]}"
        if self.bundle_id and self.bundle_id != expected:
            raise ValueError("bundle_id does not match evidence content")
        object.__setattr__(self, "bundle_id", expected)
        return self

    def by_agent(self, agent_name: str) -> AgentEvidence:
        return self.evidence[self._agent_index(agent_name)]

    def input_for(self, agent_name: str) -> AgentInput:
        return self.agent_inputs[self._agent_index(agent_name)]

    def memory_for(self, agent_name: str) -> AgentMemory:
        return self.memories[self._agent_index(agent_name)]

    def _agent_index(self, agent_name: str) -> int:
        for index, item in enumerate(self.evidence):
            if item.agent_name == agent_name:
                return index
        raise KeyError(agent_name)


class EvidenceKernel:
    """Reduce an event, resolve bounded facts, and update specialists in fixed order."""

    def __init__(
        self,
        *,
        initial_state: SharedRuntimeState,
        catalog: ToolCatalog,
        tool_access: Mapping[str, tuple[str, ...]],
        agents: tuple[SpecialistAgent, ...] | None = None,
    ) -> None:
        configured = agents or (
            ChartAgent(),
            QuantitativeAgent(),
            HistoricalSimilarityAgent(),
            MarketRegimeAgent(),
            NewsMacroAgent(),
        )
        by_name = {agent.name: agent for agent in configured}
        if set(by_name) != set(AGENT_ORDER) or len(by_name) != len(configured):
            raise ValueError("kernel requires exactly one of each specialist agent")
        if set(tool_access) != set(AGENT_ORDER):
            raise ValueError("tool access must be explicit for every specialist")
        catalog_names = set(catalog.names())
        unknown = {
            name
            for names in tool_access.values()
            for name in names
            if name not in catalog_names
        }
        if unknown:
            raise ValueError(f"tool access references unknown tools: {sorted(unknown)}")
        self._state = initial_state
        self._catalog = catalog
        self._tool_access = {
            name: tuple(tool_access[name]) for name in AGENT_ORDER
        }
        self._agents = tuple(by_name[name] for name in AGENT_ORDER)
        self._memories: dict[str, AgentMemory] = {}
        self._last_processed: tuple[str, str | None, EvidenceBundle] | None = None

    @property
    def state(self) -> SharedRuntimeState:
        return self._state

    def process(
        self,
        event: RuntimeEvent,
        *,
        feature_snapshot: CausalFeatureSnapshot | None = None,
    ) -> EvidenceBundle:
        snapshot_id = (
            feature_snapshot.snapshot_id if feature_snapshot is not None else None
        )
        processed = self._last_processed
        if processed is not None and processed[0] == event.event_id:
            _, previous_snapshot_id, previous_bundle = processed
            if previous_snapshot_id != snapshot_id:
                raise ValueError("duplicate event has a different feature snapshot")
            return previous_bundle
        state = reduce_state(self._state, event, now=event.available_at)
        tool_input = ToolInput(state=state, feature_snapshot=feature_snapshot)
        inputs: list[AgentInput] = []
        evidence_items: list[AgentEvidence] = []
        memories: list[AgentMemory] = []
        for agent in self._agents:
            results = self._catalog.evaluate(self._tool_access[agent.name], tool_input)
            agent_input = AgentInput.from_runtime(
                state=state,
                feature_snapshot_id=(
                    feature_snapshot.snapshot_id if feature_snapshot is not None else None
                ),
                tool_results=results,
                previous_memory=self._memories.get(agent.name),
            )
            evidence, memory = agent.observe(agent_input)
            inputs.append(agent_input)
            evidence_items.append(evidence)
            memories.append(memory)
        bundle = EvidenceBundle(
            event_id=event.event_id,
            runtime_state_id=state.state_id,
            as_of=state.as_of,
            agent_inputs=tuple(inputs),
            evidence=tuple(evidence_items),
            memories=tuple(memories),
        )
        self._state = state
        self._memories = {
            memory.agent_name: memory for memory in bundle.memories
        }
        self._last_processed = (event.event_id, snapshot_id, bundle)
        return bundle
