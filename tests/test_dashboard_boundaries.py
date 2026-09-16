"""Static isolation checks for the read-only dashboard MVP."""

from __future__ import annotations

import ast
from pathlib import Path


def test_dashboard_has_no_mutating_backend_imports_or_calls() -> None:
    files = tuple(Path("src/axq/dashboard").glob("*.py"))
    forbidden_imports = {
        "axq.database",
        "axq.execution_boundary.persistence",
        "axq.mt5",
        "axq.orchestration.service",
        "axq.reasoning.service",
        "axq.reasoning.store",
    }
    forbidden_calls = {
        "append_attempt",
        "append_request",
        "append_response",
        "complete",
        "migrate",
        "order_check",
        "order_send",
        "run_reflection_explanation",
    }
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert not imports & forbidden_imports
        assert not calls & forbidden_calls


def test_dashboard_uses_no_filesystem_discovery() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/axq/dashboard").glob("*.py")
    )
    for forbidden in ("glob(", "rglob(", "os.walk", "Get-ChildItem"):
        assert forbidden not in text
