"""Loopback-only native HTTP adapter for a local Ollama provider."""

from __future__ import annotations

import ipaddress
import json
from collections.abc import Mapping
from hashlib import sha256
from typing import Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from axq.reasoning.contracts import (
    LLMAttemptStatus,
    LLMFailureCode,
    LLMRequestEnvelope,
    ProviderModelIdentity,
)
from axq.reasoning.prompts import RenderedReasoningPrompt
from axq.reasoning.provider import (
    LLMInvalidProviderResponseError,
    LLMModelIdentityMismatchError,
    LLMModelUnavailableError,
    LLMProviderConnectionError,
    LLMProviderError,
    LLMProviderTimeoutError,
    ProviderAttemptControls,
    ProviderCompletion,
    ProviderUsage,
)

_IDENTITY_RESPONSE_LIMIT = 1_048_576


def validate_loopback_ollama_url(value: str) -> str:
    """Validate and normalize a V1 local Ollama endpoint."""

    parsed = urlsplit(value)
    if parsed.scheme.casefold() != "http":
        raise ValueError("Ollama V1 endpoint must use HTTP")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Ollama V1 endpoint cannot contain credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("Ollama V1 endpoint cannot contain query or fragment data")
    if parsed.path not in {"", "/"}:
        raise ValueError("Ollama V1 endpoint cannot contain an API path")
    hostname = parsed.hostname
    if hostname is None:
        raise ValueError("Ollama V1 endpoint requires a loopback host")
    loopback = hostname.casefold() == "localhost"
    if not loopback:
        try:
            loopback = ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            loopback = False
    if not loopback:
        raise ValueError("Ollama V1 endpoint must use a loopback host")
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("Ollama V1 endpoint has an invalid port") from error
    host = f"[{hostname}]" if ":" in hostname else hostname.casefold()
    netloc = host if port is None else f"{host}:{port}"
    return urlunsplit(("http", netloc, "", "", ""))


class OllamaTransport(Protocol):
    """Injectable byte transport used by the Ollama provider."""

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, object] | None,
        timeout_seconds: float,
        response_byte_limit: int,
    ) -> bytes: ...


class OllamaHTTPTransport:
    """Standard-library HTTP transport restricted to a loopback endpoint."""

    def __init__(self, endpoint: str) -> None:
        self.endpoint = validate_loopback_ollama_url(endpoint)

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, object] | None,
        timeout_seconds: float,
        response_byte_limit: int,
    ) -> bytes:
        if method not in {"GET", "POST"}:
            raise ValueError("Ollama transport supports only GET and POST")
        if not path.startswith("/api/") or "?" in path or "#" in path:
            raise ValueError("Ollama transport requires a fixed API path")
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.endpoint}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
                body = cast(bytes, response.read(response_byte_limit + 1))
        except HTTPError as error:
            body = error.read(response_byte_limit + 1)
            digest = sha256(body).hexdigest() if body else None
            raise LLMProviderError(
                status=LLMAttemptStatus.HTTP_ERROR,
                code=LLMFailureCode.HTTP_ERROR,
                message=f"Ollama HTTP request failed with status {error.code}.",
                http_status=error.code,
                raw_response_digest=digest,
                raw_response_bytes=len(body) if body else None,
            ) from None
        except TimeoutError as error:
            raise LLMProviderTimeoutError() from error
        except URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise LLMProviderTimeoutError() from error
            raise LLMProviderConnectionError() from error
        except OSError as error:
            raise LLMProviderConnectionError() from error
        if len(body) > response_byte_limit:
            raise LLMInvalidProviderResponseError(
                "Provider response exceeded the configured byte limit.",
                raw_response_digest=sha256(body).hexdigest(),
                raw_response_bytes=len(body),
            )
        return body


def _json_object(body: bytes, *, description: str) -> dict[str, Any]:
    try:
        decoded = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LLMInvalidProviderResponseError(
            f"Ollama returned invalid JSON for {description}.",
            raw_response_digest=sha256(body).hexdigest(),
            raw_response_bytes=len(body),
        ) from error
    if not isinstance(decoded, dict):
        raise LLMInvalidProviderResponseError(
            f"Ollama returned a non-object payload for {description}.",
            raw_response_digest=sha256(body).hexdigest(),
            raw_response_bytes=len(body),
        )
    return decoded


def _bounded_body(body: bytes, limit: int) -> bytes:
    if len(body) > limit:
        raise LLMInvalidProviderResponseError(
            "Provider response exceeded the configured byte limit.",
            raw_response_digest=sha256(body).hexdigest(),
            raw_response_bytes=len(body),
        )
    return body


class OllamaProvider:
    """Provider implementation for one exact local Ollama model."""

    def __init__(
        self,
        endpoint: str,
        *,
        transport: OllamaTransport | None = None,
    ) -> None:
        self.endpoint = validate_loopback_ollama_url(endpoint)
        self._transport = transport or OllamaHTTPTransport(self.endpoint)

    def verify_identity(
        self,
        expected: ProviderModelIdentity,
        *,
        timeout_seconds: float,
    ) -> ProviderModelIdentity:
        version_body = self._transport.request(
            "GET",
            "/api/version",
            payload=None,
            timeout_seconds=timeout_seconds,
            response_byte_limit=_IDENTITY_RESPONSE_LIMIT,
        )
        version = _json_object(version_body, description="version")
        if version.get("version") != expected.provider_server_version:
            raise LLMModelIdentityMismatchError("Ollama server version does not match request.")

        tags_body = self._transport.request(
            "GET",
            "/api/tags",
            payload=None,
            timeout_seconds=timeout_seconds,
            response_byte_limit=_IDENTITY_RESPONSE_LIMIT,
        )
        tags = _json_object(tags_body, description="model tags")
        models = tags.get("models")
        if not isinstance(models, list):
            raise LLMInvalidProviderResponseError("Ollama model tags payload is invalid.")
        exact = [
            item
            for item in models
            if isinstance(item, dict)
            and item.get("name") == expected.configured_model_name
            and item.get("model") == expected.resolved_model_name
        ]
        if not exact:
            raise LLMModelUnavailableError()
        if len(exact) != 1:
            raise LLMModelIdentityMismatchError("Ollama model identity is ambiguous.")
        model = exact[0]
        if model.get("digest") != expected.model_digest:
            raise LLMModelIdentityMismatchError("Ollama model digest does not match request.")
        details = model.get("details")
        if not isinstance(details, dict):
            raise LLMInvalidProviderResponseError("Ollama model details payload is invalid.")
        if expected.model_family is not None and details.get("family") != expected.model_family:
            raise LLMModelIdentityMismatchError("Ollama model family does not match request.")
        if (
            expected.quantization is not None
            and details.get("quantization_level") != expected.quantization
        ):
            raise LLMModelIdentityMismatchError("Ollama quantization does not match request.")
        return expected

    def complete(
        self,
        request: LLMRequestEnvelope,
        prompt: RenderedReasoningPrompt,
        *,
        controls: ProviderAttemptControls,
    ) -> ProviderCompletion:
        payload: dict[str, object] = {
            "model": request.provider_model.resolved_model_name,
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
            "stream": False,
            "think": False,
            "format": prompt.response_schema,
            "options": {
                "temperature": request.generation.temperature,
                "seed": request.generation.seed,
                "num_predict": request.generation.max_output_tokens,
            },
        }
        body = self._transport.request(
            "POST",
            "/api/chat",
            payload=payload,
            timeout_seconds=controls.timeout_seconds,
            response_byte_limit=controls.response_byte_limit,
        )
        body = _bounded_body(body, controls.response_byte_limit)
        response = _json_object(body, description="chat completion")
        if response.get("model") != request.provider_model.resolved_model_name:
            raise LLMInvalidProviderResponseError("Ollama chat model does not match request.")
        if response.get("done") is not True:
            raise LLMInvalidProviderResponseError("Ollama chat response is not terminal.")
        message = response.get("message")
        if not isinstance(message, dict):
            raise LLMInvalidProviderResponseError("Ollama chat message is missing.")
        if message.get("role", "assistant") != "assistant":
            raise LLMInvalidProviderResponseError("Ollama chat message role is invalid.")
        raw_content = message.get("content")
        if not isinstance(raw_content, str) or not raw_content:
            raise LLMInvalidProviderResponseError("Ollama chat content is missing.")
        raw = raw_content.encode("utf-8")
        unexpected_thinking = bool(message.get("thinking") or response.get("thinking"))
        usage = ProviderUsage(
            prompt_token_count=_optional_nonnegative_int(response, "prompt_eval_count"),
            output_token_count=_optional_nonnegative_int(response, "eval_count"),
            total_duration_ns=_optional_nonnegative_int(response, "total_duration"),
            load_duration_ns=_optional_nonnegative_int(response, "load_duration"),
            prompt_duration_ns=_optional_nonnegative_int(response, "prompt_eval_duration"),
            output_duration_ns=_optional_nonnegative_int(response, "eval_duration"),
        )
        return ProviderCompletion(
            raw_content=raw_content,
            raw_response_digest=sha256(raw).hexdigest(),
            raw_response_bytes=len(raw),
            usage=usage,
            unexpected_thinking=unexpected_thinking,
        )


def _optional_nonnegative_int(payload: Mapping[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise LLMInvalidProviderResponseError(f"Ollama {key} metadata is invalid.")
    return value
