"""Content-derived dataset and configuration identities."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


class DatasetManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    dataset_name: str
    symbol: str
    timeframes: list[str]
    source_files: dict[str, str]
    row_counts: dict[str, int]
    period_start: datetime
    period_end: datetime
    cleaning_version: str
    feature_version: str | None = None
    label_version: str | None = None
    config_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def dataset_version(self) -> str:
        body = self.model_dump(mode="json", exclude={"created_at"})
        return f"ds-{canonical_hash(body)[:16]}"

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.model_dump(mode="json") | {"dataset_version": self.dataset_version}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
