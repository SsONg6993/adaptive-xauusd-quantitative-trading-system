"""Read-only source check for the optional operator dashboard."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from axq.dashboard.readers import (
    load_performance_snapshot,
    load_reasoning_snapshot,
    load_runtime_snapshot,
    read_ollama_status,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check")
    check.add_argument("--reasoning-db", type=Path)
    check.add_argument("--runtime-db", type=Path)
    check.add_argument("--metrics-json", type=Path)
    check.add_argument("--ollama-endpoint")
    check.add_argument("--ollama-model")
    check.add_argument("--attempt-limit", type=int, default=10)
    return parser


def _status(component: object) -> dict[str, object]:
    value = component.model_dump(mode="json")  # type: ignore[attr-defined]
    return {
        "as_of": value["as_of"],
        "detail": value["detail"],
        "source_path": value["source_path"],
        "state": value["state"],
    }


def _check(args: argparse.Namespace) -> int:
    reasoning = load_reasoning_snapshot(args.reasoning_db, limit=args.attempt_limit)
    runtime = load_runtime_snapshot(args.runtime_db)
    performance = load_performance_snapshot(args.metrics_json)
    ollama = read_ollama_status(
        args.ollama_endpoint,
        model_name=args.ollama_model,
    )
    payload = {
        "ollama": _status(ollama) | {"metadata": ollama.metadata},
        "performance": _status(performance.component)
        | {
            "completed_trades": performance.completed_trades,
            "range_end": performance.range_end,
            "range_start": performance.range_start,
            "rows": performance.rows,
        },
        "reasoning": _status(reasoning.component) | {"attempt_count": len(reasoning.attempts)},
        "runtime": _status(runtime.component)
        | {
            "open_positions": (
                None if runtime.state is None else len(runtime.state.positions.positions)
            ),
        },
    }
    print(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "check":
        return _check(args)
    raise SystemExit("unknown dashboard command")


__all__ = ["main"]
