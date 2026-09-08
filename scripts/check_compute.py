"""Report local compute and optional ML library capabilities."""

from __future__ import annotations

import argparse
import json

from axq.quant.development.compute import compute_report


def main() -> None:
    argparse.ArgumentParser(
        description="Report CPU, NVIDIA, CUDA, XGBoost, and LightGBM capability"
    ).parse_args()
    print(json.dumps(compute_report(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
