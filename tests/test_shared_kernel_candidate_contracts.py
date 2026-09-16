from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from axq.master import default_fusion_policy
from axq.reflection.evaluation_contracts import MetricScope, SemanticArtifactRef
from axq.reflection.proposal_contracts import ProposalTargetComponent
from axq.reflection.shared_kernel_candidate_contracts import (
    FrozenSharedKernelCandidateConfig,
    SharedKernelCandidateAudit,
    SharedKernelCandidateRequest,
    SharedKernelCSVFileRef,
    SharedKernelDataManifestRef,
    SharedKernelMetricArtifactRef,
    SharedKernelReplayDataManifest,
    SharedKernelReplayResultRef,
)
from axq.replay_validation import default_shared_kernel_policy_set

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=UTC)
NAMES = ("xauusd_h1.csv", "xauusd_h4.csv", "xauusd_m15.csv", "xauusd_m5.csv")


def _files() -> tuple[SharedKernelCSVFileRef, ...]:
    return tuple(
        SharedKernelCSVFileRef(file_name=name, sha256=f"{index + 1:064x}", byte_size=100)
        for index, name in enumerate(NAMES)
    )


def _manifest(scope: MetricScope = MetricScope.VALIDATION) -> SharedKernelReplayDataManifest:
    return SharedKernelReplayDataManifest(
        proposal_id="proposal-1",
        candidate_id="candidate-1",
        plan_id="plan-1",
        scope=scope,
        period_start=NOW - timedelta(days=1),
        period_end=NOW,
        available_at=NOW,
        m5_row_count=100,
        files=tuple(reversed(_files())),
    )


def _config() -> FrozenSharedKernelCandidateConfig:
    return FrozenSharedKernelCandidateConfig(
        proposal_id="proposal-1",
        proposal_key="proposal-key-1",
        base_policy_set_id=default_shared_kernel_policy_set().policy_set_id,
        source_identity="git:test-shared-kernel",
        fusion_policy=default_fusion_policy(),
    )


def test_frozen_config_and_manifest_are_normalized_and_content_addressed() -> None:
    config = _config()
    manifest = _manifest()

    assert config.target_component is ProposalTargetComponent.MASTER_FUSION
    assert config.config_id.startswith("frozen-shared-kernel-config-")
    assert tuple(item.file_name for item in manifest.files) == NAMES
    assert manifest.manifest_id.startswith("shared-kernel-data-manifest-")


def test_manifest_requires_exact_csv_bundle_and_rejects_final_oos() -> None:
    with pytest.raises(ValidationError, match="exactly"):
        SharedKernelReplayDataManifest(
            **_manifest().model_dump(exclude={"manifest_id", "files"}),
            files=(_files()[0], _files()[0], _files()[1], _files()[2]),
        )
    with pytest.raises(ValidationError, match="Final OOS"):
        _manifest(MetricScope.FINAL_OOS)
    with pytest.raises(ValidationError, match="Final OOS"):
        SharedKernelDataManifestRef(
            scope=MetricScope.FINAL_OOS,
            semantic_id="forbidden",
            sha256="f" * 64,
        )


def test_request_identity_excludes_operational_timestamp() -> None:
    config = _config()
    manifest = _manifest()
    values = dict(
        proposal_id="proposal-1",
        candidate_id="candidate-1",
        plan_id="plan-1",
        config_ref=SemanticArtifactRef(semantic_id=config.config_id, sha256="a" * 64),
        data_manifest_refs=(
            SharedKernelDataManifestRef(
                scope=manifest.scope,
                semantic_id=manifest.manifest_id,
                sha256="b" * 64,
            ),
        ),
        evaluation_run_key="shared-kernel-controlled-v1",
        deterministic_seed=1729,
        environment_identity="python-3.12-lock-controlled",
    )
    first = SharedKernelCandidateRequest(**values, requested_at=NOW)
    later = SharedKernelCandidateRequest(**values, requested_at=NOW + timedelta(days=1))

    assert first.request_id == later.request_id


def test_all_operational_timestamps_reject_naive_values() -> None:
    data = _manifest().model_dump(exclude={"manifest_id", "available_at"})
    with pytest.raises(ValidationError, match="timezone-aware"):
        SharedKernelReplayDataManifest(**data, available_at=NOW.replace(tzinfo=None))


def test_audit_identity_excludes_operational_timestamps() -> None:
    request = SharedKernelCandidateRequest(
        proposal_id="proposal-1",
        candidate_id="candidate-1",
        plan_id="plan-1",
        config_ref=SemanticArtifactRef(semantic_id="config-1", sha256="a" * 64),
        data_manifest_refs=(
            SharedKernelDataManifestRef(
                scope=MetricScope.VALIDATION,
                semantic_id="manifest-1",
                sha256="b" * 64,
            ),
        ),
        evaluation_run_key="run-1",
        deterministic_seed=1729,
        environment_identity="environment-1",
        requested_at=NOW,
    )
    values = dict(
        request_id=request.request_id,
        proposal_id=request.proposal_id,
        candidate_id=request.candidate_id,
        plan_id=request.plan_id,
        config_ref=request.config_ref,
        data_manifest_refs=request.data_manifest_refs,
        replay_result_refs=(
            SharedKernelReplayResultRef(
                scope=MetricScope.VALIDATION,
                semantic_id="replay-1",
                sha256="c" * 64,
            ),
        ),
        output_artifact_refs=(
            SharedKernelMetricArtifactRef(
                scope=MetricScope.VALIDATION,
                semantic_id="samples-1",
                sha256="d" * 64,
            ),
        ),
        evaluation_run_key=request.evaluation_run_key,
        deterministic_seed=request.deterministic_seed,
        environment_identity=request.environment_identity,
    )
    first = SharedKernelCandidateAudit(**values, started_at=NOW, completed_at=NOW)
    later = SharedKernelCandidateAudit(
        **values,
        started_at=NOW + timedelta(days=1),
        completed_at=NOW + timedelta(days=1, minutes=1),
    )

    assert first.audit_id == later.audit_id
