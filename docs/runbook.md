# Phase 0-2 runbook

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
