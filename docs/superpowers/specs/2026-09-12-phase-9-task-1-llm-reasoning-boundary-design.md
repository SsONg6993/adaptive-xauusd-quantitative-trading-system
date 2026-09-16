# Phase 9 Task 1 LLM Provider and Structured Reasoning Boundary Design

## Status

This specification defines Phase 9 Task 1 only. It is approved in principle but remains subject to
final user review before an implementation plan or code is written. The authoritative base is
commit `f7f9a62e8af43700f2a68c901bb1b0af1b80090f` on
`codex/phase-9-llm-reasoning`.

## Goal

Task 1 adds a provider-neutral, offline reasoning boundary for controlled explanations of immutable
Phase 8 reflection evidence. The first supported task is `REFLECTION_EXPLANATION`. A local Ollama
adapter receives an exact, bounded, versioned context and may return only a strictly validated
structured explanation.

The boundary is analytical and advisory. It cannot participate in the Phase 6/7 fast decision path,
change trading behavior, promote a proposal, authorize deployment, access Final OOS, or contact MT5.

## Selected approach

Create a separate `axq.reasoning` package with a narrow `LLMProvider` protocol and an Ollama-native
HTTP implementation using the Python standard library. The Ollama adapter uses loopback endpoints
only and hides transport details behind an injectable transport so deterministic fakes can provide
authoritative tests without installing or running Ollama.

This approach is preferred to the Ollama Python client because it adds no required dependency and
keeps timeout, response-size, identity, and error handling visible. It is preferred to Ollama's
OpenAI-compatible endpoint because Task 1 needs only one local provider and benefits from native
model-digest and server-version metadata without adding a premature compatibility layer.

## Package and dependency boundaries

The implementation will add the following focused modules:

- `axq.reasoning.contracts`: immutable schemas and identities.
- `axq.reasoning.prompts`: the code-owned `REFLECTION_EXPLANATION` template and renderer.
- `axq.reasoning.provider`: the provider and transport-neutral completion protocols.
- `axq.reasoning.ollama`: loopback-only standard-library HTTP transport and provider adapter.
- `axq.reasoning.store`: append-only SQLite request, response, and attempt persistence.
- `axq.reasoning.service`: validation, reuse, provider invocation, and audit orchestration.
- `axq.reasoning.cli` and `axq.reasoning.__main__`: run, show, history, and summary commands.

No existing runtime package may import `axq.reasoning`. The package may depend on immutable
reflection contracts, strict UTC types, canonical hashing/serialization helpers, and the existing
database migration adapter. It may not import orchestration, Master, Discipline, Risk, execution,
position management, broker, MT5, replay execution, training, or Final OOS readers.

Task 1 adds no Ollama Python dependency. The external Ollama process remains optional.

## Supported reasoning task

`ReasoningTask` contains only `REFLECTION_EXPLANATION` in V1. Its inputs are exact references to one
or more immutable records of these allowlisted kinds:

- `DAILY_REFLECTION`
- `WEEKLY_REFLECTION`
- `PATTERN`
- `IMPROVEMENT_PROPOSAL`

Task 1 does not retrieve those records itself. A caller supplies already-controlled references and
sanitized canonical context. There is no graph traversal, similarity search, embedding, vector
index, RAG, arbitrary file reader, web fetch, database query language, or tool-calling loop.

## Immutable contracts

All contracts use strict Pydantic models with `extra="forbid"`, `frozen=True`, versioned schemas,
strict UTC where timestamps are allowed, normalized tuple ordering, bounded text, and
content-addressed identifiers.

### Provider and model identity

`ProviderModelIdentity` binds:

- provider kind (`OLLAMA`);
- AXQ provider-adapter version;
- Ollama server version;
- configured model name;
- resolved canonical model name;
- exact model digest;
- available family and quantization facts.

The semantic request identity includes the provider kind, adapter version, server version,
canonical model name, model digest, family, and quantization. A mutable model tag alone is not an
adequate identity. The provider resolves the model through Ollama's model-list endpoint before
generation and fails closed if the requested name is absent, ambiguous, or differs from an expected
digest supplied by the request configuration.

The normalized loopback endpoint is safe audit metadata. Credentials, authorization headers, URL
query strings, and non-loopback endpoints are forbidden in V1.

### Prompt and response-schema identity

`PromptTemplateIdentity` binds:

- reasoning task;
- template name;
- template version;
- digest of the exact system/user template text;
- response-schema name and version;
- digest of the canonical JSON Schema.

The prompt is code-owned. The CLI cannot accept arbitrary system or user instructions. Any template
or response-schema change creates a new semantic request identity.

### Source references and bounded context

`ReasoningSourceReference` binds an allowlisted source kind, exact source ID, and canonical source
digest. `BoundedReasoningContextItem` binds a stable context item ID, its source reference, context
kind, exact sanitized canonical structured content, and content digest.

V1 limits are:

- no more than 16 context items;
- no more than 2,000 Unicode characters in one canonical item;
- no more than 16,000 Unicode characters across all items;
- unique source and context identities after canonical sorting;
- only JSON-compatible scalar, list, and object content accepted;
- no binary content, filesystem path ingestion, URLs, secrets, credentials, or arbitrary prompt
  fragments.

Both exact sanitized content and its digest are stored. The digest must match the canonical bytes.
This preserves reconstructability without creating an unbounded document store.

### Generation policy

`LLMGenerationPolicy` binds all response-affecting settings:

- temperature;
- deterministic seed;
- maximum generated tokens;
- structured JSON-schema mode;
- streaming disabled;
- model thinking disabled;
- response byte limit;
- prompt/context budget version.

Timeout and local connection settings are attempt controls rather than model-output semantics and
are recorded in attempt audit metadata. They do not alter semantic request identity.

### Semantic request envelope

`LLMRequestEnvelope` contains:

- content-addressed `request_id`;
- schema version;
- task;
- exact provider/model identity;
- exact prompt/schema identity;
- normalized source references;
- normalized bounded context;
- generation policy.

`request_id` excludes requested, started, and completed timestamps; attempt key or sequence; local
database/output paths; host working directory; latency; token counts; transport errors; and mutable
runtime status. These values belong to attempt audit records.

Changing provider/model identity, prompt/schema identity, generation policy, source identity, or
canonical context bytes necessarily changes `request_id`.

## Structured response contract

`ReflectionExplanation` contains only:

- `explanation`: concise synthesis of the cited facts;
- `cited_evidence_ids`: normalized unique IDs drawn from the request's allowed source/context IDs;
- `hypothesis`: a falsifiable interpretation, not a trading instruction;
- `uncertainty`: `LOW`, `MEDIUM`, or `HIGH` plus a concise basis;
- `suggested_next_investigation`: one bounded offline investigation suggestion.

All strings have explicit minimum and maximum lengths. At least one citation is required. Every
citation must be an exact allowed input ID. Additional fields are rejected. In particular, the
schema has no chain-of-thought, reasoning trace, hidden analysis, tool call, policy recommendation,
deployment instruction, or trading action field.

`LLMStructuredResponseArtifact` binds the content-addressed `response_id`, request ID, exact
provider/model identity, structured response, and canonical structured-response digest. Its semantic
identity excludes operational timestamps, token counts, latency, output path, and attempt status.

If two fresh executions return different valid structured content, they produce different response
IDs. Neither silently overwrites the other.

## Semantic determinism boundary

AXQ guarantees:

- canonical and content-addressed request identity;
- strict input and response validation;
- canonical and content-addressed structured-response identity;
- byte-stable canonical JSON for an already-materialized request or response;
- exact reuse of a verified stored completed response under the approved reuse policy.

AXQ does not claim that two independent LLM generations are byte-identical. Temperature zero and a
fixed seed reduce variation but do not remove differences caused by model builds, Ollama versions,
hardware, numerical kernels, or provider behavior. Fresh generations remain separate auditable
attempts and may create different valid response artifacts.

## Provider protocol and Ollama adapter

`LLMProvider` exposes two operations:

1. resolve an exact `ProviderModelIdentity` for a configured model;
2. complete one validated `LLMRequestEnvelope` under explicit attempt controls.

`OllamaProvider` uses an injectable `OllamaTransport`. The production transport uses standard-library
HTTP and accepts only `http://localhost`, `http://127.0.0.1`, or the IPv6 loopback equivalent. It:

1. reads `/api/version`;
2. reads `/api/tags` and selects one exact model entry;
3. verifies the expected model digest when configured;
4. posts to `/api/chat` with `stream=false`, `think=false`, explicit generation options, and the
   exact response JSON Schema in `format`;
5. enforces connect/read timeout and response-size bounds;
6. maps provider metrics into safe typed metadata.

The provider never requests tools, embeddings, vision, remote/cloud models, or chain-of-thought.
Any unexpected provider `thinking` content is discarded before persistence and is never included in
an error message, hash payload, or diagnostic artifact.

## Attempt audit and failure handling

Every provider invocation or completed-result reuse appends an immutable
`LLMExecutionAttemptAudit`. It records:

- content-addressed attempt ID;
- request ID and explicit attempt key;
- terminal status;
- strict-UTC requested, started, and completed times;
- timeout and safe endpoint metadata;
- response ID when successful or reused;
- provider prompt/output token counts when available;
- provider duration metrics when available;
- local elapsed duration;
- sanitized failure code/message;
- HTTP status when safe and applicable;
- invalid raw-response digest and byte count when applicable;
- exact provider/model identity.

Terminal statuses are:

- `COMPLETED`
- `REUSED`
- `TIMEOUT`
- `CONNECTION_ERROR`
- `HTTP_ERROR`
- `MODEL_UNAVAILABLE`
- `MODEL_IDENTITY_MISMATCH`
- `INVALID_RESPONSE`
- `PROVIDER_ERROR`

Attempt identity includes the request ID, explicit attempt key, terminal status, exact response
linkage or failure fingerprint, and provider/model identity. Operational timestamps and measured
durations do not participate in attempt semantic identity. Attempt keys are unique per request.
An identical attempt retry reuses its existing audit record; the same attempt key with different
semantic content fails closed.

Failure messages are length-bounded and sanitized. Raw successful provider text is discarded after
strict parsing. Raw invalid responses and exception traces are not persisted; only a digest, byte
count, typed error code, and safe concise message remain. A failed attempt is never deleted or
changed when a later attempt succeeds.

## Reuse policies

`LLMReusePolicy` supports:

- `NEVER_REUSE`
- `REUSE_FIRST_COMPLETED_EXACT`

The CLI default is `REUSE_FIRST_COMPLETED_EXACT`. Under that policy, the service may reuse only the
first committed `COMPLETED` response whose stored request ID, canonical request bytes, response
linkage, response digest, and provider/model identity all verify exactly. It does not call Ollama and
appends a new `REUSED` attempt audit linked to the unchanged response bytes.

Failed or invalid attempts are never reusable results. Under `NEVER_REUSE`, the service performs a
new provider call even when an earlier valid response exists. A different valid result is appended
as a separate response and attempt.

## Authoritative append-only persistence

Migration `016_llm_reasoning_audit.sql` creates:

- `llm_request_envelopes`;
- `llm_structured_responses`;
- `llm_execution_attempts`.

Every table stores canonical record JSON and a payload digest. Foreign keys enforce exact request and
response linkage. Unique constraints protect content and attempt identities. UPDATE and DELETE
triggers reject mutation on every table. There is no mutable current-result table.

Store behavior is fail-closed:

- same ID and same canonical bytes is an idempotent append;
- same ID and different bytes is rejected;
- a response without its exact request is rejected;
- a completed/reused attempt requires an exact stored response;
- a failure attempt cannot reference a successful response;
- a response's provider/model identity must equal its request identity;
- replayed audit history must preserve valid linkage and unique attempt keys.

SQLite is the authoritative audit and provenance store. Canonical JSON request, response, attempt,
history, and summary output remains the portable machine-readable artifact format.

## Service flow

The offline service performs this sequence:

1. validate allowlisted source references and bounded sanitized context;
2. resolve and verify exact Ollama/model identity;
3. render the code-owned prompt deterministically;
4. construct and append the content-addressed request envelope;
5. apply the explicit reuse policy;
6. either append a verified `REUSED` audit or invoke the provider;
7. parse JSON and validate the exact structured schema;
8. verify every citation against the request's allowed IDs;
9. append the valid response artifact, if any;
10. append the terminal attempt audit in all provider-attempt cases;
11. emit canonical JSON.

Input-contract failures that occur before a valid request can be constructed are ordinary validation
errors and cannot be journaled against a fabricated identity. Once a valid request is persisted, all
provider, transport, model-resolution, timeout, and output-validation terminal outcomes are appended
to its audit history.

## CLI boundary

The package exposes:

```text
run-reflection-explanation
show-request
show-response
show-history
reasoning-summary
```

`run-reflection-explanation` accepts a controlled canonical request-input file, SQLite store path,
output path, explicit attempt key, reuse policy, loopback Ollama endpoint, model name, expected model
digest, and timeout. It does not accept arbitrary prompt text, credentials, source database queries,
Final OOS paths, broker configuration, or runtime configuration.

The run command always writes one canonical machine-readable result describing request ID, response
ID when present, attempt ID, terminal status, reuse status, and safe error metadata. Show/history/
summary commands read only the append-only audit store.

## Safety invariants

- Reasoning is offline and optional; unavailable Ollama never blocks or changes trading.
- No fast-path component imports or calls `axq.reasoning`.
- No output is an `AgentEvidence`, Master proposal, Discipline/Risk decision, execution intent,
  proposal transition, authorization, or deployment record.
- No Task 1 code reads Final OOS, runtime journals, broker state, credentials, or MT5.
- No Task 1 code performs RAG, embedding, vector search, graph lookup, web retrieval, arbitrary tool
  execution, model training, parameter tuning, or policy mutation.
- Only strict structured output is retained; hidden reasoning is neither requested nor persisted.
- Provider failure is evidence about the offline reasoning attempt only and has no trading fallback
  effect.

## Test strategy

Implementation will be test-first and use a deterministic fake provider/transport as the
authoritative gate. Focused tests will cover:

- frozen strict schemas, normalization, bounded content, and strict UTC;
- stable request identity across operational timestamp/path changes;
- changed provider, model digest, server/adapter version, prompt/schema, generation settings,
  source, or context producing changed request identity;
- response identity and canonical JSON byte stability;
- citation subset enforcement and rejection of extra/chain-of-thought fields;
- loopback-only endpoint validation;
- exact model-name/digest resolution;
- non-streaming, thinking-disabled, schema-constrained Ollama request construction;
- timeout, connection, HTTP, model, malformed JSON, schema, citation, and response-size failures;
- omission of raw invalid output, raw exceptions, and provider thinking from persistence;
- append-only SQL UPDATE/DELETE rejection and conflict detection;
- permanent failure history followed by an appended success;
- `NEVER_REUSE` invoking the provider again;
- exact completed-result reuse skipping provider invocation and preserving response bytes;
- attempt-key idempotency and stale/conflicting retry rejection;
- CLI run/show/history/summary output;
- import audits proving no runtime, execution, Final OOS, broker, or MT5 dependency;
- byte snapshots proving referenced Phase 8 records remain unchanged.

A real local Ollama smoke test is optional and environment-dependent. Its absence or failure is
reported as an environment limitation, not worked around by weakening contracts. It is not part of
the deterministic acceptance gate.

## Expected implementation validation

After focused tests, the final lightweight gate will run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest
& '..\..\.venv\Scripts\python.exe' -m ruff check .
& '..\..\.venv\Scripts\python.exe' -m mypy src/axq --no-warn-unused-ignores
& '..\..\.venv\Scripts\python.exe' -m pip check
git diff --check
```

No model training, replay, backtest, policy tuning, broker action, or Phase 9 Task 2 work is part of
this specification.

## Acceptance criteria

Task 1 is complete only when:

1. one controlled fixture produces a strictly validated `REFLECTION_EXPLANATION` through the fake
   provider boundary;
2. exact request, response, and attempt provenance is reconstructable from append-only SQLite;
3. failures remain immutable after later success;
4. exact completed-result reuse skips the provider and preserves response bytes;
5. fresh-generation nondeterminism is explicitly represented rather than falsely hidden;
6. no hidden reasoning or unsafe raw provider content is persisted;
7. no forbidden fast-path, Final OOS, mutation, deployment, broker, or MT5 dependency exists;
8. focused and full lightweight validation passes.

## Deferred work

Task 1 deliberately defers additional providers, remote endpoints, RAG, embeddings, vector stores,
Experience Graph construction, general research tasks, tool calls, specialist runtime integration,
proposal generation, automatic promotion, candidate deployment, and any use of LLM output in live or
replay trading decisions.
