from __future__ import annotations

import hashlib
from datetime import timedelta

from evaluation_execution_test_support import NOW, persist_controlled_plan

from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import CanonicalMetricSampleArtifact, MetricSampleSeries
from axq.reflection.paired_evaluation_contracts import PairedArtifactRef, PairedEvaluationRequest
from axq.reflection.shared_kernel_candidate_contracts import SharedKernelDataManifestRef
from axq.reflection.shared_kernel_candidate_store import SQLiteSharedKernelCandidateStore
from axq.replay_validation import default_shared_kernel_policy_set


def artifact(
    scope: MetricScope,
    metric_key: str,
    values: tuple[float, ...],
) -> CanonicalMetricSampleArtifact:
    return CanonicalMetricSampleArtifact(
        scope=scope,
        available_at=NOW + timedelta(minutes=5),
        series=(MetricSampleSeries(metric_key=metric_key, values=values),),
    )


def artifact_ref(
    item: CanonicalMetricSampleArtifact,
    *,
    policy_identity: str,
    marker: str,
    manifest_ref: SharedKernelDataManifestRef | None = None,
    seed: int = 1729,
    environment: str = "python-3.12-lock-controlled",
) -> PairedArtifactRef:
    manifest = manifest_ref or SharedKernelDataManifestRef(
        scope=item.scope,
        semantic_id=f"shared-manifest-{item.scope.value.lower()}",
        sha256=marker * 64,
    )
    payload = canonical_record_bytes(item)
    return PairedArtifactRef(
        scope=item.scope,
        semantic_id=item.artifact_id,
        sha256=hashlib.sha256(payload).hexdigest(),
        manifest_ref=manifest,
        policy_identity=policy_identity,
        deterministic_seed=seed,
        environment_identity=environment,
    )


def paired_fixture(path):
    proposal, candidate, plan = persist_controlled_plan(path)
    baseline_policy = default_shared_kernel_policy_set().policy_set_id
    candidate_config = candidate.config_identity
    baseline = artifact(
        MetricScope.VALIDATION,
        "validation_expectancy",
        (-0.1, 0.1),
    )
    candidate_artifact = artifact(
        MetricScope.VALIDATION,
        "validation_expectancy",
        (0.1, 0.3),
    )
    baseline_ref = artifact_ref(
        baseline,
        policy_identity=baseline_policy,
        marker="a",
    )
    candidate_ref = artifact_ref(
        candidate_artifact,
        policy_identity=candidate_config,
        marker="a",
    )
    request = PairedEvaluationRequest(
        proposal_id=proposal.proposal_id,
        candidate_id=candidate.candidate_id,
        plan_id=plan.plan_id,
        baseline_policy_set_id=baseline_policy,
        candidate_config_id=candidate_config,
        baseline_artifact_refs=(baseline_ref,),
        candidate_artifact_refs=(candidate_ref,),
        evaluation_run_key="controlled-paired-v1",
        deterministic_seed=plan.deterministic_seed,
        environment_identity=plan.environment_identity,
        requested_at=NOW + timedelta(minutes=6),
    )
    return proposal, candidate, plan, baseline, candidate_artifact, request


def persisted_paired_fixture(path):
    from shared_kernel_candidate_test_support import (
        manifest_ref,
        persisted_shared_kernel_inputs,
    )

    (
        store_path,
        proposal,
        candidate,
        plan,
        config,
        manifests,
        _,
        _,
    ) = persisted_shared_kernel_inputs(path)
    shared_store = SQLiteSharedKernelCandidateStore(store_path)
    shared_store.append_config(config)
    for manifest in manifests:
        shared_store.append_manifest(manifest)
    metric = next(item for item in plan.metrics if item.scope is MetricScope.VALIDATION)
    baseline = artifact(MetricScope.VALIDATION, metric.metric_key, (0.10, 0.20))
    candidate_artifact = artifact(MetricScope.VALIDATION, metric.metric_key, (0.20, 0.40))
    manifest_reference = manifest_ref(manifests[0])
    baseline_ref = artifact_ref(
        baseline,
        policy_identity=config.base_policy_set_id,
        marker="a",
        manifest_ref=manifest_reference,
        seed=plan.deterministic_seed,
        environment=plan.environment_identity,
    )
    candidate_ref = artifact_ref(
        candidate_artifact,
        policy_identity=config.config_id,
        marker="a",
        manifest_ref=manifest_reference,
        seed=plan.deterministic_seed,
        environment=plan.environment_identity,
    )
    request = PairedEvaluationRequest(
        proposal_id=proposal.proposal_id,
        candidate_id=candidate.candidate_id,
        plan_id=plan.plan_id,
        baseline_policy_set_id=config.base_policy_set_id,
        candidate_config_id=config.config_id,
        baseline_artifact_refs=(baseline_ref,),
        candidate_artifact_refs=(candidate_ref,),
        evaluation_run_key="controlled-shared-kernel-pair-v1",
        deterministic_seed=plan.deterministic_seed,
        environment_identity=plan.environment_identity,
        requested_at=NOW + timedelta(minutes=20),
    )
    return store_path, proposal, candidate, plan, config, baseline, candidate_artifact, request
