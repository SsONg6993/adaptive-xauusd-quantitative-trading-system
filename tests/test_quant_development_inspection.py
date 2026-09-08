from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from axq.quant.development.compute import _optional_positive_int, compute_report
from axq.quant.development.history import inspect_history_frames


def test_history_inspection_reports_quality_and_completed_bar_semantics() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-05T00:00:00Z",
                    "2026-01-05T00:05:00Z",
                    "2026-01-05T00:05:00Z",
                    "2026-01-05T00:20:00Z",
                ],
                utc=True,
            ),
            "open": [2600.0, 2601.0, 2601.0, 2603.0],
            "high": [2602.0, 2602.0, 2602.0, 2604.0],
            "low": [2599.0, 2600.0, 2600.0, 2602.0],
            "close": [2601.0, 2601.5, 2601.5, 2603.5],
            "tick_volume": [12, 0, 0, 15],
            "spread": [20, 25, 25, 500],
        }
    )

    report = inspect_history_frames(
        {"M5": frame},
        now=datetime(2026, 1, 5, 0, 22, tzinfo=UTC),
        abnormal_spread=100.0,
    )

    m5 = report["timeframes"]["M5"]
    assert m5["rows"] == 4
    assert m5["duplicate_bars"] == 1
    assert m5["major_gaps"] == 1
    assert m5["zero_tick_volume"] == 2
    assert m5["abnormal_spread_rows"] == 1
    assert m5["ohlc_invalid_rows"] == 0
    assert m5["latest_bar_completed"] is False
    assert m5["timestamps_are_utc"] is True


def test_compute_report_does_not_claim_gpu_without_verified_capability() -> None:
    report = compute_report(
        module_available=lambda name: name in {"xgboost", "lightgbm"},
        nvidia_probe=lambda: None,
        xgboost_build_info=lambda: {"USE_CUDA": True},
        lightgbm_gpu_probe=lambda: False,
        memory_probe=lambda: 16_000_000_000,
        physical_cores_probe=lambda: 8,
    )

    assert report["nvidia"]["detected"] is False
    assert report["xgboost"]["gpu_capable"] is False
    assert report["lightgbm"]["gpu_capable"] is False
    assert report["recommendations"]["xgboost"] == "cpu"
    assert report["recommendations"]["lightgbm"] == "cpu"
    assert report["cpu"]["physical_cores"] == 8
    assert report["cpu"]["ram_bytes"] == 16_000_000_000


def test_empty_windows_hardware_probe_degrades_to_unavailable() -> None:
    assert _optional_positive_int("") is None
    assert _optional_positive_int("not-an-integer") is None
    assert _optional_positive_int("24\n") == 24
