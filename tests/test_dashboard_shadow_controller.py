from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from axq.dashboard.shadow_controller import (
    ManagedShadowSnapshot,
    ProcessIdentity,
    ShadowRuntimeController,
    default_managed_shadow_config,
)
from axq.orchestration.shadow_control import (
    ManagedRuntimeEvent,
    ManagedRuntimeInstance,
    ManagedRuntimeStatus,
    ManagedShadowConfig,
)

T0 = datetime(2026, 9, 14, 7, 0, tzinfo=UTC)


def _config(tmp_path: Path) -> ManagedShadowConfig:
    python = tmp_path / ".venv/Scripts/python.exe"
    python.parent.mkdir(parents=True, exist_ok=True)
    if not python.exists():
        python.write_bytes(b"valid-python")
    return ManagedShadowConfig(
        project_root=tmp_path,
        python_executable=python,
        terminal_path=Path("C:/Program Files/MetaTrader 5/terminal64.exe"),
        gold_symbols=("XAUUSD", "XAUUSD.sc", "GOLD"),
        output_dir=tmp_path / "runtime/live-shadow",
        poll_seconds=2.0,
    )


class FakeProcesses:
    def __init__(self) -> None:
        self.spawn_count = 0
        self.identities: dict[int, ProcessIdentity] = {}
        self.wait_result = True
        self.terminated: list[ProcessIdentity] = []
        self.commands: list[tuple[str, ...]] = []

    def spawn(self, command, *, cwd, log_path):
        del cwd, log_path
        self.spawn_count += 1
        self.commands.append(tuple(command))
        identity = ProcessIdentity(
            pid=1000 + self.spawn_count,
            creation_token=f"created-{self.spawn_count}",
            executable=Path(command[0]),
        )
        self.identities[identity.pid] = identity
        return identity

    def inspect(self, pid: int):
        return self.identities.get(pid)

    def wait(self, identity: ProcessIdentity, timeout_seconds: float) -> bool:
        del timeout_seconds
        if self.wait_result:
            self.identities.pop(identity.pid, None)
        return self.wait_result

    def terminate(self, identity: ProcessIdentity) -> None:
        self.terminated.append(identity)
        self.identities.pop(identity.pid, None)


def _controller(tmp_path: Path, processes: FakeProcesses) -> ShadowRuntimeController:
    return ShadowRuntimeController(
        control_db=tmp_path / "runtime/live-shadow/shadow-control.sqlite3",
        process_adapter=processes,
        instance_id_factory=lambda: "managed-instance-1",
    )


def test_repeated_start_and_new_controller_after_ui_rerun_reuse_one_process(
    tmp_path: Path,
) -> None:
    processes = FakeProcesses()
    first_controller = _controller(tmp_path, processes)
    first = first_controller.start(_config(tmp_path), now=T0)
    repeated = first_controller.start(_config(tmp_path), now=T0)
    rerun_controller = _controller(tmp_path, processes)
    after_browser_refresh = rerun_controller.status(now=T0)

    assert processes.spawn_count == 1
    assert first.status is ManagedRuntimeStatus.STARTING
    assert repeated.instance_id == first.instance_id
    assert after_browser_refresh.instance_id == first.instance_id
    assert after_browser_refresh.status is ManagedRuntimeStatus.STARTING
    assert processes.commands[0][1].replace("\\", "/").endswith(
        "scripts/run_shadow_runtime.py"
    )


def test_controller_passes_only_exact_shadow_configuration(tmp_path: Path) -> None:
    processes = FakeProcesses()
    controller = _controller(tmp_path, processes)

    controller.start(_config(tmp_path), now=T0)

    command = processes.commands[0]
    assert command[1].replace("\\", "/").endswith("scripts/run_shadow_runtime.py")
    assert command[command.index("--gold-symbols") + 1] == "XAUUSD,XAUUSD.sc,GOLD"
    assert command[command.index("--poll-seconds") + 1] == "2.0"
    assert "DEMO" not in command
    assert "LIVE" not in command


def test_graceful_stop_requests_only_the_exact_current_instance(tmp_path: Path) -> None:
    processes = FakeProcesses()
    controller = _controller(tmp_path, processes)
    started = controller.start(_config(tmp_path), now=T0)

    stopped = controller.stop(now=T0, grace_seconds=1.0)

    assert stopped.status is ManagedRuntimeStatus.STOPPED
    assert controller.store.stop_requested(started.instance_id) is True
    assert processes.terminated == []


def test_forced_stop_reverifies_full_identity_and_blocks_automatic_restart(
    tmp_path: Path,
) -> None:
    processes = FakeProcesses()
    processes.wait_result = False
    controller = _controller(tmp_path, processes)
    started = controller.start(_config(tmp_path), now=T0)

    result = controller.restart(_config(tmp_path), now=T0, grace_seconds=0.0)

    assert result.status is ManagedRuntimeStatus.ERROR
    assert result.reason_code == "FORCED_STOP_AFTER_TIMEOUT"
    assert processes.terminated == [started.process_identity]
    assert processes.spawn_count == 1


def test_identity_mismatch_is_never_terminated(tmp_path: Path) -> None:
    processes = FakeProcesses()
    processes.wait_result = False
    controller = _controller(tmp_path, processes)
    started = controller.start(_config(tmp_path), now=T0)
    assert started.process_identity is not None
    processes.identities[started.process_identity.pid] = ProcessIdentity(
        pid=started.process_identity.pid,
        creation_token="different-process",
        executable=started.process_identity.executable,
    )

    result = controller.stop(now=T0, grace_seconds=0.0)

    assert result.status is ManagedRuntimeStatus.ERROR
    assert result.reason_code == "PROCESS_IDENTITY_MISMATCH"
    assert processes.terminated == []


def test_status_maps_persisted_market_wait_to_waiting_without_spawning(tmp_path: Path) -> None:
    processes = FakeProcesses()
    controller = _controller(tmp_path, processes)
    started = controller.start(_config(tmp_path), now=T0)
    controller.record_runtime_status(
        started.instance_id,
        ManagedRuntimeStatus.WAITING_FOR_MARKET,
        now=T0,
        reason_code="STALE_QUOTE",
    )

    snapshot = controller.status(now=T0)

    assert isinstance(snapshot, ManagedShadowSnapshot)
    assert snapshot.status is ManagedRuntimeStatus.WAITING_FOR_MARKET
    assert processes.spawn_count == 1


def test_start_never_spawns_over_an_exact_registered_process(tmp_path: Path) -> None:
    processes = FakeProcesses()
    controller = _controller(tmp_path, processes)
    started = controller.start(_config(tmp_path), now=T0)
    controller.record_runtime_status(
        started.instance_id,
        ManagedRuntimeStatus.ERROR,
        now=T0,
        reason_code="RUNTIME_CRASH_REPORTED",
    )

    result = controller.start(_config(tmp_path), now=T0)

    assert result.instance_id == started.instance_id
    assert result.status is ManagedRuntimeStatus.ERROR
    assert processes.spawn_count == 1


def test_repeated_start_reuses_running_instance_before_validating_new_config(
    tmp_path: Path,
) -> None:
    processes = FakeProcesses()
    controller = _controller(tmp_path, processes)
    started = controller.start(_config(tmp_path), now=T0)
    invalid = tmp_path / "invalid/python.exe"
    invalid.parent.mkdir(parents=True)
    invalid.touch()
    changed_config = _config(tmp_path).model_copy(update={"python_executable": invalid})

    repeated = controller.start(changed_config, now=T0)

    assert repeated.instance_id == started.instance_id
    assert processes.spawn_count == 1


def test_default_operator_configuration_matches_approved_local_workflow(tmp_path: Path) -> None:
    shared_venv = tmp_path / ".venv/Scripts/python.exe"
    shared_venv.parent.mkdir(parents=True)
    shared_venv.write_bytes(b"valid-python")

    config = default_managed_shadow_config(tmp_path)

    assert config.gold_symbols == ("XAUUSD", "XAUUSD.sc", "GOLD")
    assert config.terminal_path == Path("C:/Program Files/MetaTrader/terminal64.exe")
    assert config.output_dir == tmp_path / "runtime/live-shadow"
    assert config.poll_seconds == 2.0
    assert config.python_executable == shared_venv


def test_default_configuration_skips_zero_byte_local_python_for_shared_venv(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "Project With Spaces/.worktrees/phase-nine"
    local = worktree / ".venv/Scripts/python.exe"
    local.parent.mkdir(parents=True)
    local.touch()
    shared = worktree.parent.parent / ".venv/Scripts/python.exe"
    shared.parent.mkdir(parents=True)
    shared.write_bytes(b"valid-python")

    config = default_managed_shadow_config(worktree)

    assert config.python_executable == shared.resolve()


def test_controller_rejects_invalid_python_before_process_spawn(tmp_path: Path) -> None:
    processes = FakeProcesses()
    invalid = tmp_path / ".venv/Scripts/python.exe"
    invalid.parent.mkdir(parents=True)
    invalid.touch()
    config = _config(tmp_path).model_copy(update={"python_executable": invalid})
    controller = _controller(tmp_path, processes)

    with pytest.raises(FileNotFoundError, match="Configured Python executable was not found"):
        controller.start(config, now=T0)

    assert processes.spawn_count == 0


def test_start_terminates_exact_spawned_process_when_registration_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processes = FakeProcesses()
    controller = _controller(tmp_path, processes)

    def fail_registration(instance: ManagedRuntimeInstance) -> None:
        del instance
        raise RuntimeError("registration failed")

    monkeypatch.setattr(controller.store, "register_instance", fail_registration)

    with pytest.raises(RuntimeError, match="registration failed"):
        controller.start(_config(tmp_path), now=T0)

    assert processes.spawn_count == 1
    assert len(processes.terminated) == 1
    assert processes.inspect(processes.terminated[0].pid) is None


def test_shared_python_and_module_are_separate_argv_with_space_safe_paths(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "Project With Spaces/.worktrees/phase-nine"
    worktree.mkdir(parents=True)
    shared = worktree.parent.parent / ".venv/Scripts/python.exe"
    shared.parent.mkdir(parents=True)
    shared.write_bytes(b"valid-python")
    processes = FakeProcesses()
    controller = ShadowRuntimeController(
        control_db=worktree / "runtime/live-shadow/shadow-control.sqlite3",
        process_adapter=processes,
        instance_id_factory=lambda: "managed-space-instance",
    )

    controller.start(default_managed_shadow_config(worktree), now=T0)

    command = processes.commands[0]
    assert command[0] == str(shared.resolve())
    assert command[1] == str(worktree / "scripts/run_shadow_runtime.py")


def test_dead_stale_registry_with_invalid_python_does_not_control_new_start(
    tmp_path: Path,
) -> None:
    worktree = tmp_path / "Project With Spaces/.worktrees/phase-nine"
    worktree.mkdir(parents=True)
    invalid = worktree / ".venv/Scripts/python.exe"
    invalid.parent.mkdir(parents=True)
    invalid.touch()
    shared = worktree.parent.parent / ".venv/Scripts/python.exe"
    shared.parent.mkdir(parents=True)
    shared.write_bytes(b"valid-python")
    processes = FakeProcesses()
    controller = ShadowRuntimeController(
        control_db=worktree / "runtime/live-shadow/shadow-control.sqlite3",
        process_adapter=processes,
        instance_id_factory=lambda: "replacement-instance",
    )
    stale_config = ManagedShadowConfig(
        project_root=worktree,
        python_executable=invalid,
        terminal_path=Path("C:/Program Files/MetaTrader 5/terminal64.exe"),
        gold_symbols=("XAUUSD",),
        output_dir=worktree / "runtime/live-shadow",
        poll_seconds=2.0,
    )
    controller.store.register_instance(
        ManagedRuntimeInstance(
            instance_id="stale-instance",
            config=stale_config,
            pid=9999,
            process_creation_token="dead-process",
            expected_executable=invalid,
            registered_at=T0,
        )
    )
    controller.store.append_event(
        ManagedRuntimeEvent(
            instance_id="stale-instance",
            status=ManagedRuntimeStatus.STARTING,
            occurred_at=T0,
            reason_code="OLD_PROCESS",
        )
    )

    result = controller.start(default_managed_shadow_config(worktree), now=T0)

    assert result.instance_id == "replacement-instance"
    assert processes.commands[0][0] == str(shared.resolve())
