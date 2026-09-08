from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


def breakout_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    """Donchian and breakout-state candidates using only past/current bars."""
    period = int(params.get("period", 20))
    tolerance = float(params.get("retest_tolerance", 0.001))
    prior_high = frame["high"].rolling(period, min_periods=period).max().shift(1)
    prior_low = frame["low"].rolling(period, min_periods=period).min().shift(1)
    width = prior_high - prior_low
    close = frame["close"]
    above = (close > prior_high).where(prior_high.notna())
    below = (close < prior_low).where(prior_low.notna())
    previous_above = above.shift(1).astype("boolean").fillna(False).astype(bool)
    previous_below = below.shift(1).astype("boolean").fillna(False).astype(bool)
    failed_up = (previous_above & (close <= prior_high)).where(prior_high.notna())
    failed_down = (previous_below & (close >= prior_low)).where(prior_low.notna())
    had_up = (
        above.shift(1).astype("Float64").rolling(period, min_periods=1).max().fillna(0.0)
        .astype(bool)
    )
    had_down = (
        below.shift(1).astype("Float64").rolling(period, min_periods=1).max().fillna(0.0)
        .astype(bool)
    )
    retest_up = (
        had_up
        & ((frame["low"] - prior_high).abs() / prior_high <= tolerance)
        & (close >= prior_high)
    ).where(prior_high.notna())
    retest_down = (
        had_down
        & ((frame["high"] - prior_low).abs() / prior_low <= tolerance)
        & (close <= prior_low)
    ).where(prior_low.notna())
    result = pd.DataFrame(index=frame.index)
    result[f"breakout_donchian_high_{period}"] = prior_high
    result[f"breakout_donchian_low_{period}"] = prior_low
    result[f"breakout_donchian_width_{period}"] = width / close
    result[f"breakout_position_{period}"] = ((close - prior_low) / width).mask(width == 0.0)
    result[f"breakout_above_{period}"] = above.astype("Float64")
    result[f"breakout_below_{period}"] = below.astype("Float64")
    result[f"breakout_failed_up_{period}"] = failed_up.astype("Float64")
    result[f"breakout_failed_down_{period}"] = failed_down.astype("Float64")
    result[f"breakout_retest_up_{period}"] = retest_up.astype("Float64")
    result[f"breakout_retest_down_{period}"] = retest_down.astype("Float64")
    return result.replace([np.inf, -np.inf], np.nan)
