"""Focused tests for the offline reasoning command-line boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

import pytest

from axq.reasoning.cli import _parser, main
from axq.reasoning.contracts import LLMAttemptStatus, LLMFailureCode
from axq.reasoning.provider import (
    LLMProviderError,
    ProviderAttemptControls,
    ProviderCompletion,
    ProviderUsage,
)
from axq.reasoning.store import SQLiteReasoningAuditStore
from tests.reasoning_test_support import utc

_FIXTURE = Path(__file__).parent / "fixtures" / "reasoning" / "reflection_explanation_input.json"
_DIGEST = "a" * 64


def _valid_output() -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "explanation": "Repeated weakness is present.",
            "cited_evidence_ids": ["context-weekly-summary"],
            "hypothesis": "The weakness may be conditional on the London session.",
            "uncertainty": {
                "schema_version": "1.0",
                "level": "MEDIUM",
                "basis": "Only two complete weekly observations are available.",
            },
            "suggested_next_investigation": "Compare guarded development periods.",
        },
        sort_keys=True,
        separators=(",", ":"),
    )


class FakeCLIProvider:
    def __init__(self, outcome: str | LLMProviderError) -> None:
        self.outcome = outcome
        self.verify_calls = 0
        self.complete_calls = 0

    def verify_identity(self, expected: object, *, timeout_seconds: float) -> object:
        self.verify_calls += 1
        if isinstance(self.outcome, LLMProviderError):
            raise self.outcome
        return expected

    def complete(
        self,
        request: object,
        prompt: object,
        *,
        controls: ProviderAttemptControls,
    ) -> ProviderCompletion:
        self.complete_calls += 1
        assert isinstance(self.outcome, str)
        raw = self.outcome.encode("utf-8")
        return ProviderCompletion(
            raw_content=self.outcome,
            raw_response_digest=sha256(raw).hexdigest(),
            raw_response_bytes=len(raw),
            usage=ProviderUsage(prompt_token_count=120, output_token_count=42),
        )


def _run_args(tmp_path: Path, *, attempt_key: str, output_name: str) -> list[str]:
    return [
        "run-reflection-explanation",
        "--input",
        str(_FIXTURE),
        "--store",
        str(tmp_path / "reasoning.sqlite3"),
        "--output",
        str(tmp_path / output_name),
        "--attempt-key",
        attempt_key,
        "--model",
        "qwen3:8b",
        "--model-digest",
        _DIGEST,
        "--ollama-version",
        "0.12.6",
        "--timeout-seconds",
        "30",
    ]


def test_run_parser_has_narrow_required_surface_and_safe_defaults(tmp_path: Path) -> None:
    args = _parser().parse_args(
        _run_args(tmp_path, attempt_key="attempt-001", output_name="r.json")
    )
    assert args.endpoint == "http://127.0.0.1:11434"
    assert args.reuse_policy == "REUSE_FIRST_COMPLETED_EXACT"
    destinations = {action.dest for action in _parser()._actions}
    run_parser = next(
        action for action in _parser()._actions if action.dest == "command"
    ).choices["run-reflection-explanation"]
    destinations |= {action.dest for action in run_parser._actions}
    assert not destinations & {
        "prompt",
        "final_oos",
        "broker",
        "mt5",
        "runtime_config",
        "credentials",
        "retrieval_url",
        "tools",
    }


def test_run_emits_and_atomically_writes_one_canonical_safe_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = FakeCLIProvider(_valid_output())
    output = tmp_path / "result.json"

    exit_code = main(
        _run_args(tmp_path, attempt_key="attempt-001", output_name=output.name),
        provider_factory=lambda endpoint: provider,
        clock=lambda: utc("2026-09-12T00:00:00Z"),
    )

    stdout = capsys.readouterr().out.encode("ascii")
    assert exit_code == 0
    assert stdout == output.read_bytes() + b"\n"
    payload = json.loads(output.read_bytes())
    assert set(payload) == {
        "attempt_id",
        "failure",
        "request_id",
        "response_id",
        "reused",
        "schema_version",
        "status",
    }
    assert payload["status"] == "COMPLETED"
    assert payload["failure"] is None
    assert provider.verify_calls == provider.complete_calls == 1


def test_run_records_observed_wall_and_monotonic_timing(tmp_path: Path) -> None:
    provider = FakeCLIProvider(_valid_output())
    wall_times = iter(
        (
            utc("2026-09-12T00:00:00Z"),
            utc("2026-09-12T00:00:01Z"),
            utc("2026-09-12T00:00:03Z"),
        )
    )
    monotonic_times = iter((10.0, 12.5))

    main(
        _run_args(tmp_path, attempt_key="timed-001", output_name="result.json"),
        provider_factory=lambda endpoint: provider,
        clock=lambda: next(wall_times),
        monotonic_clock=lambda: next(monotonic_times),
    )

    attempt = SQLiteReasoningAuditStore(
        tmp_path / "reasoning.sqlite3"
    ).all_attempts()[0]
    assert attempt.requested_at < attempt.started_at < attempt.completed_at
    assert attempt.local_elapsed_ms == 2500.0


def test_exact_reuse_emits_same_response_without_provider_call(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = FakeCLIProvider(_valid_output())
    main(
        _run_args(tmp_path, attempt_key="attempt-001", output_name="first.json"),
        provider_factory=lambda endpoint: provider,
        clock=lambda: utc("2026-09-12T00:00:00Z"),
    )
    capsys.readouterr()
    main(
        _run_args(tmp_path, attempt_key="attempt-002", output_name="second.json"),
        provider_factory=lambda endpoint: provider,
        clock=lambda: utc("2026-09-13T00:00:00Z"),
    )
    second_stdout = capsys.readouterr().out

    first = json.loads((tmp_path / "first.json").read_bytes())
    second = json.loads((tmp_path / "second.json").read_bytes())
    assert first["response_id"] == second["response_id"]
    assert second["status"] == "REUSED"
    assert second["reused"] is True
    assert json.loads(second_stdout) == second
    assert provider.verify_calls == provider.complete_calls == 1


def test_failure_output_contains_only_safe_metadata(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = FakeCLIProvider(
        LLMProviderError(
            status=LLMAttemptStatus.HTTP_ERROR,
            code=LLMFailureCode.HTTP_ERROR,
            message="Provider returned an HTTP error.",
            http_status=503,
            raw_response_digest="d" * 64,
            raw_response_bytes=27,
        )
    )
    output = tmp_path / "failed.json"

    main(
        _run_args(tmp_path, attempt_key="attempt-001", output_name=output.name),
        provider_factory=lambda endpoint: provider,
        clock=lambda: utc("2026-09-12T00:00:00Z"),
    )

    assert capsys.readouterr().out.encode("ascii") == output.read_bytes() + b"\n"
    payload = json.loads(output.read_bytes())
    assert payload["status"] == "HTTP_ERROR"
    assert payload["response_id"] is None
    assert payload["failure"] == {
        "code": "HTTP_ERROR",
        "http_status": 503,
        "message": "Provider returned an HTTP error.",
        "raw_response_bytes": 27,
        "raw_response_digest": "d" * 64,
        "schema_version": "1.0",
    }
    assert "raw_content" not in output.read_text(encoding="ascii")
    assert "thinking" not in output.read_text(encoding="ascii")


def test_show_history_and_summary_are_read_only_and_do_not_build_provider(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = FakeCLIProvider(_valid_output())
    main(
        _run_args(tmp_path, attempt_key="attempt-001", output_name="result.json"),
        provider_factory=lambda endpoint: provider,
        clock=lambda: utc("2026-09-12T00:00:00Z"),
    )
    capsys.readouterr()
    store_path = tmp_path / "reasoning.sqlite3"
    store = SQLiteReasoningAuditStore(store_path)
    request = store.requests()[0]
    response = store.responses()[0]
    before = (store.requests(), store.responses(), store.all_attempts())

    def forbidden_factory(endpoint: str) -> FakeCLIProvider:
        raise AssertionError("read-only command initialized a provider")

    commands = (
        ["show-request", "--store", str(store_path), "--request-id", request.request_id],
        ["show-response", "--store", str(store_path), "--response-id", response.response_id],
        ["show-history", "--store", str(store_path), "--request-id", request.request_id],
        ["reasoning-summary", "--store", str(store_path)],
    )
    outputs: list[object] = []
    for command in commands:
        assert main(command, provider_factory=forbidden_factory) == 0
        outputs.append(json.loads(capsys.readouterr().out))

    assert outputs[0]["request_id"] == request.request_id
    assert outputs[1]["response_id"] == response.response_id
    assert outputs[2][0]["status"] == "COMPLETED"
    assert outputs[3] == {
        "attempt_count": 1,
        "completed_response_count": 1,
        "failure_count": 0,
        "request_count": 1,
        "response_count": 1,
        "reused_attempt_count": 0,
        "status_counts": {"COMPLETED": 1},
    }
    after = (store.requests(), store.responses(), store.all_attempts())
    assert after == before


def test_noncanonical_or_extra_controlled_input_is_rejected_before_provider(
    tmp_path: Path,
) -> None:
    noncanonical = tmp_path / "input.json"
    payload = json.loads(_FIXTURE.read_bytes())
    payload["arbitrary_prompt"] = "forbidden"
    noncanonical.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    provider = FakeCLIProvider(_valid_output())
    args = _run_args(tmp_path, attempt_key="attempt-001", output_name="result.json")
    args[args.index(str(_FIXTURE))] = str(noncanonical)

    with pytest.raises(SystemExit, match="controlled input"):
        main(
            args,
            provider_factory=lambda endpoint: provider,
            clock=lambda: utc("2026-09-12T00:00:00Z"),
        )
    assert provider.verify_calls == provider.complete_calls == 0


def test_non_loopback_endpoint_is_rejected_before_provider_construction(
    tmp_path: Path,
) -> None:
    args = _run_args(tmp_path, attempt_key="attempt-001", output_name="result.json")
    args.extend(["--endpoint", "https://remote.example.invalid"])
    factory_calls = 0

    def provider_factory(endpoint: str) -> FakeCLIProvider:
        nonlocal factory_calls
        factory_calls += 1
        return FakeCLIProvider(_valid_output())

    with pytest.raises(ValueError, match="HTTP|loopback"):
        main(
            args,
            provider_factory=provider_factory,
            clock=lambda: utc("2026-09-12T00:00:00Z"),
        )
    assert factory_calls == 0


def test_python_module_entrypoint_exposes_offline_commands() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [sys.executable, "-m", "axq.reasoning", "--help"],
        cwd=Path(__file__).parents[1],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "run-reflection-explanation" in completed.stdout
    assert "reasoning-summary" in completed.stdout
