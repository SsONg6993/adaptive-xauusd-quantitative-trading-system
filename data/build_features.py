from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from axq.config import load_config
from axq.features import default_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/base.yaml"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--quality-report", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    source = pd.read_csv(args.input)
    registry = default_registry()
    result = registry.compute(
        source,
        enabled_groups=config.features.groups,
        parameters=config.features.parameters,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    manifest_path = args.manifest or args.output.with_suffix(".features.json")
    manifest = registry.manifest(
        feature_set_version=config.features.version,
        enabled_groups=config.features.groups,
        parameters=config.features.parameters,
        available_source_columns=source.columns,
    )
    manifest.write(manifest_path)
    if args.quality_report:
        from axq.features.analysis import quality_report

        args.quality_report.parent.mkdir(parents=True, exist_ok=True)
        args.quality_report.write_text(
            json.dumps(quality_report(result), indent=2, default=str), encoding="utf-8"
        )
    print(f"wrote {len(result)} rows with {len(result.columns)} columns to {args.output}")
    print(f"wrote feature manifest {manifest.manifest_id} to {manifest_path}")


if __name__ == "__main__":
    main()
