from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from axq.labels import (
    BarrierMode,
    CollisionPolicy,
    LabelDefinition,
    LabelKind,
    ReturnMode,
    ThresholdMode,
    TradeSide,
    generate_labels,
)
from axq.labels.analysis import compare_label_definitions


def bars(close: list[float]) -> pd.DataFrame:
    values = np.asarray(close, dtype=float)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=len(values), freq="5min", tz="UTC"),
            "open": values,
            "high": values + 0.4,
            "low": values - 0.4,
            "close": values,
            "vol_atr_14": 2.0,
        }
    )


@pytest.mark.parametrize("horizon", [1, 3, 5, 10, 20])
def test_direction_horizons(horizon: int) -> None:
    frame = bars(list(range(100, 125)))
    definition = LabelDefinition(
        name=f"next_{horizon}", version="v1", kind=LabelKind.DIRECTION,
        horizon_bars=horizon, threshold_mode=ThresholdMode.ABSOLUTE,
    )
    target = generate_labels(frame, definition).frame[f"target_next_{horizon}"]
    assert target.iloc[0] == "UP"
    assert target.iloc[-horizon:].isna().all()


def test_direction_threshold_modes_and_neutral() -> None:
    frame = bars([100.0, 100.05, 100.4])
    percentage = LabelDefinition(
        name="pct", version="v1", kind=LabelKind.DIRECTION, horizon_bars=1,
        threshold_mode=ThresholdMode.PERCENTAGE, neutral_threshold=0.001,
    )
    atr_scaled = LabelDefinition(
        name="atr", version="v1", kind=LabelKind.DIRECTION, horizon_bars=1,
        threshold_mode=ThresholdMode.ATR, neutral_threshold=0.1,
    )
    assert generate_labels(frame, percentage).frame["target_pct"].iloc[0] == "NEUTRAL"
    assert generate_labels(frame, atr_scaled).frame["target_atr"].iloc[1] == "UP"


def test_forward_simple_log_and_atr_returns() -> None:
    frame = bars([100.0, 101.0, 102.0])
    simple = LabelDefinition(
        name="simple", version="v1", kind=LabelKind.FORWARD_RETURN, horizon_bars=2,
    )
    log = simple.model_copy(update={"name": "log", "return_mode": ReturnMode.LOG})
    atr = simple.model_copy(
        update={"name": "atr_return", "kind": LabelKind.ATR_ADJUSTED_RETURN}
    )
    assert generate_labels(frame, simple).frame["target_simple"].iloc[0] == pytest.approx(0.02)
    assert generate_labels(frame, log).frame["target_log"].iloc[0] == pytest.approx(
        np.log(1.02)
    )
    assert generate_labels(frame, atr).frame["target_atr_return"].iloc[0] == pytest.approx(1.0)


def barrier_definition(
    *,
    kind: LabelKind = LabelKind.TRIPLE_BARRIER,
    policy: CollisionPolicy = CollisionPolicy.AMBIGUOUS,
    side: TradeSide = TradeSide.LONG,
) -> LabelDefinition:
    return LabelDefinition(
        name="barrier", version="v1", kind=kind, horizon_bars=2,
        barrier_mode=BarrierMode.ABSOLUTE, upper_barrier=1.0, lower_barrier=1.0,
        collision_policy=policy, side=side,
    )


@pytest.mark.parametrize(
    ("high", "low", "expected"),
    [
        ([100.2, 101.2, 100.5], [99.8, 99.5, 99.5], "UPPER_FIRST"),
        ([100.2, 100.5, 100.5], [99.8, 98.8, 99.5], "LOWER_FIRST"),
        ([100.2, 100.5, 100.5], [99.8, 99.5, 99.5], "TIMEOUT"),
    ],
)
def test_triple_barrier_outcomes(
    high: list[float], low: list[float], expected: str
) -> None:
    frame = bars([100.0, 100.0, 100.0])
    frame["high"], frame["low"] = high, low
    output = generate_labels(frame, barrier_definition()).frame
    assert output["target_barrier"].iloc[0] == expected


@pytest.mark.parametrize(
    ("policy", "expected"),
    [
        (CollisionPolicy.AMBIGUOUS, "AMBIGUOUS"),
        (CollisionPolicy.PESSIMISTIC, "LOWER_FIRST"),
        (CollisionPolicy.OPTIMISTIC, "UPPER_FIRST"),
    ],
)
def test_same_bar_collision_policy(policy: CollisionPolicy, expected: str) -> None:
    frame = bars([100.0, 100.0, 100.0])
    frame.loc[1, ["high", "low"]] = [101.2, 98.8]
    output = generate_labels(frame, barrier_definition(policy=policy)).frame
    assert output["target_barrier"].iloc[0] == expected


def test_lower_timeframe_collision_resolution() -> None:
    frame = bars([100.0, 100.0, 100.0])
    frame.loc[1, ["high", "low"]] = [101.2, 98.8]
    lower = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-01-01 00:05Z", "2026-01-01 00:06Z"]),
            "high": [100.5, 101.2],
            "low": [99.5, 99.5],
        }
    )
    definition = barrier_definition(policy=CollisionPolicy.LOWER_TIMEFRAME)
    assert generate_labels(
        frame, definition, lower_timeframe=lower
    ).frame["target_barrier"].iloc[0] == "UPPER_FIRST"


def test_tp_before_sl_and_mfe_mae() -> None:
    frame = bars([100.0, 100.0, 100.0])
    frame["high"] = [100.2, 101.2, 100.4]
    frame["low"] = [99.8, 99.5, 99.7]
    definition = barrier_definition(kind=LabelKind.TP_BEFORE_SL)
    output = generate_labels(frame, definition).frame
    assert output["target_barrier"].iloc[0] == "TP_FIRST"
    assert output["label_barrier_mfe_raw"].iloc[0] == pytest.approx(1.2)
    assert output["label_barrier_mae_raw"].iloc[0] == pytest.approx(0.5)
    assert output["label_barrier_mfe_r"].iloc[0] == pytest.approx(1.2)


def test_label_sensitivity_reports_without_rebalancing() -> None:
    frame = bars(list(range(100, 110)))
    definitions = [
        LabelDefinition(
            name=f"horizon_{horizon}", version="v1", kind=LabelKind.DIRECTION,
            horizon_bars=horizon,
        )
        for horizon in (1, 3, 5)
    ]
    report = compare_label_definitions(frame, definitions)
    assert set(report["label_name"]) == {"horizon_1", "horizon_3", "horizon_5"}
    assert set(report["outcome"]) == {"UP"}
