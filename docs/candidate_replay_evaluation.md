# Governed Candidate Replay Evaluation

Phase 8 Task 7 creates deterministic DEVELOPMENT and VALIDATION metric-sample artifacts for one
exact persisted proposal, candidate, and evaluation plan. It establishes the governed replay-engine
boundary with the allowlisted `CONTROLLED_REPLAY_FIXTURE_V1` implementation only. Task 7 does not
inject candidates into the full Phase 7 runtime and does not execute the seven baseline proposals.

## Controlled input and engine

A `ControlledReplayFixtureArtifact` is a content-addressed causal stream of strict-UTC observations.
It binds the exact proposal/candidate/plan and one DEVELOPMENT or VALIDATION scope. Every observation
contains finite values for exactly the metric keys preregistered for that scope. The engine orders
observations by `(available_at, event_id)` and emits one Task 6
`CanonicalMetricSampleArtifact` per required scope without aggregation, tuning, or parameter search.

The service loads authoritative proposal, candidate, and plan records from the shared SQLite store.
A new request requires the proposal's current append-only lifecycle status to be `CANDIDATE` and
must reproduce the plan seed/environment and exact input scopes. Final OOS references and fixtures
are rejected, and the CLI has no Final OOS option.

## Determinism and persistence

`CandidateReplayRequest` identity binds proposal/candidate/plan/run linkage, engine kind/version,
seed/environment, and exact input semantic IDs and canonical-byte SHA-256 digests. `requested_at`
is strict-UTC operational metadata excluded from identity.

Migration `011_candidate_replay_evaluation.sql` stores append-only requests, input references,
canonical output artifacts, output references, and completed audits. An audit binds all request
facts and exact output IDs/digests. `started_at` and `completed_at` are strict-UTC metadata excluded
from audit identity. Every new table rejects UPDATE and DELETE.

An equivalent completed retry returns the stored canonical output bytes without invoking the engine
again. Output directories do not participate in identity. A failed digest, linkage, metric, or scope
check creates no completed audit.

## Task 6 handoff

The emitted JSON files validate directly as Task 6 `CanonicalMetricSampleArtifact` objects. Their
Task 6 input references are derived from the same artifact IDs and canonical-byte digests. Task 6
then applies the plan's preregistered aggregations and creates `ProposalEvaluationResult`; any Final
OOS metric remains `UNAVAILABLE / FINAL_OOS_NOT_ACCESSED`.

## Controlled CLI

The database must already contain the exact CANDIDATE proposal, candidate spec, and plan:

```powershell
python -m axq.reflection run-candidate-replay --store runtime/phase8-task7/candidate-replay.sqlite3 --request candidate-replay-request.json --validation-input validation-replay-fixture.json --output-dir runtime/phase8-task7/artifacts --started-at 2026-09-11T12:00:00Z --completed-at 2026-09-11T12:00:01Z
python -m axq.reflection show-candidate-replay --store runtime/phase8-task7/candidate-replay.sqlite3 --request-id <request-id>
python -m axq.reflection candidate-replay-summary --store runtime/phase8-task7/candidate-replay.sqlite3
```

Add `--development-input development-replay-fixture.json` only when the plan declares DEVELOPMENT
metrics. No command promotes a proposal, deploys a candidate, mutates runtime, contacts a broker, or
opens Final OOS data.
