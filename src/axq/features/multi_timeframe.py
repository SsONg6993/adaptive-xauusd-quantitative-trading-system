from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd


def multi_timeframe_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    del params
    result = pd.DataFrame(index=frame.index)
    for timeframe in ("m15", "h1", "h4"):
        column = f"close_{timeframe}"
        if column in frame:
            result[f"mtf_close_ratio_{timeframe}"] = frame[column] / frame["close"] - 1.0
    return result
