from __future__ import annotations

from pathlib import Path

import pytest
from shared_kernel_candidate_test_support import (
    data_manifest,
    persisted_shared_kernel_plan,
    shared_kernel_request,
    write_synthetic_csv_bundle,
)

from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.shared_kernel_candidate_engine import SharedKernelMasterFusionEngineV1


def _inputs(tmp_path: Path):
    store_path = tmp_path / "governance.sqlite3"
    proposal, candidate, plan, config = persisted_shared_kernel_plan(store_path)
    data_dir = tmp_path / "validation-data"
    write_synthetic_csv_bundle(data_dir)
    manifest = data_manifest(
        data_dir,
        proposal.proposal_id,
        candidate.candidate_id,
        plan.plan_id,
        MetricScope.VALIDATION,
    )
    request = shared_kernel_request(
        proposal.proposal_id,
        candidate.candidate_id,
        plan.plan_id,
        config,
        (manifest,),
    )
    return proposal, candidate, plan, config, data_dir, manifest, request


def test_engine_runs_existing_shared_kernel_and_emits_only_plan_metrics(tmp_path) -> None:
    proposal, candidate, plan, config, data_dir, manifest, request = _inputs(tmp_path)

    output = SharedKernelMasterFusionEngineV1().execute(
        request,
        proposal,
        candidate,
        plan,
        config,
        (manifest,),
        {MetricScope.VALIDATION: data_dir},
        tmp_path / "runs",
    )

    assert len(output.artifacts) == 1
    assert output.artifacts[0].scope is MetricScope.VALIDATION
    assert tuple(item.metric_key for item in output.artifacts[0].series) == (
        "validation_master_actionable_rate",
    )
    assert len(output.replay_result_refs) == 1
    assert (tmp_path / "runs" / "validation" / "metrics.json").exists()


def test_engine_rejects_changed_csv_bytes_before_replay(tmp_path) -> None:
    proposal, candidate, plan, config, data_dir, manifest, request = _inputs(tmp_path)
    with (data_dir / "xauusd_m5.csv").open("a", encoding="utf-8") as handle:
        handle.write("\n")

    with pytest.raises(ValueError, match="digest"):
        SharedKernelMasterFusionEngineV1().execute(
            request,
            proposal,
            candidate,
            plan,
            config,
            (manifest,),
            {MetricScope.VALIDATION: data_dir},
            tmp_path / "runs",
        )

def test_engine_rejects_unallowlisted_metric_key(tmp_path) -> None:
    proposal, candidate, plan, config, data_dir, manifest, request = _inputs(tmp_path)
    invalid_plan = plan.model_copy(
        update={
            "metrics": tuple(
                item.model_copy(update={"metric_key": "validation_unknown"})
                if item.scope is MetricScope.VALIDATION
                else item
                for item in plan.metrics
            )
        }
    )

    with pytest.raises(ValueError, match="allowlisted"):
        SharedKernelMasterFusionEngineV1().execute(
            request,
            proposal,
            candidate,
            invalid_plan,
            config,
            (manifest,),
            {MetricScope.VALIDATION: data_dir},
            tmp_path / "runs",
        )
