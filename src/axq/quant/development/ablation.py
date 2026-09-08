"""Manifest-bound feature ablation plans; execution remains fold-local."""

from __future__ import annotations

from axq.features.manifest import FeatureManifest


def feature_ablation_variants(
    manifest: FeatureManifest,
    selected_features: list[str],
    *,
    groups: list[str],
    single_features: list[str],
) -> dict[str, list[str]]:
    selected = list(selected_features)
    known = {entry.feature_name: entry.feature_group for entry in manifest.entries if entry.enabled}
    missing = sorted(set(selected) - set(known))
    if missing:
        raise ValueError(f"Selected features are absent from enabled manifest: {missing}")
    variants = {"ALL_FEATURES": selected}
    for group in groups:
        normalized = group.upper()
        variants[f"ALL_MINUS_{normalized}"] = [
            name for name in selected if known[name].upper() != normalized
        ]
    for feature in single_features:
        if feature not in selected:
            raise ValueError(f"Single-feature ablation is not selected: {feature}")
        variants[f"ALL_MINUS_FEATURE_{feature}"] = [
            name for name in selected if name != feature
        ]
    if any(not features for features in variants.values()):
        raise ValueError("An ablation variant removes every feature")
    return variants
