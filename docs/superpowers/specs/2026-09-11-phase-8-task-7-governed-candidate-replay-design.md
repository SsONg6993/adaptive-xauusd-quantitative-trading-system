# Phase 8 Task 7 Governed Candidate Replay Evaluator Design

## Scope

Task 7 produces deterministic DEVELOPMENT and VALIDATION
`CanonicalMetricSampleArtifact` records for one exact persisted
`ProposalEvaluationPlan` and `EvaluationCandidateSpec`. Task 6 remains the only layer that consumes
those samples and creates a `ProposalEvaluationResult`.

Task 7 provides one allowlisted `CONTROLLED_REPLAY_FIXTURE_V1` engine. It establishes the governed
engine, identity, persistence, and compatibility boundaries without injecting candidate behavior
into the full Phase 7 runtime. It does not execute the seven baseline proposals.

## Contracts and identity

`CandidateReplayRequest` is frozen, versioned, strict, and content-addressed. It binds the exact
proposal, candidate, plan, evaluation run key, engine kind/version, deterministic seed/environment,
and one content-digested input reference for every required non-Final-OOS plan scope. Its
`requested_at` field is strict-UTC operational metadata excluded from semantic identity. Filesystem
paths and mutable status do not participate in identity.

`ControlledReplayFixtureArtifact` is the only accepted input. It binds the exact proposal,
candidate, plan, scope, strict-UTC availability, and a causally ordered non-empty sequence of
immutable `ControlledReplayObservation` records. Each observation has a unique event ID,
strict-UTC `available_at`, and unique finite values keyed by metric. Fixture identity includes all
semantic content. Canonical sorted-key compact JSON bytes determine the stored SHA-256.

`CandidateReplayAudit` binds the request, proposal/candidate/plan, run key, engine/version,
seed/environment, exact input refs, exact Task 6-compatible output refs, and terminal `COMPLETED`
status. `started_at` and `completed_at` remain strict-UTC audit metadata excluded from semantic
audit identity. Equivalent semantic retries therefore preserve request, output, and audit IDs.

## Exact linkage and Final OOS boundary

The service reloads the proposal, candidate, and plan from their existing authoritative stores.
It rejects missing records, non-CANDIDATE current proposal status, candidate/plan/proposal mismatch,
seed/environment mismatch, stale or incorrect artifact digests, and input scopes that do not equal
the plan's DEVELOPMENT/VALIDATION scope set.

`FINAL_OOS` is forbidden in input references and fixture artifacts. The CLI exposes no Final OOS
argument. The engine considers only plan metrics in the current non-Final-OOS scope; Final OOS keys
are neither requested nor emitted.

## Controlled replay engine

`CandidateReplayEngine` is a narrow in-process protocol. The only Task 7 implementation is
`ControlledReplayFixtureEngine`, selected by the closed
`CONTROLLED_REPLAY_FIXTURE_V1` kind/version pair. It receives authoritative stored records and
already digest-verified fixture artifacts. It has no filesystem, subprocess, plugin, broker,
deployment, proposal-lifecycle, or runtime-mutation capability.

For each scope, every observation must contain exactly the preregistered metric keys for that scope.
The engine orders observations causally by `(available_at, event_id)`, collects each metric's values
without aggregation or parameter selection, and creates one Task 6 `CanonicalMetricSampleArtifact`.
Missing, extra, duplicate, wrong-scope, non-finite, or undeclared values fail closed. The engine
never changes the candidate or plan.

## Persistence, service, and reuse

Migration `011_candidate_replay_evaluation.sql` stores immutable requests, exact input refs,
canonical output artifacts, exact output refs, and completed audits. Every table rejects UPDATE and
DELETE. There is no mutable running-state table.

The service appends the request before evaluation. If a completed exact audit exists, it reloads
the stored output artifacts, verifies their canonical byte digests, and returns them without
invoking the engine. Otherwise it validates all linkage and input bytes, invokes the allowlisted
engine once, persists the outputs, then appends the terminal audit. Failures never create a
completed audit and may be retried using the same semantic request.

Output directories and retry times are operational only. A later equivalent request with identical
canonical input bytes reuses identical request, artifact, and audit IDs and produces byte-identical
artifact files.

## CLI

`run-candidate-replay` accepts the shared store, canonical request JSON, optional DEVELOPMENT and
VALIDATION fixture paths, an output directory, and explicit strict-UTC start/completion times. It
accepts exactly the scopes required by the plan and writes one canonical artifact per scope.

`show-candidate-replay` returns the stored request, audit, and output artifacts for a request ID.
`candidate-replay-summary` reports request/audit/artifact counts, scopes, engine/status counts, and
reuse-independent semantic IDs. No command changes proposal status.

## Validation

Tests use one synthetic proposal explicitly advanced to CANDIDATE, one exact candidate/plan, and a
tiny causal fixture. They prove strict UTC, content identity, timestamp exclusion, exact linkage,
Final OOS rejection, preregistered-key enforcement, append-only persistence, engine-once reuse,
byte identity, CLI behavior, and unchanged proposal status.

The end-to-end test constructs a Task 6 `EvaluationExecutionRequest` directly from Task 7 output
refs and artifacts, then verifies Task 6 creates the exact linked `ProposalEvaluationResult`, with
any preregistered Final OOS metric represented only as
`UNAVAILABLE / FINAL_OOS_NOT_ACCESSED`.
