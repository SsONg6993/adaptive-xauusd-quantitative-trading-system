"""Evaluate a frozen Quant Agent artifact without retraining."""

from __future__ import annotations

import argparse
import json

from axq.quant.evaluation import evaluate_saved_run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--split", choices=["train", "validation", "oos"], default="oos")
    args = parser.parse_args()
    print(
        json.dumps(
            evaluate_saved_run(args.run, args.dataset, split=args.split),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
