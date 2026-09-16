"""Capability-focused fact tools and their small deterministic catalog."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from axq.runtime import FreshnessStatus
from axq.tools.contracts import (
    AnalyticalTool,
    ToolCategory,
    ToolFact,
    ToolInput,
    ToolProvenance,
    ToolQuality,
    ToolResult,
    ToolStatus,
)


def _result(
    tool: AnalyticalTool,
    tool_input: ToolInput,
    *,
    status: ToolStatus,
    freshness: FreshnessStatus,
    facts: tuple[ToolFact, ...] = (),
    quality: ToolQuality,
    warnings: tuple[str, ...] = (),
    provenance: tuple[ToolProvenance, ...] = (),
    available_at: datetime | None = None,
) -> ToolResult:
    snapshot = tool_input.feature_snapshot
    return ToolResult(
        tool_name=tool.name,
        tool_version=tool.version,
        category=tool.category,
        as_of=tool_input.state.as_of,
        available_at=available_at or tool_input.state.as_of,
        runtime_state_id=tool_input.state.state_id,
        input_snapshot_id=(snapshot.snapshot_id if snapshot else tool_input.state.state_id),
        freshness=freshness,
        status=status,
        facts=facts,
        quality=quality,
        warnings=warnings,
        provenance=provenance,
    )


@dataclass(frozen=True)
class FeatureFactTool:
    name: str
    category: ToolCategory
    feature_names: tuple[str, ...]
    required_timeframe: str = "M5"
    version: str = "1.0.0"

    def evaluate(self, tool_input: ToolInput) -> ToolResult:
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
        timeframe = self.required_timeframe.upper()
        completed = set(snapshot.completed_timeframes) & set(
            tool_input.state.market.completed_timeframes
        )
        if timeframe not in completed:
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=(f"{timeframe} candle is not completed and available",),
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
        values = snapshot.as_mapping()
        missing = tuple(name for name in self.feature_names if name not in values)
        if missing:
            return _result(
                self,
                tool_input,
                status=ToolStatus.INSUFFICIENT_DATA,
                freshness=market_status,
                quality=ToolQuality(valid=False, missing_fields=missing),
                warnings=("required causal features are not valid",),
                available_at=snapshot.available_at,
            )
        facts = tuple(ToolFact(name=name, value=values[name]) for name in self.feature_names)
        status = (
            ToolStatus.STALE
            if market_status is FreshnessStatus.STALE
            else ToolStatus.AVAILABLE
        )
        return _result(
            self,
            tool_input,
            status=status,
            freshness=market_status,
            facts=facts,
            quality=ToolQuality(valid=True),
            provenance=(
                ToolProvenance(
                    source=snapshot.source,
                    source_version=snapshot.source_version,
                    source_identity=snapshot.feature_manifest_id,
                ),
            ),
            available_at=snapshot.available_at,
        )


@dataclass(frozen=True)
class SlowContextFactTool:
    provider: str
    version: str = "1.0.0"
    category: ToolCategory = ToolCategory.SLOW_CONTEXT

    @property
    def name(self) -> str:
        return f"slow_context.{self.provider}"

    def evaluate(self, tool_input: ToolInput) -> ToolResult:
        context = next(
            (item for item in tool_input.state.slow_context if item.provider == self.provider),
            None,
        )
        cursor = next(
            (item for item in tool_input.state.source_cursors if item.source == self.provider),
            None,
        )
        if context is None or cursor is None or cursor.available_at is None:
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=("slow context is unavailable",),
            )
        usable_at = max(context.effective_at, cursor.available_at)
        if usable_at > tool_input.state.as_of:
            return _result(
                self,
                tool_input,
                status=ToolStatus.UNAVAILABLE,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=ToolQuality(valid=False),
                warnings=("slow context is not yet causally available",),
            )
        stale = tool_input.state.as_of >= context.expires_at
        return _result(
            self,
            tool_input,
            status=ToolStatus.STALE if stale else ToolStatus.AVAILABLE,
            freshness=FreshnessStatus.STALE if stale else FreshnessStatus.AVAILABLE,
            facts=(
                ToolFact(name="context_version", value=context.context_version),
                ToolFact(name="content_hash", value=context.content_hash),
            ),
            quality=ToolQuality(valid=True),
            provenance=(
                ToolProvenance(
                    source=self.provider,
                    source_version=context.context_version,
                    source_identity=context.content_hash,
                ),
            ),
            available_at=usable_at,
        )


class ToolCatalog:
    def __init__(self, tools: tuple[AnalyticalTool, ...] = ()) -> None:
        self._tools: dict[str, AnalyticalTool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: AnalyticalTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def evaluate(self, names: tuple[str, ...], tool_input: ToolInput) -> tuple[ToolResult, ...]:
        unknown = tuple(name for name in names if name not in self._tools)
        if unknown:
            raise ValueError(f"unknown tools: {unknown}")
        results: list[ToolResult] = []
        for name in names:
            tool = self._tools[name]
            try:
                results.append(tool.evaluate(tool_input))
            except Exception as error:
                results.append(
                    _result(
                        tool,
                        tool_input,
                        status=ToolStatus.ERROR,
                        freshness=FreshnessStatus.UNAVAILABLE,
                        quality=ToolQuality(valid=False),
                        warnings=(f"tool evaluation failed: {type(error).__name__}: {error}",),
                    )
                )
        return tuple(results)
