# Phase 9 Task 2 Experience Retrieval and Embeddings Implementation Plan

> **Status:** PAUSED after the contract-foundation stage below. Only
> `src/axq/retrieval/contracts.py`, package exports, the additive Task 1 `EXPERIENCE` source kind,
> and their focused tests are implemented. Internal Tasks 2–11 have not started; there is no
> renderer, provider, store, index, ranking service, CLI, automatic Ollama call, or runtime path.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline, append-only, causally bounded retrieval layer that indexes exact Phase 8 evidence, ranks complete exact-vector candidate sets, and emits Task 1-compatible bounded context without gaining truth, trading, governance, or deployment authority.

**Architecture:** A separate `axq.retrieval` package reads allowlisted immutable Phase 8 stores through verified adapters, renders content-addressed evidence documents, and embeds them through a provider-neutral protocol with one loopback Ollama implementation. Exact little-endian float32 vectors and complete index/candidate manifests are persisted append-only; deterministic metadata filtering and brute-force cosine ranking produce a bounded retrieval result that a pure adapter can turn into the existing Task 1 input.

**Tech Stack:** Python 3.12, Pydantic 2, standard-library `urllib.request`, `struct`, `math`, `decimal`, and SQLite through `axq.database.Database`; pytest, Ruff, strict mypy, and Graphify.

**Spec:** `docs/superpowers/specs/2026-09-12-phase-9-task-2-experience-retrieval-embeddings-design.md`

## Global Constraints

- Work only in `.worktrees/phase-9-llm-reasoning` on `codex/phase-9-llm-reasoning` from checkpoint `9b9b70e1ff232550626c16e5cea98274a5795e52`, preserving the subsequently validated Task 1 `REFLECTION_EXPLANATION_V2` citation-contract fix already present in the working tree.
- Do not commit, push, merge, or begin Phase 9 Task 3 without separate authorization.
- Keep `axq.retrieval` offline-only; no fast-path package may import it.
- Support only exact immutable Phase 8 Experience, daily/weekly reflection, success/failure pattern, and ImprovementProposal sources.
- Add only the `EXPERIENCE` value to Task 1 `ReasoningSourceKind`; do not change the active Task 1 V2 prompt text, request-specific citation allowlist/schema behavior, service, store, or provider behavior.
- Accept only code-owned source-derived queries; no arbitrary natural-language query input.
- V1 uses loopback Ollama with configured name `nomic-embed-text:v1.5`, exact resolved name/digest, expected 768 dimensions, and the versioned Nomic query/document prefix profile.
- The configured name alone is never authoritative embedding identity.
- Store canonical vectors as `IEEE754_FLOAT32_LE_V1` BLOBs and rank only exact stored bytes.
- Metadata/time filters run before semantic similarity; a filtered item cannot be reintroduced by ranking.
- Require complete index and candidate manifests; never silently search a partial index.
- Maximum retrieval `top_k` is eight; similarity scores remain outside Task 1 LLM context.
- Exact first-completed embedding reuse is the default; fresh generations are not claimed byte-deterministic.
- Select the latest causally available revision only in explicit supersession chains; retain all history append-only and do not collapse ordinary recurring `pattern_key` observations.
- Retrieval is non-authoritative evidence only.
- Final OOS, dataset readers, replay, training, runtime, agents, Master, Discipline, Risk, execution, position management, broker, MT5, proposal promotion/transition, deployment, RAG, vector stores/extensions, Experience Graph, subprocess/plugins, arbitrary web/file retrieval, and hidden chain-of-thought remain inaccessible.
- Real Ollama smoke and large one-month indexing are optional user-run work, not acceptance requirements.
- Use focused tests during stages. Run the full repository gate and Graphify refresh only at the separately approved final stage.

### Non-blocking Task 1 smoke follow-ups

The real Ollama vertical smoke completed with one valid V2 response and no failed attempts. Preserve
these observations as follow-up work outside Task 2:

- `local_elapsed_ms` currently remains `0.0` in CLI-driven real-provider attempts even though
  provider duration metadata is present;
- `llama3.2` may produce weak or noisy prose inside otherwise schema-valid fields.

Neither observation changes retrieval contracts or blocks Task 2. Do not redesign Task 1, add prose
quality scoring, or change Task 1 timing instrumentation while executing this plan.

### Authoritative post-spec identity clarification

`timeout_seconds` and maximum provider response bytes are execution controls only. They must exist in
`EmbeddingAttemptControls` and be copied into `EmbeddingAttemptAudit`, but they must not be fields in
`EmbeddingRequest` and must not participate in `embedding_request_id`.

Embedding request identity is based only on:

- exact provider/model identity;
- `DOCUMENT` versus `QUERY` role;
- exact canonical content and prefixed-text digests;
- prefix/profile identity;
- dimension and vector-encoding contract.

Changing only timeout or response-size controls must preserve the request ID. The resulting attempts
remain distinguishable and fully auditable through attempt key, controls, terminal outcome, vector or
failure linkage, and operational timing.

## File Structure

**Create:**

- `src/axq/retrieval/__init__.py` — public offline retrieval exports only.
- `src/axq/retrieval/contracts.py` — strict evidence, embedding, execution-control, manifest, request, result, and audit schemas.
- `src/axq/retrieval/rendering.py` — code-owned source and query renderers plus renderer/profile identities.
- `src/axq/retrieval/sources.py` — allowlisted read-only Phase 8 source catalog and exact provenance resolution.
- `src/axq/retrieval/provider.py` — embedding provider protocol, in-memory results, and typed safe failures.
- `src/axq/retrieval/vectors.py` — canonical float32 codec, validation, cosine scoring, and Decimal quantization.
- `src/axq/retrieval/ollama.py` — loopback native Ollama embedding adapter.
- `src/axq/retrieval/store.py` — append-only SQLite persistence and verified reads.
- `src/axq/retrieval/indexing.py` — deterministic document enumeration, embedding reuse, and complete index publication.
- `src/axq/retrieval/ranking.py` — metadata-first candidate construction and deterministic ranking.
- `src/axq/retrieval/service.py` — retrieval orchestration and pure Task 1 input adapter.
- `src/axq/retrieval/cli.py` — controlled build/run/show/summary commands.
- `src/axq/retrieval/__main__.py` — `python -m axq.retrieval` entry point.
- `database/migrations/017_experience_retrieval_embeddings.sql` — append-only Task 2 schema.
- `tests/retrieval_test_support.py` — exact Phase 8 fixtures, fake vectors/provider, clocks, and source catalog.
- `tests/test_retrieval_contracts.py` — schema, identity, UTC, bounds, and Task 1 source-kind tests.
- `tests/test_retrieval_rendering.py` — source/query rendering and provenance tests.
- `tests/test_embedding_provider.py` — provider protocol and safe failure tests.
- `tests/test_retrieval_vectors.py` — float codec, cosine, Decimal, and tie tests.
- `tests/test_ollama_embedding_provider.py` — loopback identity and `/api/embed` tests.
- `tests/test_retrieval_store.py` — migration, append-only, linkage, idempotency, and corruption tests.
- `tests/test_retrieval_indexing.py` — incremental index, supersession, reuse, and completeness tests.
- `tests/test_retrieval_ranking.py` — candidate construction, filters, causality, ranking, and top-k tests.
- `tests/test_retrieval_service.py` — orchestration and Task 1 context compatibility tests.
- `tests/test_retrieval_cli.py` — canonical CLI and read-only inspection tests.
- `tests/test_retrieval_boundaries.py` — forbidden-import, Phase 8 mutation, and Task 1 stability tests.
- `tests/fixtures/retrieval/controlled_query.json` — one canonical source-derived query fixture.
- `docs/experience_retrieval.md` — operator contract, identity, commands, and non-goals.

**Modify:**

- `src/axq/reasoning/contracts.py` — add only `ReasoningSourceKind.EXPERIENCE`.
- `README.md` — add the completed offline retrieval capability and documentation link.
- `docs/agentic_architecture.md` — place retrieval between immutable Phase 8 evidence and Task 1 reasoning.
- `docs/project_status.md` — record measured controlled-fixture results and remaining boundaries.
- `docs/decision_log.md` — record exact-vector, metadata-first, non-authoritative retrieval decision.
- `docs/runbook.md` — add build, retrieve, inspect, and Task 1 input commands.
- `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` — one final refresh after code/docs stabilize.

No existing Phase 8 source-store schema is modified.

---

### Task 1: Contract foundation and Task 1 source compatibility

**Files:**

- Create: `src/axq/retrieval/contracts.py`
- Create: `src/axq/retrieval/__init__.py`
- Create: `tests/test_retrieval_contracts.py`
- Create: `tests/retrieval_test_support.py`
- Modify: `src/axq/reasoning/contracts.py`

**Interfaces:**

- Consumes: `axq.versioning.canonical_hash`, Phase 8 enums, Task 1 strict UTC/canonical conventions.
- Produces: all immutable Task 2 enums, `EmbeddingAttemptControls`, and data contracts used by later tasks; additive `ReasoningSourceKind.EXPERIENCE`.

- [x] **Step 1: Write failing Task 1 compatibility tests**

Add tests that assert the new source kind is accepted while these existing identities remain exact:

```python
def test_experience_source_kind_does_not_change_task1_prompt_or_schema_identity() -> None:
    input_record = ReflectionExplanationInput.model_validate_json(
        Path("tests/fixtures/reasoning/reflection_explanation_input.json").read_bytes()
    )
    identity = reflection_explanation_prompt_identity(input_record)
    rendered = render_reflection_explanation_prompt(input_record)
    assert ReasoningSourceKind.EXPERIENCE.value == "EXPERIENCE"
    assert identity.template_name == "REFLECTION_EXPLANATION_V2"
    assert identity.template_digest == (
        "eb84ab90ff749a2357d155a6d8409faf48349ee1949f030fe884f792dc638f84"
    )
    assert identity.response_schema_digest == (
        "00524fad3ad09d2663954865c46abe88ad3dec8153ce930af6fb76512666037a"
    )
    assert identity.response_schema_digest == canonical_hash(rendered.response_schema)
    assert rendered.response_schema["properties"]["cited_evidence_ids"]["items"][
        "enum"
    ] == ["context-weekly-summary", "weekly-reflection-aaaaaaaaaaaaaaaaaaaa"]
```

Assert an `EXPERIENCE` `ReasoningSourceReference` binds exact ID/digest and works in an otherwise
unchanged `ReflectionExplanationInput`.

- [x] **Step 2: Run the compatibility test and verify red**

Run:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src')
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_contracts.py -v
```

Expected: collection or assertion failure because `axq.retrieval.contracts` and
`ReasoningSourceKind.EXPERIENCE` do not exist.

- [x] **Step 3: Add the retrieval enums and strict base model**

Define a frozen `RetrievalModel` with `extra="forbid"` and schema version `1.0`. Add exact enums for:

```python
class RetrievalSourceKind(StrEnum):
    EXPERIENCE = "EXPERIENCE"
    DAILY_REFLECTION = "DAILY_REFLECTION"
    WEEKLY_REFLECTION = "WEEKLY_REFLECTION"
    SUCCESS_PATTERN = "SUCCESS_PATTERN"
    FAILURE_PATTERN = "FAILURE_PATTERN"
    IMPROVEMENT_PROPOSAL = "IMPROVEMENT_PROPOSAL"


class EmbeddingInputRole(StrEnum):
    DOCUMENT = "DOCUMENT"
    QUERY = "QUERY"


class EmbeddingReusePolicy(StrEnum):
    NEVER_REUSE = "NEVER_REUSE"
    REUSE_FIRST_COMPLETED_EXACT = "REUSE_FIRST_COMPLETED_EXACT"
```

Also define explicit terminal status/failure enums from the spec. Reuse the repository's strict UTC
validator behavior: reject naive and nonzero-offset datetimes rather than normalizing them silently.

- [x] **Step 4: Write failing identity and control-separation tests**

Cover exact field changes, canonical tuple ordering, top-k bounds, finite values, and these mandatory
control tests:

```python
def test_timeout_and_response_limit_do_not_change_embedding_request_identity() -> None:
    request = embedding_request()
    fast = EmbeddingAttemptControls(timeout_seconds=1.0, response_byte_limit=4_096)
    patient = EmbeddingAttemptControls(timeout_seconds=90.0, response_byte_limit=1_048_576)
    assert request.embedding_request_id == embedding_request().embedding_request_id
    assert fast != patient
    assert "timeout_seconds" not in type(request).model_fields
    assert "response_byte_limit" not in type(request).model_fields


def test_attempt_audit_preserves_execution_controls() -> None:
    audit = completed_embedding_attempt(
        timeout_seconds=90.0,
        response_byte_limit=1_048_576,
    )
    assert audit.timeout_seconds == 90.0
    assert audit.response_byte_limit == 1_048_576
```

Changing provider kind, adapter version, server version, resolved model name, exact model digest,
dimensions, family/quantization, prefix profile, role, content digest, prefixed-text digest, or vector
encoding must change the embedding request ID.

- [x] **Step 5: Implement exact evidence, model, embedding, manifest, retrieval, and audit contracts**

Implement named contracts from the spec with normalized tuple fields and content IDs. Define
`EmbeddingAttemptControls` here as a strict frozen execution-only contract, then keep
`EmbeddingRequest` exactly limited to:

```python
class EmbeddingRequest(RetrievalModel):
    embedding_request_id: str = ""
    provider_model: EmbeddingModelIdentity
    role: EmbeddingInputRole
    semantic_input_id: str
    canonical_content_digest: str
    prefixed_text_digest: str
    prefix_profile: EmbeddingPrefixProfileIdentity
    expected_dimensions: Literal[768] = 768
    vector_encoding: Literal["IEEE754_FLOAT32_LE_V1"] = "IEEE754_FLOAT32_LE_V1"
```

Compute `embedding_request_id` from all fields except itself. Put timeout and response-byte controls
only in `EmbeddingAttemptControls` and `EmbeddingAttemptAudit`. Exclude requested/started/completed
timestamps from semantic request, vector, index, and retrieval-result identity.

- [x] **Step 6: Implement the one additive Task 1 source-kind change**

Add `EXPERIENCE = "EXPERIENCE"` to `ReasoningSourceKind`. Do not edit the active Task 1 V2 prompts,
provider, service, store, CLI, or request-specific response schemas.

- [x] **Step 7: Run contract tests and diff hygiene**

Run:

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_contracts.py tests/test_reasoning_contracts.py tests/test_reasoning_prompts.py -v
git diff --check
```

Expected: all tests pass; the active V2 prompt and request-specific schema digest assertions remain
exact; diff check is clean.

Stop for stage review. Do not start Task 2 or commit.

---

### Task 2: Exact Phase 8 source adapters and code-owned rendering

**Files:**

- Create: `src/axq/retrieval/sources.py`
- Create: `src/axq/retrieval/rendering.py`
- Create: `tests/test_retrieval_rendering.py`
- Modify: `tests/retrieval_test_support.py`
- Modify: `src/axq/retrieval/__init__.py`

**Interfaces:**

- Consumes: Task 1 contracts; `SQLiteExperienceStore`, `SQLiteReflectionStore`,
  `SQLiteWeeklyReflectionStore`, and `SQLiteImprovementProposalStore` verified read APIs.
- Produces: `ExactPhase8SourceResolver`, `Phase8EvidenceSourceCatalog`,
  `evidence_renderer_identity()`, `render_evidence_document()`, `retrieval_query_renderer_identity()`,
  and `render_source_derived_query()`.

- [ ] **Step 1: Build exact controlled Phase 8 fixtures**

Create one immutable fixture for each supported source family using existing contract constructors.
Include an Experience with complete provenance, a revised DailyReflection chain, a revised
WeeklyReflection chain, one success and one failure pattern in an exact weekly parent, and a revised
ImprovementProposal chain. Persist them only to pytest temporary SQLite stores.

- [ ] **Step 2: Write failing source-resolution tests**

Assert:

- every source resolves by exact kind/ID;
- source canonical digest is recomputed, not trusted from caller input;
- pattern `available_at` equals the exact containing WeeklyReflection `available_at`;
- success/failure patterns map to distinct retrieval kinds and Task 1 `PATTERN`;
- missing pattern parent, conflicting duplicate parent, source digest mismatch, or missing supporting
  Phase 8 provenance fails closed;
- no store is mutated by enumeration or resolution.

- [ ] **Step 3: Run the source tests and verify red**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_rendering.py -v
```

Expected: missing adapter/renderer imports.

- [ ] **Step 4: Implement the fixed source catalog and exact resolver**

Define an explicit constructor accepting the four authoritative store objects. Do not accept a
dynamic module, class path, SQL string, callable registry, or raw filesystem glob. Enumerate records
in `(source_kind.value, semantic_id)` order. For patterns, enumerate exact pattern members from
verified WeeklyReflection records and require one exact containing parent.

Implement supersession replay by following only existing explicit `supersedes_*` fields. Detect
cycles, missing predecessors, forks within the same revision key, and successors unavailable at the
cutoff. Return the latest valid revision at or before cutoff; retain recurring weekly patterns as
distinct observations even when `pattern_key` matches.

- [ ] **Step 5: Write failing rendering and controlled-query tests**

Prove caller/store enumeration order does not affect renderer identity, document ID, metadata,
content, or embedding text. Assert each context payload is at most 1,500 canonical characters and
contains no storage path, score, rank, URL, secret-like field, or arbitrary prompt.

Assert query construction accepts an exact anchor reference plus renderer identity but no free-form
query string. Document and query text must begin with exact `search_document: ` and
`search_query: ` prefixes respectively.

- [ ] **Step 6: Implement versioned source and query rendering**

Use a discriminated renderer per source kind. Render canonical safe JSON containing meaningful facts
and metrics; keep long provenance ID lists in exact linkage rather than embedding text. Bind these
constants through an exact digest:

```python
DOCUMENT_PREFIX = "search_document: "
QUERY_PREFIX = "search_query: "
PREFIX_PROFILE_NAME = "NOMIC_RETRIEVAL_PREFIX_V1"
CONTEXT_PROFILE_NAME = "PHASE8_REASONING_CONTEXT_V1"
```

Build query content from the exact anchor's source type, categories, direction/session/regime,
findings, metrics, and reason codes defined by that source. There is no operator text field.

- [ ] **Step 7: Run rendering and contract tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_rendering.py tests/test_retrieval_contracts.py -v
git diff --check
```

Expected: all pass and source stores remain byte-identical.

Stop for stage review. Do not start Task 3 or commit.

---

### Task 3: Embedding provider protocol and canonical vector primitives

**Files:**

- Create: `src/axq/retrieval/provider.py`
- Create: `src/axq/retrieval/vectors.py`
- Create: `tests/test_embedding_provider.py`
- Create: `tests/test_retrieval_vectors.py`
- Modify: `src/axq/retrieval/__init__.py`

**Interfaces:**

- Consumes: Task 1 embedding contracts.
- Produces: `EmbeddingProvider`, `EmbeddingProviderResult`, typed provider exceptions,
  `encode_float32_le`, `decode_float32_le`, `validate_vector`, `cosine_similarity`, and
  `canonical_similarity_decimal`.

- [ ] **Step 1: Write failing provider-protocol tests**

Define a deterministic fake provider and assert runtime protocol compatibility. Its methods must be:

```python
class EmbeddingProvider(Protocol):
    def verify_identity(
        self,
        expected: EmbeddingModelIdentity,
        *,
        timeout_seconds: float,
    ) -> EmbeddingModelIdentity: ...

    def embed(
        self,
        request: EmbeddingRequest,
        *,
        controls: EmbeddingAttemptControls,
    ) -> EmbeddingProviderResult: ...
```

Assert typed failures expose only failure code, bounded safe message, optional HTTP status, response
digest, and response byte count. They must not expose raw bodies, headers, URLs containing
credentials, or tracebacks.

- [ ] **Step 2: Run provider tests and verify red**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_embedding_provider.py -v
```

Expected: missing provider module.

- [ ] **Step 3: Implement provider-neutral protocol, safe results, and failures**

Consume the already-defined `EmbeddingAttemptControls`, whose contract requires positive finite
`timeout_seconds` and bounded positive `response_byte_limit`. `EmbeddingProviderResult` contains only
validated numeric values in memory, safe usage/duration metadata, response digest/size, and observed
model name. It has no store method.

- [ ] **Step 4: Write failing canonical-vector and ranking-math tests**

Use fixed 768-element vectors to prove:

- exact `<f` little-endian packing per element;
- exact byte length `768 * 4`;
- round-trip to stored float32 values;
- NaN, Inf, wrong dimension, zero vector, trailing bytes, and wrong encoding rejection;
- cosine values for identical, orthogonal, and opposite vectors;
- `0.1234567890125` rounds to `0.123456789012` under `ROUND_HALF_EVEN`;
- element order is fixed and `math.fsum` is used rather than provider/SQLite order.

- [ ] **Step 5: Implement vector codec and deterministic score conversion**

Encode each validated value through `struct.pack("<f", value)`. Decode only an exact 3,072-byte BLOB
for V1. Compute cosine from decoded values with `math.fsum` and reject a non-finite or zero norm.
Convert the finite float through `Decimal(str(value))` and quantize with:

```python
SIMILARITY_QUANTUM = Decimal("0.000000000001")
score.quantize(SIMILARITY_QUANTUM, rounding=ROUND_HALF_EVEN)
```

Persist/display the canonical Decimal as a fixed 12-place string.

- [ ] **Step 6: Run provider/vector tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_embedding_provider.py tests/test_retrieval_vectors.py tests/test_retrieval_contracts.py -v
git diff --check
```

Expected: all pass; timeout/control identity regression remains green.

Stop for stage review. Do not start Task 4 or commit.

---

### Task 4: Loopback Ollama embedding adapter

**Files:**

- Create: `src/axq/retrieval/ollama.py`
- Create: `tests/test_ollama_embedding_provider.py`
- Modify: `src/axq/retrieval/__init__.py`

**Interfaces:**

- Consumes: Task 3 provider/vector boundaries; Task 1 loopback URL validation and injectable native
  HTTP transport without changing Task 1 source.
- Produces: `OllamaEmbeddingProvider` and an internal injectable `OllamaEmbeddingTransport` protocol.

- [ ] **Step 1: Write failing loopback and identity tests**

With a deterministic fake transport, accept only `localhost`, `127.0.0.1`, and IPv6 loopback HTTP
roots. Reject cloud/LAN hosts, HTTPS, credentials, query, fragment, and non-root paths. Assert exact
GET calls to `/api/version` and `/api/tags`, then fail closed for absent/ambiguous model, server
version mismatch, configured/resolved name mismatch, exact digest mismatch, expected family or
quantization mismatch, and expected-dimension contract mismatch.

- [ ] **Step 2: Run adapter tests and verify red**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_ollama_embedding_provider.py -v
```

Expected: missing Ollama embedding adapter.

- [ ] **Step 3: Implement strict identity preflight**

Use the Task 1 standard-library transport seam where compatible. Require configured name
`nomic-embed-text:v1.5`, exact expected resolved name, exact 64-character digest, Ollama version,
768 dimensions, adapter version, and prefix profile identity. Optional family/quantization facts are
strict when supplied. Do not accept `latest` as sufficient identity.

- [ ] **Step 4: Write failing `/api/embed` request and response tests**

Assert exact request body:

```python
{
    "model": expected.resolved_model_name,
    "input": [request_text],
    "truncate": False,
}
```

Assert controls supply HTTP timeout and maximum response bytes without entering `EmbeddingRequest`.
Validate returned model name, one output for one request, 768 values, finite values, and nonzero norm.
Map Ollama nanosecond durations and prompt token counts into safe metadata.

- [ ] **Step 5: Implement embedding and complete safe failure mapping**

Map timeouts, connection errors, HTTP errors, invalid/oversized JSON, missing model, identity
mismatch, wrong item count, wrong dimensions, NaN/Inf, and zero norm to exact typed failures. Compute
safe raw response digest/size in memory. Never persist raw invalid JSON.

- [ ] **Step 6: Run focused adapter and Task 1 Ollama regressions**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_ollama_embedding_provider.py tests/test_embedding_provider.py tests/test_ollama_provider.py -v
git diff --check
```

Expected: all fake-transport tests pass without a running Ollama service; Task 1 behavior is unchanged.

Stop for stage review. Do not start Task 5 or commit.

---

### Task 5: Append-only migration and retrieval store

**Files:**

- Create: `database/migrations/017_experience_retrieval_embeddings.sql`
- Create: `src/axq/retrieval/store.py`
- Create: `tests/test_retrieval_store.py`
- Modify: `src/axq/retrieval/__init__.py`

**Interfaces:**

- Consumes: Tasks 1 and 3 contracts/codecs; `axq.database.Database`.
- Produces: `SQLiteRetrievalStore` append/read/list/history APIs for documents, embedding requests,
  vectors, attempts, index manifests, candidate manifests, retrieval requests/results/attempts, and
  first-exact-completion reuse.

- [ ] **Step 1: Write failing migration and append-only tests**

Create a temporary store, append one complete document/vector/index/candidate/retrieval chain, and
assert exact canonical JSON and vector bytes round-trip. Direct SQL `UPDATE` and `DELETE` against all
nine logical tables must raise `sqlite3.IntegrityError` with table-specific append-only messages.

- [ ] **Step 2: Run store tests and verify red**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_store.py -v
```

Expected: migration/store missing.

- [ ] **Step 3: Implement migration 017**

Create tables:

```text
retrieval_documents
embedding_requests
embedding_vectors
embedding_attempts
retrieval_index_manifests
retrieval_candidate_manifests
retrieval_requests
retrieval_results
retrieval_attempts
```

Each semantic table stores ID, indexed exact-link columns, schema version, payload hash, and canonical
record JSON. `embedding_vectors` additionally stores vector BLOB, vector digest, dimension, and
encoding. Add foreign keys, unique `(request_id, attempt_key)` constraints, ordered history indexes,
success/failure linkage checks, and UPDATE/DELETE rejection triggers. Add no current-state table.

- [ ] **Step 4: Implement verified append/read methods**

Every append follows:

```python
if existing_canonical_bytes == incoming_canonical_bytes:
    return False
if existing_id is not None:
    raise ValueError("semantic ID already exists with different content")
```

On every read, recompute payload hash, parse strict contract, regenerate semantic ID, validate indexed
columns, validate vector BLOB digest/encoding/dimension, and traverse required foreign-key linkage.

- [ ] **Step 5: Write conflict, corruption, history, and reuse tests**

Prove orphan vectors/results, altered canonical JSON, altered payload hash, altered BLOB, wrong member
order, incomplete manifest marked complete, successful attempt without output, failure attempt with
output, duplicate attempt-key conflict, and mismatched model/profile linkage fail closed.

Append failure, completion, and reuse attempts; prove all remain ordered and
`first_completed_vector(embedding_request_id)` returns the earliest exact committed success only.

- [ ] **Step 6: Run store/contract/vector tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_store.py tests/test_retrieval_contracts.py tests/test_retrieval_vectors.py -v
git diff --check
```

Expected: all pass and migration 016/Task 1 store tests remain unaffected.

Stop for stage review. Do not start Task 6 or commit.

---

### Task 6: Deterministic indexing, exact reuse, and complete manifests

**Files:**

- Create: `src/axq/retrieval/indexing.py`
- Create: `tests/test_retrieval_indexing.py`
- Modify: `tests/retrieval_test_support.py`
- Modify: `src/axq/retrieval/__init__.py`

**Interfaces:**

- Consumes: exact source catalog/renderers, embedding provider, vector codec, and retrieval store.
- Produces: `IndexBuildRequest`, `IndexBuildResult`, and `build_retrieval_index(...)`.

- [ ] **Step 1: Write failing deterministic enumeration and supersession tests**

Use the controlled Phase 8 stores to prove:

- caller/SQLite order produces the same document/member order;
- only records available by `source_cutoff` enter;
- later unavailable revisions do not affect an earlier build;
- latest available daily/weekly/proposal revision wins an explicit valid chain;
- predecessor records remain stored;
- same-key weekly patterns remain separate observations;
- missing predecessor, cycle, or fork fails closed;
- a pattern receives its exact containing WeeklyReflection availability and parent provenance.

- [ ] **Step 2: Run index tests and verify red**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_indexing.py -v
```

Expected: missing indexing service.

- [ ] **Step 3: Implement document publication and embedding execution**

Define:

```python
def build_retrieval_index(
    *,
    request: IndexBuildRequest,
    catalog: Phase8EvidenceSourceCatalog,
    provider: EmbeddingProvider,
    store: SQLiteRetrievalStore,
    controls: EmbeddingAttemptControls,
) -> IndexBuildResult:
```

Enumerate/render/append documents in exact ID order. Build each `EmbeddingRequest` without controls.
Under `REUSE_FIRST_COMPLETED_EXACT`, validate and reuse the first exact vector without provider
verification or embedding. Under `NEVER_REUSE`, invoke the provider even if a completed vector exists.

For fresh execution, verify exact model identity, call the provider, encode exact float32 bytes,
append the vector, and append terminal audit containing controls. Catch only typed failures and append
safe failure audits.

- [ ] **Step 4: Write mandatory control-variation and nondeterminism tests**

Call the same semantic request with different timeout/response-size controls and attempt keys. Assert:

- embedding request ID is unchanged;
- both attempt audits preserve their exact controls;
- exact reuse skips provider verification and embedding;
- `NEVER_REUSE` can append a second differing vector ID under the same request;
- neither vector overwrites the other;
- index construction binds one explicit vector per document.

- [ ] **Step 5: Implement atomic complete-manifest publication**

Do not append a usable `RetrievalIndexManifest` until every selected document has an exact vector for
the same provider/model/profile/dimension/encoding identity. If any item fails, append failure audit
and return `INCOMPLETE_INDEX`; retain already committed immutable documents/vectors but publish no
partial manifest. Identical member sets reuse the same manifest ID and bytes.

- [ ] **Step 6: Run indexing/store/provider tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_indexing.py tests/test_retrieval_store.py tests/test_embedding_provider.py -v
git diff --check
```

Expected: all pass; provider invocation counters prove exact reuse and fresh-generation behavior.

Stop for stage review. Do not start Task 7 or commit.

---

### Task 7: Metadata-first candidate construction and deterministic ranking

**Files:**

- Create: `src/axq/retrieval/ranking.py`
- Create: `tests/test_retrieval_ranking.py`
- Modify: `src/axq/retrieval/__init__.py`

**Interfaces:**

- Consumes: complete index manifests, exact documents/vectors, query specs, metadata filters, and
  Task 3 vector scoring.
- Produces: `build_candidate_manifest(...)` and `rank_retrieval_candidates(...)`.

- [ ] **Step 1: Write failing metadata/time ordering tests**

Build controlled candidates where the highest cosine item is future-dated or metadata-ineligible.
Assert it never appears in the candidate manifest or result. Cover OR-within-field and AND-between-
field semantics, missing metadata, anchor exclusion, strict source kind, exact as-of boundary, and
explicit lifecycle status replay through the same cutoff.

- [ ] **Step 2: Run ranking tests and verify red**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_ranking.py -v
```

Expected: missing ranking module.

- [ ] **Step 3: Implement complete candidate-manifest construction**

Require one complete index manifest and exact query anchor available by `retrieval_as_of`. Filter in
canonical field order, exclude the anchor, normalize members by `(source_kind, source_id,
document_id)`, and content-address the full exact list. Return an explicit empty manifest for no
matches; do not broaden filters.

- [ ] **Step 4: Write deterministic score/tie/top-k tests**

Use fixed vector BLOBs to assert descending 12-place score order and ties broken by source kind,
source ID, then document ID. Reverse input and SQLite insertion order and require byte-identical
candidate manifests/results. Test `top_k` 1 and 8, reject 0 and 9, and prove no recency boost or score
threshold exists.

- [ ] **Step 5: Implement exact ranking**

Load and revalidate every vector/document/member. Require identical provider/model/profile/dimension/
encoding identity. Score via `cosine_similarity` and `canonical_similarity_decimal`, sort by the
declared tuple, and take exactly `min(top_k, candidate_count)`. Mark every item non-authoritative.
Return `NO_MATCH` for an empty candidate manifest without provider or Task 1 invocation.

- [ ] **Step 6: Run ranking/vector/index tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_ranking.py tests/test_retrieval_vectors.py tests/test_retrieval_indexing.py -v
git diff --check
```

Expected: all pass with byte-identical ranking artifacts.

Stop for stage review. Do not start Task 8 or commit.

---

### Task 8: Retrieval service and Task 1 bounded-context adapter

**Files:**

- Create: `src/axq/retrieval/service.py`
- Create: `tests/test_retrieval_service.py`
- Modify: `src/axq/retrieval/__init__.py`

**Interfaces:**

- Consumes: code-owned query renderer, embedding provider/store, complete index, ranking functions,
  exact Phase 8 resolver, and Task 1 `ReflectionExplanationInput` contracts.
- Produces: `run_evidence_retrieval(...)` and `build_reflection_explanation_input(...)`.

- [ ] **Step 1: Write failing end-to-end controlled retrieval tests**

Use one anchor plus fixed exact candidates. Assert the service:

- renders a code-owned query;
- embeds/reuses the query under exact model identity;
- constructs metadata-filtered complete candidate manifest;
- persists request/result/attempt append-only;
- returns the fixed expected source order and canonical scores;
- reuses byte-identical completed results without reranking;
- stores later attempts without changing result identity.

- [ ] **Step 2: Run service tests and verify red**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_service.py -v
```

Expected: missing service functions.

- [ ] **Step 3: Implement retrieval orchestration and safe terminal audit**

Define:

```python
def run_evidence_retrieval(
    *,
    query: RetrievalQuerySpec,
    index_manifest_id: str,
    provider: EmbeddingProvider,
    store: SQLiteRetrievalStore,
    source_resolver: ExactPhase8SourceResolver,
    controls: EmbeddingAttemptControls,
    attempt_key: str,
    requested_at: datetime,
    started_at: datetime,
    completed_at: datetime,
) -> RetrievalRunResult:
```

Validate the anchor/source cutoff, create a query `EmbeddingRequest` without timeout/size fields,
reuse or execute exact query embedding, persist the retrieval request, construct/reuse the candidate
manifest, rank, persist result, and append terminal audit. Failures retain only safe metadata.

- [ ] **Step 4: Write failing Task 1 context tests**

Assert `build_reflection_explanation_input` emits one anchor plus up to eight selected context items,
all exact source IDs/digests, no scores/ranks, no URLs/secrets, at most 1,500 characters each, at most
13,500 aggregate characters, and valid Task 1 canonical bytes. Tampered source, document, vector,
manifest, result, or provenance must fail closed.

- [ ] **Step 5: Implement the pure Task 1 adapter**

Reload and verify anchor plus each selected Phase 8 source. Map Experience to Task 1 `EXPERIENCE`,
both pattern types to `PATTERN`, and other source kinds directly. Use the stored bounded semantic
content unchanged. Do not include similarity, rank, vector, filter, endpoint, or audit metadata in
LLM context. Do not invoke Task 1 service automatically.

- [ ] **Step 6: Write failure/retry tests**

Cover `NO_MATCH`, provider failures, invalid query vector, incomplete index, invalid filter,
provenance mismatch, failure then later success, exact result reuse, and different operational
timestamps/controls preserving semantic request/result IDs. Assert failed retrieval never produces a
Task 1 input.

- [ ] **Step 7: Run service, ranking, and Task 1 regressions**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_service.py tests/test_retrieval_ranking.py tests/test_reasoning_service.py tests/test_reasoning_contracts.py -v
git diff --check
```

Expected: all pass; Task 1 V2 prompt/service and strict citation behavior remain unchanged.

Stop for stage review. Do not start Task 9 or commit.

---

### Task 9: Controlled offline CLI and canonical artifacts

**Files:**

- Create: `src/axq/retrieval/cli.py`
- Create: `src/axq/retrieval/__main__.py`
- Create: `tests/test_retrieval_cli.py`
- Create: `tests/fixtures/retrieval/controlled_query.json`
- Modify: `src/axq/retrieval/__init__.py`

**Interfaces:**

- Consumes: Tasks 6–8 index/retrieval/context services and store reads.
- Produces: `python -m axq.retrieval` commands `build-index`, `run-retrieval`, `show-document`,
  `show-vector-metadata`, `show-index-manifest`, `show-retrieval`, `show-history`,
  `retrieval-summary`, and `build-reasoning-input`.

- [ ] **Step 1: Write failing parser and forbidden-argument tests**

Require explicit Phase 8 store paths, retrieval store/output, source cutoff or retrieval as-of,
controlled anchor kind/ID, typed filters, top-k, exact model name/digest/version/dimensions, loopback
endpoint, attempt key, timeout, response-byte limit, and reuse policy where applicable.

Assert there is no argument for arbitrary query/prompt, arbitrary source file/URL, Final OOS,
dataset, runtime, replay, broker, MT5, tool/plugin, graph/RAG, deployment, or proposal mutation.

- [ ] **Step 2: Run CLI tests and verify red**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_cli.py -v
```

Expected: missing CLI entry point.

- [ ] **Step 3: Implement controlled run commands and canonical output**

Use strict canonical JSON inputs only. Build providers only inside mutating offline build/retrieve
handlers. Write result artifacts atomically as sorted compact ASCII JSON. Safe run output includes
semantic IDs, attempt ID/status, counts, reused flags, and safe errors; it excludes raw provider
responses and full vectors.

- [ ] **Step 4: Implement read-only inspection commands**

Show commands instantiate only `SQLiteRetrievalStore`; they must not instantiate an embedding
provider, contact Ollama, or open Phase 8 source stores unless exact source revalidation is explicitly
required by `build-reasoning-input`. `show-vector-metadata` emits dimension/encoding/digests only.

- [ ] **Step 5: Add controlled end-to-end fake-provider CLI tests**

Build a tiny index, run retrieval, show all records, produce Task 1 input, and summarize counts. Retry
with later operational timestamps and different timeout/response-size limits under exact reuse;
assert request/result/vector IDs and canonical result bytes are unchanged and provider invocation
count does not increase.

- [ ] **Step 6: Run CLI/service/store tests**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_cli.py tests/test_retrieval_service.py tests/test_retrieval_store.py -v
git diff --check
```

Expected: all pass; no real Ollama or large Phase 8 index is built.

Stop for stage review. Do not start Task 10 or commit.

---

### Task 10: Forbidden-scope and mutation-safety audit

**Files:**

- Create: `tests/test_retrieval_boundaries.py`
- Modify only if a failing audit proves a genuine violation: files under `src/axq/retrieval/`

**Interfaces:**

- Consumes: complete Task 2 package and controlled immutable Phase 8/Task 1 fixtures.
- Produces: executable proof of offline isolation, provenance safety, and non-authority.

- [ ] **Step 1: Add static import and source-boundary tests**

Parse every retrieval Python file with `ast` and reject imports rooted at runtime, agents, Master,
Discipline, Risk, execution, position management/actions, MT5, replay validation, Quant/datasets, or
proposal-transition modules. Search for `FINAL_OOS`, MetaTrader5 calls, subprocess/dynamic imports,
web clients beyond the loopback Ollama transport, vector-store/embedding libraries, graph/RAG, tool
calls, deployment, and mutation APIs.

- [ ] **Step 2: Add reverse fast-path dependency tests**

Parse runtime/trading/agent packages and assert none imports `axq.retrieval`. Importing
`axq.retrieval` must not open a database, contact a network, initialize Ollama, or enumerate stores.

- [ ] **Step 3: Add Phase 8 and Task 1 mutation-safety tests**

Serialize controlled Experience, daily/weekly reflection, patterns, and proposal rows before index,
retrieval, and context construction; require byte equality afterward. Assert no new Phase 8 lifecycle,
evaluation, review, authorization, or proposal rows. Assert the active Task 1 V2 prompt and
request-specific response-schema identities for the controlled fixture, plus existing
request/response records, remain byte-identical.

- [ ] **Step 4: Add authority and information-flow tests**

Prove similarity/rank cannot populate confidence, proposal status, trading action, or deployment
fields; scores are absent from Task 1 context; Final OOS/dataset paths cannot be passed; and a
`NO_MATCH`/failed result cannot invoke Task 1.

- [ ] **Step 5: Run all focused Task 2 tests once**

```powershell
& '..\..\.venv\Scripts\python.exe' -m pytest tests/test_retrieval_contracts.py tests/test_retrieval_rendering.py tests/test_embedding_provider.py tests/test_retrieval_vectors.py tests/test_ollama_embedding_provider.py tests/test_retrieval_store.py tests/test_retrieval_indexing.py tests/test_retrieval_ranking.py tests/test_retrieval_service.py tests/test_retrieval_cli.py tests/test_retrieval_boundaries.py -v
git diff --check
```

Expected: all focused tests pass, no prohibited dependency is found, and no source outside the
approved Task 1 additive enum change. The pre-existing Task 1 V2 citation fix is preserved but is not
part of Task 2 implementation scope.

Stop for stage review. Do not start Task 11 or commit.

---

### Task 11: Documentation, measured fixture, Graphify, and final gate

**Files:**

- Create: `docs/experience_retrieval.md`
- Modify: `README.md`
- Modify: `docs/agentic_architecture.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**

- Consumes: final contracts, CLI, controlled fixture artifacts, and test results.
- Produces: operator guidance, current durable context, and final validation evidence.

- [ ] **Step 1: Run one tiny fake-provider fixture and capture measured facts**

Build only the controlled fixture index and one retrieval. Capture exact document/vector/index/
candidate/request/result/attempt counts, status breakdown, provider invocation/reuse counts, selected
IDs/scores, canonical artifact sizes, and SQLite size. Run the identical semantic fixture again with
later timestamps and different timeout/response-size controls; prove exact reuse and byte-identical
semantic outputs.

- [ ] **Step 2: Update operator and architecture documentation**

Document exact provider/model/profile identity, configured-name limitation, causal source selection,
pattern parent availability, metadata-before-similarity behavior, vector encoding, complete
manifests, ranking/ties, nondeterminism boundary, exact reuse, failures, Task 1 adapter, commands,
storage, privacy, non-authority, and all prohibited scopes. Record measured fixture facts only; do not
claim retrieval quality from a synthetic test.

- [ ] **Step 3: Run focused documentation consistency checks**

Verify documented commands against `python -m axq.retrieval --help`, local links, current table/status
names, no stale status claims, no trailing whitespace, and `git diff --check`. Do not run the full gate
yet.

- [ ] **Step 4: Refresh Graphify exactly once**

```powershell
graphify update .
graphify cluster-only . --no-label
```

Record nodes, edges, communities, and warnings. Do not refresh again unless a genuine code change
after this step requires it.

- [ ] **Step 5: Run the full repository gate exactly once**

```powershell
$env:PYTHONPATH = (Resolve-Path 'src')
& '..\..\.venv\Scripts\python.exe' -m pytest --basetemp='.pytest_tmp_phase9_task2_final'
& '..\..\.venv\Scripts\python.exe' -m ruff check .
& '..\..\.venv\Scripts\python.exe' -m mypy src/axq --no-warn-unused-ignores
& '..\..\.venv\Scripts\python.exe' -m pip check
git diff --check
```

Expected: full pytest, Ruff, strict mypy, dependency integrity, and diff hygiene pass.

- [ ] **Step 6: Perform final scope and identity audit**

Run `git status --short`, inspect every changed/untracked path, and confirm only Task 2 files plus the
one additive Task 1 enum change exist. Re-run static searches without modifying files. Confirm:

- controls remain absent from `EmbeddingRequest` and present in attempt audits;
- exact identity/reuse/ranking tests are green;
- no large index, real provider call, runtime artifact, or protected data was added;
- no forbidden integration exists;
- Graphify is current;
- no commit/push/merge occurred.

- [ ] **Step 7: Report and stop**

Report architecture, contracts, model identity, source/index counts, ranking results, Task 1
compatibility, control-separation behavior, append-only/reuse behavior, failure behavior, full test
results, source-file count, Graphify counts, files changed, warnings, exact CLI commands, optional
Ollama smoke status, known risks, and recommended checkpoint/next scope. Stop before checkpoint commit
or Phase 9 Task 3 unless explicitly authorized.
