"""CLI handlers for governed shared-kernel candidate evaluation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.shared_kernel_candidate_contracts import (
    FrozenSharedKernelCandidateConfig,
    SharedKernelCandidateRequest,
    SharedKernelReplayDataManifest,
)
from axq.reflection.shared_kernel_candidate_service import execute_shared_kernel_candidate
from axq.reflection.shared_kernel_candidate_store import SQLiteSharedKernelCandidateStore


def register_shared_kernel_candidate_commands(commands: Any) -> None:
    run = commands.add_parser("run-shared-kernel-candidate")
    run.add_argument("--store", type=Path, required=True)
    run.add_argument("--request", type=Path, required=True)
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--development-manifest", type=Path)
    run.add_argument("--development-data-dir", type=Path)
    run.add_argument("--validation-manifest", type=Path)
    run.add_argument("--validation-data-dir", type=Path)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--started-at", type=datetime.fromisoformat, required=True)
    run.add_argument("--completed-at", type=datetime.fromisoformat, required=True)

    show = commands.add_parser("show-shared-kernel-candidate")
    show.add_argument("--store", type=Path, required=True)
    show.add_argument("--request-id", required=True)

    summary = commands.add_parser("shared-kernel-candidate-summary")
    summary.add_argument("--store", type=Path, required=True)


def _emit(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _optional_scope(
    manifest_path: Path | None,
    data_dir: Path | None,
    scope: MetricScope,
) -> tuple[SharedKernelReplayDataManifest | None, Path | None]:
    if (manifest_path is None) != (data_dir is None):
        raise ValueError(f"{scope.value} manifest and data directory must be supplied together")
    if manifest_path is None:
        return None, None
    manifest = SharedKernelReplayDataManifest.model_validate_json(manifest_path.read_bytes())
    if manifest.scope is not scope:
        raise ValueError(f"{scope.value} shared-kernel manifest has the wrong scope")
    return manifest, data_dir


def _run(args: argparse.Namespace) -> int:
    request = SharedKernelCandidateRequest.model_validate_json(args.request.read_bytes())
    config = FrozenSharedKernelCandidateConfig.model_validate_json(args.config.read_bytes())
    manifests = []
    directories: dict[MetricScope, Path] = {}
    for manifest_path, data_dir, scope in (
        (args.development_manifest, args.development_data_dir, MetricScope.DEVELOPMENT),
        (args.validation_manifest, args.validation_data_dir, MetricScope.VALIDATION),
    ):
        manifest, directory = _optional_scope(manifest_path, data_dir, scope)
        if manifest is not None and directory is not None:
            manifests.append(manifest)
            directories[scope] = directory
    outcome = execute_shared_kernel_candidate(
        args.store,
        request,
        config,
        tuple(manifests),
        directories,
        args.output_dir / "kernel-runs",
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
    store = SQLiteSharedKernelCandidateStore(args.store)
    request = store.request(args.request_id)
    if request is None:
        raise SystemExit("shared-kernel candidate request not found")
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
    store = SQLiteSharedKernelCandidateStore(args.store)
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


def handle_shared_kernel_candidate_command(args: argparse.Namespace) -> int | None:
    handlers = {
        "run-shared-kernel-candidate": _run,
        "show-shared-kernel-candidate": _show,
        "shared-kernel-candidate-summary": _summary,
    }
    handler = handlers.get(args.command)
    return None if handler is None else handler(args)
