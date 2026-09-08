from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from axq.quant.config import Architecture
from axq.quant.development.config import (
    ExperimentConfig,
    TuningConfig,
    development_run_id,
    load_experiment_config,
)
from axq.quant.development.state import RunStateStore
from axq.quant.development.tuning import tuning_plan


def experiment_payload(dataset_dir: Path) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "name": "logistic-baseline",
        "training": {
            "architecture": "logistic_regression",
            "dataset_dir": str(dataset_dir),
            "random_seed": 17,
        },
        "evaluation": {"hold_thresholds": [0.4, 0.5, 0.6]},
    }


def test_experiment_config_is_strict_and_content_addressed(tmp_path: Path) -> None:
    payload = experiment_payload(tmp_path / "dataset")
    config = ExperimentConfig.model_validate(payload)

    first = development_run_id(config, dataset_id="ds-abc", git_identity="abc123")
    second = development_run_id(config, dataset_id="ds-abc", git_identity="abc123")

    assert first == second
    assert first.startswith("qdev-logistic-baseline-")
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(payload | {"unexpected": True})


def test_loader_resolves_paths_relative_to_config(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    path = config_dir / "experiment.yaml"
    path.write_text(
        """schema_version: '1.0'
name: logistic
training:
  architecture: logistic_regression
  dataset_dir: ../datasets/example
  output_root: ../runtime/models/quant
evaluation:
  hold_thresholds: [0.5]
""",
        encoding="utf-8",
    )

    loaded = load_experiment_config(path)

    assert loaded.training.dataset_dir == (tmp_path / "datasets/example").resolve()
    assert loaded.training.output_root == (tmp_path / "runtime/models/quant").resolve()


@pytest.mark.parametrize("scope", ["oos", "final_oos", "test"])
def test_tuning_config_rejects_any_oos_objective(scope: str) -> None:
    with pytest.raises(ValidationError):
        TuningConfig(
            architecture=Architecture.XGBOOST,
            objective_scope=scope,  # type: ignore[arg-type]
            metric="log_loss",
        )


def test_run_state_recovers_interrupted_run_and_preserves_identity(tmp_path: Path) -> None:
    store = RunStateStore(tmp_path / "status.json")
    store.start("run-1", config_hash="cfg-1")
    initial = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert initial["status"] == "RUNNING"

    recovered = RunStateStore(tmp_path / "status.json")
    assert recovered.is_interrupted("run-1", config_hash="cfg-1")
    recovered.complete("run-1", config_hash="cfg-1", artifacts={"metrics": "metrics.json"})

    assert recovered.load()["status"] == "COMPLETE"
    assert not list(tmp_path.glob("*.tmp"))
    with pytest.raises(ValueError, match="identity"):
        recovered.start("run-1", config_hash="different")


def test_tuning_plan_names_only_development_scopes() -> None:
    config = TuningConfig(
        architecture=Architecture.RANDOM_FOREST,
        objective_scope="walk_forward_validation",
        metric="log_loss",
    )

    plan = tuning_plan(config, dataset_id="ds-1", development_split_id="sm-dev")

    assert plan["objective_scope"] == "walk_forward_validation"
    assert plan["immutable_final_oos_access"] is False
    assert "oos" not in plan["allowed_selection_scopes"]
