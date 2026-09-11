"""CLI handlers for deterministic paired baseline/candidate comparison."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.execution_contracts import CanonicalMetricSampleArtifact
from axq.reflection.paired_evaluation_contracts import PairedEvaluationRequest
from axq.reflection.paired_evaluation_service import execute_paired_evaluation
from axq.reflection.paired_evaluation_store import SQLitePairedEvaluationStore


def register_paired_evaluation_commands(commands: Any) -> None:
    run = commands.add_parser("run-paired-evaluation")
    run.add_argument("--store", type=Path, required=True)
    run.add_argument("--request", type=Path, required=True)
    run.add_argument("--baseline-development-input", type=Path)
    run.add_argument("--baseline-validation-input", type=Path)
    run.add_argument("--candidate-development-input", type=Path)
    run.add_argument("--candidate-validation-input", type=Path)
    run.add_argument("--result-output", type=Path, required=True)
    run.add_argument("--started-at", type=datetime.fromisoformat, required=True)
    run.add_argument("--completed-at", type=datetime.fromisoformat, required=True)

    show = commands.add_parser("show-paired-evaluation")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--request-id", required=True)

    summary = commands.add_parser("paired-evaluation-summary")
    summary.add_argument("--store", type=Path, required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _artifacts(args: argparse.Namespace, side: str) -> tuple[CanonicalMetricSampleArtifact, ...]:
    artifacts = []
    for scope in (MetricScope.DEVELOPMENT, MetricScope.VALIDATION):
        path = getattr(args, f"{side}_{scope.value.lower()}_input")
        if path is None:
            continue
        artifact = CanonicalMetricSampleArtifact.model_validate_json(path.read_bytes())
        if artifact.scope is not scope:
            raise ValueError(f"{side} {scope.value} artifact has the wrong scope")
        artifacts.append(artifact)
    return tuple(artifacts)


def _run(args: argparse.Namespace) -> int:
    request = PairedEvaluationRequest.model_validate_json(args.request.read_bytes())
    outcome = execute_paired_evaluation(
        args.store,
        request,
        _artifacts(args, "baseline"),
        _artifacts(args, "candidate"),
        started_at=args.started_at,
        completed_at=args.completed_at,
    )
    args.result_output.parent.mkdir(parents=True, exist_ok=True)
    args.result_output.write_bytes(outcome.result_bytes)
    _emit(
        {
            "audit_id": outcome.audit.audit_id,
            "criterion_status_counts": dict(
                sorted(
                    Counter(item.status.value for item in outcome.result.criterion_outcomes).items()
                )
            ),
            "request_id": outcome.request.request_id,
            "result_id": outcome.result.result_id,
            "reused": outcome.reused,
        }
    )
    return 0


def _show(args: argparse.Namespace) -> int:
    store = SQLitePairedEvaluationStore(args.store)
    request = store.request(args.request_id)
    if request is None:
        raise SystemExit("paired evaluation request not found")
    result = store.result(args.request_id)
    audit = store.audit(args.request_id)
    _emit(
        {
            "audit": None if audit is None else audit.model_dump(mode="json"),
            "request": request.model_dump(mode="json"),
            "result": None if result is None else result.model_dump(mode="json"),
        }
    )
    return 0


def _summary(args: argparse.Namespace) -> int:
    store = SQLitePairedEvaluationStore(args.store)
    requests = store.requests()
    results = store.results()
    audits = store.audits()
    comparisons = tuple(item for result in results for item in result.metric_comparisons)
    outcomes = tuple(item for result in results for item in result.criterion_outcomes)
    _emit(
        {
            "audit_count": len(audits),
            "completed_request_count": len({item.request_id for item in audits}),
            "criterion_status_counts": dict(
                sorted(Counter(item.status.value for item in outcomes).items())
            ),
            "final_oos_not_accessed_count": sum(
                item.reason_code == "FINAL_OOS_NOT_ACCESSED" for item in comparisons
            ),
            "metric_status_counts": dict(
                sorted(Counter(item.status.value for item in comparisons).items())
            ),
            "request_count": len(requests),
            "result_count": len(results),
        }
    )
    return 0


def handle_paired_evaluation_command(args: argparse.Namespace) -> int | None:
    handlers = {
        "run-paired-evaluation": _run,
        "show-paired-evaluation": _show,
        "paired-evaluation-summary": _summary,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
