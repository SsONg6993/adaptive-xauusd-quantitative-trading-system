"""Label balance and definition-sensitivity reporting; never resamples data."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from axq.labels.base import LabelDefinition
from axq.labels.registry import generate_labels


def label_balance(target: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(target, errors="coerce")
    if pd.api.types.is_numeric_dtype(target) and target.nunique(dropna=True) > 20:
        valid = numeric.dropna()
        return {
            "rows": len(target),
            "kind": "continuous",
            "counts": {},
            "rates": {},
            "summary": {
                "valid": len(valid),
                "missing_rate": float(target.isna().mean()),
                "mean": float(valid.mean()),
                "std": float(valid.std(ddof=0)),
                "p01": float(valid.quantile(0.01)),
                "p50": float(valid.quantile(0.50)),
                "p99": float(valid.quantile(0.99)),
            },
        }
    counts = target.value_counts(dropna=False)
    total = len(target)
    return {
        "rows": total,
        "kind": "categorical",
        "counts": {str(key): int(value) for key, value in counts.items()},
        "rates": {
            str(key): float(value / total) if total else 0.0 for key, value in counts.items()
        },
    }


def compare_label_definitions(
    frame: pd.DataFrame, definitions: Iterable[LabelDefinition]
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for definition in definitions:
        result = generate_labels(frame, definition)
        target = result.frame[result.manifest.target_columns[0]]
        balance = label_balance(target.dropna())
        if balance["kind"] == "continuous":
            records.append(
                {
                    "label_name": definition.name,
                    "label_version": definition.version,
                    "manifest_id": result.manifest.manifest_id,
                    "outcome": "CONTINUOUS",
                    "count": balance["summary"]["valid"],
                    "rate": 1.0,
                }
            )
            continue
        for outcome, count in balance["counts"].items():
            records.append(
                {
                    "label_name": definition.name,
                    "label_version": definition.version,
                    "manifest_id": result.manifest.manifest_id,
                    "outcome": outcome,
                    "count": count,
                    "rate": balance["rates"][outcome],
                }
            )
    return pd.DataFrame.from_records(records)
