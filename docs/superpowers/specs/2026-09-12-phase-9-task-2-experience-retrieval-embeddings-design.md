# Phase 9 Task 2 Experience Retrieval and Embeddings Design

## Status

Approved architecture captured for review. The strict contract-foundation stage is implemented and
tested: immutable retrieval identities/manifests/audit contracts, package exports, and the additive
Task 1 `EXPERIENCE` source kind. All later implementation remains PAUSED. There are no source
adapters, renderers, embedding providers, migrations, stores, indexes, ranking services, CLI
commands, automatic Ollama invocations, or live/replay imports.

Base checkpoint:

- branch: `codex/phase-9-llm-reasoning`;
- original design commit: `9b9b70e1ff232550626c16e5cea98274a5795e52`;
- prerequisite: completed Phase 9 Task 1 offline structured-reasoning boundary.

## Goal

Add an offline, auditable retrieval layer that selects causally available and semantically relevant
Phase 8 evidence for the existing Task 1 `REFLECTION_EXPLANATION` boundary. Retrieval must preserve
exact Phase 8 provenance, apply typed metadata filters before similarity ranking, bind every vector
to an exact embedding environment and model, and produce an existing Task 1-compatible bounded
context input.

Task 2 is evidence selection, not truth discovery or decision authority. A similarity score says
only that two exact rendered records are close under one exact embedding artifact. It is not trading
confidence, causal proof, correctness, proposal approval, or permission to mutate any system state.

## Selected approach

Create a separate offline-only `axq.retrieval` package backed by append-only SQLite. Source-specific,
allowlisted adapters read immutable Phase 8 records and render versioned retrieval documents. A
provider-neutral embedding protocol has one V1 implementation using loopback Ollama and the
configured model name `nomic-embed-text:v1.5`. Exact vectors are stored as versioned little-endian
IEEE-754 float32 BLOBs. Complete content-addressed index manifests bind the exact source documents
and vector artifacts eligible for a retrieval. Ranking uses deterministic brute-force cosine
similarity over those stored bytes.

This design deliberately avoids a native vector extension. The current corrected one-month corpus
is small enough for offline brute-force ranking, while the simpler dependency surface makes exact
audit, Windows portability, and tie behavior easier to verify. A specialized vector index may be
considered later only after measured scale or latency requires it, behind the same contracts.

## Package and dependency boundaries

The new package is `src/axq/retrieval/`. It may depend on:

- immutable contracts and read APIs under `axq.experience` and `axq.reflection`;
- Task 1 source/context contracts under `axq.reasoning.contracts`;
- the existing loopback URL validation and standard-library Ollama transport boundary where reuse
  does not alter Task 1 behavior;
- `axq.database.Database` and canonical hashing utilities;
- Python standard-library numeric, binary, HTTP, and SQLite facilities.

No runtime, agent, Master, Discipline, Risk, execution, position-management, replay, broker, MT5,
training, dataset, Final OOS, deployment, proposal-transition, web retrieval, arbitrary file
retrieval, plugin, RAG, vector-store, Experience Graph, or hidden-reasoning path may import or be
invoked by `axq.retrieval`.

No live/replay fast-path package may import `axq.retrieval`. Importing the package must not connect to
Ollama, open Phase 8 databases, build an index, or execute a retrieval.

## Source universe and exact provenance

V1 supports only these Phase 8 source families:

- `Experience`, including every concrete immutable Experience subtype;
- `DailyReflection`;
- `WeeklyReflection`;
- `SuccessPattern`;
- `FailurePattern`;
- `ImprovementProposal`.

Every source enters through a code-owned adapter. There is no dynamic adapter loading or operator
supplied Python path. Each adapter must:

1. load through the authoritative Phase 8 store's verified read API;
2. validate the strict immutable contract;
3. recompute canonical source bytes and SHA-256;
4. preserve the source semantic ID and `available_at`;
5. resolve and record exact supporting Phase 8 IDs and digests where those records exist;
6. render typed metadata and bounded semantic content using a versioned code-owned renderer;
7. fail closed on missing, conflicting, future, or malformed provenance.

`SuccessPattern` and `FailurePattern` do not carry an independent `available_at`. Their causal
availability is the `available_at` of the exact containing `WeeklyReflection`, which is recorded as
mandatory parent provenance and revalidated before indexing or retrieval. Both pattern subtypes map
to Task 1's existing `PATTERN` source kind; their more specific type remains in retrieval metadata.

The retrieval database is an index and audit store, not the authority for Phase 8 evidence. Before a
selected item is adapted into Task 1 context, its authoritative Phase 8 source must be loaded and its
ID, canonical bytes, digest, availability, and recorded provenance revalidated.

Filesystem paths and SQLite physical file digests do not participate in semantic identity. Paths
are operational configuration; SQLite physical bytes are not a canonical representation of their
immutable rows.

## Immutable contracts

All contracts use strict frozen schemas, explicit schema versions, finite-number validation,
canonical field ordering, and strict UTC where timestamps are accepted.

### Retrieval source and evidence references

`RetrievalSourceKind` contains:

- `EXPERIENCE`;
- `DAILY_REFLECTION`;
- `WEEKLY_REFLECTION`;
- `SUCCESS_PATTERN`;
- `FAILURE_PATTERN`;
- `IMPROVEMENT_PROPOSAL`.

`ExactEvidenceReference` contains:

- retrieval source kind;
- exact Phase 8 source semantic ID;
- canonical source digest;
- strict-UTC `available_at`;
- normalized exact upstream Phase 8 references;
- source schema/version identity.

The Task 1 `ReasoningSourceKind` gains one additive `EXPERIENCE` member. Existing source kinds,
prompt text, prompt-template identity, response-schema identity, and structured output remain
unchanged. A Task 1 request that cites an Experience receives a new request identity naturally
because source kind, source ID, and digest already participate in that identity.

### Typed metadata

`EvidenceMetadata` is a discriminated union rather than a generic dictionary. Source-specific
members may expose only canonical fields useful for filtering, including:

- symbol and Experience type;
- direction, session, regime, rejection layer, or reason code when the source defines them;
- reflection category and signal;
- pattern type, signal class, reason code, scope, and scope value;
- proposal target component, category, and recorded proposal status.

Unavailable metadata remains absent, not an empty string or invented default. Metadata values are
facts copied from exact source records or deterministic append-only lifecycle replay as of the
retrieval cutoff.

`RetrievalMetadataFilter` contains typed normalized tuples for the supported fields. Values within a
field use OR semantics; populated fields combine with AND semantics. A candidate lacking a required
field does not match. Unknown fields, arbitrary expressions, SQL fragments, and user-defined filter
functions are forbidden.

### Renderer identity and documents

`EvidenceRendererIdentity` binds:

- renderer kind;
- renderer version;
- exact renderer/template digest;
- source schema identity;
- embedding-text profile identity;
- Task 1 bounded-context profile identity.

`RetrievableEvidenceDocument` contains:

- content-addressed `document_id`;
- exact evidence reference;
- typed metadata;
- renderer identity;
- canonical bounded context content and digest;
- canonical document embedding text and digest;
- explicit character and UTF-8 byte counts.

One source record and one renderer identity produce one document. IDs, digests, long provenance
lists, storage paths, and audit timestamps are not added to embedding text merely as noise. They
remain exact linked metadata. The code-owned renderer selects meaningful source facts and metrics,
while canonical source digest proves which complete record produced them.

Each V1 bounded context item is limited to 1,500 canonical characters. Embedding text is the
versioned Nomic document prefix plus canonical JSON for that same bounded semantic content. This
single semantic rendering prevents the indexed meaning from diverging from the evidence later shown
to Task 1.

### Embedding identity

`EmbeddingModelIdentity` contains:

- provider kind (`OLLAMA`);
- AXQ embedding-adapter version;
- Ollama server version;
- configured model name;
- resolved canonical model name;
- exact model digest;
- expected vector dimensions;
- expected family and quantization when configured and available;
- embedding API contract version;
- encoding/prefix profile name, version, and digest;
- canonical vector encoding version.

`nomic-embed-text:v1.5` is only the configured model name. It is never sufficient model identity.
The authoritative identity is the complete tuple above. V1 requires expected dimensions of 768 and
an exact locally installed model digest. Mutable aliases cannot substitute for that digest.

`NOMIC_RETRIEVAL_PREFIX_V1` renders:

- documents as `search_document: <canonical-content>`;
- queries as `search_query: <canonical-content>`.

The exact prefix strings and rendering rules participate through the profile digest. Changing a
prefix or encoding rule changes request and vector identities.

### Embedding request, vector, and attempt

`EmbeddingInputRole` is `DOCUMENT` or `QUERY`.

`EmbeddingRequest` binds:

- exact embedding model identity;
- role;
- exact document or query semantic ID;
- exact unprefixed content digest;
- exact prefixed UTF-8 text digest;
- encoding/prefix profile identity;
- timeout and response-size policy identity where semantically relevant.

Operational timestamps, endpoint, output path, batch position, and process identity are excluded
from semantic request identity.

`EmbeddingVectorArtifact` binds:

- exact embedding request ID;
- exact model identity;
- vector encoding (`IEEE754_FLOAT32_LE_V1`);
- dimension count;
- exact vector BLOB digest;
- exact provider response digest and safe byte count;
- nonzero finite norm validation metadata.

The vector BLOB is authoritative for ranking. Conversion from validated provider JSON numbers to
little-endian float32 follows one versioned routine. No JSON float array is treated as the canonical
stored vector.

`EmbeddingAttemptAudit` binds request, attempt key, terminal semantic outcome, vector linkage when
successful, and safe failure metadata. Strict-UTC requested/started/completed times, endpoint, token
count, and durations remain audit metadata and do not change embedding request or vector identity.

### Query and index contracts

`RetrievalQuerySpec` contains:

- exact anchor evidence reference;
- code-owned query-renderer identity;
- exact canonical query content and digest;
- strict-UTC semantic `retrieval_as_of`;
- exact typed metadata filter;
- `top_k` from 1 through 8;
- ranking-policy identity.

V1 accepts no arbitrary query text. A source-specific code-owned query renderer builds query content
from the exact anchor record and approved semantic fields. Changing the anchor, renderer, filter,
cutoff, or top-k changes query identity.

The anchor must itself satisfy `anchor.available_at <= retrieval_as_of`. `top_k` counts retrieved
neighbors and excludes the anchor.

`RetrievalIndexManifest` contains:

- content-addressed manifest ID;
- source cutoff/as-of identity;
- source-adapter and renderer identities;
- embedding model identity;
- exact normalized document/vector member pairs;
- exact source revision-selection policy;
- member count and manifest digest;
- explicit completeness guard.

Only complete manifests can support retrieval. A candidate source document without an exact vector
for the manifest's model/profile makes publication fail with `INCOMPLETE_INDEX`; it is never silently
omitted.

### Retrieval request and result

`RetrievalRankingPolicy` V1 binds:

- cosine similarity;
- stored float32 input;
- deterministic `math.fsum` accumulation;
- Decimal quantization to 12 places with `ROUND_HALF_EVEN`;
- descending score order;
- ascending source kind, source ID, and document ID tie breaks;
- maximum top-k of eight;
- no recency boost and no implicit score threshold.

`RetrievalRequest` binds exact query specification, query-vector artifact, complete index manifest,
metadata filter, candidate-set manifest, and ranking policy.

`RetrievedEvidenceItem` contains rank, canonical Decimal similarity, exact source/document/vector
references, and source availability. It is explicitly labeled non-authoritative retrieval evidence.

`RetrievalResult` binds:

- exact request, query vector, and candidate manifest IDs;
- exact ordered selected items;
- candidate and selected counts;
- terminal result status;
- Task 1 context-bundle digest when compatible output exists.

Scores and rank remain in retrieval artifacts and are excluded from Task 1 LLM context.

`RetrievalAttemptAudit` preserves exact request/result linkage, attempt key, terminal status, safe
failure metadata, and strict-UTC operational timing. It grants no truth, proposal, deployment,
runtime, or trading authority.

## Embedding provider boundary

The provider-neutral protocol is:

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

The first provider is `OllamaEmbeddingProvider`. It uses Python standard-library HTTP through an
injectable transport and accepts loopback endpoints only. Before embedding it verifies `/api/version`
and the exact `/api/tags` model entry. It calls `/api/embed` with:

- exact resolved model name;
- a string or deterministic bounded batch of prefixed inputs;
- `truncate=false` so content is never silently shortened;
- explicit dimensions only when supported and bound by the provider contract;
- bounded timeout and response size.

It validates response model name, item count, ordering, dimensions, finite values, and nonzero vector
norm. A model name, digest, server version, dimension, family, or configured quantization mismatch
fails closed before publishing an artifact.

The protocol permits future providers, but Task 2 implements and allowlists only local Ollama. There
is no cloud-provider configuration or arbitrary endpoint.

## Semantic determinism and embedding variation

These properties are deterministic:

- source validation and rendering;
- source/document/query/request identities;
- exact completed-vector reuse;
- index and candidate manifest membership;
- ranking over exact stored vector bytes;
- Decimal score serialization and tie breaks;
- selected-item order;
- Task 1 bounded-context construction;
- canonical result and audit identities.

An independently generated embedding is not promised byte equality across Ollama versions, exact
model builds, execution backends, hardware, or environments. Even with the same semantic embedding
request, a fresh provider execution may produce different vector bytes. Such a vector receives a
different content-addressed vector artifact ID. Retrieval never refers to "the vector" implicitly;
it binds one exact vector ID for every query and candidate.

The default reuse policy is `REUSE_FIRST_COMPLETED_EXACT`. It revalidates and returns the first exact
completed vector without provider invocation. An explicit `NEVER_REUSE` mode may produce another
append-only vector artifact for controlled diagnostics, but never replaces the earlier artifact.
Operational timestamps do not perturb semantic request, vector, index, or retrieval identity.

## Index construction and update strategy

Indexing is an explicit offline command, not a watcher or runtime service:

1. Open configured Phase 8 SQLite stores read-only through their verified APIs.
2. Enumerate allowlisted records in deterministic source-kind and semantic-ID order.
3. Require `available_at <= source_cutoff`.
4. Replay explicit supersession chains as of that cutoff.
5. Select the latest causally available revision in each valid supersession chain.
6. Retain ordinary historical pattern observations even when they share a stable `pattern_key`.
7. Validate and append exact retrieval documents.
8. reuse or generate exact embeddings in deterministic document-ID order and bounded batches.
9. Publish a complete index manifest only after every selected document has one exact vector.
10. Append a terminal index/retrieval audit; never update an earlier record.

Repeated construction with identical source records, cutoff, adapters, renderers, model identity,
and exact vector artifacts reuses the same index manifest. New Phase 8 records or superseding
revisions create a new manifest. Old documents, vectors, attempts, and manifests remain queryable for
audit and historical replay.

V1 does not physically delete or mutate stale embeddings. Compaction, archival, and approximate
nearest-neighbor indexing are deferred operational concerns.

## Candidate-set construction and metadata filtering

Candidate construction is deterministic and precedes similarity:

1. start from one complete index manifest;
2. exclude the exact anchor source/document;
3. enforce `candidate.available_at <= retrieval_as_of`;
4. enforce source-kind allowlist;
5. apply typed metadata filters in canonical field order;
6. resolve latest revisions as of the same cutoff;
7. sort exact document/vector pairs by source kind, source ID, and document ID;
8. persist the complete content-addressed candidate-set manifest;
9. rank only those persisted candidates.

Metadata filtering is a factual selection boundary. Semantic similarity cannot reintroduce an item
excluded by time or metadata. An empty candidate set yields an auditable `NO_MATCH` result; it does
not fall back to unrestricted search.

## Similarity ranking and ties

Cosine similarity is computed from exact stored query and document float32 values. Vectors must
share the exact embedding identity and dimension. Dot products and norms use a fixed element order
and `math.fsum`. The resulting finite score is converted to Decimal and quantized to 12 decimal
places with `ROUND_HALF_EVEN`.

Candidates sort by:

1. quantized similarity descending;
2. source kind ascending;
3. source semantic ID ascending;
4. document ID ascending.

The result takes the first `top_k`, where V1 enforces `1 <= top_k <= 8`. No hidden recency boost,
random tie-break, provider ordering, approximate index, or post-hoc threshold may affect rank.

Quantization intentionally treats differences below the declared precision as ties. The exact vector
digests remain available for audit. A future ranking policy or precision requires a new version and
therefore new retrieval identity.

## Causality and revision semantics

`retrieval_as_of` is semantic strict-UTC state and participates in identity. Every candidate and its
selected revision must have become available at or before that instant. Lifecycle status filters, if
used, are derived by replaying append-only transitions only through that same cutoff; present-day
status is never projected backward.

An old immutable revision remains permanently stored and auditable. Default retrieval suppresses it
only when a valid later revision in its explicit supersession chain was already available at the
query cutoff. A revision arriving after the cutoff has no effect on that historical retrieval.

Task 2 reads no labels, Final OOS split, protected evaluation artifacts, or future runtime events.
If a Phase 8 source record itself links protected or prohibited scope, the source adapter fails
closed rather than rendering it.

## Authoritative append-only persistence

Migration 017 creates these logical tables:

- `retrieval_documents`;
- `embedding_requests`;
- `embedding_vectors`;
- `embedding_attempts`;
- `retrieval_index_manifests`;
- `retrieval_candidate_manifests`;
- `retrieval_requests`;
- `retrieval_results`;
- `retrieval_attempts`.

Canonical contract JSON and SHA-256 are stored for every semantic record. Vector rows additionally
store the canonical float32 BLOB and its digest. Manifest JSON stores the exact normalized member
list; indexed columns are lookup aids and must revalidate against canonical payloads.

Every table has `UPDATE` and `DELETE` rejection triggers. Same-ID/same-canonical-bytes appends are
idempotent. Same-ID/different-bytes, same attempt key with different semantics, orphan linkage,
altered digest, malformed member order, or mismatched provider/model identity fails closed. There is
no mutable current-index, current-vector, or current-result table.

Source paths, local process details, endpoints, and operational timestamps are safe audit metadata,
not content identity. Secrets, credentials, raw invalid provider bodies, exception traces, and hidden
reasoning are never persisted.

## Failure semantics

Embedding and retrieval attempts use explicit terminal statuses:

- `COMPLETED`;
- `REUSED`;
- `NO_MATCH`;
- `TIMEOUT`;
- `CONNECTION_ERROR`;
- `HTTP_ERROR`;
- `MODEL_UNAVAILABLE`;
- `MODEL_IDENTITY_MISMATCH`;
- `INVALID_VECTOR`;
- `DIMENSION_MISMATCH`;
- `PROVENANCE_MISMATCH`;
- `INCOMPLETE_INDEX`;
- `INVALID_FILTER`;
- `PROVIDER_ERROR`.

Successful/reused attempts require exact output linkage. Failures cannot reference a successful
vector or retrieval result. A failed batch publishes no completed vector from that response. Valid
documents or vectors committed by earlier completed requests remain immutable, but an incomplete
index manifest is never published as usable.

There is no lexical, recency, random, metadata-only, or alternative-model fallback after semantic
embedding failure. A later success appends a new attempt and artifact without overwriting the
failure. `NO_MATCH` is a valid auditable empty retrieval but cannot be adapted into Task 1 because
Task 1 requires evidence context.

## Task 1 integration boundary

Task 2 exposes one pure adapter:

```python
def build_reflection_explanation_input(
    retrieval_result: RetrievalResult,
    *,
    generation: LLMGenerationPolicy,
    source_resolver: ExactPhase8SourceResolver,
) -> ReflectionExplanationInput: ...
```

The adapter:

1. requires a completed retrieval result;
2. revalidates request, complete manifests, exact selected document/vector identities, and ranking;
3. reloads each selected Phase 8 source through the read-only resolver;
4. proves exact semantic ID, canonical digest, availability, and provenance equality;
5. maps the anchor and selected sources to existing `ReasoningSourceReference` records;
6. maps the anchor content plus each selected document's bounded semantic content to
   `BoundedReasoningContextItem`;
7. enforces Task 1 item and aggregate context budgets;
8. emits the existing `ReflectionExplanationInput` without changing the prompt or response schema.

Retrieval rank and similarity scores are deliberately omitted from LLM context so the generative
model cannot misread them as truth or confidence. The Task 1 request still binds every exact source,
context item, provider/model, prompt/schema, and generation policy. Task 1 remains responsible for
structured reasoning execution and its own request/response/attempt audit.

The adapter emits one anchor context item plus at most eight retrieved neighbor items. At the V1
1,500-character per-item cap, the maximum nine items remain below Task 1's existing 16-item and
16,000-character limits without truncation or query-dependent packing.

Task 2 does not automatically invoke Task 1. Indexing, retrieval, context construction, and reasoning
remain explicit operator-visible steps.

## CLI boundary

The eventual CLI should provide explicit offline commands such as:

- `build-index`;
- `run-retrieval`;
- `show-document`;
- `show-vector-metadata` (never dump vectors by default);
- `show-index-manifest`;
- `show-retrieval`;
- `show-history`;
- `retrieval-summary`;
- `build-reasoning-input`.

Commands accept only configured local Phase 8 store paths, retrieval store/output paths, controlled
anchor source IDs, typed filters, strict-UTC cutoff, top-k, loopback endpoint, exact model identity,
attempt keys, and explicit reuse policy. They expose no arbitrary query/prompt, URL/file retrieval,
Final OOS, runtime, broker, MT5, deployment, or proposal-mutation arguments.

All machine-readable outputs use canonical compact sorted ASCII JSON and safe metadata. Generated
stores and artifacts remain under ignored runtime paths.

## Safety invariants

- Retrieval and embedding are offline-only and optional.
- Retrieval never enters the deterministic live/replay decision kernel.
- Metadata filters always precede semantic ranking.
- Exact source bytes and provenance remain authoritative.
- Similarity and rank confer no truth, confidence, approval, or deployment status.
- Final OOS and protected dataset readers are structurally inaccessible.
- No arbitrary prompt, query text, web source, file source, tool, or plugin is accepted.
- No RAG, vector extension, Experience Graph, runtime integration, policy mutation, proposal
  promotion, deployment, broker, or MT5 behavior is introduced.
- The Task 1 prompt and structured response schema do not change.
- No hidden chain-of-thought is requested, accepted, or persisted.
- Model tags alone are never authoritative; exact provider/model/profile identity is mandatory.
- Partial indexes are never searched.
- No failed embedding silently changes retrieval semantics.

## Test strategy

### Contract tests

- strict frozen/versioned schemas and rejection of extra fields;
- strict UTC and finite numeric/vector values;
- canonical normalization and content-addressed identities;
- configured model-name changes are insufficient without complete model identity;
- provider, adapter, server, resolved name, digest, dimensions, family/quantization, or profile changes
  alter semantic identity;
- operational timestamp/path changes do not alter semantic identity;
- additive Task 1 `EXPERIENCE` provenance remains compatible without prompt/schema changes.

### Source and renderer tests

- every supported Phase 8 source type maps to exact references and typed metadata;
- canonical source-byte or digest mismatch fails closed;
- supporting provenance is preserved exactly;
- renderer output is deterministic and within context budgets;
- no arbitrary source adapter or query text is accepted;
- protected/Final OOS scope is rejected.

### Provider tests

- loopback-only URL enforcement;
- exact `/api/version` and `/api/tags` preflight;
- configured versus resolved model-name behavior;
- exact digest, 768 dimensions, family, quantization, adapter, and prefix profile checks;
- `/api/embed` uses `truncate=false` and deterministic input ordering;
- timeout, HTTP, connection, model, response-size, count, dimension, NaN/Inf, and zero-norm failures;
- deterministic fake transport is authoritative; real Ollama smoke is optional.

### Persistence and indexing tests

- migration 017 and foreign-key linkage;
- UPDATE/DELETE rejection on every table;
- same-ID/same-bytes idempotency and conflicting-byte rejection;
- canonical float32 little-endian encoding and digest verification;
- exact first-completed reuse skips the provider;
- fresh differing embeddings receive different vector IDs;
- failure-then-success preserves both attempts;
- deterministic incremental indexing and identical manifest reuse;
- incomplete index publication fails closed;
- latest-as-of supersession without deleting old revisions;
- ordinary recurring patterns are not incorrectly collapsed by `pattern_key`.

### Filtering and ranking tests

- temporal/source/typed metadata filters run before similarity;
- future records cannot enter historical candidate manifests;
- empty filters and empty results have explicit behavior;
- cosine fixtures use exact stored vectors;
- Decimal 12-place quantization and all tie-break levels;
- caller order, SQLite row order, and provider order cannot change ranking;
- top-k is bounded to eight;
- identical manifest/vector inputs produce byte-identical results;
- index, vector, or provenance mismatch yields unavailable/failure rather than fallback.

### Task 1 and boundary tests

- completed retrieval maps directly to valid `ReflectionExplanationInput`;
- selected Experience IDs can be cited through the additive source kind;
- scores/ranks do not appear in Task 1 context;
- Task 1 prompt/template and response-schema identities remain unchanged;
- Phase 8 source records remain byte-identical after indexing/retrieval;
- no fast-path package imports `axq.retrieval`;
- static audit finds no runtime, trading, Final OOS, broker, MT5, deployment, proposal-transition,
  RAG, embedding library, vector-store, Experience Graph, subprocess, plugin, or non-loopback path.

## Acceptance criteria

Task 2 is complete only when:

1. all approved immutable contracts and deterministic identities are implemented;
2. all six allowlisted Phase 8 source families produce exact auditable documents;
3. local Ollama embedding identity is verified as the complete authoritative tuple;
4. fixed fake-provider vectors index and retrieve deterministically;
5. metadata and temporal filters precede similarity and are fully captured in candidate manifests;
6. complete index manifests are mandatory;
7. float32 vector bytes, digests, ranking, score quantization, and ties are reproducible;
8. append-only store, failure preservation, and exact reuse are proven;
9. the output maps to Task 1 without prompt/schema changes or leaked scores;
10. Final OOS and every prohibited runtime/governance integration remain inaccessible;
11. focused and full repository validation pass;
12. documentation and Graphify are updated at the final gate;
13. no large indexing run or real Ollama dependency is required for acceptance;
14. no commit, push, merge, or Phase 9 Task 3 occurs without separate authorization.

## Deferred work

- Experience Graph or graph traversal;
- vector databases, SQLite vector extensions, or approximate nearest-neighbor indexes;
- RAG orchestration or automatic invocation of Task 1;
- arbitrary natural-language retrieval queries;
- additional embedding models or providers;
- cloud embeddings;
- hybrid lexical/semantic ranking, rerankers, score calibration, or learned thresholds;
- deletion, compaction, archival, and large-corpus performance tuning;
- large baseline indexing or quality evaluation;
- runtime, specialist, trading, broker, MT5, proposal, deployment, or Final OOS integration.
