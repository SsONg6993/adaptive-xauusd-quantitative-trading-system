"""Plan or run fold-local feature ablations; never use immutable final OOS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from axq.quant.dataset import load_training_dataset
from axq.quant.development.ablation import feature_ablation_variants
from axq.quant.development.config import (
    load_ablation_config,
    load_experiment_config,
    load_walk_forward_config,
)
from axq.quant.development.folds import development_split_manifest, run_walk_forward


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--ablation", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("runtime/experiments/quant/ablations"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    dataset = load_training_dataset(args.dataset)
    experiment = load_experiment_config(args.config)
    policy = load_walk_forward_config(args.policy)
    ablation = load_ablation_config(args.ablation)
    variants = feature_ablation_variants(
        dataset.feature_manifest,
        dataset.manifest.feature_columns,
        groups=ablation.feature_groups,
        single_features=ablation.single_features,
    )
    manifest = development_split_manifest(
        row_count=len(dataset.frame),
        final_oos_start=dataset.split_manifest.folds[0].oos.start,
        label_horizon_bars=dataset.split_manifest.label_horizon_bars,
        policy=policy,
    )
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "DRY_RUN",
                    "variants": {name: len(values) for name, values in variants.items()},
                    "fold_count": len(manifest.folds),
                    "immutable_final_oos_used_for_development": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    summaries = {}
    for name, features in variants.items():
        summaries[name] = run_walk_forward(
            dataset.frame,
            manifest,
            features=features,
            target_column=experiment.training.target_column
            or dataset.manifest.target_columns[0],
            config=experiment.training,
            dataset_id=dataset.manifest.dataset_id,
            output_dir=args.output / name,
            metadata_columns=dataset.manifest.label_metadata_columns,
        )
    print(json.dumps(summaries, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
