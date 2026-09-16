# Deterministic Evaluation Execution

Phase 8 Task 6 executes one already-persisted `ProposalEvaluationPlan` through the deliberately
narrow `CANONICAL_METRIC_SAMPLES_V1` adapter. It accepts reviewed DEVELOPMENT and VALIDATION metric
sample artifacts only. It does not run replay, train or tune a candidate, load plugins, access a
broker, promote a proposal, deploy a change, or mutate production runtime behavior.

## Identity and inputs

`CanonicalMetricSampleArtifact` contains a scope, strict-UTC `available_at`, and finite samples by
metric key. Its semantic ID and its canonical-byte SHA-256 are both bound into an
`EvaluationExecutionRequest`. The request identity includes the exact plan/candidate/run key,
adapter kind/version, seed, environment, and ordered input semantic IDs/digests. `requested_at` is
strict-UTC audit metadata and is deliberately excluded from that identity.

The adapter requires exact equality with the persisted plan and candidate. Input scopes must equal
the plan's required non-Final-OOS scopes, input digests must match canonical bytes, and sample keys
must match the preregistered metrics for each supplied scope. The closed aggregation set is
`MEAN`, `MIN`, `MAX`, `SUM`, and `COUNT`; an undeclared aggregation fails before execution. No
metric outside the plan can be computed or included in the result.

## Protected Final OOS

Final OOS is never an execution input. The contracts reject Final OOS artifacts, the CLI exposes no
Final OOS path, and the adapter never requests or opens one. Each preregistered Final OOS metric is
preserved in the `ProposalEvaluationResult` as `UNAVAILABLE`, with zero samples and reason code
`FINAL_OOS_NOT_ACCESSED`. These reporting-only observations cannot support or reject a candidate.

## Persistence and retry

Migration `010_evaluation_execution.sql` adds append-only execution requests, exact input refs, and
terminal audits. A completed `EvaluationExecutionAudit` binds the exact request/result/plan/
candidate/input linkage, adapter/version, seed/environment, canonical result digest, and terminal
status. `started_at` and `completed_at` are strict-UTC metadata excluded from audit identity.

An identical completed request is recovered without invoking the adapter again. Equivalent
semantic requests over identical canonical input bytes therefore reuse the same request, result,
and audit IDs and reproduce the same result bytes even when retried later. An input mismatch or a
missing persisted link fails closed; records are never updated or deleted.

## Controlled CLI workflow

The store must already contain the exact CANDIDATE proposal, candidate spec, and plan. Timestamps
are explicit operational audit inputs, not identity inputs:

```powershell
python -m axq.reflection run-evaluation-execution --store runtime/phase8-task6/evaluations.sqlite3 --request execution-request.json --validation-input validation-samples.json --result-output runtime/phase8-task6/result.json --started-at 2026-09-11T12:00:00Z --completed-at 2026-09-11T12:00:01Z
python -m axq.reflection show-evaluation-execution --store runtime/phase8-task6/evaluations.sqlite3 --request-id <request-id>
python -m axq.reflection evaluation-execution-summary --store runtime/phase8-task6/evaluations.sqlite3
```

Add `--development-input development-samples.json` only when the stored plan preregisters
DEVELOPMENT metrics. Task 6 validation uses a single controlled fixture; it does not execute the
seven baseline advisory proposals.
