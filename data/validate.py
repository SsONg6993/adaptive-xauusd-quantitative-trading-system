from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from axq.data.validation import validate_candles


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--timeframe", choices=("M5", "M15", "H1", "H4"), required=True)
    args = parser.parse_args()
    report = validate_candles(pd.read_csv(args.input), args.timeframe)
    print(json.dumps(asdict(report), indent=2))
    raise SystemExit(0 if report.valid else 1)


if __name__ == "__main__":
    main()
