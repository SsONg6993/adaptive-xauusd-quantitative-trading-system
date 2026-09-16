"""Focused persistence tests for the append-only reasoning audit store."""

from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from axq.reasoning.contracts import (
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
from axq.reasoning.store import SQLiteReasoningAuditStore
from tests.reasoning_test_support import provider_identity, request_envelope, utc


def _explanation(**changes: object) -> ReflectionExplanation:
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
        "suggested_next_investigation": "Compare guarded development periods.",
    }
    values.update(changes)
    return ReflectionExplanation.model_validate(values)


def _response(
    request: LLMRequestEnvelope,
    **output_changes: object,
) -> LLMStructuredResponseArtifact:
    return LLMStructuredResponseArtifact.from_request(
        request=request,
        output=_explanation(**output_changes),
    )


def _attempt(
    request: LLMRequestEnvelope,
    *,
    response: LLMStructuredResponseArtifact | None = None,
    attempt_key: str = "attempt-001",
    status: LLMAttemptStatus = LLMAttemptStatus.COMPLETED,
    failure: LLMFailureMetadata | None = None,
) -> LLMExecutionAttemptAudit:
    return LLMExecutionAttemptAudit(
        request_id=request.request_id,
        attempt_key=attempt_key,
        status=status,
        provider_model=request.provider_model,
        response_id=None if response is None else response.response_id,
        failure=failure,
        requested_at=utc("2026-09-12T00:00:00Z"),
        started_at=utc("2026-09-12T00:00:01Z"),
        completed_at=utc("2026-09-12T00:00:02Z"),
        timeout_seconds=30.0,
        endpoint="http://127.0.0.1:11434",
        prompt_token_count=None if response is None else 120,
        output_token_count=None if response is None else 42,
        provider_total_duration_ns=None if response is None else 4_000_000,
        local_elapsed_ms=5.0,
    )


def test_migration_creates_only_append_only_reasoning_records(tmp_path: Path) -> None:
    path = tmp_path / "reasoning.sqlite3"
    SQLiteReasoningAuditStore(path)

    with sqlite3.connect(path) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {
        "llm_reasoning_requests",
        "llm_reasoning_responses",
        "llm_reasoning_attempts",
    }.issubset(tables)
    assert not any("current" in name for name in tables)


def test_request_response_and_attempt_round_trip_canonical_bytes(tmp_path: Path) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    request = request_envelope()
    response = _response(request)
    attempt = _attempt(request, response=response)

    assert store.append_request(request) is True
    assert store.append_response(response) is True
    assert store.append_attempt(attempt) is True
    assert store.append_request(request) is False
    assert store.append_response(response) is False
    assert store.append_attempt(attempt) is False

    assert canonical_reasoning_bytes(
        store.request(request.request_id)
    ) == canonical_reasoning_bytes(request)
    assert canonical_reasoning_bytes(
        store.response(response.response_id)
    ) == canonical_reasoning_bytes(response)
    assert canonical_reasoning_bytes(
        store.attempt(attempt.attempt_id)
    ) == canonical_reasoning_bytes(attempt)


def test_exact_linkage_and_attempt_key_conflicts_fail_closed(tmp_path: Path) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    request = request_envelope()
    response = _response(request)

    with pytest.raises(ValueError, match="request is not persisted"):
        store.append_response(response)
    store.append_request(request)
    with pytest.raises(ValueError, match="response is not persisted"):
        store.append_attempt(_attempt(request, response=response))
    store.append_response(response)
    store.append_attempt(_attempt(request, response=response))

    timeout = _attempt(
        request,
        attempt_key="attempt-001",
        status=LLMAttemptStatus.TIMEOUT,
        failure=LLMFailureMetadata(
            code=LLMFailureCode.TIMEOUT,
            message="Timed out without a structured response.",
        ),
    )
    with pytest.raises(ValueError, match="attempt key.*different content"):
        store.append_attempt(timeout)

    other_request = request_envelope(provider_model=provider_identity(model_digest="d" * 64))
    other_response = _response(other_request)
    store.append_request(other_request)
    store.append_response(other_response)
    mismatched = _attempt(request, response=other_response, attempt_key="attempt-002")
    with pytest.raises(ValueError, match="response.*request linkage"):
        store.append_attempt(mismatched)

    failed_with_response = timeout.model_copy(update={"response_id": response.response_id})
    with pytest.raises(ValidationError, match="failed attempt cannot reference response"):
        store.append_attempt(failed_with_response)


def test_forged_same_identity_with_different_bytes_fails_validation(
    tmp_path: Path,
) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    request = request_envelope()
    store.append_request(request)
    forged = request.model_copy(
        update={"generation": request.generation.model_copy(update={"seed": 999})}
    )
    with pytest.raises(ValidationError, match="request_id"):
        store.append_request(forged)


def test_same_attempt_identity_with_different_audit_bytes_fails_closed(
    tmp_path: Path,
) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    request = request_envelope()
    response = _response(request)
    original = _attempt(request, response=response)
    store.append_request(request)
    store.append_response(response)
    store.append_attempt(original)
    later = original.model_copy(
        update={
            "requested_at": utc("2026-09-13T00:00:00Z"),
            "started_at": utc("2026-09-13T00:00:01Z"),
            "completed_at": utc("2026-09-13T00:00:02Z"),
        }
    )
    assert later.attempt_id == original.attempt_id
    with pytest.raises(ValueError, match="attempt ID.*different content"):
        store.append_attempt(later)


def test_all_reasoning_records_reject_update_and_delete(tmp_path: Path) -> None:
    path = tmp_path / "reasoning.sqlite3"
    store = SQLiteReasoningAuditStore(path)
    request = request_envelope()
    response = _response(request)
    attempt = _attempt(request, response=response)
    store.append_request(request)
    store.append_response(response)
    store.append_attempt(attempt)

    cases = (
        ("llm_reasoning_requests", "request_id", request.request_id),
        ("llm_reasoning_responses", "response_id", response.response_id),
        ("llm_reasoning_attempts", "attempt_id", attempt.attempt_id),
    )
    with sqlite3.connect(path) as connection:
        for table, key, value in cases:
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(
                    f"UPDATE {table} SET schema_version = schema_version WHERE {key} = ?",
                    (value,),
                )
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                connection.execute(f"DELETE FROM {table} WHERE {key} = ?", (value,))


def test_history_replays_failures_and_returns_first_completed_response(
    tmp_path: Path,
) -> None:
    store = SQLiteReasoningAuditStore(tmp_path / "reasoning.sqlite3")
    request = request_envelope()
    first = _response(request)
    second = _response(request, explanation="A later independently generated explanation.")
    timeout = _attempt(
        request,
        attempt_key="attempt-001",
        status=LLMAttemptStatus.TIMEOUT,
        failure=LLMFailureMetadata(code=LLMFailureCode.TIMEOUT, message="Timed out."),
    )
    completed = _attempt(request, response=first, attempt_key="attempt-002")
    later = _attempt(request, response=second, attempt_key="attempt-003")
    reused = _attempt(
        request,
        response=first,
        attempt_key="attempt-004",
        status=LLMAttemptStatus.REUSED,
    )
    store.append_request(request)
    store.append_attempt(timeout)
    store.append_response(first)
    store.append_attempt(completed)
    store.append_response(second)
    store.append_attempt(later)
    store.append_attempt(reused)

    assert store.attempts(request.request_id) == (timeout, completed, later, reused)
    assert store.first_completed_response(request.request_id) == first
    assert store.requests() == (request,)
    assert store.responses() == (first, second)
    assert store.all_attempts() == (timeout, completed, later, reused)


def test_reads_detect_corrupted_payload_digest(tmp_path: Path) -> None:
    path = tmp_path / "reasoning.sqlite3"
    store = SQLiteReasoningAuditStore(path)
    request = request_envelope()
    store.append_request(request)

    with sqlite3.connect(path) as connection:
        connection.execute("DROP TRIGGER llm_reasoning_requests_no_update")
        connection.execute(
            "UPDATE llm_reasoning_requests SET payload_hash = ? WHERE request_id = ?",
            (sha256(b"corrupt").hexdigest(), request.request_id),
        )
        connection.commit()
    with pytest.raises(ValueError, match="payload digest"):
        store.request(request.request_id)


def test_reads_detect_record_column_divergence(tmp_path: Path) -> None:
    path = tmp_path / "reasoning.sqlite3"
    store = SQLiteReasoningAuditStore(path)
    request = request_envelope()
    store.append_request(request)
    payload = canonical_reasoning_bytes(request)

    with sqlite3.connect(path) as connection:
        connection.execute("DROP TRIGGER llm_reasoning_requests_no_update")
        connection.execute(
            "UPDATE llm_reasoning_requests SET task = ?, payload_hash = ?, record_json = ? "
            "WHERE request_id = ?",
            (
                "CORRUPTED_TASK",
                sha256(payload).hexdigest(),
                payload.decode("ascii"),
                request.request_id,
            ),
        )
        connection.commit()
    with pytest.raises(ValueError, match="indexed columns"):
        store.request(request.request_id)


def test_persisted_json_is_canonical_and_digest_bound(tmp_path: Path) -> None:
    path = tmp_path / "reasoning.sqlite3"
    store = SQLiteReasoningAuditStore(path)
    request = request_envelope()
    store.append_request(request)
    expected = canonical_reasoning_bytes(request)

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT record_json, payload_hash FROM llm_reasoning_requests WHERE request_id = ?",
            (request.request_id,),
        ).fetchone()
    assert row is not None
    assert str(row[0]).encode("ascii") == expected
    assert row[1] == sha256(expected).hexdigest()
    assert json.loads(str(row[0])) == request.model_dump(mode="json")
