"""Governed V1 driver over the existing Phase 6/7 shared replay kernel."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Protocol

import pandas as pd

from axq.reflection.evaluation_contracts import (
    CandidateKind,
    EvaluationCandidateSpec,
    MetricScope,
    ProposalEvaluationPlan,
)
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    MetricSampleSeries,
)
from axq.reflection.proposal_contracts import ImprovementProposal, ProposalTargetComponent
from axq.reflection.shared_kernel_candidate_contracts import (
    FrozenSharedKernelCandidateConfig,
    SharedKernelCandidateEngineKind,
    SharedKernelCandidateRequest,
    SharedKernelReplayDataManifest,
    SharedKernelReplayResultRef,
)
from axq.replay_validation import default_shared_kernel_policy_set, run_system_replay

_METRIC_SUFFIXES = frozenset(
    {
        "master_actionable_rate",
        "discipline_pass_rate",
        "risk_pass_rate",
        "execution_intent_count",
        "completed_trade_count",
        "realized_pnl_usd",
        "max_drawdown_usd",
    }
)


@dataclass(frozen=True)
class SharedKernelCandidateEngineOutput:
    artifacts: tuple[CanonicalMetricSampleArtifact, ...]
    artifact_bytes: tuple[bytes, ...]
    replay_result_refs: tuple[SharedKernelReplayResultRef, ...]


class SharedKernelCandidateEngine(Protocol):
    kind: SharedKernelCandidateEngineKind
    version: str

    def execute(
        self,
        request: SharedKernelCandidateRequest,
        proposal: ImprovementProposal,
        candidate: EvaluationCandidateSpec,
        plan: ProposalEvaluationPlan,
        config: FrozenSharedKernelCandidateConfig,
        manifests: tuple[SharedKernelReplayDataManifest, ...],
        data_directories: Mapping[MetricScope, Path],
        output_directory: Path,
    ) -> SharedKernelCandidateEngineOutput: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SharedKernelMasterFusionEngineV1:
    """Run one frozen Master policy through the production-equivalent replay composition."""

    kind = SharedKernelCandidateEngineKind.SHARED_KERNEL_MASTER_FUSION_V1
    version = "1.0"

    def execute(
        self,
        request: SharedKernelCandidateRequest,
        proposal: ImprovementProposal,
        candidate: EvaluationCandidateSpec,
        plan: ProposalEvaluationPlan,
        config: FrozenSharedKernelCandidateConfig,
        manifests: tuple[SharedKernelReplayDataManifest, ...],
        data_directories: Mapping[MetricScope, Path],
        output_directory: Path,
    ) -> SharedKernelCandidateEngineOutput:
        self._validate_governance(request, proposal, candidate, plan, config)
        manifest_by_scope = {item.scope: item for item in manifests}
        required_scopes = {
            item.scope for item in plan.metrics if item.scope is not MetricScope.FINAL_OOS
        }
        if (
            len(manifest_by_scope) != len(manifests)
            or set(manifest_by_scope) != required_scopes
            or set(data_directories) != required_scopes
        ):
            raise ValueError("shared-kernel input scopes do not match plan")
        expected_keys = {
            item.metric_key
            for item in plan.metrics
            if item.scope is not MetricScope.FINAL_OOS
        }
        for metric in plan.metrics:
            if metric.scope is MetricScope.FINAL_OOS:
                continue
            prefix = f"{metric.scope.value.lower()}_"
            if not metric.metric_key.startswith(prefix) or metric.metric_key[len(prefix) :] not in (
                _METRIC_SUFFIXES
            ):
                raise ValueError(f"metric is not allowlisted: {metric.metric_key}")

        baseline = default_shared_kernel_policy_set()
        if config.base_policy_set_id != baseline.policy_set_id:
            raise ValueError("frozen candidate baseline policy set is not current")
        policies = baseline.with_master_fusion(config.fusion_policy)
        artifacts: list[CanonicalMetricSampleArtifact] = []
        replay_refs: list[SharedKernelReplayResultRef] = []
        for scope in sorted(required_scopes, key=lambda item: item.value):
            manifest = manifest_by_scope[scope]
            data_dir = Path(data_directories[scope])
            self._verify_manifest(request, manifest, data_dir)
            run_dir = output_directory / scope.value.lower()
            metrics_path = run_system_replay(
                data_dir,
                run_dir,
                months=1,
                policy_set=policies,
            )
            payload = metrics_path.read_bytes()
            metrics = json.loads(payload)
            replay_refs.append(
                SharedKernelReplayResultRef(
                    scope=scope,
                    semantic_id=str(metrics["artifact_id"]),
                    sha256=hashlib.sha256(payload).hexdigest(),
                )
            )
            scoped_keys = tuple(
                sorted(
                    key
                    for key in expected_keys
                    if key.startswith(f"{scope.value.lower()}_")
                )
            )
            artifacts.append(
                CanonicalMetricSampleArtifact(
                    scope=scope,
                    available_at=manifest.available_at,
                    series=tuple(
                        MetricSampleSeries(
                            metric_key=key,
                            values=(self._metric_value(metrics, key, scope),),
                        )
                        for key in scoped_keys
                    ),
                )
            )
        normalized = tuple(sorted(artifacts, key=lambda item: item.scope.value))
        return SharedKernelCandidateEngineOutput(
            artifacts=normalized,
            artifact_bytes=tuple(canonical_record_bytes(item) for item in normalized),
            replay_result_refs=tuple(sorted(replay_refs, key=lambda item: item.scope.value)),
        )

    @staticmethod
    def _validate_governance(
        request: SharedKernelCandidateRequest,
        proposal: ImprovementProposal,
        candidate: EvaluationCandidateSpec,
        plan: ProposalEvaluationPlan,
        config: FrozenSharedKernelCandidateConfig,
    ) -> None:
        config_payload = canonical_record_bytes(config)
        config_digest = hashlib.sha256(config_payload).hexdigest()
        if (
            request.engine_kind
            is not SharedKernelCandidateEngineKind.SHARED_KERNEL_MASTER_FUSION_V1
            or request.engine_version != "1.0"
            or request.proposal_id != proposal.proposal_id
            or candidate.proposal_id != proposal.proposal_id
            or plan.proposal_id != proposal.proposal_id
            or config.proposal_id != proposal.proposal_id
            or config.proposal_key != proposal.proposal_key
            or request.candidate_id != candidate.candidate_id
            or plan.candidate_id != candidate.candidate_id
            or request.plan_id != plan.plan_id
            or candidate.candidate_kind is not CandidateKind.CONFIGURATION
            or candidate.target_component is not ProposalTargetComponent.MASTER_FUSION
            or config.target_component is not ProposalTargetComponent.MASTER_FUSION
            or candidate.config_identity != config.config_id
            or candidate.source_identity != config.source_identity
            or request.config_ref.semantic_id != config.config_id
            or request.config_ref.sha256 != config_digest
            or request.config_ref not in candidate.artifact_refs
            or request.deterministic_seed != plan.deterministic_seed
            or request.environment_identity != plan.environment_identity
        ):
            raise ValueError("shared-kernel candidate governance linkage mismatch")

    @staticmethod
    def _verify_manifest(
        request: SharedKernelCandidateRequest,
        manifest: SharedKernelReplayDataManifest,
        data_dir: Path,
    ) -> None:
        payload = canonical_record_bytes(manifest)
        request_ref = next(
            (item for item in request.data_manifest_refs if item.scope is manifest.scope), None
        )
        if (
            request_ref is None
            or request_ref.semantic_id != manifest.manifest_id
            or request_ref.sha256 != hashlib.sha256(payload).hexdigest()
            or manifest.proposal_id != request.proposal_id
            or manifest.candidate_id != request.candidate_id
            or manifest.plan_id != request.plan_id
        ):
            raise ValueError("shared-kernel data manifest digest or linkage mismatch")
        for reference in manifest.files:
            path = data_dir / reference.file_name
            if (
                not path.is_file()
                or path.stat().st_size != reference.byte_size
                or _sha256(path) != reference.sha256
            ):
                raise ValueError(f"shared-kernel CSV digest mismatch: {reference.file_name}")
        m5 = pd.read_csv(data_dir / "xauusd_m5.csv", usecols=["timestamp"])
        if len(m5) != manifest.m5_row_count:
            raise ValueError("shared-kernel M5 row count mismatch")
        times = pd.to_datetime(m5["timestamp"], utc=True)
        if (
            times.iloc[0].to_pydatetime() != manifest.period_start
            or times.iloc[-1].to_pydatetime() + timedelta(minutes=5) != manifest.period_end
        ):
            raise ValueError("shared-kernel M5 coverage mismatch")

    @staticmethod
    def _metric_value(metrics: dict[str, object], key: str, scope: MetricScope) -> float:
        suffix = key.removeprefix(f"{scope.value.lower()}_")
        decisions = metrics["decisions"]
        discipline = metrics["discipline"]
        risk = metrics["risk"]
        execution = metrics["execution"]
        trades = metrics["trades"]
        assert isinstance(decisions, dict)
        assert isinstance(discipline, dict)
        assert isinstance(risk, dict)
        assert isinstance(execution, dict)
        assert isinstance(trades, dict)
        cycles = int(decisions["m5_cycles"])
        master = decisions["master"]
        discipline_results = discipline["results"]
        risk_results = risk["results"]
        assert isinstance(master, dict)
        assert isinstance(discipline_results, dict)
        assert isinstance(risk_results, dict)
        values = {
            "master_actionable_rate": (
                (int(master.get("BUY", 0)) + int(master.get("SELL", 0))) / cycles
                if cycles
                else 0.0
            ),
            "discipline_pass_rate": int(discipline_results.get("PASS", 0)) / cycles
            if cycles
            else 0.0,
            "risk_pass_rate": int(risk_results.get("PASS", 0)) / cycles if cycles else 0.0,
            "execution_intent_count": float(execution["intents"]),
            "completed_trade_count": float(trades["completed"]),
            "realized_pnl_usd": float(trades["realized_pnl"]),
            "max_drawdown_usd": float(trades["max_drawdown"]),
        }
        return values[suffix]
