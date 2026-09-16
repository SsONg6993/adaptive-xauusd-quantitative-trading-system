"""Deterministic fixtures shared by Phase 9 retrieval tests."""

from __future__ import annotations

from datetime import UTC, datetime

from axq.retrieval.contracts import (
    EmbeddingAttemptAudit,
    EmbeddingAttemptStatus,
    EmbeddingInputRole,
    EmbeddingModelIdentity,
    EmbeddingPrefixProfileIdentity,
    EmbeddingRequest,
    EmbeddingVectorArtifact,
    ExactEvidenceReference,
    RetrievalSourceKind,
)


def utc(value: str = "2026-09-12T00:00:00+00:00") -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def evidence_reference() -> ExactEvidenceReference:
    return ExactEvidenceReference(
        source_kind=RetrievalSourceKind.WEEKLY_REFLECTION,
        source_id="weekly-reflection-aaaaaaaaaaaaaaaaaaaa",
        source_digest="1" * 64,
        available_at=utc(),
        source_schema_name="WeeklyReflection",
        source_schema_version="1.0",
    )


def prefix_profile() -> EmbeddingPrefixProfileIdentity:
    return EmbeddingPrefixProfileIdentity(
        profile_name="NOMIC_RETRIEVAL_PREFIX_V1",
        profile_version="1.0",
        profile_digest="2" * 64,
    )


def embedding_model(**changes: object) -> EmbeddingModelIdentity:
    payload: dict[str, object] = {
        "adapter_version": "ollama-embedding-native-http-v1",
        "ollama_server_version": "0.12.6",
        "configured_model_name": "nomic-embed-text:v1.5",
        "resolved_model_name": "nomic-embed-text:v1.5",
        "model_digest": "3" * 64,
        "expected_dimensions": 768,
        "model_family": "nomic-bert",
        "quantization": "F16",
        "prefix_profile": prefix_profile(),
    }
    payload.update(changes)
    return EmbeddingModelIdentity.model_validate(payload)


def embedding_request(**changes: object) -> EmbeddingRequest:
    payload: dict[str, object] = {
        "provider_model": embedding_model(),
        "role": EmbeddingInputRole.DOCUMENT,
        "semantic_input_id": "retrieval-document-aaaaaaaaaaaaaaaaaaaa",
        "canonical_content_digest": "4" * 64,
        "prefixed_text_digest": "5" * 64,
        "prefix_profile": prefix_profile(),
    }
    payload.update(changes)
    return EmbeddingRequest.model_validate(payload)


def vector_artifact(**changes: object) -> EmbeddingVectorArtifact:
    request = embedding_request()
    payload: dict[str, object] = {
        "embedding_request_id": request.embedding_request_id,
        "provider_model": request.provider_model,
        "dimension_count": 768,
        "vector_blob_digest": "6" * 64,
        "provider_response_digest": "7" * 64,
        "provider_response_bytes": 8_192,
        "vector_norm": 1.25,
    }
    payload.update(changes)
    return EmbeddingVectorArtifact.model_validate(payload)


def completed_embedding_attempt(**changes: object) -> EmbeddingAttemptAudit:
    request = embedding_request()
    vector = vector_artifact()
    payload: dict[str, object] = {
        "embedding_request_id": request.embedding_request_id,
        "attempt_key": "attempt-001",
        "status": EmbeddingAttemptStatus.COMPLETED,
        "vector_id": vector.vector_id,
        "requested_at": utc(),
        "started_at": utc(),
        "completed_at": utc(),
        "endpoint": "http://127.0.0.1:11434",
        "timeout_seconds": 30.0,
        "response_byte_limit": 1_048_576,
        "prompt_token_count": 10,
        "provider_total_duration_ns": 1_000,
        "local_elapsed_ms": 1.0,
    }
    payload.update(changes)
    return EmbeddingAttemptAudit.model_validate(payload)
