"""Contract and identity tests for offline experience retrieval."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from axq.reasoning.contracts import (
    ReasoningSourceKind,
    ReasoningSourceReference,
    ReflectionExplanationInput,
)
from axq.reasoning.prompts import (
    reflection_explanation_prompt_identity,
    render_reflection_explanation_prompt,
)
from axq.retrieval.contracts import (
    CandidateManifestMember,
    EmbeddingAttemptControls,
    EmbeddingAttemptStatus,
    EmbeddingInputRole,
    EmbeddingRequest,
    EvidenceLink,
    ExactEvidenceReference,
    ExperienceEvidenceMetadata,
    IndexCompleteness,
    RetrievalCandidateManifest,
    RetrievalIndexManifest,
    RetrievalIndexMember,
    RetrievalMetadataFilter,
    RetrievalQuerySpec,
    RetrievalRankingPolicy,
    RetrievalSourceKind,
    canonical_retrieval_bytes,
)
from axq.versioning import canonical_hash
from tests.retrieval_test_support import (
    completed_embedding_attempt,
    embedding_model,
    embedding_request,
    evidence_reference,
    prefix_profile,
    utc,
)


def test_experience_source_kind_preserves_task1_v2_prompt_contract() -> None:
    fixture = Path("tests/fixtures/reasoning/reflection_explanation_input.json")
    input_record = ReflectionExplanationInput.model_validate_json(fixture.read_bytes())
    identity = reflection_explanation_prompt_identity(input_record)
    rendered = render_reflection_explanation_prompt(input_record)

    assert ReasoningSourceKind.EXPERIENCE.value == "EXPERIENCE"
    assert identity.template_name == "REFLECTION_EXPLANATION_V2"
    assert identity.template_digest == (
        "eb84ab90ff749a2357d155a6d8409faf48349ee1949f030fe884f792dc638f84"
    )
    assert identity.response_schema_digest == (
        "00524fad3ad09d2663954865c46abe88ad3dec8153ce930af6fb76512666037a"
    )
    assert identity.response_schema_digest == canonical_hash(rendered.response_schema)
    assert rendered.response_schema["properties"]["cited_evidence_ids"]["items"][
        "enum"
    ] == ["context-weekly-summary", "weekly-reflection-aaaaaaaaaaaaaaaaaaaa"]

    reference = ReasoningSourceReference(
        source_kind=ReasoningSourceKind.EXPERIENCE,
        source_id="trade-experience-aaaaaaaaaaaaaaaaaaaa",
        source_digest="8" * 64,
    )
    assert reference.source_kind is ReasoningSourceKind.EXPERIENCE


def test_timeout_and_response_limit_are_operational_not_semantic() -> None:
    request = embedding_request()
    fast = EmbeddingAttemptControls(timeout_seconds=1.0, response_byte_limit=4_096)
    patient = EmbeddingAttemptControls(
        timeout_seconds=90.0,
        response_byte_limit=1_048_576,
    )

    assert request.embedding_request_id == embedding_request().embedding_request_id
    assert fast != patient
    assert "timeout_seconds" not in type(request).model_fields
    assert "response_byte_limit" not in type(request).model_fields


def test_attempt_audit_preserves_controls_and_excludes_times_from_identity() -> None:
    baseline = completed_embedding_attempt()
    later = completed_embedding_attempt(
        requested_at=utc("2026-09-13T00:00:00+00:00"),
        started_at=utc("2026-09-13T00:00:01+00:00"),
        completed_at=utc("2026-09-13T00:00:02+00:00"),
    )
    patient = completed_embedding_attempt(
        attempt_key="attempt-002",
        timeout_seconds=90.0,
        response_byte_limit=1_048_576,
    )

    assert baseline.attempt_id == later.attempt_id
    assert patient.timeout_seconds == 90.0
    assert patient.response_byte_limit == 1_048_576
    assert patient.attempt_id != baseline.attempt_id


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("role", EmbeddingInputRole.QUERY),
        ("semantic_input_id", "retrieval-query-bbbbbbbbbbbbbbbbbbbb"),
        ("canonical_content_digest", "9" * 64),
        ("prefixed_text_digest", "a" * 64),
        ("prefix_profile", None),
    ],
)
def test_embedding_request_identity_binds_semantic_fields(
    field: str,
    replacement: object,
) -> None:
    baseline = embedding_request()
    actual = prefix_profile().model_copy(update={"profile_digest": "b" * 64})
    changes = {field: actual if replacement is None else replacement}
    if field == "prefix_profile":
        changes["provider_model"] = embedding_model(prefix_profile=actual)
    changed = embedding_request(**changes)

    assert changed.embedding_request_id != baseline.embedding_request_id


def test_embedding_request_identity_binds_complete_model_identity() -> None:
    baseline = embedding_request()
    fields = {
        "adapter_version": "ollama-embedding-native-http-v2",
        "ollama_server_version": "0.12.7",
        "resolved_model_name": "nomic-embed-text:immutable",
        "model_digest": "c" * 64,
        "model_family": "different-family",
        "quantization": "Q8_0",
    }
    for field, value in fields.items():
        changed = embedding_request(provider_model=embedding_model(**{field: value}))
        assert changed.embedding_request_id != baseline.embedding_request_id


def test_contracts_reject_naive_or_non_utc_timestamps() -> None:
    reference = evidence_reference().model_dump()
    for invalid in (
        datetime(2026, 9, 12),
        datetime(2026, 9, 12, tzinfo=timezone(timedelta(hours=8))),
    ):
        with pytest.raises(ValidationError, match="UTC"):
            ExactEvidenceReference.model_validate(reference | {"available_at": invalid})


def test_evidence_provenance_and_filter_tuples_are_canonical() -> None:
    links = (
        EvidenceLink(
            source_kind=RetrievalSourceKind.DAILY_REFLECTION,
            source_id="daily-b",
            source_digest="d" * 64,
        ),
        EvidenceLink(
            source_kind=RetrievalSourceKind.EXPERIENCE,
            source_id="experience-a",
            source_digest="e" * 64,
        ),
    )
    reference = evidence_reference().model_copy(update={"upstream_references": links})
    metadata = ExperienceEvidenceMetadata(
        symbol="XAUUSD",
        experience_type="COMPLETED_TRADE",
        direction="SELL",
        session="LONDON",
    )
    filters = RetrievalMetadataFilter(
        source_kinds=(RetrievalSourceKind.WEEKLY_REFLECTION, RetrievalSourceKind.EXPERIENCE),
        symbols=("XAUUSD", "XAUUSD"),
        directions=("SELL", "BUY"),
    )

    assert [item.source_id for item in reference.upstream_references] == [
        "daily-b",
        "experience-a",
    ]
    assert metadata.metadata_kind == "EXPERIENCE"
    assert filters.source_kinds == (
        RetrievalSourceKind.EXPERIENCE,
        RetrievalSourceKind.WEEKLY_REFLECTION,
    )
    assert filters.symbols == ("XAUUSD",)
    assert filters.directions == ("BUY", "SELL")


def test_query_and_complete_manifests_are_content_addressed_and_ordered() -> None:
    ranking = RetrievalRankingPolicy()
    query = RetrievalQuerySpec(
        anchor=evidence_reference(),
        query_renderer_name="SOURCE_DERIVED_QUERY_V1",
        query_renderer_version="1.0",
        query_renderer_digest="f" * 64,
        canonical_query_content_digest="0" * 64,
        retrieval_as_of=utc(),
        metadata_filter=RetrievalMetadataFilter(),
        top_k=8,
        ranking_policy=ranking,
    )
    members = (
        RetrievalIndexMember(
            document_id="retrieval-document-b",
            vector_id="embedding-vector-b",
            source_kind=RetrievalSourceKind.WEEKLY_REFLECTION,
            source_id="weekly-b",
        ),
        RetrievalIndexMember(
            document_id="retrieval-document-a",
            vector_id="embedding-vector-a",
            source_kind=RetrievalSourceKind.EXPERIENCE,
            source_id="experience-a",
        ),
    )
    manifest = RetrievalIndexManifest(
        source_cutoff=utc(),
        source_adapter_identity="PHASE8_SOURCE_ADAPTERS_V1",
        renderer_identity_digest="1" * 64,
        provider_model=embedding_model(),
        members=members,
        revision_selection_policy="LATEST_CAUSALLY_AVAILABLE_EXPLICIT_CHAIN_V1",
        completeness=IndexCompleteness.COMPLETE,
    )
    candidates = RetrievalCandidateManifest(
        query_id=query.query_id,
        index_manifest_id=manifest.manifest_id,
        members=tuple(
            CandidateManifestMember(
                document_id=item.document_id,
                vector_id=item.vector_id,
                source_kind=item.source_kind,
                source_id=item.source_id,
            )
            for item in reversed(manifest.members)
        ),
    )

    assert query.query_id.startswith("retrieval-query-")
    assert manifest.member_count == 2
    assert manifest.members[0].source_kind is RetrievalSourceKind.EXPERIENCE
    assert candidates.members[0].source_kind is RetrievalSourceKind.EXPERIENCE
    assert canonical_retrieval_bytes(manifest) == canonical_retrieval_bytes(
        RetrievalIndexManifest.model_validate_json(canonical_retrieval_bytes(manifest))
    )


def test_top_k_bounds_and_attempt_linkage_fail_closed() -> None:
    for top_k in (0, 9):
        with pytest.raises(ValidationError):
            RetrievalQuerySpec(
                anchor=evidence_reference(),
                query_renderer_name="SOURCE_DERIVED_QUERY_V1",
                query_renderer_version="1.0",
                query_renderer_digest="f" * 64,
                canonical_query_content_digest="0" * 64,
                retrieval_as_of=utc(),
                metadata_filter=RetrievalMetadataFilter(),
                top_k=top_k,
                ranking_policy=RetrievalRankingPolicy(),
            )
    with pytest.raises(ValidationError, match="completed embedding attempt"):
        completed_embedding_attempt(
            status=EmbeddingAttemptStatus.COMPLETED,
            vector_id=None,
        )


def test_unknown_fields_and_mutation_are_rejected() -> None:
    with pytest.raises(ValidationError):
        EmbeddingRequest.model_validate(
            embedding_request().model_dump() | {"timeout_seconds": 30.0}
        )
    with pytest.raises(ValidationError):
        RetrievalMetadataFilter.model_validate({"sql": "DROP TABLE evidence"})
    with pytest.raises(ValidationError):
        embedding_request().role = EmbeddingInputRole.QUERY
