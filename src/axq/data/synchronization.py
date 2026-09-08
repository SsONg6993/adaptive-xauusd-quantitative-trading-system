"""Leakage-safe multi-timeframe alignment."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from axq.data.timeframes import timeframe_delta


def synchronize_completed_bars(
    frames: Mapping[str, pd.DataFrame], *, base_timeframe: str = "M5"
) -> pd.DataFrame:
    """Attach bars only when their UTC close time is at/before the base bar's UTC open.

    MT5 timestamps identify candle opens. Naive timestamps are explicitly interpreted as UTC.
    Retained available-at columns provide an auditable point-in-time boundary.
    """
    base_key = base_timeframe.upper()
    if base_key not in frames:
        raise ValueError(f"Missing base timeframe {base_key}")
    result = frames[base_key].copy().sort_values("timestamp")
    result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True)
    base_delta = timeframe_delta(base_key)

    for timeframe, raw in sorted(frames.items()):
        key = timeframe.upper()
        if key == base_key:
            continue
        if timeframe_delta(key) <= base_delta:
            raise ValueError(f"{key} is not higher than base timeframe {base_key}")
        higher = raw.copy().sort_values("timestamp")
        higher["timestamp"] = pd.to_datetime(higher["timestamp"], utc=True)
        if higher["timestamp"].duplicated().any():
            raise ValueError(f"Duplicate {key} timestamps cannot be synchronized")
        available_column = f"available_at_{key.lower()}"
        source_column = f"source_open_{key.lower()}"
        higher[source_column] = higher["timestamp"]
        higher[available_column] = higher["timestamp"] + pd.Timedelta(timeframe_delta(key))
        values = [
            column
            for column in higher.columns
            if column not in {"timestamp", available_column, source_column}
        ]
        higher = higher[[available_column, source_column, *values]].rename(
            columns={column: f"{column}_{key.lower()}" for column in values}
        )
        result = pd.merge_asof(
            result.sort_values("timestamp"),
            higher.sort_values(available_column),
            left_on="timestamp",
            right_on=available_column,
            direction="backward",
            allow_exact_matches=True,
        )
    return result
