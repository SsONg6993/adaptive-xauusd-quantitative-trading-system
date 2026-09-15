"""Code-owned, versioned prompts for offline structured reasoning."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, NamedTuple, cast

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
    "supplied schema. The evidence contains an allowed_citation_ids list; cite only exact "
    "values from that list. Do not cite source_digest. Do not cite content_digest. Do not "
    "cite finding_ids. Do not cite schema_version. Do not cite any other identifier that is "
    "not in allowed_citation_ids. State a falsifiable hypothesis, calibrated uncertainty, "
    "and one offline next investigation. Do not authorize trades, change policies, promote "
    "proposals, or recommend deployment."
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


def _allowed_citation_ids(input_record: ReflectionExplanationInput) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                *(item.source_id for item in input_record.source_references),
                *(item.context_id for item in input_record.context),
            }
        )
    )


def _response_schema(allowed_citation_ids: tuple[str, ...]) -> dict[str, Any]:
    schema = deepcopy(ReflectionExplanation.model_json_schema())
    properties = cast(dict[str, Any], schema["properties"])
    citations = cast(dict[str, Any], properties["cited_evidence_ids"])
    items = cast(dict[str, Any], citations["items"])
    items["enum"] = list(allowed_citation_ids)
    return schema


def reflection_explanation_prompt_identity(
    input_record: ReflectionExplanationInput,
) -> PromptTemplateIdentity:
    """Return the V2 template and request-specific response-schema identity."""

    allowed_citation_ids = _allowed_citation_ids(input_record)
    template_digest = canonical_hash(
        {
            "system": _SYSTEM_TEMPLATE,
            "user_template": _USER_TEMPLATE,
        }
    )
    response_schema_digest = canonical_hash(_response_schema(allowed_citation_ids))
    return PromptTemplateIdentity(
        task=ReasoningTask.REFLECTION_EXPLANATION,
        template_name="REFLECTION_EXPLANATION_V2",
        template_version="2.0",
        template_digest=template_digest,
        response_schema_version="2.0",
        response_schema_digest=response_schema_digest,
    )


def render_reflection_explanation_prompt(
    input_record: ReflectionExplanationInput,
) -> RenderedReasoningPrompt:
    """Render the V2 prompt with its exact allowed citation identifiers."""

    allowed_citation_ids = _allowed_citation_ids(input_record)
    evidence = {
        "allowed_citation_ids": list(allowed_citation_ids),
        "context": [item.model_dump(mode="json") for item in input_record.context],
        "source_references": [
            item.model_dump(mode="json") for item in input_record.source_references
        ],
        "task": ReasoningTask.REFLECTION_EXPLANATION.value,
    }
    user = _USER_TEMPLATE.format(evidence_json=_canonical_bytes(evidence).decode("ascii"))
    response_schema = _response_schema(allowed_citation_ids)
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
