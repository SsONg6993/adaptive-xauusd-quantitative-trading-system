"""Lightweight local SQLite experiment audit log."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ExperimentTracker:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS quant_runs ("
                "run_id TEXT PRIMARY KEY, model TEXT NOT NULL, dataset_id TEXT NOT NULL, "
                "config_json TEXT NOT NULL, metrics_json TEXT, started_at TEXT NOT NULL, "
                "ended_at TEXT, status TEXT NOT NULL, device TEXT NOT NULL, failure TEXT)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def start(
        self, run_id: str, model: str, dataset_id: str, config: dict[str, Any], device: str
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO quant_runs VALUES (?, ?, ?, ?, NULL, ?, NULL, ?, ?, NULL)",
                (
                    run_id,
                    model,
                    dataset_id,
                    json.dumps(config, sort_keys=True, default=str),
                    datetime.now(UTC).isoformat(),
                    "RUNNING",
                    device,
                ),
            )

    def finish(self, run_id: str, metrics: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE quant_runs SET metrics_json=?, ended_at=?, "
                "status='COMPLETE' WHERE run_id=?",
                (json.dumps(metrics, sort_keys=True), datetime.now(UTC).isoformat(), run_id),
            )

    def fail(self, run_id: str, failure: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE quant_runs SET ended_at=?, status='FAILED', failure=? WHERE run_id=?",
                (datetime.now(UTC).isoformat(), failure, run_id),
            )
