"""Explicit, structurally validated Python executable resolution for AXQ operators."""

from __future__ import annotations

from pathlib import Path


def _viable_python(candidate: Path) -> bool:
    return candidate.is_file() and candidate.stat().st_size > 0


def resolve_project_python(
    project_root: str | Path,
    explicit_override: str | Path | None = None,
) -> Path:
    """Resolve only the approved local or shared AXQ virtual-environment Python."""
    root = Path(project_root).resolve()
    if explicit_override is not None:
        override = Path(explicit_override).resolve()
        if _viable_python(override):
            return override
        raise FileNotFoundError(f"Configured Python executable was not found: {override}")
    candidates = (
        root / ".venv/Scripts/python.exe",
        root.parent.parent / ".venv/Scripts/python.exe",
    )
    for candidate in candidates:
        if _viable_python(candidate):
            return candidate.resolve()
    raise FileNotFoundError(
        "AXQ project virtual environment was not found. Expected .venv in the "
        "project root or its approved parent repository."
    )


__all__ = ["resolve_project_python"]
