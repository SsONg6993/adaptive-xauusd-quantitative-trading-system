"""Canonical label manifests."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from axq.labels.base import LabelDefinition
from axq.versioning import canonical_hash


class LabelManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    definition: LabelDefinition
    target_columns: list[str]
    metadata_columns: list[str]
    decision_reference: str = "completed candle close at row T"
    implementation_version: str = "1.0.0"

    @property
    def manifest_id(self) -> str:
        return f"lm-{canonical_hash(self.model_dump(mode='json'))[:16]}"

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.model_dump(mode="json") | {"manifest_id": self.manifest_id}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
