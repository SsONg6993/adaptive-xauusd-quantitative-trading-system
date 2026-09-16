# Proposal Evaluation

Phase 8 Task 5 preregisters evaluation semantics and persists externally produced evidence. It does
not run an evaluator, replay, challenger, training, tuning, deployment, or runtime mutation.

## Governance boundary

An `EvaluationCandidateSpec` freezes the exact subject under evaluation with its proposal ID/key,
target component, semantic source/config/manifest identities, artifact SHA-256 digests, and explicit
UTC definition time. It contains no executable command or deployment authority.

A `ProposalEvaluationPlan` can be registered only while the exact persisted proposal's replayed
status is `CANDIDATE`. The plan copies all canonical pattern, finding, daily-reflection, Experience,
and weekly-reflection IDs from that proposal. It preregisters metrics, criteria, sample thresholds,
environment identity, seed, missing-data behavior, and operator authorization before results exist.

Metric scopes are `DEVELOPMENT`, `VALIDATION`, and `FINAL_OOS`. Every plan requires at least one
non-Final-OOS decision criterion. Every Final OOS criterion is structurally `REPORTING_ONLY` and is
excluded from `SUPPORTED`, `NOT_SUPPORTED`, and `INCONCLUSIVE` aggregation. Final OOS can report
performance but cannot select, tune, calibrate, or accept a candidate.

`ProposalEvaluationResult` stores exactly one observation for every declared metric and derives
criterion outcomes only from the persisted plan. Missing or undersampled decision evidence is
`INCONCLUSIVE`; any failed decision criterion is `NOT_SUPPORTED`; otherwise evidence is
`SUPPORTED`. Result input cannot add or replace criteria.

`OperatorEvaluationDecision` records `ACCEPT_EVIDENCE`, `REJECT_EVIDENCE`, or `DEFER` separately.
It may reference only declared non-Final-OOS decision criteria. This record does not transition the
proposal, write configuration, register a model, deploy anything, or mutate runtime behavior.
`VALIDATED` and `ACCEPT_EVIDENCE` are evidence states, never deployment states.

## Persistence and corrections

Migration `009_proposal_evaluation.sql` stores candidates, plans, exact plan sources, metric and
criterion definitions, results, observations and evidence digests, criterion outcomes, and operator
decisions. Every table rejects UPDATE and DELETE. There is no mutable current-state or deployment
table.

Identical inserts are idempotent. A revised plan must append with `supersedes_plan_id` naming the
latest plan for the exact proposal/candidate subject. Corrected evidence for the same plan/run key
must append with `supersedes_result_id`. Later operator decisions append a linear
`previous_decision_id` chain. Missing parents, stale predecessors, altered criteria, source
mismatches, and time reversal fail closed.

## CLI workflow

All input files are reviewed canonical JSON. The commands only validate and persist records:

```powershell
python -m axq.reflection register-evaluation-candidate --store runtime/phase8-task5/evaluations.sqlite3 --input candidate.json
python -m axq.reflection build-evaluation-plan --store runtime/phase8-task5/evaluations.sqlite3 --input plan.json
python -m axq.reflection record-evaluation-result --store runtime/phase8-task5/evaluations.sqlite3 --input result-evidence.json
python -m axq.reflection record-operator-evaluation-decision --store runtime/phase8-task5/evaluations.sqlite3 --input operator-decision.json
python -m axq.reflection show-evaluation-plan --store runtime/phase8-task5/evaluations.sqlite3 --plan-id <plan-id>
python -m axq.reflection show-evaluation-result --store runtime/phase8-task5/evaluations.sqlite3 --result-id <result-id>
python -m axq.reflection show-operator-evaluation-history --store runtime/phase8-task5/evaluations.sqlite3 --result-id <result-id>
python -m axq.reflection evaluation-summary --store runtime/phase8-task5/evaluations.sqlite3
```

The proposal and evaluation records must share the same SQLite database so foreign keys and exact
lifecycle replay remain authoritative. The existing seven Task 4 baseline proposals remain
`OBSERVATION`; Task 5 does not promote or evaluate them automatically.
