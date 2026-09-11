"""Immutable contracts for preregistered proposal evaluation evidence."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from axq.reflection.contracts import ReflectionModel
from axq.reflection.proposal_contracts import ProposalTargetComponent
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class CandidateKind(StrEnum):
    CONFIGURATION = "CONFIGURATION"
    RULE = "RULE"
    FEATURE = "FEATURE"
    MODEL = "MODEL"
    PROCESS = "PROCESS"


class MetricScope(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATION = "VALIDATION"
    FINAL_OOS = "FINAL_OOS"


class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    DESCRIPTIVE = "DESCRIPTIVE"


class CriterionComparator(StrEnum):
    GE = "GE"
    LE = "LE"
    BETWEEN = "BETWEEN"


class CriterionRole(StrEnum):
    DECISION = "DECISION"
    REPORTING_ONLY = "REPORTING_ONLY"


class FinalOOSPolicy(StrEnum):
    REPORTING_ONLY = "REPORTING_ONLY"


class MetricObservationStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class CriterionOutcomeStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvaluationAggregateOutcome(StrEnum):
    SUPPORTED = "SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class OperatorEvaluationDecisionKind(StrEnum):
    ACCEPT_EVIDENCE = "ACCEPT_EVIDENCE"
    REJECT_EVIDENCE = "REJECT_EVIDENCE"
    DEFER = "DEFER"


class SemanticArtifactRef(ReflectionModel):
    semantic_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class EvaluationCandidateSpec(ReflectionModel):
    candidate_id: str = ""
    proposal_id: str = Field(min_length=1)
    proposal_key: str = Field(min_length=1)
    target_component: ProposalTargetComponent
    candidate_kind: CandidateKind
    description: str = Field(min_length=1)
    implementation_version: str = Field(min_length=1)
    source_identity: str = Field(min_length=1)
    config_identity: str = Field(min_length=1)
    manifest_identity: str = Field(min_length=1)
    artifact_refs: tuple[SemanticArtifactRef, ...] = Field(min_length=1)
    defined_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> EvaluationCandidateSpec:
        artifacts = tuple(sorted(set(self.artifact_refs), key=lambda item: item.semantic_id))
        if len({item.semantic_id for item in artifacts}) != len(artifacts):
            raise ValueError("candidate artifact semantic IDs must be unique")
        object.__setattr__(self, "artifact_refs", artifacts)
        identity = self.model_dump(mode="json", exclude={"candidate_id"})
        expected = f"evaluation-candidate-{canonical_hash(identity)[:20]}"
        if self.candidate_id and self.candidate_id != expected:
            raise ValueError("candidate_id does not match candidate content")
        object.__setattr__(self, "candidate_id", expected)
        return self

class ValidationMetricSpec(ReflectionModel):
    metric_id: str = ""
    metric_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    aggregation: str = Field(min_length=1)
    scope: MetricScope
    direction: MetricDirection

    @model_validator(mode="after")
    def bind_identity(self) -> ValidationMetricSpec:
        identity = self.model_dump(mode="json", exclude={"metric_id"})
        expected = f"validation-metric-{canonical_hash(identity)[:20]}"
        if self.metric_id and self.metric_id != expected:
            raise ValueError("metric_id does not match metric content")
        object.__setattr__(self, "metric_id", expected)
        return self


class AcceptanceCriterion(ReflectionModel):
    criterion_id: str = ""
    metric_key: str = Field(min_length=1)
    comparator: CriterionComparator
    lower_threshold: FiniteFloat | None = None
    upper_threshold: FiniteFloat | None = None
    minimum_samples: int = Field(ge=1)
    role: CriterionRole

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> AcceptanceCriterion:
        if self.comparator in {CriterionComparator.GE, CriterionComparator.LE}:
            if self.lower_threshold is None or self.upper_threshold is not None:
                raise ValueError("GE/LE criterion requires only lower_threshold")
        elif (
            self.lower_threshold is None
            or self.upper_threshold is None
            or self.lower_threshold > self.upper_threshold
        ):
            raise ValueError("BETWEEN criterion requires ordered lower and upper thresholds")
        identity = self.model_dump(mode="json", exclude={"criterion_id"})
        expected = f"acceptance-criterion-{canonical_hash(identity)[:20]}"
        if self.criterion_id and self.criterion_id != expected:
            raise ValueError("criterion_id does not match criterion content")
        object.__setattr__(self, "criterion_id", expected)
        return self


class ProposalEvaluationPlan(ReflectionModel):
    plan_id: str = ""
    proposal_id: str = Field(min_length=1)
    proposal_key: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    source_pattern_ids: tuple[str, ...] = Field(min_length=1)
    source_finding_ids: tuple[str, ...] = Field(min_length=1)
    source_daily_reflection_ids: tuple[str, ...] = Field(min_length=1)
    source_experience_ids: tuple[str, ...] = Field(min_length=1)
    source_weekly_reflection_ids: tuple[str, ...] = Field(min_length=1)
    deterministic_seed: int = Field(ge=0)
    environment_identity: str = Field(min_length=1)
    metrics: tuple[ValidationMetricSpec, ...] = Field(min_length=1)
    criteria: tuple[AcceptanceCriterion, ...] = Field(min_length=1)
    minimum_total_samples: int = Field(ge=1)
    missing_data_policy: Literal["INCONCLUSIVE"] = "INCONCLUSIVE"
    final_oos_policy: Literal[FinalOOSPolicy.REPORTING_ONLY] = FinalOOSPolicy.REPORTING_ONLY
    defined_at: UTCDateTime
    actor_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    supersedes_plan_id: str | None = None

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> ProposalEvaluationPlan:
        for field_name in (
            "source_pattern_ids",
            "source_finding_ids",
            "source_daily_reflection_ids",
            "source_experience_ids",
            "source_weekly_reflection_ids",
        ):
            object.__setattr__(self, field_name, tuple(sorted(set(getattr(self, field_name)))))
        metrics = tuple(sorted(self.metrics, key=lambda item: item.metric_key))
        criteria = tuple(sorted(self.criteria, key=lambda item: item.criterion_id))
        if len({item.metric_key for item in metrics}) != len(metrics):
            raise ValueError("plan metric keys must be unique")
        if len({item.criterion_id for item in criteria}) != len(criteria):
            raise ValueError("plan criterion IDs must be unique")
        metric_by_key = {item.metric_key: item for item in metrics}
        if any(item.metric_key not in metric_by_key for item in criteria):
            raise ValueError("criterion references undeclared metric")
        if any(
            metric_by_key[item.metric_key].scope is MetricScope.FINAL_OOS
            and item.role is not CriterionRole.REPORTING_ONLY
            for item in criteria
        ):
            raise ValueError("Final OOS criteria must be reporting-only")
        if not any(
            item.role is CriterionRole.DECISION
            and metric_by_key[item.metric_key].scope is not MetricScope.FINAL_OOS
            for item in criteria
        ):
            raise ValueError("plan requires a non-Final-OOS decision criterion")
        object.__setattr__(self, "metrics", metrics)
        object.__setattr__(self, "criteria", criteria)
        identity = self.model_dump(mode="json", exclude={"plan_id"})
        expected = f"proposal-evaluation-plan-{canonical_hash(identity)[:20]}"
        if self.plan_id and self.plan_id != expected:
            raise ValueError("plan_id does not match plan content")
        object.__setattr__(self, "plan_id", expected)
        return self


class MetricObservation(ReflectionModel):
    observation_id: str = ""
    metric_key: str = Field(min_length=1)
    scope: MetricScope
    status: MetricObservationStatus
    value: FiniteFloat | None
    sample_count: int = Field(ge=0)
    evidence_refs: tuple[SemanticArtifactRef, ...] = Field(min_length=1)
    available_at: UTCDateTime

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> MetricObservation:
        if self.status is MetricObservationStatus.AVAILABLE and self.value is None:
            raise ValueError("available metric observation requires a value")
        if self.status is MetricObservationStatus.UNAVAILABLE and self.value is not None:
            raise ValueError("unavailable metric observation cannot have a value")
        refs = tuple(sorted(set(self.evidence_refs), key=lambda item: item.semantic_id))
        if len({item.semantic_id for item in refs}) != len(refs):
            raise ValueError("observation evidence semantic IDs must be unique")
        object.__setattr__(self, "evidence_refs", refs)
        identity = self.model_dump(mode="json", exclude={"observation_id"})
        expected = f"metric-observation-{canonical_hash(identity)[:20]}"
        if self.observation_id and self.observation_id != expected:
            raise ValueError("observation_id does not match observation content")
        object.__setattr__(self, "observation_id", expected)
        return self


class CriterionOutcome(ReflectionModel):
    outcome_id: str = ""
    criterion_id: str = Field(min_length=1)
    metric_key: str = Field(min_length=1)
    role: CriterionRole
    status: CriterionOutcomeStatus
    observation_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def bind_identity(self) -> CriterionOutcome:
        identity = self.model_dump(mode="json", exclude={"outcome_id"})
        expected = f"criterion-outcome-{canonical_hash(identity)[:20]}"
        if self.outcome_id and self.outcome_id != expected:
            raise ValueError("outcome_id does not match outcome content")
        object.__setattr__(self, "outcome_id", expected)
        return self


class ProposalEvaluationResult(ReflectionModel):
    result_id: str = ""
    plan_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    evaluation_run_key: str = Field(min_length=1)
    available_at: UTCDateTime
    observations: tuple[MetricObservation, ...] = Field(min_length=1)
    criterion_outcomes: tuple[CriterionOutcome, ...] = Field(min_length=1)
    aggregate_outcome: EvaluationAggregateOutcome
    supersedes_result_id: str | None = None

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> ProposalEvaluationResult:
        observations = tuple(sorted(self.observations, key=lambda item: item.metric_key))
        outcomes = tuple(sorted(self.criterion_outcomes, key=lambda item: item.criterion_id))
        if len({item.metric_key for item in observations}) != len(observations):
            raise ValueError("result observation metric keys must be unique")
        if len({item.criterion_id for item in outcomes}) != len(outcomes):
            raise ValueError("result criterion IDs must be unique")
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "criterion_outcomes", outcomes)
        identity = self.model_dump(mode="json", exclude={"result_id"})
        expected = f"proposal-evaluation-result-{canonical_hash(identity)[:20]}"
        if self.result_id and self.result_id != expected:
            raise ValueError("result_id does not match result content")
        object.__setattr__(self, "result_id", expected)
        return self


class OperatorEvaluationDecision(ReflectionModel):
    decision_id: str = ""
    result_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    decision: OperatorEvaluationDecisionKind
    decision_criterion_ids: tuple[str, ...] = ()
    actor_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    effective_at: UTCDateTime
    previous_decision_id: str | None = None

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> OperatorEvaluationDecision:
        criterion_ids = tuple(sorted(set(self.decision_criterion_ids)))
        if (
            self.decision is not OperatorEvaluationDecisionKind.DEFER
            and not criterion_ids
        ):
            raise ValueError("accept/reject decision requires a decision criterion")
        object.__setattr__(self, "decision_criterion_ids", criterion_ids)
        identity = self.model_dump(mode="json", exclude={"decision_id"})
        expected = f"operator-evaluation-decision-{canonical_hash(identity)[:20]}"
        if self.decision_id and self.decision_id != expected:
            raise ValueError("decision_id does not match decision content")
        object.__setattr__(self, "decision_id", expected)
        return self
