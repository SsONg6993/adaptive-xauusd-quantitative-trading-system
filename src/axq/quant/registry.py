"""Explicit local lifecycle registry; promotion is never automatic."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModelState(StrEnum):
    CANDIDATE = "CANDIDATE"
    CHALLENGER = "CHALLENGER"
    CHAMPION = "CHAMPION"
    RETIRED = "RETIRED"


class RegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: str
    run_dir: str
    state: ModelState = ModelState.CANDIDATE
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    promotion_evidence: dict[str, Any] | None = None


class LocalModelRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def entries(self) -> list[RegistryEntry]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [RegistryEntry.model_validate(item) for item in payload.get("models", [])]

    def register(self, model_id: str, run_dir: str | Path) -> RegistryEntry:
        entries = self.entries()
        existing = next((item for item in entries if item.model_id == model_id), None)
        if existing is not None:
            if existing.run_dir != str(run_dir):
                raise ValueError("Model ID is already registered at a different path")
            return existing
        entry = RegistryEntry(model_id=model_id, run_dir=str(run_dir))
        entries.append(entry)
        self._write(entries)
        return entry

    def transition(
        self,
        model_id: str,
        state: ModelState,
        *,
        evidence: dict[str, Any] | None = None,
    ) -> RegistryEntry:
        entries = self.entries()
        entry = next((item for item in entries if item.model_id == model_id), None)
        if entry is None:
            raise KeyError(model_id)
        allowed = {
            ModelState.CANDIDATE: {ModelState.CHALLENGER, ModelState.RETIRED},
            ModelState.CHALLENGER: {ModelState.CHAMPION, ModelState.RETIRED},
            ModelState.CHAMPION: {ModelState.RETIRED},
            ModelState.RETIRED: set(),
        }
        if state not in allowed[entry.state]:
            raise ValueError(f"Invalid registry transition {entry.state} -> {state}")
        if state is ModelState.CHAMPION and not evidence:
            raise ValueError("Champion promotion requires explicit evaluation evidence")
        if state is ModelState.CHAMPION and any(
            item.state is ModelState.CHAMPION and item.model_id != model_id
            for item in entries
        ):
            raise ValueError("Retire the current champion before promoting another")
        entry.state = state
        entry.updated_at = datetime.now(UTC)
        entry.promotion_evidence = evidence
        self._write(entries)
        return entry

    def _write(self, entries: list[RegistryEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"schema_version": "1.0", "models": [e.model_dump(mode="json") for e in entries]},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )


CHAMPION_CHALLENGER_CRITERIA = (
    "OOS classification metrics",
    "calibration quality",
    "trading-oriented diagnostics",
    "time/regime stability",
    "trade-frequency behavior",
    "future walk-forward evidence",
)
