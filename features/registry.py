"""Compatibility entry point; implementation lives in the installable axq package."""

from axq.features.registry import FeatureDefinition, FeatureRegistry, default_registry

__all__ = ["FeatureDefinition", "FeatureRegistry", "default_registry"]
