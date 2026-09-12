"""Focused tests for the loopback-only native Ollama adapter."""

from __future__ import annotations

import json
from collections.abc import Mapping
from io import BytesIO
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from axq.reasoning.contracts import LLMAttemptStatus
from axq.reasoning.ollama import (
    OllamaHTTPTransport,
    OllamaProvider,
    validate_loopback_ollama_url,
)
from axq.reasoning.prompts import render_reflection_explanation_prompt
from axq.reasoning.provider import (
    LLMInvalidProviderResponseError,
    LLMModelIdentityMismatchError,
    LLMModelUnavailableError,
    LLMProviderConnectionError,
    LLMProviderError,
    LLMProviderTimeoutError,
    ProviderAttemptControls,
)
from tests.reasoning_test_support import provider_identity, request_envelope


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class FakeOllamaTransport:
    def __init__(self, responses: Mapping[tuple[str, str], bytes]) -> None:
        self.responses = dict(responses)
        self.calls: list[dict[str, object]] = []

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, object] | None,
        timeout_seconds: float,
        response_byte_limit: int,
    ) -> bytes:
        self.calls.append(
            {
                "method": method,
                "path": path,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
                "response_byte_limit": response_byte_limit,
            }
        )
        return self.responses[(method, path)]


def _identity_responses(
    *,
    server_version: str = "0.12.6",
    model_name: str = "qwen3:8b",
    digest: str = "a" * 64,
    duplicate: bool = False,
) -> dict[tuple[str, str], bytes]:
    model = {
        "name": model_name,
        "model": model_name,
        "digest": digest,
        "modified_at": "2026-09-12T00:00:00Z",
        "size": 5_000_000_000,
        "details": {
            "format": "gguf",
            "family": "qwen3",
            "families": ["qwen3"],
            "parameter_size": "8B",
            "quantization_level": "Q4_K_M",
        },
    }
    models = [model, dict(model)] if duplicate else [model]
    return {
        ("GET", "/api/version"): _json_bytes({"version": server_version}),
        ("GET", "/api/tags"): _json_bytes({"models": models}),
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("http://localhost:11434", "http://localhost:11434"),
        ("http://127.0.0.1:11434/", "http://127.0.0.1:11434"),
        ("http://[::1]:11434", "http://[::1]:11434"),
    ],
)
def test_loopback_endpoint_is_normalized(value: str, expected: str) -> None:
    assert validate_loopback_ollama_url(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "https://ollama.com",
        "http://192.168.1.20:11434",
        "http://example.com:11434",
        "http://user:secret@localhost:11434",
        "http://localhost:11434/api",
        "http://localhost:11434?token=secret",
        "file:///tmp/ollama.sock",
    ],
)
def test_non_loopback_or_unsafe_endpoint_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="loopback|credentials|path|query|HTTP"):
        validate_loopback_ollama_url(value)


def test_exact_model_identity_is_verified_from_version_and_tags() -> None:
    transport = FakeOllamaTransport(_identity_responses())
    provider = OllamaProvider("http://127.0.0.1:11434", transport=transport)

    observed = provider.verify_identity(provider_identity(), timeout_seconds=5.0)

    assert observed == provider_identity()
    assert [(call["method"], call["path"]) for call in transport.calls] == [
        ("GET", "/api/version"),
        ("GET", "/api/tags"),
    ]


@pytest.mark.parametrize(
    ("responses", "expected_error"),
    [
        (_identity_responses(server_version="0.12.7"), LLMModelIdentityMismatchError),
        (_identity_responses(digest="b" * 64), LLMModelIdentityMismatchError),
        (_identity_responses(model_name="qwen3:14b"), LLMModelUnavailableError),
        (_identity_responses(duplicate=True), LLMModelIdentityMismatchError),
    ],
)
def test_identity_failure_is_fail_closed_before_generation(
    responses: Mapping[tuple[str, str], bytes],
    expected_error: type[LLMProviderError],
) -> None:
    transport = FakeOllamaTransport(responses)
    provider = OllamaProvider("http://localhost:11434", transport=transport)

    with pytest.raises(expected_error):
        provider.verify_identity(provider_identity(), timeout_seconds=5.0)

    assert all(call["path"] != "/api/chat" for call in transport.calls)


def test_chat_request_is_non_streaming_non_thinking_and_schema_constrained() -> None:
    request = request_envelope()
    prompt_input = {
        "source_references": request.source_references,
        "context": request.context,
        "generation": request.generation,
    }
    from axq.reasoning.contracts import ReflectionExplanationInput

    prompt = render_reflection_explanation_prompt(
        ReflectionExplanationInput.model_validate(prompt_input)
    )
    content = json.dumps(
        {
            "schema_version": "1.0",
            "explanation": "The bounded evidence indicates repeated session weakness.",
            "cited_evidence_ids": ["context-weekly-summary"],
            "hypothesis": "The weakness may be conditional on the London session.",
            "uncertainty": {
                "schema_version": "1.0",
                "level": "MEDIUM",
                "basis": "The evidence covers only two complete weeks.",
            },
            "suggested_next_investigation": "Compare development periods by session.",
        },
        separators=(",", ":"),
    )
    responses = _identity_responses() | {
        ("POST", "/api/chat"): _json_bytes(
            {
                "model": "qwen3:8b",
                "created_at": "2026-09-12T00:00:00Z",
                "message": {
                    "role": "assistant",
                    "content": content,
                    "thinking": "private model reasoning that must be discarded",
                },
                "done": True,
                "done_reason": "stop",
                "total_duration": 8_000,
                "load_duration": 1_000,
                "prompt_eval_count": 120,
                "prompt_eval_duration": 2_000,
                "eval_count": 42,
                "eval_duration": 5_000,
            }
        )
    }
    transport = FakeOllamaTransport(responses)
    provider = OllamaProvider("http://127.0.0.1:11434", transport=transport)

    completion = provider.complete(
        request,
        prompt,
        controls=ProviderAttemptControls(
            timeout_seconds=30.0,
            response_byte_limit=16_384,
        ),
    )

    chat_call = transport.calls[-1]
    assert chat_call == {
        "method": "POST",
        "path": "/api/chat",
        "payload": {
            "model": "qwen3:8b",
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
            "stream": False,
            "think": False,
            "format": prompt.response_schema,
            "options": {"temperature": 0.0, "seed": 17, "num_predict": 384},
        },
        "timeout_seconds": 30.0,
        "response_byte_limit": 16_384,
    }
    assert completion.raw_content == content
    assert completion.unexpected_thinking is True
    assert "private model reasoning" not in completion.model_dump_json()
    assert completion.usage.prompt_token_count == 120
    assert completion.usage.output_token_count == 42
    assert completion.usage.total_duration_ns == 8_000
    assert completion.usage.load_duration_ns == 1_000
    assert completion.usage.prompt_duration_ns == 2_000
    assert completion.usage.output_duration_ns == 5_000


@pytest.mark.parametrize(
    "payload",
    [
        b"not-json",
        _json_bytes({"model": "qwen3:8b", "done": False, "message": {"content": "{}"}}),
        _json_bytes({"model": "wrong:8b", "done": True, "message": {"content": "{}"}}),
        _json_bytes({"model": "qwen3:8b", "done": True, "message": {"content": ""}}),
    ],
)
def test_invalid_chat_response_maps_to_safe_typed_failure(payload: bytes) -> None:
    transport = FakeOllamaTransport({("POST", "/api/chat"): payload})
    provider = OllamaProvider("http://localhost:11434", transport=transport)
    request = request_envelope()
    from axq.reasoning.contracts import ReflectionExplanationInput

    prompt = render_reflection_explanation_prompt(
        ReflectionExplanationInput(
            source_references=request.source_references,
            context=request.context,
            generation=request.generation,
        )
    )
    with pytest.raises(LLMInvalidProviderResponseError) as captured:
        provider.complete(
            request,
            prompt,
            controls=ProviderAttemptControls(
                timeout_seconds=30.0,
                response_byte_limit=16_384,
            ),
        )
    assert captured.value.status is LLMAttemptStatus.INVALID_RESPONSE
    assert payload.decode("utf-8", errors="replace") not in str(captured.value)


class _HTTPResponse:
    def __init__(self, body: bytes) -> None:
        self._body = BytesIO(body)

    def __enter__(self) -> _HTTPResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, limit: int = -1) -> bytes:
        return self._body.read(limit)


def test_standard_library_transport_enforces_response_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "axq.reasoning.ollama.urlopen",
        lambda *_args, **_kwargs: _HTTPResponse(b"x" * 9),
    )
    transport = OllamaHTTPTransport("http://127.0.0.1:11434")
    with pytest.raises(LLMInvalidProviderResponseError) as captured:
        transport.request(
            "GET",
            "/api/version",
            payload=None,
            timeout_seconds=3.0,
            response_byte_limit=8,
        )
    assert captured.value.failure.raw_response_bytes == 9


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (TimeoutError(), LLMProviderTimeoutError),
        (URLError(TimeoutError()), LLMProviderTimeoutError),
        (URLError("connection refused"), LLMProviderConnectionError),
        (
            HTTPError(
                "http://127.0.0.1:11434/api/chat",
                500,
                "error",
                hdrs=None,
                fp=BytesIO(b'{"error":"internal secret detail"}'),
            ),
            LLMProviderError,
        ),
    ],
)
def test_standard_library_transport_maps_safe_failures(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected: type[Exception],
) -> None:
    def fail(*_args: object, **_kwargs: object) -> Any:
        raise error

    monkeypatch.setattr("axq.reasoning.ollama.urlopen", fail)
    transport = OllamaHTTPTransport("http://localhost:11434")
    with pytest.raises(expected) as captured:
        transport.request(
            "GET",
            "/api/version",
            payload=None,
            timeout_seconds=3.0,
            response_byte_limit=1_024,
        )
    assert "internal secret detail" not in str(captured.value)
