"""Deterministic fixtures for Phase 9 reasoning tests."""

from __future__ import annotations

from datetime import UTC, datetime

from axq.reasoning.contracts import (
    BoundedReasoningContextItem,
    LLMGenerationPolicy,
    LLMRequestEnvelope,
    PromptTemplateIdentity,
    ProviderKind,
    ProviderModelIdentity,
    ReasoningSourceKind,
    ReasoningSourceReference,
    ReasoningTask,
)
from axq.versioning import canonical_hash


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def source_reference(
    *,
    source_id: str = "weekly-reflection-aaaaaaaaaaaaaaaaaaaa",
    source_kind: ReasoningSourceKind = ReasoningSourceKind.WEEKLY_REFLECTION,
    source_digest: str = "1" * 64,
) -> ReasoningSourceReference:
    return ReasoningSourceReference(
        source_kind=source_kind,
        source_id=source_id,
        source_digest=source_digest,
    )


def context_item(
    *,
    context_id: str = "context-weekly-summary",
    source: ReasoningSourceReference | None = None,
    content: object | None = None,
) -> BoundedReasoningContextItem:
    actual_content = (
        {
            "finding_ids": ["finding-b", "finding-a"],
            "summary": "London-session losses repeated in two complete weeks.",
        }
        if content is None
        else content
    )
    return BoundedReasoningContextItem(
        context_id=context_id,
        source=source or source_reference(),
        context_kind="WEEKLY_FINDING_SUMMARY",
        content=actual_content,
        content_digest=canonical_hash(actual_content),
    )


def provider_identity(**changes: object) -> ProviderModelIdentity:
    values: dict[str, object] = {
        "provider": ProviderKind.OLLAMA,
        "adapter_version": "ollama-native-http-v1",
        "provider_server_version": "0.12.6",
        "configured_model_name": "qwen3:8b",
        "resolved_model_name": "qwen3:8b",
        "model_digest": "a" * 64,
        "model_family": "qwen3",
        "quantization": "Q4_K_M",
    }
    values.update(changes)
    return ProviderModelIdentity.model_validate(values)


def prompt_identity(**changes: object) -> PromptTemplateIdentity:
    values: dict[str, object] = {
        "task": ReasoningTask.REFLECTION_EXPLANATION,
        "template_name": "REFLECTION_EXPLANATION_V1",
        "template_version": "1.0",
        "template_digest": "b" * 64,
        "response_schema_name": "ReflectionExplanation",
        "response_schema_version": "1.0",
        "response_schema_digest": "c" * 64,
    }
    values.update(changes)
    return PromptTemplateIdentity.model_validate(values)


def generation_policy(**changes: object) -> LLMGenerationPolicy:
    values: dict[str, object] = {
        "temperature": 0.0,
        "seed": 17,
        "max_output_tokens": 384,
        "response_byte_limit": 16_384,
        "prompt_context_budget_version": "bounded-context-v1",
    }
    values.update(changes)
    return LLMGenerationPolicy.model_validate(values)


def request_envelope(**changes: object) -> LLMRequestEnvelope:
    source = source_reference()
    values: dict[str, object] = {
        "task": ReasoningTask.REFLECTION_EXPLANATION,
        "provider_model": provider_identity(),
        "prompt": prompt_identity(),
        "source_references": (source,),
        "context": (context_item(source=source),),
        "generation": generation_policy(),
    }
    values.update(changes)
    return LLMRequestEnvelope.model_validate(values)
