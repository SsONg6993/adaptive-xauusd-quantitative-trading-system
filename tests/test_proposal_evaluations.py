from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from axq.reflection.contracts import FindingCategory, SampleGuardStatus
from axq.reflection.evaluation_contracts import (
    AcceptanceCriterion,
    CandidateKind,
    CriterionComparator,
    CriterionOutcomeStatus,
    CriterionRole,
    EvaluationAggregateOutcome,
    EvaluationCandidateSpec,
    MetricDirection,
    MetricObservation,
    MetricObservationStatus,
    MetricScope,
    SemanticArtifactRef,
    ValidationMetricSpec,
)
from axq.reflection.evaluations import build_evaluation_plan, build_evaluation_result
from axq.reflection.proposal_contracts import (
    ImprovementProposal,
    ImprovementProposalPolicy,
    ProposalEvidenceGuard,
    ProposalGuardKind,
    ProposalStatus,
    ProposalTargetComponent,
)
from axq.reflection.weekly_contracts import PatternSignalClass, PatternType

NOW = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)


def _proposal() -> ImprovementProposal:
    guard = ProposalEvidenceGuard(
        guard_kind=ProposalGuardKind.PATTERN_RECURRENCE,
        observed_samples=2,
        required_samples=2,
        status=SampleGuardStatus.PASSED,
        supporting_pattern_ids=("pattern-1", "pattern-2"),
    )
    return ImprovementProposal(
        policy_id=ImprovementProposalPolicy().policy_id,
        pattern_key="pattern-key-1",
        target_component=ProposalTargetComponent.MASTER_FUSION,
        category=FindingCategory.DIRECTION_OUTCOME,
        pattern_type=PatternType.FAILURE,
        signal_class=PatternSignalClass.ADVERSE,
        reason_code="NEGATIVE_AVERAGE_R",
        scope="direction",
        scope_value="BUY",
        rationale="Repeated adverse outcome.",
        proposed_change="Evaluate a frozen fusion rule candidate.",
        expected_benefit="Reduce adverse outcomes if supported.",
        risks=("Overfitting",),
        validation_plan=("Use preregistered validation evidence.",),
        source_week_starts=(NOW - timedelta(days=21), NOW - timedelta(days=14)),
        available_at=NOW - timedelta(days=7),
        supporting_weekly_reflection_ids=("weekly-1", "weekly-2"),
        supporting_pattern_ids=("pattern-1", "pattern-2"),
        supporting_daily_reflection_ids=("daily-1", "daily-2"),
        supporting_finding_ids=("finding-1", "finding-2"),
        supporting_experience_ids=("experience-1", "experience-2"),
        supporting_weekly_guard_ids=("guard-1", "guard-2"),
        evidence_guards=(guard,),
    )


def _candidate(proposal: ImprovementProposal, **changes: object) -> EvaluationCandidateSpec:
    values: dict[str, object] = {
        "proposal_id": proposal.proposal_id,
        "proposal_key": proposal.proposal_key,
        "target_component": proposal.target_component,
        "candidate_kind": CandidateKind.RULE,
        "description": "Frozen candidate.",
        "implementation_version": "v1",
        "source_identity": "git-source",
        "config_identity": "config-source",
        "manifest_identity": "manifest-source",
        "artifact_refs": (
            SemanticArtifactRef(semantic_id="candidate-artifact", sha256="a" * 64),
        ),
        "defined_at": NOW,
    }
    values.update(changes)
    return EvaluationCandidateSpec(**values)


def _metric(key: str, scope: MetricScope) -> ValidationMetricSpec:
    return ValidationMetricSpec(
        metric_key=key,
        name=key,
        unit="ratio",
        aggregation="MEAN",
        scope=scope,
        direction=MetricDirection.HIGHER_IS_BETTER,
    )


def _criterion(
    key: str,
    comparator: CriterionComparator,
    threshold: float,
    *,
    role: CriterionRole = CriterionRole.DECISION,
    upper: float | None = None,
) -> AcceptanceCriterion:
    return AcceptanceCriterion(
        metric_key=key,
        comparator=comparator,
        lower_threshold=threshold,
        upper_threshold=upper,
        minimum_samples=10,
        role=role,
    )


def _plan_inputs() -> tuple[
    tuple[ValidationMetricSpec, ...], tuple[AcceptanceCriterion, ...]
]:
    metrics = (
        _metric("validation_expectancy", MetricScope.VALIDATION),
        _metric("validation_drawdown", MetricScope.VALIDATION),
        _metric("validation_coverage", MetricScope.VALIDATION),
        _metric("final_oos_expectancy", MetricScope.FINAL_OOS),
    )
    criteria = (
        _criterion("validation_expectancy", CriterionComparator.GE, 0.0),
        _criterion("validation_drawdown", CriterionComparator.LE, 0.2),
        _criterion("validation_coverage", CriterionComparator.BETWEEN, 0.2, upper=0.8),
        _criterion(
            "final_oos_expectancy",
            CriterionComparator.GE,
            0.0,
            role=CriterionRole.REPORTING_ONLY,
        ),
    )
    return metrics, criteria


def _observation(
    key: str,
    scope: MetricScope,
    value: float,
    samples: int = 20,
) -> MetricObservation:
    return MetricObservation(
        metric_key=key,
        scope=scope,
        status=MetricObservationStatus.AVAILABLE,
        value=value,
        sample_count=samples,
        evidence_refs=(
            SemanticArtifactRef(semantic_id=f"evidence-{key}", sha256="b" * 64),
        ),
        available_at=NOW + timedelta(hours=1),
    )


def test_plan_builder_requires_candidate_status_and_exact_provenance() -> None:
    proposal = _proposal()
    candidate = _candidate(proposal)
    metrics, criteria = _plan_inputs()

    with pytest.raises(ValueError, match="CANDIDATE"):
        build_evaluation_plan(
            proposal=proposal,
            proposal_status=ProposalStatus.HYPOTHESIS,
            candidate=candidate,
            metrics=metrics,
            criteria=criteria,
            deterministic_seed=7,
            environment_identity="test-env",
            defined_at=NOW,
            actor_id="operator",
            action_id="plan-1",
        )
    with pytest.raises(ValueError, match="target component"):
        build_evaluation_plan(
            proposal=proposal,
            proposal_status=ProposalStatus.CANDIDATE,
            candidate=_candidate(proposal, target_component=ProposalTargetComponent.RISK_BOUNDARY),
            metrics=metrics,
            criteria=criteria,
            deterministic_seed=7,
            environment_identity="test-env",
            defined_at=NOW,
            actor_id="operator",
            action_id="plan-1",
        )

    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=candidate,
        metrics=metrics,
        criteria=criteria,
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )
    assert plan.source_pattern_ids == proposal.supporting_pattern_ids
    assert plan.source_experience_ids == proposal.supporting_experience_ids
    assert plan.source_weekly_reflection_ids == proposal.supporting_weekly_reflection_ids


def test_result_builder_ignores_final_oos_for_aggregate() -> None:
    proposal = _proposal()
    metrics, criteria = _plan_inputs()
    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=_candidate(proposal),
        metrics=metrics,
        criteria=criteria,
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )
    observations = (
        _observation("validation_expectancy", MetricScope.VALIDATION, 0.1),
        _observation("validation_drawdown", MetricScope.VALIDATION, 0.1),
        _observation("validation_coverage", MetricScope.VALIDATION, 0.5),
        _observation("final_oos_expectancy", MetricScope.FINAL_OOS, -99.0),
    )

    result = build_evaluation_result(
        plan=plan,
        evaluation_run_key="run-1",
        observations=observations,
        available_at=NOW + timedelta(hours=2),
    )

    assert result.aggregate_outcome is EvaluationAggregateOutcome.SUPPORTED
    assert [item.status for item in result.criterion_outcomes].count(
        CriterionOutcomeStatus.FAILED
    ) == 1
    assert next(
        item for item in result.criterion_outcomes if item.status is CriterionOutcomeStatus.FAILED
    ).role is CriterionRole.REPORTING_ONLY


def test_result_builder_fails_closed_for_missing_undeclared_or_insufficient_evidence() -> None:
    proposal = _proposal()
    metrics, criteria = _plan_inputs()
    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=_candidate(proposal),
        metrics=metrics,
        criteria=criteria,
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )
    complete = (
        _observation("validation_expectancy", MetricScope.VALIDATION, 0.1, samples=2),
        _observation("validation_drawdown", MetricScope.VALIDATION, 0.1),
        _observation("validation_coverage", MetricScope.VALIDATION, 0.5),
        _observation("final_oos_expectancy", MetricScope.FINAL_OOS, 1.0),
    )
    result = build_evaluation_result(
        plan=plan,
        evaluation_run_key="run-2",
        observations=complete,
        available_at=NOW + timedelta(hours=2),
    )
    assert result.aggregate_outcome is EvaluationAggregateOutcome.INCONCLUSIVE

    with pytest.raises(ValueError, match="exactly match preregistered metrics"):
        build_evaluation_result(
            plan=plan,
            evaluation_run_key="run-3",
            observations=complete[:-1],
            available_at=NOW + timedelta(hours=2),
        )
    with pytest.raises(ValueError, match="exactly match preregistered metrics"):
        build_evaluation_result(
            plan=plan,
            evaluation_run_key="run-4",
            observations=complete
            + (_observation("undeclared", MetricScope.DEVELOPMENT, 1.0),),
            available_at=NOW + timedelta(hours=2),
        )
