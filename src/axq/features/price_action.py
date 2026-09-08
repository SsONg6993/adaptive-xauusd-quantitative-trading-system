from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


def price_action_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    del params
    candle_range = (frame["high"] - frame["low"]).replace(0, np.nan)
    body = frame["close"] - frame["open"]
    absolute_body = body.abs()
    result = pd.DataFrame(index=frame.index)
    result["pa_body"] = body
    result["pa_body_pct"] = absolute_body / candle_range
    result["pa_upper_wick"] = frame["high"] - frame[["open", "close"]].max(axis=1)
    result["pa_lower_wick"] = frame[["open", "close"]].min(axis=1) - frame["low"]
    result["pa_range"] = candle_range
    result["pa_direction"] = np.sign(body).astype("int8")
    result["pa_gap"] = frame["open"] - frame["close"].shift(1)
    result["pa_return_1"] = frame["close"].pct_change(fill_method=None)
    result["pa_log_return_1"] = np.log(frame["close"] / frame["close"].shift(1))
    previous_high = frame["high"].shift(1)
    previous_low = frame["low"].shift(1)
    result["pa_higher_high"] = (frame["high"] > previous_high).where(
        previous_high.notna()
    ).astype("Float64")
    result["pa_higher_low"] = (frame["low"] > previous_low).where(
        previous_low.notna()
    ).astype("Float64")
    return result
