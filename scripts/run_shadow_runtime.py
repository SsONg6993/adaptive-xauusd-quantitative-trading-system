"""Run the worktree-local Shadow Runtime with the validated project Python."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root / "src"))
    from axq.orchestration.shadow_runtime import main as shadow_main

    shadow_main()


if __name__ == "__main__":
    main()
