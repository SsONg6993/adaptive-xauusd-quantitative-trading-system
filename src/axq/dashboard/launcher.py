"""One-click, verified local Streamlit dashboard launcher."""

from __future__ import annotations

import sqlite3
import time
import urllib.error
import urllib.request
import uuid
import webbrowser
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from axq.dashboard.python_runtime import resolve_project_python
from axq.dashboard.shadow_controller import (
    ProcessAdapter,
    ProcessIdentity,
    WindowsProcessAdapter,
)
from axq.orchestration.shadow_control import ShadowRuntimeInstanceGuard
from axq.runtime.state import UTCDateTime


class DashboardLaunchStatus(StrEnum):
    STARTED = "STARTED"
    REUSED = "REUSED"


class DashboardLaunchRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    launch_id: str = Field(min_length=1)
    process_identity: ProcessIdentity
    project_root: Path
    url: str = Field(pattern=r"^http://127\.0\.0\.1:[0-9]+$")
    registered_at: UTCDateTime


class DashboardLaunchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: DashboardLaunchStatus
    launch_id: str
    process_identity: ProcessIdentity
    url: str


_SCHEMA = """
CREATE TABLE IF NOT EXISTS dashboard_launches (
    launch_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    launch_id TEXT NOT NULL UNIQUE,
    record_json TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS dashboard_launches_no_update
BEFORE UPDATE ON dashboard_launches BEGIN
    SELECT RAISE(ABORT, 'dashboard launches are append-only');
END;
CREATE TRIGGER IF NOT EXISTS dashboard_launches_no_delete
BEFORE DELETE ON dashboard_launches BEGIN
    SELECT RAISE(ABORT, 'dashboard launches are append-only');
END;
"""


class SQLiteDashboardLaunchStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        return connection

    def append(self, record: DashboardLaunchRecord) -> None:
        payload = record.model_dump_json()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT record_json FROM dashboard_launches WHERE launch_id = ?",
                (record.launch_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) != payload:
                    raise ValueError("dashboard launch ID already has different content")
                return
            connection.execute(
                "INSERT INTO dashboard_launches(launch_id, record_json) VALUES (?, ?)",
                (record.launch_id, payload),
            )

    def latest(self) -> DashboardLaunchRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM dashboard_launches "
                "ORDER BY launch_sequence DESC LIMIT 1"
            ).fetchone()
        return None if row is None else DashboardLaunchRecord.model_validate_json(row[0])

    def connection_for_tests(self) -> sqlite3.Connection:
        return self._connect()


def _same_process(actual: ProcessIdentity | None, expected: ProcessIdentity) -> bool:
    return actual is not None and (
        actual.pid == expected.pid
        and actual.creation_token == expected.creation_token
        and str(actual.executable.resolve()).casefold()
        == str(expected.executable.resolve()).casefold()
    )


def loopback_streamlit_health(url: str) -> bool:
    try:
        with urllib.request.urlopen(  # noqa: S310 - URL is code-owned loopback only
            f"{url}/_stcore/health",
            timeout=1.0,
        ) as response:
            return int(response.status) == 200
    except (OSError, urllib.error.URLError):
        return False


class DashboardLauncher:
    """Start or reuse one verified local Streamlit process."""

    def __init__(
        self,
        *,
        project_root: str | Path,
        python_executable: str | Path,
        registry_path: str | Path,
        process_adapter: ProcessAdapter | None = None,
        health_probe: Callable[[str], bool] = loopback_streamlit_health,
        browser_opener: Callable[[str], object] = webbrowser.open,
        launch_id_factory: Callable[[], str] | None = None,
        readiness_attempts: int = 50,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.python_executable = Path(python_executable).resolve()
        self.store = SQLiteDashboardLaunchStore(registry_path)
        self._processes = process_adapter or WindowsProcessAdapter()
        self._health = health_probe
        self._open_browser = browser_opener
        self._launch_id_factory = launch_id_factory or (lambda: str(uuid.uuid4()))
        self._readiness_attempts = readiness_attempts
        self.url = "http://127.0.0.1:8501"

    def _command(self) -> tuple[str, ...]:
        return (
            str(self.python_executable),
            str(self.project_root / "scripts/run_dashboard.py"),
        )

    def _ready(self) -> bool:
        for attempt in range(self._readiness_attempts):
            if self._health(self.url):
                return True
            if attempt + 1 < self._readiness_attempts:
                time.sleep(0.1)
        return False

    def _result(
        self,
        status: DashboardLaunchStatus,
        record: DashboardLaunchRecord,
    ) -> DashboardLaunchResult:
        self._open_browser(record.url)
        return DashboardLaunchResult(
            status=status,
            launch_id=record.launch_id,
            process_identity=record.process_identity,
            url=record.url,
        )

    def _terminate_verified(self, identity: ProcessIdentity) -> None:
        actual = self._processes.inspect(identity.pid)
        if not _same_process(actual, identity):
            raise RuntimeError("dashboard process identity changed before cleanup")
        self._processes.terminate(identity)

    def launch(self, *, now: UTCDateTime | None = None) -> DashboardLaunchResult:
        launched_at = now or datetime.now(UTC)
        lock_root = self.store.path.parent / ".dashboard-launch-command"
        with ShadowRuntimeInstanceGuard(lock_root):
            prior = self.store.latest()
            if prior is not None:
                actual = self._processes.inspect(prior.process_identity.pid)
                if _same_process(actual, prior.process_identity):
                    if not self._ready():
                        self._terminate_verified(prior.process_identity)
                        raise RuntimeError(
                            "registered dashboard process is alive but "
                            "Streamlit health check failed"
                        )
                    return self._result(DashboardLaunchStatus.REUSED, prior)
            if self._health(self.url):
                raise RuntimeError(
                    "healthy Streamlit endpoint is not owned by the durable AXQ registry"
                )
            identity = self._processes.spawn(
                self._command(),
                cwd=self.project_root,
                log_path=self.store.path.parent / "dashboard.log",
            )
            record = DashboardLaunchRecord(
                launch_id=self._launch_id_factory(),
                process_identity=identity,
                project_root=self.project_root,
                url=self.url,
                registered_at=launched_at,
            )
            try:
                self.store.append(record)
                if not self._ready():
                    raise RuntimeError("Streamlit dashboard did not become ready")
            except Exception:
                self._terminate_verified(identity)
                raise
            return self._result(DashboardLaunchStatus.STARTED, record)


__all__ = [
    "DashboardLaunchRecord",
    "DashboardLaunchResult",
    "DashboardLaunchStatus",
    "DashboardLauncher",
    "SQLiteDashboardLaunchStore",
    "loopback_streamlit_health",
    "resolve_project_python",
]
