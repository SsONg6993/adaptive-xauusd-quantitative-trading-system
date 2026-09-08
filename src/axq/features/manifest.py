"""Canonical feature-manifest models."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class FeatureManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature_name: str
    feature_group: str
    parameters: dict[str, Any]
    implementation_version: str
    enabled: bool
    minimum_lookback: int
    warmup_rows: int
    valid_from_row: int
    insufficient_history_behavior: str = "NaN"
    required_source_columns: list[str]
    output_dtype: str
    causal_status: str


class FeatureManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    feature_set_version: str
    entries: list[FeatureManifestEntry]

    @property
    def manifest_id(self) -> str:
        body = self.model_dump(mode="json")
        encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        return f"fm-{hashlib.sha256(encoded).hexdigest()[:16]}"

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.model_dump(mode="json") | {"manifest_id": self.manifest_id}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
