"""Guards that force future preprocessing components to fit on training rows only."""

from __future__ import annotations

from typing import Any, Protocol

import pandas as pd

from axq.datasets.splits import SplitFold


class FitTransformComponent(Protocol):
    def fit(self, values: pd.DataFrame) -> Any: ...


def fit_on_training_only(
    component: FitTransformComponent,
    frame: pd.DataFrame,
    *,
    fold: SplitFold,
    feature_columns: list[str],
) -> Any:
    if fold.train.stop > len(frame):
        raise ValueError("Training boundary exceeds frame")
    training = frame.iloc[fold.train.start : fold.train.stop][feature_columns]
    if training.empty:
        raise ValueError("Training split is empty")
    return component.fit(training)
