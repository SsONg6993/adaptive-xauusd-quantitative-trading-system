from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from axq.reflection.evaluation_contracts import (
    AcceptanceCriterion,
    CandidateKind,
    CriterionComparator,
    CriterionOutcome,
    CriterionOutcomeStatus,
    CriterionRole,
    EvaluationAggregateOutcome,
    EvaluationCandidateSpec,
    FinalOOSPolicy,
    MetricDirection,
    MetricObservation,
    MetricObservationStatus,
    MetricScope,
    OperatorEvaluationDecision,
    OperatorEvaluationDecisionKind,
    ProposalEvaluationPlan,
    ProposalEvaluationResult,
    SemanticArtifactRef,
    ValidationMetricSpec,
)
from axq.reflection.proposal_contracts import ProposalTargetComponent

NOW = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)


def _candidate(**changes: object) -> EvaluationCandidateSpec:
    values: dict[str, object] = {
        "proposal_id": "improvement-proposal-1",
        "proposal_key": "improvement-proposal-key-1",
        "target_component": ProposalTargetComponent.MASTER_FUSION,
        "candidate_kind": CandidateKind.RULE,
        "description": "Evaluate a frozen evidence-fusion rule candidate.",
        "implementation_version": "candidate-v1",
        "source_identity": "git-abc123",
        "config_identity": "config-123",
        "manifest_identity": "manifest-123",
        "artifact_refs": (
            SemanticArtifactRef(
                semantic_id="artifact-b",
                sha256="b" * 64,
            ),
            SemanticArtifactRef(
                semantic_id="artifact-a",
                sha256="a" * 64,
            ),
        ),
        "defined_at": NOW,
    }
    values.update(changes)
    return EvaluationCandidateSpec(**values)


def _metric(
    key: str = "validation_expectancy_r",
    *,
    scope: MetricScope = MetricScope.VALIDATION,
) -> ValidationMetricSpec:
    return ValidationMetricSpec(
        metric_key=key,
        name="Expectancy",
        unit="R",
        aggregation="MEAN",
        scope=scope,
        direction=MetricDirection.HIGHER_IS_BETTER,
    )


def _criterion(
    metric_key: str = "validation_expectancy_r",
    *,
    role: CriterionRole = CriterionRole.DECISION,
) -> AcceptanceCriterion:
    return AcceptanceCriterion(
        metric_key=metric_key,
        comparator=CriterionComparator.GE,
        lower_threshold=0.0,
        minimum_samples=20,
        role=role,
    )


def _plan(**changes: object) -> ProposalEvaluationPlan:
    candidate = _candidate()
    values: dict[str, object] = {
        "proposal_id": candidate.proposal_id,
        "proposal_key": candidate.proposal_key,
        "candidate_id": candidate.candidate_id,
        "source_pattern_ids": ("pattern-b", "pattern-a"),
        "source_finding_ids": ("finding-b", "finding-a"),
        "source_daily_reflection_ids": ("daily-b", "daily-a"),
        "source_experience_ids": ("experience-b", "experience-a"),
        "source_weekly_reflection_ids": ("weekly-b", "weekly-a"),
        "deterministic_seed": 1729,
        "environment_identity": "python-3.12-lock-abc",
        "metrics": (_metric(),),
        "criteria": (_criterion(),),
        "minimum_total_samples": 20,
        "final_oos_policy": FinalOOSPolicy.REPORTING_ONLY,
        "defined_at": NOW,
        "actor_id": "operator-1",
        "action_id": "plan-registration-1",
    }
    values.update(changes)
    return ProposalEvaluationPlan(**values)


def test_candidate_is_frozen_strict_utc_and_content_addressed() -> None:
    first = _candidate()
    reordered = _candidate(artifact_refs=tuple(reversed(first.artifact_refs)))

    assert first == reordered
    assert first.candidate_id.startswith("evaluation-candidate-")
    with pytest.raises(ValidationError):
        first.description = "mutated"
    with pytest.raises(ValidationError, match="timezone-aware"):
        _candidate(defined_at=datetime(2026, 9, 11, 8, 0))
    with pytest.raises(ValidationError, match="candidate_id does not match"):
        _candidate(candidate_id="evaluation-candidate-tampered")
    with pytest.raises(ValidationError):
        _candidate(extra_field=True)


def test_plan_identity_normalizes_provenance_metrics_and_criteria() -> None:
    first = _plan()
    reordered = _plan(
        source_pattern_ids=("pattern-a", "pattern-b", "pattern-a"),
        metrics=tuple(reversed(first.metrics)),
        criteria=tuple(reversed(first.criteria)),
    )

    assert first == reordered
    assert first.plan_id.startswith("proposal-evaluation-plan-")
    assert first.source_pattern_ids == ("pattern-a", "pattern-b")
    with pytest.raises(ValidationError, match="plan_id does not match"):
        _plan(plan_id="proposal-evaluation-plan-tampered")


def test_plan_rejects_missing_decision_criterion_and_duplicate_keys() -> None:
    with pytest.raises(ValidationError, match="non-Final-OOS decision criterion"):
        _plan(criteria=(_criterion(role=CriterionRole.REPORTING_ONLY),))
    with pytest.raises(ValidationError, match="metric keys must be unique"):
        _plan(metrics=(_metric(), _metric()))
    duplicated = _criterion()
    with pytest.raises(ValidationError, match="criterion IDs must be unique"):
        _plan(criteria=(duplicated, duplicated))


def test_final_oos_is_structurally_reporting_only() -> None:
    final_metric = _metric("final_oos_expectancy_r", scope=MetricScope.FINAL_OOS)
    with pytest.raises(ValidationError, match="Final OOS criteria must be reporting-only"):
        _plan(
            metrics=(_metric(), final_metric),
            criteria=(
                _criterion(),
                _criterion("final_oos_expectancy_r", role=CriterionRole.DECISION),
            ),
        )

    plan = _plan(
        metrics=(_metric(), final_metric),
        criteria=(
            _criterion(),
            _criterion("final_oos_expectancy_r", role=CriterionRole.REPORTING_ONLY),
        ),
    )
    assert plan.final_oos_policy is FinalOOSPolicy.REPORTING_ONLY


def test_result_and_operator_decision_are_immutable_content_records() -> None:
    plan = _plan()
    observation = MetricObservation(
        metric_key="validation_expectancy_r",
        scope=MetricScope.VALIDATION,
        status=MetricObservationStatus.AVAILABLE,
        value=0.25,
        sample_count=25,
        evidence_refs=(SemanticArtifactRef(semantic_id="result-evidence", sha256="c" * 64),),
        available_at=NOW,
    )
    criterion = plan.criteria[0]
    outcome = CriterionOutcome(
        criterion_id=criterion.criterion_id,
        metric_key=criterion.metric_key,
        role=criterion.role,
        status=CriterionOutcomeStatus.PASSED,
        observation_id=observation.observation_id,
    )
    result = ProposalEvaluationResult(
        plan_id=plan.plan_id,
        proposal_id=plan.proposal_id,
        candidate_id=plan.candidate_id,
        evaluation_run_key="run-1",
        available_at=NOW,
        observations=(observation,),
        criterion_outcomes=(outcome,),
        aggregate_outcome=EvaluationAggregateOutcome.SUPPORTED,
    )
    decision = OperatorEvaluationDecision(
        result_id=result.result_id,
        plan_id=plan.plan_id,
        proposal_id=plan.proposal_id,
        candidate_id=plan.candidate_id,
        decision=OperatorEvaluationDecisionKind.ACCEPT_EVIDENCE,
        decision_criterion_ids=(criterion.criterion_id,),
        actor_id="operator-1",
        action_id="evidence-review-1",
        reason_code="CRITERIA_SUPPORTED",
        effective_at=NOW,
    )

    assert result.result_id.startswith("proposal-evaluation-result-")
    assert decision.decision_id.startswith("operator-evaluation-decision-")
    with pytest.raises(ValidationError):
        result.aggregate_outcome = EvaluationAggregateOutcome.NOT_SUPPORTED
    with pytest.raises(ValidationError, match="criteria"):
        ProposalEvaluationResult(
            **result.model_dump(exclude={"result_id"}),
            criteria=plan.criteria,
        )
    with pytest.raises(ValidationError, match="decision criterion"):
        OperatorEvaluationDecision(
            **decision.model_dump(exclude={"decision_id", "decision_criterion_ids"}),
            decision_criterion_ids=(),
        )
