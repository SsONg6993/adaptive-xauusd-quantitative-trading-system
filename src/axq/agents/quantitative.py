"""Deterministic quantitative-condition interpretation."""

from axq.agents._deterministic import (
    DeterministicSpecialistAgent,
    Interpretation,
    ObservedFact,
    fact_map,
    numeric,
)
from axq.agents.contracts import AgentStatus, DirectionalBias
from axq.tools import ToolCategory, ToolResult


class QuantitativeAgent(DeterministicSpecialistAgent):
    name = "quant"
    allowed_categories = frozenset(
        {
            ToolCategory.TREND,
            ToolCategory.MOMENTUM,
            ToolCategory.VOLATILITY,
            ToolCategory.STATISTICS,
            ToolCategory.VOLUME,
            ToolCategory.PREDICTIVE_MODEL,
        }
    )
    unavailable_hypothesis = "quantitatively_mixed"

    def interpret(
        self,
        observations: tuple[ObservedFact, ...],
        usable_results: tuple[ToolResult, ...],
    ) -> Interpretation:
        del usable_results
        facts = fact_map(observations)
        signed: dict[str, float] = {}
        ema = numeric(facts.get("trend_close_to_ema_20"))
        if ema is not None and abs(ema) >= 0.001:
            signed["trend_close_to_ema_20"] = 0.4 if ema > 0.0 else -0.4
        plus = numeric(facts.get("trend_plus_di_14"))
        minus = numeric(facts.get("trend_minus_di_14"))
        if plus is not None and minus is not None and abs(plus - minus) >= 2.0:
            signed["trend_plus_di_14" if plus > minus else "trend_minus_di_14"] = (
                0.35 if plus > minus else -0.35
            )
        macd = numeric(facts.get("momentum_macd_hist_12_26_9"))
        if macd is not None and abs(macd) >= 0.05:
            signed["momentum_macd_hist_12_26_9"] = 0.2 if macd > 0.0 else -0.2
        rsi = numeric(facts.get("momentum_rsi_14"))
        if rsi is not None and abs(rsi - 50.0) >= 5.0:
            signed["momentum_rsi_14"] = 0.15 if rsi > 50.0 else -0.15
        probability_up = numeric(facts.get("class_probability_up"))
        probability_down = numeric(facts.get("class_probability_down"))
        if (
            probability_up is not None
            and probability_down is not None
            and abs(probability_up - probability_down) >= 0.1
        ):
            model_fact = (
                "class_probability_up"
                if probability_up > probability_down
                else "class_probability_down"
            )
            signed[model_fact] = 0.15 if probability_up > probability_down else -0.15
        score = sum(signed.values())
        positive = frozenset(name for name, value in signed.items() if value > 0.0)
        negative = frozenset(name for name, value in signed.items() if value < 0.0)
        zscore = numeric(facts.get("statistics_zscore_20"))
        extended = (rsi is not None and (rsi >= 70.0 or rsi <= 30.0)) or (
            zscore is not None and abs(zscore) >= 2.0
        )
        extension_names = frozenset(
            name
            for name in ("momentum_rsi_14", "statistics_zscore_20")
            if name in facts
        )
        if abs(score) < 0.3:
            return Interpretation(
                hypothesis="quantitatively_mixed",
                direction=DirectionalBias.NEUTRAL,
                confidence=0.35,
                supports=positive,
                contradicts=negative,
                status=AgentStatus.DEGRADED,
                rationale="Directional quantitative evidence is weak or mixed.",
            )
        bullish = score > 0.0
        hypothesis = (
            "bullish_but_overextended"
            if bullish and extended
            else "bearish_but_overextended"
            if extended
            else "bullish_quantitative_tendency"
            if bullish
            else "bearish_quantitative_tendency"
        )
        return Interpretation(
            hypothesis=hypothesis,
            direction=DirectionalBias.BULLISH if bullish else DirectionalBias.BEARISH,
            confidence=min(0.8, 0.4 + abs(score) * 0.35),
            supports=positive if bullish else negative,
            contradicts=(negative if bullish else positive) | extension_names,
            rationale=(
                "Direction is supported, but statistical extension raises chase risk."
                if extended
                else "Independent quantitative categories support a directional tendency."
            ),
        )
