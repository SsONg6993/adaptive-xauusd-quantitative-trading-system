"""Operator entrypoint for starting or reusing the local AXQ dashboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--python-executable", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    project_root = args.project_root.resolve()
    sys.path.insert(0, str(project_root / "src"))
    from axq.dashboard.launcher import DashboardLauncher, resolve_project_python

    try:
        python_executable = resolve_project_python(project_root, args.python_executable)
    except FileNotFoundError as error:
        print(f"Unable to start AXQ Dashboard: {error}")
        return 2

    result = DashboardLauncher(
        project_root=project_root,
        python_executable=python_executable,
        registry_path=project_root / "runtime/dashboard/dashboard-launch.sqlite3",
    ).launch()
    print(f"AXQ Dashboard {result.status.value}: {result.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
