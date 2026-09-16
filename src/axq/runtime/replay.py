"""One shared event-stream harness for live-like and replay adapters."""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterator, Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.agents import AgentMemory, EntryEligibility, ThesisState
from axq.runtime.clock import ReplayClock, RuntimeClock
from axq.runtime.events import RuntimeEvent
from axq.runtime.journal import (
    JournalOutcome,
    JournalOutcomeStatus,
    JournalRecord,
    JournalRecordType,
    JournalSemantic,
    RuntimeJournal,
    SQLiteRuntimeJournal,
)
from axq.runtime.kernel import EvidenceBundle, EvidenceKernel, KernelPerformance
from axq.runtime.source import EventSource
from axq.runtime.state import SharedRuntimeState, UTCDateTime
from axq.tools import CausalFeatureSnapshot, ToolResult
from axq.versioning import canonical_hash

ScenarioTransition = Callable[
    [RuntimeEvent, EvidenceBundle, ThesisState | None],
    ThesisState | None,
]


class SemanticTraceStep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    step_id: str = ""
    event_id: str = Field(min_length=1)
    available_at: UTCDateTime
    runtime_state_id: str = Field(min_length=1)
    tool_result_ids: tuple[str, ...]
    agent_input_ids: tuple[str, ...]
    agent_evidence_ids: tuple[str, ...]
    agent_memory_ids: tuple[str, ...]
    bundle_id: str = Field(min_length=1)
    thesis_state_id: str | None = None
    scenario_state_ids: tuple[str, ...] = ()
    entry_eligibility: EntryEligibility | None = None
    bundle: EvidenceBundle

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> SemanticTraceStep:
        if self.bundle.bundle_id != self.bundle_id:
            raise ValueError("trace bundle ID does not match bundle")
        if self.bundle.runtime_state_id != self.runtime_state_id:
            raise ValueError("trace runtime state ID does not match bundle")
        identity = self.model_dump(mode="json", exclude={"step_id"})
        expected = f"step-{canonical_hash(identity)[:20]}"
        if self.step_id and self.step_id != expected:
            raise ValueError("step_id does not match trace content")
        object.__setattr__(self, "step_id", expected)
        return self


class StreamRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    steps: tuple[SemanticTraceStep, ...]


class JournalEventSource:
    """Canonical event source reconstructed from append-only journal records."""

    def __init__(self, journal: SQLiteRuntimeJournal) -> None:
        self._journal = journal

    def events(self) -> Iterator[RuntimeEvent]:
        return self._journal.events()


def _reason_code(error: Exception) -> str:
    message = str(error).lower()
    if "different feature snapshot" in message:
        return "FEATURE_SNAPSHOT_MISMATCH"
    if "source sequence collision" in message:
        return "SOURCE_SEQUENCE_COLLISION"
    if "event order" in message or "stale source sequence" in message:
        return "OUT_OF_ORDER_EVENT"
    if "provenance" in message or "fact value" in message:
        return "PROVENANCE_MISMATCH"
    if "thesis" in message or "hypothesis" in message:
        return "SCENARIO_LINKAGE_MISMATCH"
    if "clock" in message or "not yet available" in message:
        return "INVALID_REPLAY_ORDERING"
    return "VALIDATION_ERROR"


def _tool_results(bundle: EvidenceBundle) -> tuple[ToolResult, ...]:
    values: dict[str, ToolResult] = {}
    for agent_input in bundle.agent_inputs:
        for result in agent_input.tool_results:
            values[result.result_id] = result
    return tuple(values[key] for key in sorted(values))


class RuntimeStreamRunner:
    """Feed one source/clock adapter through the unchanged shared kernel."""

    def __init__(
        self,
        kernel: EvidenceKernel,
        clock: RuntimeClock,
        *,
        journal: RuntimeJournal | None = None,
        retained_record_types: Collection[JournalRecordType] | None = None,
        scenario_transition: ScenarioTransition | None = None,
    ) -> None:
        self._kernel = kernel
        self._clock = clock
        self._journal = journal
        self._retained_record_types = (
            frozenset(retained_record_types)
            if retained_record_types is not None
            else None
        )
        self._scenario_transition = scenario_transition
        self._thesis: ThesisState | None = None
        self._steps: list[SemanticTraceStep] = []
        self._last: tuple[str, str | None, SemanticTraceStep] | None = None

    @property
    def steps(self) -> tuple[SemanticTraceStep, ...]:
        return tuple(self._steps)

    @property
    def state(self) -> SharedRuntimeState:
        """Expose the immutable current state for orchestration and diagnostics."""
        return self._kernel.state

    @property
    def thesis(self) -> ThesisState | None:
        return self._thesis

    @property
    def last_kernel_performance(self) -> KernelPerformance:
        return self._kernel.last_performance

    def restore_thesis(self, thesis: ThesisState) -> None:
        """Restore durable thesis continuity before accepting a new event."""
        if self._steps or self._last is not None:
            raise RuntimeError("thesis restoration is only valid before event processing")
        self._thesis = thesis

    def restore_runtime(
        self,
        state: SharedRuntimeState,
        memories: tuple[AgentMemory, ...] = (),
    ) -> None:
        """Restore reducer cursors and specialist memory before event intake."""
        if self._steps or self._last is not None:
            raise RuntimeError("runtime restoration is only valid before event processing")
        self._kernel.restore(state, memories)

    def _advance_clock(self, event: RuntimeEvent) -> None:
        if isinstance(self._clock, ReplayClock):
            self._clock.advance_to(event.available_at)
        elif self._clock.now() < event.available_at:
            raise ValueError("event is not yet available on the injected clock")

    def _append_outcome(
        self,
        event: RuntimeEvent,
        status: JournalOutcomeStatus,
        reason_code: str,
        message: str,
    ) -> None:
        if self._journal is None or not self._retains(JournalRecordType.OUTCOME):
            return
        outcome = JournalOutcome(
            status=status,
            reason_code=reason_code,
            message=message,
        )
        if isinstance(self._journal, SQLiteRuntimeJournal):
            self._journal.append_outcome(event, outcome)
        else:
            self._journal.append(self._outcome_record(event, outcome))

    def _retains(self, record_type: JournalRecordType) -> bool:
        return (
            self._retained_record_types is None
            or record_type in self._retained_record_types
        )

    def _append_record(self, record: JournalRecord) -> None:
        if self._journal is not None and self._retains(record.record_type):
            self._journal.append(record)

    @staticmethod
    def _outcome_record(
        event: RuntimeEvent,
        outcome: JournalOutcome,
    ) -> JournalRecord:
        return JournalRecord.from_semantic(
            outcome,
            event_id=event.event_id,
            parent_id=event.event_id,
            available_at=event.available_at,
        )

    def process(
        self,
        event: RuntimeEvent,
        feature_snapshot: CausalFeatureSnapshot | None,
    ) -> SemanticTraceStep:
        snapshot_id = (
            feature_snapshot.snapshot_id if feature_snapshot is not None else None
        )
        last = self._last
        try:
            self._advance_clock(event)
            if last is not None and last[0] == event.event_id:
                _, previous_snapshot_id, previous_step = last
                if previous_snapshot_id != snapshot_id:
                    raise ValueError("duplicate event has a different feature snapshot")
                duplicate_bundle = self._kernel.process(
                    event,
                    feature_snapshot=feature_snapshot,
                )
                if duplicate_bundle.bundle_id != previous_step.bundle_id:
                    raise ValueError("duplicate event changed semantic bundle identity")
                self._append_outcome(
                    event,
                    JournalOutcomeStatus.DUPLICATE,
                    "DUPLICATE_EVENT",
                    "exact event and feature snapshot were already processed",
                )
                return previous_step

            previous_state_id = self._kernel.state.state_id
            previous_thesis = self._thesis
            previous_memories = {
                item.agent_name: item for item in self._steps[-1].bundle.memories
            } if self._steps else {}
            if self._journal is not None:
                self._append_record(
                    self._semantic_record(event, event.event_id)
                )
                if feature_snapshot is not None:
                    self._append_record(
                        self._semantic_record(
                            feature_snapshot,
                            event.event_id,
                            parent_id=event.event_id,
                        )
                    )
            bundle = self._kernel.process(event, feature_snapshot=feature_snapshot)
            thesis = (
                self._scenario_transition(event, bundle, self._thesis)
                if self._scenario_transition is not None
                else self._thesis
            )
            step = SemanticTraceStep(
                event_id=event.event_id,
                available_at=event.available_at,
                runtime_state_id=self._kernel.state.state_id,
                tool_result_ids=tuple(item.result_id for item in _tool_results(bundle)),
                agent_input_ids=tuple(item.input_id for item in bundle.agent_inputs),
                agent_evidence_ids=tuple(item.evidence_id for item in bundle.evidence),
                agent_memory_ids=tuple(item.memory_id for item in bundle.memories),
                bundle_id=bundle.bundle_id,
                thesis_state_id=thesis.state_id if thesis is not None else None,
                scenario_state_ids=(
                    tuple(item.state_id for item in thesis.scenarios)
                    if thesis is not None
                    else ()
                ),
                entry_eligibility=(
                    thesis.entry_eligibility if thesis is not None else None
                ),
                bundle=bundle,
            )
            if self._journal is not None:
                self._journal_semantics(
                    event,
                    feature_snapshot,
                    bundle,
                    thesis,
                    previous_state_id,
                    previous_memories,
                    previous_thesis,
                )
                self._append_outcome(
                    event,
                    JournalOutcomeStatus.APPLIED,
                    "APPLIED",
                    "event produced one deterministic semantic trace step",
                )
            self._thesis = thesis
            self._steps.append(step)
            self._last = (event.event_id, snapshot_id, step)
            return step
        except Exception as error:
            self._append_outcome(
                event,
                JournalOutcomeStatus.REJECTED,
                _reason_code(error),
                str(error) or type(error).__name__,
            )
            raise

    def reduce_only(self, event: RuntimeEvent) -> SharedRuntimeState:
        """Apply a state refresh while preserving specialist memory unchanged."""
        self._advance_clock(event)
        return self._kernel.reduce_event(event)

    def reduce_broker_refresh(self, event: RuntimeEvent) -> SharedRuntimeState:
        """Journal and reduce a broker snapshot fact without semantic evaluation."""
        self._advance_clock(event)
        self._append_record(self._semantic_record(event, event.event_id))
        previous_state_id = self._kernel.state.state_id
        try:
            state = self._kernel.reduce_broker_refresh_event(event)
        except Exception as error:
            self._append_outcome(
                event,
                JournalOutcomeStatus.REJECTED,
                _reason_code(error),
                str(error) or type(error).__name__,
            )
            raise
        self._append_record(
            self._semantic_record(
                state,
                event.event_id,
                parent_id=event.event_id,
                previous_id=previous_state_id,
            )
        )
        self._append_outcome(
            event,
            JournalOutcomeStatus.APPLIED,
            "BROKER_REFRESH_APPLIED",
            "broker snapshot fact advanced state without semantic evaluation",
        )
        return state

    @staticmethod
    def _semantic_record(
        value: JournalSemantic,
        event_id: str,
        *,
        parent_id: str | None = None,
        previous_id: str | None = None,
    ) -> JournalRecord:
        return JournalRecord.from_semantic(
            value,
            event_id=event_id,
            parent_id=parent_id,
            previous_id=previous_id,
        )

    def _journal_semantics(
        self,
        event: RuntimeEvent,
        feature_snapshot: CausalFeatureSnapshot | None,
        bundle: EvidenceBundle,
        thesis: ThesisState | None,
        previous_state_id: str,
        previous_memories: Mapping[str, AgentMemory],
        previous_thesis: ThesisState | None,
    ) -> None:
        if self._journal is None:
            return
        self._append_record(
            self._semantic_record(
                self._kernel.state,
                event.event_id,
                parent_id=event.event_id,
                previous_id=previous_state_id,
            )
        )
        snapshot_parent = (
            feature_snapshot.snapshot_id
            if feature_snapshot is not None
            else self._kernel.state.state_id
        )
        for result in _tool_results(bundle):
            self._append_record(
                self._semantic_record(
                    result,
                    event.event_id,
                    parent_id=snapshot_parent,
                )
            )
        for agent_input, evidence, memory in zip(
            bundle.agent_inputs,
            bundle.evidence,
            bundle.memories,
            strict=True,
        ):
            self._append_record(
                self._semantic_record(
                    agent_input,
                    event.event_id,
                    parent_id=self._kernel.state.state_id,
                )
            )
            self._append_record(
                self._semantic_record(
                    evidence,
                    event.event_id,
                    parent_id=agent_input.input_id,
                )
            )
            previous_memory = previous_memories.get(memory.agent_name)
            self._append_record(
                self._semantic_record(
                    memory,
                    event.event_id,
                    parent_id=evidence.evidence_id,
                    previous_id=(
                        previous_memory.memory_id
                        if previous_memory is not None
                        else None
                    ),
                )
            )
        self._append_record(
            self._semantic_record(
                bundle,
                event.event_id,
                parent_id=event.event_id,
            )
        )
        if thesis is not None:
            self._append_record(
                self._semantic_record(
                    thesis,
                    event.event_id,
                    parent_id=bundle.bundle_id,
                    previous_id=(
                        previous_thesis.state_id
                        if previous_thesis is not None
                        else None
                    ),
                )
            )
            previous_scenarios = (
                {item.scenario_id: item for item in previous_thesis.scenarios}
                if previous_thesis is not None
                else {}
            )
            for scenario in thesis.scenarios:
                previous_scenario = previous_scenarios.get(scenario.scenario_id)
                self._append_record(
                    self._semantic_record(
                        scenario,
                        event.event_id,
                        parent_id=thesis.state_id,
                        previous_id=(
                            previous_scenario.state_id
                            if previous_scenario is not None
                            else None
                        ),
                    )
                )


def run_event_stream(
    source: EventSource,
    kernel: EvidenceKernel,
    clock: RuntimeClock,
    *,
    snapshots: Mapping[str, CausalFeatureSnapshot] | None = None,
    journal: RuntimeJournal | None = None,
    scenario_transition: ScenarioTransition | None = None,
) -> StreamRun:
    """Run an adapter-provided stream through the one shared semantic path."""
    runner = RuntimeStreamRunner(
        kernel,
        clock,
        journal=journal,
        scenario_transition=scenario_transition,
    )
    available_snapshots = snapshots or {}
    for event in source.events():
        runner.process(event, available_snapshots.get(event.event_id))
    return StreamRun(steps=runner.steps)
