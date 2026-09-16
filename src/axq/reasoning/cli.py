"""Offline-only CLI for structured reasoning execution and audit inspection."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from axq.reasoning.contracts import (
    LLMReusePolicy,
    ProviderKind,
    ProviderModelIdentity,
    ReflectionExplanationInput,
    canonical_reasoning_bytes,
)
from axq.reasoning.ollama import OllamaProvider, validate_loopback_ollama_url
from axq.reasoning.provider import LLMProvider
from axq.reasoning.service import run_reflection_explanation
from axq.reasoning.store import SQLiteReasoningAuditStore

ProviderFactory = Callable[[str], LLMProvider]
Clock = Callable[[], datetime]
MonotonicClock = Callable[[], float]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run-reflection-explanation")
    run.add_argument("--input", type=Path, required=True)
    run.add_argument("--store", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--attempt-key", required=True)
    run.add_argument(
        "--reuse-policy",
        choices=[item.value for item in LLMReusePolicy],
        default=LLMReusePolicy.REUSE_FIRST_COMPLETED_EXACT.value,
    )
    run.add_argument("--endpoint", default="http://127.0.0.1:11434")
    run.add_argument("--model", required=True)
    run.add_argument("--model-digest", required=True)
    run.add_argument("--ollama-version", required=True)
    run.add_argument("--timeout-seconds", type=float, required=True)

    show_request = commands.add_parser("show-request")
    show_request.add_argument("--store", type=Path, required=True)
    show_request.add_argument("--request-id", required=True)

    show_response = commands.add_parser("show-response")
    show_response.add_argument("--store", type=Path, required=True)
    show_response.add_argument("--response-id", required=True)

    show_history = commands.add_parser("show-history")
    show_history.add_argument("--store", type=Path, required=True)
    show_history.add_argument("--request-id", required=True)

    summary = commands.add_parser("reasoning-summary")
    summary.add_argument("--store", type=Path, required=True)
    return parser


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _emit_bytes(payload: bytes) -> None:
    print(payload.decode("ascii"))


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        temporary_path.replace(path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _load_controlled_input(path: Path) -> ReflectionExplanationInput:
    raw = path.read_bytes()
    try:
        value = ReflectionExplanationInput.model_validate_json(raw)
    except ValueError as error:
        raise SystemExit("controlled input is not a valid reflection explanation input") from error
    canonical = canonical_reasoning_bytes(value)
    if raw.rstrip(b"\r\n") != canonical:
        raise SystemExit("controlled input must use canonical JSON bytes")
    return value


def _run(
    args: argparse.Namespace,
    *,
    provider_factory: ProviderFactory,
    clock: Clock,
    monotonic_clock: MonotonicClock,
) -> int:
    input_record = _load_controlled_input(args.input)
    provider_model = ProviderModelIdentity(
        provider=ProviderKind.OLLAMA,
        adapter_version="ollama-native-http-v1",
        provider_server_version=args.ollama_version,
        configured_model_name=args.model,
        resolved_model_name=args.model,
        model_digest=args.model_digest,
    )
    endpoint = validate_loopback_ollama_url(args.endpoint)
    provider = provider_factory(endpoint)
    observed_at = clock()
    result = run_reflection_explanation(
        input_record=input_record,
        expected_provider_model=provider_model,
        provider=provider,
        store=SQLiteReasoningAuditStore(args.store),
        attempt_key=args.attempt_key,
        reuse_policy=LLMReusePolicy(args.reuse_policy),
        requested_at=observed_at,
        started_at=observed_at,
        completed_at=observed_at,
        timeout_seconds=args.timeout_seconds,
        endpoint=endpoint,
        local_elapsed_ms=0.0,
        operational_clock=clock,
        monotonic_clock=monotonic_clock,
    )
    payload = canonical_reasoning_bytes(result)
    _atomic_write(args.output, payload)
    _emit_bytes(payload)
    return 0


def _show_request(args: argparse.Namespace) -> int:
    request = SQLiteReasoningAuditStore(args.store).request(args.request_id)
    if request is None:
        raise SystemExit("reasoning request not found")
    _emit_bytes(canonical_reasoning_bytes(request))
    return 0


def _show_response(args: argparse.Namespace) -> int:
    response = SQLiteReasoningAuditStore(args.store).response(args.response_id)
    if response is None:
        raise SystemExit("reasoning response not found")
    _emit_bytes(canonical_reasoning_bytes(response))
    return 0


def _show_history(args: argparse.Namespace) -> int:
    attempts = SQLiteReasoningAuditStore(args.store).attempts(args.request_id)
    _emit_bytes(_json_bytes([item.model_dump(mode="json") for item in attempts]))
    return 0


def _summary(args: argparse.Namespace) -> int:
    store = SQLiteReasoningAuditStore(args.store)
    requests = store.requests()
    responses = store.responses()
    attempts = store.all_attempts()
    status_counts = Counter(item.status.value for item in attempts)
    _emit_bytes(
        _json_bytes(
            {
                "attempt_count": len(attempts),
                "completed_response_count": len(
                    {item.response_id for item in attempts if item.status.value == "COMPLETED"}
                ),
                "failure_count": sum(
                    item.status.value not in {"COMPLETED", "REUSED"} for item in attempts
                ),
                "request_count": len(requests),
                "response_count": len(responses),
                "reused_attempt_count": status_counts.get("REUSED", 0),
                "status_counts": dict(sorted(status_counts.items())),
            }
        )
    )
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    provider_factory: ProviderFactory = OllamaProvider,
    clock: Clock = lambda: datetime.now(UTC),
    monotonic_clock: MonotonicClock = perf_counter,
) -> int:
    """Dispatch the offline reasoning CLI."""

    args = _parser().parse_args(argv)
    if args.command == "run-reflection-explanation":
        return _run(
            args,
            provider_factory=provider_factory,
            clock=clock,
            monotonic_clock=monotonic_clock,
        )
    handlers: dict[str, Callable[[argparse.Namespace], int]] = {
        "show-request": _show_request,
        "show-response": _show_response,
        "show-history": _show_history,
        "reasoning-summary": _summary,
    }
    return handlers[args.command](args)


__all__ = ["main"]
