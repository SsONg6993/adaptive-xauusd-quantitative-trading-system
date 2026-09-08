"""Atomic, identity-bound state for resumable local experiments."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RunStateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Run state must be a JSON object")
        return payload

    def _validate_identity(self, run_id: str, config_hash: str) -> None:
        existing = self.load()
        if existing and (
            existing.get("run_id") != run_id
            or existing.get("config_hash") != config_hash
        ):
            raise ValueError("Run state identity does not match requested identity")

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def start(self, run_id: str, *, config_hash: str) -> None:
        self._validate_identity(run_id, config_hash)
        now = datetime.now(UTC).isoformat()
        prior = self.load()
        self._write(
            {
                "schema_version": "1.0",
                "run_id": run_id,
                "config_hash": config_hash,
                "status": "RUNNING",
                "started_at": prior.get("started_at", now),
                "updated_at": now,
                "artifacts": prior.get("artifacts", {}),
            }
        )

    def complete(
        self, run_id: str, *, config_hash: str, artifacts: dict[str, str]
    ) -> None:
        self._validate_identity(run_id, config_hash)
        prior = self.load()
        self._write(
            prior
            | {
                "run_id": run_id,
                "config_hash": config_hash,
                "status": "COMPLETE",
                "updated_at": datetime.now(UTC).isoformat(),
                "artifacts": artifacts,
            }
        )

    def fail(self, run_id: str, *, config_hash: str, failure: str) -> None:
        self._validate_identity(run_id, config_hash)
        prior = self.load()
        self._write(
            prior
            | {
                "run_id": run_id,
                "config_hash": config_hash,
                "status": "FAILED",
                "updated_at": datetime.now(UTC).isoformat(),
                "failure": failure,
            }
        )

    def is_interrupted(self, run_id: str, *, config_hash: str) -> bool:
        self._validate_identity(run_id, config_hash)
        return self.load().get("status") == "RUNNING"
