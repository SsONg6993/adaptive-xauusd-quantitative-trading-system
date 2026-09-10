"""Deterministic M5 thesis and intrabar scenario lifecycle."""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum

from pydantic import Field, model_validator

from axq.agents.base import AgentInput, validate_agent_output
from axq.agents.contracts import (
    AgentEvidence,
    AgentModel,
    AgentStatus,
    DirectionalBias,
    EvidencePolarity,
    HypothesisRelationship,
    HypothesisStatus,
)
from axq.agents.state import AgentMemory, transition_memory
from axq.runtime import RuntimeEvent, RuntimeEventType
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class EntryEligibility(StrEnum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    WATCHING = "WATCHING"
    ELIGIBLE = "ELIGIBLE"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


class ScenarioStatus(StrEnum):
    WATCHING = "WATCHING"
    STRENGTHENED = "STRENGTHENED"
    WEAKENED = "WEAKENED"
    CONFIRMED = "CONFIRMED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"


class ContinuityStatus(StrEnum):
    COMPLETE = "COMPLETE"
    UNKNOWN = "UNKNOWN"
    MISSING_INTRABAR_DATA = "MISSING_INTRABAR_DATA"


class ScenarioDefinition(AgentModel):
    name: str = Field(min_length=1, max_length=100)
    confirmation_facts: tuple[str, ...] = Field(min_length=1, max_length=8)
    invalidation_facts: tuple[str, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def validate_conditions(self) -> ScenarioDefinition:
        for values in (self.confirmation_facts, self.invalidation_facts):
            if len(values) != len(set(values)):
                raise ValueError("scenario conditions must be unique")
        return self


class ScenarioPolicy(AgentModel):
    ttl_seconds: int = Field(gt=0)
    max_m5_bars: int = Field(gt=0)
    max_scenarios: int = Field(default=3, gt=0, le=3)


class ScenarioState(AgentModel):
    scenario_id: str = ""
    state_id: str = ""
    parent_thesis_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: ScenarioStatus
    confirmation_facts: tuple[str, ...]
    invalidation_facts: tuple[str, ...]
    matched_confirmation_facts: tuple[str, ...] = ()
    confirmation_progress: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    last_matched_event_id: str | None = None
    began_at: UTCDateTime
    updated_at: UTCDateTime
    expires_at: UTCDateTime
    entry_eligibility: EntryEligibility
    evidence_ids: tuple[str, ...]
    tool_result_ids: tuple[str, ...]

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ScenarioState:
        if not self.began_at <= self.updated_at <= self.expires_at:
            raise ValueError("scenario timestamps are inconsistent")
        if not set(self.matched_confirmation_facts).issubset(self.confirmation_facts):
            raise ValueError("matched facts must belong to confirmation conditions")
        if (
            self.status is ScenarioStatus.CONFIRMED
            and self.entry_eligibility is not EntryEligibility.ELIGIBLE
        ):
            raise ValueError("confirmed scenario must be eligible")
        definition_identity = {
            "thesis_id": self.parent_thesis_id,
            "definition": {
                "schema_version": self.schema_version,
                "name": self.name,
                "confirmation_facts": list(self.confirmation_facts),
                "invalidation_facts": list(self.invalidation_facts),
            },
        }
        expected_scenario_id = (
            f"scenario-root-{canonical_hash(definition_identity)[:20]}"
        )
        if self.scenario_id and self.scenario_id != expected_scenario_id:
            raise ValueError("scenario_id does not match scenario content")
        object.__setattr__(self, "scenario_id", expected_scenario_id)
        state_identity = self.model_dump(mode="json", exclude={"state_id"})
        expected_state_id = f"scenario-state-{canonical_hash(state_identity)[:20]}"
        if self.state_id and self.state_id != expected_state_id:
            raise ValueError("state_id does not match scenario state content")
        object.__setattr__(self, "state_id", expected_state_id)
        return self


class ThesisState(AgentModel):
    state_id: str = ""
    thesis_id: str = Field(min_length=1)
    supersedes_thesis_id: str | None = None
    symbol: str = Field(min_length=1)
    agent_name: str = Field(min_length=1)
    agent_version: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    direction: DirectionalBias | None = None
    hypothesis_status: HypothesisStatus
    relationship: HypothesisRelationship
    runtime_state_id: str = Field(min_length=1)
    feature_snapshot_id: str | None = None
    began_at: UTCDateTime
    updated_at: UTCDateTime
    expires_at: UTCDateTime
    m5_bars_observed: int = Field(ge=1)
    entry_eligibility: EntryEligibility
    scenarios: tuple[ScenarioState, ...] = Field(min_length=1, max_length=3)
    evidence_ids: tuple[str, ...]
    latest_evidence_id: str = Field(min_length=1)
    latest_evidence_as_of: UTCDateTime
    latest_evidence_available_at: UTCDateTime
    agent_memory: AgentMemory
    last_event_id: str = Field(min_length=1)
    last_event_time: UTCDateTime
    last_observed_at: UTCDateTime
    last_available_at: UTCDateTime
    last_source_sequence: int = Field(ge=0)
    continuity_status: ContinuityStatus = ContinuityStatus.COMPLETE

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ThesisState:
        if not self.began_at <= self.updated_at <= self.expires_at:
            raise ValueError("thesis timestamps are inconsistent")
        if self.latest_evidence_available_at > self.latest_evidence_as_of:
            raise ValueError("evidence availability cannot follow its as_of time")
        if any(item.parent_thesis_id != self.thesis_id for item in self.scenarios):
            raise ValueError("scenario is linked to a different thesis")
        if self.entry_eligibility is EntryEligibility.ELIGIBLE and not any(
            item.entry_eligibility is EntryEligibility.ELIGIBLE for item in self.scenarios
        ):
            raise ValueError("eligible thesis requires an eligible scenario")
        identity = self.model_dump(mode="json", exclude={"state_id"})
        expected = f"thesis-state-{canonical_hash(identity)[:20]}"
        if self.state_id and self.state_id != expected:
            raise ValueError("state_id does not match thesis state content")
        object.__setattr__(self, "state_id", expected)
        return self


def _thesis_id(event: RuntimeEvent, evidence: AgentEvidence) -> str:
    identity = {
        "symbol": event.symbol,
        "primary_m5_available_at": event.available_at,
        "agent_name": evidence.agent_name,
        "agent_version": evidence.agent_version,
        "hypothesis_id": evidence.hypothesis_id,
        "hypothesis": evidence.hypothesis,
        "direction": evidence.direction,
        "feature_snapshot_id": evidence.feature_snapshot_id,
    }
    return f"thesis-{canonical_hash(identity)[:20]}"


def _scenario_id(thesis_id: str, definition: ScenarioDefinition) -> str:
    identity = {
        "thesis_id": thesis_id,
        "definition": definition.model_dump(mode="json"),
    }
    return f"scenario-root-{canonical_hash(identity)[:20]}"


def _new_scenarios(
    thesis_id: str,
    definitions: tuple[ScenarioDefinition, ...],
    evidence: AgentEvidence,
    event: RuntimeEvent,
    expires_at: UTCDateTime,
) -> tuple[ScenarioState, ...]:
    result: list[ScenarioState] = []
    tool_ids = tuple(item.tool_result_id for item in evidence.tool_inputs)
    for definition in definitions:
        result.append(
            ScenarioState(
                scenario_id=_scenario_id(thesis_id, definition),
                parent_thesis_id=thesis_id,
                name=definition.name,
                status=ScenarioStatus.WATCHING,
                confirmation_facts=definition.confirmation_facts,
                invalidation_facts=definition.invalidation_facts,
                confirmation_progress=0.0,
                confidence=evidence.confidence,
                began_at=event.available_at,
                updated_at=event.available_at,
                expires_at=expires_at,
                entry_eligibility=EntryEligibility.WATCHING,
                evidence_ids=(evidence.evidence_id,),
                tool_result_ids=tool_ids,
            )
        )
    return tuple(result)


def _create_thesis(
    event: RuntimeEvent,
    evidence: AgentEvidence,
    policy: ScenarioPolicy,
    definitions: tuple[ScenarioDefinition, ...],
    previous_memory: AgentMemory | None = None,
    supersedes_thesis_id: str | None = None,
) -> ThesisState:
    if event.symbol is None:
        raise ValueError("M5 thesis event requires a symbol")
    if not definitions:
        raise ValueError("new thesis requires at least one scenario")
    if len(definitions) > policy.max_scenarios:
        raise ValueError("scenario count exceeds configured maximum")
    names = [item.name for item in definitions]
    if len(names) != len(set(names)):
        raise ValueError("scenario names must be unique")
    thesis_id = _thesis_id(event, evidence)
    memory = transition_memory(previous_memory, evidence)
    expires_at = event.available_at + timedelta(seconds=policy.ttl_seconds)
    scenarios = _new_scenarios(thesis_id, definitions, evidence, event, expires_at)
    return ThesisState(
        thesis_id=thesis_id,
        supersedes_thesis_id=supersedes_thesis_id,
        symbol=event.symbol,
        agent_name=evidence.agent_name,
        agent_version=evidence.agent_version,
        hypothesis_id=evidence.hypothesis_id,
        hypothesis=evidence.hypothesis,
        direction=evidence.direction,
        hypothesis_status=evidence.hypothesis_status,
        relationship=evidence.relationship,
        runtime_state_id=evidence.runtime_state_id,
        feature_snapshot_id=evidence.feature_snapshot_id,
        began_at=event.available_at,
        updated_at=event.available_at,
        expires_at=expires_at,
        m5_bars_observed=1,
        entry_eligibility=EntryEligibility.WATCHING,
        scenarios=scenarios,
        evidence_ids=(evidence.evidence_id,),
        latest_evidence_id=evidence.evidence_id,
        latest_evidence_as_of=evidence.as_of,
        latest_evidence_available_at=evidence.available_at,
        agent_memory=memory,
        last_event_id=event.event_id,
        last_event_time=event.event_time,
        last_observed_at=event.observed_at,
        last_available_at=event.available_at,
        last_source_sequence=event.source_sequence,
    )


def _terminal_state(
    previous: ThesisState,
    event: RuntimeEvent,
    *,
    expired: bool,
) -> ThesisState:
    status = ScenarioStatus.EXPIRED if expired else ScenarioStatus.INVALIDATED
    eligibility = EntryEligibility.EXPIRED if expired else EntryEligibility.INVALIDATED
    scenarios = tuple(
        ScenarioState.model_validate(
            item.model_dump(mode="python", exclude={"state_id"})
            | {
                "status": status,
                "updated_at": min(event.available_at, item.expires_at),
                "entry_eligibility": eligibility,
            }
        )
        for item in previous.scenarios
    )
    data = previous.model_dump(mode="python", exclude={"state_id"})
    data.update(
        {
            "hypothesis_status": (
                HypothesisStatus.EXPIRED if expired else HypothesisStatus.INVALIDATED
            ),
            "relationship": (
                HypothesisRelationship.EXPIRED
                if expired
                else HypothesisRelationship.INVALIDATED
            ),
            "updated_at": min(event.available_at, previous.expires_at),
            "entry_eligibility": eligibility,
            "scenarios": scenarios,
            "last_event_id": event.event_id,
            "last_event_time": event.event_time,
            "last_observed_at": event.observed_at,
            "last_available_at": event.available_at,
            "last_source_sequence": event.source_sequence,
        }
    )
    return ThesisState.model_validate(data)


def _updated_scenarios(
    previous: ThesisState,
    evidence: AgentEvidence,
    event: RuntimeEvent,
) -> tuple[ScenarioState, ...]:
    supporting = {
        item.fact_name
        for item in evidence.evidence_for
        if item.polarity is EvidencePolarity.SUPPORTS
    }
    tool_ids = tuple(item.tool_result_id for item in evidence.tool_inputs)
    result: list[ScenarioState] = []
    for scenario in previous.scenarios:
        invalidated = evidence.invalidation.invalidated or bool(
            supporting & set(scenario.invalidation_facts)
        )
        matched = tuple(
            sorted(set(scenario.matched_confirmation_facts) | supporting)
        )
        matched = tuple(name for name in matched if name in scenario.confirmation_facts)
        progress = len(matched) / len(scenario.confirmation_facts)
        confirmed = (
            progress == 1.0
            and evidence.hypothesis_status is HypothesisStatus.CONFIRMED
        )
        if invalidated:
            status = ScenarioStatus.INVALIDATED
            eligibility = EntryEligibility.INVALIDATED
        elif confirmed:
            status = ScenarioStatus.CONFIRMED
            eligibility = EntryEligibility.ELIGIBLE
        elif evidence.relationship is HypothesisRelationship.STRENGTHENED:
            status = ScenarioStatus.STRENGTHENED
            eligibility = EntryEligibility.WATCHING
        elif evidence.relationship is HypothesisRelationship.WEAKENED:
            status = ScenarioStatus.WEAKENED
            eligibility = EntryEligibility.WATCHING
        else:
            status = ScenarioStatus.WATCHING
            eligibility = EntryEligibility.WATCHING
        data = scenario.model_dump(mode="python", exclude={"state_id"})
        data.update(
            {
                "status": status,
                "matched_confirmation_facts": matched,
                "confirmation_progress": progress,
                "confidence": evidence.confidence,
                "last_matched_event_id": event.event_id if supporting else None,
                "updated_at": event.available_at,
                "entry_eligibility": eligibility,
                "evidence_ids": scenario.evidence_ids + (evidence.evidence_id,),
                "tool_result_ids": tuple(
                    dict.fromkeys(scenario.tool_result_ids + tool_ids)
                ),
            }
        )
        result.append(ScenarioState.model_validate(data))
    return tuple(result)


def _validate_causality(
    event: RuntimeEvent,
    agent_input: AgentInput,
    evidence: AgentEvidence,
    previous: ThesisState | None,
) -> None:
    validate_agent_output(agent_input, evidence)
    if event.available_at > agent_input.as_of:
        raise ValueError("runtime event is not yet causally available")
    if evidence.available_at < event.available_at:
        raise ValueError("agent evidence predates event availability")
    if (
        previous is not None
        and event.ordering_key
        < (
            previous.last_available_at,
            previous.last_source_sequence,
            previous.last_event_id,
        )
    ):
        raise ValueError("scenario event violates causal ordering")


def update_scenario(
    event: RuntimeEvent,
    agent_input: AgentInput,
    evidence: AgentEvidence,
    previous: ThesisState | None,
    *,
    policy: ScenarioPolicy,
    scenario_definitions: tuple[ScenarioDefinition, ...] = (),
) -> ThesisState | None:
    """Apply one M5 or intrabar evidence event without consulting a clock."""
    allowed = {
        RuntimeEventType.M5_CLOSED,
        RuntimeEventType.M1_CLOSED,
        RuntimeEventType.TICK,
    }
    if event.event_type not in allowed:
        raise ValueError("scenario state machine only accepts M5, M1, or tick events")
    if previous is None and event.event_type is not RuntimeEventType.M5_CLOSED:
        return None
    _validate_causality(event, agent_input, evidence, previous)
    if previous is None:
        if evidence.relationship is not HypothesisRelationship.NEW:
            raise ValueError("new M5 thesis requires NEW evidence")
        return _create_thesis(event, evidence, policy, scenario_definitions)
    if event.event_id == previous.last_event_id:
        return previous
    previous_is_terminal = previous.hypothesis_status in {
        HypothesisStatus.INVALIDATED,
        HypothesisStatus.EXPIRED,
    }
    previous_is_causally_expired = event.available_at >= previous.expires_at
    if event.event_type is RuntimeEventType.M5_CLOSED and (
        evidence.relationship is HypothesisRelationship.REVERSED
    ):
        if evidence.previous_hypothesis_id != previous.hypothesis_id:
            raise ValueError("reversal does not reference current thesis hypothesis")
        return _create_thesis(
            event,
            evidence,
            policy,
            scenario_definitions,
            previous_memory=previous.agent_memory,
            supersedes_thesis_id=previous.thesis_id,
        )
    if (
        event.event_type is RuntimeEventType.M5_CLOSED
        and evidence.relationship is HypothesisRelationship.NEW
        and (previous_is_terminal or previous_is_causally_expired)
    ):
        if evidence.hypothesis_id == previous.hypothesis_id:
            raise ValueError("new M5 thesis must use a distinct hypothesis_id")
        previous_memory = (
            previous.agent_memory
            if previous.agent_memory.hypothesis_status
            in {HypothesisStatus.INVALIDATED, HypothesisStatus.EXPIRED}
            else None
        )
        return _create_thesis(
            event,
            evidence,
            policy,
            scenario_definitions,
            previous_memory=previous_memory,
            supersedes_thesis_id=previous.thesis_id,
        )
    valid_continuing_status = evidence.hypothesis_status in {
        HypothesisStatus.DEVELOPING,
        HypothesisStatus.ACTIVE,
        HypothesisStatus.CONFIRMED,
        HypothesisStatus.WEAKENING,
    }
    valid_continuing_relationship = evidence.relationship in {
        HypothesisRelationship.UNCHANGED,
        HypothesisRelationship.STRENGTHENED,
        HypothesisRelationship.WEAKENED,
    }
    if (
        event.event_type is RuntimeEventType.M5_CLOSED
        and previous.hypothesis_status is HypothesisStatus.EXPIRED
        and evidence.status in {AgentStatus.READY, AgentStatus.DEGRADED}
        and valid_continuing_status
        and valid_continuing_relationship
        and evidence.hypothesis_id == previous.hypothesis_id
        and evidence.previous_hypothesis_id == previous.hypothesis_id
        and evidence.thesis_id in {None, previous.thesis_id}
    ):
        return _create_thesis(
            event,
            evidence,
            policy,
            scenario_definitions,
            previous_memory=previous.agent_memory,
            supersedes_thesis_id=previous.thesis_id,
        )
    if previous_is_terminal and event.event_type is not RuntimeEventType.M5_CLOSED:
        return previous
    if previous_is_causally_expired:
        return _terminal_state(previous, event, expired=True)
    if evidence.hypothesis_id != previous.hypothesis_id or (
        evidence.thesis_id is not None and evidence.thesis_id != previous.thesis_id
    ):
        raise ValueError("evidence references an unrelated thesis")
    if evidence.previous_hypothesis_id != previous.hypothesis_id:
        raise ValueError("evidence does not reference current hypothesis")
    if evidence.hypothesis_status in {
        HypothesisStatus.INVALIDATED,
        HypothesisStatus.EXPIRED,
    }:
        memory = transition_memory(previous.agent_memory, evidence)
        terminal = _terminal_state(
            previous,
            event,
            expired=evidence.hypothesis_status is HypothesisStatus.EXPIRED,
        )
        data = terminal.model_dump(mode="python", exclude={"state_id"})
        data.update(
            {
                "agent_memory": memory,
                "evidence_ids": previous.evidence_ids + (evidence.evidence_id,),
                "latest_evidence_id": evidence.evidence_id,
                "latest_evidence_as_of": evidence.as_of,
                "latest_evidence_available_at": evidence.available_at,
                "runtime_state_id": evidence.runtime_state_id,
                "feature_snapshot_id": evidence.feature_snapshot_id,
            }
        )
        return ThesisState.model_validate(data)
    memory = transition_memory(previous.agent_memory, evidence)
    scenarios = _updated_scenarios(previous, evidence, event)
    eligibility = (
        EntryEligibility.ELIGIBLE
        if any(item.entry_eligibility is EntryEligibility.ELIGIBLE for item in scenarios)
        else EntryEligibility.WATCHING
    )
    m5_bars = previous.m5_bars_observed + int(
        event.event_type is RuntimeEventType.M5_CLOSED
    )
    data = previous.model_dump(mode="python", exclude={"state_id"})
    data.update(
        {
            "hypothesis": evidence.hypothesis,
            "direction": evidence.direction,
            "hypothesis_status": evidence.hypothesis_status,
            "relationship": evidence.relationship,
            "runtime_state_id": evidence.runtime_state_id,
            "feature_snapshot_id": evidence.feature_snapshot_id,
            "updated_at": event.available_at,
            "m5_bars_observed": m5_bars,
            "entry_eligibility": eligibility,
            "scenarios": scenarios,
            "evidence_ids": previous.evidence_ids + (evidence.evidence_id,),
            "latest_evidence_id": evidence.evidence_id,
            "latest_evidence_as_of": evidence.as_of,
            "latest_evidence_available_at": evidence.available_at,
            "agent_memory": memory,
            "last_event_id": event.event_id,
            "last_event_time": event.event_time,
            "last_observed_at": event.observed_at,
            "last_available_at": event.available_at,
            "last_source_sequence": event.source_sequence,
        }
    )
    updated = ThesisState.model_validate(data)
    if m5_bars > policy.max_m5_bars:
        return _terminal_state(updated, event, expired=True)
    return updated
