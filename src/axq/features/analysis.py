"""Lightweight feature-analysis and quality-diagnostic utilities."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any, Literal, cast

import numpy as np
import pandas as pd


def correlation_matrix(frame: pd.DataFrame, *, method: str = "pearson") -> pd.DataFrame:
    if method not in {"pearson", "spearman"}:
        raise ValueError("method must be pearson or spearman")
    correlation_method = cast(Literal["pearson", "spearman"], method)
    return frame.select_dtypes(include="number").corr(method=correlation_method)


def highly_correlated_features(
    frame: pd.DataFrame, *, threshold: float = 0.95, method: str = "spearman"
) -> list[tuple[str, str, float]]:
    correlation = correlation_matrix(frame, method=method).abs()
    pairs: list[tuple[str, str, float]] = []
    for right_index, right in enumerate(correlation.columns):
        for left in correlation.columns[:right_index]:
            raw_value = correlation.loc[left, right]
            if pd.notna(raw_value):
                value = cast(float, raw_value)
                if value >= threshold:
                    pairs.append((str(left), str(right), value))
    return pairs


def variance_report(frame: pd.DataFrame, *, threshold: float = 1e-12) -> pd.DataFrame:
    numeric = frame.select_dtypes(include="number")
    variances = numeric.var(ddof=0)
    return pd.DataFrame(
        {"variance": variances, "near_zero_variance": variances.le(threshold)}
    )


def duplicate_features(frame: pd.DataFrame) -> list[tuple[str, str]]:
    columns = list(frame.columns)
    duplicates: list[tuple[str, str]] = []
    for right_index, right in enumerate(columns):
        for left in columns[:right_index]:
            if frame[left].equals(frame[right]):
                duplicates.append((str(left), str(right)))
    return duplicates


def missing_value_rate(frame: pd.DataFrame) -> pd.Series:
    return frame.isna().mean().rename("missing_rate")


def validate_explainer_compatibility(frame: pd.DataFrame) -> dict[str, Any]:
    numeric = frame.select_dtypes(include="number")
    return {
        "permutation_importance_compatible": len(numeric.columns) == len(frame.columns),
        "shap_compatible": len(numeric.columns) == len(frame.columns),
        "requires_imputation": bool(numeric.isna().any().any()),
        "has_infinite": bool(np.isinf(numeric.to_numpy(dtype=float)).any()),
        "note": "Fit imputation/model/explainer on training folds only.",
    }


def feature_group_ablations(
    columns: Iterable[str], groups: Mapping[str, Iterable[str]]
) -> dict[str, list[str]]:
    all_columns = list(columns)
    return {
        f"drop_group:{group}": [column for column in all_columns if column not in set(members)]
        for group, members in groups.items()
    }


def single_feature_ablations(columns: Iterable[str]) -> dict[str, list[str]]:
    all_columns = list(columns)
    return {
        f"drop_feature:{excluded}": [column for column in all_columns if column != excluded]
        for excluded in all_columns
    }


def feature_stability(
    frame: pd.DataFrame, periods: pd.Series
) -> pd.DataFrame:
    numeric = frame.select_dtypes(include="number")
    records: list[dict[str, Any]] = []
    for period, group in numeric.groupby(periods, observed=True):
        for column in numeric.columns:
            values = group[column]
            records.append(
                {
                    "period": str(period),
                    "feature": str(column),
                    "mean": float(values.mean()) if values.notna().any() else np.nan,
                    "std": float(values.std(ddof=0)) if values.notna().any() else np.nan,
                    "missing_rate": float(values.isna().mean()),
                }
            )
    return pd.DataFrame.from_records(records)


@dataclass(frozen=True)
class FeatureQuality:
    feature: str
    rows: int
    valid_rows: int
    nan_percentage: float
    infinite_values: int
    minimum: float | None
    maximum: float | None
    p01: float | None
    p25: float | None
    p50: float | None
    p75: float | None
    p99: float | None
    outlier_rate: float
    constant: bool
    warmup_rows: int


def _optional_float(value: float) -> float | None:
    return None if pd.isna(value) else float(value)


def quality_report(
    frame: pd.DataFrame, *, correlation_threshold: float = 0.95
) -> dict[str, Any]:
    numeric = frame.select_dtypes(include="number")
    features: list[dict[str, Any]] = []
    for column in numeric.columns:
        raw = numeric[column].astype(float)
        finite = raw.replace([np.inf, -np.inf], np.nan)
        valid = finite.dropna()
        q1 = valid.quantile(0.25) if len(valid) else np.nan
        q3 = valid.quantile(0.75) if len(valid) else np.nan
        iqr = q3 - q1
        outliers = ((valid < q1 - 1.5 * iqr) | (valid > q3 + 1.5 * iqr)).mean()
        positions = np.flatnonzero(raw.notna().to_numpy())
        warmup = len(raw) if not len(positions) else int(positions[0])
        summary = FeatureQuality(
            feature=str(column),
            rows=len(raw),
            valid_rows=len(valid),
            nan_percentage=float(raw.isna().mean() * 100.0),
            infinite_values=int(np.isinf(raw.to_numpy()).sum()),
            minimum=_optional_float(valid.min()),
            maximum=_optional_float(valid.max()),
            p01=_optional_float(valid.quantile(0.01)),
            p25=_optional_float(q1),
            p50=_optional_float(valid.quantile(0.50)),
            p75=_optional_float(q3),
            p99=_optional_float(valid.quantile(0.99)),
            outlier_rate=float(outliers) if pd.notna(outliers) else 0.0,
            constant=bool(valid.nunique(dropna=True) <= 1),
            warmup_rows=warmup,
        )
        features.append(asdict(summary))
    return {
        "number_of_rows": len(frame),
        "features": features,
        "constant_features": [item["feature"] for item in features if item["constant"]],
        "high_correlation_groups": highly_correlated_features(
            numeric, threshold=correlation_threshold
        ),
    }
