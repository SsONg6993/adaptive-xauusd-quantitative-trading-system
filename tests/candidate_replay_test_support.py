from __future__ import annotations

import hashlib
from datetime import timedelta
from pathlib import Path

from evaluation_execution_test_support import NOW, persist_controlled_plan

from axq.reflection.candidate_replay_contracts import (
    CandidateReplayArtifactRef,
    CandidateReplayRequest,
    ControlledMetricValue,
    ControlledReplayFixtureArtifact,
    ControlledReplayObservation,
)
from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.execution_adapter import canonical_record_bytes


def controlled_fixture(
    proposal_id: str,
    candidate_id: str,
    plan_id: str,
    scope: MetricScope,
) -> ControlledReplayFixtureArtifact:
    metric_key = (
        "development_expectancy"
        if scope is MetricScope.DEVELOPMENT
        else "validation_expectancy"
    )
    return ControlledReplayFixtureArtifact(
        proposal_id=proposal_id,
        candidate_id=candidate_id,
        plan_id=plan_id,
        scope=scope,
        available_at=NOW + timedelta(minutes=2),
        observations=(
            ControlledReplayObservation(
                event_id=f"{scope.value.lower()}-event-2",
                available_at=NOW + timedelta(minutes=2),
                metric_values=(ControlledMetricValue(metric_key=metric_key, value=0.3),),
            ),
            ControlledReplayObservation(
                event_id=f"{scope.value.lower()}-event-1",
                available_at=NOW + timedelta(minutes=1),
                metric_values=(ControlledMetricValue(metric_key=metric_key, value=-0.1),),
            ),
        ),
    )


def fixture_ref(fixture: ControlledReplayFixtureArtifact) -> CandidateReplayArtifactRef:
    payload = canonical_record_bytes(fixture)
    return CandidateReplayArtifactRef(
        scope=fixture.scope,
        semantic_id=fixture.artifact_id,
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def persisted_candidate_replay(path: Path, *, include_development: bool = False):
    proposal, candidate, plan = persist_controlled_plan(
        path,
        include_development=include_development,
    )
    scopes = (
        (MetricScope.DEVELOPMENT, MetricScope.VALIDATION)
        if include_development
        else (MetricScope.VALIDATION,)
    )
    fixtures = tuple(
        controlled_fixture(proposal.proposal_id, candidate.candidate_id, plan.plan_id, scope)
        for scope in scopes
    )
    request = CandidateReplayRequest(
        proposal_id=proposal.proposal_id,
        candidate_id=candidate.candidate_id,
        plan_id=plan.plan_id,
        evaluation_run_key="controlled-candidate-replay",
        deterministic_seed=plan.deterministic_seed,
        environment_identity=plan.environment_identity,
        input_artifact_refs=tuple(fixture_ref(item) for item in fixtures),
        requested_at=NOW + timedelta(minutes=3),
    )
    return proposal, candidate, plan, fixtures, request
