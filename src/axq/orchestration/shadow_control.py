"""Operational-only process control records for the Live Shadow Runtime."""

from __future__ import annotations

import os
import sqlite3
from enum import StrEnum
from pathlib import Path
from typing import IO, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class ManagedRuntimeStatus(StrEnum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    WAITING_FOR_MARKET = "WAITING_FOR_MARKET"
    ERROR = "ERROR"
    STOPPING = "STOPPING"


class ControlModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ManagedShadowConfig(ControlModel):
    config_id: str = ""
    project_root: Path
    python_executable: Path
    terminal_path: Path
    gold_symbols: tuple[str, ...] = Field(min_length=1, max_length=16)
    output_dir: Path
    poll_seconds: float = Field(ge=0.25, le=60.0)

    @model_validator(mode="after")
    def validate_and_bind(self) -> ManagedShadowConfig:
        symbols = tuple(item.strip() for item in self.gold_symbols)
        if any(not item or "," in item for item in symbols):
            raise ValueError("Gold symbols must be explicit non-empty names")
        if len(set(symbols)) != len(symbols):
            raise ValueError("Gold symbol allowlist must be unique")
        object.__setattr__(self, "gold_symbols", symbols)
        identity = self.model_dump(mode="json", exclude={"config_id"})
        expected = f"msc-{canonical_hash(identity)[:20]}"
        if self.config_id and self.config_id != expected:
            raise ValueError("config_id does not match managed Shadow configuration")
        object.__setattr__(self, "config_id", expected)
        return self


class ManagedRuntimeInstance(ControlModel):
    instance_id: str = Field(min_length=1)
    config: ManagedShadowConfig
    pid: int = Field(gt=0)
    process_creation_token: str = Field(min_length=1)
    expected_executable: Path
    registered_at: UTCDateTime


class ManagedRuntimeEvent(ControlModel):
    event_id: str = ""
    instance_id: str = Field(min_length=1)
    status: ManagedRuntimeStatus
    occurred_at: UTCDateTime
    reason_code: str = Field(min_length=1, max_length=100)
    error: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def bind_identity(self) -> ManagedRuntimeEvent:
        identity = self.model_dump(mode="json", exclude={"event_id", "occurred_at"})
        expected = f"msce-{canonical_hash(identity)[:20]}"
        if self.event_id and self.event_id != expected:
            raise ValueError("event_id does not match lifecycle semantics")
        object.__setattr__(self, "event_id", expected)
        return self


_SCHEMA = """
CREATE TABLE IF NOT EXISTS shadow_control_instances (
    instance_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id TEXT NOT NULL UNIQUE,
    registered_at TEXT NOT NULL,
    record_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shadow_control_events (
    event_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    instance_id TEXT NOT NULL REFERENCES shadow_control_instances(instance_id),
    occurred_at TEXT NOT NULL,
    record_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shadow_stop_requests (
    request_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id TEXT NOT NULL UNIQUE REFERENCES shadow_control_instances(instance_id),
    requested_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS shadow_control_instances_no_update
BEFORE UPDATE ON shadow_control_instances BEGIN
    SELECT RAISE(ABORT, 'shadow control is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shadow_control_instances_no_delete
BEFORE DELETE ON shadow_control_instances BEGIN
    SELECT RAISE(ABORT, 'shadow control is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shadow_control_events_no_update
BEFORE UPDATE ON shadow_control_events BEGIN
    SELECT RAISE(ABORT, 'shadow control is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shadow_control_events_no_delete
BEFORE DELETE ON shadow_control_events BEGIN
    SELECT RAISE(ABORT, 'shadow control is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shadow_stop_requests_no_update
BEFORE UPDATE ON shadow_stop_requests BEGIN
    SELECT RAISE(ABORT, 'shadow control is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shadow_stop_requests_no_delete
BEFORE DELETE ON shadow_stop_requests BEGIN
    SELECT RAISE(ABORT, 'shadow control is append-only');
END;
"""


class SQLiteShadowControlStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def register_instance(self, value: ManagedRuntimeInstance) -> None:
        payload = value.model_dump_json()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT record_json FROM shadow_control_instances WHERE instance_id = ?",
                (value.instance_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) != payload:
                    raise ValueError("runtime instance ID already has different content")
                return
            connection.execute(
                "INSERT INTO shadow_control_instances(instance_id, registered_at, record_json) "
                "VALUES (?, ?, ?)",
                (value.instance_id, value.registered_at.isoformat(), payload),
            )

    def append_event(self, value: ManagedRuntimeEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO shadow_control_events"
                "(event_id, instance_id, occurred_at, record_json) "
                "VALUES (?, ?, ?, ?)",
                (
                    value.event_id,
                    value.instance_id,
                    value.occurred_at.isoformat(),
                    value.model_dump_json(),
                ),
            )

    def request_stop(self, instance_id: str, *, requested_at: UTCDateTime) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO shadow_stop_requests(instance_id, requested_at) "
                "VALUES (?, ?)",
                (instance_id, requested_at.isoformat()),
            )

    def stop_requested(self, instance_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM shadow_stop_requests WHERE instance_id = ?",
                (instance_id,),
            ).fetchone()
        return row is not None

    def latest_instance(self) -> ManagedRuntimeInstance | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM shadow_control_instances "
                "ORDER BY instance_sequence DESC LIMIT 1"
            ).fetchone()
        return None if row is None else ManagedRuntimeInstance.model_validate_json(row[0])

    def events(self, instance_id: str) -> tuple[ManagedRuntimeEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM shadow_control_events WHERE instance_id = ? "
                "ORDER BY event_sequence",
                (instance_id,),
            ).fetchall()
        return tuple(ManagedRuntimeEvent.model_validate_json(row[0]) for row in rows)

    def latest_event(self, instance_id: str) -> ManagedRuntimeEvent | None:
        values = self.events(instance_id)
        return values[-1] if values else None

    def connection_for_tests(self) -> sqlite3.Connection:
        return self._connect()


class ManagedRuntimeControl:
    """Exact-instance operational channel consumed by the Shadow process."""

    def __init__(self, store: SQLiteShadowControlStore, instance_id: str) -> None:
        if not instance_id:
            raise ValueError("managed runtime instance ID is required")
        self.store = store
        self.instance_id = instance_id

    def stop_requested(self) -> bool:
        return self.store.stop_requested(self.instance_id)

    def record(
        self,
        status: ManagedRuntimeStatus,
        *,
        now: UTCDateTime,
        reason_code: str,
        error: str | None = None,
    ) -> None:
        self.store.append_event(
            ManagedRuntimeEvent(
                instance_id=self.instance_id,
                status=status,
                occurred_at=now,
                reason_code=reason_code,
                error=error,
            )
        )


class ShadowRuntimeInstanceGuard:
    """OS-held singleton lock owned by the Shadow Runtime process itself."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir).resolve()
        self._handle: IO[bytes] | None = None

    def acquire(self) -> None:
        if self._handle is not None:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / ".shadow-runtime.lock"
        handle = path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:  # pragma: no cover - repository production target is Windows
                fcntl_module: Any = __import__("fcntl")
                fcntl_module.flock(
                    handle.fileno(), fcntl_module.LOCK_EX | fcntl_module.LOCK_NB
                )
        except OSError as error:
            handle.close()
            raise RuntimeError(
                f"Live Shadow Runtime is already running for {self.output_dir}"
            ) from error
        self._handle = handle

    def release(self) -> None:
        handle = self._handle
        if handle is None:
            return
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:  # pragma: no cover
            fcntl_module: Any = __import__("fcntl")
            fcntl_module.flock(handle.fileno(), fcntl_module.LOCK_UN)
        handle.close()
        self._handle = None

    def __enter__(self) -> ShadowRuntimeInstanceGuard:
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback
        self.release()


__all__ = [
    "ManagedRuntimeEvent",
    "ManagedRuntimeControl",
    "ManagedRuntimeInstance",
    "ManagedRuntimeStatus",
    "ManagedShadowConfig",
    "SQLiteShadowControlStore",
    "ShadowRuntimeInstanceGuard",
]
