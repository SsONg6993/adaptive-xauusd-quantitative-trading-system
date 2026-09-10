"""Descriptive-only analytics for persisted Phase 8 experiences."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict

from axq.experience.contracts import (
    AgentContributionExperience,
    AttributionStatus,
    Experience,
    RejectedDecisionExperience,
    TradeExperience,
)


class ExperienceSummary(BaseModel):
    """Versioned aggregate facts; no score, recommendation, or policy mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    total_experiences: int
    experience_type_counts: dict[str, int]
    incomplete_attributions: int
    trade_count: int
    trade_direction_counts: dict[str, int]
    trade_session_counts: dict[str, int]
    trade_regime_counts: dict[str, int]
    realized_pnl: float | None
    average_r: float | None
    average_mfe_points: float | None
    average_mae_points: float | None
    average_holding_seconds: float | None
    win_rate: float | None
    profit_factor: float | None
    rejection_layer_counts: dict[str, int]
    rejection_reason_counts: dict[str, int]
    specialist_status_counts: dict[str, int]


def _counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _average(values: Iterable[float | None]) -> float | None:
    known = [value for value in values if value is not None]
    return sum(known) / len(known) if known else None


def summarize_experiences(experiences: Iterable[Experience]) -> ExperienceSummary:
    """Return descriptive aggregates while keeping unavailable values as ``None``."""

    records = tuple(experiences)
    trades = tuple(item for item in records if isinstance(item, TradeExperience))
    rejections = tuple(item for item in records if isinstance(item, RejectedDecisionExperience))
    contributions = tuple(
        item for item in records if isinstance(item, AgentContributionExperience)
    )
    gross_profit = sum(max(item.realized_pnl, 0.0) for item in trades)
    gross_loss = abs(sum(min(item.realized_pnl, 0.0) for item in trades))
    return ExperienceSummary(
        total_experiences=len(records),
        experience_type_counts=_counts(item.experience_type.value for item in records),
        incomplete_attributions=sum(
            item.attribution_status is AttributionStatus.INCOMPLETE for item in records
        ),
        trade_count=len(trades),
        trade_direction_counts=_counts(item.direction.value for item in trades),
        trade_session_counts=_counts(
            item.session if item.session is not None else "UNKNOWN" for item in trades
        ),
        trade_regime_counts=_counts(
            item.regime if item.regime is not None else "UNKNOWN" for item in trades
        ),
        realized_pnl=sum(item.realized_pnl for item in trades) if trades else None,
        average_r=_average(item.r_outcome for item in trades),
        average_mfe_points=_average(item.mfe_points for item in trades),
        average_mae_points=_average(item.mae_points for item in trades),
        average_holding_seconds=_average(item.holding_seconds for item in trades),
        win_rate=(
            sum(item.realized_pnl > 0.0 for item in trades) / len(trades)
            if trades
            else None
        ),
        profit_factor=gross_profit / gross_loss if gross_loss > 0.0 else None,
        rejection_layer_counts=_counts(item.rejection_layer.value for item in rejections),
        rejection_reason_counts=_counts(
            reason for item in rejections for reason in item.reason_codes
        ),
        specialist_status_counts=_counts(
            f"{item.specialist}:{item.status.value}" for item in contributions
        ),
    )
