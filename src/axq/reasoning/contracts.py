"""Strict immutable contracts for offline structured LLM reasoning."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, JsonValue, model_validator

from axq.versioning import canonical_hash

_DIGEST_PATTERN = r"^[0-9a-f]{64}$"
_MAX_CONTEXT_ITEMS = 16
_MAX_CONTEXT_ITEM_CHARACTERS = 2_000
_MAX_CONTEXT_CHARACTERS = 16_000
_FORBIDDEN_CONTEXT_KEYS = {
    "api_key",
    "authorization",
    "credential",
    "credentials",
    "password",
    "secret",
    "token",
}


def _strict_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must use UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must use UTC offset +00:00")
    return value.astimezone(UTC)


ReasoningUTCDateTime = Annotated[datetime, AfterValidator(_strict_utc)]


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("numeric audit value must be finite")
    return value


FiniteFloat = Annotated[float, AfterValidator(_finite)]


def _canonical_json_bytes(value: Any) -> bytes:
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def canonical_reasoning_bytes(value: BaseModel) -> bytes:
    """Return the canonical persisted representation of a reasoning contract."""

    return _canonical_json_bytes(value)


def _canonical_character_count(value: JsonValue) -> int:
    return len(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    )


def _validate_safe_context(value: JsonValue, *, key: str | None = None) -> None:
    if key is not None and key.casefold() in _FORBIDDEN_CONTEXT_KEYS:
        raise ValueError(f"context contains forbidden sensitive key: {key}")
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            _validate_safe_context(child_value, key=child_key)
    elif isinstance(value, list):
        for child in value:
            _validate_safe_context(child)
    elif isinstance(value, str):
        lowered = value.strip().casefold()
        if lowered.startswith(("http://", "https://")):
            raise ValueError("context cannot contain URLs")
        if "\x00" in value:
            raise ValueError("context cannot contain NUL characters")


class ReasoningModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ReasoningTask(StrEnum):
    REFLECTION_EXPLANATION = "REFLECTION_EXPLANATION"


class ReasoningSourceKind(StrEnum):
    DAILY_REFLECTION = "DAILY_REFLECTION"
    WEEKLY_REFLECTION = "WEEKLY_REFLECTION"
    PATTERN = "PATTERN"
    IMPROVEMENT_PROPOSAL = "IMPROVEMENT_PROPOSAL"


class ProviderKind(StrEnum):
    OLLAMA = "OLLAMA"


class UncertaintyLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class LLMReusePolicy(StrEnum):
    NEVER_REUSE = "NEVER_REUSE"
    REUSE_FIRST_COMPLETED_EXACT = "REUSE_FIRST_COMPLETED_EXACT"


class LLMAttemptStatus(StrEnum):
    COMPLETED = "COMPLETED"
    REUSED = "REUSED"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_IDENTITY_MISMATCH = "MODEL_IDENTITY_MISMATCH"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    PROVIDER_ERROR = "PROVIDER_ERROR"


class LLMFailureCode(StrEnum):
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_IDENTITY_MISMATCH = "MODEL_IDENTITY_MISMATCH"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    PROVIDER_ERROR = "PROVIDER_ERROR"


class ProviderModelIdentity(ReasoningModel):
    provider: Literal[ProviderKind.OLLAMA] = ProviderKind.OLLAMA
    adapter_version: str = Field(min_length=1, max_length=100)
    provider_server_version: str = Field(min_length=1, max_length=100)
    configured_model_name: str = Field(min_length=1, max_length=200)
    resolved_model_name: str = Field(min_length=1, max_length=200)
    model_digest: str = Field(pattern=_DIGEST_PATTERN)
    model_family: str | None = Field(default=None, min_length=1, max_length=100)
    quantization: str | None = Field(default=None, min_length=1, max_length=100)


class PromptTemplateIdentity(ReasoningModel):
    task: Literal[ReasoningTask.REFLECTION_EXPLANATION] = (
        ReasoningTask.REFLECTION_EXPLANATION
    )
    template_name: Literal["REFLECTION_EXPLANATION_V1"] = "REFLECTION_EXPLANATION_V1"
    template_version: Literal["1.0"] = "1.0"
    template_digest: str = Field(pattern=_DIGEST_PATTERN)
    response_schema_name: Literal["ReflectionExplanation"] = "ReflectionExplanation"
    response_schema_version: Literal["1.0"] = "1.0"
    response_schema_digest: str = Field(pattern=_DIGEST_PATTERN)


class ReasoningSourceReference(ReasoningModel):
    source_kind: ReasoningSourceKind
    source_id: str = Field(min_length=1, max_length=200)
    source_digest: str = Field(pattern=_DIGEST_PATTERN)


class BoundedReasoningContextItem(ReasoningModel):
    context_id: str = Field(min_length=1, max_length=200)
    source: ReasoningSourceReference
    context_kind: str = Field(min_length=1, max_length=100)
    content: JsonValue
    content_digest: str = Field(pattern=_DIGEST_PATTERN)

    @model_validator(mode="after")
    def validate_content(self) -> BoundedReasoningContextItem:
        _validate_safe_context(self.content)
        characters = _canonical_character_count(self.content)
        if characters > _MAX_CONTEXT_ITEM_CHARACTERS:
            raise ValueError("context item cannot exceed 2,000 canonical characters")
        expected = canonical_hash(self.content)
        if self.content_digest != expected:
            raise ValueError("content_digest does not match canonical context content")
        return self


class LLMGenerationPolicy(ReasoningModel):
    temperature: FiniteFloat = Field(default=0.0, ge=0.0, le=2.0)
    seed: int = Field(default=0, ge=0)
    max_output_tokens: int = Field(default=384, ge=1, le=8_192)
    structured_output: Literal[True] = True
    stream: Literal[False] = False
    think: Literal[False] = False
    response_byte_limit: int = Field(default=16_384, ge=1, le=1_048_576)
    prompt_context_budget_version: Literal["bounded-context-v1"] = "bounded-context-v1"


class ReflectionExplanationInput(ReasoningModel):
    source_references: tuple[ReasoningSourceReference, ...] = Field(min_length=1)
    context: tuple[BoundedReasoningContextItem, ...] = Field(min_length=1)
    generation: LLMGenerationPolicy = LLMGenerationPolicy()

    @model_validator(mode="after")
    def normalize_and_validate(self) -> ReflectionExplanationInput:
        sources, context = _normalize_sources_and_context(
            self.source_references,
            self.context,
        )
        object.__setattr__(self, "source_references", sources)
        object.__setattr__(self, "context", context)
        return self


def _normalize_sources_and_context(
    source_references: tuple[ReasoningSourceReference, ...],
    context: tuple[BoundedReasoningContextItem, ...],
) -> tuple[tuple[ReasoningSourceReference, ...], tuple[BoundedReasoningContextItem, ...]]:
    if len(context) > _MAX_CONTEXT_ITEMS:
        raise ValueError("request cannot contain more than 16 context items")
    sources = tuple(
        sorted(
            source_references,
            key=lambda item: (item.source_kind.value, item.source_id, item.source_digest),
        )
    )
    contexts = tuple(sorted(context, key=lambda item: item.context_id))
    if len({item.source_id for item in sources}) != len(sources):
        raise ValueError("source reference IDs must be unique")
    if len({item.context_id for item in contexts}) != len(contexts):
        raise ValueError("context item IDs must be unique")
    source_keys = {
        (item.source_kind, item.source_id, item.source_digest)
        for item in sources
    }
    if any(
        (item.source.source_kind, item.source.source_id, item.source.source_digest)
        not in source_keys
        for item in contexts
    ):
        raise ValueError("every context item must reference an exact request source")
    total_characters = sum(_canonical_character_count(item.content) for item in contexts)
    if total_characters > _MAX_CONTEXT_CHARACTERS:
        raise ValueError("request context cannot exceed 16,000 canonical characters")
    return sources, contexts


class LLMRequestEnvelope(ReasoningModel):
    request_id: str = ""
    task: Literal[ReasoningTask.REFLECTION_EXPLANATION] = (
        ReasoningTask.REFLECTION_EXPLANATION
    )
    provider_model: ProviderModelIdentity
    prompt: PromptTemplateIdentity
    source_references: tuple[ReasoningSourceReference, ...] = Field(min_length=1)
    context: tuple[BoundedReasoningContextItem, ...] = Field(min_length=1)
    generation: LLMGenerationPolicy = LLMGenerationPolicy()

    @model_validator(mode="after")
    def normalize_validate_and_bind_identity(self) -> LLMRequestEnvelope:
        if self.prompt.task is not self.task:
            raise ValueError("prompt task must match request task")
        sources, context = _normalize_sources_and_context(
            self.source_references,
            self.context,
        )
        object.__setattr__(self, "source_references", sources)
        object.__setattr__(self, "context", context)
        identity = self.model_dump(mode="json", exclude={"request_id"})
        expected = f"llm-request-{canonical_hash(identity)[:20]}"
        if self.request_id and self.request_id != expected:
            raise ValueError("request_id does not match request content")
        object.__setattr__(self, "request_id", expected)
        return self


class UncertaintyAssessment(ReasoningModel):
    level: UncertaintyLevel
    basis: str = Field(min_length=1, max_length=300)


class ReflectionExplanation(ReasoningModel):
    explanation: str = Field(min_length=1, max_length=1_000)
    cited_evidence_ids: tuple[str, ...] = Field(min_length=1, max_length=32)
    hypothesis: str = Field(min_length=1, max_length=500)
    uncertainty: UncertaintyAssessment
    suggested_next_investigation: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def normalize_citations(self) -> ReflectionExplanation:
        citations = tuple(sorted(set(self.cited_evidence_ids)))
        if any(not item for item in citations):
            raise ValueError("cited evidence IDs cannot be empty")
        object.__setattr__(self, "cited_evidence_ids", citations)
        return self


class LLMStructuredResponseArtifact(ReasoningModel):
    response_id: str = ""
    request_id: str = Field(min_length=1)
    provider_model: ProviderModelIdentity
    output: ReflectionExplanation
    structured_response_digest: str = Field(pattern=_DIGEST_PATTERN)

    @classmethod
    def from_request(
        cls,
        *,
        request: LLMRequestEnvelope,
        output: ReflectionExplanation,
    ) -> LLMStructuredResponseArtifact:
        allowed_ids = {
            *(item.source_id for item in request.source_references),
            *(item.context_id for item in request.context),
        }
        if not set(output.cited_evidence_ids).issubset(allowed_ids):
            raise ValueError("citations must reference allowed evidence IDs")
        return cls(
            request_id=request.request_id,
            provider_model=request.provider_model,
            output=output,
            structured_response_digest=canonical_hash(output.model_dump(mode="json")),
        )

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> LLMStructuredResponseArtifact:
        expected_digest = canonical_hash(self.output.model_dump(mode="json"))
        if self.structured_response_digest != expected_digest:
            raise ValueError("structured_response_digest does not match response output")
        identity = self.model_dump(mode="json", exclude={"response_id"})
        expected = f"llm-response-{canonical_hash(identity)[:20]}"
        if self.response_id and self.response_id != expected:
            raise ValueError("response_id does not match response content")
        object.__setattr__(self, "response_id", expected)
        return self


class LLMFailureMetadata(ReasoningModel):
    code: LLMFailureCode
    message: str = Field(min_length=1, max_length=500)
    http_status: int | None = Field(default=None, ge=100, le=599)
    raw_response_digest: str | None = Field(default=None, pattern=_DIGEST_PATTERN)
    raw_response_bytes: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_raw_response_metadata(self) -> LLMFailureMetadata:
        if (self.raw_response_digest is None) != (self.raw_response_bytes is None):
            raise ValueError("raw response digest and byte count must be supplied together")
        return self


class LLMExecutionAttemptAudit(ReasoningModel):
    attempt_id: str = ""
    request_id: str = Field(min_length=1)
    attempt_key: str = Field(min_length=1, max_length=200)
    status: LLMAttemptStatus
    provider_model: ProviderModelIdentity
    response_id: str | None = None
    failure: LLMFailureMetadata | None = None
    requested_at: ReasoningUTCDateTime
    started_at: ReasoningUTCDateTime
    completed_at: ReasoningUTCDateTime
    timeout_seconds: FiniteFloat = Field(gt=0.0, le=3_600.0)
    endpoint: str = Field(min_length=1, max_length=300)
    prompt_token_count: int | None = Field(default=None, ge=0)
    output_token_count: int | None = Field(default=None, ge=0)
    provider_total_duration_ns: int | None = Field(default=None, ge=0)
    provider_load_duration_ns: int | None = Field(default=None, ge=0)
    provider_prompt_duration_ns: int | None = Field(default=None, ge=0)
    provider_output_duration_ns: int | None = Field(default=None, ge=0)
    local_elapsed_ms: FiniteFloat = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_semantics_and_bind_identity(self) -> LLMExecutionAttemptAudit:
        if not self.requested_at <= self.started_at <= self.completed_at:
            raise ValueError("requested_at, started_at, and completed_at must be ordered")
        successful = self.status in {LLMAttemptStatus.COMPLETED, LLMAttemptStatus.REUSED}
        if successful:
            if self.response_id is None:
                raise ValueError("successful attempt requires response_id")
            if self.failure is not None:
                raise ValueError("successful attempt cannot contain failure")
        else:
            if self.response_id is not None:
                raise ValueError("failed attempt cannot reference response")
            if self.failure is None:
                raise ValueError("failed attempt requires failure metadata")
            if self.failure.code.value != self.status.value:
                raise ValueError("failure code must match attempt status")
        identity = self.model_dump(
            mode="json",
            exclude={
                "attempt_id",
                "requested_at",
                "started_at",
                "completed_at",
                "timeout_seconds",
                "endpoint",
                "prompt_token_count",
                "output_token_count",
                "provider_total_duration_ns",
                "provider_load_duration_ns",
                "provider_prompt_duration_ns",
                "provider_output_duration_ns",
                "local_elapsed_ms",
            },
        )
        expected = f"llm-attempt-{canonical_hash(identity)[:20]}"
        if self.attempt_id and self.attempt_id != expected:
            raise ValueError("attempt_id does not match attempt content")
        object.__setattr__(self, "attempt_id", expected)
        return self


class ReasoningRunResult(ReasoningModel):
    request_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    status: LLMAttemptStatus
    response_id: str | None = None
    reused: bool = False
    failure: LLMFailureMetadata | None = None

    @model_validator(mode="after")
    def validate_result(self) -> ReasoningRunResult:
        if self.reused != (self.status is LLMAttemptStatus.REUSED):
            raise ValueError("reused flag must match REUSED status")
        successful = self.status in {LLMAttemptStatus.COMPLETED, LLMAttemptStatus.REUSED}
        if successful != (self.response_id is not None):
            raise ValueError("successful run must contain response_id")
        if successful != (self.failure is None):
            raise ValueError("failure metadata must match run status")
        return self
