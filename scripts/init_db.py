from __future__ import annotations

import argparse
from pathlib import Path

from axq.database import Database


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("runtime/axq.sqlite3"))
    args = parser.parse_args()
    Database(args.path).migrate(Path("database/migrations"))
    print(f"database initialized at {args.path}")


if __name__ == "__main__":
    main()
