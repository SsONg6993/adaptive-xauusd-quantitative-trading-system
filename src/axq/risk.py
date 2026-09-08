"""Deterministic pre-trade veto and broker-specification position sizing."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    max_risk_fraction: float = 0.005
    max_daily_loss_fraction: float = 0.02
    max_drawdown_fraction: float = 0.10
    max_open_positions: int = 1
    max_spread_points: float = 50
    min_master_confidence: float = 0.65
    max_data_age_seconds: float = 15


@dataclass(frozen=True)
class RiskContext:
    equity: float
    daily_loss_fraction: float
    drawdown_fraction: float
    open_positions: int
    spread_points: float
    master_confidence: float
    data_age_seconds: float
    python_healthy: bool
    mt5_healthy: bool


def veto_reasons(context: RiskContext, limits: RiskLimits) -> list[str]:
    reasons: list[str] = []
    if context.equity <= 0:
        reasons.append("invalid_equity")
    if context.daily_loss_fraction >= limits.max_daily_loss_fraction:
        reasons.append("daily_loss_limit")
    if context.drawdown_fraction >= limits.max_drawdown_fraction:
        reasons.append("drawdown_limit")
    if context.open_positions >= limits.max_open_positions:
        reasons.append("position_limit")
    if context.spread_points > limits.max_spread_points:
        reasons.append("spread_limit")
    if context.master_confidence < limits.min_master_confidence:
        reasons.append("confidence_below_minimum")
    if context.data_age_seconds > limits.max_data_age_seconds:
        reasons.append("stale_data")
    if not context.python_healthy:
        reasons.append("python_unhealthy")
    if not context.mt5_healthy:
        reasons.append("mt5_unhealthy")
    return reasons


def calculate_volume_lots(
    *,
    equity: float,
    risk_fraction: float,
    stop_distance_price: float,
    tick_size: float,
    tick_value_loss: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
) -> float:
    """Size from broker specs and round down; return zero when minimum volume is unsafe."""
    values = (
        equity,
        risk_fraction,
        stop_distance_price,
        tick_size,
        tick_value_loss,
        volume_min,
        volume_max,
        volume_step,
    )
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("all sizing inputs must be finite and positive")
    loss_per_lot = (stop_distance_price / tick_size) * tick_value_loss
    raw_volume = equity * risk_fraction / loss_per_lot
    capped = min(raw_volume, volume_max)
    stepped = math.floor((capped + 1e-12) / volume_step) * volume_step
    if stepped < volume_min:
        return 0.0
    precision = max(0, -int(math.floor(math.log10(volume_step)))) + 2
    return round(stepped, precision)
