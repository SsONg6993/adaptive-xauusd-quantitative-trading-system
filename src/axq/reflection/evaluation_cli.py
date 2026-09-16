"""CLI handlers for preregistered proposal evaluation evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from axq.reflection.evaluation_contracts import (
    AcceptanceCriterion,
    EvaluationCandidateSpec,
    MetricObservation,
    OperatorEvaluationDecision,
    OperatorEvaluationDecisionKind,
    ValidationMetricSpec,
)
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.evaluations import build_evaluation_plan, build_evaluation_result
from axq.reflection.proposal_store import SQLiteImprovementProposalStore


def register_evaluation_commands(commands: Any) -> None:
    for name in (
        "register-evaluation-candidate",
        "build-evaluation-plan",
        "record-evaluation-result",
        "record-operator-evaluation-decision",
    ):
        command = commands.add_parser(name)
        command.add_argument("--store", type=Path, required=True)
        command.add_argument("--input", type=Path, required=True)
    for name, identifier in (
        ("show-evaluation-plan", "plan-id"),
        ("show-evaluation-result", "result-id"),
        ("show-operator-evaluation-history", "result-id"),
    ):
        command = commands.add_parser(name)
        command.add_argument("--store", type=Path, required=True)
        command.add_argument(f"--{identifier}", required=True)
    summary = commands.add_parser("evaluation-summary")
    summary.add_argument("--store", type=Path, required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _input(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("evaluation input must be a JSON object")
    return value


def _register_candidate(args: argparse.Namespace) -> int:
    candidate = EvaluationCandidateSpec.model_validate(_input(args.input))
    inserted = SQLiteProposalEvaluationStore(args.store).append_candidate(candidate)
    _emit({"candidate_id": candidate.candidate_id, "inserted": inserted})
    return 0


def _build_plan(args: argparse.Namespace) -> int:
    data = _input(args.input)
    proposal_store = SQLiteImprovementProposalStore(args.store)
    proposal = proposal_store.proposal(str(data.pop("proposal_id")))
    if proposal is None:
        raise ValueError("evaluation proposal is not persisted")
    store = SQLiteProposalEvaluationStore(args.store)
    candidate = store.candidate(str(data.pop("candidate_id")))
    if candidate is None:
        raise ValueError("evaluation candidate is not persisted")
    metrics = tuple(ValidationMetricSpec.model_validate(item) for item in data.pop("metrics"))
    criteria = tuple(AcceptanceCriterion.model_validate(item) for item in data.pop("criteria"))
    data["defined_at"] = datetime.fromisoformat(str(data["defined_at"]))
    plan = build_evaluation_plan(
        proposal=proposal,
        proposal_status=proposal_store.current_status(proposal.proposal_id),
        candidate=candidate,
        metrics=metrics,
        criteria=criteria,
        **data,
    )
    inserted = store.append_plan(plan)
    store.sync()
    _emit(
        {
            "criterion_ids": [item.criterion_id for item in plan.criteria],
            "inserted": inserted,
            "metric_ids": [item.metric_id for item in plan.metrics],
            "plan_id": plan.plan_id,
        }
    )
    return 0


def _record_result(args: argparse.Namespace) -> int:
    data = _input(args.input)
    store = SQLiteProposalEvaluationStore(args.store)
    plan = store.plan(str(data.pop("plan_id")))
    if plan is None:
        raise ValueError("evaluation plan is not persisted")
    observations = tuple(
        MetricObservation.model_validate(item) for item in data.pop("observations")
    )
    data["available_at"] = datetime.fromisoformat(str(data["available_at"]))
    result = build_evaluation_result(plan=plan, observations=observations, **data)
    inserted = store.append_result(result)
    store.sync()
    _emit(
        {
            "aggregate_outcome": result.aggregate_outcome.value,
            "inserted": inserted,
            "result_id": result.result_id,
        }
    )
    return 0


def _record_decision(args: argparse.Namespace) -> int:
    data = _input(args.input)
    store = SQLiteProposalEvaluationStore(args.store)
    result = store.result(str(data.pop("result_id")))
    if result is None:
        raise ValueError("evaluation result is not persisted")
    decision = OperatorEvaluationDecision(
        result_id=result.result_id,
        plan_id=result.plan_id,
        proposal_id=result.proposal_id,
        candidate_id=result.candidate_id,
        decision=OperatorEvaluationDecisionKind(data.pop("decision")),
        **{
            **data,
            "effective_at": datetime.fromisoformat(str(data["effective_at"])),
        },
    )
    inserted = store.append_decision(decision)
    store.sync()
    _emit(
        {
            "decision": decision.decision.value,
            "decision_id": decision.decision_id,
            "inserted": inserted,
        }
    )
    return 0


def _show_plan(args: argparse.Namespace) -> int:
    plan = SQLiteProposalEvaluationStore(args.store).plan(args.plan_id)
    if plan is None:
        raise SystemExit("evaluation plan not found")
    _emit(plan.model_dump(mode="json"))
    return 0


def _show_result(args: argparse.Namespace) -> int:
    result = SQLiteProposalEvaluationStore(args.store).result(args.result_id)
    if result is None:
        raise SystemExit("evaluation result not found")
    _emit(result.model_dump(mode="json"))
    return 0


def _show_history(args: argparse.Namespace) -> int:
    history = SQLiteProposalEvaluationStore(args.store).decision_history(args.result_id)
    _emit(
        {
            "current_decision": None if not history else history[-1].decision.value,
            "decisions": [item.model_dump(mode="json") for item in history],
            "result_id": args.result_id,
        }
    )
    return 0


def _summary(args: argparse.Namespace) -> int:
    store = SQLiteProposalEvaluationStore(args.store)
    candidates = store.candidates()
    plans = store.plans()
    results = store.results()
    decisions = store.decisions()
    proposal_store = SQLiteImprovementProposalStore(args.store)
    proposal_ids = tuple(sorted({item.proposal_id for item in candidates}))
    _emit(
        {
            "candidate_count": len(candidates),
            "operator_decision_count": len(decisions),
            "operator_decision_counts": dict(
                sorted(Counter(item.decision.value for item in decisions).items())
            ),
            "plan_count": len(plans),
            "plan_supersession_count": sum(item.supersedes_plan_id is not None for item in plans),
            "proposal_status_counts": dict(
                sorted(
                    Counter(
                        proposal_store.current_status(proposal_id).value
                        for proposal_id in proposal_ids
                    ).items()
                )
            ),
            "result_count": len(results),
            "result_outcome_counts": dict(
                sorted(Counter(item.aggregate_outcome.value for item in results).items())
            ),
            "result_supersession_count": sum(
                item.supersedes_result_id is not None for item in results
            ),
        }
    )
    return 0


def handle_evaluation_command(args: argparse.Namespace) -> int | None:
    handlers = {
        "register-evaluation-candidate": _register_candidate,
        "build-evaluation-plan": _build_plan,
        "record-evaluation-result": _record_result,
        "record-operator-evaluation-decision": _record_decision,
        "show-evaluation-plan": _show_plan,
        "show-evaluation-result": _show_result,
        "show-operator-evaluation-history": _show_history,
        "evaluation-summary": _summary,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
