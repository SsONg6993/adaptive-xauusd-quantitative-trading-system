"""Closed deterministic adapter for canonical metric sample artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pydantic import BaseModel

from axq.reflection.evaluation_contracts import (
    MetricObservation,
    MetricObservationStatus,
    MetricScope,
    ProposalEvaluationPlan,
    ProposalEvaluationResult,
    SemanticArtifactRef,
    ValidationMetricSpec,
)
from axq.reflection.evaluations import build_evaluation_result
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationAdapterKind,
    EvaluationExecutionRequest,
    ExecutionInputArtifactRef,
)
from axq.versioning import canonical_hash

_AGGREGATIONS = frozenset({"MEAN", "MIN", "MAX", "SUM", "COUNT"})


def canonical_record_bytes(record: BaseModel) -> bytes:
    return json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def input_artifact_ref(artifact: CanonicalMetricSampleArtifact) -> ExecutionInputArtifactRef:
    return ExecutionInputArtifactRef(
        scope=artifact.scope,
        semantic_id=artifact.artifact_id,
        sha256=hashlib.sha256(canonical_record_bytes(artifact)).hexdigest(),
    )


@dataclass(frozen=True)
class EvaluationAdapterOutput:
    result: ProposalEvaluationResult
    result_bytes: bytes


def _aggregate(metric: ValidationMetricSpec, values: tuple[float, ...]) -> float:
    if metric.aggregation == "MEAN":
        return sum(values) / len(values)
    if metric.aggregation == "MIN":
        return min(values)
    if metric.aggregation == "MAX":
        return max(values)
    if metric.aggregation == "SUM":
        return sum(values)
    if metric.aggregation == "COUNT":
        return float(len(values))
    raise ValueError(f"unsupported aggregation: {metric.aggregation}")


class CanonicalMetricSamplesAdapter:
    """Aggregate exact preregistered metric series without executing candidate code."""

    def execute(
        self,
        request: EvaluationExecutionRequest,
        plan: ProposalEvaluationPlan,
        artifacts: tuple[CanonicalMetricSampleArtifact, ...],
    ) -> EvaluationAdapterOutput:
        if request.adapter_kind is not EvaluationAdapterKind.CANONICAL_METRIC_SAMPLES_V1:
            raise ValueError("execution request adapter kind is unsupported")
        if request.plan_id != plan.plan_id:
            raise ValueError("request plan linkage does not match plan")
        if request.candidate_id != plan.candidate_id:
            raise ValueError("request candidate linkage does not match plan")
        if request.deterministic_seed != plan.deterministic_seed:
            raise ValueError("request seed does not match plan")
        if request.environment_identity != plan.environment_identity:
            raise ValueError("request environment does not match plan")
        if any(metric.aggregation not in _AGGREGATIONS for metric in plan.metrics):
            unsupported = next(
                metric.aggregation
                for metric in plan.metrics
                if metric.aggregation not in _AGGREGATIONS
            )
            raise ValueError(f"unsupported aggregation: {unsupported}")

        metrics_by_scope = {
            scope: tuple(metric for metric in plan.metrics if metric.scope is scope)
            for scope in (MetricScope.DEVELOPMENT, MetricScope.VALIDATION)
        }
        required_scopes = {scope for scope, metrics in metrics_by_scope.items() if metrics}
        artifact_by_scope = {artifact.scope: artifact for artifact in artifacts}
        if len(artifact_by_scope) != len(artifacts) or set(artifact_by_scope) != required_scopes:
            raise ValueError("execution artifact input scopes do not match plan")
        request_refs = {item.scope: item for item in request.input_artifact_refs}
        if set(request_refs) != required_scopes:
            raise ValueError("execution request input scopes do not match plan")
        for scope, artifact in artifact_by_scope.items():
            if request_refs[scope] != input_artifact_ref(artifact):
                raise ValueError("execution input artifact digest/linkage mismatch")

        available_at = max(
            (artifact.available_at for artifact in artifacts),
            default=plan.defined_at,
        )
        observations: list[MetricObservation] = []
        for scope, metrics in metrics_by_scope.items():
            if not metrics:
                continue
            artifact = artifact_by_scope[scope]
            samples = {series.metric_key: series.values for series in artifact.series}
            expected_keys = {metric.metric_key for metric in metrics}
            if set(samples) != expected_keys:
                raise ValueError("artifact metric series must exactly match preregistered metrics")
            evidence = input_artifact_ref(artifact)
            for metric in metrics:
                values = tuple(float(item) for item in samples[metric.metric_key])
                observations.append(
                    MetricObservation(
                        metric_key=metric.metric_key,
                        scope=scope,
                        status=MetricObservationStatus.AVAILABLE,
                        value=_aggregate(metric, values),
                        sample_count=len(values),
                        evidence_refs=(
                            SemanticArtifactRef(
                                semantic_id=evidence.semantic_id,
                                sha256=evidence.sha256,
                            ),
                        ),
                        available_at=artifact.available_at,
                    )
                )
        for metric in plan.metrics:
            if metric.scope is not MetricScope.FINAL_OOS:
                continue
            marker = {
                "reason_code": "FINAL_OOS_NOT_ACCESSED",
                "request_id": request.request_id,
                "metric_id": metric.metric_id,
            }
            observations.append(
                MetricObservation(
                    metric_key=metric.metric_key,
                    scope=MetricScope.FINAL_OOS,
                    status=MetricObservationStatus.UNAVAILABLE,
                    value=None,
                    sample_count=0,
                    evidence_refs=(
                        SemanticArtifactRef(
                            semantic_id=(
                                f"final-oos-withheld-{canonical_hash(marker)[:20]}"
                            ),
                            sha256=canonical_hash(marker),
                        ),
                    ),
                    available_at=available_at,
                    reason_code="FINAL_OOS_NOT_ACCESSED",
                )
            )
        result = build_evaluation_result(
            plan=plan,
            evaluation_run_key=request.evaluation_run_key,
            observations=tuple(observations),
            available_at=available_at,
        )
        return EvaluationAdapterOutput(result=result, result_bytes=canonical_record_bytes(result))
