# Offline LLM reasoning boundary

## Scope

Phase 9 Task 1 implements one optional offline reasoning task:
`REFLECTION_EXPLANATION`. It accepts bounded immutable reflection, pattern, or proposal evidence and
returns a strictly structured explanation, cited evidence IDs, a falsifiable hypothesis, calibrated
`LOW`/`MEDIUM`/`HIGH` uncertainty with a concise basis, and one suggested offline investigation.

The package is deliberately separate under `axq.reasoning`. It is not imported by the live/replay
fast path and cannot emit agent evidence, Master/Discipline/Risk outcomes, execution or position
intents, proposal transitions, deployments, or broker instructions. Ollama failure has no trading
fallback effect because reasoning is not a runtime dependency.

## Identity and structured-output boundary

`ProviderModelIdentity` binds the provider kind, adapter version, Ollama server version, configured
and resolved model names, exact model digest, and optional family/quantization assertions. V1 uses
the native Ollama HTTP API through the Python standard library and rejects every non-loopback URL.
Before fresh generation it checks `/api/version` and `/api/tags`; a name, digest, version, family,
quantization, missing-model, or ambiguous-model mismatch fails closed before `/api/chat`.

The current prompt is the code-owned `REFLECTION_EXPLANATION_V2`; persisted V1 identities remain
readable. V2 explicitly lists the exact source/context IDs that may be cited, prohibits citations
to digests, nested finding IDs, schema versions, or other identifiers, and constrains the provider
JSON Schema to the same per-request allowlist. `PromptTemplateIdentity` binds the template
name/version/digest and that exact `ReflectionExplanation` JSON Schema name/version/digest. The CLI
cannot accept arbitrary system or user prompts. Rendering is deterministic for the same canonical
bounded input, and `/api/chat` is sent with `stream=false`, `think=false`, the exact JSON Schema,
explicit temperature/seed/output limit, and the resolved model name.

`LLMRequestEnvelope` identity includes task, exact provider/model identity, prompt/schema identity,
normalized source references, sanitized bounded context, and generation settings. It contains no
operational timestamp or output path. Provider/model, prompt/schema, source/context, or generation
changes therefore produce a different request ID.

`LLMStructuredResponseArtifact` stores only the validated structure. Its response ID binds the
request, provider/model identity, output, and structured-output digest. Citations must be a subset
of the exact supplied source and context IDs. Extra fields, invented citations, malformed JSON,
oversized output, or unexpected thinking are invalid.

## Append-only audit

Migration `016_llm_reasoning_audit.sql` creates:

- `llm_reasoning_requests` for canonical request envelopes;
- `llm_reasoning_responses` for exact request-linked structured responses;
- `llm_reasoning_attempts` for completed, reused, and failed execution attempts.

Each row stores compact sorted ASCII JSON and its SHA-256 digest. Foreign keys and service/store
validation enforce exact request/provider/response linkage. Attempt keys are unique per request.
Every table rejects `UPDATE` and `DELETE`, and no mutable current-result table exists. Same-ID and
same-byte appends are idempotent; same-ID or same attempt-key conflicts fail closed. Read and reuse
paths revalidate canonical bytes, digest, content identity, indexed columns, and linkage.

Attempt status is one of `COMPLETED`, `REUSED`, `TIMEOUT`, `CONNECTION_ERROR`, `HTTP_ERROR`,
`MODEL_UNAVAILABLE`, `MODEL_IDENTITY_MISMATCH`, `INVALID_RESPONSE`, or `PROVIDER_ERROR`. Operational
UTC timestamps, endpoint, token counts, and duration measurements remain audit metadata and do not
change semantic attempt identity. A later success appends after a failure; it never overwrites or
converts the failed attempt.

The CLI samples request, operation start, and completion wall time separately and measures local
elapsed duration with a monotonic clock. Unexpected provider or response-persistence exceptions are
converted to a bounded `PROVIDER_ERROR` terminal attempt without persisting exception text. A store
failure that prevents the audit database itself from accepting any write remains an external
operational failure and cannot be made durable in that unavailable store.

Invalid raw provider content and exception traces are not persisted. The audit retains only a
typed code, bounded safe message, optional HTTP status, optional raw-response SHA-256/byte count,
and provider usage/duration metadata when a completion was successfully received. Hidden thinking
is neither requested nor stored.

## Exact-result reuse and determinism

`REUSE_FIRST_COMPLETED_EXACT` revalidates the first committed `COMPLETED` result for the exact
request, skips provider identity resolution and generation, appends a `REUSED` attempt, and returns
the original response bytes. Failures and invalid results are never reusable. `NEVER_REUSE` performs
a fresh provider check and generation even when an earlier completion exists.

Content-addressed request identity, strict validation, response identity, audit linkage, canonical
serialization, and exact completed-result reuse are deterministic. Independent LLM generations are
not promised to be byte-identical across Ollama versions, model builds, hardware, or environments;
two valid fresh generations may have different response IDs. Reuse is the mechanism that guarantees
exact prior response bytes when that behavior is explicitly selected.

## CLI

From the Phase 9 worktree, make the worktree sources authoritative when reusing the root environment:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src')
```

Run one controlled explanation:

```powershell
python -m axq.reasoning run-reflection-explanation `
  --input tests/fixtures/reasoning/reflection_explanation_input.json `
  --store runtime/phase9/reasoning.sqlite3 `
  --output runtime/phase9/reflection-explanation.json `
  --attempt-key operator-smoke-001 `
  --reuse-policy REUSE_FIRST_COMPLETED_EXACT `
  --endpoint http://127.0.0.1:11434 `
  --model qwen3:8b `
  --model-digest '<exact-64-character-model-digest>' `
  --ollama-version '<exact-server-version>' `
  --timeout-seconds 30
```

The output file and stdout contain one canonical `ReasoningRunResult`: request, response, and attempt
IDs; terminal status; reuse flag; schema version; and safe failure metadata. They never contain raw
provider output or hidden reasoning.

Inspect the append-only store without initializing an Ollama provider:

```powershell
$result = Get-Content -Raw runtime/phase9/reflection-explanation.json | ConvertFrom-Json
python -m axq.reasoning show-request --store runtime/phase9/reasoning.sqlite3 --request-id $result.request_id
python -m axq.reasoning show-response --store runtime/phase9/reasoning.sqlite3 --response-id $result.response_id
python -m axq.reasoning show-history --store runtime/phase9/reasoning.sqlite3 --request-id $result.request_id
python -m axq.reasoning reasoning-summary --store runtime/phase9/reasoning.sqlite3
```

All databases and result artifacts belong under ignored `runtime/`.

## Optional real Ollama smoke test

The fake-provider suite is authoritative. A real smoke test is optional and environment-dependent.
Start Ollama locally, ensure the intended model is already installed, then inspect its exact identity:

```powershell
$ollamaRoot = 'http://127.0.0.1:11434'
$ollamaVersion = (Invoke-RestMethod "$ollamaRoot/api/version").version
$model = (Invoke-RestMethod "$ollamaRoot/api/tags").models |
  Where-Object { $_.name -eq 'qwen3:8b' } |
  Select-Object -First 1

python -m axq.reasoning run-reflection-explanation `
  --input tests/fixtures/reasoning/reflection_explanation_input.json `
  --store runtime/phase9/ollama-smoke.sqlite3 `
  --output runtime/phase9/ollama-smoke-result.json `
  --attempt-key ollama-smoke-001 `
  --endpoint $ollamaRoot `
  --model $model.name `
  --model-digest $model.digest `
  --ollama-version $ollamaVersion `
  --timeout-seconds 30

Get-Content -Raw runtime/phase9/ollama-smoke-result.json
python -m axq.reasoning reasoning-summary --store runtime/phase9/ollama-smoke.sqlite3
```

Do not weaken identity checks when Ollama is unavailable or reports a different digest/version.
Record the environment limitation or update the expected reviewed identity deliberately.

## Measured controlled fixture

The deterministic fake-provider fixture produced one request, one structured response, and two
attempts (`COMPLETED`, then exact `REUSED`). Provider identity and completion were each invoked once;
the reuse invoked neither. Canonical result sizes were 221 bytes for completion and 217 bytes for
reuse. The SQLite file was 962,560 bytes after all repository migrations on the validation host;
database size is environment- and migration-set-dependent, not semantic identity.

## Non-goals

Task 1 adds no RAG, embeddings, vector store, Experience Graph, web research, cloud provider,
arbitrary tool/plugin execution, runtime or specialist integration, policy mutation, proposal
promotion, deployment, training, replay execution, broker/MT5 access, or Final OOS reader. Those
remain separately governed future work.
