"""Small fit-boundary scaffold for leakage-safe downstream preprocessing."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FittedStandardizer:
    columns: tuple[str, ...]
    mean: pd.Series
    scale: pd.Series
    train_end_exclusive: int

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        missing = set(self.columns) - set(frame.columns)
        if missing:
            raise ValueError(f"Missing columns for transform: {sorted(missing)}")
        return (frame.loc[:, list(self.columns)] - self.mean) / self.scale


def fit_standardizer(
    frame: pd.DataFrame, *, columns: list[str], train_end_exclusive: int
) -> FittedStandardizer:
    if not 0 < train_end_exclusive <= len(frame):
        raise ValueError("train_end_exclusive must define a non-empty in-frame prefix")
    training = frame.iloc[:train_end_exclusive][columns].astype(float)
    mean = training.mean()
    scale = training.std(ddof=0).replace(0.0, np.nan)
    return FittedStandardizer(tuple(columns), mean, scale, train_end_exclusive)
