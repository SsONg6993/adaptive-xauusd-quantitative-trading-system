# Phase 9 Task 1 LLM Provider and Structured Reasoning Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an offline-only, provider-neutral structured reasoning boundary with a loopback Ollama
adapter, deterministic semantic identities, and an authoritative append-only SQLite audit trail.

**Architecture:** A new `axq.reasoning` package separates strict content-addressed contracts,
code-owned prompt rendering, provider transport, append-only persistence, orchestration, and CLI
concerns. The service persists a request before provider preflight, optionally reuses the first exact
completed response, validates fresh structured output, and always appends a terminal attempt audit.
No fast-path or trading component depends on the package.

**Tech Stack:** Python 3.12, Pydantic 2, standard-library `urllib.request`, SQLite through
`axq.database.Database`, pytest, Ruff, and strict mypy.

**Spec:** `docs/superpowers/specs/2026-09-12-phase-9-task-1-llm-reasoning-boundary-design.md`

## Global Constraints

- Work only in `.worktrees/phase-9-llm-reasoning` on `codex/phase-9-llm-reasoning`.
- Preserve base commit `f7f9a62e8af43700f2a68c901bb1b0af1b80090f` and all Phase 8 behavior.
- Do not commit, push, merge, or begin Phase 9 Task 2 unless the user separately authorizes it.
- Add no required Ollama Python dependency; production HTTP uses the Python standard library.
- Accept loopback Ollama endpoints only in V1.
- Support only `REFLECTION_EXPLANATION` and controlled, bounded, sanitized context.
- Store exact sanitized context and its canonical digest.
- Never request or persist hidden chain-of-thought.
- Final OOS, RAG, embeddings, Experience Graph, runtime/policy mutation, proposal promotion,
  deployment, broker/MT5, training, tuning, and fast-path integration remain inaccessible.
- Do not claim independent LLM generations are byte-deterministic. Guarantee only semantic request
  identity, strict validation, content-addressed response identity, canonical bytes, and exact-result
  reuse.
- Use test-first development. After each task, inspect `git diff --check`; do not create a commit at
  task boundaries without explicit user authorization.

## File Structure

**Create:**

- `src/axq/reasoning/__init__.py` — public offline reasoning exports.
- `src/axq/reasoning/contracts.py` — strict immutable schemas and content identities.
- `src/axq/reasoning/prompts.py` — one versioned code-owned reflection prompt and renderer.
- `src/axq/reasoning/provider.py` — provider/completion protocols and in-memory result types.
- `src/axq/reasoning/ollama.py` — loopback URL validation and native Ollama HTTP adapter.
- `src/axq/reasoning/store.py` — append-only SQLite persistence and verified reads.
- `src/axq/reasoning/service.py` — request creation, reuse, invocation, validation, and audit flow.
- `src/axq/reasoning/cli.py` — run/show/history/summary command handlers.
- `src/axq/reasoning/__main__.py` — module CLI entry point.
- `database/migrations/016_llm_reasoning_audit.sql` — three append-only reasoning tables.
- `tests/reasoning_test_support.py` — deterministic identities, contexts, clocks, and fake provider.
- `tests/test_reasoning_contracts.py` — schema, identity, bounds, UTC, and canonical-byte tests.
- `tests/test_reasoning_prompts.py` — prompt ownership and deterministic rendering tests.
- `tests/test_ollama_provider.py` — URL, preflight, payload, response, and failure mapping tests.
- `tests/test_reasoning_store.py` — migration, linkage, append-only, idempotency, and conflict tests.
- `tests/test_reasoning_service.py` — completion, failure, retry, reuse, and nondeterminism tests.
- `tests/test_reasoning_cli.py` — canonical CLI run/show/history/summary tests.
- `tests/test_reasoning_boundaries.py` — forbidden-import and Phase 8 mutation-safety tests.
- `tests/fixtures/reasoning/reflection_explanation_input.json` — tiny controlled input fixture.
- `docs/llm_reasoning.md` — operator-facing contracts and commands.

**Modify during final documentation task only:**

- `docs/project_status.md` — mark Phase 9 Task 1 implemented after validation.
- `docs/architecture.md` — add the offline reasoning boundary to the system overview.
- `docs/agentic_architecture.md` — replace the Task 1 Ollama-unimplemented statement precisely.
- `docs/decision_log.md` — record the local structured-output and determinism boundary.
- `docs/runbook.md` — add controlled local Ollama and fake-fixture commands.
- `README.md` — add a concise optional reasoning entry point.
- `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` — one final Graphify refresh.

---

### Task 1: Contract foundation and canonical identities

**Files:**

- Create: `src/axq/reasoning/contracts.py`
- Create: `src/axq/reasoning/__init__.py`
- Create: `tests/reasoning_test_support.py`
- Create: `tests/test_reasoning_contracts.py`

**Interfaces:**

- Consumes: `axq.runtime.state.UTCDateTime`, `axq.versioning.canonical_hash`, Pydantic strict models.
- Produces: `ReasoningTask`, `ReasoningSourceKind`, `ProviderKind`, `ProviderModelIdentity`,
  `PromptTemplateIdentity`, `BoundedReasoningContextItem`, `LLMGenerationPolicy`,
  `ReflectionExplanationInput`, `LLMRequestEnvelope`, `UncertaintyAssessment`,
  `ReflectionExplanation`, `LLMStructuredResponseArtifact`, `LLMAttemptStatus`,
  `LLMFailureMetadata`, `LLMExecutionAttemptAudit`, `LLMReusePolicy`, `ReasoningRunResult`, and
  `canonical_reasoning_bytes(value: BaseModel) -> bytes`.

- [ ] **Step 1: Write failing tests for strict immutable primitives**

Add tests that construct one exact provider identity and source reference, reject extra fields,
reject mutation, reject blank IDs/digests, and normalize source/context tuples. Use explicit fixture
values rather than random UUIDs:

```python
def test_provider_identity_is_strict_frozen_and_content_addressable() -> None:
    identity = provider_identity()
    assert identity.provider is ProviderKind.OLLAMA
    assert identity.model_digest == "sha256:" + "a" * 64
    with pytest.raises(ValidationError):
        identity.model_copy(update={"unexpected": True})
    with pytest.raises(ValidationError):
        identity.model_validate(identity.model_dump() | {"unexpected": True})
```

- [ ] **Step 2: Run the primitive contract tests and verify failure**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_contracts.py -v
```

Expected: collection fails because `axq.reasoning.contracts` does not exist.

- [ ] **Step 3: Implement the strict base enums and value contracts**

Define a frozen base model and exact enums:

```python
class ReasoningModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ReasoningTask(StrEnum):
    REFLECTION_EXPLANATION = "REFLECTION_EXPLANATION"


class LLMReusePolicy(StrEnum):
    NEVER_REUSE = "NEVER_REUSE"
    REUSE_FIRST_COMPLETED_EXACT = "REUSE_FIRST_COMPLETED_EXACT"
```

Add the remaining enums and bounded value models named in the interface block. Require the expected
Ollama server version and expected model digest in `ProviderModelIdentity`; these are controlled
semantic inputs that the provider later verifies. This lets a valid request be persisted before a
network/model preflight failure. Model family and quantization are optional identity facts: when a
controlled input supplies them, provider preflight must match them; otherwise the exact model digest
remains authoritative and observed family/quantization stay safe attempt metadata rather than
silently changing the persisted request after verification.

- [ ] **Step 4: Write failing identity and UTC tests**

Cover these exact cases:

```python
@pytest.mark.parametrize("changed", [
    "adapter_version", "provider_server_version", "model_name", "model_digest",
])
def test_request_identity_changes_with_provider_or_model(changed: str) -> None: ...

def test_request_identity_ignores_operational_attempt_times() -> None: ...

def test_attempt_rejects_naive_or_non_utc_times() -> None: ...

def test_response_identity_changes_when_structured_content_changes() -> None: ...
```

The operational-time test must construct two attempt audits with later timestamps but prove that
request identity and response identity remain unchanged. Attempt IDs may differ only when the
explicit attempt key or terminal semantic outcome differs.

- [ ] **Step 5: Implement normalization, validation, and content-addressed IDs**

Use validators that replace caller ordering with canonical ordering before hashing. Compute IDs from
`model_dump(mode="json", exclude={...})`:

```python
expected = f"llm-request-{canonical_hash(identity)[:20]}"
expected_response = f"llm-response-{canonical_hash(identity)[:20]}"
expected_attempt = f"llm-attempt-{canonical_hash(identity)[:20]}"
```

Validate context limits of 16 items, 2,000 characters per canonical item, and 16,000 aggregate
characters. Recompute every supplied context and response digest from canonical compact JSON and
reject mismatches. Require UTC offset exactly zero, not merely timezone awareness.

- [ ] **Step 6: Implement structured-response semantic checks**

Require `ReflectionExplanation` to contain only explanation, cited IDs, hypothesis, uncertainty, and
next investigation. Define:

```python
class UncertaintyLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class UncertaintyAssessment(ReasoningModel):
    level: UncertaintyLevel
    basis: str = Field(min_length=1, max_length=300)
```

Validate citation membership against the request when building `LLMStructuredResponseArtifact`.
Require at least one normalized citation. Do not add any reasoning-trace or chain-of-thought field.

- [ ] **Step 7: Run contract tests and inspect the diff**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_contracts.py -v
git diff --check
```

Expected: all contract tests pass and diff check is silent.

---

### Task 2: Code-owned prompt and provider-neutral protocol

**Files:**

- Create: `src/axq/reasoning/prompts.py`
- Create: `src/axq/reasoning/provider.py`
- Create: `tests/test_reasoning_prompts.py`
- Modify: `src/axq/reasoning/__init__.py`

**Interfaces:**

- Consumes: Task 1 request, response, provider identity, and failure contracts.
- Produces: `RenderedReasoningPrompt`, `reflection_explanation_prompt_identity()`,
  `render_reflection_explanation_prompt(input)`, `LLMProvider`, `ProviderCompletion`,
  `ProviderUsage`, `ProviderAttemptControls`, and typed provider exceptions.

- [ ] **Step 1: Write failing deterministic prompt tests**

Prove identical normalized input produces identical system text, user text, rendered digest, prompt
identity, and response-schema digest. Prove reversed caller ordering yields the same output. Assert
that arbitrary prompt text is not accepted and these forbidden terms are absent from persisted
fields: `chain_of_thought`, `thinking`, `tool_calls`, `trading_action`.

- [ ] **Step 2: Run prompt tests and verify failure**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_prompts.py -v
```

Expected: imports fail because prompt/provider modules do not exist.

- [ ] **Step 3: Implement the one versioned prompt renderer**

Define constants for `REFLECTION_EXPLANATION_V1`, the exact system template, and the exact user
template. Render only canonical JSON from `ReflectionExplanationInput`; do not interpolate operator
instructions. Return:

```python
class RenderedReasoningPrompt(NamedTuple):
    system: str
    user: str
    response_schema: dict[str, object]
    rendered_digest: str
```

The system prompt must state that output is descriptive, citations must come from allowed IDs, no
trading action is authorized, and only the supplied JSON schema may be emitted.

- [ ] **Step 4: Implement the provider-neutral protocol and in-memory completion types**

Use exact protocol signatures:

```python
class LLMProvider(Protocol):
    def verify_identity(
        self, expected: ProviderModelIdentity, *, timeout_seconds: float
    ) -> ProviderModelIdentity: ...

    def complete(
        self,
        request: LLMRequestEnvelope,
        prompt: RenderedReasoningPrompt,
        *,
        controls: ProviderAttemptControls,
    ) -> ProviderCompletion: ...
```

`ProviderCompletion` may hold raw response text in memory long enough for strict parsing, plus safe
usage data, raw digest/size, and an `unexpected_thinking` boolean. It must not expose a persistence
method. Define typed exceptions carrying only a safe code, safe message, optional HTTP status, raw
digest, and raw byte count.

- [ ] **Step 5: Run prompt/protocol tests and inspect the diff**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_prompts.py tests/test_reasoning_contracts.py -v
git diff --check
```

Expected: both files pass.

---

### Task 3: Loopback-only native Ollama adapter

**Files:**

- Create: `src/axq/reasoning/ollama.py`
- Create: `tests/test_ollama_provider.py`
- Modify: `src/axq/reasoning/__init__.py`

**Interfaces:**

- Consumes: Task 2 `LLMProvider`, prompt, controls, completion, and typed exceptions.
- Produces: `OllamaHTTPTransport`, `OllamaProvider`, `validate_loopback_ollama_url(url: str) -> str`,
  and an internal injectable `OllamaTransport` protocol.

- [ ] **Step 1: Write failing loopback and identity-preflight tests**

Test acceptance of `http://localhost:11434`, `http://127.0.0.1:11434`, and bracketed IPv6 loopback.
Reject HTTPS cloud hosts, LAN addresses, credentials, query strings, fragments, non-HTTP schemes,
and paths outside the API root. With a fake transport, verify exact `/api/version` and `/api/tags`
reads and fail closed for missing, ambiguous, or mismatched model/server identity.

- [ ] **Step 2: Run the focused tests and verify failure**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_ollama_provider.py -v
```

Expected: import failure for `axq.reasoning.ollama`.

- [ ] **Step 3: Implement URL validation and standard-library transport**

Use `urllib.parse.urlsplit`, `ipaddress.ip_address`, `urllib.request.Request`, and
`urllib.request.urlopen`. Normalize the endpoint to an API root, cap response reads at
`response_byte_limit + 1`, and translate `HTTPError`, `URLError`, `TimeoutError`, `socket.timeout`,
invalid JSON, and over-size responses into typed safe provider failures. Do not import a third-party
HTTP or Ollama package.

- [ ] **Step 4: Write failing chat-payload and metadata tests**

Assert the exact outbound body includes:

```python
{
    "model": expected.resolved_model_name,
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
```

Verify prompt/output token counts and Ollama nanosecond durations map to `ProviderUsage`. Supply a
fake response containing `thinking="secret trace"` and prove the completion stores only the boolean
that unexpected thinking was present, never its contents.

- [ ] **Step 5: Implement identity verification and chat completion**

Require observed server version, model name, digest, family, and quantization to equal the persisted
expected identity. Set `stream=false` and `think=false`; reject missing completion content or
non-terminal responses. Compute raw digest and size in memory, but return no raw thinking field.

- [ ] **Step 6: Add complete failure-mapping tests**

Cover timeout, connection refusal, HTTP 400/404/500, invalid provider JSON, missing model, identity
mismatch, malformed chat payload, and response-size overflow. Assert safe failure messages contain no
raw provider output, local filesystem path, authorization header, or stack trace.

- [ ] **Step 7: Run Ollama and existing reasoning tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_ollama_provider.py tests/test_reasoning_contracts.py tests/test_reasoning_prompts.py -v
git diff --check
```

Expected: all focused tests pass without a running Ollama service.

---

### Task 4: Append-only reasoning migration and store

**Files:**

- Create: `database/migrations/016_llm_reasoning_audit.sql`
- Create: `src/axq/reasoning/store.py`
- Create: `tests/test_reasoning_store.py`
- Modify: `src/axq/reasoning/__init__.py`

**Interfaces:**

- Consumes: Task 1 request, response, and attempt contracts;
  `canonical_reasoning_bytes(value: BaseModel) -> bytes`; `Database`.
- Produces: `SQLiteLLMReasoningStore` with `append_request`, `append_response`, `append_attempt`,
  `request`, `response`, `attempt`, `attempts`, `first_completed_response`, `requests`, `responses`,
  `all_attempts`, and `sync`.

- [ ] **Step 1: Write failing migration and append-only tests**

Create a temporary store, append one request/response/attempt chain, and assert exact canonical bytes
round-trip. Direct SQL `UPDATE` and `DELETE` against all three tables must raise
`sqlite3.IntegrityError` with the append-only trigger message.

- [ ] **Step 2: Run store tests and verify failure**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_store.py -v
```

Expected: missing migration/store failure.

- [ ] **Step 3: Add migration 016**

Create `llm_request_envelopes`, `llm_structured_responses`, and `llm_execution_attempts`. Store each
canonical JSON payload and payload hash. Add exact foreign keys, indexes for request history, a
unique `(request_id, attempt_key)` constraint, and UPDATE/DELETE rejection triggers for every table.
Do not add a current-result table.

- [ ] **Step 4: Implement verified request and response persistence**

Use the established store rule:

```python
if existing_payload == canonical_payload:
    return False
if existing_payload is not None:
    raise ValueError("... ID already exists with different content")
```

Before appending a response, load and validate its request, provider/model identity, request ID, and
structured digest. Reject orphan or inconsistent responses.

- [ ] **Step 5: Implement verified attempt persistence and reads**

Completed/reused attempts must reference an exact stored response. Failure attempts cannot reference
a response. Enforce time ordering `requested_at <= started_at <= completed_at`. Enforce unique
attempt keys and exact-byte idempotency. Validate payload hashes and semantic IDs on every read.

- [ ] **Step 6: Write failure-history, conflict, and first-completed tests**

Append `TIMEOUT`, then `COMPLETED`, then `REUSED`; prove all remain in sequence and
`first_completed_response(request_id)` returns the response linked by the earliest committed
`COMPLETED`, never a failure or a later alternative. Prove altered stored JSON or digest fails closed.

- [ ] **Step 7: Run store and contract tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_store.py tests/test_reasoning_contracts.py -v
git diff --check
```

Expected: all focused tests pass.

---

### Task 5: Offline reasoning service, failures, and deterministic reuse

**Files:**

- Create: `src/axq/reasoning/service.py`
- Create: `tests/test_reasoning_service.py`
- Modify: `tests/reasoning_test_support.py`
- Modify: `src/axq/reasoning/__init__.py`

**Interfaces:**

- Consumes: Task 1 contracts, Task 2 prompt/provider interfaces, and Task 4 store.
- Produces: `build_reflection_explanation_request(...) -> LLMRequestEnvelope` and
  `run_reflection_explanation(...) -> ReasoningRunResult`.

- [ ] **Step 1: Write a failing successful-run service test**

Use a fake provider whose expected identity and one raw structured response are fixed. Call:

```python
result = run_reflection_explanation(
    input_record=input_record(),
    provider=fake_provider,
    store=store,
    attempt_key="fixture-attempt-001",
    reuse_policy=LLMReusePolicy.REUSE_FIRST_COMPLETED_EXACT,
    requested_at=utc("2026-09-12T00:00:00Z"),
    started_at=utc("2026-09-12T00:00:01Z"),
    completed_at=utc("2026-09-12T00:00:02Z"),
    timeout_seconds=30.0,
)
```

Assert one request, one response, and one completed attempt are stored; citations match exact allowed
IDs; and the emitted response bytes equal the stored canonical bytes.

- [ ] **Step 2: Run the service test and verify failure**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_service.py -v
```

Expected: missing service functions.

- [ ] **Step 3: Implement request construction and successful execution**

Build and persist the request from the controlled expected provider identity before calling
`provider.verify_identity`. Verify observed identity exactly, render the prompt, call completion,
parse with `ReflectionExplanation.model_validate_json`, verify citations, append the response, then
append a completed attempt. Always produce compact sorted ASCII JSON through one canonical helper.

- [ ] **Step 4: Write failing reuse and fresh-generation tests**

Test that a later operational timestamp and new attempt key under
`REUSE_FIRST_COMPLETED_EXACT`:

- preserves request and response IDs;
- emits byte-identical response JSON;
- increments attempts with `REUSED`;
- does not increment fake-provider verification or completion call counts.

Under `NEVER_REUSE`, return a different valid explanation and prove the provider runs again, a
second response ID is appended, and no claim of independent byte determinism is made.

- [ ] **Step 5: Implement exact completed-result reuse**

Before provider verification, ask the store for the first exact completed response. Revalidate the
request bytes, response bytes, digest, and provider/model identity. Append a `REUSED` attempt with
the new operational times and unchanged response linkage. Never reuse failures or invalid output.

- [ ] **Step 6: Write failing typed-failure audit tests**

Parametrize every terminal failure status. Prove provider identity mismatch, timeout, connection,
HTTP, model unavailable, malformed JSON, extra response fields, false citations, excessive output,
and unexpected thinking all create the approved failure or invalid-response audit. For malformed
output, assert only digest and byte count are stored. Assert the raw string and exception traceback
are absent from database bytes.

- [ ] **Step 7: Implement failure mapping and guaranteed terminal audit**

Catch only typed provider failures plus Pydantic/JSON validation errors. Sanitize messages through a
single bounded function. Append a terminal audit after every valid persisted request attempt.
Unexpected thinking must make the output invalid rather than silently accepting a provider contract
violation; persist only the safe `INVALID_RESPONSE` metadata.

- [ ] **Step 8: Add attempt-key idempotency and conflict tests**

An identical repeat with the same request, attempt key, outcome, and semantic linkage must return the
existing audit. Reusing the attempt key with different outcome/response/failure must raise before a
provider call. A later success after a failed attempt must use a new key and preserve the failure.

- [ ] **Step 9: Run service, store, provider, and contract tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_service.py tests/test_reasoning_store.py tests/test_ollama_provider.py tests/test_reasoning_contracts.py tests/test_reasoning_prompts.py -v
git diff --check
```

Expected: all focused tests pass.

---

### Task 6: Controlled CLI and canonical fixture artifacts

**Files:**

- Create: `src/axq/reasoning/cli.py`
- Create: `src/axq/reasoning/__main__.py`
- Create: `tests/test_reasoning_cli.py`
- Create: `tests/fixtures/reasoning/reflection_explanation_input.json`
- Modify: `src/axq/reasoning/__init__.py`

**Interfaces:**

- Consumes: Task 5 service and Task 4 store.
- Produces: `python -m axq.reasoning` commands `run-reflection-explanation`, `show-request`,
  `show-response`, `show-history`, and `reasoning-summary`.

- [ ] **Step 1: Write failing parser and controlled-input tests**

Assert the run command requires store, input, output, attempt key, model name, expected model digest,
expected Ollama version, and timeout. Assert reuse defaults to `REUSE_FIRST_COMPLETED_EXACT` and the
endpoint defaults to `http://127.0.0.1:11434`. Prove there are no arguments for arbitrary prompts,
Final OOS, runtime, broker, MT5, tools, URLs, retrieval, or credentials.

- [ ] **Step 2: Run CLI tests and verify failure**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_cli.py -v
```

Expected: missing CLI module/commands.

- [ ] **Step 3: Implement the command parser and dispatch**

Keep handlers small and emit only:

```python
print(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
```

Load the controlled input using strict `ReflectionExplanationInput.model_validate_json`. Build
`OllamaProvider` only inside the run handler. Show/history/summary handlers must not initialize a
provider or connect to Ollama.

- [ ] **Step 4: Implement canonical output-file writing**

Write a canonical `ReasoningRunResult` artifact atomically to the requested ignored runtime path.
The output contains request ID, response ID when valid, attempt ID, terminal status, reuse flag, and
safe failure metadata. It contains no raw invalid provider output or hidden thinking.

- [ ] **Step 5: Add fake-provider CLI injection and end-to-end tests**

Expose an internal `main(argv, *, provider_factory=...)` test seam. Run a successful fixture, show
its request and response, inspect history, and summarize counts. Rerun with later timestamps and a
new attempt key; assert the provider completion count remains one and response JSON bytes remain
identical.

- [ ] **Step 6: Run all reasoning CLI and service tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_cli.py tests/test_reasoning_service.py tests/test_reasoning_store.py -v
git diff --check
```

Expected: all focused tests pass.

---

### Task 7: Forbidden-scope and mutation-safety audit

**Files:**

- Create: `tests/test_reasoning_boundaries.py`
- Modify only if a failing audit proves necessary: files under `src/axq/reasoning/`

**Interfaces:**

- Consumes: complete Task 1 reasoning package and immutable Phase 8 fixture records.
- Produces: executable proof that reasoning remains offline and advisory.

- [ ] **Step 1: Write static import-boundary tests**

Parse every Python file under `src/axq/reasoning` with `ast` and reject imports rooted at:

```python
FORBIDDEN = {
    "axq.orchestration", "axq.master", "axq.discipline", "axq.risk_boundary",
    "axq.execution_boundary", "axq.position_management", "axq.position_actions",
    "axq.mt5", "axq.replay_validation", "axq.quant", "MetaTrader5",
}
```

Also search source text for Final-OOS readers, embedding endpoints, vector-store packages, subprocess
execution, dynamic imports, and provider tool calls.

- [ ] **Step 2: Write reverse-dependency tests for the fast path**

Parse runtime, agents, tools, Master, Discipline, Risk, execution, position, MT5, and orchestration
packages and assert none import `axq.reasoning`. Importing `axq.reasoning` must not connect to a
network or instantiate `OllamaProvider`.

- [ ] **Step 3: Write Phase 8 mutation-safety tests**

Serialize controlled DailyReflection, WeeklyReflection, Pattern, and ImprovementProposal records
before and after a reasoning run. Assert byte equality, unchanged proposal lifecycle status, and no
new rows in Phase 8 proposal/evaluation/review/authorization tables.

- [ ] **Step 4: Run the safety audit and all focused Task 1 tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_boundaries.py tests/test_reasoning_contracts.py tests/test_reasoning_prompts.py tests/test_ollama_provider.py tests/test_reasoning_store.py tests/test_reasoning_service.py tests/test_reasoning_cli.py -v
git diff --check
```

Expected: all focused tests pass and no source change outside `axq.reasoning` is needed.

---

### Task 8: Documentation, measured fixture report, and Graphify refresh

**Files:**

- Create: `docs/llm_reasoning.md`
- Modify: `README.md`
- Modify: `docs/project_status.md`
- Modify: `docs/agentic_architecture.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**

- Consumes: final Task 1 contracts, commands, measured controlled-fixture output, and test results.
- Produces: accurate operator guidance and current durable project context.

- [ ] **Step 1: Run one fake-provider fixture and capture measured counts**

Use the test seam or a dedicated test helper, never a real network call, to create an ignored
temporary SQLite store and canonical result. Record exact request/response/attempt counts, status
breakdown, reuse behavior, output size, and database size for documentation.

- [ ] **Step 2: Write operator documentation with exact commands**

Document the semantic-versus-generative determinism boundary, Ollama prerequisites, loopback-only
restriction, expected server/model identity, context limits, failure states, reuse policies, storage
tables, privacy behavior, and these command forms:

```powershell
$ollamaRoot = 'http://127.0.0.1:11434'
$ollamaVersion = (Invoke-RestMethod "$ollamaRoot/api/version").version
$model = (Invoke-RestMethod "$ollamaRoot/api/tags").models[0]
& '..\..\.venv\Scripts\python.exe' -m axq.reasoning run-reflection-explanation --store 'runtime/phase9_reasoning.sqlite3' --input 'tests/fixtures/reasoning/reflection_explanation_input.json' --output 'runtime/reflection_explanation.json' --attempt-key 'operator-smoke-001' --model $model.name --expected-model-digest $model.digest --expected-ollama-version $ollamaVersion
$result = Get-Content -Raw 'runtime/reflection_explanation.json' | ConvertFrom-Json
& '..\..\.venv\Scripts\python.exe' -m axq.reasoning show-request --store 'runtime/phase9_reasoning.sqlite3' --request-id $result.request_id
& '..\..\.venv\Scripts\python.exe' -m axq.reasoning show-response --store 'runtime/phase9_reasoning.sqlite3' --response-id $result.response_id
& '..\..\.venv\Scripts\python.exe' -m axq.reasoning show-history --store 'runtime/phase9_reasoning.sqlite3' --request-id $result.request_id
& '..\..\.venv\Scripts\python.exe' -m axq.reasoning reasoning-summary --store 'runtime/phase9_reasoning.sqlite3'
```

State clearly that the real Ollama smoke test is optional and that no independent-generation byte
determinism is promised.

- [ ] **Step 3: Update architecture, status, decision log, runbook, and README narrowly**

Mark only Task 1 complete after its gate passes. Replace obsolete claims that all Ollama integration
is unimplemented, while retaining later LLM/RAG/graph/runtime work as unimplemented. Do not rewrite
Phase 6-8 history.

- [ ] **Step 4: Refresh Graphify exactly once**

```powershell
graphify update .
graphify cluster-only . --no-label
```

Confirm only tracked `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` durable outputs are
included; generated HTML/cache files remain ignored.

- [ ] **Step 5: Run documentation and diff checks**

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors and only intended Task 1 files are modified/untracked.

---

### Task 9: Final lightweight validation and completion audit

**Files:**

- Modify only when a failing Task 1 test proves a genuine Task 1 defect.

**Interfaces:**

- Consumes: completed Tasks 1-8.
- Produces: final evidence that Task 1 is ready for a separately authorized checkpoint commit.

- [ ] **Step 1: Run the complete reasoning-focused suite once**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_reasoning_contracts.py tests/test_reasoning_prompts.py tests/test_ollama_provider.py tests/test_reasoning_store.py tests/test_reasoning_service.py tests/test_reasoning_cli.py tests/test_reasoning_boundaries.py -v
```

Expected: all Task 1 tests pass.

- [ ] **Step 2: Run the full repository gate once**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest
& '..\..\.venv\Scripts\python.exe' -m ruff check .
& '..\..\.venv\Scripts\python.exe' -m mypy src/axq --no-warn-unused-ignores
& '..\..\.venv\Scripts\python.exe' -m pip check
git diff --check
```

Expected: pytest, Ruff, strict mypy, pip integrity, and diff check all pass.

- [ ] **Step 3: Audit repository scope and prohibited behavior**

Run:

```powershell
git status --short
git diff --stat
rg -n "MetaTrader5|order_send|FINAL_OOS|subprocess|embedding|vector|tool_calls" src/axq/reasoning tests/test_reasoning_*.py
rg -n "axq\.reasoning" src/axq/runtime src/axq/agents src/axq/tools src/axq/master src/axq/discipline src/axq/risk_boundary src/axq/execution_boundary src/axq/position_management src/axq/position_actions src/axq/mt5 src/axq/orchestration
```

Interpret expected prompt/schema mentions carefully, but require zero forbidden imports or calls and
zero fast-path references to `axq.reasoning`.

- [ ] **Step 4: Verify deterministic reuse and immutable failure history one final time**

Run the controlled fixture twice with later operational timestamps under exact completed reuse.
Compare canonical response files byte-for-byte and assert provider completion count is one. Run the
failure-then-success fixture and confirm both attempt records remain stored.

- [ ] **Step 5: Report without committing or starting Task 2**

Report provider boundary, request/response schemas, exact identities, request/response/attempt
counts, failure handling, reuse behavior, canonical artifact/database sizes, test results, exact CLI
commands, optional Ollama smoke status, files changed, known risks, and the recommended next Task 2
scope. Stop before any commit, push, merge, deployment, real proposal execution, or Task 2 work.
