"""DST-aware session features. Source timestamps are interpreted as UTC."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import time
from typing import Any

import pandas as pd


def _local_window(timestamp: pd.Series, timezone: str, start: time, end: time) -> pd.Series:
    local = timestamp.dt.tz_convert(timezone)
    minutes = local.dt.hour * 60 + local.dt.minute
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    result: pd.Series = (
        (minutes >= start_minutes) & (minutes < end_minutes) & (local.dt.dayofweek < 5)
    )
    return result


def session_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    del params
    timestamp = pd.to_datetime(frame["timestamp"], utc=True)
    asia = _local_window(timestamp, "Asia/Tokyo", time(9), time(17))
    london = _local_window(timestamp, "Europe/London", time(8), time(17))
    new_york = _local_window(timestamp, "America/New_York", time(8), time(17))
    result = pd.DataFrame(index=frame.index)
    result["session_hour_utc"] = timestamp.dt.hour
    result["session_day_of_week"] = timestamp.dt.dayofweek
    result["session_asia"] = asia.astype("int8")
    result["session_london"] = london.astype("int8")
    result["session_new_york"] = new_york.astype("int8")
    result["session_london_ny_overlap"] = (london & new_york).astype("int8")
    return result
