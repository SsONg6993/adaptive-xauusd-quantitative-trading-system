"""Strict immutable contracts for the paused Phase 9 Task 2 retrieval boundary."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    model_validator,
)

from axq.versioning import canonical_hash

_DIGEST_PATTERN = r"^[0-9a-f]{64}$"
_ID_MAX_LENGTH = 240


def _strict_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must use UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must use UTC offset +00:00")
    return value.astimezone(UTC)


RetrievalUTCDateTime = Annotated[datetime, AfterValidator(_strict_utc)]


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("numeric retrieval value must be finite")
    return value


FiniteFloat = Annotated[float, AfterValidator(_finite)]


def canonical_retrieval_bytes(value: BaseModel) -> bytes:
    """Return compact canonical bytes for a retrieval contract."""

    return json.dumps(
        value.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _bind_identity(model: BaseModel, field_name: str, prefix: str) -> None:
    identity = model.model_dump(mode="json", exclude={field_name})
    expected = f"{prefix}-{canonical_hash(identity)[:20]}"
    actual = getattr(model, field_name)
    if actual and actual != expected:
        raise ValueError(f"{field_name} does not match contract content")
    object.__setattr__(model, field_name, expected)


def _normalize_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    if any(not item.strip() for item in values):
        raise ValueError("filter values cannot be empty")
    return tuple(sorted(set(values)))


class RetrievalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class RetrievalSourceKind(StrEnum):
    EXPERIENCE = "EXPERIENCE"
    DAILY_REFLECTION = "DAILY_REFLECTION"
    WEEKLY_REFLECTION = "WEEKLY_REFLECTION"
    SUCCESS_PATTERN = "SUCCESS_PATTERN"
    FAILURE_PATTERN = "FAILURE_PATTERN"
    IMPROVEMENT_PROPOSAL = "IMPROVEMENT_PROPOSAL"


class EmbeddingProviderKind(StrEnum):
    OLLAMA = "OLLAMA"


class EmbeddingInputRole(StrEnum):
    DOCUMENT = "DOCUMENT"
    QUERY = "QUERY"


class EmbeddingReusePolicy(StrEnum):
    NEVER_REUSE = "NEVER_REUSE"
    REUSE_FIRST_COMPLETED_EXACT = "REUSE_FIRST_COMPLETED_EXACT"


class EmbeddingAttemptStatus(StrEnum):
    COMPLETED = "COMPLETED"
    REUSED = "REUSED"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_IDENTITY_MISMATCH = "MODEL_IDENTITY_MISMATCH"
    INVALID_VECTOR = "INVALID_VECTOR"
    DIMENSION_MISMATCH = "DIMENSION_MISMATCH"
    PROVIDER_ERROR = "PROVIDER_ERROR"


class RetrievalAttemptStatus(StrEnum):
    COMPLETED = "COMPLETED"
    REUSED = "REUSED"
    NO_MATCH = "NO_MATCH"
    PROVENANCE_MISMATCH = "PROVENANCE_MISMATCH"
    INCOMPLETE_INDEX = "INCOMPLETE_INDEX"
    INVALID_FILTER = "INVALID_FILTER"
    INVALID_VECTOR = "INVALID_VECTOR"
    PROVIDER_ERROR = "PROVIDER_ERROR"


class RetrievalFailureCode(StrEnum):
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_IDENTITY_MISMATCH = "MODEL_IDENTITY_MISMATCH"
    INVALID_VECTOR = "INVALID_VECTOR"
    DIMENSION_MISMATCH = "DIMENSION_MISMATCH"
    PROVENANCE_MISMATCH = "PROVENANCE_MISMATCH"
    INCOMPLETE_INDEX = "INCOMPLETE_INDEX"
    INVALID_FILTER = "INVALID_FILTER"
    PROVIDER_ERROR = "PROVIDER_ERROR"


class RetrievalResultStatus(StrEnum):
    COMPLETED = "COMPLETED"
    NO_MATCH = "NO_MATCH"


class IndexCompleteness(StrEnum):
    COMPLETE = "COMPLETE"


class EvidenceLink(RetrievalModel):
    source_kind: RetrievalSourceKind
    source_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    source_digest: str = Field(pattern=_DIGEST_PATTERN)


class ExactEvidenceReference(EvidenceLink):
    available_at: RetrievalUTCDateTime
    upstream_references: tuple[EvidenceLink, ...] = ()
    source_schema_name: str = Field(min_length=1, max_length=120)
    source_schema_version: str = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def normalize_provenance(self) -> ExactEvidenceReference:
        values = tuple(
            sorted(
                self.upstream_references,
                key=lambda item: (
                    item.source_kind.value,
                    item.source_id,
                    item.source_digest,
                ),
            )
        )
        keys = {(item.source_kind, item.source_id, item.source_digest) for item in values}
        if len(keys) != len(values):
            raise ValueError("upstream evidence references must be unique")
        object.__setattr__(self, "upstream_references", values)
        return self


class ExperienceEvidenceMetadata(RetrievalModel):
    metadata_kind: Literal["EXPERIENCE"] = "EXPERIENCE"
    symbol: str = Field(min_length=1, max_length=40)
    experience_type: str = Field(min_length=1, max_length=100)
    direction: str | None = Field(default=None, min_length=1, max_length=40)
    session: str | None = Field(default=None, min_length=1, max_length=80)
    regime: str | None = Field(default=None, min_length=1, max_length=80)
    rejection_layer: str | None = Field(default=None, min_length=1, max_length=100)
    reason_code: str | None = Field(default=None, min_length=1, max_length=120)


class ReflectionEvidenceMetadata(RetrievalModel):
    metadata_kind: Literal["REFLECTION"] = "REFLECTION"
    reflection_kind: Literal["DAILY_REFLECTION", "WEEKLY_REFLECTION"]
    category: str | None = Field(default=None, min_length=1, max_length=100)
    signal_class: str | None = Field(default=None, min_length=1, max_length=100)


class PatternEvidenceMetadata(RetrievalModel):
    metadata_kind: Literal["PATTERN"] = "PATTERN"
    pattern_type: Literal["SUCCESS_PATTERN", "FAILURE_PATTERN"]
    category: str = Field(min_length=1, max_length=100)
    signal_class: str = Field(min_length=1, max_length=100)
    reason_code: str | None = Field(default=None, min_length=1, max_length=120)
    scope: str = Field(min_length=1, max_length=100)
    scope_value: str = Field(min_length=1, max_length=160)


class ProposalEvidenceMetadata(RetrievalModel):
    metadata_kind: Literal["IMPROVEMENT_PROPOSAL"] = "IMPROVEMENT_PROPOSAL"
    target_component: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    proposal_status: str = Field(min_length=1, max_length=60)


EvidenceMetadata = Annotated[
    ExperienceEvidenceMetadata
    | ReflectionEvidenceMetadata
    | PatternEvidenceMetadata
    | ProposalEvidenceMetadata,
    Field(discriminator="metadata_kind"),
]


class RetrievalMetadataFilter(RetrievalModel):
    source_kinds: tuple[RetrievalSourceKind, ...] = ()
    symbols: tuple[str, ...] = ()
    experience_types: tuple[str, ...] = ()
    directions: tuple[str, ...] = ()
    sessions: tuple[str, ...] = ()
    regimes: tuple[str, ...] = ()
    rejection_layers: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    signal_classes: tuple[str, ...] = ()
    pattern_types: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()
    scope_values: tuple[str, ...] = ()
    target_components: tuple[str, ...] = ()
    proposal_statuses: tuple[str, ...] = ()

    @model_validator(mode="after")
    def normalize_values(self) -> RetrievalMetadataFilter:
        object.__setattr__(
            self,
            "source_kinds",
            tuple(sorted(set(self.source_kinds), key=lambda item: item.value)),
        )
        for name in type(self).model_fields:
            if name not in {"schema_version", "source_kinds"}:
                object.__setattr__(self, name, _normalize_strings(getattr(self, name)))
        return self


class EmbeddingPrefixProfileIdentity(RetrievalModel):
    profile_name: Literal["NOMIC_RETRIEVAL_PREFIX_V1"] = "NOMIC_RETRIEVAL_PREFIX_V1"
    profile_version: Literal["1.0"] = "1.0"
    profile_digest: str = Field(pattern=_DIGEST_PATTERN)


class EvidenceRendererIdentity(RetrievalModel):
    renderer_kind: str = Field(min_length=1, max_length=100)
    renderer_version: str = Field(min_length=1, max_length=40)
    renderer_digest: str = Field(pattern=_DIGEST_PATTERN)
    source_schema_name: str = Field(min_length=1, max_length=120)
    source_schema_version: str = Field(min_length=1, max_length=40)
    embedding_profile: EmbeddingPrefixProfileIdentity
    bounded_context_profile: str = Field(min_length=1, max_length=100)


class RetrievableEvidenceDocument(RetrievalModel):
    document_id: str = ""
    evidence: ExactEvidenceReference
    metadata: EvidenceMetadata
    renderer: EvidenceRendererIdentity
    bounded_context_content: JsonValue
    bounded_context_digest: str = Field(pattern=_DIGEST_PATTERN)
    embedding_text: str = Field(min_length=1, max_length=20_000)
    embedding_text_digest: str = Field(pattern=_DIGEST_PATTERN)
    canonical_character_count: int = Field(ge=1, le=1_500)
    embedding_utf8_bytes: int = Field(ge=1, le=40_000)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> RetrievableEvidenceDocument:
        if canonical_hash(self.bounded_context_content) != self.bounded_context_digest:
            raise ValueError("bounded context digest does not match content")
        if canonical_hash(self.embedding_text) != self.embedding_text_digest:
            raise ValueError("embedding text digest does not match text")
        if len(self.embedding_text.encode("utf-8")) != self.embedding_utf8_bytes:
            raise ValueError("embedding UTF-8 byte count does not match text")
        _bind_identity(self, "document_id", "retrieval-document")
        return self


class EmbeddingModelIdentity(RetrievalModel):
    provider: Literal[EmbeddingProviderKind.OLLAMA] = EmbeddingProviderKind.OLLAMA
    adapter_version: str = Field(min_length=1, max_length=100)
    ollama_server_version: str = Field(min_length=1, max_length=100)
    configured_model_name: str = Field(min_length=1, max_length=200)
    resolved_model_name: str = Field(min_length=1, max_length=200)
    model_digest: str = Field(pattern=_DIGEST_PATTERN)
    expected_dimensions: Literal[768] = 768
    model_family: str | None = Field(default=None, min_length=1, max_length=100)
    quantization: str | None = Field(default=None, min_length=1, max_length=100)
    embedding_api_contract_version: Literal["OLLAMA_EMBED_V1"] = "OLLAMA_EMBED_V1"
    prefix_profile: EmbeddingPrefixProfileIdentity
    vector_encoding: Literal["IEEE754_FLOAT32_LE_V1"] = "IEEE754_FLOAT32_LE_V1"


class EmbeddingAttemptControls(RetrievalModel):
    timeout_seconds: FiniteFloat = Field(gt=0.0, le=3_600.0)
    response_byte_limit: int = Field(ge=1, le=16_777_216)


class EmbeddingRequest(RetrievalModel):
    embedding_request_id: str = ""
    provider_model: EmbeddingModelIdentity
    role: EmbeddingInputRole
    semantic_input_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    canonical_content_digest: str = Field(pattern=_DIGEST_PATTERN)
    prefixed_text_digest: str = Field(pattern=_DIGEST_PATTERN)
    prefix_profile: EmbeddingPrefixProfileIdentity
    expected_dimensions: Literal[768] = 768
    vector_encoding: Literal["IEEE754_FLOAT32_LE_V1"] = "IEEE754_FLOAT32_LE_V1"

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> EmbeddingRequest:
        if self.prefix_profile != self.provider_model.prefix_profile:
            raise ValueError("embedding request prefix profile must match provider identity")
        if self.expected_dimensions != self.provider_model.expected_dimensions:
            raise ValueError("embedding request dimensions must match provider identity")
        if self.vector_encoding != self.provider_model.vector_encoding:
            raise ValueError("embedding request encoding must match provider identity")
        _bind_identity(self, "embedding_request_id", "embedding-request")
        return self


class EmbeddingVectorArtifact(RetrievalModel):
    vector_id: str = ""
    embedding_request_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    provider_model: EmbeddingModelIdentity
    vector_encoding: Literal["IEEE754_FLOAT32_LE_V1"] = "IEEE754_FLOAT32_LE_V1"
    dimension_count: Literal[768] = 768
    vector_blob_digest: str = Field(pattern=_DIGEST_PATTERN)
    provider_response_digest: str = Field(pattern=_DIGEST_PATTERN)
    provider_response_bytes: int = Field(ge=1)
    vector_norm: FiniteFloat = Field(gt=0.0)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> EmbeddingVectorArtifact:
        if self.dimension_count != self.provider_model.expected_dimensions:
            raise ValueError("vector dimensions must match provider identity")
        if self.vector_encoding != self.provider_model.vector_encoding:
            raise ValueError("vector encoding must match provider identity")
        _bind_identity(self, "vector_id", "embedding-vector")
        return self


class RetrievalFailureMetadata(RetrievalModel):
    code: RetrievalFailureCode
    message: str = Field(min_length=1, max_length=500)
    http_status: int | None = Field(default=None, ge=100, le=599)
    provider_response_digest: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    provider_response_bytes: int | None = Field(default=None, ge=0)


class EmbeddingAttemptAudit(RetrievalModel):
    attempt_id: str = ""
    embedding_request_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    attempt_key: str = Field(min_length=1, max_length=160)
    status: EmbeddingAttemptStatus
    vector_id: str | None = Field(default=None, min_length=1, max_length=_ID_MAX_LENGTH)
    failure: RetrievalFailureMetadata | None = None
    requested_at: RetrievalUTCDateTime
    started_at: RetrievalUTCDateTime
    completed_at: RetrievalUTCDateTime
    endpoint: str = Field(min_length=1, max_length=300)
    timeout_seconds: FiniteFloat = Field(gt=0.0, le=3_600.0)
    response_byte_limit: int = Field(ge=1, le=16_777_216)
    prompt_token_count: int | None = Field(default=None, ge=0)
    provider_total_duration_ns: int | None = Field(default=None, ge=0)
    local_elapsed_ms: FiniteFloat = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> EmbeddingAttemptAudit:
        if not self.requested_at <= self.started_at <= self.completed_at:
            raise ValueError("embedding attempt timestamps must be ordered")
        success = self.status in {
            EmbeddingAttemptStatus.COMPLETED,
            EmbeddingAttemptStatus.REUSED,
        }
        if success and (self.vector_id is None or self.failure is not None):
            raise ValueError("completed embedding attempt requires exact vector linkage")
        if not success and (self.vector_id is not None or self.failure is None):
            raise ValueError("failed embedding attempt requires failure without vector linkage")
        identity = self.model_dump(
            mode="json",
            exclude={
                "attempt_id",
                "requested_at",
                "started_at",
                "completed_at",
                "endpoint",
                "timeout_seconds",
                "response_byte_limit",
                "prompt_token_count",
                "provider_total_duration_ns",
                "local_elapsed_ms",
            },
        )
        expected = f"embedding-attempt-{canonical_hash(identity)[:20]}"
        if self.attempt_id and self.attempt_id != expected:
            raise ValueError("attempt_id does not match embedding attempt content")
        object.__setattr__(self, "attempt_id", expected)
        return self


class RetrievalRankingPolicy(RetrievalModel):
    policy_name: Literal["BRUTE_FORCE_COSINE_V1"] = "BRUTE_FORCE_COSINE_V1"
    policy_version: Literal["1.0"] = "1.0"
    input_encoding: Literal["IEEE754_FLOAT32_LE_V1"] = "IEEE754_FLOAT32_LE_V1"
    accumulation: Literal["MATH_FSUM_V1"] = "MATH_FSUM_V1"
    score_quantization_places: Literal[12] = 12
    rounding: Literal["ROUND_HALF_EVEN"] = "ROUND_HALF_EVEN"
    tie_break: Literal[
        "SOURCE_KIND_SOURCE_ID_DOCUMENT_ID_ASC_V1"
    ] = "SOURCE_KIND_SOURCE_ID_DOCUMENT_ID_ASC_V1"
    recency_boost: Literal[False] = False
    implicit_score_threshold: Literal[False] = False


class RetrievalQuerySpec(RetrievalModel):
    query_id: str = ""
    anchor: ExactEvidenceReference
    query_renderer_name: Literal["SOURCE_DERIVED_QUERY_V1"]
    query_renderer_version: Literal["1.0"]
    query_renderer_digest: str = Field(pattern=_DIGEST_PATTERN)
    canonical_query_content_digest: str = Field(pattern=_DIGEST_PATTERN)
    retrieval_as_of: RetrievalUTCDateTime
    metadata_filter: RetrievalMetadataFilter
    top_k: int = Field(ge=1, le=8)
    ranking_policy: RetrievalRankingPolicy

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> RetrievalQuerySpec:
        if self.anchor.available_at > self.retrieval_as_of:
            raise ValueError("query anchor is not causally available")
        _bind_identity(self, "query_id", "retrieval-query")
        return self


class RetrievalIndexMember(RetrievalModel):
    document_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    vector_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    source_kind: RetrievalSourceKind
    source_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)


class RetrievalIndexManifest(RetrievalModel):
    manifest_id: str = ""
    source_cutoff: RetrievalUTCDateTime
    source_adapter_identity: str = Field(min_length=1, max_length=160)
    renderer_identity_digest: str = Field(pattern=_DIGEST_PATTERN)
    provider_model: EmbeddingModelIdentity
    members: tuple[RetrievalIndexMember, ...] = Field(min_length=1)
    revision_selection_policy: Literal[
        "LATEST_CAUSALLY_AVAILABLE_EXPLICIT_CHAIN_V1"
    ] = "LATEST_CAUSALLY_AVAILABLE_EXPLICIT_CHAIN_V1"
    member_count: int = 0
    completeness: Literal[IndexCompleteness.COMPLETE] = IndexCompleteness.COMPLETE

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> RetrievalIndexManifest:
        members = tuple(
            sorted(
                self.members,
                key=lambda item: (
                    item.source_kind.value,
                    item.source_id,
                    item.document_id,
                    item.vector_id,
                ),
            )
        )
        if len({item.document_id for item in members}) != len(members):
            raise ValueError("index document members must be unique")
        if len({item.vector_id for item in members}) != len(members):
            raise ValueError("index vector members must be unique")
        if self.member_count not in {0, len(members)}:
            raise ValueError("index member_count does not match members")
        object.__setattr__(self, "members", members)
        object.__setattr__(self, "member_count", len(members))
        _bind_identity(self, "manifest_id", "retrieval-index")
        return self


class CandidateManifestMember(RetrievalIndexMember):
    pass


class RetrievalCandidateManifest(RetrievalModel):
    candidate_manifest_id: str = ""
    query_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    index_manifest_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    members: tuple[CandidateManifestMember, ...]
    candidate_count: int = 0

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> RetrievalCandidateManifest:
        members = tuple(
            sorted(
                self.members,
                key=lambda item: (
                    item.source_kind.value,
                    item.source_id,
                    item.document_id,
                    item.vector_id,
                ),
            )
        )
        if len({item.document_id for item in members}) != len(members):
            raise ValueError("candidate documents must be unique")
        if self.candidate_count not in {0, len(members)}:
            raise ValueError("candidate_count does not match members")
        object.__setattr__(self, "members", members)
        object.__setattr__(self, "candidate_count", len(members))
        _bind_identity(self, "candidate_manifest_id", "retrieval-candidates")
        return self


class RetrievalRequest(RetrievalModel):
    request_id: str = ""
    query: RetrievalQuerySpec
    query_vector_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    index_manifest_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    candidate_manifest_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    ranking_policy: RetrievalRankingPolicy

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> RetrievalRequest:
        if self.ranking_policy != self.query.ranking_policy:
            raise ValueError("retrieval ranking policy must match query")
        _bind_identity(self, "request_id", "retrieval-request")
        return self


def _canonical_score(value: str) -> str:
    try:
        score = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("similarity score must be decimal") from exc
    if not score.is_finite() or score < -1 or score > 1:
        raise ValueError("similarity score must be finite and between -1 and 1")
    expected = format(score.quantize(Decimal("0.000000000001")), "f")
    if value != expected:
        raise ValueError("similarity score must use canonical 12-place decimal form")
    return value


class RetrievedEvidenceItem(RetrievalModel):
    rank: int = Field(ge=1, le=8)
    similarity: Annotated[str, AfterValidator(_canonical_score)]
    source_kind: RetrievalSourceKind
    source_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    source_digest: str = Field(pattern=_DIGEST_PATTERN)
    document_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    vector_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    available_at: RetrievalUTCDateTime
    evidence_role: Literal["NON_AUTHORITATIVE_RETRIEVAL_EVIDENCE"] = (
        "NON_AUTHORITATIVE_RETRIEVAL_EVIDENCE"
    )


class RetrievalResult(RetrievalModel):
    result_id: str = ""
    request_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    query_vector_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    candidate_manifest_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    selected_items: tuple[RetrievedEvidenceItem, ...]
    candidate_count: int = Field(ge=0)
    selected_count: int = 0
    status: RetrievalResultStatus
    context_bundle_digest: str | None = Field(default=None, pattern=_DIGEST_PATTERN)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> RetrievalResult:
        if self.selected_count not in {0, len(self.selected_items)}:
            raise ValueError("selected_count does not match selected items")
        object.__setattr__(self, "selected_count", len(self.selected_items))
        expected_ranks = tuple(range(1, len(self.selected_items) + 1))
        if tuple(item.rank for item in self.selected_items) != expected_ranks:
            raise ValueError("retrieved item ranks must be contiguous")
        if self.status is RetrievalResultStatus.COMPLETED:
            if not self.selected_items or self.context_bundle_digest is None:
                raise ValueError("completed retrieval requires selected context")
        elif self.selected_items or self.context_bundle_digest is not None:
            raise ValueError("no-match retrieval cannot contain selected context")
        _bind_identity(self, "result_id", "retrieval-result")
        return self


class RetrievalAttemptAudit(RetrievalModel):
    attempt_id: str = ""
    request_id: str = Field(min_length=1, max_length=_ID_MAX_LENGTH)
    attempt_key: str = Field(min_length=1, max_length=160)
    status: RetrievalAttemptStatus
    result_id: str | None = Field(default=None, min_length=1, max_length=_ID_MAX_LENGTH)
    failure: RetrievalFailureMetadata | None = None
    requested_at: RetrievalUTCDateTime
    started_at: RetrievalUTCDateTime
    completed_at: RetrievalUTCDateTime
    local_elapsed_ms: FiniteFloat = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> RetrievalAttemptAudit:
        if not self.requested_at <= self.started_at <= self.completed_at:
            raise ValueError("retrieval attempt timestamps must be ordered")
        success = self.status in {
            RetrievalAttemptStatus.COMPLETED,
            RetrievalAttemptStatus.REUSED,
            RetrievalAttemptStatus.NO_MATCH,
        }
        if success and (self.result_id is None or self.failure is not None):
            raise ValueError("successful retrieval attempt requires result linkage")
        if not success and (self.result_id is not None or self.failure is None):
            raise ValueError("failed retrieval attempt requires failure without result linkage")
        identity = self.model_dump(
            mode="json",
            exclude={
                "attempt_id",
                "requested_at",
                "started_at",
                "completed_at",
                "local_elapsed_ms",
            },
        )
        expected = f"retrieval-attempt-{canonical_hash(identity)[:20]}"
        if self.attempt_id and self.attempt_id != expected:
            raise ValueError("attempt_id does not match retrieval attempt content")
        object.__setattr__(self, "attempt_id", expected)
        return self


__all__ = [
    "CandidateManifestMember",
    "EmbeddingAttemptAudit",
    "EmbeddingAttemptControls",
    "EmbeddingAttemptStatus",
    "EmbeddingInputRole",
    "EmbeddingModelIdentity",
    "EmbeddingPrefixProfileIdentity",
    "EmbeddingProviderKind",
    "EmbeddingRequest",
    "EmbeddingReusePolicy",
    "EmbeddingVectorArtifact",
    "EvidenceLink",
    "EvidenceMetadata",
    "EvidenceRendererIdentity",
    "ExactEvidenceReference",
    "ExperienceEvidenceMetadata",
    "IndexCompleteness",
    "PatternEvidenceMetadata",
    "ProposalEvidenceMetadata",
    "ReflectionEvidenceMetadata",
    "RetrievableEvidenceDocument",
    "RetrievalAttemptAudit",
    "RetrievalAttemptStatus",
    "RetrievalCandidateManifest",
    "RetrievalFailureCode",
    "RetrievalFailureMetadata",
    "RetrievalIndexManifest",
    "RetrievalIndexMember",
    "RetrievalMetadataFilter",
    "RetrievalModel",
    "RetrievalQuerySpec",
    "RetrievalRankingPolicy",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalResultStatus",
    "RetrievalSourceKind",
    "RetrievalUTCDateTime",
    "RetrievedEvidenceItem",
    "canonical_retrieval_bytes",
]
