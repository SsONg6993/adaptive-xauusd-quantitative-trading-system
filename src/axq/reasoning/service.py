"""Offline orchestration for strictly structured reflection explanations."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from time import perf_counter

from pydantic import TypeAdapter, ValidationError

from axq.reasoning.contracts import (
    LLMAttemptStatus,
    LLMExecutionAttemptAudit,
    LLMFailureCode,
    LLMFailureMetadata,
    LLMRequestEnvelope,
    LLMReusePolicy,
    LLMStructuredResponseArtifact,
    ProviderModelIdentity,
    ReasoningRunResult,
    ReasoningUTCDateTime,
    ReflectionExplanation,
    ReflectionExplanationInput,
)
from axq.reasoning.prompts import (
    reflection_explanation_prompt_identity,
    render_reflection_explanation_prompt,
)
from axq.reasoning.provider import (
    LLMInvalidProviderResponseError,
    LLMModelIdentityMismatchError,
    LLMProvider,
    LLMProviderError,
    ProviderAttemptControls,
    ProviderCompletion,
    ProviderUsage,
)
from axq.reasoning.store import SQLiteReasoningAuditStore

_UTC_ADAPTER = TypeAdapter(ReasoningUTCDateTime)


def build_reflection_explanation_request(
    *,
    input_record: ReflectionExplanationInput,
    provider_model: ProviderModelIdentity,
) -> LLMRequestEnvelope:
    """Build the V2 request from validated bounded input and exact model identity."""

    validated_input = ReflectionExplanationInput.model_validate(input_record.model_dump())
    validated_provider = ProviderModelIdentity.model_validate(provider_model.model_dump())
    return LLMRequestEnvelope(
        provider_model=validated_provider,
        prompt=reflection_explanation_prompt_identity(validated_input),
        source_references=validated_input.source_references,
        context=validated_input.context,
        generation=validated_input.generation,
    )


def _safe_failure(failure: LLMFailureMetadata) -> LLMFailureMetadata:
    message = " ".join(failure.message.split())[:500]
    return LLMFailureMetadata(
        code=failure.code,
        message=message or "Provider failed without a safe diagnostic message.",
        http_status=failure.http_status,
        raw_response_digest=failure.raw_response_digest,
        raw_response_bytes=failure.raw_response_bytes,
    )


def _invalid_response_failure(
    completion: ProviderCompletion,
    message: str,
) -> LLMFailureMetadata:
    return _safe_failure(
        LLMFailureMetadata(
            code=LLMFailureCode.INVALID_RESPONSE,
            message=message,
            raw_response_digest=completion.raw_response_digest,
            raw_response_bytes=completion.raw_response_bytes,
        )
    )


def _result(attempt: LLMExecutionAttemptAudit) -> ReasoningRunResult:
    return ReasoningRunResult(
        request_id=attempt.request_id,
        attempt_id=attempt.attempt_id,
        status=attempt.status,
        response_id=attempt.response_id,
        reused=attempt.status is LLMAttemptStatus.REUSED,
        failure=attempt.failure,
    )


def _audit(
    *,
    request: LLMRequestEnvelope,
    attempt_key: str,
    status: LLMAttemptStatus,
    response_id: str | None,
    failure: LLMFailureMetadata | None,
    requested_at: datetime,
    started_at: datetime,
    completed_at: datetime,
    timeout_seconds: float,
    endpoint: str,
    local_elapsed_ms: float,
    usage: ProviderUsage | None = None,
) -> LLMExecutionAttemptAudit:
    actual_usage = usage or ProviderUsage()
    return LLMExecutionAttemptAudit(
        request_id=request.request_id,
        attempt_key=attempt_key,
        status=status,
        provider_model=request.provider_model,
        response_id=response_id,
        failure=failure,
        requested_at=requested_at,
        started_at=started_at,
        completed_at=completed_at,
        timeout_seconds=timeout_seconds,
        endpoint=endpoint,
        prompt_token_count=actual_usage.prompt_token_count,
        output_token_count=actual_usage.output_token_count,
        provider_total_duration_ns=actual_usage.total_duration_ns,
        provider_load_duration_ns=actual_usage.load_duration_ns,
        provider_prompt_duration_ns=actual_usage.prompt_duration_ns,
        provider_output_duration_ns=actual_usage.output_duration_ns,
        local_elapsed_ms=local_elapsed_ms,
    )


def _validate_operational_input(
    *,
    requested_at: datetime,
    started_at: datetime,
    completed_at: datetime,
    timeout_seconds: float,
    response_byte_limit: int,
    endpoint: str,
) -> ProviderAttemptControls:
    for value in (requested_at, started_at, completed_at):
        _UTC_ADAPTER.validate_python(value)
    if not requested_at <= started_at <= completed_at:
        raise ValueError("requested_at, started_at, and completed_at must be ordered")
    if not endpoint or len(endpoint) > 300:
        raise ValueError("endpoint must contain between 1 and 300 characters")
    return ProviderAttemptControls(
        timeout_seconds=timeout_seconds,
        response_byte_limit=response_byte_limit,
    )


def run_reflection_explanation(
    *,
    input_record: ReflectionExplanationInput,
    expected_provider_model: ProviderModelIdentity,
    provider: LLMProvider,
    store: SQLiteReasoningAuditStore,
    attempt_key: str,
    reuse_policy: LLMReusePolicy,
    requested_at: datetime,
    started_at: datetime,
    completed_at: datetime,
    timeout_seconds: float,
    endpoint: str,
    local_elapsed_ms: float,
    operational_clock: Callable[[], datetime] | None = None,
    monotonic_clock: Callable[[], float] = perf_counter,
) -> ReasoningRunResult:
    """Execute or exactly reuse one append-only offline reasoning attempt."""

    request = build_reflection_explanation_request(
        input_record=input_record,
        provider_model=expected_provider_model,
    )
    controls = _validate_operational_input(
        requested_at=requested_at,
        started_at=started_at,
        completed_at=completed_at,
        timeout_seconds=timeout_seconds,
        response_byte_limit=request.generation.response_byte_limit,
        endpoint=endpoint,
    )
    operation_started = monotonic_clock() if operational_clock is not None else None
    if operational_clock is not None:
        started_at = operational_clock()

    def completed_timing() -> tuple[datetime, float]:
        if operational_clock is None or operation_started is None:
            return completed_at, local_elapsed_ms
        observed_completed_at = operational_clock()
        observed_elapsed_ms = max(0.0, (monotonic_clock() - operation_started) * 1000.0)
        return observed_completed_at, observed_elapsed_ms

    store.append_request(request)

    prior = next(
        (item for item in store.attempts(request.request_id) if item.attempt_key == attempt_key),
        None,
    )
    if prior is not None:
        return _result(prior)

    if reuse_policy is LLMReusePolicy.REUSE_FIRST_COMPLETED_EXACT:
        reusable = store.first_completed_response(request.request_id)
        if reusable is not None:
            actual_completed_at, actual_elapsed_ms = completed_timing()
            reused = _audit(
                request=request,
                attempt_key=attempt_key,
                status=LLMAttemptStatus.REUSED,
                response_id=reusable.response_id,
                failure=None,
                requested_at=requested_at,
                started_at=started_at,
                completed_at=actual_completed_at,
                timeout_seconds=timeout_seconds,
                endpoint=endpoint,
                local_elapsed_ms=actual_elapsed_ms,
            )
            store.append_attempt(reused)
            return _result(reused)

    prompt = render_reflection_explanation_prompt(
        ReflectionExplanationInput(
            source_references=request.source_references,
            context=request.context,
            generation=request.generation,
        )
    )
    completion: ProviderCompletion | None = None
    try:
        observed = provider.verify_identity(
            request.provider_model,
            timeout_seconds=timeout_seconds,
        )
        if observed != request.provider_model:
            raise LLMModelIdentityMismatchError()
        completion = provider.complete(request, prompt, controls=controls)
        if completion.unexpected_thinking:
            raise LLMInvalidProviderResponseError(
                "Provider returned unexpected hidden reasoning content.",
                raw_response_digest=completion.raw_response_digest,
                raw_response_bytes=completion.raw_response_bytes,
            )
        if completion.raw_response_bytes > controls.response_byte_limit:
            raise LLMInvalidProviderResponseError(
                "Provider response exceeded the configured byte limit.",
                raw_response_digest=completion.raw_response_digest,
                raw_response_bytes=completion.raw_response_bytes,
            )
        try:
            output = ReflectionExplanation.model_validate_json(completion.raw_content)
            response = LLMStructuredResponseArtifact.from_request(
                request=request,
                output=output,
            )
        except (ValidationError, ValueError):
            failure = _invalid_response_failure(
                completion,
                "Provider response failed strict structured-output validation.",
            )
            actual_completed_at, actual_elapsed_ms = completed_timing()
            attempt = _audit(
                request=request,
                attempt_key=attempt_key,
                status=LLMAttemptStatus.INVALID_RESPONSE,
                response_id=None,
                failure=failure,
                requested_at=requested_at,
                started_at=started_at,
                completed_at=actual_completed_at,
                timeout_seconds=timeout_seconds,
                endpoint=endpoint,
                local_elapsed_ms=actual_elapsed_ms,
                usage=completion.usage,
            )
            store.append_attempt(attempt)
            return _result(attempt)
        store.append_response(response)
        actual_completed_at, actual_elapsed_ms = completed_timing()
        attempt = _audit(
            request=request,
            attempt_key=attempt_key,
            status=LLMAttemptStatus.COMPLETED,
            response_id=response.response_id,
            failure=None,
            requested_at=requested_at,
            started_at=started_at,
            completed_at=actual_completed_at,
            timeout_seconds=timeout_seconds,
            endpoint=endpoint,
            local_elapsed_ms=actual_elapsed_ms,
            usage=completion.usage,
        )
        store.append_attempt(attempt)
        return _result(attempt)
    except LLMProviderError as error:
        actual_completed_at, actual_elapsed_ms = completed_timing()
        attempt = _audit(
            request=request,
            attempt_key=attempt_key,
            status=error.status,
            response_id=None,
            failure=_safe_failure(error.failure),
            requested_at=requested_at,
            started_at=started_at,
            completed_at=actual_completed_at,
            timeout_seconds=timeout_seconds,
            endpoint=endpoint,
            local_elapsed_ms=actual_elapsed_ms,
            usage=None if completion is None else completion.usage,
        )
        store.append_attempt(attempt)
        return _result(attempt)
    except Exception as error:
        actual_completed_at, actual_elapsed_ms = completed_timing()
        failure = LLMFailureMetadata(
            code=LLMFailureCode.PROVIDER_ERROR,
            message=(
                "Unexpected provider or response-persistence failure: "
                f"{type(error).__name__}."
            ),
        )
        attempt = _audit(
            request=request,
            attempt_key=attempt_key,
            status=LLMAttemptStatus.PROVIDER_ERROR,
            response_id=None,
            failure=failure,
            requested_at=requested_at,
            started_at=started_at,
            completed_at=actual_completed_at,
            timeout_seconds=timeout_seconds,
            endpoint=endpoint,
            local_elapsed_ms=actual_elapsed_ms,
            usage=None if completion is None else completion.usage,
        )
        store.append_attempt(attempt)
        return _result(attempt)
