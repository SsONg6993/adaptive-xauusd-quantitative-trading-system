"""Focused tests for offline reasoning orchestration and exact-result reuse."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from axq.reasoning.contracts import (
    LLMAttemptStatus,
    LLMFailureCode,
    LLMReusePolicy,
    LLMStructuredResponseArtifact,
    ReflectionExplanationInput,
    canonical_reasoning_bytes,
)
from axq.reasoning.prompts import RenderedReasoningPrompt
from axq.reasoning.provider import (
    LLMProviderConnectionError,
    LLMProviderError,
    LLMProviderTimeoutError,
    ProviderAttemptControls,
    ProviderCompletion,
    ProviderUsage,
)
from axq.reasoning.service import (
    build_reflection_explanation_request,
    run_reflection_explanation,
)
from axq.reasoning.store import SQLiteReasoningAuditStore
from tests.reasoning_test_support import provider_identity, request_envelope, utc


def _input_record() -> ReflectionExplanationInput:
    request = request_envelope()
    return ReflectionExplanationInput(
        source_references=request.source_references,
        context=request.context,
        generation=request.generation,
    )


def _output_json(*, explanation: str = "Repeated weakness is present.") -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "explanation": explanation,
            "cited_evidence_ids": [
                "context-weekly-summary",
                "weekly-reflection-aaaaaaaaaaaaaaaaaaaa",
            ],
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


def _completion(
    raw_content: str,
    *,
    unexpected_thinking: bool = False,
) -> ProviderCompletion:
    raw = raw_content.encode("utf-8")
    return ProviderCompletion(
        raw_content=raw_content,
        raw_response_digest=sha256(raw).hexdigest(),
        raw_response_bytes=len(raw),
        unexpected_thinking=unexpected_thinking,
        usage=ProviderUsage(
            prompt_token_count=120,
            output_token_count=42,
            total_duration_ns=4_000_000,
            load_duration_ns=100_000,
            prompt_duration_ns=1_000_000,
            output_duration_ns=2_900_000,
        ),
    )


class FakeReasoningProvider:
    endpoint = "http://127.0.0.1:11434"

    def __init__(
        self,
        outcomes: Sequence[ProviderCompletion | LLMProviderError],
        *,
        observed_identity: object | None = None,
    ) -> None:
        self.outcomes = list(outcomes)
        self.observed_identity = observed_identity
        self.verify_calls = 0
        self.complete_calls = 0
        self.prompts: list[RenderedReasoningPrompt] = []

    def verify_identity(self, expected: object, *, timeout_seconds: float) -> object:
        self.verify_calls += 1
        if self.outcomes and isinstance(self.outcomes[0], LLMProviderError):
            raise self.outcomes.pop(0)
        return expected if self.observed_identity is None else self.observed_identity

    def complete(
        self,
        request: object,
        prompt: RenderedReasoningPrompt,
        *,
        controls: ProviderAttemptControls,
    ) -> ProviderCompletion:
        self.complete_calls += 1
        self.prompts.append(prompt)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, LLMProviderError):
            raise outcome
        return outcome


def _run(
    *,
    store: SQLiteReasoningAuditStore,
    provider: FakeReasoningProvider,
    attempt_key: str,
    reuse_policy: LLMReusePolicy = LLMReusePolicy.REUSE_FIRST_COMPLETED_EXACT,
    requested_at: object | None = None,
    input_record: ReflectionExplanationInput | None = None,
) -> object:
    start = requested_at or utc("2026-09-12T00:00:00Z")
    return run_reflection_explanation(
        input_record=input_record or _input_record(),
        expected_provider_model=provider_identity(),
        provider=provider,
        store=store,
        attempt_key=attempt_key,
        reuse_policy=reuse_policy,
        requested_at=start,
        started_at=start,
        completed_at=start,
        timeout_seconds=30.0,
        endpoint=provider.endpoint,
        local_elapsed_ms=5.0,
    )


def test_builds_persists_and_completes_one_strict_request(tmp_path: Path) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider([_completion(_output_json())])

    result = _run(store=store, provider=provider, attempt_key="attempt-001")

    assert result.status is LLMAttemptStatus.COMPLETED
    assert result.reused is False
    assert provider.verify_calls == 1
    assert provider.complete_calls == 1
    assert len(store.requests()) == len(store.responses()) == len(store.all_attempts()) == 1
    response = store.response(result.response_id)
    assert response is not None
    assert canonical_reasoning_bytes(response) == canonical_reasoning_bytes(
        LLMStructuredResponseArtifact.from_request(
            request=store.requests()[0],
            output=response.output,
        )
    )
    assert response.output.cited_evidence_ids == (
        "context-weekly-summary",
        "weekly-reflection-aaaaaaaaaaaaaaaaaaaa",
    )


def test_exact_completed_reuse_skips_provider_and_preserves_response_bytes(
    tmp_path: Path,
) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider([_completion(_output_json())])
    first = _run(store=store, provider=provider, attempt_key="attempt-001")
    before = canonical_reasoning_bytes(store.response(first.response_id))

    second = _run(
        store=store,
        provider=provider,
        attempt_key="attempt-002",
        requested_at=utc("2026-09-13T00:00:00Z"),
    )

    assert second.status is LLMAttemptStatus.REUSED
    assert second.reused is True
    assert second.response_id == first.response_id
    assert canonical_reasoning_bytes(store.response(second.response_id)) == before
    assert provider.verify_calls == provider.complete_calls == 1
    assert [item.status for item in store.all_attempts()] == [
        LLMAttemptStatus.COMPLETED,
        LLMAttemptStatus.REUSED,
    ]


def test_never_reuse_invokes_provider_and_can_append_different_generation(
    tmp_path: Path,
) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider(
        [
            _completion(_output_json()),
            _completion(_output_json(explanation="A distinct valid generation.")),
        ]
    )
    first = _run(
        store=store,
        provider=provider,
        attempt_key="attempt-001",
        reuse_policy=LLMReusePolicy.NEVER_REUSE,
    )
    second = _run(
        store=store,
        provider=provider,
        attempt_key="attempt-002",
        reuse_policy=LLMReusePolicy.NEVER_REUSE,
    )

    assert first.response_id != second.response_id
    assert provider.verify_calls == provider.complete_calls == 2
    assert len(store.responses()) == 2


@pytest.mark.parametrize(
    "failure",
    [
        LLMProviderTimeoutError(),
        LLMProviderConnectionError(),
        LLMProviderError(
            status=LLMAttemptStatus.HTTP_ERROR,
            code=LLMFailureCode.HTTP_ERROR,
            message="Provider returned an HTTP error.",
            http_status=503,
        ),
        LLMProviderError(
            status=LLMAttemptStatus.MODEL_UNAVAILABLE,
            code=LLMFailureCode.MODEL_UNAVAILABLE,
            message="Model unavailable.",
        ),
        LLMProviderError(
            status=LLMAttemptStatus.PROVIDER_ERROR,
            code=LLMFailureCode.PROVIDER_ERROR,
            message="Provider failed safely.",
        ),
    ],
)
def test_typed_provider_failures_are_permanently_audited(
    tmp_path: Path,
    failure: LLMProviderError,
) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider([failure])

    result = _run(store=store, provider=provider, attempt_key="attempt-001")

    assert result.status is failure.status
    assert result.failure == failure.failure
    assert store.all_attempts()[0].failure == failure.failure
    assert store.responses() == ()


def test_observed_model_identity_mismatch_is_audited_before_completion(
    tmp_path: Path,
) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider(
        [_completion(_output_json())],
        observed_identity=provider_identity(model_digest="d" * 64),
    )

    result = _run(store=store, provider=provider, attempt_key="attempt-001")

    assert result.status is LLMAttemptStatus.MODEL_IDENTITY_MISMATCH
    assert provider.verify_calls == 1
    assert provider.complete_calls == 0


@pytest.mark.parametrize(
    "raw_content",
    [
        "not-json PRIVATE_RAW_TEXT",
        json.dumps({"explanation": "PRIVATE_RAW_TEXT"}),
        _output_json().replace(
            '"context-weekly-summary"',
            '"invented-evidence-id"',
        ),
        _output_json()[:-1] + ',"chain_of_thought":"PRIVATE_RAW_TEXT"}',
    ],
)
def test_invalid_output_persists_only_safe_digest_size_and_error(
    tmp_path: Path,
    raw_content: str,
) -> None:
    path = tmp_path / "reasoning.sqlite3"
    store = SQLiteReasoningAuditStore(path)
    provider = FakeReasoningProvider([_completion(raw_content)])

    result = _run(store=store, provider=provider, attempt_key="attempt-001")

    assert result.status is LLMAttemptStatus.INVALID_RESPONSE
    assert result.failure is not None
    assert result.failure.raw_response_digest == sha256(raw_content.encode()).hexdigest()
    assert result.failure.raw_response_bytes == len(raw_content.encode())
    assert store.responses() == ()
    with sqlite3.connect(path) as connection:
        records = "\n".join(
            str(row[0])
            for table in (
                "llm_reasoning_requests",
                "llm_reasoning_responses",
                "llm_reasoning_attempts",
            )
            for row in connection.execute(f"SELECT record_json FROM {table}")
        )
    assert raw_content not in records
    assert "PRIVATE_RAW_TEXT" not in records
    assert "traceback" not in records.casefold()


def test_unexpected_thinking_is_rejected_without_persisting_content(tmp_path: Path) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider(
        [_completion(_output_json(), unexpected_thinking=True)]
    )

    result = _run(store=store, provider=provider, attempt_key="attempt-001")

    assert result.status is LLMAttemptStatus.INVALID_RESPONSE
    assert store.responses() == ()


def test_output_over_request_byte_limit_is_rejected(tmp_path: Path) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider([_completion(_output_json())])
    input_record = _input_record().model_copy(
        update={
            "generation": _input_record().generation.model_copy(
                update={"response_byte_limit": 100}
            )
        }
    )

    result = _run(
        store=store,
        provider=provider,
        attempt_key="attempt-001",
        input_record=input_record,
    )

    assert result.status is LLMAttemptStatus.INVALID_RESPONSE
    assert store.responses() == ()


def test_failure_then_later_success_preserves_both_attempts(tmp_path: Path) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider(
        [LLMProviderTimeoutError(), _completion(_output_json())]
    )
    failed = _run(store=store, provider=provider, attempt_key="attempt-001")
    succeeded = _run(store=store, provider=provider, attempt_key="attempt-002")

    assert failed.status is LLMAttemptStatus.TIMEOUT
    assert succeeded.status is LLMAttemptStatus.COMPLETED
    assert [item.status for item in store.all_attempts()] == [
        LLMAttemptStatus.TIMEOUT,
        LLMAttemptStatus.COMPLETED,
    ]
    assert provider.verify_calls == 2
    assert provider.complete_calls == 1


def test_same_attempt_key_is_idempotent_without_provider_reinvocation(tmp_path: Path) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider([_completion(_output_json())])
    first = _run(store=store, provider=provider, attempt_key="attempt-001")
    second = _run(store=store, provider=provider, attempt_key="attempt-001")

    assert second == first
    assert provider.verify_calls == provider.complete_calls == 1
    assert len(store.all_attempts()) == 1


def test_invalid_bounded_input_fails_before_persistence(tmp_path: Path) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    provider = FakeReasoningProvider([_completion(_output_json())])
    valid = _input_record()
    invalid = valid.model_copy(update={"context": ()})

    with pytest.raises(ValidationError):
        run_reflection_explanation(
            input_record=invalid,
            expected_provider_model=provider_identity(),
            provider=provider,
            store=store,
            attempt_key="attempt-001",
            reuse_policy=LLMReusePolicy.REUSE_FIRST_COMPLETED_EXACT,
            requested_at=utc("2026-09-12T00:00:00Z"),
            started_at=utc("2026-09-12T00:00:00Z"),
            completed_at=utc("2026-09-12T00:00:00Z"),
            timeout_seconds=30.0,
            endpoint=provider.endpoint,
            local_elapsed_ms=0.0,
        )
    assert store.requests() == ()


def test_request_identity_does_not_include_operational_timestamps() -> None:
    first = build_reflection_explanation_request(
        input_record=_input_record(),
        provider_model=provider_identity(),
    )
    second = build_reflection_explanation_request(
        input_record=_input_record(),
        provider_model=provider_identity(),
    )
    assert first.request_id == second.request_id
    assert canonical_reasoning_bytes(first) == canonical_reasoning_bytes(second)
