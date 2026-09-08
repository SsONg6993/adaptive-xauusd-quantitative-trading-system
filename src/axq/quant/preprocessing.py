"""Training-only feature selection, imputation, and scaling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler, StandardScaler  # type: ignore[import-untyped]

from axq.quant.config import FeatureSelectionConfig, PreprocessingConfig
from axq.versioning import canonical_hash


@dataclass
class FrozenPreprocessor:
    config: PreprocessingConfig
    selection: FeatureSelectionConfig
    input_features: list[str]
    selected_features: list[str]
    medians: pd.Series | None
    scaler: StandardScaler | RobustScaler | None
    fit_row_count: int
    unavailable_training_features: list[str]

    @classmethod
    def fit(
        cls,
        frame: pd.DataFrame,
        features: list[str],
        config: PreprocessingConfig,
        selection: FeatureSelectionConfig,
    ) -> FrozenPreprocessor:
        if not features:
            raise ValueError("At least one feature is required")
        values = frame.loc[:, features].astype(float)
        if np.isinf(values.to_numpy()).any():
            raise ValueError("Infinite feature value in training split")
        medians: pd.Series | None = None
        unavailable = values.columns[values.isna().all(axis=0)].tolist()
        selected = [name for name in features if name not in unavailable]
        if not selected:
            raise ValueError("Every feature is unavailable throughout TRAIN")
        if config.imputation == "median":
            medians = values.median(axis=0, skipna=True)
            values = values.fillna(medians)
        elif config.imputation != "none":
            raise ValueError(f"Unsupported imputation: {config.imputation}")
        if values[selected].isna().any().any():
            raise ValueError("NaN remains after training preprocessing")
        if selection.variance_threshold is not None:
            variances = values.var(axis=0, ddof=0)
            selected = [
                name for name in selected if variances[name] > selection.variance_threshold
            ]
        if selection.correlation_threshold is not None and selected:
            correlation = values[selected].corr().abs()
            correlation_values = correlation.to_numpy(dtype=float)
            positions = {name: index for index, name in enumerate(selected)}
            kept: list[str] = []
            for name in selected:
                if all(
                    correlation_values[positions[name], positions[prior]]
                    < selection.correlation_threshold
                    for prior in kept
                ):
                    kept.append(name)
            selected = kept
        if not selected:
            raise ValueError("Feature selection removed every feature")
        scaler: StandardScaler | RobustScaler | None
        if config.scaler == "standard":
            scaler = StandardScaler().fit(values[selected])
        elif config.scaler == "robust":
            scaler = RobustScaler().fit(values[selected])
        elif config.scaler == "none":
            scaler = None
        else:
            raise ValueError(f"Unsupported scaler: {config.scaler}")
        return cls(
            config,
            selection,
            list(features),
            selected,
            medians,
            scaler,
            len(frame),
            unavailable,
        )

    @property
    def feature_list_version(self) -> str:
        return f"fs-{canonical_hash(self.selected_features)[:16]}"

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        missing = [name for name in self.input_features if name not in frame.columns]
        if missing:
            raise ValueError(f"Missing required features: {missing}")
        values = frame.loc[:, self.input_features].astype(float)
        if np.isinf(values.to_numpy()).any():
            raise ValueError("Infinite feature value at transform time")
        if self.medians is not None:
            values = values.fillna(self.medians)
        values = values.loc[:, self.selected_features]
        if values.isna().any().any():
            raise ValueError("NaN violates transform policy")
        transformed = values.to_numpy(dtype=float)
        if self.scaler is not None:
            transformed = self.scaler.transform(values)
        return np.asarray(transformed, dtype=float)
