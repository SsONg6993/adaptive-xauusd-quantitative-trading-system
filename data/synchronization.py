from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from axq.data.synchronization import synchronize_completed_bars


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m5", type=Path, required=True)
    parser.add_argument("--m15", type=Path)
    parser.add_argument("--h1", type=Path)
    parser.add_argument("--h4", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frames = {
        key.upper(): pd.read_csv(path)
        for key, path in vars(args).items()
        if key in {"m5", "m15", "h1", "h4"} and path
    }
    synchronized = synchronize_completed_bars(frames)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    synchronized.to_csv(args.output, index=False)
    print(f"wrote {len(synchronized)} synchronized rows to {args.output}")


if __name__ == "__main__":
    main()
