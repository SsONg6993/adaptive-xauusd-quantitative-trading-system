from __future__ import annotations

import hashlib
from datetime import timedelta
from pathlib import Path

import pandas as pd
from evaluation_execution_test_support import NOW, persist_controlled_plan

from axq.master import FusionPolicy, default_fusion_policy
from axq.reflection.evaluation_contracts import (
    AcceptanceCriterion,
    CandidateKind,
    CriterionComparator,
    CriterionRole,
    EvaluationCandidateSpec,
    MetricDirection,
    MetricScope,
    SemanticArtifactRef,
    ValidationMetricSpec,
)
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.evaluations import build_evaluation_plan
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.shared_kernel_candidate_contracts import (
    FrozenSharedKernelCandidateConfig,
    SharedKernelCandidateRequest,
    SharedKernelCSVFileRef,
    SharedKernelDataManifestRef,
    SharedKernelReplayDataManifest,
)
from axq.replay_validation import default_shared_kernel_policy_set


def _ohlc_rows(periods: int, minutes: int, *, shift: float) -> pd.DataFrame:
    end = NOW - timedelta(minutes=minutes)
    timestamps = pd.date_range(end=end, periods=periods, freq=f"{minutes}min", tz="UTC")
    closes = [2500.0 + shift + index * 0.12 + ((index % 7) - 3) * 0.08 for index in range(periods)]
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": [value - 0.05 for value in closes],
            "high": [value + 0.8 for value in closes],
            "low": [value - 0.8 for value in closes],
            "close": closes,
            "tick_volume": [100 + index for index in range(periods)],
            "spread": [20.0] * periods,
        }
    )


def write_synthetic_csv_bundle(path: Path, *, shift: float = 0.0) -> None:
    path.mkdir(parents=True, exist_ok=True)
    frames = {
        "m5": _ohlc_rows(140, 5, shift=shift),
        "m15": _ohlc_rows(80, 15, shift=shift),
        "h1": _ohlc_rows(80, 60, shift=shift),
        "h4": _ohlc_rows(80, 240, shift=shift),
    }
    for name, frame in frames.items():
        frame.to_csv(path / f"xauusd_{name}.csv", index=False, lineterminator="\n")


def data_manifest(
    path: Path,
    proposal_id: str,
    candidate_id: str,
    plan_id: str,
    scope: MetricScope,
) -> SharedKernelReplayDataManifest:
    m5 = pd.read_csv(path / "xauusd_m5.csv")
    files = []
    for name in ("xauusd_m5.csv", "xauusd_m15.csv", "xauusd_h1.csv", "xauusd_h4.csv"):
        payload = (path / name).read_bytes()
        files.append(
            SharedKernelCSVFileRef(
                file_name=name,
                sha256=hashlib.sha256(payload).hexdigest(),
                byte_size=len(payload),
            )
        )
    start = pd.Timestamp(m5.iloc[0]["timestamp"]).to_pydatetime()
    end = pd.Timestamp(m5.iloc[-1]["timestamp"]).to_pydatetime() + timedelta(minutes=5)
    return SharedKernelReplayDataManifest(
        proposal_id=proposal_id,
        candidate_id=candidate_id,
        plan_id=plan_id,
        scope=scope,
        period_start=start,
        period_end=end,
        available_at=end,
        m5_row_count=len(m5),
        files=tuple(files),
    )


def persisted_shared_kernel_plan(path: Path, *, include_development: bool = False):
    proposal, _, _ = persist_controlled_plan(path)
    baseline = default_shared_kernel_policy_set()
    default_fusion = default_fusion_policy()
    replacement = FusionPolicy.model_validate(
        default_fusion.model_dump(exclude={"policy_id"})
        | {"minimum_actionable_confidence": default_fusion.minimum_actionable_confidence + 0.01}
    )
    config = FrozenSharedKernelCandidateConfig(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        base_policy_set_id=baseline.policy_set_id,
        source_identity="git:shared-kernel-controlled-v1",
        fusion_policy=replacement,
    )
    config_payload = canonical_record_bytes(config)
    candidate = EvaluationCandidateSpec(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        target_component=proposal.target_component,
        candidate_kind=CandidateKind.CONFIGURATION,
        description="Frozen Master-fusion configuration fixture.",
        implementation_version="SHARED_KERNEL_MASTER_FUSION_V1",
        source_identity=config.source_identity,
        config_identity=config.config_id,
        manifest_identity="controlled-synthetic-csv-v1",
        artifact_refs=(
            SemanticArtifactRef(
                semantic_id=config.config_id,
                sha256=hashlib.sha256(config_payload).hexdigest(),
            ),
        ),
        defined_at=NOW,
    )
    scopes = (
        (MetricScope.DEVELOPMENT, MetricScope.VALIDATION)
        if include_development
        else (MetricScope.VALIDATION,)
    )
    metrics = tuple(
        ValidationMetricSpec(
            metric_key=f"{scope.value.lower()}_master_actionable_rate",
            name=f"{scope.value.title()} Master actionable rate",
            unit="ratio",
            aggregation="MEAN",
            scope=scope,
            direction=MetricDirection.DESCRIPTIVE,
        )
        for scope in scopes
    ) + (
        ValidationMetricSpec(
            metric_key="final_oos_master_actionable_rate",
            name="Final OOS Master actionable rate",
            unit="ratio",
            aggregation="MEAN",
            scope=MetricScope.FINAL_OOS,
            direction=MetricDirection.DESCRIPTIVE,
        ),
    )
    validation_key = "validation_master_actionable_rate"
    criteria = (
        AcceptanceCriterion(
            metric_key=validation_key,
            comparator=CriterionComparator.GE,
            lower_threshold=0.0,
            minimum_samples=1,
            role=CriterionRole.DECISION,
        ),
        AcceptanceCriterion(
            metric_key="final_oos_master_actionable_rate",
            comparator=CriterionComparator.GE,
            lower_threshold=0.0,
            minimum_samples=1,
            role=CriterionRole.REPORTING_ONLY,
        ),
    )
    store = SQLiteProposalEvaluationStore(path)
    store.append_candidate(candidate)
    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=candidate,
        metrics=metrics,
        criteria=criteria,
        deterministic_seed=1729,
        environment_identity="python-3.12-lock-controlled",
        defined_at=NOW,
        actor_id="operator",
        action_id="shared-kernel-controlled-plan",
    )
    store.append_plan(plan)
    return proposal, candidate, plan, config


def manifest_ref(manifest: SharedKernelReplayDataManifest) -> SharedKernelDataManifestRef:
    payload = canonical_record_bytes(manifest)
    return SharedKernelDataManifestRef(
        scope=manifest.scope,
        semantic_id=manifest.manifest_id,
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def shared_kernel_request(
    proposal_id: str,
    candidate_id: str,
    plan_id: str,
    config: FrozenSharedKernelCandidateConfig,
    manifests: tuple[SharedKernelReplayDataManifest, ...],
) -> SharedKernelCandidateRequest:
    config_payload = canonical_record_bytes(config)
    return SharedKernelCandidateRequest(
        proposal_id=proposal_id,
        candidate_id=candidate_id,
        plan_id=plan_id,
        config_ref=SemanticArtifactRef(
            semantic_id=config.config_id,
            sha256=hashlib.sha256(config_payload).hexdigest(),
        ),
        data_manifest_refs=tuple(manifest_ref(item) for item in manifests),
        evaluation_run_key="shared-kernel-controlled-run",
        deterministic_seed=1729,
        environment_identity="python-3.12-lock-controlled",
        requested_at=NOW + timedelta(minutes=10),
    )


def persisted_shared_kernel_inputs(path: Path, *, include_development: bool = False):
    store_path = path / "governance.sqlite3"
    proposal, candidate, plan, config = persisted_shared_kernel_plan(
        store_path, include_development=include_development
    )
    scopes = (
        (MetricScope.DEVELOPMENT, MetricScope.VALIDATION)
        if include_development
        else (MetricScope.VALIDATION,)
    )
    directories: dict[MetricScope, Path] = {}
    manifests = []
    for index, scope in enumerate(scopes):
        data_dir = path / f"{scope.value.lower()}-data"
        write_synthetic_csv_bundle(data_dir, shift=float(index))
        directories[scope] = data_dir
        manifests.append(
            data_manifest(
                data_dir,
                proposal.proposal_id,
                candidate.candidate_id,
                plan.plan_id,
                scope,
            )
        )
    manifest_tuple = tuple(manifests)
    request = shared_kernel_request(
        proposal.proposal_id,
        candidate.candidate_id,
        plan.plan_id,
        config,
        manifest_tuple,
    )
    return (
        store_path,
        proposal,
        candidate,
        plan,
        config,
        manifest_tuple,
        directories,
        request,
    )
