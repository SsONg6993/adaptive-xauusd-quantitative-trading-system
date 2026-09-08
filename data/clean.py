from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from axq.data.cleaning import clean_candles


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cleaned = clean_candles(pd.read_csv(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.output, index=False)
    print(f"wrote {len(cleaned)} cleaned rows to {args.output}")


if __name__ == "__main__":
    main()
