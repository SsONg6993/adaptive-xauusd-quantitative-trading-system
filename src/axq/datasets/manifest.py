"""Immutable, content-derived Phase 3 dataset contract."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from axq.versioning import canonical_hash


class DatasetManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "2.0"
    dataset_name: str
    symbol: str
    base_timeframe: str
    higher_timeframes: list[str]
    start_timestamp: datetime
    end_timestamp: datetime
    row_count: int
    feature_count: int
    target_count: int
    feature_columns: list[str]
    target_columns: list[str]
    label_metadata_columns: list[str]
    feature_manifest_id: str
    label_manifest_id: str
    split_manifest_id: str | None
    source_data_hash: str
    dataset_content_hash: str
    configuration_hash: str
    timezone: str = "UTC"
    decision_timestamp_convention: str
    train_validation_oos_boundaries: dict[str, dict[str, int]] | None
    storage_format: str
    git_commit: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def dataset_id(self) -> str:
        body = self.model_dump(mode="json", exclude={"created_at"})
        return f"ds-{canonical_hash(body)[:16]}"

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.model_dump(mode="json") | {"dataset_id": self.dataset_id}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
