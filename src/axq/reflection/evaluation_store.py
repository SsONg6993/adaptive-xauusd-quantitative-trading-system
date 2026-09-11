"""Append-only persistence for preregistered proposal evaluations."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from axq.database import Database
from axq.reflection.contracts import ReflectionModel
from axq.reflection.evaluation_contracts import (
    CriterionRole,
    EvaluationCandidateSpec,
    MetricScope,
    OperatorEvaluationDecision,
    ProposalEvaluationPlan,
    ProposalEvaluationResult,
)
from axq.reflection.evaluations import build_evaluation_result
from axq.reflection.proposal_contracts import ProposalStatus
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.versioning import canonical_hash

_MIGRATIONS = Path(__file__).parents[3] / "database" / "migrations"


def _payload(record: ReflectionModel) -> str:
    return json.dumps(
        record.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


class SQLiteProposalEvaluationStore:
    """Store immutable candidates, plans, results, and operator decisions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._database = Database(self.path)
        self._database.migrate(_MIGRATIONS)
        self._proposals = SQLiteImprovementProposalStore(self.path)

    def append_candidate(self, candidate: EvaluationCandidateSpec) -> bool:
        proposal = self._proposals.proposal(candidate.proposal_id)
        if proposal is None:
            raise ValueError("candidate proposal is not persisted")
        if (
            candidate.proposal_key != proposal.proposal_key
            or candidate.target_component is not proposal.target_component
        ):
            raise ValueError("candidate linkage does not match persisted proposal")
        if candidate.defined_at < proposal.available_at:
            raise ValueError("candidate cannot predate proposal availability")
        payload = _payload(candidate)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM evaluation_candidate_specs WHERE candidate_id = ?",
                (candidate.candidate_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("candidate ID already exists with different content")
            connection.execute(
                """
                INSERT INTO evaluation_candidate_specs(
                    candidate_id, proposal_id, proposal_key, target_component, defined_at,
                    schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.candidate_id,
                    candidate.proposal_id,
                    candidate.proposal_key,
                    candidate.target_component.value,
                    candidate.defined_at.isoformat(),
                    candidate.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def candidate(self, candidate_id: str) -> EvaluationCandidateSpec | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM evaluation_candidate_specs WHERE candidate_id = ?",
                (candidate_id,),
            ).fetchone()
        return (
            None
            if row is None
            else EvaluationCandidateSpec.model_validate_json(row["record_json"])
        )

    def candidates(self) -> tuple[EvaluationCandidateSpec, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM evaluation_candidate_specs ORDER BY candidate_sequence"
            ).fetchall()
        return tuple(
            EvaluationCandidateSpec.model_validate_json(row["record_json"]) for row in rows
        )

    @staticmethod
    def _plan_sources(plan: ProposalEvaluationPlan) -> dict[str, tuple[str, ...]]:
        return {
            "WEEKLY_PATTERN": plan.source_pattern_ids,
            "FINDING": plan.source_finding_ids,
            "DAILY_REFLECTION": plan.source_daily_reflection_ids,
            "EXPERIENCE": plan.source_experience_ids,
            "WEEKLY_REFLECTION": plan.source_weekly_reflection_ids,
        }

    def _validate_plan_linkage(self, plan: ProposalEvaluationPlan) -> None:
        proposal = self._proposals.proposal(plan.proposal_id)
        candidate = self.candidate(plan.candidate_id)
        if proposal is None:
            raise ValueError("plan proposal is not persisted")
        if candidate is None:
            raise ValueError("plan candidate is not persisted")
        if self._proposals.current_status(proposal.proposal_id) is not ProposalStatus.CANDIDATE:
            raise ValueError("evaluation plan registration requires CANDIDATE proposal status")
        if (
            plan.proposal_key != proposal.proposal_key
            or candidate.proposal_id != proposal.proposal_id
            or candidate.proposal_key != proposal.proposal_key
            or candidate.target_component is not proposal.target_component
        ):
            raise ValueError("plan proposal/candidate linkage is inconsistent")
        expected = {
            "WEEKLY_PATTERN": proposal.supporting_pattern_ids,
            "FINDING": proposal.supporting_finding_ids,
            "DAILY_REFLECTION": proposal.supporting_daily_reflection_ids,
            "EXPERIENCE": proposal.supporting_experience_ids,
            "WEEKLY_REFLECTION": proposal.supporting_weekly_reflection_ids,
        }
        if self._plan_sources(plan) != expected:
            raise ValueError("plan provenance must exactly equal canonical proposal sources")
        if plan.defined_at < proposal.available_at or plan.defined_at < candidate.defined_at:
            raise ValueError("plan cannot predate proposal or candidate availability")

    def append_plan(self, plan: ProposalEvaluationPlan) -> bool:
        payload = _payload(plan)
        with self._database.connect() as connection:
            existing = connection.execute(
                "SELECT record_json FROM proposal_evaluation_plans WHERE plan_id = ?",
                (plan.plan_id,),
            ).fetchone()
        if existing is not None:
            if str(existing["record_json"]) == payload:
                return False
            raise ValueError("plan ID already exists with different content")
        self._validate_plan_linkage(plan)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM proposal_evaluation_plans WHERE plan_id = ?",
                (plan.plan_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("plan ID already exists with different content")
            latest = connection.execute(
                """
                SELECT plan_id FROM proposal_evaluation_plans
                WHERE proposal_id = ? AND candidate_id = ?
                ORDER BY plan_sequence DESC LIMIT 1
                """,
                (plan.proposal_id, plan.candidate_id),
            ).fetchone()
            expected_parent = None if latest is None else str(latest["plan_id"])
            if plan.supersedes_plan_id != expected_parent:
                raise ValueError("plan must explicitly supersede latest plan")
            connection.execute(
                """
                INSERT INTO proposal_evaluation_plans(
                    plan_id, proposal_id, candidate_id, defined_at, supersedes_plan_id,
                    schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.plan_id,
                    plan.proposal_id,
                    plan.candidate_id,
                    plan.defined_at.isoformat(),
                    plan.supersedes_plan_id,
                    plan.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
            connection.executemany(
                """
                INSERT INTO proposal_evaluation_sources(plan_id, source_kind, source_semantic_id)
                VALUES (?, ?, ?)
                """,
                (
                    (plan.plan_id, kind, source_id)
                    for kind, source_ids in self._plan_sources(plan).items()
                    for source_id in source_ids
                ),
            )
            connection.executemany(
                """
                INSERT INTO proposal_evaluation_metrics(
                    plan_id, metric_id, metric_key, scope, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        plan.plan_id,
                        metric.metric_id,
                        metric.metric_key,
                        metric.scope.value,
                        canonical_hash(metric.model_dump(mode="json")),
                        _payload(metric),
                    )
                    for metric in plan.metrics
                ),
            )
            connection.executemany(
                """
                INSERT INTO proposal_acceptance_criteria(
                    plan_id, criterion_id, metric_key, role, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        plan.plan_id,
                        criterion.criterion_id,
                        criterion.metric_key,
                        criterion.role.value,
                        canonical_hash(criterion.model_dump(mode="json")),
                        _payload(criterion),
                    )
                    for criterion in plan.criteria
                ),
            )
        return True

    def plan(self, plan_id: str) -> ProposalEvaluationPlan | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM proposal_evaluation_plans WHERE plan_id = ?",
                (plan_id,),
            ).fetchone()
        return (
            None
            if row is None
            else ProposalEvaluationPlan.model_validate_json(row["record_json"])
        )

    def plans(self) -> tuple[ProposalEvaluationPlan, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM proposal_evaluation_plans ORDER BY plan_sequence"
            ).fetchall()
        return tuple(ProposalEvaluationPlan.model_validate_json(row["record_json"]) for row in rows)

    def append_result(self, result: ProposalEvaluationResult) -> bool:
        plan = self.plan(result.plan_id)
        if plan is None:
            raise ValueError("evaluation plan is not persisted")
        if result.proposal_id != plan.proposal_id or result.candidate_id != plan.candidate_id:
            raise ValueError("result linkage does not match persisted plan")
        rebuilt = build_evaluation_result(
            plan=plan,
            evaluation_run_key=result.evaluation_run_key,
            observations=result.observations,
            available_at=result.available_at,
            supersedes_result_id=result.supersedes_result_id,
        )
        if rebuilt != result:
            raise ValueError("result does not exactly apply persisted plan criteria")
        payload = _payload(result)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM proposal_evaluation_results WHERE result_id = ?",
                (result.result_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("result ID already exists with different content")
            latest = connection.execute(
                """
                SELECT result_id FROM proposal_evaluation_results
                WHERE plan_id = ? AND evaluation_run_key = ?
                ORDER BY result_sequence DESC LIMIT 1
                """,
                (result.plan_id, result.evaluation_run_key),
            ).fetchone()
            expected_parent = None if latest is None else str(latest["result_id"])
            if result.supersedes_result_id != expected_parent:
                raise ValueError("result must explicitly supersede latest result for its run")
            connection.execute(
                """
                INSERT INTO proposal_evaluation_results(
                    result_id, plan_id, proposal_id, candidate_id, evaluation_run_key,
                    available_at, aggregate_outcome, supersedes_result_id, schema_version,
                    payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.result_id,
                    result.plan_id,
                    result.proposal_id,
                    result.candidate_id,
                    result.evaluation_run_key,
                    result.available_at.isoformat(),
                    result.aggregate_outcome.value,
                    result.supersedes_result_id,
                    result.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
            for observation in result.observations:
                observation_payload = _payload(observation)
                connection.execute(
                    """
                    INSERT INTO proposal_metric_observations(
                        result_id, observation_id, metric_key, scope, status,
                        payload_hash, record_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.result_id,
                        observation.observation_id,
                        observation.metric_key,
                        observation.scope.value,
                        observation.status.value,
                        canonical_hash(json.loads(observation_payload)),
                        observation_payload,
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO proposal_metric_evidence(
                        result_id, observation_id, semantic_id, sha256
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        (
                            result.result_id,
                            observation.observation_id,
                            ref.semantic_id,
                            ref.sha256,
                        )
                        for ref in observation.evidence_refs
                    ),
                )
            connection.executemany(
                """
                INSERT INTO proposal_criterion_outcomes(
                    result_id, outcome_id, criterion_id, status, role,
                    payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        result.result_id,
                        outcome.outcome_id,
                        outcome.criterion_id,
                        outcome.status.value,
                        outcome.role.value,
                        canonical_hash(outcome.model_dump(mode="json")),
                        _payload(outcome),
                    )
                    for outcome in result.criterion_outcomes
                ),
            )
        return True

    def result(self, result_id: str) -> ProposalEvaluationResult | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM proposal_evaluation_results WHERE result_id = ?",
                (result_id,),
            ).fetchone()
        return (
            None
            if row is None
            else ProposalEvaluationResult.model_validate_json(row["record_json"])
        )

    def results(self) -> tuple[ProposalEvaluationResult, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM proposal_evaluation_results ORDER BY result_sequence"
            ).fetchall()
        return tuple(
            ProposalEvaluationResult.model_validate_json(row["record_json"]) for row in rows
        )

    def append_decision(self, decision: OperatorEvaluationDecision) -> bool:
        result = self.result(decision.result_id)
        plan = self.plan(decision.plan_id)
        if result is None or plan is None:
            raise ValueError("operator decision result and plan must be persisted")
        if (
            decision.plan_id != result.plan_id
            or decision.proposal_id != result.proposal_id
            or decision.candidate_id != result.candidate_id
        ):
            raise ValueError("operator decision linkage does not match result")
        allowed = {
            criterion.criterion_id
            for criterion in plan.criteria
            if criterion.role is CriterionRole.DECISION
            and next(
                metric for metric in plan.metrics if metric.metric_key == criterion.metric_key
            ).scope
            is not MetricScope.FINAL_OOS
        }
        if not set(decision.decision_criterion_ids).issubset(allowed):
            raise ValueError("operator decision references protected or undeclared criterion")
        if decision.effective_at < result.available_at:
            raise ValueError("operator decision cannot predate result availability")
        payload = _payload(decision)
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT record_json FROM operator_evaluation_decisions WHERE decision_id = ?",
                (decision.decision_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["record_json"]) == payload:
                    return False
                raise ValueError("decision ID already exists with different content")
            latest = connection.execute(
                """
                SELECT decision_id, effective_at FROM operator_evaluation_decisions
                WHERE result_id = ? ORDER BY decision_sequence DESC LIMIT 1
                """,
                (decision.result_id,),
            ).fetchone()
            expected_parent = None if latest is None else str(latest["decision_id"])
            if decision.previous_decision_id != expected_parent:
                raise ValueError("operator decision previous decision does not match latest")
            if latest is not None and decision.effective_at < datetime.fromisoformat(
                str(latest["effective_at"])
            ):
                raise ValueError("operator decision effective_at cannot move backward")
            connection.execute(
                """
                INSERT INTO operator_evaluation_decisions(
                    decision_id, result_id, plan_id, proposal_id, candidate_id, decision,
                    effective_at, previous_decision_id, schema_version, payload_hash, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.decision_id,
                    decision.result_id,
                    decision.plan_id,
                    decision.proposal_id,
                    decision.candidate_id,
                    decision.decision.value,
                    decision.effective_at.isoformat(),
                    decision.previous_decision_id,
                    decision.schema_version,
                    canonical_hash(json.loads(payload)),
                    payload,
                ),
            )
        return True

    def decision_history(self, result_id: str) -> tuple[OperatorEvaluationDecision, ...]:
        if self.result(result_id) is None:
            raise ValueError("evaluation result is not persisted")
        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT record_json FROM operator_evaluation_decisions
                WHERE result_id = ? ORDER BY decision_sequence
                """,
                (result_id,),
            ).fetchall()
        history = tuple(
            OperatorEvaluationDecision.model_validate_json(row["record_json"]) for row in rows
        )
        previous: str | None = None
        for decision in history:
            if decision.previous_decision_id != previous:
                raise ValueError("stored operator decision chain has invalid predecessor")
            previous = decision.decision_id
        return history

    def decisions(self) -> tuple[OperatorEvaluationDecision, ...]:
        with self._database.connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM operator_evaluation_decisions ORDER BY decision_sequence"
            ).fetchall()
        return tuple(
            OperatorEvaluationDecision.model_validate_json(row["record_json"]) for row in rows
        )

    def sync(self) -> None:
        with self._database.connect() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
