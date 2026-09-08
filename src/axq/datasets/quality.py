from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from axq.datasets.splits import SplitManifest
from axq.labels.analysis import label_balance


def dataset_quality_report(
    frame: pd.DataFrame,
    *,
    rows_before_filtering: int,
    rows_after_warmup: int,
    feature_columns: list[str],
    target_columns: list[str],
    label_metadata_columns: list[str],
    split_manifest: SplitManifest | None,
    maximum_warmup_rows: int,
) -> dict[str, Any]:
    target = target_columns[0]
    mfe_columns = [column for column in label_metadata_columns if "_mfe_" in column]
    mae_columns = [column for column in label_metadata_columns if "_mae_" in column]
    excursion_summary: dict[str, dict[str, float | None]] = {}
    for column in [*mfe_columns, *mae_columns]:
        values = pd.to_numeric(frame[column], errors="coerce")
        excursion_summary[column] = {
            "mean": float(values.mean()) if values.notna().any() else None,
            "median": float(values.median()) if values.notna().any() else None,
            "p95": float(values.quantile(0.95)) if values.notna().any() else None,
        }
    barrier_values = {"UPPER_FIRST", "LOWER_FIRST", "TP_FIRST", "SL_FIRST", "TIMEOUT",
                      "AMBIGUOUS"}
    observed = set(frame[target].dropna().astype(str).unique())
    return {
        "rows_before_filtering": rows_before_filtering,
        "rows_after_warmup": rows_after_warmup,
        "rows_final": len(frame),
        "maximum_warmup_rows": maximum_warmup_rows,
        "label_distribution": label_balance(frame[target]),
        "neutral_class_rate": float(frame[target].eq("NEUTRAL").mean()),
        "missing_feature_rate": {
            column: float(frame[column].isna().mean()) for column in feature_columns
        },
        "duplicate_decision_timestamps": int(frame["decision_timestamp"].duplicated().sum()),
        "chronological_order": bool(frame["decision_timestamp"].is_monotonic_increasing),
        "split_sizes": (
            {
                "train": split_manifest.folds[0].train.size,
                "validation": split_manifest.folds[0].validation.size,
                "oos": split_manifest.folds[0].oos.size,
            }
            if split_manifest
            else None
        ),
        "purged_rows": (
            sum(
                fold.purged_train_rows + fold.purged_validation_rows
                for fold in split_manifest.folds
            )
            if split_manifest
            else 0
        ),
        "embargoed_rows": (
            sum(
                fold.embargoed_validation_rows + fold.embargoed_oos_rows
                for fold in split_manifest.folds
            )
            if split_manifest
            else 0
        ),
        "horizon_coverage_rate": float(frame[target].notna().mean()),
        "barrier_outcome_distribution": (
            label_balance(frame[target]) if observed & barrier_values else None
        ),
        "mfe_mae_summary": excursion_summary,
        "feature_label_separation": not bool(
            set(feature_columns) & set([*target_columns, *label_metadata_columns])
        ),
        "infinite_feature_values": int(
            np.isinf(frame[feature_columns].to_numpy(dtype=float, na_value=np.nan)).sum()
        ),
    }
