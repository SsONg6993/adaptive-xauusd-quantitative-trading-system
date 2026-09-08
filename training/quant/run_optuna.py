"""Explicit user-run Optuna study over development folds only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from axq.quant.dataset import load_training_dataset
from axq.quant.development.config import (
    load_experiment_config,
    load_tuning_config,
    load_walk_forward_config,
)
from axq.quant.development.folds import development_split_manifest
from axq.quant.development.tuning import run_optuna_study, tuning_plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuning", required=True, type=Path)
    parser.add_argument("--experiment", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    tuning = load_tuning_config(args.tuning)
    experiment = load_experiment_config(args.experiment)
    experiment = experiment.model_copy(
        update={
            "training": experiment.training.model_copy(
                update={"dataset_dir": args.dataset.resolve()}
            )
        }
    )
    dataset = load_training_dataset(args.dataset)
    policy = load_walk_forward_config(args.policy)
    splits = development_split_manifest(
        row_count=len(dataset.frame),
        final_oos_start=dataset.split_manifest.folds[0].oos.start,
        label_horizon_bars=dataset.split_manifest.label_horizon_bars,
        policy=policy,
    )
    if not args.execute:
        print(
            json.dumps(
                tuning_plan(
                    tuning,
                    dataset_id=dataset.manifest.dataset_id,
                    development_split_id=splits.manifest_id,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return
    print(
        json.dumps(
            run_optuna_study(
                tuning, experiment, dataset, splits, output_dir=args.output
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
