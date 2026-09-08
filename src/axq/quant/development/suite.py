"""Failure-isolated, resumable local experiment suites."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from axq.quant.development.artifacts import write_json_atomic
from axq.quant.development.config import SuiteConfig, load_experiment_config
from axq.quant.development.runner import run_experiment
from axq.quant.development.state import RunStateStore
from axq.versioning import canonical_hash


def _execute(path: Path) -> Any:
    return run_experiment(load_experiment_config(path))


def run_suite(
    config: SuiteConfig,
    *,
    executor: Callable[[Path], Any] = _execute,
) -> dict[str, Any]:
    config_hash = canonical_hash(config.model_dump(mode="json"))
    suite_id = f"qsuite-{config.name}-{config_hash[:16]}"
    root = config.output_root / suite_id
    summary_path = root / "suite_summary.json"
    prior: dict[str, Any] = {}
    if config.resume and summary_path.is_file():
        loaded = json.loads(summary_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            prior = {
                str(item.get("config")): item
                for item in loaded.get("runs", [])
                if isinstance(item, dict)
            }
    state = RunStateStore(root / "status.json")
    state.start(suite_id, config_hash=config_hash)
    rows: list[dict[str, Any]] = []
    for path in config.experiments:
        key = str(path)
        previous = prior.get(key)
        if previous and previous.get("status") in {"COMPLETE", "SKIPPED_COMPLETE"}:
            rows.append(previous | {"status": "SKIPPED_COMPLETE"})
            continue
        try:
            result = executor(path)
            rows.append(
                {
                    "config": key,
                    "status": "COMPLETE",
                    "run_id": str(result.run_id),
                    "run_dir": str(result.run_dir),
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "config": key,
                    "status": "FAILED",
                    "failure": f"{type(exc).__name__}: {exc}",
                }
            )
            if not config.continue_on_failure:
                break
    summary = {
        "schema_version": "1.0",
        "suite_id": suite_id,
        "status": "COMPLETE_WITH_FAILURES"
        if any(row["status"] == "FAILED" for row in rows)
        else "COMPLETE",
        "runs": rows,
        "resume": config.resume,
    }
    write_json_atomic(summary_path, summary)
    state.complete(
        suite_id,
        config_hash=config_hash,
        artifacts={"suite_summary": "suite_summary.json"},
    )
    return summary
