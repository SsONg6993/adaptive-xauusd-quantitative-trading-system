"""Run or dry-run a resumable Quant experiment suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from axq.quant.development.config import load_experiment_config, load_suite_config
from axq.quant.development.runner import plan_experiment, run_experiment
from axq.quant.development.suite import run_suite


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    suite = load_suite_config(args.suite)

    def configured(path: Path) -> Any:
        config = load_experiment_config(path)
        config = config.model_copy(
            update={
                "training": config.training.model_copy(
                    update={"dataset_dir": args.dataset.resolve()}
                )
            }
        )
        return plan_experiment(config) if args.dry_run else run_experiment(config)

    if args.dry_run:
        plans = [configured(path) for path in suite.experiments]
        print(json.dumps({"status": "DRY_RUN", "plans": plans}, indent=2, default=str))
        return
    print(json.dumps(run_suite(suite, executor=configured), indent=2, default=str))


if __name__ == "__main__":
    main()
