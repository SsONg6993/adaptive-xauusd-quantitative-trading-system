# Phase 0-6 runbook

## Data lifecycle

1. Preserve raw MT5 exports under `data/raw` (ignored by Git).
2. Record broker symbol, terminal/build/package versions, UTC request range, and file SHA-256.
3. Clean into a new file; never mutate raw history.
4. Validate every timeframe and classify gaps as expected closure, broker-history limit, or outage.
5. Synchronize on completed-bar availability.
6. Write a dataset manifest before features/labels are built.
7. Build configured feature groups; retain warm-up NaNs until a later dataset policy handles them.
8. Archive the generated feature manifest with the dataset and verify its manifest ID.
9. Review the tiny-data quality report before any Phase 3 experiment; do not globally impute,
   scale, correlate-select, or clip.

## Operational checks

- Compare first/last returned timestamp with the requested range.
- Inspect MT5's “Max bars in chart” setting if history is truncated.
- Confirm broker point, tick size/value, contract size, volume min/max/step, stop level, and freeze level.
- Do not interpret missing weekend bars as data corruption or forward-fill prices.
- Check UTC continuously; define session rules separately from broker display timezone.
- Keep the live SQLite database on a local VPS disk rather than a sync/network folder; back it up.
- Run only one database writer process in V1 and keep transactions short.

## Recovery principles

Atomic IPC instructions are immutable and expire. Replaying an idempotency key is rejected. On
restart, reconcile instructions, ACKs, broker orders, and positions before enabling new trades. If
Python and MT5 disagree, pause entries while leaving broker-side SL/TP management active.

## Phase 2 lightweight verification

    python -m pytest
    python -m ruff check .
    python -m mypy src/axq
    python data/build_features.py --input data/processed/xauusd_m5_sample.csv --output data/processed/xauusd_m5_features.csv --config configs/base.yaml --quality-report runtime/feature-quality-smoke.json

The build writes xauusd_m5_features.features.json. Inspect its enabled flags, parameters,
lookbacks, dtypes, and causal statuses. Formula parity with the optional TA-Lib wrapper can be run
after installing TA-Lib, but it is not required by the runtime.

## Readiness gates for Phase 3

Before training: review the feature manifest, approve candidate groups, classify source-data gaps,
choose fold-local imputation/scaling policy, and agree label horizons/purging. Phase 2 tests must
remain green, especially future-mutation, prefix-invariance, completed-bar, and swing-delay tests.

## Phase 3 dataset lifecycle

1. Validate source candles and classify reported session/weekend gaps.
2. Synchronize higher timeframes on completed-bar availability.
3. Select a versioned label definition and keep the AMBIGUOUS collision default unless a reviewed
   alternative is explicitly required.
4. Build the immutable dataset with datasets/build_dataset.py.
5. Archive dataset, feature, label, split, and quality manifests together.
6. Inspect row counts, label balance, missingness reasons, purged/embargoed rows, and MFE/MAE.
7. Never fit imputation, scaling, selection, or reduction outside a fold's training range.

    python datasets/build_dataset.py --config configs/datasets/xauusd_m5.yaml
    python datasets/inspect_dataset.py --dataset-manifest datasets/generated/DATASET_ID/dataset.manifest.json

Phase 4 may consume these artifacts only after their IDs and split boundaries are reviewed.

## Phase 4 Quant Agent lifecycle

1. Inspect the dataset, feature, label, and split manifests; never edit an immutable dataset.
2. Install `.[ml]` for scikit-learn baselines. Install XGBoost/LightGBM separately only when needed.
3. Review target, ordered features, preprocessing, selection, weights, calibration, HOLD threshold,
   seed, device, and output path in `configs/quant/`.
4. Train from the dataset artifact. Confirm fit scopes in `run_summary.json`: TRAIN for preprocessing
   and model, VALIDATION for calibration, OOS only for final frozen evaluation.
5. Re-run `training/quant/evaluate.py`; it must reproduce saved OOS metrics without retraining.
6. Smoke one current feature row through `QuantAgent` with matching manifest IDs and UTC timestamp.
7. Review metric breadth, calibration, class distribution, BUY/SELL/HOLD coverage, confidence
   buckets, and return/MFE/MAE diagnostics without interpreting them as profitability.
8. Leave the run as CANDIDATE unless an explicit future Champion/Challenger review is completed.

Generated models, registries, and experiment databases belong under ignored `runtime/`. Never load
untrusted joblib artifacts. If identity/hash/order/freshness validation fails, inference must HOLD at
the orchestration boundary rather than attempting repair. Phase 4 performs no automatic promotion,
threshold optimization, retraining loop, or online learning.

## Phase 5 local model development

1. Run the bounded MT5 history report before requesting a large range.
2. Build one immutable M5/M15/H1/H4 dataset explicitly with `--execute`; review quality and split
   manifests before fitting.
3. Run majority and prior baselines before Logistic Regression, then compare calibration, stability,
   and actionable coverage rather than accuracy alone.
4. Run Random Forest and boosting only after simpler evidence is reviewed. Probe actual device
   support first; package presence alone is not GPU capability.
5. Limit early walk-forward runs to a few folds. Resume reuses only identity-matching completed fold
   outputs. Every learned component is fold-local.
6. Run feature-group ablation only on finalists. Run Optuna last, only with `--execute`, and never
   allow final OOS into its objective.
7. Preserve completed reports for review; no fold model is registered and no Challenger is promoted
   automatically.

Exact commands, compute categories, and output locations are in
[Phase 5 local runs](phase5_local_runs.md).

## Phase 6 deterministic evidence runtime

Use only canonical UTC `RuntimeEvent` objects. Live-like and replay operation must both traverse:

`RuntimeEvent -> reducer -> tools -> specialists -> scenario lifecycle -> EvidenceBundle`

Events order by `(available_at, source_sequence, event_id)`. Only completed M5 events can establish a
primary thesis; completed M1 and tick events may update an existing thesis. Do not treat
`ENTRY_ELIGIBLE` as trade permission. Missing intrabar history must remain explicit through
`ContinuityStatus`, and missing/unknown account or broker values must remain `None` with freshness
status rather than becoming numeric zero.

`SQLiteRuntimeJournal` stores append-only `JournalRecord` rows. UPDATE and DELETE are blocked by
triggers. The journal records runtime events/state, feature snapshots, tool results, agent inputs,
evidence and memory, bundles, thesis/scenario states, and `JournalOutcome` values. Exact duplicates
are journaled as `DUPLICATE` without a second semantic step; no-ops and rejected events are also
recorded. A duplicate event with a different feature snapshot is rejected. Keep journal databases
under ignored `runtime/`; database row sequences are not semantic IDs.

Lightweight verification only:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest --basetemp=.pytest_tmp
& '.\.venv\Scripts\python.exe' -m ruff check .
& '.\.venv\Scripts\python.exe' -m mypy src/axq
& '.\.venv\Scripts\python.exe' -m pip check
git diff --check
graphify query "How do live and replay share the Phase 6 evidence kernel?" --budget 2500
```

Phase 6 has no broker connection or execution sink. Do not use the journal/replay fixture as a P&L
backtest. Master, Discipline, Risk integration, simulated/live execution, and restart recovery are
Phase 7+ work.

## Future restart and reconciliation gate

Before unattended operation, implement graceful shutdown and journal flush, persist the last causal
cursor, reconcile MT5 account/positions/orders and execution feedback at startup, resync open
positions, backfill missing candles, preserve explicit missing-intrabar continuity, enforce thesis
and scenario TTLs, and validate freshness. New entries must remain disabled until reconciliation and
freshness checks pass.

## Phase 7 Task 5 recovery procedure

1. Open `SQLiteExecutionLedger` on the ignored runtime database. Its append-only transitions, not a
   recovery checkpoint, are the execution source of truth.
2. Acquire one fresh broker snapshot through `MT5BrokerSnapshotProvider`. Do not enable entries while any
   critical component is UNKNOWN, UNAVAILABLE, or STALE.
3. Refresh shared state through the canonical market, account, positions, orders, exposure, and
   broker-constraints runtime events.
4. Reconcile using only exact intent/client, ticket, or persisted transport linkage. Do not match by
   approximate price/time/direction/volume.
5. Append the reconciliation report. A follow-up must name the immediately preceding report it
   supersedes; never update an earlier UNKNOWN or CONFLICT row.
6. Require `ResumeStatus.SAFE`. Any unresolved execution anomaly, missing intrabar continuity, or
   expired execution-relevant thesis keeps new entries blocked.
7. On graceful shutdown, append a recovery checkpoint and flush both runtime journal and execution
   ledger. After a crash, replay committed execution transitions even when no checkpoint exists.

Task 5 itself does not send orders, backfill candles, or manage positions; Task 8 supplies the
snapshot adapter without changing Task 5 reconciliation semantics.

## Phase 7 Task 6 position-management evaluation

1. Begin from one authoritative open `PositionState`. If there is no position, record `NO_ACTION`.
2. Require the original `ExecutionIntent` and `ExecutionResult`, an exact persisted
   `BrokerIntentLink`, and a resolved reconciliation finding for that intent and position. Never
   recover linkage from similar price, time, side, or volume.
3. Require Task 5 `ResumeStatus.SAFE`, fresh account/position/broker-constraint state, and complete
   intrabar continuity. UNKNOWN execution or any unresolved broker anomaly records `NO_ACTION`.
4. Bind the position to its existing setup, thesis, and scenario. Do not create a replacement thesis
   or interpret a new Master direction as a position action.
5. ACTIVE or CONFIRMED normally records `HOLD_POSITION`. INVALIDATED or policy-configured EXPIRED
   state may record `EXIT_POSITION`; this is a request, not a broker close.
6. WEAKENING may request `PROTECT_POSITION` only when policy, age, current price, and broker stop/
   freeze constraints allow a monotonic stop move toward break-even. Never widen long or short risk.
7. Append the immutable `PositionManagementOutcome` to the future decision journal chain. Task 6
   contains no transport; a later dedicated safety validation must precede any broker modification.

## Phase 7 Task 7 position-action safety

1. Begin with an immutable `PositionManagementOutcome` and reacquire the latest authoritative
   position/account/broker/reconciliation/readiness facts; do not transport the Task 6 outcome.
2. Evaluate `PositionActionContext` with its exact content-addressed policy. HOLD/NO_ACTION maps to
   safety `NO_ACTION`. Only safety `PASS` may create a `PositionActionIntent`.
3. Treat unsafe recovery, UNKNOWN execution, unresolved anomaly, kill switch, or broken exact
   intent/result/ticket/transport linkage as `EMERGENCY_BLOCK`. Stale/missing or broker-invalid
   action facts produce `REJECT`. Neither result produces an intent.
4. For stop protection, require fresh bid/ask and broker constraints, unchanged current SL, monotonic
   risk reduction, and valid point/tick/stops/freeze distance. Tick normalization may only tighten.
5. For exit, target only the exact-linked still-open broker position and request its full current
   volume. Never express close as an opposing entry, reversal, partial close, or scale action.
6. Append the management outcome, safety outcome, and optional passed intent with
   `append_position_action_chain`. Equivalent retries recover the existing journal entries rather
   than append a second semantic action. Keep the journal under ignored `runtime/`.
7. Stop at the semantic intent. Task 8 transport is a separate boundary and must independently
   repeat exact-ticket and broker-fact validation.

## Phase 8 Task 1 experience reconstruction

From an activated environment with the worktree installed, run the corrected one-month replay into
a new ignored output directory:

```powershell
python -m axq.replay_validation run --data-dir data/raw/mt5/xauusd-six-months --output-dir runtime/phase8-task1/baseline --months 1
```

Build the append-only store with the expected-trade gate, then display counts and descriptive
metrics:

```powershell
python -m axq.experience build-experiences --runtime-journal runtime/phase8-task1/baseline/runtime.sqlite3 --execution-ledger runtime/phase8-task1/baseline/execution.sqlite3 --position-action-ledger runtime/phase8-task1/baseline/position-actions.sqlite3 --replay-outcomes runtime/phase8-task1/baseline/replay-outcomes.json --store runtime/phase8-task1/baseline/experiences.sqlite3 --expected-trades 166
python -m axq.experience summary --store runtime/phase8-task1/baseline/experiences.sqlite3
python -m axq.experience show-experiences --store runtime/phase8-task1/baseline/experiences.sqlite3 --type TRADE --limit 5
```

Use a new output directory for a new source run. Do not delete or update experience rows. Identical
rebuild inserts are idempotent; a same-ID content conflict fails closed. The expected count is a
baseline validation guard, not production trading logic. Task 1 does not generate Reflection,
counterfactual outcomes, proposals, scores, or policy changes.

## Phase 8 Task 2 deterministic daily reflection

Build the corrected one-month UTC range from the immutable Experience Store, then immediately show
the concise aggregate report and one authoritative daily JSON record:

```powershell
python -m axq.reflection build-daily-reflections --experience-store runtime/phase8-task1/baseline-c/experiences.sqlite3 --reflection-store runtime/phase8-task2/daily-reflections.sqlite3 --start-date 2026-08-10 --through-date 2026-09-08
python -m axq.reflection report --store runtime/phase8-task2/daily-reflections.sqlite3
python -m axq.reflection show-daily-reflection --store runtime/phase8-task2/daily-reflections.sqlite3 --date 2026-08-10
```

The range is inclusive and each reflection selects inputs by `available_at` in `[00:00Z, next
00:00Z)`. Use `--policy path/to/policy.json` to load a reviewed versioned diagnostic policy.
Identical reruns reuse existing semantic IDs. If same-day source content changes, the new immutable
record explicitly supersedes the latest stored record; prior records are never updated or deleted.
The SQLite artifact belongs under ignored `runtime/`. Findings and guards are observations, not
trading instructions, and this command has no path to mutate runtime policy.

## Phase 8 Task 3 deterministic weekly reflection

Build ISO-week reflections from the immutable daily-reflection and Experience stores, then display
the aggregate summary and one authoritative weekly JSON record:

```powershell
python -m axq.reflection build-weekly-reflections --experience-store runtime/phase8-task1/baseline-c/experiences.sqlite3 --daily-store runtime/phase8-task2/daily-reflections.sqlite3 --weekly-store runtime/phase8-task3/weekly-reflections.sqlite3 --daily-policy-id reflection-policy-7b50a68850d575afb986 --start-week 2026-08-10 --through-week 2026-09-07
python -m axq.reflection weekly-summary --store runtime/phase8-task3/weekly-reflections.sqlite3
python -m axq.reflection show-weekly-reflection --store runtime/phase8-task3/weekly-reflections.sqlite3 --week-start 2026-08-10
```

Weeks use `[Monday 00:00Z, following Monday 00:00Z)`. Incomplete weeks remain immutable and emit an
exact `WEEK_COMPLETENESS` guard listing present and missing daily periods; they generate no patterns.
All generated success and failure patterns start as `OBSERVATION`. Rebuilding identical inputs is
idempotent. Changed source content creates a superseding weekly reflection rather than modifying the
earlier record.

Only an explicit reviewed operator or evaluation action may advance or terminate pattern status:

```powershell
python -m axq.reflection transition-pattern --store runtime/phase8-task3/weekly-reflections.sqlite3 --pattern-id <pattern-id> --pattern-key <pattern-key> --from-status OBSERVATION --to-status HYPOTHESIS --effective-at 2026-09-14T00:00:00Z --action-kind OPERATOR --actor-id <operator-id> --action-id <review-id> --reason-code <reason-code>
python -m axq.reflection show-pattern-history --store runtime/phase8-task3/weekly-reflections.sqlite3 --pattern-key <pattern-key>
```

Transitions are append-only and fail closed unless they extend the exact current lifecycle chain.
Weekly reflection and pattern status remain descriptive; neither command tunes or mutates trading
runtime behavior.

## Phase 8 Task 4 advisory improvement proposals

Build proposals from the unchanged exact Experience/Daily/Weekly stores, then show the summary and
one canonical proposal:

```powershell
python -m axq.reflection build-improvement-proposals --experience-store runtime/phase8-task1/baseline-c/experiences.sqlite3 --daily-store runtime/phase8-task2/daily-reflections.sqlite3 --weekly-store runtime/phase8-task3/weekly-reflections.sqlite3 --proposal-store runtime/phase8-task4/improvement-proposals.sqlite3
python -m axq.reflection proposal-summary --store runtime/phase8-task4/improvement-proposals.sqlite3
python -m axq.reflection show-improvement-proposal --store runtime/phase8-task4/improvement-proposals.sqlite3 --proposal-id <proposal-id>
```

Only recurring pattern keys with at least two complete weeks and passed required guards produce a
proposal. Identical builds reuse IDs. Changed evidence appends a proposal that explicitly
supersedes the latest record with the same proposal key.

Lifecycle changes require explicit reviewed action and remain advisory:

```powershell
python -m axq.reflection transition-proposal --store runtime/phase8-task4/improvement-proposals.sqlite3 --proposal-id <proposal-id> --proposal-key <proposal-key> --from-status OBSERVATION --to-status HYPOTHESIS --effective-at 2026-09-14T00:00:00Z --action-kind OPERATOR --actor-id <operator-id> --action-id <review-id> --reason-code <reason-code>
python -m axq.reflection show-proposal-history --store runtime/phase8-task4/improvement-proposals.sqlite3 --proposal-id <proposal-id>
```

`VALIDATED` never means deployed. These commands cannot write trading configuration, register a
model, run a replay/challenger, or alter the shared runtime.

## Phase 8 Task 5 proposal evaluation registration and evidence

First explicitly move a reviewed proposal through its existing append-only lifecycle to
`CANDIDATE`. Task 5 will reject every other status. Then use reviewed JSON inputs:

```powershell
python -m axq.reflection register-evaluation-candidate --store runtime/phase8-task5/evaluations.sqlite3 --input candidate.json
python -m axq.reflection build-evaluation-plan --store runtime/phase8-task5/evaluations.sqlite3 --input plan.json
python -m axq.reflection record-evaluation-result --store runtime/phase8-task5/evaluations.sqlite3 --input result-evidence.json
python -m axq.reflection record-operator-evaluation-decision --store runtime/phase8-task5/evaluations.sqlite3 --input operator-decision.json
python -m axq.reflection evaluation-summary --store runtime/phase8-task5/evaluations.sqlite3
```

The evaluation store must be the same SQLite database that contains the source proposal and its
transition history. A plan must exist before evidence is accepted. Result JSON supplies observations
but cannot supply criteria; those are evaluated from the stored plan. Final OOS metrics and criteria
must be reporting-only and never affect the aggregate evidence outcome.

Inspect exact records and decision history:

```powershell
python -m axq.reflection show-evaluation-plan --store runtime/phase8-task5/evaluations.sqlite3 --plan-id <plan-id>
python -m axq.reflection show-evaluation-result --store runtime/phase8-task5/evaluations.sqlite3 --result-id <result-id>
python -m axq.reflection show-operator-evaluation-history --store runtime/phase8-task5/evaluations.sqlite3 --result-id <result-id>
```

Corrections never overwrite. Revised plans name the latest `supersedes_plan_id`; corrected evidence
for one run names `supersedes_result_id`; later operator decisions name `previous_decision_id`.
`ACCEPT_EVIDENCE`, `REJECT_EVIDENCE`, and `DEFER` are audit facts only. None promotes the proposal,
deploys a candidate, executes replay/challenger work, tunes policy, or mutates runtime behavior.

## Phase 8 Task 6 deterministic evaluation execution

Execute only a previously persisted exact plan/candidate using reviewed canonical metric-sample
artifacts. The CLI intentionally has no Final OOS input option:

```powershell
python -m axq.reflection run-evaluation-execution --store runtime/phase8-task6/evaluations.sqlite3 --request execution-request.json --development-input development-samples.json --validation-input validation-samples.json --result-output runtime/phase8-task6/result.json --started-at 2026-09-11T12:00:00Z --completed-at 2026-09-11T12:00:01Z
python -m axq.reflection show-evaluation-execution --store runtime/phase8-task6/evaluations.sqlite3 --request-id <request-id>
python -m axq.reflection evaluation-execution-summary --store runtime/phase8-task6/evaluations.sqlite3
```

Supply only the DEVELOPMENT/VALIDATION inputs required by the stored plan. Their semantic IDs and
canonical-byte SHA-256 digests must exactly match the request. Every preregistered Final OOS metric
is emitted as `UNAVAILABLE` with `FINAL_OOS_NOT_ACCESSED`; no Final OOS artifact is opened.
Completed equivalent retries reuse the same request/result/audit identities and result bytes even
when operational request/start/completion timestamps differ. This adapter neither tunes nor runs a
candidate and has no proposal-promotion, deployment, runtime, or broker authority. See
`docs/evaluation_execution.md`.

## Phase 8 Task 7 governed candidate replay

Generate Task 6-compatible canonical metric samples from one exact controlled fixture. The shared
store must already contain the exact CANDIDATE proposal, candidate spec, and evaluation plan:

```powershell
python -m axq.reflection run-candidate-replay --store runtime/phase8-task7/candidate-replay.sqlite3 --request candidate-replay-request.json --development-input development-replay-fixture.json --validation-input validation-replay-fixture.json --output-dir runtime/phase8-task7/artifacts --started-at 2026-09-11T12:00:00Z --completed-at 2026-09-11T12:00:01Z
python -m axq.reflection show-candidate-replay --store runtime/phase8-task7/candidate-replay.sqlite3 --request-id <request-id>
python -m axq.reflection candidate-replay-summary --store runtime/phase8-task7/candidate-replay.sqlite3
```

Supply only scopes required by the plan. Each fixture must reproduce the exact proposal/candidate/
plan linkage and every preregistered metric key for its scope. The engine emits canonical sample
files without aggregation; Task 6 consumes those files and owns result construction. Equivalent
completed retries reuse stored artifact bytes and do not run the engine again.

The command has no Final OOS argument. It cannot tune parameters, launch arbitrary code, promote a
proposal, deploy, mutate runtime, contact a broker, or execute the seven baseline proposals. See
`docs/candidate_replay_evaluation.md`.


## Phase 7 Task 8 direct MT5 demo transport

1. Keep the execution policy `DISABLED` unless an operator has deliberately selected `DRY_RUN` or
   `DEMO_ENABLED`. Task 8 has no live-money mode.
2. Configure one explicit `MT5SymbolMapping`, for example canonical `XAUUSD` to the exact Market
   Watch symbol. Never auto-discover a suffix or substitute `GOLD` heuristically.
3. Use `MetaTrader5Gateway` only on the local Windows host with the intended terminal already logged
   in. `MT5BrokerSnapshotProvider.capture()` is read-only and feeds Task 5 through
   `broker_snapshot_runtime_events`.
4. Run `DRY_RUN` first. It connects, validates account/symbol/tick/volume/stop or exact position,
   and calls `order_check`; it must not call `order_send` or any position-changing operation.
5. `DEMO_ENABLED` must re-read the account and submission facts immediately before mutation. A
   passing `order_check` is not acceptance; preserve the authoritative `order_send` retcode/result.
6. Never retry an entry, stop change, or close whose result is `UNKNOWN`. Inspect the append-only
   entry or position-action ledger, take a fresh snapshot, and append explicit reconciliation before
   considering later action.
7. For position actions, require the exact broker ticket and unchanged side, volume, and current SL.
   Close is full-volume against that ticket, never a free opposing order. Stop modification preserves
   broker TP and must remain monotonic.
8. Runtime artifacts and SQLite files remain under ignored `runtime/`. Task 9 now owns coordinated
   flush/checkpoint/close behavior; Task 8 itself remains only the broker edge.

## Phase 7 Task 9 runtime lifecycle

1. Review `configs/runtime/demo.yaml`; leave `mode: DISABLED` until the exact symbol, policies, and
   local paths are reviewed. Supply an MT5 terminal path only as environment-specific operational
   configuration. Never store credentials in YAML.
2. Construct the established EvidenceKernel/runner and decision-cycle processor, then inject the
   runtime journal, execution ledger, position-action ledger, and the appropriate source/clock.
3. Call `startup()`. In SHADOW/DEMO, do not accept decisions unless status reaches `SAFE` after
   snapshot reduction, exact reconciliation, continuity/expiry checks, and ResumeReadiness.
4. Use SHADOW before DEMO. Shadow journals the complete semantic would-act path but never invokes
   entry or position-action adapters.
5. In DEMO, every mutation causes another broker snapshot/reconciliation/readiness evaluation first.
   UNKNOWN results block further autonomy and are never retried.
6. A pause blocks new entries while allowing existing-position safety actions. Execution-disable or
   kill switch blocks every mutation and cannot bypass Risk/readiness.
7. Call `shutdown()` before planned host shutdown. It appends a recovery checkpoint, flushes all
   three stores, and closes MT5. On crash restart, committed append-only history remains sufficient;
   the checkpoint is only an anchor.

See `docs/runtime_orchestration.md` for mode and sequence contracts. No checked-in command enables
live money, and Task 9 does not add an unbounded polling daemon.
