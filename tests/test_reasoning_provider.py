"""Tests for the provider-neutral reasoning protocol and result contracts."""

from __future__ import annotations

from hashlib import sha256

import pytest
from pydantic import ValidationError

from axq.reasoning.contracts import LLMAttemptStatus, LLMFailureCode
from axq.reasoning.prompts import render_reflection_explanation_prompt
from axq.reasoning.provider import (
    LLMProvider,
    LLMProviderError,
    ProviderAttemptControls,
    ProviderCompletion,
    ProviderUsage,
)
from tests.reasoning_test_support import provider_identity, request_envelope


class CompatibleProvider:
    def verify_identity(self, expected: object, *, timeout_seconds: float) -> object:
        return expected

    def complete(
        self,
        request: object,
        prompt: object,
        *,
        controls: ProviderAttemptControls,
    ) -> ProviderCompletion:
        raw = b'{"explanation":"bounded"}'
        return ProviderCompletion(
            raw_content=raw.decode("ascii"),
            raw_response_digest=sha256(raw).hexdigest(),
            raw_response_bytes=len(raw),
            usage=ProviderUsage(prompt_token_count=10, output_token_count=4),
        )


def test_provider_protocol_is_structural_and_extensible() -> None:
    provider = CompatibleProvider()
    assert isinstance(provider, LLMProvider)
    assert provider.verify_identity(provider_identity(), timeout_seconds=5.0) == provider_identity()


def test_provider_completion_binds_raw_digest_and_safe_usage() -> None:
    raw = b'{"explanation":"bounded"}'
    completion = ProviderCompletion(
        raw_content=raw.decode("ascii"),
        raw_response_digest=sha256(raw).hexdigest(),
        raw_response_bytes=len(raw),
        usage=ProviderUsage(
            prompt_token_count=10,
            output_token_count=4,
            total_duration_ns=1_000,
            load_duration_ns=100,
            prompt_duration_ns=300,
            output_duration_ns=600,
        ),
    )
    assert completion.raw_response_bytes == len(raw)
    assert completion.unexpected_thinking is False
    assert completion.usage.output_token_count == 4

    with pytest.raises(ValidationError, match="raw_response_digest"):
        ProviderCompletion(
            raw_content=raw.decode("ascii"),
            raw_response_digest="f" * 64,
            raw_response_bytes=len(raw),
        )


def test_provider_completion_has_no_hidden_reasoning_field() -> None:
    assert set(ProviderCompletion.model_fields) == {
        "schema_version",
        "raw_content",
        "raw_response_digest",
        "raw_response_bytes",
        "usage",
        "unexpected_thinking",
    }


def test_attempt_controls_are_strict_and_bounded() -> None:
    controls = ProviderAttemptControls(
        timeout_seconds=30.0,
        response_byte_limit=16_384,
    )
    assert controls.timeout_seconds == 30.0
    with pytest.raises(ValidationError):
        ProviderAttemptControls(timeout_seconds=0.0, response_byte_limit=16_384)
    with pytest.raises(ValidationError):
        ProviderAttemptControls(
            timeout_seconds=30.0,
            response_byte_limit=16_384,
            endpoint="not-provider-neutral",
        )


def test_provider_error_exposes_only_typed_safe_metadata() -> None:
    error = LLMProviderError(
        status=LLMAttemptStatus.HTTP_ERROR,
        code=LLMFailureCode.HTTP_ERROR,
        message="Ollama returned an HTTP error.",
        http_status=500,
        raw_response_digest="d" * 64,
        raw_response_bytes=24,
    )
    assert error.status is LLMAttemptStatus.HTTP_ERROR
    assert error.failure.code is LLMFailureCode.HTTP_ERROR
    assert "traceback" not in str(error).casefold()
    assert not hasattr(error, "raw_response")


def test_compatible_provider_can_consume_neutral_request_and_prompt() -> None:
    request = request_envelope()
    prompt_input = request.model_dump(
        include={"source_references", "context", "generation"}
    )
    from axq.reasoning.contracts import ReflectionExplanationInput

    prompt = render_reflection_explanation_prompt(
        ReflectionExplanationInput.model_validate(prompt_input)
    )
    provider = CompatibleProvider()
    completion = provider.complete(
        request,
        prompt,
        controls=ProviderAttemptControls(
            timeout_seconds=30.0,
            response_byte_limit=request.generation.response_byte_limit,
        ),
    )
    assert completion.raw_content == '{"explanation":"bounded"}'
