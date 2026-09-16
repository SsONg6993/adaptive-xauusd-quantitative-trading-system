# Deterministic paired baseline-vs-candidate comparison

Phase 8 Task 9 compares canonical baseline and candidate metric evidence without rerunning either
system. One immutable request binds the exact persisted proposal, candidate, evaluation plan,
baseline policy set, candidate configuration, DEVELOPMENT/VALIDATION manifests, canonical artifacts,
deterministic seed, and environment identity.

## Governance

Every comparison uses the plan's existing `ValidationMetricSpec` and `AcceptanceCriterion` records.
The candidate observation alone determines `PASS` or `FAIL`. Baseline values and
`candidate - baseline` deltas are evidence only. No delta threshold, direction-derived rule, or
post-plan acceptance condition exists.

If scope, manifest, seed, environment, policy/config linkage, artifact digest, or metric definitions
do not establish an exact pair, the paired metrics and criteria are `UNAVAILABLE`. Final OOS input
references are structurally forbidden. Preregistered Final OOS metrics remain visible only as
`UNAVAILABLE / FINAL_OOS_NOT_ACCESSED`.

Values and deltas use normalized finite decimal strings. The controlled fixture produced:

| Metric | Baseline | Candidate | Delta | Criterion |
|---|---:|---:|---:|---|
| `validation_master_actionable_rate` | `0.15` | `0.3` | `0.15` | `PASS` |
| `final_oos_master_actionable_rate` | unavailable | unavailable | unavailable | `UNAVAILABLE` |

This is pipeline validation, not evidence that the candidate is better or profitable.

## Persistence and retry behavior

Migration 013 stores immutable requests, input references, results, and completed audits. UPDATE and
DELETE are rejected. Operational request/start/completion timestamps are strict UTC but excluded
from request/audit semantic identity. The controlled retry one day later reused:

- request `paired-evaluation-request-1b61bf393874a848963f`;
- result `paired-evaluation-result-8f7b2d505b7d92519485`;
- audit `paired-evaluation-audit-c9604d75261bfa81df29`;
- result SHA-256 `59e2f35e429249022b2a4bf9c3810c9b7139147fa41c05cb490fd6bc231a3522`.

The retry skipped recomparison and reproduced the exact 4,161-byte result. The controlled SQLite
database was 888,832 bytes.

## Commands

The store must already contain the exact proposal, CANDIDATE lifecycle, candidate, plan, frozen
candidate configuration, and referenced shared-kernel manifests.

```powershell
$env:PYTHONPATH = (Resolve-Path 'src')
python -m axq.reflection run-paired-evaluation --store runtime/phase8-task9/governance.sqlite3 --request paired-request.json --baseline-development-input baseline-development.json --baseline-validation-input baseline-validation.json --candidate-development-input candidate-development.json --candidate-validation-input candidate-validation.json --result-output runtime/phase8-task9/paired-result.json --started-at 2026-09-11T12:21:00+00:00 --completed-at 2026-09-11T12:22:00+00:00
python -m axq.reflection show-paired-evaluation --store runtime/phase8-task9/governance.sqlite3 --request-id <request-id>
python -m axq.reflection paired-evaluation-summary --store runtime/phase8-task9/governance.sqlite3
```

Supply only the DEVELOPMENT/VALIDATION flags required by the plan. The CLI intentionally exposes no
Final OOS option. This layer does not run replay, tune/search, promote, deploy, mutate runtime, or
contact broker/MT5, and the seven real proposals remain unevaluated.
