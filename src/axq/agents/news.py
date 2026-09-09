"""Deterministic baseline interpretation of supplied slow-context facts."""

from axq.agents._deterministic import (
    DeterministicSpecialistAgent,
    Interpretation,
    ObservedFact,
    fact_map,
)
from axq.agents.contracts import AgentStatus
from axq.tools import ToolCategory, ToolResult, ToolStatus


class NewsMacroAgent(DeterministicSpecialistAgent):
    name = "news"
    allowed_categories = frozenset({ToolCategory.SLOW_CONTEXT})
    unavailable_hypothesis = "NO_VALID_CONTEXT"

    def interpret(
        self,
        observations: tuple[ObservedFact, ...],
        usable_results: tuple[ToolResult, ...],
    ) -> Interpretation:
        facts = fact_map(observations)
        names = frozenset(facts)
        if any(result.status is ToolStatus.STALE for result in usable_results):
            return Interpretation(
                hypothesis="CONTEXT_STALE",
                direction=None,
                confidence=0.25,
                supports=names,
                status=AgentStatus.DEGRADED,
                rationale="Slow context exists but is stale at the causal decision time.",
            )
        risk = str(facts.get("event_risk_level", "normal")).lower()
        if risk in {"high", "critical"}:
            hypothesis, confidence = "HIGH_EVENT_RISK", 0.75
        elif str(facts.get("usd_pressure_context", "")).lower() == "supportive":
            hypothesis, confidence = "USD_SUPPORTIVE", 0.6
        elif str(facts.get("usd_pressure_context", "")).lower() == "pressure":
            hypothesis, confidence = "USD_PRESSURE", 0.6
        elif facts:
            hypothesis, confidence = "NORMAL_EVENT_RISK", 0.6
        else:
            hypothesis, confidence = "MACRO_MIXED", 0.35
        return Interpretation(
            hypothesis=hypothesis,
            direction=None,
            confidence=confidence,
            supports=names,
            status=(
                AgentStatus.DEGRADED
                if hypothesis == "MACRO_MIXED"
                else AgentStatus.READY
            ),
            rationale="Only causally supplied slow-context facts were interpreted.",
        )
