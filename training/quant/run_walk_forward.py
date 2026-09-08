"""Run a resumable fold-local walk-forward evaluation before final OOS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from axq.quant.dataset import load_training_dataset
from axq.quant.development.config import (
    load_experiment_config,
    load_walk_forward_config,
)
from axq.quant.development.folds import development_split_manifest, run_walk_forward


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("runtime/experiments/quant/walk_forward")
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    experiment = load_experiment_config(args.config)
    experiment = experiment.model_copy(
        update={
            "training": experiment.training.model_copy(
                update={"dataset_dir": args.dataset.resolve()}
            )
        }
    )
    dataset = load_training_dataset(args.dataset)
    final_oos_start = dataset.split_manifest.folds[0].oos.start
    policy = load_walk_forward_config(args.policy)
    manifest = development_split_manifest(
        row_count=len(dataset.frame),
        final_oos_start=final_oos_start,
        label_horizon_bars=dataset.split_manifest.label_horizon_bars,
        policy=policy,
    )
    plan = {
        "status": "DRY_RUN",
        "dataset_id": dataset.manifest.dataset_id,
        "fold_count": len(manifest.folds),
        "split_manifest_id": manifest.manifest_id,
        "immutable_final_oos_start": final_oos_start,
        "immutable_final_oos_used_for_development": False,
        "output": str(args.output.resolve()),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return
    summary = run_walk_forward(
        dataset.frame,
        manifest,
        features=dataset.manifest.feature_columns,
        target_column=experiment.training.target_column
        or dataset.manifest.target_columns[0],
        config=experiment.training,
        dataset_id=dataset.manifest.dataset_id,
        output_dir=args.output,
        metadata_columns=dataset.manifest.label_metadata_columns,
    )
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
