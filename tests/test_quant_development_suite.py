from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from axq.quant.development.config import SuiteConfig
from axq.quant.development.suite import run_suite


def test_suite_continues_after_failure_and_skips_completed_on_resume(tmp_path: Path) -> None:
    configs = [tmp_path / "a.yaml", tmp_path / "b.yaml", tmp_path / "c.yaml"]
    for path in configs:
        path.write_text("name: test", encoding="utf-8")
    calls: list[str] = []

    def executor(path: Path) -> SimpleNamespace:
        calls.append(path.stem)
        if path.stem == "b":
            raise RuntimeError("controlled failure")
        return SimpleNamespace(run_id=f"run-{path.stem}", run_dir=tmp_path / path.stem)

    config = SuiteConfig(
        name="tiny-suite",
        experiments=configs,
        output_root=tmp_path / "suite-output",
        continue_on_failure=True,
        resume=True,
    )
    first = run_suite(config, executor=executor)
    second = run_suite(config, executor=executor)

    assert [item["status"] for item in first["runs"]] == [
        "COMPLETE",
        "FAILED",
        "COMPLETE",
    ]
    assert [item["status"] for item in second["runs"]] == [
        "SKIPPED_COMPLETE",
        "FAILED",
        "SKIPPED_COMPLETE",
    ]
    assert calls == ["a", "b", "c", "b"]
