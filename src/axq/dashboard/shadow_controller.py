"""Durable operator control of the existing Live Shadow Runtime subprocess."""

from __future__ import annotations

import ctypes
import os
import subprocess
import time
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from axq.dashboard.python_runtime import resolve_project_python
from axq.orchestration.shadow_control import (
    ManagedRuntimeEvent,
    ManagedRuntimeInstance,
    ManagedRuntimeStatus,
    ManagedShadowConfig,
    ShadowRuntimeInstanceGuard,
    SQLiteShadowControlStore,
)
from axq.runtime.state import UTCDateTime


class ProcessIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    pid: int = Field(gt=0)
    creation_token: str = Field(min_length=1)
    executable: Path


class ManagedShadowSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    status: ManagedRuntimeStatus
    instance_id: str | None = None
    config: ManagedShadowConfig | None = None
    process_identity: ProcessIdentity | None = None
    reason_code: str
    error: str | None = None
    occurred_at: UTCDateTime | None = None


class ProcessAdapter(Protocol):
    def spawn(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        log_path: Path,
    ) -> ProcessIdentity: ...

    def inspect(self, pid: int) -> ProcessIdentity | None: ...

    def wait(self, identity: ProcessIdentity, timeout_seconds: float) -> bool: ...

    def terminate(self, identity: ProcessIdentity) -> None: ...


class WindowsProcessAdapter:
    """Windows process operations with PID-reuse-resistant identity checks."""

    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _PROCESS_TERMINATE = 0x0001
    _STILL_ACTIVE = 259

    class _FileTime(ctypes.Structure):
        _fields_ = (("low", ctypes.c_uint32), ("high", ctypes.c_uint32))

    def _open(self, pid: int, access: int) -> int | None:
        if os.name != "nt":  # pragma: no cover - production launcher is Windows-only
            raise RuntimeError("managed Shadow process control requires Windows")
        handle = ctypes.windll.kernel32.OpenProcess(access, False, pid)
        return int(handle) if handle else None

    def inspect(self, pid: int) -> ProcessIdentity | None:
        handle = self._open(pid, self._PROCESS_QUERY_LIMITED_INFORMATION)
        if handle is None:
            return None
        kernel32 = ctypes.windll.kernel32
        try:
            exit_code = ctypes.c_uint32()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return None
            if exit_code.value != self._STILL_ACTIVE:
                return None
            created = self._FileTime()
            exited = self._FileTime()
            kernel = self._FileTime()
            user = self._FileTime()
            if not kernel32.GetProcessTimes(
                handle,
                ctypes.byref(created),
                ctypes.byref(exited),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                return None
            size = ctypes.c_uint32(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not kernel32.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(size)
            ):
                return None
            token = str((created.high << 32) | created.low)
            return ProcessIdentity(pid=pid, creation_token=token, executable=Path(buffer.value))
        finally:
            kernel32.CloseHandle(handle)

    def spawn(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        log_path: Path,
    ) -> ProcessIdentity:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("ab") as log:
            process = subprocess.Popen(  # noqa: S603 - fixed module command built internally
                list(command),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                    if os.name == "nt"
                    else 0
                ),
                close_fds=True,
            )
        for _ in range(50):
            identity = self.inspect(process.pid)
            if identity is not None:
                return identity
            time.sleep(0.02)
        raise RuntimeError("spawned Shadow Runtime identity could not be verified")

    def wait(self, identity: ProcessIdentity, timeout_seconds: float) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self.inspect(identity.pid) is None:
                return True
            time.sleep(0.1)
        return self.inspect(identity.pid) is None

    def terminate(self, identity: ProcessIdentity) -> None:
        current = self.inspect(identity.pid)
        if current != identity:
            raise RuntimeError("process identity changed before forced termination")
        handle = self._open(identity.pid, self._PROCESS_TERMINATE)
        if handle is None:
            raise RuntimeError("verified Shadow Runtime process is no longer available")
        kernel32 = ctypes.windll.kernel32
        try:
            if not kernel32.TerminateProcess(handle, 1):
                raise RuntimeError("forced Shadow Runtime termination failed")
        finally:
            kernel32.CloseHandle(handle)


def _same_process(actual: ProcessIdentity | None, expected: ProcessIdentity) -> bool:
    if actual is None:
        return False
    return (
        actual.pid == expected.pid
        and actual.creation_token == expected.creation_token
        and str(actual.executable.resolve()).casefold()
        == str(expected.executable.resolve()).casefold()
    )


class ShadowRuntimeController:
    """Manage one SHADOW-only process from durable state, never Streamlit session state."""

    def __init__(
        self,
        *,
        control_db: str | Path,
        process_adapter: ProcessAdapter | None = None,
        instance_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.control_db = Path(control_db).resolve()
        self.store = SQLiteShadowControlStore(self.control_db)
        self._processes = process_adapter or WindowsProcessAdapter()
        self._instance_id_factory = instance_id_factory or (lambda: str(uuid.uuid4()))

    def _command_lock(self) -> ShadowRuntimeInstanceGuard:
        return ShadowRuntimeInstanceGuard(self.control_db.parent / ".controller-command")

    @staticmethod
    def _identity(instance: ManagedRuntimeInstance) -> ProcessIdentity:
        return ProcessIdentity(
            pid=instance.pid,
            creation_token=instance.process_creation_token,
            executable=instance.expected_executable,
        )

    def _append(
        self,
        instance_id: str,
        status: ManagedRuntimeStatus,
        *,
        now: UTCDateTime,
        reason_code: str,
        error: str | None = None,
    ) -> ManagedRuntimeEvent:
        value = ManagedRuntimeEvent(
            instance_id=instance_id,
            status=status,
            occurred_at=now,
            reason_code=reason_code,
            error=error,
        )
        latest = self.store.latest_event(instance_id)
        if latest is None or latest != value:
            self.store.append_event(value)
        return value

    def _snapshot_for(
        self,
        instance: ManagedRuntimeInstance,
        event: ManagedRuntimeEvent,
    ) -> ManagedShadowSnapshot:
        return ManagedShadowSnapshot(
            status=event.status,
            instance_id=instance.instance_id,
            config=instance.config,
            process_identity=self._identity(instance),
            reason_code=event.reason_code,
            error=event.error,
            occurred_at=event.occurred_at,
        )

    def status(self, *, now: UTCDateTime) -> ManagedShadowSnapshot:
        instance = self.store.latest_instance()
        if instance is None:
            return ManagedShadowSnapshot(
                status=ManagedRuntimeStatus.STOPPED,
                reason_code="NO_MANAGED_INSTANCE",
                occurred_at=now,
            )
        latest = self.store.latest_event(instance.instance_id)
        if latest is None:
            latest = self._append(
                instance.instance_id,
                ManagedRuntimeStatus.ERROR,
                now=now,
                reason_code="MISSING_LIFECYCLE_STATE",
            )
            return self._snapshot_for(instance, latest)
        expected = self._identity(instance)
        actual = self._processes.inspect(instance.pid)
        terminal = {ManagedRuntimeStatus.STOPPED, ManagedRuntimeStatus.ERROR}
        if actual is None and latest.status not in terminal:
            reason = (
                "GRACEFUL_STOP_CONFIRMED"
                if latest.status is ManagedRuntimeStatus.STOPPING
                and self.store.stop_requested(instance.instance_id)
                else "PROCESS_EXITED_UNEXPECTEDLY"
            )
            status = (
                ManagedRuntimeStatus.STOPPED
                if reason == "GRACEFUL_STOP_CONFIRMED"
                else ManagedRuntimeStatus.ERROR
            )
            latest = self._append(
                instance.instance_id,
                status,
                now=now,
                reason_code=reason,
                error=None if status is ManagedRuntimeStatus.STOPPED else "Shadow Runtime exited",
            )
        elif actual is not None and not _same_process(actual, expected):
            latest = self._append(
                instance.instance_id,
                ManagedRuntimeStatus.ERROR,
                now=now,
                reason_code="PROCESS_IDENTITY_MISMATCH",
                error="Registered PID now belongs to a different process",
            )
        return self._snapshot_for(instance, latest)

    def _command(self, config: ManagedShadowConfig, instance_id: str) -> tuple[str, ...]:
        return (
            str(config.python_executable),
            str(config.project_root / "scripts/run_shadow_runtime.py"),
            "--gold-symbols",
            ",".join(config.gold_symbols),
            "--terminal-path",
            str(config.terminal_path),
            "--output-dir",
            str(config.output_dir),
            "--poll-seconds",
            str(config.poll_seconds),
            "--managed-instance-id",
            instance_id,
            "--control-db",
            str(self.control_db),
        )

    def start(self, config: ManagedShadowConfig, *, now: UTCDateTime) -> ManagedShadowSnapshot:
        with self._command_lock():
            current = self.status(now=now)
            if current.process_identity is not None and _same_process(
                self._processes.inspect(current.process_identity.pid),
                current.process_identity,
            ):
                return current
            if current.status in {
                ManagedRuntimeStatus.STARTING,
                ManagedRuntimeStatus.RUNNING,
                ManagedRuntimeStatus.WAITING_FOR_MARKET,
                ManagedRuntimeStatus.STOPPING,
            }:
                return current
            resolve_project_python(config.project_root, config.python_executable)
            instance_id = self._instance_id_factory()
            identity = self._processes.spawn(
                self._command(config, instance_id),
                cwd=config.project_root,
                log_path=config.output_dir / "shadow-runtime.log",
            )
            instance = ManagedRuntimeInstance(
                instance_id=instance_id,
                config=config,
                pid=identity.pid,
                process_creation_token=identity.creation_token,
                expected_executable=identity.executable,
                registered_at=now,
            )
            try:
                self.store.register_instance(instance)
                event = self._append(
                    instance_id,
                    ManagedRuntimeStatus.STARTING,
                    now=now,
                    reason_code="PROCESS_SPAWNED",
                )
            except Exception:
                actual = self._processes.inspect(identity.pid)
                if _same_process(actual, identity):
                    self._processes.terminate(identity)
                raise
            return self._snapshot_for(instance, event)

    def stop(
        self,
        *,
        now: UTCDateTime,
        grace_seconds: float = 15.0,
    ) -> ManagedShadowSnapshot:
        with self._command_lock():
            current = self.status(now=now)
            if current.instance_id is None or current.process_identity is None:
                return current
            if current.status in {ManagedRuntimeStatus.STOPPED, ManagedRuntimeStatus.ERROR}:
                return current
            expected = current.process_identity
            actual = self._processes.inspect(expected.pid)
            if not _same_process(actual, expected):
                event = self._append(
                    current.instance_id,
                    ManagedRuntimeStatus.ERROR,
                    now=now,
                    reason_code="PROCESS_IDENTITY_MISMATCH",
                    error="Stop refused because exact process identity was not verified",
                )
                instance = self.store.latest_instance()
                assert instance is not None
                return self._snapshot_for(instance, event)
            self.store.request_stop(current.instance_id, requested_at=now)
            self._append(
                current.instance_id,
                ManagedRuntimeStatus.STOPPING,
                now=now,
                reason_code="GRACEFUL_STOP_REQUESTED",
            )
            if self._processes.wait(expected, grace_seconds):
                event = self._append(
                    current.instance_id,
                    ManagedRuntimeStatus.STOPPED,
                    now=now,
                    reason_code="GRACEFUL_STOP_CONFIRMED",
                )
            else:
                actual = self._processes.inspect(expected.pid)
                if not _same_process(actual, expected):
                    event = self._append(
                        current.instance_id,
                        ManagedRuntimeStatus.ERROR,
                        now=now,
                        reason_code="PROCESS_IDENTITY_MISMATCH",
                        error="Forced stop refused after process identity changed",
                    )
                else:
                    self._processes.terminate(expected)
                    event = self._append(
                        current.instance_id,
                        ManagedRuntimeStatus.ERROR,
                        now=now,
                        reason_code="FORCED_STOP_AFTER_TIMEOUT",
                        error="Graceful shutdown timed out; exact process was terminated",
                    )
            instance = self.store.latest_instance()
            assert instance is not None
            return self._snapshot_for(instance, event)

    def restart(
        self,
        config: ManagedShadowConfig,
        *,
        now: UTCDateTime,
        grace_seconds: float = 15.0,
    ) -> ManagedShadowSnapshot:
        stopped = self.stop(now=now, grace_seconds=grace_seconds)
        if stopped.status is not ManagedRuntimeStatus.STOPPED:
            return stopped
        return self.start(config, now=now)

    def record_runtime_status(
        self,
        instance_id: str,
        status: ManagedRuntimeStatus,
        *,
        now: UTCDateTime,
        reason_code: str,
        error: str | None = None,
    ) -> None:
        self._append(
            instance_id,
            status,
            now=now,
            reason_code=reason_code,
            error=error,
        )


def default_managed_shadow_config(project_root: str | Path) -> ManagedShadowConfig:
    """Return the explicit approved local defaults without filesystem discovery."""
    root = Path(project_root).resolve()
    python_executable = resolve_project_python(root)
    return ManagedShadowConfig(
        project_root=root,
        python_executable=python_executable,
        terminal_path=Path("C:/Program Files/MetaTrader/terminal64.exe"),
        gold_symbols=("XAUUSD", "XAUUSD.sc", "GOLD"),
        output_dir=root / "runtime/live-shadow",
        poll_seconds=2.0,
    )


__all__ = [
    "ManagedShadowSnapshot",
    "ProcessAdapter",
    "ProcessIdentity",
    "ShadowRuntimeController",
    "WindowsProcessAdapter",
    "default_managed_shadow_config",
]
