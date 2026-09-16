"""Optional adapter exposing predictive probabilities as non-decisional facts."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Protocol

from axq.runtime import FreshnessStatus
from axq.tools.catalog import _result
from axq.tools.contracts import (
    ToolCategory,
    ToolFact,
    ToolInput,
    ToolProvenance,
    ToolQuality,
    ToolResult,
    ToolStatus,
    fact_name,
)

if TYPE_CHECKING:
    from axq.quant.inference import QuantAgent


class PredictiveModelEvidenceProvider(Protocol):
    model_id: str
    feature_manifest_id: str
    maximum_data_age_ms: int

    def probabilities(self, feature_values: dict[str, Any]) -> dict[str, float]:
        """Return label-to-probability facts without a trading decision."""


class QuantAgentEvidenceProvider:
    """Narrow adapter around the existing frozen Phase 4 QuantAgent."""

    def __init__(self, agent: QuantAgent) -> None:
        self._agent = agent
        self.model_id = str(agent.manifest.model_id)
        self.feature_manifest_id = str(agent.manifest.feature_manifest_id)
        self.maximum_data_age_ms = int(agent.maximum_data_age_ms)

    def probabilities(self, feature_values: dict[str, Any]) -> dict[str, float]:
        values = self._agent.predict_probabilities(feature_values)
        labels = self._agent.model.classes_
        return {str(label): float(values[index]) for index, label in enumerate(labels)}


class OptionalPredictiveModelTool:
    name = "predictive.optional"
    version = "1.0.0"
    category = ToolCategory.PREDICTIVE_MODEL

    def __init__(self, provider: PredictiveModelEvidenceProvider | None) -> None:
        self._provider = provider

    def evaluate(self, tool_input: ToolInput) -> ToolResult:
        if self._provider is None:
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=("no predictive model is installed",),
            )
        snapshot = tool_input.feature_snapshot
        if snapshot is None:
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=("causal feature snapshot is unavailable",),
            )
        if snapshot.available_at > tool_input.state.as_of:
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=("feature snapshot is not yet causally available",),
            )
        if snapshot.feature_manifest_id != self._provider.feature_manifest_id:
            return _result(
                self,
                tool_input,
                status=ToolStatus.ERROR,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=("feature manifest is incompatible with predictive model",),
            )
        age_ms = int((tool_input.state.as_of - snapshot.available_at).total_seconds() * 1_000)
        if age_ms > self._provider.maximum_data_age_ms:
            return _result(
                self,
                tool_input,
                status=ToolStatus.STALE,
                freshness=FreshnessStatus.STALE,
                quality=ToolQuality(valid=False),
                warnings=("predictive model input is stale",),
                available_at=snapshot.available_at,
            )
        market_freshness = tool_input.state.market.freshness.status
        if market_freshness in {FreshnessStatus.UNKNOWN, FreshnessStatus.UNAVAILABLE}:
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=market_freshness,
                quality=ToolQuality(valid=False),
                warnings=("market state is unavailable",),
                available_at=snapshot.available_at,
            )
        try:
            probabilities = self._provider.probabilities(snapshot.as_mapping())
            facts = _probability_facts(probabilities)
        except Exception as error:
            return _result(
                self,
                tool_input,
                status=ToolStatus.ERROR,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=(f"predictive inference failed: {type(error).__name__}: {error}",),
                available_at=snapshot.available_at,
            )
        return _result(
            self,
            tool_input,
            status=(
                ToolStatus.STALE
                if market_freshness is FreshnessStatus.STALE
                else ToolStatus.AVAILABLE
            ),
            freshness=market_freshness,
            facts=facts,
            quality=ToolQuality(valid=True),
            provenance=(
                ToolProvenance(
                    source="phase4-quant-agent",
                    source_version=self.version,
                    source_identity=self._provider.model_id,
                ),
            ),
            available_at=snapshot.available_at,
        )


def _probability_facts(probabilities: Mapping[str, float]) -> tuple[ToolFact, ...]:
    if not probabilities:
        raise ValueError("predictive model returned no probabilities")
    normalized_labels = {"BUY": "up", "SELL": "down", "HOLD": "neutral"}
    facts: list[ToolFact] = []
    total = 0.0
    for label, raw_value in sorted(probabilities.items()):
        value = float(raw_value)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError("predictive probability must be finite and between zero and one")
        total += value
        normalized = normalized_labels.get(label.upper(), fact_name(label))
        facts.append(ToolFact(name=f"class_probability_{normalized}", value=value))
    if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError("predictive probabilities must sum to one")
    return tuple(sorted(facts, key=lambda fact: fact.name))
