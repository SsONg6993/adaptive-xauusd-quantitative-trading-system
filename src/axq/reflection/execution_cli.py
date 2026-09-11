"""CLI handlers for deterministic preregistered evaluation execution."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.evaluation_store import SQLiteProposalEvaluationStore
from axq.reflection.execution_contracts import (
    CanonicalMetricSampleArtifact,
    EvaluationExecutionRequest,
)
from axq.reflection.execution_service import execute_evaluation_request
from axq.reflection.execution_store import SQLiteEvaluationExecutionStore


def register_execution_commands(commands: Any) -> None:
    run = commands.add_parser("run-evaluation-execution")
    run.add_argument("--store", type=Path, required=True)
    run.add_argument("--request", type=Path, required=True)
    run.add_argument("--development-input", type=Path)
    run.add_argument("--validation-input", type=Path)
    run.add_argument("--result-output", type=Path, required=True)
    run.add_argument("--started-at", type=datetime.fromisoformat, required=True)
    run.add_argument("--completed-at", type=datetime.fromisoformat, required=True)

    show = commands.add_parser("show-evaluation-execution")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--request-id", required=True)

    summary = commands.add_parser("evaluation-execution-summary")
    summary.add_argument("--store", type=Path, required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _artifact(path: Path, scope: MetricScope) -> CanonicalMetricSampleArtifact:
    artifact = CanonicalMetricSampleArtifact.model_validate_json(path.read_bytes())
    if artifact.scope is not scope:
        raise ValueError(f"{scope.value} input artifact has the wrong scope")
    return artifact


def _run(args: argparse.Namespace) -> int:
    request = EvaluationExecutionRequest.model_validate_json(args.request.read_bytes())
    artifacts: list[CanonicalMetricSampleArtifact] = []
    if args.development_input is not None:
        artifacts.append(_artifact(args.development_input, MetricScope.DEVELOPMENT))
    if args.validation_input is not None:
        artifacts.append(_artifact(args.validation_input, MetricScope.VALIDATION))
    outcome = execute_evaluation_request(
        args.store,
        request,
        tuple(artifacts),
        started_at=args.started_at,
        completed_at=args.completed_at,
    )
    args.result_output.parent.mkdir(parents=True, exist_ok=True)
    args.result_output.write_bytes(outcome.result_bytes)
    _emit(
        {
            "audit_id": outcome.audit.audit_id,
            "request_id": outcome.request.request_id,
            "result_id": outcome.result.result_id,
            "result_output": str(args.result_output),
            "reused": outcome.reused,
        }
    )
    return 0


def _show(args: argparse.Namespace) -> int:
    execution_store = SQLiteEvaluationExecutionStore(args.store)
    evaluation_store = SQLiteProposalEvaluationStore(args.store)
    request = execution_store.request(args.request_id)
    audit = execution_store.audit(args.request_id)
    if request is None:
        raise SystemExit("evaluation execution request not found")
    result = None if audit is None else evaluation_store.result(audit.result_id)
    _emit(
        {
            "audit": None if audit is None else audit.model_dump(mode="json"),
            "request": request.model_dump(mode="json"),
            "result": None if result is None else result.model_dump(mode="json"),
        }
    )
    return 0


def _summary(args: argparse.Namespace) -> int:
    execution_store = SQLiteEvaluationExecutionStore(args.store)
    evaluation_store = SQLiteProposalEvaluationStore(args.store)
    requests = execution_store.requests()
    audits = execution_store.audits()
    results = tuple(
        result
        for audit in audits
        if (result := evaluation_store.result(audit.result_id)) is not None
    )
    observations = tuple(item for result in results for item in result.observations)
    _emit(
        {
            "audit_count": len(audits),
            "completed_request_count": len({item.request_id for item in audits}),
            "final_oos_not_accessed_count": sum(
                item.scope is MetricScope.FINAL_OOS
                and item.reason_code == "FINAL_OOS_NOT_ACCESSED"
                for item in observations
            ),
            "metric_observation_count": len(observations),
            "request_count": len(requests),
            "result_count": len(results),
            "status_counts": dict(sorted(Counter(item.status.value for item in audits).items())),
        }
    )
    return 0


def handle_execution_command(args: argparse.Namespace) -> int | None:
    handlers = {
        "run-evaluation-execution": _run,
        "show-evaluation-execution": _show,
        "evaluation-execution-summary": _summary,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
