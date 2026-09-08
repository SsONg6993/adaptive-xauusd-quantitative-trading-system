"""Compare completed Phase 5 runs without retraining."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from axq.quant.development.comparison import compare_runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = compare_runs(args.runs)
    serialized = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
