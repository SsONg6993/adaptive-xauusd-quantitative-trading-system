from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from axq.features.indicators import money_flow_index


def volume_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    period = int(params.get("period", 20))
    delta = frame["close"].diff()
    direction = delta.gt(0.0).astype(float) - delta.lt(0.0).astype(float)
    signed = direction * frame["tick_volume"].astype(float)
    average = frame["tick_volume"].rolling(period, min_periods=period).mean()
    result = pd.DataFrame(index=frame.index)
    result["volume_obv"] = signed.cumsum()
    if len(result):
        result.loc[result.index[0], "volume_obv"] = 0.0
    result[f"volume_relative_{period}"] = frame["tick_volume"] / average
    result[f"volume_roc_{period}"] = frame["tick_volume"].pct_change(
        period, fill_method=None
    )
    mfi_period = int(params.get("mfi_period", 14))
    result[f"volume_mfi_{mfi_period}"] = money_flow_index(frame, mfi_period)
    return result
