from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from axq.quant.development.config import (
    load_experiment_config,
    load_suite_config,
    load_tuning_config,
)

ROOT = Path(__file__).parents[1]


def test_all_experiment_and_tuning_configs_are_strictly_loadable() -> None:
    experiments = sorted((ROOT / "configs/quant/experiments").glob("*.yaml"))
    tuning = sorted((ROOT / "configs/quant/tuning").glob("*.yaml"))

    assert len(experiments) == 8
    assert len(tuning) == 3
    for path in experiments:
        load_experiment_config(path)
    for path in tuning:
        load_tuning_config(path)
    suite = load_suite_config(ROOT / "configs/quant/suites/baseline_suite.yaml")
    assert len(suite.experiments) == 6


def test_phase5_clis_have_non_training_help_paths() -> None:
    scripts = [
        "data/inspect_mt5_history.py",
        "data/build_mt5_dataset.py",
        "scripts/check_compute.py",
        "training/quant/run_experiment.py",
        "training/quant/run_suite.py",
        "training/quant/run_walk_forward.py",
        "training/quant/run_ablation.py",
        "training/quant/compare_runs.py",
        "training/quant/prepare_optuna.py",
        "training/quant/run_optuna.py",
    ]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    for relative in scripts:
        result = subprocess.run(
            [sys.executable, str(ROOT / relative), "--help"],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{relative}: {result.stderr}"
        assert "usage:" in result.stdout.lower()
