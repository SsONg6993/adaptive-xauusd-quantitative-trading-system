"""Pure deterministic comparison of governed baseline and candidate evidence."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from axq.reflection.evaluation_contracts import (
    CriterionOutcomeStatus,
    MetricScope,
    ProposalEvaluationPlan,
    ProposalEvaluationResult,
)
from axq.reflection.execution_adapter import (
    CanonicalMetricSamplesAdapter,
    canonical_record_bytes,
    input_artifact_ref,
)
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationExecutionRequest,
)
from axq.reflection.paired_evaluation_contracts import (
    PairedArtifactRef,
    PairedCriterionOutcome,
    PairedCriterionStatus,
    PairedEvaluationRequest,
    PairedEvaluationResult,
    PairedMetricComparison,
    PairedMetricStatus,
    PairedParityCheck,
    PairedParityStatus,
    canonical_decimal,
)


@dataclass(frozen=True)
class PairedEvaluationOutput:
    result: PairedEvaluationResult
    result_bytes: bytes


def _parity(check_key: str, passed: bool, reason: str) -> PairedParityCheck:
    return PairedParityCheck(
        check_key=check_key,
        status=PairedParityStatus.PASS if passed else PairedParityStatus.FAIL,
        reason_code=None if passed else reason,
    )


def _artifact_matches(ref: PairedArtifactRef, artifact: CanonicalMetricSampleArtifact) -> bool:
    canonical = input_artifact_ref(artifact)
    return (
        ref.scope is artifact.scope
        and ref.semantic_id == canonical.semantic_id
        and ref.sha256 == canonical.sha256
    )


def _metric_keys(
    artifacts: dict[MetricScope, CanonicalMetricSampleArtifact],
) -> dict[MetricScope, set[str]]:
    return {
        scope: {series.metric_key for series in artifact.series}
        for scope, artifact in artifacts.items()
    }


def _decimal_aggregate(aggregation: str, values: tuple[float, ...]) -> Decimal:
    decimals = tuple(Decimal(str(item)) for item in values)
    if aggregation == "MEAN":
        return sum(decimals, Decimal(0)) / Decimal(len(decimals))
    if aggregation == "MIN":
        return min(decimals)
    if aggregation == "MAX":
        return max(decimals)
    if aggregation == "SUM":
        return sum(decimals, Decimal(0))
    if aggregation == "COUNT":
        return Decimal(len(decimals))
    raise ValueError(f"unsupported aggregation: {aggregation}")


def _ephemeral_result(
    request: PairedEvaluationRequest,
    plan: ProposalEvaluationPlan,
    artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    side: str,
) -> ProposalEvaluationResult:
    execution_request = EvaluationExecutionRequest(
        plan_id=plan.plan_id,
        candidate_id=plan.candidate_id,
        evaluation_run_key=f"{request.evaluation_run_key}:{side}",
        deterministic_seed=request.deterministic_seed,
        environment_identity=request.environment_identity,
        input_artifact_refs=tuple(input_artifact_ref(item) for item in artifacts),
        requested_at=request.requested_at,
    )
    return CanonicalMetricSamplesAdapter().execute(execution_request, plan, artifacts).result


def compare_paired_evidence(
    request: PairedEvaluationRequest,
    plan: ProposalEvaluationPlan,
    baseline_artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    candidate_artifacts: tuple[CanonicalMetricSampleArtifact, ...],
) -> PairedEvaluationOutput:
    """Compare supplied canonical artifacts without executing either evaluated system."""

    baseline_refs = {item.scope: item for item in request.baseline_artifact_refs}
    candidate_refs = {item.scope: item for item in request.candidate_artifact_refs}
    baseline_by_scope = {item.scope: item for item in baseline_artifacts}
    candidate_by_scope = {item.scope: item for item in candidate_artifacts}
    required_scopes = {
        item.scope for item in plan.metrics if item.scope is not MetricScope.FINAL_OOS
    }
    expected_keys = {
        scope: {item.metric_key for item in plan.metrics if item.scope is scope}
        for scope in required_scopes
    }
    checks = (
        _parity(
            "PLAN_LINKAGE",
            request.plan_id == plan.plan_id
            and request.proposal_id == plan.proposal_id
            and request.candidate_id == plan.candidate_id,
            "PLAN_LINKAGE_MISMATCH",
        ),
        _parity(
            "SCOPE_PARITY",
            len(baseline_by_scope) == len(baseline_artifacts)
            and len(candidate_by_scope) == len(candidate_artifacts)
            and set(baseline_refs)
            == set(candidate_refs)
            == set(baseline_by_scope)
            == set(candidate_by_scope)
            == required_scopes,
            "SCOPE_PARITY_MISMATCH",
        ),
        _parity(
            "MANIFEST_PARITY",
            set(baseline_refs) == set(candidate_refs)
            and all(
                baseline_refs[scope].manifest_ref == candidate_refs[scope].manifest_ref
                for scope in set(baseline_refs) & set(candidate_refs)
            ),
            "MANIFEST_PARITY_MISMATCH",
        ),
        _parity(
            "SEED_PARITY",
            request.deterministic_seed == plan.deterministic_seed
            and all(
                item.deterministic_seed == request.deterministic_seed
                for item in (*request.baseline_artifact_refs, *request.candidate_artifact_refs)
            ),
            "SEED_PARITY_MISMATCH",
        ),
        _parity(
            "ENVIRONMENT_PARITY",
            request.environment_identity == plan.environment_identity
            and all(
                item.environment_identity == request.environment_identity
                for item in (*request.baseline_artifact_refs, *request.candidate_artifact_refs)
            ),
            "ENVIRONMENT_PARITY_MISMATCH",
        ),
        _parity(
            "POLICY_LINKAGE",
            all(
                item.policy_identity == request.baseline_policy_set_id
                for item in request.baseline_artifact_refs
            )
            and all(
                item.policy_identity == request.candidate_config_id
                for item in request.candidate_artifact_refs
            ),
            "POLICY_LINKAGE_MISMATCH",
        ),
        _parity(
            "ARTIFACT_DIGEST_PARITY",
            set(baseline_refs) == set(baseline_by_scope)
            and set(candidate_refs) == set(candidate_by_scope)
            and all(
                _artifact_matches(baseline_refs[scope], baseline_by_scope[scope])
                for scope in set(baseline_refs) & set(baseline_by_scope)
            )
            and all(
                _artifact_matches(candidate_refs[scope], candidate_by_scope[scope])
                for scope in set(candidate_refs) & set(candidate_by_scope)
            ),
            "ARTIFACT_DIGEST_MISMATCH",
        ),
        _parity(
            "METRIC_DEFINITION_PARITY",
            set(baseline_by_scope) == set(candidate_by_scope) == required_scopes
            and _metric_keys(baseline_by_scope) == expected_keys
            and _metric_keys(candidate_by_scope) == expected_keys,
            "METRIC_DEFINITION_MISMATCH",
        ),
    )
    parity_passed = all(item.status is PairedParityStatus.PASS for item in checks)
    candidate_result = None
    if parity_passed:
        _ephemeral_result(request, plan, baseline_artifacts, "baseline")
        candidate_result = _ephemeral_result(request, plan, candidate_artifacts, "candidate")

    comparisons: list[PairedMetricComparison] = []
    for metric in plan.metrics:
        if metric.scope is MetricScope.FINAL_OOS:
            comparisons.append(
                PairedMetricComparison(
                    metric_id=metric.metric_id,
                    metric_key=metric.metric_key,
                    scope=metric.scope,
                    status=PairedMetricStatus.UNAVAILABLE,
                    baseline_value=None,
                    candidate_value=None,
                    delta=None,
                    baseline_sample_count=0,
                    candidate_sample_count=0,
                    reason_code="FINAL_OOS_NOT_ACCESSED",
                )
            )
            continue
        if not parity_passed:
            comparisons.append(
                PairedMetricComparison(
                    metric_id=metric.metric_id,
                    metric_key=metric.metric_key,
                    scope=metric.scope,
                    status=PairedMetricStatus.UNAVAILABLE,
                    baseline_value=None,
                    candidate_value=None,
                    delta=None,
                    baseline_sample_count=0,
                    candidate_sample_count=0,
                    reason_code="PAIR_PARITY_UNAVAILABLE",
                )
            )
            continue
        baseline_series = next(
            item
            for item in baseline_by_scope[metric.scope].series
            if item.metric_key == metric.metric_key
        )
        candidate_series = next(
            item
            for item in candidate_by_scope[metric.scope].series
            if item.metric_key == metric.metric_key
        )
        baseline_value = _decimal_aggregate(metric.aggregation, baseline_series.values)
        candidate_value = _decimal_aggregate(metric.aggregation, candidate_series.values)
        comparisons.append(
            PairedMetricComparison(
                metric_id=metric.metric_id,
                metric_key=metric.metric_key,
                scope=metric.scope,
                status=PairedMetricStatus.AVAILABLE,
                baseline_value=canonical_decimal(baseline_value),
                candidate_value=canonical_decimal(candidate_value),
                delta=canonical_decimal(candidate_value - baseline_value),
                baseline_sample_count=len(baseline_series.values),
                candidate_sample_count=len(candidate_series.values),
                baseline_artifact_ref=baseline_refs[metric.scope],
                candidate_artifact_ref=candidate_refs[metric.scope],
            )
        )

    by_metric = {item.metric_key: item for item in comparisons}
    candidate_outcomes = (
        {}
        if candidate_result is None
        else {item.criterion_id: item for item in candidate_result.criterion_outcomes}
    )
    outcomes: list[PairedCriterionOutcome] = []
    for criterion in plan.criteria:
        comparison = by_metric[criterion.metric_key]
        candidate_outcome = candidate_outcomes.get(criterion.criterion_id)
        if comparison.status is PairedMetricStatus.UNAVAILABLE or candidate_outcome is None:
            status = PairedCriterionStatus.UNAVAILABLE
            reason = comparison.reason_code or "PAIR_EVIDENCE_UNAVAILABLE"
        elif candidate_outcome.status is CriterionOutcomeStatus.PASSED:
            status = PairedCriterionStatus.PASS
            reason = None
        elif candidate_outcome.status is CriterionOutcomeStatus.FAILED:
            status = PairedCriterionStatus.FAIL
            reason = None
        else:
            status = PairedCriterionStatus.UNAVAILABLE
            reason = "CANDIDATE_CRITERION_INCONCLUSIVE"
        outcomes.append(
            PairedCriterionOutcome(
                criterion_id=criterion.criterion_id,
                metric_key=criterion.metric_key,
                role=criterion.role,
                status=status,
                comparison_id=comparison.comparison_id,
                reason_code=reason,
            )
        )

    available_times = tuple(
        item.available_at for item in (*baseline_artifacts, *candidate_artifacts)
    )
    result = PairedEvaluationResult(
        request_id=request.request_id,
        proposal_id=request.proposal_id,
        candidate_id=request.candidate_id,
        plan_id=request.plan_id,
        available_at=max((plan.defined_at, *available_times)),
        parity_checks=checks,
        metric_comparisons=tuple(comparisons),
        criterion_outcomes=tuple(outcomes),
    )
    payload = canonical_record_bytes(result)
    return PairedEvaluationOutput(result=result, result_bytes=payload)
