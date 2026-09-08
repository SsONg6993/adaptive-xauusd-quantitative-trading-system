from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from axq.features.indicators import cci, rsi, seeded_ema, stochastic


def momentum_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    result = pd.DataFrame(index=frame.index)
    rsi_period = int(params.get("rsi_period", 14))
    result[f"momentum_rsi_{rsi_period}"] = rsi(frame["close"], rsi_period)
    fast_period = int(params.get("macd_fast", 12))
    slow_period = int(params.get("macd_slow", 26))
    signal_period = int(params.get("macd_signal", 9))
    fast = seeded_ema(frame["close"], fast_period)
    slow = seeded_ema(frame["close"], slow_period)
    macd = fast - slow
    signal = seeded_ema(macd, signal_period)
    suffix = f"{fast_period}_{slow_period}_{signal_period}"
    result[f"momentum_macd_{suffix}"] = macd
    result[f"momentum_macd_signal_{suffix}"] = signal
    result[f"momentum_macd_hist_{suffix}"] = macd - signal
    stochastic_period = int(params.get("stochastic_period", 14))
    smooth_k = int(params.get("stochastic_smooth_k", 3))
    smooth_d = int(params.get("stochastic_smooth_d", 3))
    stoch_k, stoch_d = stochastic(frame, stochastic_period, smooth_k, smooth_d)
    stoch_suffix = f"{stochastic_period}_{smooth_k}_{smooth_d}"
    result[f"momentum_stoch_k_{stoch_suffix}"] = stoch_k
    result[f"momentum_stoch_d_{stoch_suffix}"] = stoch_d
    cci_period = int(params.get("cci_period", 20))
    result[f"momentum_cci_{cci_period}"] = cci(frame, cci_period)
    roc_period = int(params.get("roc_period", 10))
    result[f"momentum_roc_{roc_period}"] = frame["close"].pct_change(
        roc_period, fill_method=None
    )
    williams_period = int(params.get("williams_period", 14))
    high = frame["high"].rolling(williams_period, min_periods=williams_period).max()
    low = frame["low"].rolling(williams_period, min_periods=williams_period).min()
    width = high - low
    result[f"momentum_williams_r_{williams_period}"] = (
        -100.0 * (high - frame["close"]) / width
    ).mask(width == 0.0)
    return result
