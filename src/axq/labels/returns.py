from __future__ import annotations

import numpy as np
import pandas as pd

from axq.labels.base import LabelDefinition, LabelKind, ReturnMode, TradeSide
from axq.labels.excursions import path_excursions


def forward_return_labels(frame: pd.DataFrame, definition: LabelDefinition) -> pd.DataFrame:
    horizon = definition.horizon_bars
    future = frame["close"].shift(-horizon)
    simple = future / frame["close"] - 1.0
    if definition.kind == LabelKind.ATR_ADJUSTED_RETURN or definition.return_mode == ReturnMode.ATR:
        target = (future - frame["close"]) / frame[definition.atr_column]
    elif definition.return_mode == ReturnMode.LOG:
        target = pd.Series(
            np.log(future / frame["close"]), index=frame.index, dtype=float
        )
    else:
        target = simple
    output = pd.DataFrame(
        {
            f"target_{definition.name}": target,
            f"label_{definition.name}_simple_return": simple,
            f"label_{definition.name}_log_return": np.log(future / frame["close"]),
        },
        index=frame.index,
    )
    excursion_rows: list[dict[str, float]] = []
    for position in range(len(frame)):
        atr_value = (
            float(frame[definition.atr_column].iloc[position])
            if definition.atr_column in frame
            else None
        )
        excursion_rows.append(
            path_excursions(
                frame, position, horizon, side=TradeSide.LONG, atr_value=atr_value
            )
        )
    excursions = pd.DataFrame(excursion_rows, index=frame.index).add_prefix(
        f"label_{definition.name}_"
    )
    return output.join(excursions)
