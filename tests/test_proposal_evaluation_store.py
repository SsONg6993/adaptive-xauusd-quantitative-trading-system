from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from axq.reflection.contracts import FindingCategory, SampleGuardStatus
from axq.reflection.evaluation_contracts import (
    AcceptanceCriterion,
    CandidateKind,
    CriterionComparator,
    CriterionRole,
    EvaluationCandidateSpec,
    MetricDirection,
    MetricObservation,
    MetricObservationStatus,
    MetricScope,
    OperatorEvaluationDecision,
    OperatorEvaluationDecisionKind,
    SemanticArtifactRef,
    ValidationMetricSpec,
)
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.evaluations import build_evaluation_plan, build_evaluation_result
from axq.reflection.proposal_contracts import (
    ImprovementProposal,
    ImprovementProposalPolicy,
    ProposalEvidenceGuard,
    ProposalGuardKind,
    ProposalStatus,
    ProposalStatusTransition,
    ProposalTargetComponent,
)
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.weekly_contracts import (
    PatternSignalClass,
    PatternType,
    TransitionActionKind,
)

NOW = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)


def _proposal() -> ImprovementProposal:
    policy = ImprovementProposalPolicy()
    return ImprovementProposal(
        policy_id=policy.policy_id,
        pattern_key="pattern-key-1",
        target_component=ProposalTargetComponent.MASTER_FUSION,
        category=FindingCategory.DIRECTION_OUTCOME,
        pattern_type=PatternType.FAILURE,
        signal_class=PatternSignalClass.ADVERSE,
        reason_code="NEGATIVE_AVERAGE_R",
        scope="direction",
        scope_value="BUY",
        rationale="Repeated adverse outcome.",
        proposed_change="Evaluate a frozen fusion candidate.",
        expected_benefit="Reduce adverse outcomes if supported.",
        risks=("Overfitting",),
        validation_plan=("Use preregistered evidence.",),
        source_week_starts=(NOW - timedelta(days=21), NOW - timedelta(days=14)),
        available_at=NOW - timedelta(days=7),
        supporting_weekly_reflection_ids=("weekly-1", "weekly-2"),
        supporting_pattern_ids=("pattern-1", "pattern-2"),
        supporting_daily_reflection_ids=("daily-1", "daily-2"),
        supporting_finding_ids=("finding-1", "finding-2"),
        supporting_experience_ids=("experience-1", "experience-2"),
        supporting_weekly_guard_ids=("guard-1", "guard-2"),
        evidence_guards=(
            ProposalEvidenceGuard(
                guard_kind=ProposalGuardKind.PATTERN_RECURRENCE,
                observed_samples=2,
                required_samples=2,
                status=SampleGuardStatus.PASSED,
                supporting_pattern_ids=("pattern-1", "pattern-2"),
            ),
        ),
    )


def _promote_candidate(
    store: SQLiteImprovementProposalStore,
    proposal: ImprovementProposal,
) -> None:
    previous: str | None = None
    for index, (source, target) in enumerate(
        (
            (ProposalStatus.OBSERVATION, ProposalStatus.HYPOTHESIS),
            (ProposalStatus.HYPOTHESIS, ProposalStatus.CANDIDATE),
        ),
        start=1,
    ):
        transition = ProposalStatusTransition(
            proposal_id=proposal.proposal_id,
            proposal_key=proposal.proposal_key,
            from_status=source,
            to_status=target,
            effective_at=proposal.available_at + timedelta(minutes=index),
            action_kind=TransitionActionKind.OPERATOR,
            actor_id="operator",
            action_id=f"promotion-{index}",
            reason_code="EXPLICIT_REVIEW",
            previous_transition_id=previous,
        )
        store.append_transition(transition)
        previous = transition.transition_id


def _setup(path, *, promote: bool = True):
    proposal_store = SQLiteImprovementProposalStore(path)
    proposal = _proposal()
    proposal_store.append_policy(ImprovementProposalPolicy())
    proposal_store.append(proposal)
    if promote:
        _promote_candidate(proposal_store, proposal)
    candidate = EvaluationCandidateSpec(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        target_component=proposal.target_component,
        candidate_kind=CandidateKind.RULE,
        description="Frozen candidate.",
        implementation_version="v1",
        source_identity="git-source",
        config_identity="config-source",
        manifest_identity="manifest-source",
        artifact_refs=(SemanticArtifactRef(semantic_id="candidate", sha256="a" * 64),),
        defined_at=NOW,
    )
    metric = ValidationMetricSpec(
        metric_key="validation_expectancy",
        name="Expectancy",
        unit="R",
        aggregation="MEAN",
        scope=MetricScope.VALIDATION,
        direction=MetricDirection.HIGHER_IS_BETTER,
    )
    criterion = AcceptanceCriterion(
        metric_key=metric.metric_key,
        comparator=CriterionComparator.GE,
        lower_threshold=0.0,
        minimum_samples=10,
        role=CriterionRole.DECISION,
    )
    return proposal_store, proposal, candidate, metric, criterion


def test_store_requires_candidate_proposal_and_candidate_status(tmp_path) -> None:
    path = tmp_path / "evaluation.sqlite3"
    proposal_store, proposal, candidate, metric, criterion = _setup(path, promote=False)
    store = SQLiteProposalEvaluationStore(path)

    assert store.append_candidate(candidate) is True
    assert store.append_candidate(candidate) is False
    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=candidate,
        metrics=(metric,),
        criteria=(criterion,),
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )
    with pytest.raises(ValueError, match="CANDIDATE"):
        store.append_plan(plan)

    _promote_candidate(proposal_store, proposal)
    assert store.append_plan(plan) is True
    assert store.append_plan(plan) is False
    assert store.plan(plan.plan_id) == plan
    candidate_transition = ProposalStatusTransition(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        from_status=ProposalStatus.CANDIDATE,
        to_status=ProposalStatus.VALIDATED,
        effective_at=NOW + timedelta(minutes=3),
        action_kind=TransitionActionKind.OPERATOR,
        actor_id="operator",
        action_id="external-evidence-review",
        reason_code="EXPLICIT_EXTERNAL_ACTION",
        previous_transition_id=proposal_store.transition_history(proposal.proposal_id)[-1].transition_id,
    )
    proposal_store.append_transition(candidate_transition)
    assert store.append_plan(plan) is False


def test_store_requires_plan_before_result_and_exact_plan_content(tmp_path) -> None:
    path = tmp_path / "evaluation.sqlite3"
    _, proposal, candidate, metric, criterion = _setup(path)
    store = SQLiteProposalEvaluationStore(path)
    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=candidate,
        metrics=(metric,),
        criteria=(criterion,),
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )
    observation = MetricObservation(
        metric_key=metric.metric_key,
        scope=metric.scope,
        status=MetricObservationStatus.AVAILABLE,
        value=0.2,
        sample_count=20,
        evidence_refs=(SemanticArtifactRef(semantic_id="evidence", sha256="b" * 64),),
        available_at=NOW + timedelta(hours=1),
    )
    result = build_evaluation_result(
        plan=plan,
        evaluation_run_key="run-1",
        observations=(observation,),
        available_at=NOW + timedelta(hours=2),
    )

    store.append_candidate(candidate)
    with pytest.raises(ValueError, match="plan is not persisted"):
        store.append_result(result)
    store.append_plan(plan)
    assert store.append_result(result) is True
    assert store.append_result(result) is False
    assert store.result(result.result_id) == result


def test_store_enforces_result_and_operator_supersession_chains(tmp_path) -> None:
    path = tmp_path / "evaluation.sqlite3"
    _, proposal, candidate, metric, criterion = _setup(path)
    store = SQLiteProposalEvaluationStore(path)
    store.append_candidate(candidate)
    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=candidate,
        metrics=(metric,),
        criteria=(criterion,),
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )
    store.append_plan(plan)
    observation = MetricObservation(
        metric_key=metric.metric_key,
        scope=metric.scope,
        status=MetricObservationStatus.AVAILABLE,
        value=0.2,
        sample_count=20,
        evidence_refs=(SemanticArtifactRef(semantic_id="evidence", sha256="b" * 64),),
        available_at=NOW + timedelta(hours=1),
    )
    result = build_evaluation_result(
        plan=plan,
        evaluation_run_key="run-1",
        observations=(observation,),
        available_at=NOW + timedelta(hours=2),
    )
    store.append_result(result)
    decision = OperatorEvaluationDecision(
        result_id=result.result_id,
        plan_id=plan.plan_id,
        proposal_id=proposal.proposal_id,
        candidate_id=candidate.candidate_id,
        decision=OperatorEvaluationDecisionKind.ACCEPT_EVIDENCE,
        decision_criterion_ids=(criterion.criterion_id,),
        actor_id="operator",
        action_id="decision-1",
        reason_code="SUPPORTED",
        effective_at=NOW + timedelta(hours=3),
    )
    assert store.append_decision(decision) is True
    assert store.append_decision(decision) is False
    assert store.decision_history(result.result_id) == (decision,)

    stale = decision.model_copy(
        update={
            "decision_id": "",
            "decision": OperatorEvaluationDecisionKind.DEFER,
            "decision_criterion_ids": (),
            "action_id": "decision-2",
        }
    )
    with pytest.raises(ValueError, match="previous decision"):
        store.append_decision(OperatorEvaluationDecision(**stale.model_dump(exclude={"decision_id"})))


def test_plan_and_corrected_result_require_explicit_latest_supersession(tmp_path) -> None:
    path = tmp_path / "evaluation.sqlite3"
    _, proposal, candidate, metric, criterion = _setup(path)
    store = SQLiteProposalEvaluationStore(path)
    store.append_candidate(candidate)
    original_plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=candidate,
        metrics=(metric,),
        criteria=(criterion,),
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )
    store.append_plan(original_plan)
    with pytest.raises(ValueError, match="supersede latest plan"):
        store.append_plan(
            build_evaluation_plan(
                proposal=proposal,
                proposal_status=ProposalStatus.CANDIDATE,
                candidate=candidate,
                metrics=(metric,),
                criteria=(criterion,),
                deterministic_seed=7,
                environment_identity="test-env",
                defined_at=NOW + timedelta(minutes=1),
                actor_id="operator",
                action_id="plan-2",
            )
        )
    revised_plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=candidate,
        metrics=(metric,),
        criteria=(criterion,),
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW + timedelta(minutes=1),
        actor_id="operator",
        action_id="plan-2",
        supersedes_plan_id=original_plan.plan_id,
    )
    assert store.append_plan(revised_plan) is True

    first_observation = MetricObservation(
        metric_key=metric.metric_key,
        scope=metric.scope,
        status=MetricObservationStatus.AVAILABLE,
        value=0.2,
        sample_count=20,
        evidence_refs=(SemanticArtifactRef(semantic_id="evidence-1", sha256="b" * 64),),
        available_at=NOW + timedelta(hours=1),
    )
    first_result = build_evaluation_result(
        plan=revised_plan,
        evaluation_run_key="run-1",
        observations=(first_observation,),
        available_at=NOW + timedelta(hours=2),
    )
    store.append_result(first_result)
    corrected_observation = MetricObservation(
        metric_key=metric.metric_key,
        scope=metric.scope,
        status=MetricObservationStatus.AVAILABLE,
        value=0.3,
        sample_count=20,
        evidence_refs=(SemanticArtifactRef(semantic_id="evidence-2", sha256="c" * 64),),
        available_at=NOW + timedelta(hours=3),
    )
    with pytest.raises(ValueError, match="supersede latest result"):
        store.append_result(
            build_evaluation_result(
                plan=revised_plan,
                evaluation_run_key="run-1",
                observations=(corrected_observation,),
                available_at=NOW + timedelta(hours=4),
            )
        )
    corrected_result = build_evaluation_result(
        plan=revised_plan,
        evaluation_run_key="run-1",
        observations=(corrected_observation,),
        available_at=NOW + timedelta(hours=4),
        supersedes_result_id=first_result.result_id,
    )
    assert store.append_result(corrected_result) is True
    assert store.results()[-1].supersedes_result_id == first_result.result_id


def test_all_evaluation_tables_are_append_only(tmp_path) -> None:
    path = tmp_path / "evaluation.sqlite3"
    _, proposal, candidate, metric, criterion = _setup(path)
    store = SQLiteProposalEvaluationStore(path)
    store.append_candidate(candidate)
    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=ProposalStatus.CANDIDATE,
        candidate=candidate,
        metrics=(metric,),
        criteria=(criterion,),
        deterministic_seed=7,
        environment_identity="test-env",
        defined_at=NOW,
        actor_id="operator",
        action_id="plan-1",
    )
    store.append_plan(plan)
    observation = MetricObservation(
        metric_key=metric.metric_key,
        scope=metric.scope,
        status=MetricObservationStatus.AVAILABLE,
        value=0.2,
        sample_count=20,
        evidence_refs=(SemanticArtifactRef(semantic_id="evidence", sha256="b" * 64),),
        available_at=NOW + timedelta(hours=1),
    )
    result = build_evaluation_result(
        plan=plan,
        evaluation_run_key="run-1",
        observations=(observation,),
        available_at=NOW + timedelta(hours=2),
    )
    store.append_result(result)
    store.append_decision(
        OperatorEvaluationDecision(
            result_id=result.result_id,
            plan_id=plan.plan_id,
            proposal_id=proposal.proposal_id,
            candidate_id=candidate.candidate_id,
            decision=OperatorEvaluationDecisionKind.ACCEPT_EVIDENCE,
            decision_criterion_ids=(criterion.criterion_id,),
            actor_id="operator",
            action_id="decision-1",
            reason_code="SUPPORTED",
            effective_at=NOW + timedelta(hours=3),
        )
    )
    tables = (
        "evaluation_candidate_specs",
        "proposal_evaluation_plans",
        "proposal_evaluation_sources",
        "proposal_evaluation_metrics",
        "proposal_acceptance_criteria",
        "proposal_evaluation_results",
        "proposal_metric_observations",
        "proposal_metric_evidence",
        "proposal_criterion_outcomes",
        "operator_evaluation_decisions",
    )
    with sqlite3.connect(path) as connection:
        for table in tables:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"DELETE FROM {table}")
