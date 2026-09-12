"""Provider-neutral protocols and in-memory completion contracts."""

from __future__ import annotations

from hashlib import sha256
from typing import Protocol, runtime_checkable

from pydantic import Field, model_validator

from axq.reasoning.contracts import (
    FiniteFloat,
    LLMAttemptStatus,
    LLMFailureCode,
    LLMFailureMetadata,
    LLMRequestEnvelope,
    ProviderModelIdentity,
    ReasoningModel,
)
from axq.reasoning.prompts import RenderedReasoningPrompt

_DIGEST_PATTERN = r"^[0-9a-f]{64}$"


class ProviderUsage(ReasoningModel):
    """Safe provider usage and duration metadata."""

    prompt_token_count: int | None = Field(default=None, ge=0)
    output_token_count: int | None = Field(default=None, ge=0)
    total_duration_ns: int | None = Field(default=None, ge=0)
    load_duration_ns: int | None = Field(default=None, ge=0)
    prompt_duration_ns: int | None = Field(default=None, ge=0)
    output_duration_ns: int | None = Field(default=None, ge=0)


class ProviderAttemptControls(ReasoningModel):
    """Provider-neutral operational limits for one invocation."""

    timeout_seconds: FiniteFloat = Field(gt=0.0, le=3_600.0)
    response_byte_limit: int = Field(ge=1, le=1_048_576)


class ProviderCompletion(ReasoningModel):
    """Ephemeral provider output awaiting strict task-schema validation."""

    raw_content: str = Field(min_length=1)
    raw_response_digest: str = Field(pattern=_DIGEST_PATTERN)
    raw_response_bytes: int = Field(ge=1)
    usage: ProviderUsage = ProviderUsage()
    unexpected_thinking: bool = False

    @model_validator(mode="after")
    def validate_raw_content(self) -> ProviderCompletion:
        raw = self.raw_content.encode("utf-8")
        if self.raw_response_bytes != len(raw):
            raise ValueError("raw_response_bytes does not match raw content")
        if self.raw_response_digest != sha256(raw).hexdigest():
            raise ValueError("raw_response_digest does not match raw content")
        return self


@runtime_checkable
class LLMProvider(Protocol):
    """Provider-neutral boundary for exact identity verification and completion."""

    def verify_identity(
        self,
        expected: ProviderModelIdentity,
        *,
        timeout_seconds: float,
    ) -> ProviderModelIdentity: ...

    def complete(
        self,
        request: LLMRequestEnvelope,
        prompt: RenderedReasoningPrompt,
        *,
        controls: ProviderAttemptControls,
    ) -> ProviderCompletion: ...


class LLMProviderError(Exception):
    """Typed provider failure carrying only safe audit metadata."""

    def __init__(
        self,
        *,
        status: LLMAttemptStatus,
        code: LLMFailureCode,
        message: str,
        http_status: int | None = None,
        raw_response_digest: str | None = None,
        raw_response_bytes: int | None = None,
    ) -> None:
        if status in {LLMAttemptStatus.COMPLETED, LLMAttemptStatus.REUSED}:
            raise ValueError("provider error requires a failure status")
        self.status = status
        self.failure = LLMFailureMetadata(
            code=code,
            message=message,
            http_status=http_status,
            raw_response_digest=raw_response_digest,
            raw_response_bytes=raw_response_bytes,
        )
        super().__init__(self.failure.message)


class LLMProviderTimeoutError(LLMProviderError):
    def __init__(self, message: str = "Provider request timed out.") -> None:
        super().__init__(
            status=LLMAttemptStatus.TIMEOUT,
            code=LLMFailureCode.TIMEOUT,
            message=message,
        )


class LLMProviderConnectionError(LLMProviderError):
    def __init__(self, message: str = "Provider connection failed.") -> None:
        super().__init__(
            status=LLMAttemptStatus.CONNECTION_ERROR,
            code=LLMFailureCode.CONNECTION_ERROR,
            message=message,
        )


class LLMModelUnavailableError(LLMProviderError):
    def __init__(self, message: str = "Requested provider model is unavailable.") -> None:
        super().__init__(
            status=LLMAttemptStatus.MODEL_UNAVAILABLE,
            code=LLMFailureCode.MODEL_UNAVAILABLE,
            message=message,
        )


class LLMModelIdentityMismatchError(LLMProviderError):
    def __init__(self, message: str = "Provider model identity does not match request.") -> None:
        super().__init__(
            status=LLMAttemptStatus.MODEL_IDENTITY_MISMATCH,
            code=LLMFailureCode.MODEL_IDENTITY_MISMATCH,
            message=message,
        )


class LLMInvalidProviderResponseError(LLMProviderError):
    def __init__(
        self,
        message: str = "Provider returned an invalid response.",
        *,
        raw_response_digest: str | None = None,
        raw_response_bytes: int | None = None,
    ) -> None:
        super().__init__(
            status=LLMAttemptStatus.INVALID_RESPONSE,
            code=LLMFailureCode.INVALID_RESPONSE,
            message=message,
            raw_response_digest=raw_response_digest,
            raw_response_bytes=raw_response_bytes,
        )
