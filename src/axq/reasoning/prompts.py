"""Code-owned, versioned prompts for offline structured reasoning."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, NamedTuple

from axq.reasoning.contracts import (
    PromptTemplateIdentity,
    ReasoningTask,
    ReflectionExplanation,
    ReflectionExplanationInput,
)
from axq.versioning import canonical_hash

_SYSTEM_TEMPLATE = (
    "You are AXQ's offline reflection explanation assistant. "
    "Use only the supplied immutable evidence. Return exactly one JSON object matching the "
    "supplied schema. Cite only supplied evidence IDs. State a falsifiable hypothesis, "
    "calibrated uncertainty, and one offline next investigation. Do not authorize trades, "
    "change policies, promote proposals, or recommend deployment."
)
_USER_TEMPLATE = "Explain this controlled reflection evidence:\n{evidence_json}"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


class RenderedReasoningPrompt(NamedTuple):
    """One deterministic prompt rendering for a provider invocation."""

    system: str
    user: str
    response_schema: dict[str, Any]
    rendered_digest: str

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(
            {
                "response_schema": self.response_schema,
                "system": self.system,
                "user": self.user,
            }
        )


def _response_schema() -> dict[str, Any]:
    return deepcopy(ReflectionExplanation.model_json_schema())


def reflection_explanation_prompt_identity() -> PromptTemplateIdentity:
    """Return the exact template and response-schema identity for Task 1."""

    template_digest = canonical_hash(
        {
            "system": _SYSTEM_TEMPLATE,
            "user_template": _USER_TEMPLATE,
        }
    )
    response_schema_digest = canonical_hash(_response_schema())
    return PromptTemplateIdentity(
        task=ReasoningTask.REFLECTION_EXPLANATION,
        template_digest=template_digest,
        response_schema_digest=response_schema_digest,
    )


def render_reflection_explanation_prompt(
    input_record: ReflectionExplanationInput,
) -> RenderedReasoningPrompt:
    """Render the sole V1 prompt from validated canonical evidence."""

    evidence = {
        "context": [item.model_dump(mode="json") for item in input_record.context],
        "source_references": [
            item.model_dump(mode="json") for item in input_record.source_references
        ],
        "task": ReasoningTask.REFLECTION_EXPLANATION.value,
    }
    user = _USER_TEMPLATE.format(evidence_json=_canonical_bytes(evidence).decode("ascii"))
    response_schema = _response_schema()
    body = {
        "response_schema": response_schema,
        "system": _SYSTEM_TEMPLATE,
        "user": user,
    }
    return RenderedReasoningPrompt(
        system=_SYSTEM_TEMPLATE,
        user=user,
        response_schema=response_schema,
        rendered_digest=canonical_hash(body),
    )
