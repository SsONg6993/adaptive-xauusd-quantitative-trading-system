"""Future-path excursion calculations for labels only."""

from __future__ import annotations

import numpy as np
import pandas as pd

from axq.labels.base import TradeSide


def path_excursions(
    frame: pd.DataFrame,
    position: int,
    horizon: int,
    *,
    side: TradeSide,
    atr_value: float | None,
    risk_distance: float | None = None,
) -> dict[str, float]:
    entry = float(frame["close"].iloc[position])
    future = frame.iloc[position + 1 : position + horizon + 1]
    if len(future) < horizon:
        return {}
    if side == TradeSide.LONG:
        favorable = float(future["high"].max()) - entry
        adverse = entry - float(future["low"].min())
    else:
        favorable = entry - float(future["low"].min())
        adverse = float(future["high"].max()) - entry
    atr = atr_value if atr_value is not None and np.isfinite(atr_value) and atr_value > 0 else None
    risk = risk_distance if risk_distance is not None and risk_distance > 0 else None
    return {
        "mfe_raw": favorable,
        "mae_raw": adverse,
        "mfe_percent": favorable / entry,
        "mae_percent": adverse / entry,
        "mfe_atr": favorable / atr if atr else np.nan,
        "mae_atr": adverse / atr if atr else np.nan,
        "mfe_r": favorable / risk if risk else np.nan,
        "mae_r": adverse / risk if risk else np.nan,
    }
