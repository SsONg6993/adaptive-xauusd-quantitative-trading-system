from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from axq.features.indicators import atr, seeded_ema, sma, true_range


def volatility_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    atr_period = int(params.get("atr_period", 14))
    average_range = atr(frame, atr_period)
    rolling = int(params.get("rolling_period", 20))
    deviations = float(params.get("bollinger_deviations", 2.0))
    keltner_multiplier = float(params.get("keltner_multiplier", 2.0))
    returns = pd.Series(
        np.log(frame["close"] / frame["close"].shift(1)), index=frame.index, dtype=float
    )
    center = sma(frame["close"], rolling)
    std = frame["close"].rolling(rolling, min_periods=rolling).std(ddof=0)
    upper = center + deviations * std
    lower = center - deviations * std
    keltner_center = seeded_ema(frame["close"], rolling)
    keltner_upper = keltner_center + keltner_multiplier * average_range
    keltner_lower = keltner_center - keltner_multiplier * average_range
    ranges = true_range(frame)
    result = pd.DataFrame(index=frame.index)
    result[f"vol_atr_{atr_period}"] = average_range
    result[f"vol_atr_pct_{atr_period}"] = average_range / frame["close"]
    result[f"vol_realized_{rolling}"] = np.sqrt(
        returns.pow(2).rolling(rolling, min_periods=rolling).sum()
    )
    log_range = pd.Series(
        np.log(frame["high"] / frame["low"]), index=frame.index, dtype=float
    )
    result[f"vol_parkinson_{rolling}"] = np.sqrt(
        log_range.pow(2).rolling(rolling, min_periods=rolling).mean() / (4.0 * np.log(2.0))
    )
    result[f"vol_bb_mid_{rolling}"] = center
    result[f"vol_bb_upper_{rolling}_{deviations:g}"] = upper
    result[f"vol_bb_lower_{rolling}_{deviations:g}"] = lower
    result[f"vol_bb_width_{rolling}_{deviations:g}"] = (upper - lower) / center
    result[f"vol_bb_percent_b_{rolling}_{deviations:g}"] = (
        (frame["close"] - lower) / (upper - lower)
    ).mask(upper == lower)
    result[f"vol_keltner_mid_{rolling}"] = keltner_center
    result[f"vol_keltner_upper_{rolling}_{keltner_multiplier:g}"] = keltner_upper
    result[f"vol_keltner_lower_{rolling}_{keltner_multiplier:g}"] = keltner_lower
    result[f"vol_keltner_width_{rolling}_{keltner_multiplier:g}"] = (
        keltner_upper - keltner_lower
    ) / keltner_center
    result[f"vol_squeeze_{rolling}"] = (
        ((upper < keltner_upper) & (lower > keltner_lower))
        .where(upper.notna() & keltner_upper.notna())
        .astype("Float64")
    )
    range_mean = ranges.rolling(rolling, min_periods=rolling).mean()
    range_std = ranges.rolling(rolling, min_periods=rolling).std(ddof=0)
    result[f"vol_range_zscore_{rolling}"] = ((ranges - range_mean) / range_std).mask(
        range_std == 0.0
    )
    return result
