from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


def statistical_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    period = int(params.get("period", 20))
    returns = frame["close"].pct_change(fill_method=None)
    mean = returns.rolling(period).mean()
    std = returns.rolling(period).std(ddof=0)
    result = pd.DataFrame(index=frame.index)
    result[f"stat_return_mean_{period}"] = mean
    result[f"stat_return_variance_{period}"] = returns.rolling(period).var(ddof=0)
    result[f"stat_return_skew_{period}"] = returns.rolling(period).skew()
    result[f"stat_return_kurt_{period}"] = returns.rolling(period).kurt()
    result[f"stat_return_zscore_{period}"] = (returns - mean) / std
    result[f"stat_return_autocorr_1_{period}"] = returns.rolling(
        period, min_periods=period
    ).corr(returns.shift(1))
    path = frame["close"].diff().abs().rolling(period).sum()
    result[f"stat_efficiency_ratio_{period}"] = frame["close"].diff(period).abs() / path
    log_range = pd.Series(np.log(frame["high"] / frame["low"]), index=frame.index)
    result[f"stat_parkinson_variance_{period}"] = log_range.pow(2).rolling(period).mean() / (
        4 * np.log(2)
    )
    result[f"stat_price_min_{period}"] = frame["close"].rolling(
        period, min_periods=period
    ).min()
    result[f"stat_price_max_{period}"] = frame["close"].rolling(
        period, min_periods=period
    ).max()
    result[f"stat_price_median_{period}"] = frame["close"].rolling(
        period, min_periods=period
    ).median()
    result[f"stat_price_quantile_25_{period}"] = frame["close"].rolling(
        period, min_periods=period
    ).quantile(0.25)
    result[f"stat_price_quantile_75_{period}"] = frame["close"].rolling(
        period, min_periods=period
    ).quantile(0.75)
    return result
