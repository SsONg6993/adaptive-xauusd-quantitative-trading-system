from __future__ import annotations

import pandas as pd

from axq.data.validation import REQUIRED_COLUMNS


def clean_candles(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize types/order and deterministically keep the last duplicate bar."""
    absent = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if absent:
        raise ValueError(f"Cannot clean frame; missing columns: {absent}")
    result = frame.copy()
    result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True, errors="raise")
    result = result.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    for column in ("open", "high", "low", "close", "tick_volume", "spread"):
        result[column] = pd.to_numeric(result[column], errors="raise")
    return result.reset_index(drop=True)
