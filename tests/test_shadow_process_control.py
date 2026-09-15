from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from axq.orchestration.shadow_control import (
    ManagedRuntimeControl,
    ManagedRuntimeEvent,
    ManagedRuntimeInstance,
    ManagedRuntimeStatus,
    ManagedShadowConfig,
    ShadowRuntimeInstanceGuard,
    SQLiteShadowControlStore,
)

T0 = datetime(2026, 9, 14, 7, 0, tzinfo=UTC)


def _config(tmp_path: Path) -> ManagedShadowConfig:
    return ManagedShadowConfig(
        project_root=tmp_path,
        python_executable=tmp_path / ".venv/Scripts/python.exe",
        terminal_path=Path("C:/Program Files/MetaTrader 5/terminal64.exe"),
        gold_symbols=("XAUUSD", "XAUUSD.sc", "GOLD"),
        output_dir=tmp_path / "runtime/live-shadow",
        poll_seconds=2.0,
    )


def _instance(tmp_path: Path, instance_id: str, pid: int = 1234) -> ManagedRuntimeInstance:
    return ManagedRuntimeInstance(
        instance_id=instance_id,
        config=_config(tmp_path),
        pid=pid,
        process_creation_token=f"creation-{pid}",
        expected_executable=tmp_path / ".venv/Scripts/python.exe",
        registered_at=T0,
    )


def test_stop_request_is_bound_to_exact_runtime_instance(tmp_path: Path) -> None:
    store = SQLiteShadowControlStore(tmp_path / "control.sqlite3")
    old = _instance(tmp_path, "instance-old")
    new = _instance(tmp_path, "instance-new", pid=5678)
    store.register_instance(old)
    store.request_stop(old.instance_id, requested_at=T0)
    store.register_instance(new)

    assert store.stop_requested(old.instance_id) is True
    assert store.stop_requested(new.instance_id) is False


def test_lifecycle_history_is_append_only_and_latest_status_is_replayed(tmp_path: Path) -> None:
    store = SQLiteShadowControlStore(tmp_path / "control.sqlite3")
    instance = _instance(tmp_path, "instance-a")
    store.register_instance(instance)
    starting = ManagedRuntimeEvent(
        instance_id=instance.instance_id,
        status=ManagedRuntimeStatus.STARTING,
        occurred_at=T0,
        reason_code="PROCESS_SPAWNED",
    )
    running = ManagedRuntimeEvent(
        instance_id=instance.instance_id,
        status=ManagedRuntimeStatus.RUNNING,
        occurred_at=T0,
        reason_code="RUNTIME_READY",
    )
    store.append_event(starting)
    store.append_event(running)

    assert store.latest_instance() == instance
    assert store.events(instance.instance_id) == (starting, running)
    assert store.latest_event(instance.instance_id) == running
    assert store.connection_for_tests().execute(
        "SELECT COUNT(*) FROM shadow_control_events"
    ).fetchone()[0] == 2
    with pytest.raises(Exception, match="append-only"):
        store.connection_for_tests().execute("DELETE FROM shadow_control_events")


def test_runtime_process_holds_singleton_guard_for_resolved_output_directory(
    tmp_path: Path,
) -> None:
    output = tmp_path / "runtime/live-shadow"
    first = ShadowRuntimeInstanceGuard(output)
    second = ShadowRuntimeInstanceGuard(output)

    first.acquire()
    try:
        with pytest.raises(RuntimeError, match="already running"):
            second.acquire()
    finally:
        first.release()

    second.acquire()
    second.release()


def test_singleton_guard_rejects_a_second_real_process(tmp_path: Path) -> None:
    output = tmp_path / "runtime/live-shadow"
    child_code = (
        "import sys; "
        "from axq.orchestration.shadow_control import ShadowRuntimeInstanceGuard; "
        "guard=ShadowRuntimeInstanceGuard(sys.argv[1]); guard.acquire(); "
        "print('READY', flush=True); sys.stdin.readline(); guard.release()"
    )
    child = subprocess.Popen(
        [sys.executable, "-c", child_code, str(output)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=dict(os.environ),
    )
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "READY"
        with pytest.raises(RuntimeError, match="already running"):
            ShadowRuntimeInstanceGuard(output).acquire()
    finally:
        if child.stdin is not None:
            child.stdin.write("\n")
            child.stdin.flush()
        try:
            child.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5.0)

    assert child.returncode == 0


def test_heartbeat_time_is_excluded_from_event_semantic_identity() -> None:
    first = ManagedRuntimeEvent(
        instance_id="instance-a",
        status=ManagedRuntimeStatus.RUNNING,
        occurred_at=T0,
        reason_code="RUNTIME_HEARTBEAT",
    )
    later = first.model_copy(update={"event_id": "", "occurred_at": T0.replace(minute=1)})
    later = ManagedRuntimeEvent.model_validate(later.model_dump())

    assert later.event_id == first.event_id


def test_runtime_control_observes_only_its_exact_stop_request(tmp_path: Path) -> None:
    store = SQLiteShadowControlStore(tmp_path / "control.sqlite3")
    old = _instance(tmp_path, "instance-old")
    current = _instance(tmp_path, "instance-current", pid=9999)
    store.register_instance(old)
    store.request_stop(old.instance_id, requested_at=T0)
    store.register_instance(current)
    control = ManagedRuntimeControl(store, current.instance_id)

    assert control.stop_requested() is False
    store.request_stop(current.instance_id, requested_at=T0)
    assert control.stop_requested() is True


def test_runtime_control_records_waiting_heartbeat_without_semantic_runtime_data(
    tmp_path: Path,
) -> None:
    store = SQLiteShadowControlStore(tmp_path / "control.sqlite3")
    instance = _instance(tmp_path, "instance-current")
    store.register_instance(instance)
    control = ManagedRuntimeControl(store, instance.instance_id)

    control.record(
        ManagedRuntimeStatus.WAITING_FOR_MARKET,
        now=T0,
        reason_code="STALE_QUOTE",
    )

    event = store.latest_event(instance.instance_id)
    assert event is not None
    assert event.status is ManagedRuntimeStatus.WAITING_FOR_MARKET
    assert set(type(event).model_fields) == {
        "schema_version",
        "event_id",
        "instance_id",
        "status",
        "occurred_at",
        "reason_code",
        "error",
    }
