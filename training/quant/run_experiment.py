"""Run or dry-run one content-addressed Quant development experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from axq.quant.config import Device
from axq.quant.development.config import load_experiment_config
from axq.quant.development.runner import plan_experiment, run_experiment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--development-output", type=Path)
    parser.add_argument("--model-output", type=Path)
    parser.add_argument("--device", choices=[item.value for item in Device])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = load_experiment_config(args.config)
    training_updates: dict[str, object] = {}
    if args.dataset:
        training_updates["dataset_dir"] = args.dataset.resolve()
    if args.model_output:
        training_updates["output_root"] = args.model_output.resolve()
    if args.device:
        training_updates["device"] = Device(args.device)
    updates: dict[str, object] = {}
    if training_updates:
        updates["training"] = config.training.model_copy(update=training_updates)
    if args.development_output:
        updates["output_root"] = args.development_output.resolve()
    if updates:
        config = config.model_copy(update=updates)
    if args.dry_run:
        print(json.dumps(plan_experiment(config), indent=2, sort_keys=True, default=str))
        return
    result = run_experiment(config)
    print(json.dumps(result.manifest, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
