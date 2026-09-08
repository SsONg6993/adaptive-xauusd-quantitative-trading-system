"""Content-addressed Quant model manifest."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from axq.versioning import canonical_hash


class ModelManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    agent_type: str = "quant"
    architecture: str
    dataset_id: str
    feature_manifest_id: str
    label_manifest_id: str
    split_manifest_id: str
    target_column: str
    class_mapping: dict[str, str]
    selected_features: list[str]
    feature_list_version: str
    preprocessing_version: str
    calibration_method: str
    training_period: str
    validation_period: str
    oos_period: str
    metrics: dict[str, Any]
    random_seed: int
    hyperparameters: dict[str, Any]
    config_hash: str
    git_commit: str
    device: dict[str, Any]
    artifact_paths: dict[str, str]
    artifact_hashes: dict[str, str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def model_id(self) -> str:
        identity = self.model_dump(
            mode="json", exclude={"created_at", "metrics", "artifact_paths", "artifact_hashes"}
        )
        return f"qm-{canonical_hash(identity)[:16]}"

    def write(self, path: Path) -> None:
        payload = self.model_dump(mode="json") | {"model_id": self.model_id}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_model_manifest(path: str | Path) -> ModelManifest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    claimed = payload.pop("model_id", None)
    manifest = ModelManifest.model_validate(payload)
    if claimed != manifest.model_id:
        raise ValueError("Model manifest identity is corrupted")
    return manifest
