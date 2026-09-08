"""Compare completed development runs without retraining or scalar ranking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from axq.quant.development.artifacts import verify_development_run


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def compare_runs(
    run_dirs: list[str | Path], *, verify: bool = True
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for directory in run_dirs:
        root = Path(directory)
        if verify:
            verify_development_run(root)
        summary = _read(root / "run_summary.json")
        metrics = _read(root / "metrics.json").get("oos", {})
        rows.append(
            {
                "run_id": summary.get("run_id"),
                "architecture": summary.get("architecture"),
                "model_id": summary.get("model_id"),
                "dataset_id": summary.get("dataset_id"),
                "feature_count": summary.get("feature_count"),
                "balanced_accuracy": metrics.get("balanced_accuracy"),
                "log_loss": metrics.get("log_loss"),
                "brier_score": metrics.get("brier_score"),
                "actionable_coverage": metrics.get("prediction_coverage"),
                "temporal_stability": summary.get("temporal_stability"),
                "artifact_identity": summary.get("model_id"),
                "final_oos_use": summary.get("final_oos_use"),
            }
        )
    return {
        "runs": rows,
        "ranking": None,
        "accuracy_only_ranking_forbidden": True,
        "review_dimensions": [
            "baseline_comparison",
            "classification",
            "calibration",
            "actionable_coverage",
            "temporal_stability",
            "artifact_identity",
        ],
    }
