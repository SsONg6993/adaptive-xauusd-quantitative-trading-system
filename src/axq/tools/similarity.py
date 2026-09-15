"""Optional factual contract for local historical-similarity evidence."""

from __future__ import annotations

from typing import Protocol

from pydantic import Field

from axq.runtime import FreshnessStatus
from axq.runtime.state import FiniteFloat
from axq.tools.catalog import _result
from axq.tools.contracts import (
    CausalFeatureSnapshot,
    ToolCategory,
    ToolFact,
    ToolInput,
    ToolModel,
    ToolProvenance,
    ToolQuality,
    ToolResult,
    ToolStatus,
)


class SimilarityEvidence(ToolModel):
    similarity_score: FiniteFloat = Field(ge=0.0, le=1.0)
    sample_size: int = Field(gt=0)
    regime_match: bool | None = None
    session_match: bool | None = None
    forward_up_rate: FiniteFloat | None = Field(default=None, ge=0.0, le=1.0)
    forward_return_mean: FiniteFloat | None = None
    mfe_mean_atr: FiniteFloat | None = Field(default=None, ge=0.0)
    mae_mean_atr: FiniteFloat | None = Field(default=None, ge=0.0)
    source_identity: str = Field(min_length=1)


class SimilarityEvidenceProvider(Protocol):
    provider_name: str
    provider_version: str

    def find_similar(self, snapshot: CausalFeatureSnapshot) -> SimilarityEvidence:
        """Return causal distributional evidence without interpreting direction."""


class HistoricalSimilarityTool:
    name = "similarity.historical"
    version = "1.0.0"
    category = ToolCategory.SIMILARITY

    def __init__(self, provider: SimilarityEvidenceProvider | None) -> None:
        self._provider = provider

    def evaluate(self, tool_input: ToolInput) -> ToolResult:
        snapshot = tool_input.feature_snapshot
        if self._provider is None or snapshot is None:
            reason = (
                "no historical similarity provider is installed"
                if self._provider is None
                else "causal feature snapshot is unavailable"
            )
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=(reason,),
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
        if snapshot.feature_manifest_id != tool_input.state.market.feature_manifest_id:
            return _result(
                self,
                tool_input,
                status=ToolStatus.ERROR,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=("feature manifest does not match runtime market state",),
            )
        if not set(snapshot.completed_timeframes).issubset(
            tool_input.state.market.completed_timeframes
        ):
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=("feature snapshot timeframes are not completed in market state",),
            )
        market_status = tool_input.state.market.freshness.status
        if market_status in {FreshnessStatus.UNKNOWN, FreshnessStatus.UNAVAILABLE}:
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=market_status,
                quality=ToolQuality(valid=False),
                warnings=("market state is unavailable",),
            )
        try:
            evidence = self._provider.find_similar(snapshot)
        except Exception as error:
            return _result(
                self,
                tool_input,
                status=ToolStatus.ERROR,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=(f"similarity lookup failed: {type(error).__name__}: {error}",),
                available_at=snapshot.available_at,
            )
        values = evidence.model_dump(
            mode="python",
            exclude={"schema_version", "sample_size", "source_identity"},
        )
        facts = tuple(
            ToolFact(name=name, value=value)
            for name, value in values.items()
            if value is not None
        )
        stale = market_status is FreshnessStatus.STALE
        return _result(
            self,
            tool_input,
            status=ToolStatus.STALE if stale else ToolStatus.AVAILABLE,
            freshness=FreshnessStatus.STALE if stale else FreshnessStatus.AVAILABLE,
            facts=facts,
            quality=ToolQuality(valid=True, sample_size=evidence.sample_size),
            provenance=(
                ToolProvenance(
                    source=self._provider.provider_name,
                    source_version=self._provider.provider_version,
                    source_identity=evidence.source_identity,
                ),
            ),
            available_at=snapshot.available_at,
        )
