"""Causal market-structure features.

A candidate pivot at position p is emitted at p + right_bars. The output row
records the pivot value and its confirmation delay without backdating.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from axq.features.indicators import atr, true_range


def market_structure_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    left = int(params.get("left_bars", 2))
    right = int(params.get("right_bars", 2))
    level_lookback = int(params.get("level_lookback", 20))
    atr_period = int(params.get("atr_period", 14))
    if left < 1 or right < 1:
        raise ValueError("left_bars and right_bars must be positive")
    rows = len(frame)
    high = frame["high"].to_numpy(dtype=float)
    low = frame["low"].to_numpy(dtype=float)
    swing_high = np.full(rows, np.nan)
    swing_low = np.full(rows, np.nan)
    hh = np.full(rows, np.nan)
    hl = np.full(rows, np.nan)
    lh = np.full(rows, np.nan)
    ll = np.full(rows, np.nan)
    last_high = float("nan")
    last_low = float("nan")
    start = left + right
    for confirmed_at in range(start, rows):
        pivot = confirmed_at - right
        high_window = high[pivot - left : pivot + right + 1]
        low_window = low[pivot - left : pivot + right + 1]
        hh[confirmed_at] = hl[confirmed_at] = lh[confirmed_at] = ll[confirmed_at] = 0.0
        if np.isfinite(high_window).all() and high[pivot] == high_window.max():
            swing_high[confirmed_at] = high[pivot]
            if np.isfinite(last_high):
                hh[confirmed_at] = float(high[pivot] > last_high)
                lh[confirmed_at] = float(high[pivot] <= last_high)
            last_high = high[pivot]
        if np.isfinite(low_window).all() and low[pivot] == low_window.min():
            swing_low[confirmed_at] = low[pivot]
            if np.isfinite(last_low):
                hl[confirmed_at] = float(low[pivot] >= last_low)
                ll[confirmed_at] = float(low[pivot] < last_low)
            last_low = low[pivot]

    index = frame.index
    high_pulse = pd.Series(swing_high, index=index)
    low_pulse = pd.Series(swing_low, index=index)
    resistance = high_pulse.ffill()
    support = low_pulse.ffill()
    prior_resistance = resistance.shift(1)
    prior_support = support.shift(1)
    close_series = frame["close"].astype(float)
    previous_close = close_series.shift(1)
    bos_up = ((close_series > prior_resistance) & (previous_close <= prior_resistance)).where(
        prior_resistance.notna()
    )
    bos_down = ((close_series < prior_support) & (previous_close >= prior_support)).where(
        prior_support.notna()
    )
    bos_up_value = bos_up.astype("boolean").fillna(False).to_numpy(dtype=bool)
    bos_down_value = bos_down.astype("boolean").fillna(False).to_numpy(dtype=bool)
    structure_bias = np.full(rows, np.nan)
    choch_up = np.full(rows, np.nan)
    choch_down = np.full(rows, np.nan)
    bias = 0.0
    for position in range(rows):
        if pd.isna(bos_up.iloc[position]) and pd.isna(bos_down.iloc[position]):
            continue
        choch_up[position] = float(bos_up_value[position] and bias < 0.0)
        choch_down[position] = float(bos_down_value[position] and bias > 0.0)
        if bos_up_value[position]:
            bias = 1.0
        elif bos_down_value[position]:
            bias = -1.0
        structure_bias[position] = bias
    bias_series = pd.Series(structure_bias, index=index).ffill()
    average_range = atr(frame, atr_period)
    ranges = true_range(frame)
    median_range = ranges.rolling(level_lookback, min_periods=level_lookback).median()
    result = pd.DataFrame(index=index)
    result["structure_swing_high_confirmed"] = high_pulse
    result["structure_swing_low_confirmed"] = low_pulse
    result["structure_swing_confirmation_delay"] = pd.Series(
        np.where(np.arange(rows) >= start, float(right), np.nan), index=index
    )
    result["structure_hh"] = hh
    result["structure_hl"] = hl
    result["structure_lh"] = lh
    result["structure_ll"] = ll
    result["structure_resistance"] = resistance
    result["structure_support"] = support
    result["structure_bos_up"] = bos_up.astype("Float64")
    result["structure_bos_down"] = bos_down.astype("Float64")
    result["structure_choch_up"] = pd.Series(choch_up, index=index)
    result["structure_choch_down"] = pd.Series(choch_down, index=index)
    result["structure_bias"] = bias_series
    result["structure_distance_resistance_atr"] = (resistance - close_series) / average_range
    result["structure_distance_support_atr"] = (close_series - support) / average_range
    recent_high = frame["high"].rolling(level_lookback, min_periods=level_lookback).max()
    recent_low = frame["low"].rolling(level_lookback, min_periods=level_lookback).min()
    result[f"structure_distance_recent_high_{level_lookback}"] = (
        recent_high - close_series
    ) / average_range
    result[f"structure_distance_recent_low_{level_lookback}"] = (
        close_series - recent_low
    ) / average_range
    expansion = ranges / median_range
    result[f"structure_range_expansion_{level_lookback}"] = expansion
    result[f"structure_compression_{level_lookback}"] = 1.0 / expansion
    return result
