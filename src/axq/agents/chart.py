"""Deterministic hierarchical market-structure interpretation."""

from axq.agents._deterministic import (
    DeterministicSpecialistAgent,
    Interpretation,
    ObservedFact,
    fact_map,
    numeric,
)
from axq.agents.contracts import AgentStatus, DirectionalBias
from axq.tools import ToolCategory, ToolResult


class ChartAgent(DeterministicSpecialistAgent):
    name = "chart"
    allowed_categories = frozenset(
        {
            ToolCategory.STRUCTURE,
            ToolCategory.BREAKOUT,
            ToolCategory.VOLATILITY,
            ToolCategory.SESSION_CONTEXT,
        }
    )
    unavailable_hypothesis = "structure_unclear"

    def interpret(
        self,
        observations: tuple[ObservedFact, ...],
        usable_results: tuple[ToolResult, ...],
    ) -> Interpretation:
        del usable_results
        facts = fact_map(observations)
        weights = {
            "h4_structure_bias": 0.35,
            "h1_structure_bias": 0.30,
            "m15_structure_bias": 0.20,
            "m5_structure_bias": 0.15,
            "structure_bias": 0.20,
        }
        signed: dict[str, float] = {}
        for name, weight in weights.items():
            value = numeric(facts.get(name))
            if value is not None and value != 0.0:
                signed[name] = weight if value > 0.0 else -weight
        boolean_weights = {
            "structure_bos_up": 0.30,
            "structure_bos_down": -0.30,
            "structure_choch_up": 0.20,
            "structure_choch_down": -0.20,
            "breakout_above": 0.20,
            "breakout_below": -0.20,
        }
        for name, weight in boolean_weights.items():
            if facts.get(name) is True:
                signed[name] = weight
        positive = frozenset(name for name, value in signed.items() if value > 0.0)
        negative = frozenset(name for name, value in signed.items() if value < 0.0)
        htf = sum(signed.get(name, 0.0) for name in ("h4_structure_bias", "h1_structure_bias"))
        ltf = sum(signed.get(name, 0.0) for name in ("m15_structure_bias", "m5_structure_bias"))
        conflict = htf * ltf < 0.0
        score = sum(signed.values())
        if conflict or abs(score) < 0.2:
            return Interpretation(
                hypothesis="structure_unclear",
                direction=DirectionalBias.NEUTRAL,
                confidence=0.4,
                supports=positive,
                contradicts=negative,
                status=AgentStatus.DEGRADED,
                rationale="Higher- and lower-timeframe structure is mixed or weak.",
            )
        bullish = score > 0.0
        return Interpretation(
            hypothesis="bullish_continuation" if bullish else "bearish_continuation",
            direction=DirectionalBias.BULLISH if bullish else DirectionalBias.BEARISH,
            confidence=min(0.85, 0.45 + abs(score) * 0.45),
            supports=positive if bullish else negative,
            contradicts=negative if bullish else positive,
            rationale="Hierarchically weighted structure supports the directional thesis.",
        )
