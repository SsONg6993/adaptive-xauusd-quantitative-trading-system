"""Command-line entry point for Phase 7 system replay and result display."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from axq.replay_validation.system import compare_replays, run_system_replay


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--data-dir", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--months", type=int, default=1, choices=(1, 3))
    show = subparsers.add_parser("show")
    show.add_argument("metrics", type=Path)
    compare = subparsers.add_parser("compare")
    compare.add_argument("first", type=Path)
    compare.add_argument("second", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        path = run_system_replay(args.data_dir, args.output_dir, months=args.months)
        print(path)
    elif args.command == "show":
        report = json.loads(args.metrics.read_text(encoding="utf-8"))
        report.pop("semantic_ids", None)
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(compare_replays(args.first, args.second), indent=2))


if __name__ == "__main__":
    main()
