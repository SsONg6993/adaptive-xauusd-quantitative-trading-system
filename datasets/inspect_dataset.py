from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a Phase 3 dataset manifest and artifact")
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.dataset_manifest.read_text(encoding="utf-8"))
    directory = args.dataset_manifest.parent
    parquet = directory / "dataset.parquet"
    csv_debug = directory / "dataset.csv.gz"
    if parquet.exists():
        frame = pd.read_parquet(parquet)
        artifact = parquet
    elif csv_debug.exists():
        frame = pd.read_csv(csv_debug)
        artifact = csv_debug
    else:
        raise FileNotFoundError("Dataset artifact is missing")
    if len(frame) != payload["row_count"]:
        raise ValueError("Dataset row count does not match manifest")
    expected = {
        "candle_open_timestamp",
        "decision_timestamp",
        *payload["feature_columns"],
        *payload["target_columns"],
        *payload["label_metadata_columns"],
    }
    if set(frame.columns) != expected:
        raise ValueError("Dataset columns do not match manifest allowlists")
    print(f"dataset_id={payload['dataset_id']}")
    print(f"artifact={artifact} rows={len(frame)} columns={len(frame.columns)}")
    print(f"feature_manifest_id={payload['feature_manifest_id']}")
    print(f"label_manifest_id={payload['label_manifest_id']}")
    print(f"split_manifest_id={payload['split_manifest_id']}")


if __name__ == "__main__":
    main()
