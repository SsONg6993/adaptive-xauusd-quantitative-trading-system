from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.reflection.evaluation_contracts import (
    AcceptanceCriterion,
    CriterionComparator,
    CriterionRole,
    EvaluationAggregateOutcome,
    MetricDirection,
    MetricObservationStatus,
    MetricScope,
    ProposalEvaluationPlan,
    ValidationMetricSpec,
)
from axq.reflection.execution_adapter import (
    CanonicalMetricSamplesAdapter,
    canonical_record_bytes,
    input_artifact_ref,
)
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationExecutionRequest,
    MetricSampleSeries,
)

NOW = datetime(2026, 9, 11, 10, 0, tzinfo=UTC)


def _metric(key: str, aggregation: str, scope: MetricScope) -> ValidationMetricSpec:
    return ValidationMetricSpec(
        metric_key=key,
        name=key,
        unit="value",
        aggregation=aggregation,
        scope=scope,
        direction=MetricDirection.DESCRIPTIVE,
    )


def _plan() -> ProposalEvaluationPlan:
    metrics = (
        _metric("development_sum", "SUM", MetricScope.DEVELOPMENT),
        _metric("validation_count", "COUNT", MetricScope.VALIDATION),
        _metric("validation_max", "MAX", MetricScope.VALIDATION),
        _metric("validation_mean", "MEAN", MetricScope.VALIDATION),
        _metric("validation_min", "MIN", MetricScope.VALIDATION),
        _metric("final_oos_mean", "MEAN", MetricScope.FINAL_OOS),
    )
    return ProposalEvaluationPlan(
        proposal_id="improvement-proposal-1",
        proposal_key="improvement-proposal-key-1",
        candidate_id="evaluation-candidate-1",
        source_pattern_ids=("pattern-1",),
        source_finding_ids=("finding-1",),
        source_daily_reflection_ids=("daily-1",),
        source_experience_ids=("experience-1",),
        source_weekly_reflection_ids=("weekly-1",),
        deterministic_seed=1729,
        environment_identity="python-3.12-lock-a",
        metrics=metrics,
        criteria=(
            AcceptanceCriterion(
                metric_key="validation_mean",
                comparator=CriterionComparator.GE,
                lower_threshold=0.0,
                minimum_samples=3,
                role=CriterionRole.DECISION,
            ),
            AcceptanceCriterion(
                metric_key="final_oos_mean",
                comparator=CriterionComparator.GE,
                lower_threshold=0.0,
                minimum_samples=1,
                role=CriterionRole.REPORTING_ONLY,
            ),
        ),
        minimum_total_samples=1,
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )


def _artifacts() -> tuple[CanonicalMetricSampleArtifact, ...]:
    development = CanonicalMetricSampleArtifact(
        scope=MetricScope.DEVELOPMENT,
        available_at=NOW + timedelta(minutes=1),
        series=(MetricSampleSeries(metric_key="development_sum", values=(1.0, 2.0, 3.0)),),
    )
    validation = CanonicalMetricSampleArtifact(
        scope=MetricScope.VALIDATION,
        available_at=NOW + timedelta(minutes=2),
        series=(
            MetricSampleSeries(metric_key="validation_mean", values=(1.0, 2.0, 3.0)),
            MetricSampleSeries(metric_key="validation_min", values=(3.0, 1.0, 2.0)),
            MetricSampleSeries(metric_key="validation_max", values=(3.0, 1.0, 2.0)),
            MetricSampleSeries(metric_key="validation_count", values=(9.0, 8.0, 7.0)),
        ),
    )
    return development, validation


def _request(plan: ProposalEvaluationPlan, artifacts) -> EvaluationExecutionRequest:
    return EvaluationExecutionRequest(
        plan_id=plan.plan_id,
        candidate_id=plan.candidate_id,
        evaluation_run_key="controlled-fixture-v1",
        deterministic_seed=plan.deterministic_seed,
        environment_identity=plan.environment_identity,
        input_artifact_refs=tuple(input_artifact_ref(item) for item in artifacts),
        requested_at=NOW + timedelta(minutes=3),
    )


def test_adapter_computes_only_closed_preregistered_aggregations() -> None:
    plan = _plan()
    artifacts = _artifacts()
    output = CanonicalMetricSamplesAdapter().execute(_request(plan, artifacts), plan, artifacts)
    values = {item.metric_key: item.value for item in output.result.observations}

    assert values == {
        "development_sum": 6.0,
        "final_oos_mean": None,
        "validation_count": 3.0,
        "validation_max": 3.0,
        "validation_mean": 2.0,
        "validation_min": 1.0,
    }
    assert output.result.aggregate_outcome is EvaluationAggregateOutcome.SUPPORTED
    assert output.result_bytes == canonical_record_bytes(output.result)


def test_final_oos_is_unavailable_without_an_input_artifact() -> None:
    plan = _plan()
    artifacts = _artifacts()
    output = CanonicalMetricSamplesAdapter().execute(_request(plan, artifacts), plan, artifacts)
    final = next(
        item for item in output.result.observations if item.scope is MetricScope.FINAL_OOS
    )

    assert {item.scope for item in artifacts} == {
        MetricScope.DEVELOPMENT,
        MetricScope.VALIDATION,
    }
    assert final.status is MetricObservationStatus.UNAVAILABLE
    assert final.reason_code == "FINAL_OOS_NOT_ACCESSED"
    assert final.sample_count == 0
    assert final.value is None


def test_adapter_is_byte_deterministic_under_reordered_artifacts_and_series() -> None:
    plan = _plan()
    artifacts = _artifacts()
    reordered = tuple(
        CanonicalMetricSampleArtifact(
            scope=item.scope,
            available_at=item.available_at,
            series=tuple(reversed(item.series)),
        )
        for item in reversed(artifacts)
    )
    first = CanonicalMetricSamplesAdapter().execute(_request(plan, artifacts), plan, artifacts)
    second = CanonicalMetricSamplesAdapter().execute(
        _request(plan, reordered), plan, reordered
    )

    assert first.result.result_id == second.result.result_id
    assert first.result_bytes == second.result_bytes


def test_adapter_fails_closed_for_linkage_scope_series_and_aggregation_mismatch() -> None:
    plan = _plan()
    artifacts = _artifacts()
    request = _request(plan, artifacts)
    with pytest.raises(ValueError, match="candidate linkage"):
        CanonicalMetricSamplesAdapter().execute(
            request.model_copy(update={"candidate_id": "evaluation-candidate-other"}),
            plan,
            artifacts,
        )
    incomplete = (artifacts[0],)
    with pytest.raises(ValueError, match="input scopes"):
        CanonicalMetricSamplesAdapter().execute(request, plan, incomplete)
    extra = CanonicalMetricSampleArtifact(
        scope=MetricScope.VALIDATION,
        available_at=artifacts[1].available_at,
        series=artifacts[1].series
        + (MetricSampleSeries(metric_key="undeclared", values=(1.0,)),),
    )
    with pytest.raises(ValueError, match="exactly match"):
        CanonicalMetricSamplesAdapter().execute(
            _request(plan, (artifacts[0], extra)), plan, (artifacts[0], extra)
        )
    unsupported = plan.model_copy(
        update={
            "metrics": (
                *plan.metrics[:-1],
                _metric("final_oos_mean", "MEDIAN", MetricScope.FINAL_OOS),
            )
        }
    )
    with pytest.raises(ValueError, match="unsupported aggregation"):
        CanonicalMetricSamplesAdapter().execute(request, unsupported, artifacts)
