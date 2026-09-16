"""Deterministic interpretation of historical-similarity facts."""

from axq.agents._deterministic import (
    DeterministicSpecialistAgent,
    Interpretation,
    ObservedFact,
    fact_map,
    numeric,
)
from axq.agents.contracts import AbstentionReason, AgentStatus, DirectionalBias
from axq.tools import ToolCategory, ToolResult


class HistoricalSimilarityAgent(DeterministicSpecialistAgent):
    name = "historical"
    allowed_categories = frozenset(
        {ToolCategory.SIMILARITY, ToolCategory.SESSION_CONTEXT}
    )
    unavailable_hypothesis = "insufficient_comparable_cases"

    def interpret(
        self,
        observations: tuple[ObservedFact, ...],
        usable_results: tuple[ToolResult, ...],
    ) -> Interpretation:
        facts = fact_map(observations)
        sample_size = max(
            (result.quality.sample_size or 0 for result in usable_results),
            default=0,
        )
        if sample_size < 30:
            return Interpretation(
                hypothesis="insufficient_comparable_cases",
                direction=None,
                confidence=0.0,
                status=AgentStatus.ABSTAINED,
                abstention_reason=AbstentionReason.INSUFFICIENT_DATA,
            )
        similarity = numeric(facts.get("similarity_score")) or 0.0
        up_rate = numeric(facts.get("forward_up_rate"))
        mean_return = numeric(facts.get("forward_return_mean"))
        direction_conflict = (
            up_rate is not None
            and mean_return is not None
            and (up_rate - 0.5) * mean_return < 0.0
        )
        core = frozenset(
            name
            for name in ("similarity_score", "regime_match", "session_match")
            if name in facts
        )
        outcomes = frozenset(
            name
            for name in ("forward_up_rate", "forward_return_mean", "mfe_mean_atr", "mae_mean_atr")
            if name in facts
        )
        if similarity < 0.6 or up_rate is None or direction_conflict:
            return Interpretation(
                hypothesis="historically_mixed",
                direction=None,
                confidence=0.35,
                supports=core,
                contradicts=outcomes if direction_conflict else frozenset(),
                status=AgentStatus.DEGRADED,
                rationale="Comparable cases are weak, incomplete, or internally conflicting.",
            )
        if up_rate >= 0.6:
            hypothesis = "historical_continuation_bias"
            direction = DirectionalBias.BULLISH
        elif up_rate <= 0.4:
            hypothesis = "historical_reversal_bias"
            direction = DirectionalBias.BEARISH
        else:
            hypothesis = "historically_mixed"
            direction = None
        return Interpretation(
            hypothesis=hypothesis,
            direction=direction,
            confidence=min(0.75, similarity * 0.7),
            supports=core | outcomes,
            status=(
                AgentStatus.DEGRADED
                if hypothesis == "historically_mixed"
                else AgentStatus.READY
            ),
            rationale=(
                "Similarity, sample adequacy, and outcome distribution were "
                "assessed together."
            ),
        )
