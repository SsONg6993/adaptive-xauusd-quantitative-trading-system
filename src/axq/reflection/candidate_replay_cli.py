"""CLI handlers for governed deterministic candidate replay evaluation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from axq.reflection.candidate_replay_contracts import (
    CandidateReplayRequest,
    ControlledReplayFixtureArtifact,
)
from axq.reflection.candidate_replay_service import execute_candidate_replay
from axq.reflection.candidate_replay_store import SQLiteCandidateReplayStore
from axq.reflection.evaluation_contracts import MetricScope


def register_candidate_replay_commands(commands: Any) -> None:
    run = commands.add_parser("run-candidate-replay")
    run.add_argument("--store", type=Path, required=True)
    run.add_argument("--request", type=Path, required=True)
    run.add_argument("--development-input", type=Path)
    run.add_argument("--validation-input", type=Path)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--started-at", type=datetime.fromisoformat, required=True)
    run.add_argument("--completed-at", type=datetime.fromisoformat, required=True)

    show = commands.add_parser("show-candidate-replay")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--request-id", required=True)

    summary = commands.add_parser("candidate-replay-summary")
    summary.add_argument("--store", type=Path, required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _fixture(path: Path, scope: MetricScope) -> ControlledReplayFixtureArtifact:
    value = ControlledReplayFixtureArtifact.model_validate_json(path.read_bytes())
    if value.scope is not scope:
        raise ValueError(f"{scope.value} controlled replay fixture has the wrong scope")
    return value


def _run(args: argparse.Namespace) -> int:
    request = CandidateReplayRequest.model_validate_json(args.request.read_bytes())
    fixtures: list[ControlledReplayFixtureArtifact] = []
    if args.development_input is not None:
        fixtures.append(_fixture(args.development_input, MetricScope.DEVELOPMENT))
    if args.validation_input is not None:
        fixtures.append(_fixture(args.validation_input, MetricScope.VALIDATION))
    outcome = execute_candidate_replay(
        args.store,
        request,
        tuple(fixtures),
        started_at=args.started_at,
        completed_at=args.completed_at,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for artifact, payload in zip(outcome.artifacts, outcome.artifact_bytes, strict=True):
        path = args.output_dir / f"{artifact.scope.value.lower()}-metric-samples.json"
        path.write_bytes(payload)
        outputs[artifact.scope.value] = str(path)
    _emit(
        {
            "artifact_count": len(outcome.artifacts),
            "artifact_ids": [item.artifact_id for item in outcome.artifacts],
            "audit_id": outcome.audit.audit_id,
            "outputs": dict(sorted(outputs.items())),
            "request_id": outcome.request.request_id,
            "reused": outcome.reused,
        }
    )
    return 0


def _show(args: argparse.Namespace) -> int:
    store = SQLiteCandidateReplayStore(args.store)
    request = store.request(args.request_id)
    if request is None:
        raise SystemExit("candidate replay request not found")
    audit = store.audit(args.request_id)
    artifacts = store.artifacts(args.request_id)
    _emit(
        {
            "artifacts": [item.model_dump(mode="json") for item in artifacts],
            "audit": None if audit is None else audit.model_dump(mode="json"),
            "request": request.model_dump(mode="json"),
        }
    )
    return 0


def _summary(args: argparse.Namespace) -> int:
    store = SQLiteCandidateReplayStore(args.store)
    requests = store.requests()
    audits = store.audits()
    artifacts_by_id = {
        artifact.artifact_id: artifact
        for request in requests
        for artifact in store.artifacts(request.request_id)
    }
    artifacts = tuple(artifacts_by_id.values())
    _emit(
        {
            "artifact_count": len(artifacts),
            "artifact_scope_counts": dict(
                sorted(Counter(item.scope.value for item in artifacts).items())
            ),
            "audit_count": len(audits),
            "completed_request_count": len({item.request_id for item in audits}),
            "engine_counts": dict(
                sorted(Counter(item.engine_kind.value for item in requests).items())
            ),
            "request_count": len(requests),
            "status_counts": dict(sorted(Counter(item.status.value for item in audits).items())),
        }
    )
    return 0


def handle_candidate_replay_command(args: argparse.Namespace) -> int | None:
    handlers = {
        "run-candidate-replay": _run,
        "show-candidate-replay": _show,
        "candidate-replay-summary": _summary,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
