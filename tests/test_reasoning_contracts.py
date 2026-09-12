"""Contract tests for the offline Phase 9 reasoning boundary."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from axq.reasoning.contracts import (
    BoundedReasoningContextItem,
    LLMAttemptStatus,
    LLMExecutionAttemptAudit,
    LLMFailureCode,
    LLMFailureMetadata,
    LLMRequestEnvelope,
    LLMStructuredResponseArtifact,
    ReflectionExplanation,
    UncertaintyAssessment,
    UncertaintyLevel,
    canonical_reasoning_bytes,
)
from tests.reasoning_test_support import (
    context_item,
    generation_policy,
    prompt_identity,
    provider_identity,
    request_envelope,
    source_reference,
    utc,
)


def explanation(**changes: object) -> ReflectionExplanation:
    values: dict[str, object] = {
        "explanation": "The cited weekly evidence shows repeated London-session weakness.",
        "cited_evidence_ids": (
            "context-weekly-summary",
            "weekly-reflection-aaaaaaaaaaaaaaaaaaaa",
        ),
        "hypothesis": "The weakness may be concentrated in one session regime.",
        "uncertainty": UncertaintyAssessment(
            level=UncertaintyLevel.MEDIUM,
            basis="Only two complete weekly observations support the pattern.",
        ),
        "suggested_next_investigation": (
            "Compare the same setup across London and non-London development periods."
        ),
    }
    values.update(changes)
    return ReflectionExplanation.model_validate(values)


def response_artifact(
    request: LLMRequestEnvelope | None = None,
    *,
    output: ReflectionExplanation | None = None,
) -> LLMStructuredResponseArtifact:
    actual_request = request or request_envelope()
    return LLMStructuredResponseArtifact.from_request(
        request=actual_request,
        output=output or explanation(),
    )


def completed_attempt(
    *,
    request: LLMRequestEnvelope | None = None,
    response: LLMStructuredResponseArtifact | None = None,
    **changes: object,
) -> LLMExecutionAttemptAudit:
    actual_request = request or request_envelope()
    actual_response = response or response_artifact(actual_request)
    values: dict[str, object] = {
        "request_id": actual_request.request_id,
        "attempt_key": "fixture-attempt-001",
        "status": LLMAttemptStatus.COMPLETED,
        "provider_model": actual_request.provider_model,
        "response_id": actual_response.response_id,
        "requested_at": utc("2026-09-12T00:00:00Z"),
        "started_at": utc("2026-09-12T00:00:01Z"),
        "completed_at": utc("2026-09-12T00:00:02Z"),
        "timeout_seconds": 30.0,
        "endpoint": "http://127.0.0.1:11434",
        "prompt_token_count": 120,
        "output_token_count": 42,
        "provider_total_duration_ns": 4_000_000,
        "local_elapsed_ms": 5.0,
    }
    values.update(changes)
    return LLMExecutionAttemptAudit.model_validate(values)


def test_models_are_strict_and_frozen() -> None:
    identity = provider_identity()
    with pytest.raises(ValidationError, match="Instance is frozen"):
        identity.model_digest = "b" * 64
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        provider_identity().model_validate(identity.model_dump() | {"unexpected": True})


def test_context_digest_and_canonical_content_are_bound() -> None:
    left = context_item(content={"b": 2, "a": [3, 1]})
    right = context_item(content={"a": [3, 1], "b": 2})
    assert left.content_digest == right.content_digest
    assert canonical_reasoning_bytes(left) == canonical_reasoning_bytes(right)

    with pytest.raises(ValidationError, match="content_digest"):
        BoundedReasoningContextItem(
            context_id="context-weekly-summary",
            source=source_reference(),
            context_kind="WEEKLY_FINDING_SUMMARY",
            content={"summary": "safe"},
            content_digest="f" * 64,
        )


def test_context_limits_are_enforced() -> None:
    source = source_reference()
    oversized = {"summary": "x" * 2_100}
    with pytest.raises(ValidationError, match="2,000"):
        context_item(source=source, content=oversized)

    contexts = tuple(
        context_item(context_id=f"context-{index:02d}", source=source)
        for index in range(17)
    )
    with pytest.raises(ValidationError, match="16 context items"):
        request_envelope(context=contexts)


def test_request_normalizes_source_and_context_order() -> None:
    first = source_reference(
        source_id="daily-reflection-11111111111111111111",
        source_digest="1" * 64,
    )
    second = source_reference(
        source_id="weekly-reflection-22222222222222222222",
        source_digest="2" * 64,
    )
    context_first = context_item(context_id="context-a", source=first)
    context_second = context_item(context_id="context-b", source=second)

    left = request_envelope(
        source_references=(second, first),
        context=(context_second, context_first),
    )
    right = request_envelope(
        source_references=(first, second),
        context=(context_first, context_second),
    )

    assert left.request_id == right.request_id
    assert left.source_references == (first, second)
    assert left.context == (context_first, context_second)
    assert canonical_reasoning_bytes(left) == canonical_reasoning_bytes(right)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("adapter_version", "ollama-native-http-v2"),
        ("provider_server_version", "0.12.7"),
        ("configured_model_name", "qwen3:14b"),
        ("model_digest", "d" * 64),
    ],
)
def test_request_identity_changes_with_provider_or_model(
    field: str,
    replacement: object,
) -> None:
    baseline = request_envelope()
    changed = request_envelope(provider_model=provider_identity(**{field: replacement}))
    assert changed.request_id != baseline.request_id


def test_request_identity_changes_with_prompt_schema_generation_source_or_context() -> None:
    baseline = request_envelope()
    variants = (
        request_envelope(prompt=prompt_identity(template_digest="d" * 64)),
        request_envelope(prompt=prompt_identity(response_schema_digest="e" * 64)),
        request_envelope(generation=generation_policy(seed=18)),
        request_envelope(
            source_references=(source_reference(source_digest="3" * 64),),
            context=(
                context_item(source=source_reference(source_digest="3" * 64)),
            ),
        ),
        request_envelope(context=(context_item(content={"summary": "Different evidence."}),)),
    )
    assert all(item.request_id != baseline.request_id for item in variants)


def test_attempt_identity_excludes_operational_times_and_metrics() -> None:
    baseline = completed_attempt()
    later = completed_attempt(
        requested_at=utc("2026-09-13T00:00:00Z"),
        started_at=utc("2026-09-13T00:00:02Z"),
        completed_at=utc("2026-09-13T00:00:05Z"),
        timeout_seconds=60.0,
        prompt_token_count=121,
        output_token_count=43,
        provider_total_duration_ns=8_000_000,
        local_elapsed_ms=9.0,
    )
    assert later.attempt_id == baseline.attempt_id


@pytest.mark.parametrize(
    "bad_time",
    [
        datetime(2026, 9, 12, 0, 0),
        datetime(2026, 9, 12, 8, 0, tzinfo=timezone(timedelta(hours=8))),
    ],
)
def test_attempt_rejects_naive_or_non_utc_times(bad_time: datetime) -> None:
    with pytest.raises(ValidationError, match="UTC"):
        completed_attempt(requested_at=bad_time)


def test_attempt_rejects_invalid_time_order() -> None:
    with pytest.raises(ValidationError, match="requested_at.*started_at.*completed_at"):
        completed_attempt(
            started_at=utc("2026-09-12T00:00:03Z"),
            completed_at=utc("2026-09-12T00:00:02Z"),
        )


def test_structured_response_rejects_extra_fields_and_false_citations() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ReflectionExplanation.model_validate(
            explanation().model_dump() | {"chain_of_thought": "must not be accepted"}
        )

    with pytest.raises(ValueError, match="citations must reference allowed evidence IDs"):
        response_artifact(
            output=explanation(cited_evidence_ids=("invented-evidence-id",)),
        )


def test_response_identity_is_content_addressed() -> None:
    request = request_envelope()
    baseline = response_artifact(request)
    identical = response_artifact(request)
    changed = response_artifact(
        request,
        output=explanation(hypothesis="A different falsifiable hypothesis."),
    )
    assert baseline.response_id == identical.response_id
    assert canonical_reasoning_bytes(baseline) == canonical_reasoning_bytes(identical)
    assert changed.response_id != baseline.response_id


def test_failure_and_success_attempt_semantics_are_exclusive() -> None:
    request = request_envelope()
    response = response_artifact(request)
    failure = LLMFailureMetadata(
        code=LLMFailureCode.TIMEOUT,
        message="Ollama request timed out.",
    )
    with pytest.raises(ValidationError, match="successful attempt cannot contain failure"):
        completed_attempt(failure=failure)
    with pytest.raises(ValidationError, match="failed attempt cannot reference response"):
        completed_attempt(
            status=LLMAttemptStatus.TIMEOUT,
            response_id=response.response_id,
            failure=failure,
        )

    failed = completed_attempt(
        status=LLMAttemptStatus.TIMEOUT,
        response_id=None,
        failure=failure,
    )
    assert failed.failure == failure


def test_supplied_content_id_mismatches_fail_closed() -> None:
    request = request_envelope()
    with pytest.raises(ValidationError, match="request_id"):
        LLMRequestEnvelope.model_validate(request.model_dump() | {"request_id": "llm-request-bad"})

    response = response_artifact(request)
    with pytest.raises(ValidationError, match="response_id"):
        LLMStructuredResponseArtifact.model_validate(
            response.model_dump() | {"response_id": "llm-response-bad"}
        )


def test_canonical_reasoning_bytes_are_ascii_sorted_and_stable() -> None:
    request = request_envelope()
    payload = canonical_reasoning_bytes(request)
    assert payload == canonical_reasoning_bytes(request_envelope())
    assert payload.isascii()
    assert b"\n" not in payload
    assert json.loads(payload) == request.model_dump(mode="json")
    assert payload.startswith(b'{"context":')
