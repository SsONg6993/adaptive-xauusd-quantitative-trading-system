from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from axq.dashboard.launcher import (
    DashboardLauncher,
    DashboardLaunchStatus,
    SQLiteDashboardLaunchStore,
    resolve_project_python,
)
from axq.dashboard.shadow_controller import ProcessIdentity

T0 = datetime(2026, 9, 14, 7, 0, tzinfo=UTC)


class FakeProcesses:
    def __init__(self) -> None:
        self.spawn_count = 0
        self.identities: dict[int, ProcessIdentity] = {}
        self.commands: list[tuple[str, ...]] = []
        self.terminated: list[ProcessIdentity] = []

    def spawn(self, command, *, cwd, log_path):
        del cwd, log_path
        self.spawn_count += 1
        self.commands.append(tuple(command))
        identity = ProcessIdentity(
            pid=2000 + self.spawn_count,
            creation_token=f"dashboard-{self.spawn_count}",
            executable=Path(command[0]),
        )
        self.identities[identity.pid] = identity
        return identity

    def inspect(self, pid: int):
        return self.identities.get(pid)

    def wait(self, identity, timeout_seconds):  # pragma: no cover - launcher never stops UI
        raise AssertionError((identity, timeout_seconds))

    def terminate(self, identity):
        self.terminated.append(identity)
        self.identities.pop(identity.pid, None)


def _launcher(tmp_path: Path, processes: FakeProcesses, opened: list[str]) -> DashboardLauncher:
    python = tmp_path / ".venv/Scripts/python.exe"
    python.parent.mkdir(parents=True, exist_ok=True)
    python.touch()
    launch_ids = iter(("dashboard-launch-1", "dashboard-launch-2"))
    return DashboardLauncher(
        project_root=tmp_path,
        python_executable=python,
        registry_path=tmp_path / "runtime/dashboard/dashboard-launch.sqlite3",
        process_adapter=processes,
        health_probe=lambda _url: processes.spawn_count > 0,
        browser_opener=opened.append,
        launch_id_factory=lambda: next(launch_ids),
    )


def test_launcher_reuses_verified_healthy_streamlit_across_invocations(tmp_path: Path) -> None:
    processes = FakeProcesses()
    opened: list[str] = []

    first = _launcher(tmp_path, processes, opened).launch(now=T0)
    second = _launcher(tmp_path, processes, opened).launch(now=T0)

    assert first.status is DashboardLaunchStatus.STARTED
    assert second.status is DashboardLaunchStatus.REUSED
    assert second.launch_id == first.launch_id
    assert processes.spawn_count == 1
    assert processes.terminated == []
    assert opened == ["http://127.0.0.1:8501", "http://127.0.0.1:8501"]
    assert "scripts/run_dashboard.py" in processes.commands[0][1].replace("\\", "/")


def test_launcher_terminates_exact_new_process_when_readiness_fails(
    tmp_path: Path,
) -> None:
    processes = FakeProcesses()
    python = tmp_path / ".venv/Scripts/python.exe"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"python")
    launcher = DashboardLauncher(
        project_root=tmp_path,
        python_executable=python,
        registry_path=tmp_path / "runtime/dashboard/dashboard-launch.sqlite3",
        process_adapter=processes,
        health_probe=lambda _url: False,
        browser_opener=lambda _url: None,
        readiness_attempts=1,
    )

    with pytest.raises(RuntimeError, match="did not become ready"):
        launcher.launch(now=T0)

    assert processes.spawn_count == 1
    assert len(processes.terminated) == 1
    assert processes.inspect(processes.terminated[0].pid) is None


def test_launcher_does_not_reuse_pid_with_changed_creation_identity(tmp_path: Path) -> None:
    processes = FakeProcesses()
    opened: list[str] = []
    launcher = _launcher(tmp_path, processes, opened)
    first = launcher.launch(now=T0)
    assert first.process_identity is not None
    processes.identities[first.process_identity.pid] = ProcessIdentity(
        pid=first.process_identity.pid,
        creation_token="pid-reused",
        executable=first.process_identity.executable,
    )

    launcher._health = lambda _url: processes.spawn_count >= 2
    second = launcher.launch(now=T0)

    assert second.status is DashboardLaunchStatus.STARTED
    assert processes.spawn_count == 2


def test_launcher_refuses_unregistered_healthy_streamlit_port(tmp_path: Path) -> None:
    processes = FakeProcesses()
    opened: list[str] = []
    python = tmp_path / ".venv/Scripts/python.exe"
    python.parent.mkdir(parents=True, exist_ok=True)
    python.touch()
    launcher = DashboardLauncher(
        project_root=tmp_path,
        python_executable=python,
        registry_path=tmp_path / "runtime/dashboard/dashboard-launch.sqlite3",
        process_adapter=processes,
        health_probe=lambda _url: True,
        browser_opener=opened.append,
        readiness_attempts=1,
    )

    with pytest.raises(RuntimeError, match="not owned by the durable AXQ registry"):
        launcher.launch(now=T0)

    assert processes.spawn_count == 0


def test_launcher_fails_closed_when_registered_process_is_alive_but_unhealthy(
    tmp_path: Path,
) -> None:
    processes = FakeProcesses()
    opened: list[str] = []
    launcher = _launcher(tmp_path, processes, opened)
    launcher.launch(now=T0)
    unhealthy = DashboardLauncher(
        project_root=tmp_path,
        python_executable=tmp_path / ".venv/Scripts/python.exe",
        registry_path=tmp_path / "runtime/dashboard/dashboard-launch.sqlite3",
        process_adapter=processes,
        health_probe=lambda _url: False,
        browser_opener=opened.append,
        launch_id_factory=lambda: "dashboard-launch-2",
        readiness_attempts=1,
    )

    with pytest.raises(RuntimeError, match="alive but Streamlit health check failed"):
        unhealthy.launch(now=T0)

    assert processes.spawn_count == 1
    assert len(processes.terminated) == 1


def test_dashboard_launch_registry_is_append_only_and_idempotent(tmp_path: Path) -> None:
    processes = FakeProcesses()
    opened: list[str] = []
    launcher = _launcher(tmp_path, processes, opened)
    result = launcher.launch(now=T0)
    store = SQLiteDashboardLaunchStore(
        tmp_path / "runtime/dashboard/dashboard-launch.sqlite3"
    )
    record = store.latest()
    assert record is not None

    store.append(record)
    assert store.latest() == record
    with pytest.raises(Exception, match="append-only"):
        store.connection_for_tests().execute(
            "UPDATE dashboard_launches SET record_json = ? WHERE launch_id = ?",
            ("{}", result.launch_id),
        )


def test_windows_one_click_entrypoints_are_fixed_and_operator_safe() -> None:
    command = Path("Start AXQ Dashboard.cmd").read_text(encoding="utf-8")
    starter = Path("scripts/start_axq_dashboard.py").read_text(encoding="utf-8")
    runner = Path("scripts/run_dashboard.py").read_text(encoding="utf-8")
    shadow_runner = Path("scripts/run_shadow_runtime.py").read_text(encoding="utf-8")

    assert "%~dp0" in command
    assert 'for %%I in ("%~dp0.") do set "PROJECT_ROOT=%%~fI"' in command
    assert command.count('for %%I in ("%AXQ_PYTHON%") do if %%~zI GTR 0') == 2
    assert command.index("%%~zI GTR 0") < command.index('"%AXQ_PYTHON%" --version')
    assert "start_axq_dashboard.py" in command
    assert '"%PROJECT_ROOT%\\scripts\\start_axq_dashboard.py"' in command
    assert "--python-executable" not in command
    assert "DashboardLauncher" in starter
    assert 'parser.add_argument("--python-executable", type=Path)' in starter
    assert 'required=True)' not in starter.split('--python-executable", type=Path', 1)[1][:40]
    assert "webbrowser" not in starter
    assert "axq.dashboard.app.py" not in runner
    assert "streamlit" in runner
    assert "axq.orchestration.shadow_runtime" in shadow_runner
    assert "order_send" not in (command + starter + runner + shadow_runner)


def test_project_python_prefers_root_local_venv(tmp_path: Path) -> None:
    root = tmp_path / "project/.worktrees/phase-nine"
    root.mkdir(parents=True)
    local = root / ".venv/Scripts/python.exe"
    shared = root.parent.parent / ".venv/Scripts/python.exe"
    local.parent.mkdir(parents=True)
    local.write_bytes(b"python")
    shared.parent.mkdir(parents=True, exist_ok=True)
    shared.write_bytes(b"python")

    assert resolve_project_python(root) == local.resolve()


def test_project_python_resolves_worktree_shared_venv_with_spaces(tmp_path: Path) -> None:
    root = tmp_path / "Project With Spaces/.worktrees/phase-nine"
    root.mkdir(parents=True)
    shared = root.parent.parent / ".venv/Scripts/python.exe"
    shared.parent.mkdir(parents=True)
    shared.write_bytes(b"python")

    assert resolve_project_python(root) == shared.resolve()


def test_project_python_accepts_existing_explicit_override(tmp_path: Path) -> None:
    override = tmp_path / "Explicit Python/python.exe"
    override.parent.mkdir(parents=True)
    override.write_bytes(b"python")

    assert resolve_project_python(tmp_path, override) == override.resolve()


def test_project_python_fails_cleanly_when_approved_candidates_are_missing(
    tmp_path: Path,
) -> None:
    root = tmp_path / "missing/.worktrees/phase-nine"
    root.mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="AXQ project virtual environment was not found"):
        resolve_project_python(root)


def test_project_python_skips_empty_local_candidate_for_valid_shared_venv(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project/.worktrees/phase-nine"
    root.mkdir(parents=True)
    local = root / ".venv/Scripts/python.exe"
    local.parent.mkdir(parents=True)
    local.touch()
    shared = root.parent.parent / ".venv/Scripts/python.exe"
    shared.parent.mkdir(parents=True)
    shared.write_bytes(b"python")

    assert resolve_project_python(root) == shared.resolve()
