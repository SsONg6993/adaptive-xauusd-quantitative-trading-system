"""Pure, bounded market-history quality inspection."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

TIMEFRAME_MINUTES = {"M5": 5, "M15": 15, "H1": 60, "H4": 240}


def _timestamp_column(frame: pd.DataFrame) -> str:
    for candidate in ("timestamp", "time", "candle_open_timestamp"):
        if candidate in frame.columns:
            return candidate
    raise ValueError("History frame has no timestamp column")


def inspect_history_frames(
    frames: Mapping[str, pd.DataFrame],
    *,
    now: datetime | None = None,
    abnormal_spread: float | None = None,
) -> dict[str, Any]:
    """Inspect already-bounded broker frames without fetching additional history."""
    observed_at = now or datetime.now(UTC)
    if observed_at.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    results: dict[str, Any] = {}
    for timeframe, frame in frames.items():
        if timeframe not in TIMEFRAME_MINUTES:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        timestamp_name = _timestamp_column(frame)
        raw_timestamps = frame[timestamp_name]
        timestamps = pd.to_datetime(raw_timestamps, utc=True, errors="coerce")
        unique = timestamps.dropna().drop_duplicates().sort_values()
        interval = timedelta(minutes=TIMEFRAME_MINUTES[timeframe])
        gaps = unique.diff().dropna()
        invalid_ohlc = pd.Series(False, index=frame.index)
        if {"open", "high", "low", "close"} <= set(frame.columns):
            prices = frame[["open", "high", "low", "close"]].apply(
                pd.to_numeric, errors="coerce"
            )
            invalid_ohlc = (
                prices.isna().any(axis=1)
                | (prices["high"] < prices[["open", "close"]].max(axis=1))
                | (prices["low"] > prices[["open", "close"]].min(axis=1))
                | (prices["high"] < prices["low"])
                | (prices <= 0).any(axis=1)
            )
        volume = (
            pd.to_numeric(frame["tick_volume"], errors="coerce")
            if "tick_volume" in frame
            else None
        )
        spread = (
            pd.to_numeric(frame["spread"], errors="coerce")
            if "spread" in frame
            else None
        )
        latest = unique.iloc[-1] if len(unique) else None
        timezone_aware_input = isinstance(raw_timestamps.dtype, pd.DatetimeTZDtype)
        results[timeframe] = {
            "rows": len(frame),
            "earliest_bar": None if latest is None else unique.iloc[0].isoformat(),
            "latest_bar": None if latest is None else latest.isoformat(),
            "latest_bar_completed": bool(
                latest is not None
                and latest + interval <= pd.Timestamp(observed_at).tz_convert("UTC")
            ),
            "timestamps_are_utc": bool(
                timezone_aware_input
                and str(getattr(raw_timestamps.dt, "tz", "")) in {"UTC", "utc"}
            ),
            "invalid_timestamps": int(timestamps.isna().sum()),
            "duplicate_bars": int(timestamps.duplicated().sum()),
            "major_gaps": int((gaps > interval * 1.5).sum()),
            "largest_gap_minutes": float(gaps.max().total_seconds() / 60.0)
            if len(gaps)
            else 0.0,
            "ohlc_invalid_rows": int(invalid_ohlc.sum()),
            "tick_volume_available": volume is not None,
            "zero_tick_volume": int((volume <= 0).sum()) if volume is not None else None,
            "spread_available": spread is not None,
            "abnormal_spread_rows": int((spread > abnormal_spread).sum())
            if spread is not None and abnormal_spread is not None
            else None,
            "infinite_numeric_values": int(
                np.isinf(frame.select_dtypes(include="number").to_numpy(dtype=float)).sum()
            ),
        }
    return {
        "observed_at_utc": pd.Timestamp(observed_at).tz_convert("UTC").isoformat(),
        "timeframes": results,
    }
