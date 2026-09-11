from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from axq.reflection.contracts import FindingCategory, SampleGuardStatus
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

NOW = datetime(2026, 9, 11, 12, 0, tzinfo=UTC)


def persist_controlled_plan(path: Path, *, include_development: bool = False):
    policy = ImprovementProposalPolicy()
    proposal = ImprovementProposal(
        policy_id=policy.policy_id,
        pattern_key="controlled-pattern-key",
        target_component=ProposalTargetComponent.MASTER_FUSION,
        category=FindingCategory.DIRECTION_OUTCOME,
        pattern_type=PatternType.FAILURE,
        signal_class=PatternSignalClass.ADVERSE,
        reason_code="CONTROLLED_FIXTURE",
        scope="direction",
        scope_value="BUY",
        rationale="Controlled recurring evidence.",
        proposed_change="Evaluate a frozen controlled candidate.",
        expected_benefit="Exercise evaluation governance.",
        risks=("Fixture only",),
        validation_plan=("Use preregistered canonical samples.",),
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
    proposal_store = SQLiteImprovementProposalStore(path)
    proposal_store.append_policy(policy)
    proposal_store.append(proposal)
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
        proposal_store.append_transition(transition)
        previous = transition.transition_id
    candidate = EvaluationCandidateSpec(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        target_component=proposal.target_component,
        candidate_kind=CandidateKind.RULE,
        description="Controlled frozen candidate.",
        implementation_version="v1",
        source_identity="git-controlled",
        config_identity="config-controlled",
        manifest_identity="manifest-controlled",
        artifact_refs=(SemanticArtifactRef(semantic_id="candidate", sha256="a" * 64),),
        defined_at=NOW,
    )
    optional_development = (
        (
            ValidationMetricSpec(
                metric_key="development_expectancy",
                name="Development expectancy",
                unit="R",
                aggregation="MEAN",
                scope=MetricScope.DEVELOPMENT,
                direction=MetricDirection.DESCRIPTIVE,
            ),
        )
        if include_development
        else ()
    )
    metrics = (
        *optional_development,
        ValidationMetricSpec(
            metric_key="validation_expectancy",
            name="Validation expectancy",
            unit="R",
            aggregation="MEAN",
            scope=MetricScope.VALIDATION,
            direction=MetricDirection.HIGHER_IS_BETTER,
        ),
        ValidationMetricSpec(
            metric_key="final_oos_expectancy",
            name="Final OOS expectancy",
            unit="R",
            aggregation="MEAN",
            scope=MetricScope.FINAL_OOS,
            direction=MetricDirection.HIGHER_IS_BETTER,
        ),
    )
    criteria = (
        AcceptanceCriterion(
            metric_key="validation_expectancy",
            comparator=CriterionComparator.GE,
            lower_threshold=0.0,
            minimum_samples=2,
            role=CriterionRole.DECISION,
        ),
        AcceptanceCriterion(
            metric_key="final_oos_expectancy",
            comparator=CriterionComparator.GE,
            lower_threshold=0.0,
            minimum_samples=2,
            role=CriterionRole.REPORTING_ONLY,
        ),
    )
    evaluation_store = SQLiteProposalEvaluationStore(path)
    evaluation_store.append_candidate(candidate)
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
        action_id="controlled-plan",
    )
    evaluation_store.append_plan(plan)
    return proposal, candidate, plan
