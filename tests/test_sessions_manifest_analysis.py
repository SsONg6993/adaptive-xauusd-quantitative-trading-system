from __future__ import annotations

import pandas as pd

from axq.features import default_registry
from axq.features.analysis import (
    correlation_matrix,
    duplicate_features,
    feature_group_ablations,
    feature_stability,
    highly_correlated_features,
    missing_value_rate,
    quality_report,
    single_feature_ablations,
    validate_explainer_compatibility,
    variance_report,
)
from axq.features.session import session_features


def test_london_and_new_york_dst_transitions() -> None:
    timestamps = pd.to_datetime(
        [
            "2026-03-27 08:00:00Z",
            "2026-03-30 07:00:00Z",
            "2026-03-06 13:00:00Z",
            "2026-03-09 12:00:00Z",
            "2026-10-23 07:00:00Z",
            "2026-10-26 08:00:00Z",
            "2026-11-02 13:00:00Z",
        ],
        utc=True,
    )
    output = session_features(pd.DataFrame({"timestamp": timestamps}), {})
    assert output["session_london"].tolist() == [1, 1, 1, 1, 1, 1, 1]
    assert output["session_new_york"].tolist() == [0, 0, 1, 1, 0, 0, 1]


def test_session_overlap_uses_actual_zone_intersection() -> None:
    frame = pd.DataFrame(
        {"timestamp": pd.to_datetime(["2026-03-20 12:30Z", "2026-03-20 17:30Z"], utc=True)}
    )
    output = session_features(frame, {})
    assert output["session_london_ny_overlap"].tolist() == [1, 0]


def test_manifest_is_reproducible_and_complete() -> None:
    registry = default_registry()
    groups = [definition.group for definition in registry.definitions()]
    first = registry.manifest(feature_set_version="features-v2.0", enabled_groups=groups)
    second = registry.manifest(feature_set_version="features-v2.0", enabled_groups=groups)
    assert first.manifest_id == second.manifest_id
    assert len(first.entries) > 60
    assert all(entry.causal_status.startswith("causal") for entry in first.entries)
    assert all(entry.output_dtype and entry.required_source_columns for entry in first.entries)
    m5_only = registry.manifest(
        feature_set_version="features-v2.0",
        enabled_groups=groups,
        available_source_columns=[
            "timestamp", "open", "high", "low", "close", "tick_volume", "spread"
        ],
    )
    assert not any(
        entry.enabled for entry in m5_only.entries if entry.feature_group == "multi_timeframe"
    )


def test_analysis_and_quality_tiny_smoke() -> None:
    frame = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0],
            "a_copy": [1.0, 2.0, 3.0, 4.0],
            "constant": [1.0, 1.0, 1.0, 1.0],
            "missing": [None, 1.0, None, 2.0],
        }
    )
    assert ("a", "a_copy") in duplicate_features(frame)
    assert correlation_matrix(frame, method="spearman").loc["a", "a_copy"] == 1
    assert variance_report(frame).loc["constant", "near_zero_variance"]
    assert missing_value_rate(frame)["missing"] == 0.5
    assert any(pair[:2] == ("a", "a_copy") for pair in highly_correlated_features(frame))
    assert validate_explainer_compatibility(frame)["requires_imputation"]
    assert feature_group_ablations(frame.columns, {"copies": ["a", "a_copy"]})[
        "drop_group:copies"
    ] == ["constant", "missing"]
    assert "a" not in single_feature_ablations(frame.columns)["drop_feature:a"]
    stability = feature_stability(frame, pd.Series(["first", "first", "second", "second"]))
    assert set(stability["period"]) == {"first", "second"}
    report = quality_report(frame)
    assert report["number_of_rows"] == 4
    assert "constant" in report["constant_features"]
