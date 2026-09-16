"""Allowlisted deterministic engine for controlled candidate replay fixtures."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from axq.reflection.candidate_replay_contracts import (
    CandidateReplayEngineKind,
    CandidateReplayRequest,
    ControlledReplayFixtureArtifact,
)
from axq.reflection.evaluation_contracts import (
    EvaluationCandidateSpec,
    MetricScope,
    ProposalEvaluationPlan,
)
from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    MetricSampleSeries,
)
from axq.reflection.proposal_contracts import ImprovementProposal


@dataclass(frozen=True)
class CandidateReplayEngineOutput:
    artifacts: tuple[CanonicalMetricSampleArtifact, ...]
    artifact_bytes: tuple[bytes, ...]


class CandidateReplayEngine(Protocol):
    kind: CandidateReplayEngineKind
    version: str

    def execute(
        self,
        request: CandidateReplayRequest,
        proposal: ImprovementProposal,
        candidate: EvaluationCandidateSpec,
        plan: ProposalEvaluationPlan,
        fixtures: tuple[ControlledReplayFixtureArtifact, ...],
    ) -> CandidateReplayEngineOutput: ...


class ControlledReplayFixtureEngine:
    """Replay a tiny canonical observation stream without external side effects."""

    kind = CandidateReplayEngineKind.CONTROLLED_REPLAY_FIXTURE_V1
    version = "1.0"

    def execute(
        self,
        request: CandidateReplayRequest,
        proposal: ImprovementProposal,
        candidate: EvaluationCandidateSpec,
        plan: ProposalEvaluationPlan,
        fixtures: tuple[ControlledReplayFixtureArtifact, ...],
    ) -> CandidateReplayEngineOutput:
        self._validate_linkage(request, proposal, candidate, plan)
        fixtures = tuple(sorted(fixtures, key=lambda item: item.scope.value))
        required_scopes = {
            item.scope for item in plan.metrics if item.scope is not MetricScope.FINAL_OOS
        }
        if {item.scope for item in fixtures} != required_scopes:
            raise ValueError("controlled replay fixture scopes do not match plan")
        if len({item.scope for item in fixtures}) != len(fixtures):
            raise ValueError("controlled replay fixture scopes must be unique")
        refs = {item.scope: item for item in request.input_artifact_refs}
        artifacts: list[CanonicalMetricSampleArtifact] = []
        for fixture in fixtures:
            if (
                fixture.proposal_id != proposal.proposal_id
                or fixture.candidate_id != candidate.candidate_id
                or fixture.plan_id != plan.plan_id
            ):
                raise ValueError("controlled replay fixture linkage mismatch")
            payload = canonical_record_bytes(fixture)
            ref = refs.get(fixture.scope)
            if (
                ref is None
                or ref.semantic_id != fixture.artifact_id
                or ref.sha256 != hashlib.sha256(payload).hexdigest()
            ):
                raise ValueError("controlled replay fixture digest linkage mismatch")
            expected_keys = {
                item.metric_key for item in plan.metrics if item.scope is fixture.scope
            }
            values: dict[str, list[float]] = {
                metric_key: [] for metric_key in expected_keys
            }
            observations = sorted(
                fixture.observations,
                key=lambda item: (item.available_at, item.event_id),
            )
            for observation in observations:
                observed = {item.metric_key: item.value for item in observation.metric_values}
                if set(observed) != expected_keys:
                    raise ValueError("controlled replay observation metric keys do not match plan")
                for metric_key in sorted(expected_keys):
                    values[metric_key].append(observed[metric_key])
            artifacts.append(
                CanonicalMetricSampleArtifact(
                    scope=fixture.scope,
                    available_at=fixture.available_at,
                    series=tuple(
                        MetricSampleSeries(metric_key=key, values=tuple(values[key]))
                        for key in sorted(values)
                    ),
                )
            )
        normalized = tuple(sorted(artifacts, key=lambda item: item.scope.value))
        return CandidateReplayEngineOutput(
            artifacts=normalized,
            artifact_bytes=tuple(canonical_record_bytes(item) for item in normalized),
        )

    @staticmethod
    def _validate_linkage(
        request: CandidateReplayRequest,
        proposal: ImprovementProposal,
        candidate: EvaluationCandidateSpec,
        plan: ProposalEvaluationPlan,
    ) -> None:
        if (
            request.proposal_id != proposal.proposal_id
            or candidate.proposal_id != proposal.proposal_id
            or plan.proposal_id != proposal.proposal_id
            or request.candidate_id != candidate.candidate_id
            or plan.candidate_id != candidate.candidate_id
            or request.plan_id != plan.plan_id
            or request.deterministic_seed != plan.deterministic_seed
            or request.environment_identity != plan.environment_identity
            or request.evaluation_run_key == ""
        ):
            raise ValueError("candidate replay request linkage mismatch")
