"""Barrier labeling with explicit same-bar ambiguity handling."""

from __future__ import annotations

import numpy as np
import pandas as pd

from axq.labels.base import BarrierMode, CollisionPolicy, LabelDefinition, TradeSide
from axq.labels.excursions import path_excursions


def _distances(
    frame: pd.DataFrame, position: int, definition: LabelDefinition
) -> tuple[float, float] | None:
    upper = float(definition.upper_barrier or 0.0)
    lower = float(definition.lower_barrier or 0.0)
    entry = float(frame["close"].iloc[position])
    if definition.barrier_mode == BarrierMode.PERCENTAGE:
        return entry * upper, entry * lower
    if definition.barrier_mode == BarrierMode.ABSOLUTE:
        return upper, lower
    atr_value = float(frame[definition.atr_column].iloc[position])
    if not np.isfinite(atr_value) or atr_value <= 0.0:
        return None
    return atr_value * upper, atr_value * lower


def _resolve_lower_timeframe(
    lower: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    upper_price: float,
    lower_price: float,
) -> str:
    timestamp = pd.to_datetime(lower["timestamp"], utc=True)
    subset = lower.loc[(timestamp >= start) & (timestamp < end)]
    for _, bar in subset.iterrows():
        upper_hit = float(bar["high"]) >= upper_price
        lower_hit = float(bar["low"]) <= lower_price
        if upper_hit and lower_hit:
            return "AMBIGUOUS"
        if upper_hit:
            return "UPPER_FIRST"
        if lower_hit:
            return "LOWER_FIRST"
    return "AMBIGUOUS"


def _collision_outcome(
    definition: LabelDefinition,
    *,
    lower_timeframe: pd.DataFrame | None,
    start: pd.Timestamp,
    end: pd.Timestamp,
    upper_price: float,
    lower_price: float,
) -> str:
    if definition.collision_policy == CollisionPolicy.AMBIGUOUS:
        return "AMBIGUOUS"
    if definition.collision_policy == CollisionPolicy.OPTIMISTIC:
        return "UPPER_FIRST" if definition.side == TradeSide.LONG else "LOWER_FIRST"
    if definition.collision_policy == CollisionPolicy.PESSIMISTIC:
        return "LOWER_FIRST" if definition.side == TradeSide.LONG else "UPPER_FIRST"
    if lower_timeframe is None:
        return "AMBIGUOUS"
    return _resolve_lower_timeframe(lower_timeframe, start, end, upper_price, lower_price)


def triple_barrier_labels(
    frame: pd.DataFrame,
    definition: LabelDefinition,
    *,
    lower_timeframe: pd.DataFrame | None = None,
) -> pd.DataFrame:
    horizon = definition.horizon_bars
    timestamps = pd.to_datetime(frame["timestamp"], utc=True)
    candle_opens = (
        pd.to_datetime(frame["candle_open_timestamp"], utc=True)
        if "candle_open_timestamp" in frame
        else timestamps
    )
    records: list[dict[str, object]] = []
    for position in range(len(frame)):
        if position + horizon >= len(frame):
            records.append({})
            continue
        distances = _distances(frame, position, definition)
        if distances is None:
            records.append({})
            continue
        upper_distance, lower_distance = distances
        entry = float(frame["close"].iloc[position])
        upper_price = entry + upper_distance
        lower_price = entry - lower_distance
        outcome = "TIMEOUT"
        hit_position = position + horizon
        hit_price = float(frame["close"].iloc[hit_position])
        for offset in range(1, horizon + 1):
            bar_position = position + offset
            upper_hit = float(frame["high"].iloc[bar_position]) >= upper_price
            lower_hit = float(frame["low"].iloc[bar_position]) <= lower_price
            if not upper_hit and not lower_hit:
                continue
            hit_position = bar_position
            if upper_hit and lower_hit:
                resolution_end = timestamps.iloc[bar_position]
                if resolution_end <= candle_opens.iloc[bar_position]:
                    resolution_end = (
                        timestamps.iloc[bar_position + 1]
                        if bar_position + 1 < len(frame)
                        else timestamps.iloc[bar_position]
                    )
                resolution_start = candle_opens.iloc[bar_position]
                if resolution_end <= resolution_start:
                    resolution_start = timestamps.iloc[bar_position]
                    resolution_end = (
                        timestamps.iloc[bar_position + 1]
                        if bar_position + 1 < len(frame)
                        else timestamps.iloc[bar_position]
                    )
                outcome = _collision_outcome(
                    definition,
                    lower_timeframe=lower_timeframe,
                    start=resolution_start,
                    end=resolution_end,
                    upper_price=upper_price,
                    lower_price=lower_price,
                )
            else:
                outcome = "UPPER_FIRST" if upper_hit else "LOWER_FIRST"
            hit_price = (
                upper_price
                if outcome == "UPPER_FIRST"
                else (
                    lower_price
                    if outcome == "LOWER_FIRST"
                    else float(frame["close"].iloc[bar_position])
                )
            )
            break
        atr_value = (
            float(frame[definition.atr_column].iloc[position])
            if definition.atr_column in frame
            else None
        )
        excursions = path_excursions(
            frame,
            position,
            hit_position - position,
            side=definition.side,
            atr_value=atr_value,
            risk_distance=lower_distance,
        )
        if definition.side == TradeSide.LONG:
            trade_outcome = {
                "UPPER_FIRST": "TP_FIRST",
                "LOWER_FIRST": "SL_FIRST",
            }.get(outcome, outcome)
        else:
            trade_outcome = {
                "LOWER_FIRST": "TP_FIRST",
                "UPPER_FIRST": "SL_FIRST",
            }.get(outcome, outcome)
        target = trade_outcome if definition.kind.value == "TP_BEFORE_SL" else outcome
        record: dict[str, object] = {
            f"target_{definition.name}": target,
            f"label_{definition.name}_barrier_hit": outcome,
            f"label_{definition.name}_hit_timestamp": timestamps.iloc[hit_position],
            f"label_{definition.name}_bars_to_hit": hit_position - position,
            f"label_{definition.name}_realized_return": (
                (hit_price / entry - 1.0)
                * (1.0 if definition.side == TradeSide.LONG else -1.0)
            ),
        }
        record.update(
            {f"label_{definition.name}_{key}": value for key, value in excursions.items()}
        )
        records.append(record)
    columns = [
        f"target_{definition.name}",
        f"label_{definition.name}_barrier_hit",
        f"label_{definition.name}_hit_timestamp",
        f"label_{definition.name}_bars_to_hit",
        f"label_{definition.name}_realized_return",
        *[
            f"label_{definition.name}_{metric}"
            for metric in (
                "mfe_raw",
                "mae_raw",
                "mfe_percent",
                "mae_percent",
                "mfe_atr",
                "mae_atr",
                "mfe_r",
                "mae_r",
            )
        ],
    ]
    return pd.DataFrame.from_records(records, index=frame.index).reindex(columns=columns)
