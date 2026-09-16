# Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design

## Scope

Task 5 preregisters immutable evaluation plans for explicitly promoted proposal candidates, stores
externally supplied evaluation evidence, and records a separate operator evidence decision. It does
not execute replay, walk-forward, challenger, model, tuning, deployment, or runtime work.

The source proposal remains authoritative in the Task 4 append-only store. Task 5 has no authority
to append a proposal lifecycle transition. `VALIDATED`, `ACCEPT_EVIDENCE`, or a passing criterion
never means deployed.

## Registration boundary

An evaluation plan may be registered only when:

- the exact `ImprovementProposal` exists;
- its current status, derived from the exact transition chain, is `CANDIDATE`;
- the candidate spec references that exact proposal ID/key and target component;
- the plan's pattern, finding, daily-reflection, experience, and weekly-reflection source
  collections exactly equal the proposal's canonical supporting-source collections; and
- every external candidate/source artifact is identified by a stable semantic ID and SHA-256 digest.

`OBSERVATION`, `HYPOTHESIS`, `VALIDATED`, `REJECTED`, and `DEPRECATED` proposals cannot register a
new plan. Registration is an explicit operator action and does not alter proposal status.

## Candidate contract

`EvaluationCandidateSpec` is immutable and content-addressed. It includes:

- `candidate_id`;
- exact proposal ID/key and target component;
- candidate kind (`CONFIGURATION`, `RULE`, `FEATURE`, `MODEL`, or `PROCESS`);
- a bounded description of the candidate under evaluation;
- implementation version and source/config/manifest semantic IDs;
- SHA-256 content digests for every referenced candidate artifact; and
- `defined_at`, supplied explicitly as an aware UTC timestamp.

The candidate spec describes a frozen subject. It has no callable, command, broker, registry, or
deployment field. Candidate identity excludes storage sequence, filesystem path, and wall-clock
insertion time.

## Preregistered plan

`ProposalEvaluationPlan` is immutable and content-addressed. It binds:

- exact proposal and candidate IDs;
- exact proposal source pattern, finding, daily-reflection, experience, and weekly-reflection IDs;
- an explicit deterministic seed and environment identity;
- a tuple of `ValidationMetricSpec` records;
- a tuple of `AcceptanceCriterion` records;
- minimum sample requirements and explicit missing-data behavior;
- protected Final OOS policy `REPORTING_ONLY`;
- explicit `defined_at` and optional `supersedes_plan_id`; and
- operator/action identity that authorized registration.

Each metric specification declares a stable metric key, name, unit, aggregation, data scope, and
direction. Supported scopes are `DEVELOPMENT`, `VALIDATION`, and `FINAL_OOS`. Each acceptance
criterion declares one metric key, comparator (`GE`, `LE`, or `BETWEEN`), literal threshold(s),
minimum samples, and role (`DECISION` or `REPORTING_ONLY`).

Every plan must contain at least one non-Final-OOS `DECISION` criterion. Every Final OOS criterion
must be `REPORTING_ONLY`. A non-Final-OOS reporting metric is allowed. Final OOS can never determine
candidate acceptance, selection, calibration, tuning, or plan identity after results exist.

Plans exist before results. A plan cannot contain observed values, outcome status, result IDs, or
execution metadata. A revised plan is a new content-addressed record that explicitly supersedes the
latest plan for the same proposal/candidate evaluation subject; it never changes an earlier plan or
any result already linked to that plan.

## Evaluation result

`ProposalEvaluationResult` is immutable and content-addressed. It includes:

- exact plan, proposal, and candidate IDs;
- an explicit evaluation run key and evidence availability timestamp;
- one `MetricObservation` for every preregistered metric and no undeclared metrics;
- observed value or explicit unavailable state, sample count, data scope, and evidence IDs/digests;
- one `CriterionOutcome` for every preregistered criterion;
- aggregate outcome `SUPPORTED`, `NOT_SUPPORTED`, or `INCONCLUSIVE`; and
- optional `supersedes_result_id` for a corrected result under the same run key.

A pure result builder evaluates only the preregistered comparator, thresholds, minimum samples, and
missing-data behavior. Result input cannot supply or replace criteria. `SUPPORTED` depends only on
`DECISION` criteria. Final OOS observations and criterion outcomes are retained for reporting but
are excluded structurally from aggregate acceptance.

Missing or insufficient decision evidence yields `INCONCLUSIVE`; a failed decision criterion yields
`NOT_SUPPORTED`; all available decision criteria passing yields `SUPPORTED`. These are evidence
outcomes, not proposal lifecycle transitions.

## Operator decision boundary

`OperatorEvaluationDecision` is a separate immutable record with decision
`ACCEPT_EVIDENCE`, `REJECT_EVIDENCE`, or `DEFER`. It references the exact result, plan, proposal,
candidate, actor/action, reason, aware UTC effective time, and only preregistered non-Final-OOS
decision-criterion IDs used by the operator.

An operator may accept or reject evidence regardless of the aggregate result only with an explicit
reason; the record remains an audit fact. No decision appends a proposal transition or writes code,
configuration, registry state, runtime state, or deployment state. A later operator decision must
append and explicitly reference the previous decision; current decision is reconstructed by exact
linear replay.

## Identity and serialization

All contracts use strict frozen versioned schemas and canonical JSON. Tuples and semantic-ID maps
are normalized deterministically before identity binding. IDs derive from complete semantic content
except their own ID field. Explicit UTC knowledge times are semantic inputs; database sequence,
temporary path, process ID, and insertion time are not.

Candidate, plan, result, observation, criterion-outcome, and decision identities are distinct.
Equivalent inputs in any iteration order produce identical IDs and canonical JSON.

## Append-only persistence

Migration `009_proposal_evaluation.sql` creates append-only tables for candidate specs, plans,
metric definitions, criteria, results, metric observations, criterion outcomes, exact evidence
sources, and operator decisions. UPDATE and DELETE triggers protect every table. There is no mutable
current-state, acceptance, proposal-status, candidate registry, or deployment table.

The store enforces:

- candidate proposal/key/target compatibility;
- exact equality between plan source collections and the persisted proposal's canonical sources;
- CANDIDATE-only plan registration using the Task 4 store's replayed status;
- plan-before-result insertion;
- result-to-plan metric and criterion equality;
- exact evidence ID/digest linkage;
- explicit latest-plan and corrected-result supersession;
- decision-after-result insertion;
- exact linear operator-decision history;
- idempotent identical inserts; and
- fail-closed same-ID conflicts, stale predecessors, missing sources, or time reversal.

Recovery is the append-only semantic history. SQLite checkpoints are durability optimizations only.

## CLI

The existing `python -m axq.reflection` entry point gains:

- `register-evaluation-candidate`
- `build-evaluation-plan`
- `record-evaluation-result`
- `record-operator-evaluation-decision`
- `show-evaluation-plan`
- `show-evaluation-result`
- `show-operator-evaluation-history`
- `evaluation-summary`

Candidate, plan, result-evidence, and operator-decision inputs are reviewed canonical JSON files.
The CLI validates and stores them; it never launches an evaluator. `build-evaluation-plan` combines
an exact stored proposal/candidate with preregistered metric/criteria input and fails unless the
proposal is currently `CANDIDATE`. `record-evaluation-result` derives outcomes from the stored plan
and supplied observations; criteria cannot be supplied by the result file.

CLI output is compact sorted JSON with IDs, counts, evidence outcome, data-scope counts, decision
counts, supersession counts, and current operator evidence decision. Paths are operational inputs
and are excluded from semantic identities.

## Validation

Tests use tiny synthetic records and real temporary SQLite databases. They cover strict UTC,
literal content identities, input-order invariance, CANDIDATE gating, exact source linkage,
plan-before-result order, undeclared/missing metrics, comparator outcomes, sample guards, explicit
unavailable values, Final OOS reporting-only enforcement, result/plan immutability, supersession,
append-only triggers, operator history, idempotent CLI output, and the absence of execution or
promotion paths.

Task 5 validation does not run the seven baseline proposals because they remain `OBSERVATION` and
must not be promoted automatically for test convenience. A synthetic proposal is explicitly moved
through `HYPOTHESIS` to `CANDIDATE` in test fixtures before plan registration. Full pytest, Ruff,
strict mypy, pip integrity, diff checks, and one Graphify refresh close the task.
