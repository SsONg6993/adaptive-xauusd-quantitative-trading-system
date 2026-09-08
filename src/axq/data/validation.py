"""Fail-loud OHLCV validation; repair is an explicit separate step."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from axq.data.timeframes import timeframe_delta

REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "tick_volume", "spread")


@dataclass(frozen=True)
class ValidationReport:
    rows: int
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    missing_intervals: int = 0

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_candles(frame: pd.DataFrame, timeframe: str) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    if missing:
        return ValidationReport(len(frame), (f"missing columns: {missing}",))
    if frame.empty:
        return ValidationReport(0, ("dataset is empty",))

    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if timestamps.isna().any():
        errors.append("invalid timestamps")
    if timestamps.duplicated().any():
        errors.append(f"duplicate timestamps: {int(timestamps.duplicated().sum())}")
    if not timestamps.is_monotonic_increasing:
        errors.append("timestamps are not strictly chronological")

    numeric = frame[["open", "high", "low", "close", "tick_volume", "spread"]]
    if numeric.isna().any().any():
        errors.append("null values in market fields")
    if (frame["high"] < frame[["open", "close", "low"]].max(axis=1)).any():
        errors.append("high is below another OHLC value")
    if (frame["low"] > frame[["open", "close", "high"]].min(axis=1)).any():
        errors.append("low is above another OHLC value")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        errors.append("non-positive price")
    if (frame[["tick_volume", "spread"]] < 0).any().any():
        errors.append("negative volume or spread")

    expected = pd.Timedelta(timeframe_delta(timeframe))
    diffs = timestamps.diff().dropna()
    missing_intervals = int(((diffs / expected).floordiv(1).sub(1)).clip(lower=0).sum())
    if missing_intervals:
        message = f"{missing_intervals} grid intervals absent; "
        warnings.append(message + "expected market closures must be classified downstream")
    return ValidationReport(len(frame), tuple(errors), tuple(warnings), missing_intervals)
