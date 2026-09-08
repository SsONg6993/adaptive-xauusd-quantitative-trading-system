"""Causal technical-indicator primitives with explicit warm-up semantics.

All rolling windows are right aligned.  Recursive averages use an SMA seed, matching
Wilder/TA-Lib conventions instead of pandas' first-observation EWM seed.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _validate_period(period: int) -> None:
    if period < 1:
        raise ValueError("period must be positive")


def sma(values: pd.Series, period: int) -> pd.Series:
    _validate_period(period)
    return values.astype(float).rolling(period, min_periods=period).mean()


def wma(values: pd.Series, period: int) -> pd.Series:
    _validate_period(period)
    weights = np.arange(1.0, period + 1.0)
    denominator = float(weights.sum())
    return values.astype(float).rolling(period, min_periods=period).apply(
        lambda window: float(np.dot(window, weights) / denominator), raw=True
    )


def seeded_ema(values: pd.Series, period: int) -> pd.Series:
    """EMA seeded with the first period's SMA; invalid until index period-1."""
    _validate_period(period)
    array = values.astype(float).to_numpy()
    output = np.full(len(array), np.nan, dtype=float)
    if len(array) < period:
        return pd.Series(output, index=values.index, dtype=float)
    alpha = 2.0 / (period + 1.0)
    for seed_end in range(period - 1, len(array)):
        seed = array[seed_end - period + 1 : seed_end + 1]
        if np.isfinite(seed).all():
            output[seed_end] = float(seed.mean())
            for index in range(seed_end + 1, len(array)):
                current = array[index]
                if not math.isfinite(current):
                    break
                output[index] = output[index - 1] + alpha * (current - output[index - 1])
            break
    return pd.Series(output, index=values.index, dtype=float)


def wilder_average(values: pd.Series, period: int) -> pd.Series:
    """Wilder average (RMA): SMA seed followed by alpha=1/period recursion."""
    _validate_period(period)
    array = values.astype(float).to_numpy()
    output = np.full(len(array), np.nan, dtype=float)
    if len(array) < period:
        return pd.Series(output, index=values.index, dtype=float)
    alpha = 1.0 / period
    for seed_end in range(period - 1, len(array)):
        seed = array[seed_end - period + 1 : seed_end + 1]
        if np.isfinite(seed).all():
            output[seed_end] = float(seed.mean())
            for index in range(seed_end + 1, len(array)):
                current = array[index]
                if not math.isfinite(current):
                    break
                output[index] = output[index - 1] + alpha * (current - output[index - 1])
            break
    return pd.Series(output, index=values.index, dtype=float)


def true_range(frame: pd.DataFrame) -> pd.Series:
    previous_close = frame["close"].shift(1)
    return pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1, skipna=True)


def atr(frame: pd.DataFrame, period: int) -> pd.Series:
    # TA-Lib/Wilder excludes the first bar's H-L because no previous close exists.
    ranges = true_range(frame).astype(float)
    if len(ranges):
        ranges.iloc[0] = np.nan
    return wilder_average(ranges, period)


def rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.astype(float).diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    average_gain = wilder_average(gain, period)
    average_loss = wilder_average(loss, period)
    denominator = average_gain + average_loss
    result = 100.0 * average_gain / denominator
    result = result.mask((average_loss == 0.0) & (average_gain > 0.0), 100.0)
    result = result.mask((average_gain == 0.0) & (average_loss > 0.0), 0.0)
    return result.mask(denominator == 0.0, 0.0)


def directional_movement(
    frame: pd.DataFrame, period: int
) -> tuple[pd.Series, pd.Series, pd.Series]:
    up = frame["high"].diff()
    down = -frame["low"].diff()
    plus_dm = up.where((up > down) & (up > 0.0), 0.0)
    minus_dm = down.where((down > up) & (down > 0.0), 0.0)
    if len(plus_dm):
        plus_dm.iloc[0] = np.nan
        minus_dm.iloc[0] = np.nan
    average_tr = atr(frame, period)
    plus_di = 100.0 * wilder_average(plus_dm, period) / average_tr
    minus_di = 100.0 * wilder_average(minus_dm, period) / average_tr
    total = plus_di + minus_di
    dx = (100.0 * (plus_di - minus_di).abs() / total).mask(total == 0.0, 0.0)
    adx = wilder_average(dx, period)
    return plus_di, minus_di, adx


def stochastic(
    frame: pd.DataFrame, period: int, smooth_k: int, smooth_d: int
) -> tuple[pd.Series, pd.Series]:
    lowest = frame["low"].rolling(period, min_periods=period).min()
    highest = frame["high"].rolling(period, min_periods=period).max()
    width = highest - lowest
    fast_k = (100.0 * (frame["close"] - lowest) / width).mask(width == 0.0)
    slow_k = sma(fast_k, smooth_k)
    return slow_k, sma(slow_k, smooth_d)


def cci(frame: pd.DataFrame, period: int) -> pd.Series:
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    center = sma(typical, period)
    deviation = typical.rolling(period, min_periods=period).apply(
        lambda window: float(np.mean(np.abs(window - np.mean(window)))), raw=True
    )
    return ((typical - center) / (0.015 * deviation)).mask(deviation == 0.0)


def money_flow_index(frame: pd.DataFrame, period: int) -> pd.Series:
    typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
    raw_flow = typical * frame["tick_volume"].astype(float)
    direction = typical.diff()
    positive = raw_flow.where(direction > 0.0, 0.0)
    negative = raw_flow.where(direction < 0.0, 0.0)
    if len(positive):
        positive.iloc[0] = np.nan
        negative.iloc[0] = np.nan
    positive_sum = positive.rolling(period, min_periods=period).sum()
    negative_sum = negative.rolling(period, min_periods=period).sum()
    total = positive_sum + negative_sum
    result = 100.0 * positive_sum / total
    return result.mask(total == 0.0)


def aroon(frame: pd.DataFrame, period: int) -> tuple[pd.Series, pd.Series]:
    # Include the current bar plus `period` preceding intervals, as TA-Lib does.
    window = period + 1
    up = frame["high"].rolling(window, min_periods=window).apply(
        lambda values: 100.0
        * float(len(values) - 1 - np.argmax(values[::-1]))
        / period,
        raw=True,
    )
    down = frame["low"].rolling(window, min_periods=window).apply(
        lambda values: 100.0
        * float(len(values) - 1 - np.argmin(values[::-1]))
        / period,
        raw=True,
    )
    return up, down


def supertrend(
    frame: pd.DataFrame, period: int, multiplier: float
) -> tuple[pd.Series, pd.Series, pd.Series]:
    average_range = atr(frame, period)
    midpoint = (frame["high"] + frame["low"]) / 2.0
    basic_upper = midpoint + multiplier * average_range
    basic_lower = midpoint - multiplier * average_range
    upper = np.full(len(frame), np.nan)
    lower = np.full(len(frame), np.nan)
    line = np.full(len(frame), np.nan)
    direction = np.full(len(frame), np.nan)
    close = frame["close"].to_numpy(dtype=float)
    bu = basic_upper.to_numpy(dtype=float)
    bl = basic_lower.to_numpy(dtype=float)
    for index in range(len(frame)):
        if not (math.isfinite(bu[index]) and math.isfinite(bl[index])):
            continue
        if index == 0 or not math.isfinite(upper[index - 1]):
            upper[index], lower[index] = bu[index], bl[index]
            direction[index] = 1.0
        else:
            upper[index] = (
                bu[index]
                if bu[index] < upper[index - 1] or close[index - 1] > upper[index - 1]
                else upper[index - 1]
            )
            lower[index] = (
                bl[index]
                if bl[index] > lower[index - 1] or close[index - 1] < lower[index - 1]
                else lower[index - 1]
            )
            previous_direction = direction[index - 1]
            if previous_direction < 0.0 and close[index] > upper[index]:
                direction[index] = 1.0
            elif previous_direction > 0.0 and close[index] < lower[index]:
                direction[index] = -1.0
            else:
                direction[index] = previous_direction
        line[index] = lower[index] if direction[index] > 0.0 else upper[index]
    idx = frame.index
    return (
        pd.Series(line, index=idx, dtype=float),
        pd.Series(direction, index=idx, dtype=float),
        average_range,
    )
