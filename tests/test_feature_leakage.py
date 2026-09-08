from __future__ import annotations

import numpy as np
import pandas as pd

from axq.data.synchronization import synchronize_completed_bars
from axq.features import default_registry
from axq.features.preprocessing import fit_standardizer

GROUPS = [
    "price_action", "trend", "momentum", "volatility", "volume", "breakout",
    "statistical", "session", "market_structure", "multi_timeframe",
]


def candles(rows: int = 120, frequency: str = "5min") -> pd.DataFrame:
    x = np.arange(rows, dtype=float)
    close = 2600.0 + 0.04 * x + np.sin(x / 3.0)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-05", periods=rows, freq=frequency, tz="UTC"),
            "open": close - 0.1,
            "high": close + 0.5 + 0.1 * np.cos(x),
            "low": close - 0.5 - 0.1 * np.sin(x),
            "close": close,
            "tick_volume": 100 + x % 17,
            "spread": 20,
        }
    )


def test_prefix_invariance_and_future_candle_mutation() -> None:
    registry = default_registry()
    source = candles(260)
    full = registry.compute(source, enabled_groups=GROUPS)
    prefix = registry.compute(source.iloc[:180], enabled_groups=GROUPS)
    pd.testing.assert_frame_equal(full.iloc[:180], prefix)
    mutated = source.copy()
    mutated.loc[180:, ["open", "high", "low", "close"]] *= 1.7
    changed = registry.compute(mutated, enabled_groups=GROUPS)
    pd.testing.assert_frame_equal(full.iloc[:180], changed.iloc[:180])


def test_rolling_window_is_right_aligned() -> None:
    registry = default_registry()
    original = candles(60)
    baseline = registry.compute(original, enabled_groups=["statistical", "volatility"])
    mutated = original.copy()
    mutated.loc[31:, "close"] += 1000.0
    changed = registry.compute(mutated, enabled_groups=["statistical", "volatility"])
    pd.testing.assert_frame_equal(baseline.iloc[:31], changed.iloc[:31])


def test_scaler_fit_boundary_scaffolding() -> None:
    frame = pd.DataFrame({"feature": [1.0, 2.0, 3.0, 1000.0]})
    first = fit_standardizer(frame, columns=["feature"], train_end_exclusive=3)
    mutated = frame.copy()
    mutated.loc[3, "feature"] = -1000.0
    second = fit_standardizer(mutated, columns=["feature"], train_end_exclusive=3)
    pd.testing.assert_series_equal(first.mean, second.mean)
    pd.testing.assert_series_equal(first.scale, second.scale)


def test_multi_timeframe_future_bar_and_all_boundaries() -> None:
    m5 = candles(61)
    m15 = candles(20, "15min")
    h1 = candles(5, "1h")
    h4 = candles(2, "4h")
    synced = synchronize_completed_bars({"M5": m5, "M15": m15, "H1": h1, "H4": h4})
    assert pd.isna(synced.loc[2, "close_m15"])
    assert synced.loc[3, "available_at_m15"] == pd.Timestamp("2026-01-05 00:15:00Z")
    assert pd.isna(synced.loc[11, "close_h1"])
    assert synced.loc[12, "available_at_h1"] == pd.Timestamp("2026-01-05 01:00:00Z")
    assert pd.isna(synced.loc[47, "close_h4"])
    assert synced.loc[48, "available_at_h4"] == pd.Timestamp("2026-01-05 04:00:00Z")
    changed_h1 = h1.copy()
    changed_h1.loc[1:, "close"] += 900.0
    mutated = synchronize_completed_bars(
        {"M5": m5, "M15": m15, "H1": changed_h1, "H4": h4}
    )
    pd.testing.assert_series_equal(synced.loc[:23, "close_h1"], mutated.loc[:23, "close_h1"])


def test_swing_confirmation_is_delayed_and_not_backdated() -> None:
    frame = candles(9)
    frame["high"] = [1, 2, 5, 3, 2, 3, 6, 4, 3]
    frame["low"] = [0, 0, 1, 1, -2, 0, 1, 0, 0]
    frame["close"] = (frame["high"] + frame["low"]) / 2
    output = default_registry().compute(
        frame,
        enabled_groups=["market_structure"],
        parameters={"market_structure_v1": {"left_bars": 2, "right_bars": 2, "level_lookback": 3,
                                              "atr_period": 2}},
    )
    assert output["structure_swing_high_confirmed"].iloc[:4].isna().all()
    assert output.loc[4, "structure_swing_high_confirmed"] == 5
    assert output.loc[4, "structure_swing_confirmation_delay"] == 2
    assert output.loc[6, "structure_swing_low_confirmed"] == -2


def test_labels_are_not_feature_inputs() -> None:
    source = candles(80)
    source["label_forward_return"] = np.arange(len(source))
    registry = default_registry()
    baseline = registry.compute(source, enabled_groups=GROUPS)
    mutated = source.copy()
    mutated["label_forward_return"] *= -999
    changed = registry.compute(mutated, enabled_groups=GROUPS)
    generated = [column for column in baseline if column not in source.columns]
    pd.testing.assert_frame_equal(baseline[generated], changed[generated])
    manifest = registry.manifest(feature_set_version="test", enabled_groups=GROUPS)
    assert all(
        not any(column.startswith(("label", "target")) for column in entry.required_source_columns)
        for entry in manifest.entries
    )
