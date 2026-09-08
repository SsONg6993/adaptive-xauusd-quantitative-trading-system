from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from axq.features.indicators import aroon, directional_movement, seeded_ema, sma, supertrend, wma


def trend_features(frame: pd.DataFrame, params: Mapping[str, Any]) -> pd.DataFrame:
    periods = [int(value) for value in params.get("ma_periods", [20, 50, 200])]
    result = pd.DataFrame(index=frame.index)
    for period in periods:
        for name, average in (
            ("sma", sma(frame["close"], period)),
            ("ema", seeded_ema(frame["close"], period)),
            ("wma", wma(frame["close"], period)),
        ):
            result[f"trend_{name}_{period}"] = average
            result[f"trend_close_to_{name}_{period}"] = frame["close"] / average - 1.0

    dmi_period = int(params.get("dmi_period", 14))
    plus_di, minus_di, adx = directional_movement(frame, dmi_period)
    result[f"trend_plus_di_{dmi_period}"] = plus_di
    result[f"trend_minus_di_{dmi_period}"] = minus_di
    result[f"trend_adx_{dmi_period}"] = adx

    aroon_period = int(params.get("aroon_period", 14))
    aroon_up, aroon_down = aroon(frame, aroon_period)
    result[f"trend_aroon_up_{aroon_period}"] = aroon_up
    result[f"trend_aroon_down_{aroon_period}"] = aroon_down
    result[f"trend_aroon_osc_{aroon_period}"] = aroon_up - aroon_down

    supertrend_period = int(params.get("supertrend_period", 10))
    multiplier = float(params.get("supertrend_multiplier", 3.0))
    line, direction, _ = supertrend(frame, supertrend_period, multiplier)
    suffix = f"{supertrend_period}_{multiplier:g}"
    result[f"trend_supertrend_{suffix}"] = line
    result[f"trend_supertrend_direction_{suffix}"] = direction
    result[f"trend_close_to_supertrend_{suffix}"] = frame["close"] / line - 1.0

    slope_period = int(params.get("slope_period", 10))
    result[f"trend_velocity_{slope_period}"] = frame["close"].pct_change(
        slope_period, fill_method=None
    )
    return result
