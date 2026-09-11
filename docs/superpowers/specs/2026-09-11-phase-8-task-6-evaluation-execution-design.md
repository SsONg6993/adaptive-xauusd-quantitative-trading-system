# Phase 8 Task 6 Deterministic Evaluation Execution Adapter Design

## Scope

Task 6 executes one already-persisted `ProposalEvaluationPlan` through the closed
`CANONICAL_METRIC_SAMPLES_V1` adapter. It reads only content-digested DEVELOPMENT and VALIDATION
sample artifacts, computes only preregistered metrics, creates a Task 5-compatible result, and
records append-only execution audit metadata.

Task 6 does not run replay, train or tune a candidate, invoke a subprocess/plugin evaluator, access
Final OOS data, promote a proposal, deploy a candidate, mutate runtime state, or contact a broker.
The seven real baseline proposals remain untouched.

## Contracts

`EvaluationExecutionRequest` is strict, frozen, versioned, and content-addressed. It binds:

- exact `plan_id`, `candidate_id`, and `evaluation_run_key`;
- adapter kind `CANONICAL_METRIC_SAMPLES_V1` and implementation version `1.0`;
- the deterministic seed and environment identity copied from the plan;
- one `ExecutionInputArtifactRef` per required non-Final-OOS scope;
- an explicit aware UTC `requested_at` audit timestamp; and
- no filesystem path, command, callable, mutable status, or deployment field.

Request identity includes only the exact plan/candidate/run linkage, adapter kind/version,
deterministic seed/environment, and exact input artifact semantic IDs/digests. `requested_at`
remains serialized strict UTC audit metadata but is explicitly excluded from semantic request
identity. Retrying the same semantic request later therefore preserves `request_id`.

An input reference contains only `scope`, `semantic_id`, and lowercase SHA-256. Scope is limited to
`DEVELOPMENT` or `VALIDATION`; construction rejects `FINAL_OOS`.

`CanonicalMetricSampleArtifact` is immutable and content-addressed. It contains exactly one allowed
scope, explicit UTC `available_at`, and sorted unique `MetricSampleSeries` records. Each series has a
`metric_key` and a non-empty finite tuple of values. Canonical JSON bytes determine its SHA-256.

Task 5 `MetricObservation` gains optional `reason_code`. AVAILABLE requires a value and no reason;
UNAVAILABLE requires no value, zero samples, and a reason. Existing available observations remain
source compatible through the default `None`.

`EvaluationExecutionAudit` is immutable and content-addressed. Its semantic identity binds the exact
request, result, plan, candidate, input references, adapter/version, seed/environment, result
artifact digest, and terminal `COMPLETED` status. Explicit `started_at` and `completed_at` values are
serialized strict UTC audit metadata but are excluded from semantic audit identity. Task 6 does not
add a mutable running-state row. Validation failures are raised before completion and cannot be
disguised as a completed audit.

## Exact linkage and execution

The service loads the plan and candidate from `SQLiteProposalEvaluationStore`; caller-supplied
copies are not authoritative. It fails closed unless request plan/candidate, seed, environment, and
required DEVELOPMENT/VALIDATION scope set exactly match the stored records. Every input file is
parsed as `CanonicalMetricSampleArtifact`, matched to its request reference, and verified against
canonical bytes and SHA-256 before evaluation.

For each preregistered DEVELOPMENT or VALIDATION metric, the adapter selects the exact same-scope
series and applies only the declared aggregation. Version 1 supports the closed set `MEAN`, `MIN`,
`MAX`, `SUM`, and `COUNT`. Unsupported aggregations, missing series, duplicate keys, extra series,
scope mismatches, non-finite values, or undeclared metrics fail closed. No candidate parameter is
read or changed during execution.

For each preregistered FINAL_OOS metric, the adapter never requests or opens an artifact. It emits:

- `status = UNAVAILABLE`;
- `value = null`;
- `sample_count = 0`; and
- `reason_code = FINAL_OOS_NOT_ACCESSED`.

The evidence reference for this observation is a deterministic semantic marker derived from the
request and metric, not a Final OOS data artifact. The existing `build_evaluation_result` evaluates
the complete observation set. Because every Final OOS criterion is reporting-only, these explicit
unavailable observations cannot affect aggregate support or operator acceptance.

## Result artifact and determinism

The canonical `ProposalEvaluationResult.model_dump_json()` representation, normalized through
sorted-key compact JSON, is the result artifact. Its SHA-256 is recorded in the audit. Output paths
are operational CLI arguments and never enter request, result, or audit identity.

Identical persisted plan/candidate, semantic request fields, and canonical input bytes produce
identical request, metric-observation, result, and audit IDs plus identical result bytes, even when
`requested_at`, `started_at`, and `completed_at` differ on a later retry. If a completed audit already
exists for the request, the service loads and verifies its exact linked result and digest, then
reuses it without re-executing the adapter or appending records.

## Append-only persistence

Migration `010_evaluation_execution.sql` adds:

- `evaluation_execution_requests`;
- `evaluation_execution_input_refs`; and
- `evaluation_execution_audits`.

Every table rejects UPDATE and DELETE. Requests and audits accept identical inserts idempotently and
reject same-ID content conflicts. A completed audit must reference an existing exact plan,
candidate, and result. Its result must reference the same plan/candidate/run key. Input references
must equal the request. There is no mutable current-state, tuning, registry, promotion, deployment,
or runtime table.

The Task 5 result may be written before its Task 6 audit. If a process stops between those appends,
retry deterministically reuses the same result and appends the missing audit. The persisted Task 5
result plus Task 6 request/audit history remains authoritative.

## CLI

The reflection CLI gains:

- `run-evaluation-execution`;
- `show-evaluation-execution`; and
- `evaluation-execution-summary`.

`run-evaluation-execution` accepts `--store`, `--request`, optional `--development-input`, optional
`--validation-input`, and `--output`. It has no Final OOS argument. It requires exactly the input
paths whose scopes are named by the request and plan. The output file receives canonical result JSON.

Show returns request, audit, and exact result linkage. Summary reports request/audit/result counts,
adapter counts, reused runs, input scope counts, metric status/scope counts, and Final OOS withheld
counts. Neither command advances proposal lifecycle.

## Validation

Tests use one explicitly promoted synthetic proposal, a stored candidate/plan, and tiny canonical
sample artifacts. They prove contract immutability, UTC and digest checks, exact linkage, closed
aggregations, undeclared/missing/extra-series rejection, Final OOS non-access, Task 5-compatible
results, byte-identical reruns, idempotent completed-request reuse, append-only triggers, CLI output,
and unchanged proposal status. No real baseline proposal or serious evaluation is run.
