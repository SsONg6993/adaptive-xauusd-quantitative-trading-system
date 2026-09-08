from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
import pytest

from axq.features.indicators import atr, rsi, seeded_ema, sma, wma
from axq.features.momentum import momentum_features
from axq.features.volatility import volatility_features
from axq.features.volume import volume_features


def fixture() -> pd.DataFrame:
    close = pd.Series([9.0, 11.0, 12.0, 14.0, 13.0, 15.0, 16.0])
    return pd.DataFrame(
        {
            "open": close - 0.2,
            "high": [10.0, 12.0, 13.0, 15.0, 14.0, 16.0, 17.0],
            "low": [8.0, 9.0, 11.0, 12.0, 12.0, 13.0, 15.0],
            "close": close,
            "tick_volume": [10.0, 20.0, 15.0, 25.0, 20.0, 30.0, 35.0],
        }
    )


def test_moving_average_hand_calculated_fixture() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert sma(values, 3).iloc[2] == pytest.approx(2.0)
    assert wma(values, 3).iloc[2] == pytest.approx(14.0 / 6.0)
    assert seeded_ema(values, 3).tolist()[2:] == pytest.approx([2.0, 3.0, 4.0])
    assert sma(values, 3).iloc[:2].isna().all()


def test_wilder_rsi_and_atr_hand_calculated_fixtures() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 2.0])
    output = rsi(values, 2)
    assert output.iloc[:2].isna().all()
    assert output.iloc[2] == pytest.approx(100.0)
    assert output.iloc[3] == pytest.approx(50.0)
    average_range = atr(fixture().iloc[:4], 2)
    assert average_range.iloc[:2].isna().all()
    assert average_range.iloc[2] == pytest.approx(2.5)
    assert average_range.iloc[3] == pytest.approx(2.75)


def test_bollinger_population_std_and_realized_volatility() -> None:
    frame = fixture()
    output = volatility_features(
        frame, {"atr_period": 2, "rolling_period": 3, "bollinger_deviations": 2.0}
    )
    expected_mean = np.mean([9.0, 11.0, 12.0])
    expected_std = np.std([9.0, 11.0, 12.0], ddof=0)
    assert output.loc[2, "vol_bb_mid_3"] == pytest.approx(expected_mean)
    assert output.loc[2, "vol_bb_upper_3_2"] == pytest.approx(expected_mean + 2 * expected_std)
    log_returns = np.log(np.array([11.0 / 9.0, 12.0 / 11.0, 14.0 / 12.0]))
    assert output.loc[3, "vol_realized_3"] == pytest.approx(np.sqrt(np.sum(log_returns**2)))


def test_stochastic_williams_roc_cci_obv_mfi_smoke() -> None:
    frame = fixture()
    momentum = momentum_features(
        frame,
        {
            "rsi_period": 2,
            "macd_fast": 2,
            "macd_slow": 3,
            "macd_signal": 2,
            "stochastic_period": 3,
            "stochastic_smooth_k": 1,
            "stochastic_smooth_d": 1,
            "cci_period": 3,
            "roc_period": 2,
            "williams_period": 3,
        },
    )
    assert momentum.loc[2, "momentum_stoch_k_3_1_1"] == pytest.approx(80.0)
    assert momentum.loc[2, "momentum_williams_r_3"] == pytest.approx(-20.0)
    assert momentum.loc[2, "momentum_roc_2"] == pytest.approx(12.0 / 9.0 - 1.0)
    assert np.isfinite(momentum.loc[2, "momentum_cci_3"])
    volume = volume_features(frame, {"period": 3, "mfi_period": 2})
    assert volume["volume_obv"].tolist()[:4] == pytest.approx([0.0, 20.0, 35.0, 60.0])
    assert volume["volume_mfi_2"].iloc[2] == pytest.approx(100.0)


@pytest.mark.skipif(
    importlib.util.find_spec("talib") is None, reason="optional TA-Lib not installed"
)
def test_optional_talib_parity() -> None:
    import talib  # type: ignore[import-not-found,import-untyped]

    frame = fixture()
    close = frame["close"].to_numpy()
    np.testing.assert_allclose(seeded_ema(frame["close"], 3), talib.EMA(close, 3), equal_nan=True)
    np.testing.assert_allclose(rsi(frame["close"], 3), talib.RSI(close, 3), equal_nan=True)
    np.testing.assert_allclose(
        atr(frame, 3),
        talib.ATR(frame["high"], frame["low"], close, 3),
        equal_nan=True,
    )
