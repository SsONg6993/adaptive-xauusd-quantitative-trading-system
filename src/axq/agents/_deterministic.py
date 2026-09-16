"""Shared deterministic synthesis for bounded specialist agents."""

from __future__ import annotations

from dataclasses import dataclass

from axq.agents.base import AgentInput, validate_agent_output
from axq.agents.contracts import (
    AbstentionReason,
    AgentEvidence,
    AgentStatus,
    DirectionalBias,
    EvidencePolarity,
    EvidenceReference,
    HypothesisInvalidation,
    HypothesisRelationship,
    HypothesisStatus,
    ToolResultReference,
)
from axq.agents.state import AgentMemory, transition_memory
from axq.runtime import FreshnessStatus
from axq.tools import ToolCategory, ToolResult, ToolStatus
from axq.tools.contracts import FactScalar
from axq.versioning import canonical_hash


@dataclass(frozen=True)
class ObservedFact:
    result: ToolResult
    name: str
    value: FactScalar


@dataclass(frozen=True)
class Interpretation:
    hypothesis: str
    direction: DirectionalBias | None
    confidence: float
    supports: frozenset[str] = frozenset()
    contradicts: frozenset[str] = frozenset()
    status: AgentStatus = AgentStatus.READY
    abstention_reason: AbstentionReason | None = None
    rationale: str | None = None


class DeterministicSpecialistAgent:
    """Template that binds transparent interpretations to Task 4 contracts."""

    name: str
    version = "1.0.0"
    allowed_categories: frozenset[ToolCategory]
    unavailable_hypothesis = "no_meaningful_hypothesis"

    def observe(self, agent_input: AgentInput) -> tuple[AgentEvidence, AgentMemory]:
        self._validate_access(agent_input)
        usable = tuple(
            result
            for result in agent_input.tool_results
            if result.status in {ToolStatus.AVAILABLE, ToolStatus.STALE}
            and result.quality.valid
        )
        if not usable:
            reason = self._unavailable_reason(agent_input.tool_results)
            return self._abstain(agent_input, self.unavailable_hypothesis, reason)

        observations = tuple(
            ObservedFact(result=result, name=fact.name, value=fact.value)
            for result in usable
            for fact in result.facts
        )
        terminal_fact = next(
            (
                item
                for item in observations
                if item.name in {"hypothesis_invalidated", "hypothesis_expired"}
                and item.value is True
            ),
            None,
        )
        if terminal_fact is not None and agent_input.previous_memory is not None:
            return self._terminate(agent_input, terminal_fact)
        interpretation = self.interpret(observations, usable)
        if interpretation.status is AgentStatus.ABSTAINED:
            return self._abstain(
                agent_input,
                interpretation.hypothesis,
                interpretation.abstention_reason
                or AbstentionReason.NO_MEANINGFUL_HYPOTHESIS,
            )

        degraded = interpretation.status is AgentStatus.DEGRADED or any(
            result.status is not ToolStatus.AVAILABLE
            for result in agent_input.tool_results
        )
        status = AgentStatus.DEGRADED if degraded else AgentStatus.READY
        quality = self._evidence_quality(agent_input.tool_results)
        confidence = min(interpretation.confidence * quality, quality)
        if status is AgentStatus.DEGRADED:
            confidence = min(confidence, 0.5)
        evidence = self._evidence(
            agent_input,
            interpretation,
            status=status,
            confidence=confidence,
            quality=quality,
            observations=observations,
        )
        validate_agent_output(agent_input, evidence)
        return evidence, transition_memory(agent_input.previous_memory, evidence)

    def interpret(
        self,
        observations: tuple[ObservedFact, ...],
        usable_results: tuple[ToolResult, ...],
    ) -> Interpretation:
        raise NotImplementedError

    def _validate_access(self, agent_input: AgentInput) -> None:
        disallowed = {
            result.category
            for result in agent_input.tool_results
            if result.category not in self.allowed_categories
        }
        if disallowed:
            names = ", ".join(sorted(item.value for item in disallowed))
            raise ValueError(f"{self.name} received disallowed tool category: {names}")

    @staticmethod
    def _unavailable_reason(results: tuple[ToolResult, ...]) -> AbstentionReason:
        if any(result.status is ToolStatus.ERROR for result in results):
            return AbstentionReason.TOOL_FAILURE
        if any(result.status is ToolStatus.STALE for result in results):
            return AbstentionReason.STALE_EVIDENCE
        return AbstentionReason.INSUFFICIENT_DATA

    @staticmethod
    def _evidence_quality(results: tuple[ToolResult, ...]) -> float:
        if not results:
            return 0.0
        values = []
        for result in results:
            if result.status is ToolStatus.AVAILABLE and result.quality.valid:
                values.append(1.0)
            elif result.status is ToolStatus.STALE and result.quality.valid:
                values.append(0.65)
            else:
                values.append(0.35)
        return sum(values) / len(values)

    def _identity(
        self,
        hypothesis: str,
        direction: DirectionalBias | None,
    ) -> str:
        value = canonical_hash(
            {
                "agent_name": self.name,
                "agent_version": self.version,
                "hypothesis": hypothesis,
                "direction": direction,
            }
        )
        return f"hyp-{value[:20]}"

    def _relationship(
        self,
        previous: AgentMemory | None,
        hypothesis_id: str,
        confidence: float,
    ) -> tuple[HypothesisRelationship, str | None, HypothesisStatus]:
        if previous is None:
            return HypothesisRelationship.NEW, None, HypothesisStatus.DEVELOPING
        if hypothesis_id != previous.hypothesis_id:
            return (
                HypothesisRelationship.REVERSED,
                previous.hypothesis_id,
                HypothesisStatus.DEVELOPING,
            )
        delta = confidence - previous.current_confidence
        relationship = HypothesisRelationship.UNCHANGED
        if delta >= 0.1:
            relationship = HypothesisRelationship.STRENGTHENED
        elif delta <= -0.1 or (
            previous.hypothesis_status is HypothesisStatus.CONFIRMED
            and confidence < 0.7
        ):
            relationship = HypothesisRelationship.WEAKENED
        lifecycle = (
            HypothesisStatus.WEAKENING
            if relationship is HypothesisRelationship.WEAKENED
            else HypothesisStatus.CONFIRMED
            if confidence >= 0.7
            else HypothesisStatus.ACTIVE
        )
        return relationship, previous.hypothesis_id, lifecycle

    @staticmethod
    def _reference(
        observation: ObservedFact,
        polarity: EvidencePolarity,
        strength: float,
    ) -> EvidenceReference:
        return EvidenceReference(
            tool_name=observation.result.tool_name,
            tool_result_id=observation.result.result_id,
            fact_name=observation.name,
            fact_value=observation.value,
            polarity=polarity,
            strength=strength,
            freshness=observation.result.freshness,
            quality_valid=observation.result.quality.valid,
        )

    def _evidence(
        self,
        agent_input: AgentInput,
        interpretation: Interpretation,
        *,
        status: AgentStatus,
        confidence: float,
        quality: float,
        observations: tuple[ObservedFact, ...],
    ) -> AgentEvidence:
        hypothesis_id = self._identity(
            interpretation.hypothesis,
            interpretation.direction,
        )
        relationship, previous_id, lifecycle = self._relationship(
            agent_input.previous_memory,
            hypothesis_id,
            confidence,
        )
        supporting = tuple(
            self._reference(item, EvidencePolarity.SUPPORTS, 0.7)
            for item in observations
            if item.name in interpretation.supports
        )
        contradicting = tuple(
            self._reference(item, EvidencePolarity.CONTRADICTS, 0.6)
            for item in observations
            if item.name in interpretation.contradicts
        )
        freshness = (
            FreshnessStatus.STALE
            if any(item.result.freshness is FreshnessStatus.STALE for item in observations)
            else FreshnessStatus.AVAILABLE
        )
        available_at = max(item.result.available_at for item in observations)
        return AgentEvidence(
            agent_name=self.name,
            agent_version=self.version,
            runtime_state_id=agent_input.runtime_state_id,
            feature_snapshot_id=agent_input.feature_snapshot_id,
            as_of=agent_input.as_of,
            available_at=available_at,
            hypothesis_id=hypothesis_id,
            hypothesis=interpretation.hypothesis,
            hypothesis_status=lifecycle,
            relationship=relationship,
            previous_hypothesis_id=previous_id,
            direction=interpretation.direction,
            confidence=confidence,
            uncertainty=1.0 - confidence,
            evidence_quality=quality,
            evidence_for=supporting,
            evidence_against=contradicting,
            invalidation=HypothesisInvalidation(invalidated=False),
            freshness=freshness,
            status=status,
            tool_inputs=tuple(
                ToolResultReference.from_result(result)
                for result in agent_input.tool_results
            ),
            setup_id=agent_input.setup_id,
            thesis_id=agent_input.thesis_id,
            rationale=interpretation.rationale,
        )

    def _abstain(
        self,
        agent_input: AgentInput,
        hypothesis: str,
        reason: AbstentionReason,
    ) -> tuple[AgentEvidence, AgentMemory]:
        previous = agent_input.previous_memory
        hypothesis_id = (
            previous.hypothesis_id
            if previous is not None
            else self._identity(hypothesis, None)
        )
        evidence = AgentEvidence(
            agent_name=self.name,
            agent_version=self.version,
            runtime_state_id=agent_input.runtime_state_id,
            feature_snapshot_id=agent_input.feature_snapshot_id,
            as_of=agent_input.as_of,
            available_at=max(
                (result.available_at for result in agent_input.tool_results),
                default=agent_input.as_of,
            ),
            hypothesis_id=hypothesis_id,
            hypothesis=(previous.current_hypothesis if previous is not None else hypothesis),
            hypothesis_status=HypothesisStatus.ABSTAINED,
            relationship=(
                HypothesisRelationship.NEW
                if previous is None
                else HypothesisRelationship.WEAKENED
            ),
            previous_hypothesis_id=(previous.hypothesis_id if previous else None),
            direction=None,
            confidence=0.0,
            uncertainty=1.0,
            evidence_quality=0.0,
            invalidation=HypothesisInvalidation(invalidated=False),
            freshness=(
                FreshnessStatus.STALE
                if reason is AbstentionReason.STALE_EVIDENCE
                else FreshnessStatus.UNAVAILABLE
            ),
            status=AgentStatus.ABSTAINED,
            tool_inputs=tuple(
                ToolResultReference.from_result(result)
                for result in agent_input.tool_results
            ),
            abstention_reason=reason,
            setup_id=agent_input.setup_id,
            thesis_id=agent_input.thesis_id,
        )
        validate_agent_output(agent_input, evidence)
        if previous is not None:
            return evidence, previous
        return evidence, transition_memory(None, evidence)

    def _terminate(
        self,
        agent_input: AgentInput,
        terminal_fact: ObservedFact,
    ) -> tuple[AgentEvidence, AgentMemory]:
        previous = agent_input.previous_memory
        if previous is None:
            raise ValueError("terminal evidence requires previous specialist memory")
        invalidated = terminal_fact.name == "hypothesis_invalidated"
        relationship = (
            HypothesisRelationship.INVALIDATED
            if invalidated
            else HypothesisRelationship.EXPIRED
        )
        lifecycle = (
            HypothesisStatus.INVALIDATED
            if invalidated
            else HypothesisStatus.EXPIRED
        )
        quality = self._evidence_quality(agent_input.tool_results)
        evidence = AgentEvidence(
            agent_name=self.name,
            agent_version=self.version,
            runtime_state_id=agent_input.runtime_state_id,
            feature_snapshot_id=agent_input.feature_snapshot_id,
            as_of=agent_input.as_of,
            available_at=terminal_fact.result.available_at,
            hypothesis_id=previous.hypothesis_id,
            hypothesis=previous.current_hypothesis,
            hypothesis_status=lifecycle,
            relationship=relationship,
            previous_hypothesis_id=previous.hypothesis_id,
            direction=None,
            confidence=0.0,
            uncertainty=1.0,
            evidence_quality=quality,
            evidence_against=(
                self._reference(
                    terminal_fact,
                    EvidencePolarity.CONTRADICTS,
                    1.0,
                ),
            ),
            invalidation=HypothesisInvalidation(
                invalidated=invalidated,
                reason=("validated invalidation fact" if invalidated else None),
                tool_result_id=(terminal_fact.result.result_id if invalidated else None),
                fact_name=(terminal_fact.name if invalidated else None),
            ),
            freshness=terminal_fact.result.freshness,
            status=(
                AgentStatus.DEGRADED
                if any(
                    result.status is not ToolStatus.AVAILABLE
                    for result in agent_input.tool_results
                )
                else AgentStatus.READY
            ),
            tool_inputs=tuple(
                ToolResultReference.from_result(result)
                for result in agent_input.tool_results
            ),
            setup_id=agent_input.setup_id,
            thesis_id=agent_input.thesis_id,
            rationale="A validated terminal fact closed the existing hypothesis.",
        )
        validate_agent_output(agent_input, evidence)
        return evidence, transition_memory(previous, evidence)


def fact_map(observations: tuple[ObservedFact, ...]) -> dict[str, FactScalar]:
    """Return deterministic last-by-tool-order values for named factual inputs."""
    return {item.name: item.value for item in observations}


def numeric(value: FactScalar | None) -> float | None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return None
    return float(value)
