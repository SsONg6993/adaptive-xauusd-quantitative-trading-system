"""Pure preregistration and evidence evaluation for improvement proposals."""

from __future__ import annotations

from collections.abc import Sequence

from axq.reflection.evaluation_contracts import (
    AcceptanceCriterion,
    CriterionComparator,
    CriterionOutcome,
    CriterionOutcomeStatus,
    CriterionRole,
    EvaluationAggregateOutcome,
    EvaluationCandidateSpec,
    MetricObservation,
    MetricObservationStatus,
    ProposalEvaluationPlan,
    ProposalEvaluationResult,
    ValidationMetricSpec,
)
from axq.reflection.proposal_contracts import ImprovementProposal, ProposalStatus
from axq.runtime.state import UTCDateTime


def build_evaluation_plan(
    *,
    proposal: ImprovementProposal,
    proposal_status: ProposalStatus,
    candidate: EvaluationCandidateSpec,
    metrics: Sequence[ValidationMetricSpec],
    criteria: Sequence[AcceptanceCriterion],
    deterministic_seed: int,
    environment_identity: str,
    defined_at: UTCDateTime,
    actor_id: str,
    action_id: str,
    minimum_total_samples: int = 1,
    supersedes_plan_id: str | None = None,
) -> ProposalEvaluationPlan:
    """Preregister a frozen plan without executing its evaluator."""

    if proposal_status is not ProposalStatus.CANDIDATE:
        raise ValueError("evaluation plan registration requires CANDIDATE proposal status")
    if candidate.proposal_id != proposal.proposal_id:
        raise ValueError("candidate proposal ID does not match proposal")
    if candidate.proposal_key != proposal.proposal_key:
        raise ValueError("candidate proposal key does not match proposal")
    if candidate.target_component is not proposal.target_component:
        raise ValueError("candidate target component does not match proposal")
    if defined_at < proposal.available_at or defined_at < candidate.defined_at:
        raise ValueError("evaluation plan cannot predate proposal or candidate availability")
    return ProposalEvaluationPlan(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        candidate_id=candidate.candidate_id,
        source_pattern_ids=proposal.supporting_pattern_ids,
        source_finding_ids=proposal.supporting_finding_ids,
        source_daily_reflection_ids=proposal.supporting_daily_reflection_ids,
        source_experience_ids=proposal.supporting_experience_ids,
        source_weekly_reflection_ids=proposal.supporting_weekly_reflection_ids,
        deterministic_seed=deterministic_seed,
        environment_identity=environment_identity,
        metrics=tuple(metrics),
        criteria=tuple(criteria),
        minimum_total_samples=minimum_total_samples,
        defined_at=defined_at,
        actor_id=actor_id,
        action_id=action_id,
        supersedes_plan_id=supersedes_plan_id,
    )


def _criterion_status(
    criterion: AcceptanceCriterion,
    observation: MetricObservation,
    minimum_total_samples: int,
) -> CriterionOutcomeStatus:
    if (
        observation.status is MetricObservationStatus.UNAVAILABLE
        or observation.sample_count < criterion.minimum_samples
        or observation.sample_count < minimum_total_samples
        or observation.value is None
    ):
        return CriterionOutcomeStatus.INCONCLUSIVE
    value = observation.value
    threshold = criterion.lower_threshold
    if threshold is None:
        raise ValueError("criterion lower threshold is unavailable")
    if criterion.comparator is CriterionComparator.GE:
        passed = value >= threshold
    elif criterion.comparator is CriterionComparator.LE:
        passed = value <= threshold
    else:
        if criterion.upper_threshold is None:
            raise ValueError("BETWEEN criterion upper threshold is unavailable")
        passed = threshold <= value <= criterion.upper_threshold
    return CriterionOutcomeStatus.PASSED if passed else CriterionOutcomeStatus.FAILED


def build_evaluation_result(
    *,
    plan: ProposalEvaluationPlan,
    evaluation_run_key: str,
    observations: Sequence[MetricObservation],
    available_at: UTCDateTime,
    supersedes_result_id: str | None = None,
) -> ProposalEvaluationResult:
    """Evaluate supplied evidence only against the exact preregistered plan."""

    observed = {item.metric_key: item for item in observations}
    expected = {item.metric_key: item for item in plan.metrics}
    if len(observed) != len(observations) or set(observed) != set(expected):
        raise ValueError("observations must exactly match preregistered metrics")
    if available_at < plan.defined_at or any(
        item.available_at > available_at for item in observed.values()
    ):
        raise ValueError("result availability cannot predate its plan or observations")
    for metric_key, metric in expected.items():
        if observed[metric_key].scope is not metric.scope:
            raise ValueError("observation scope does not match preregistered metric")

    outcomes = tuple(
        CriterionOutcome(
            criterion_id=criterion.criterion_id,
            metric_key=criterion.metric_key,
            role=criterion.role,
            status=_criterion_status(
                criterion,
                observed[criterion.metric_key],
                plan.minimum_total_samples,
            ),
            observation_id=observed[criterion.metric_key].observation_id,
        )
        for criterion in plan.criteria
    )
    decision_statuses = tuple(
        item.status for item in outcomes if item.role is CriterionRole.DECISION
    )
    if CriterionOutcomeStatus.FAILED in decision_statuses:
        aggregate = EvaluationAggregateOutcome.NOT_SUPPORTED
    elif CriterionOutcomeStatus.INCONCLUSIVE in decision_statuses:
        aggregate = EvaluationAggregateOutcome.INCONCLUSIVE
    else:
        aggregate = EvaluationAggregateOutcome.SUPPORTED
    return ProposalEvaluationResult(
        plan_id=plan.plan_id,
        proposal_id=plan.proposal_id,
        candidate_id=plan.candidate_id,
        evaluation_run_key=evaluation_run_key,
        available_at=available_at,
        observations=tuple(observations),
        criterion_outcomes=outcomes,
        aggregate_outcome=aggregate,
        supersedes_result_id=supersedes_result_id,
    )
