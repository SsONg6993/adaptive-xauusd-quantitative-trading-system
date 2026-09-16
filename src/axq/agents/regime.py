"""Deterministic non-directional market-regime interpretation."""

from axq.agents._deterministic import (
    DeterministicSpecialistAgent,
    Interpretation,
    ObservedFact,
    fact_map,
    numeric,
)
from axq.agents.contracts import AgentStatus
from axq.tools import ToolCategory, ToolResult


class MarketRegimeAgent(DeterministicSpecialistAgent):
    name = "regime"
    allowed_categories = frozenset(
        {
            ToolCategory.TREND,
            ToolCategory.VOLATILITY,
            ToolCategory.BREAKOUT,
            ToolCategory.STATISTICS,
            ToolCategory.SESSION_CONTEXT,
        }
    )
    unavailable_hypothesis = "UNKNOWN"

    def interpret(
        self,
        observations: tuple[ObservedFact, ...],
        usable_results: tuple[ToolResult, ...],
    ) -> Interpretation:
        del usable_results
        facts = fact_map(observations)
        adx = numeric(facts.get("trend_adx_14"))
        efficiency = numeric(facts.get("statistics_efficiency_ratio_20"))
        expansion = numeric(facts.get("volatility_expansion"))
        relevant = frozenset(facts)
        if facts.get("breakout_above") is True or facts.get("breakout_below") is True:
            hypothesis, confidence, status = "BREAKOUT", 0.7, AgentStatus.READY
        elif expansion is not None and expansion >= 1.25:
            hypothesis, confidence, status = (
                "VOLATILITY_EXPANSION",
                0.7,
                AgentStatus.READY,
            )
        elif adx is not None and efficiency is not None and adx >= 25.0 and efficiency >= 0.35:
            hypothesis, confidence, status = "TRENDING", 0.72, AgentStatus.READY
        elif adx is not None and efficiency is not None and adx < 20.0 and efficiency < 0.3:
            hypothesis, confidence, status = "RANGING", 0.68, AgentStatus.READY
        else:
            hypothesis, confidence, status = "TRANSITION", 0.4, AgentStatus.DEGRADED
        return Interpretation(
            hypothesis=hypothesis,
            direction=None,
            confidence=confidence,
            supports=relevant,
            status=status,
            rationale="Regime context combines trend efficiency, volatility, and breakout facts.",
        )
