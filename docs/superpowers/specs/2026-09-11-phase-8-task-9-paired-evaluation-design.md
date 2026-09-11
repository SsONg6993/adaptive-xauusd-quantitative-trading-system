# Phase 8 Task 9 Deterministic Paired Evaluation Design

## Purpose and boundary

Task 9 compares one frozen baseline evidence set with one frozen candidate evidence set without
executing either system. It consumes canonical DEVELOPMENT and VALIDATION metric-sample artifacts
already produced by governed upstream adapters. It does not run the shared kernel, open market-data
files, tune parameters, access Final OOS, promote a proposal, deploy code, mutate runtime, or contact
MT5.

The comparison is governed by one already-persisted `ProposalEvaluationPlan`. The plan's existing
`AcceptanceCriterion` records remain the only acceptance rules. Baseline values and
candidate-minus-baseline deltas are evidence only and cannot change a criterion outcome.

## Contracts

`PairedEvaluationRequest` is immutable and content-addressed. It binds:

- exact proposal, candidate, and plan IDs;
- exact baseline `SharedKernelPolicySet` ID and candidate configuration ID;
- one baseline and one candidate artifact reference for every non-Final-OOS plan scope;
- identical baseline and candidate `SharedKernelDataManifestRef` collections;
- the plan's deterministic seed and environment identity;
- an evaluation run key and comparison adapter kind/version.

`requested_at` is strict UTC audit metadata and is excluded from request identity. Final OOS is not
a permitted manifest or artifact scope.

Each side artifact reference records scope, canonical artifact ID/digest, exact manifest ID/digest,
and policy identity. Baseline references use the baseline policy-set ID. Candidate references use
the frozen candidate-config ID. This makes policy, data, and metric evidence explicit without
claiming that Task 9 produced either side.

`PairedMetricComparison` records the exact metric ID/key/scope, baseline and candidate artifact
references, both sample counts and aggregated values, and `delta = candidate - baseline`.
Numeric evidence is serialized as canonical decimal strings. Conversion starts from `str(float)`;
subtraction uses `decimal.Decimal`; normalized finite results use a unique non-exponent decimal form,
with all signed zero representations canonicalized to `"0"`. Missing values remain `null`, never
numeric zero.

`PairedCriterionOutcome` has `PASS`, `FAIL`, or `UNAVAILABLE`. It links the unchanged criterion ID,
metric key, role, and paired metric comparison ID. PASS/FAIL is copied from evaluating the candidate
observation through the existing Task 5 criterion implementation. It becomes UNAVAILABLE whenever
the paired metric is unavailable, including missing side evidence or failed manifest, seed,
environment, scope, artifact-digest, or linkage parity.

`PairedEvaluationResult` contains all preregistered metrics, all preregistered criteria, explicit
parity checks, exact source references, and an availability timestamp derived from source evidence.
Final OOS metrics are represented only as unavailable comparison records with reason
`FINAL_OOS_NOT_ACCESSED`; no Final OOS input reference exists.

`PairedEvaluationAudit` binds the exact request/result/source digests, adapter/version, seed,
environment, and terminal `COMPLETED` status. Strict-UTC `started_at` and `completed_at` are audit
metadata excluded from semantic identity.

## Validation and comparison flow

The service first persists the request, then resolves the exact proposal, candidate, plan, frozen
config, and referenced manifests from existing append-only stores. Unknown authoritative IDs are
rejected because no governed comparison subject exists. Once authority is established, every
baseline/candidate parity condition is evaluated explicitly.

Canonical metric artifacts are provided to the comparison service and verified byte-for-byte
against the request references. Task 6 aggregation semantics are reused for both sides. No metric
outside the plan is accepted. For each DEVELOPMENT or VALIDATION metric, both available observations
produce canonical baseline, candidate, and delta evidence. If either observation or any required
parity check is unavailable, the paired metric and every linked criterion are UNAVAILABLE.

Candidate observations alone are evaluated against the plan's existing criteria. No delta threshold,
baseline threshold, direction-derived rule, or post-plan acceptance condition is created. Reporting-
only criteria remain reporting-only.

## Persistence and idempotency

Migration 013 adds append-only request, input-reference, result, and completed-audit tables. UPDATE
and DELETE triggers reject mutation. Identical semantic requests reuse the completed result and
audit without recomputing. A retry with later operational timestamps therefore returns the same
request, result, audit IDs and canonical result bytes.

Request identity includes all semantic linkage, policy/config identities, exact manifest and artifact
digests, seed/environment, adapter kind/version, and run key. Result identity includes the request,
comparisons, criterion outcomes, parity checks, and exact evidence. Audit identity excludes only its
operational timestamps.

## CLI and controlled validation

The reflection CLI adds `run-paired-evaluation`, `show-paired-evaluation`, and
`paired-evaluation-summary`. Run accepts request JSON plus baseline/candidate canonical artifacts for
DEVELOPMENT and VALIDATION only. There is no Final OOS argument.

The first fixture uses one persisted controlled CANDIDATE plan, identical deterministic manifests,
the same seed/environment, and small canonical metric artifacts. Tests cover exact linkage, parity
failure, decimal-safe deltas, unchanged criterion semantics, Final OOS withholding, append-only
storage, retry reuse, CLI output, import boundaries, and compatibility with Task 6/7/8 artifacts.

## Explicit exclusions

Task 9 does not rerun baseline or candidate, introduce delta acceptance criteria, search or tune,
evaluate the seven real proposals, promote proposals, deploy, mutate runtime, use broker/MT5 code,
or begin the next task or Phase 9.
