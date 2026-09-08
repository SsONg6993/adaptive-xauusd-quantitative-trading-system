from __future__ import annotations

import pandas as pd

from axq.labels.base import LabelDefinition, ThresholdMode, TradeSide
from axq.labels.excursions import path_excursions


def direction_labels(frame: pd.DataFrame, definition: LabelDefinition) -> pd.DataFrame:
    horizon = definition.horizon_bars
    future = frame["close"].shift(-horizon)
    delta = future - frame["close"]
    if definition.threshold_mode == ThresholdMode.ABSOLUTE:
        movement = delta
    elif definition.threshold_mode == ThresholdMode.PERCENTAGE:
        movement = delta / frame["close"]
    else:
        movement = delta / frame[definition.atr_column]
    available = future.notna() & movement.notna()
    target = pd.Series(pd.NA, index=frame.index, dtype="string")
    target.loc[available & (movement > definition.neutral_threshold)] = "UP"
    target.loc[available & (movement < -definition.neutral_threshold)] = "DOWN"
    target.loc[available & (movement.abs() <= definition.neutral_threshold)] = "NEUTRAL"
    output = pd.DataFrame(
        {
            f"target_{definition.name}": target,
            f"label_{definition.name}_forward_delta": delta.where(available),
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
        side = TradeSide.LONG if delta.iloc[position] >= 0.0 else TradeSide.SHORT
        excursion_rows.append(
            path_excursions(frame, position, horizon, side=side, atr_value=atr_value)
        )
    excursions = pd.DataFrame(excursion_rows, index=frame.index).add_prefix(
        f"label_{definition.name}_"
    )
    return output.join(excursions)
