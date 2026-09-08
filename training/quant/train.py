"""Train one manifest-bound Quant Agent model from a Phase 3 dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from axq.quant.config import Device, load_quant_config
from axq.quant.trainer import train_quant_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--device", choices=[item.value for item in Device])
    args = parser.parse_args()
    config = load_quant_config(args.config)
    updates: dict[str, object] = {}
    if args.dataset:
        updates["dataset_dir"] = args.dataset
    if args.output_root:
        updates["output_root"] = args.output_root
    if args.device:
        updates["device"] = Device(args.device)
    if updates:
        config = config.model_copy(update=updates)
    result = train_quant_model(config)
    print(
        json.dumps(
            {
                "run_id": result.manifest.model_id,
                "run_dir": str(result.run_dir),
                "device": result.manifest.device,
                "oos_metrics": result.metrics["oos"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
