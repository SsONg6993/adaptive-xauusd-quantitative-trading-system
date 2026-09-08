"""Validate and write an Optuna study plan; never starts a study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from axq.quant.development.artifacts import write_json_atomic
from axq.quant.development.config import load_tuning_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    config = load_tuning_config(args.config)
    plan = config.model_dump(mode="json") | {
        "status": "PREPARED_NOT_STARTED",
        "final_oos_allowed_as_objective": False,
        "requires_explicit_future_execution_command": True,
    }
    write_json_atomic(args.output, plan)
    print(json.dumps(plan, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
