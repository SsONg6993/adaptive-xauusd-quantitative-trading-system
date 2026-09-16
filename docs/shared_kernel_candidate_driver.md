# Shared-Kernel Candidate Driver V1

Phase 8 Task 8 evaluates one frozen Master-fusion configuration through the same deterministic
Phase 6/7 replay used for system validation. It is an evidence producer only. It cannot tune,
promote, deploy, mutate production runtime, contact MT5, or access Final OOS.

## Candidate injection boundary

`SharedKernelPolicySet` is the only candidate-aware input to `run_system_replay`. Its default factory
reproduces the previous Fusion, Discipline, Risk, Execution, Position Management, Position Action,
and Scenario composition. `FrozenSharedKernelCandidateConfig` names that exact baseline policy-set
ID and contains one complete replacement `FusionPolicy`. V1 rejects every candidate kind or target
other than `CONFIGURATION / MASTER_FUSION`.

The candidate driver resolves the default set and calls `with_master_fusion`. All tools,
specialists, lifecycle transitions, Master evaluation, Discipline, Risk, execution transport,
position lifecycle, and replay causality continue through the existing shared kernel. No candidate
strategy fork exists.

## Governance and data

The request binds exact persisted proposal/candidate/plan records, canonical candidate-config bytes,
engine version, deterministic seed/environment, and one content-digested CSV manifest for each
required DEVELOPMENT/VALIDATION scope. Each manifest covers exactly `xauusd_m5.csv`,
`xauusd_m15.csv`, `xauusd_h1.csv`, and `xauusd_h4.csv`. Paths and operational timestamps do not
participate in semantic identity.

Final OOS is rejected by the contracts and absent from the CLI. The V1 engine emits only the
preregistered scoped keys from this closed list:

- `master_actionable_rate`
- `discipline_pass_rate`
- `risk_pass_rate`
- `execution_intent_count`
- `completed_trade_count`
- `realized_pnl_usd`
- `max_drawdown_usd`

Keys are prefixed with `development_` or `validation_`. Each canonical series contains the exact
run-level measurement from the shared replay artifact. Task 6 performs the preregistered
aggregation and reports any Final OOS metric only as
`UNAVAILABLE / FINAL_OOS_NOT_ACCESSED`.

## Persistence and retry

Migration 012 stores immutable candidate configs, data manifests, requests, replay-result refs,
canonical metric artifacts, and terminal audits. All tables reject UPDATE and DELETE. A completed
semantic retry revalidates stored output digests and returns identical bytes without invoking the
kernel again. A partial request has no completed audit and remains subject to current CANDIDATE
governance before execution.

## Commands

The SQLite store must already contain the exact CANDIDATE proposal, candidate, and preregistered
plan. The config, request, and manifests must match their persisted semantic references:

```powershell
python -m axq.reflection run-shared-kernel-candidate --store runtime/phase8-task8/shared-kernel.sqlite3 --request shared-kernel-request.json --config frozen-master-fusion-config.json --development-manifest development-data-manifest.json --development-data-dir data/development --validation-manifest validation-data-manifest.json --validation-data-dir data/validation --output-dir runtime/phase8-task8/artifacts --started-at 2026-09-11T12:00:00+00:00 --completed-at 2026-09-11T12:00:01+00:00
python -m axq.reflection show-shared-kernel-candidate --store runtime/phase8-task8/shared-kernel.sqlite3 --request-id <request-id>
python -m axq.reflection shared-kernel-candidate-summary --store runtime/phase8-task8/shared-kernel.sqlite3
```

Run the controlled synthetic fixture and direct Task 6 compatibility checks with:

```powershell
python -m pytest --override-ini=pythonpath=src tests/test_shared_kernel_policy_set.py tests/test_shared_kernel_candidate_contracts.py tests/test_shared_kernel_candidate_engine.py tests/test_shared_kernel_candidate_store.py tests/test_shared_kernel_candidate_service.py tests/test_shared_kernel_candidate_cli.py -v
```

These commands do not execute the seven baseline proposals or use broker data.

## Controlled V1 validation

The deterministic synthetic fixture used 140 M5 rows plus 80 rows for each higher timeframe in
each scope. DEVELOPMENT and VALIDATION each produced one canonical
`master_actionable_rate` sample of `0.12857142857142856`. The two artifacts were 263 and 261 bytes;
the append-only governance database was 835,584 bytes. A later retry with different operational
timestamps reused the same request, audit, artifact IDs, and artifact SHA-256 values while an engine
that would fail if called was not invoked. These fixture measurements prove plumbing and parity,
not candidate quality or profitability.
