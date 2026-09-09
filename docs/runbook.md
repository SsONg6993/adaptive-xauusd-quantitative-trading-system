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
2. Acquire one fresh broker snapshot through a future adapter. Do not enable entries while any
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

Task 5 does not acquire MT5 snapshots, send orders, backfill candles, or manage positions.

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
