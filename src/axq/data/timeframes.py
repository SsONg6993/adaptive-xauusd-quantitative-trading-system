from __future__ import annotations

from datetime import timedelta

TIMEFRAME_MINUTES = {"M5": 5, "M15": 15, "H1": 60, "H4": 240}


def timeframe_delta(timeframe: str) -> timedelta:
    try:
        return timedelta(minutes=TIMEFRAME_MINUTES[timeframe.upper()])
    except KeyError as exc:
        raise ValueError(f"Unsupported timeframe: {timeframe}") from exc
