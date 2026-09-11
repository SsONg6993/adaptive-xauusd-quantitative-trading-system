from __future__ import annotations

import pytest
from pydantic import ValidationError
from shared_kernel_candidate_test_support import write_synthetic_csv_bundle

from axq.master import FusionPolicy
from axq.replay_validation.policies import default_shared_kernel_policy_set
from axq.replay_validation.system import compare_replays, run_system_replay


def test_default_shared_kernel_policy_set_is_frozen_and_content_addressed() -> None:
    first = default_shared_kernel_policy_set()
    second = default_shared_kernel_policy_set()

    assert first == second
    assert first.policy_set_id == second.policy_set_id
    assert first.policy_set_id.startswith("shared-kernel-policy-set-")
    with pytest.raises(ValidationError):
        first.model_copy(update={"policy_set_id": "changed"}).__class__(
            **(first.model_dump() | {"policy_set_id": "changed"})
        )


def test_master_fusion_replacement_changes_only_the_reviewed_policy() -> None:
    baseline = default_shared_kernel_policy_set()
    replacement = FusionPolicy.model_validate(
        baseline.fusion_policy.model_dump(exclude={"policy_id"})
        | {
            "minimum_actionable_confidence": (
                baseline.fusion_policy.minimum_actionable_confidence + 0.01
            )
        }
    )

    candidate = baseline.with_master_fusion(replacement)

    assert candidate.policy_set_id != baseline.policy_set_id
    assert candidate.fusion_policy == replacement
    assert candidate.discipline_policy == baseline.discipline_policy
    assert candidate.risk_policy == baseline.risk_policy
    assert candidate.execution_policy == baseline.execution_policy
    assert candidate.position_management_policy == baseline.position_management_policy
    assert candidate.position_action_policy == baseline.position_action_policy
    assert candidate.scenario_policy == baseline.scenario_policy


def test_explicit_default_policy_set_preserves_replay_bytes(tmp_path) -> None:
    data_dir = tmp_path / "data"
    write_synthetic_csv_bundle(data_dir)
    implicit = run_system_replay(data_dir, tmp_path / "implicit")
    explicit = run_system_replay(
        data_dir,
        tmp_path / "explicit",
        policy_set=default_shared_kernel_policy_set(),
    )

    comparison = compare_replays(implicit, explicit)
    assert comparison["byte_identical"] is True
    assert comparison["semantic_ids_identical"] is True
    assert comparison["first_sha256"] == comparison["second_sha256"]
