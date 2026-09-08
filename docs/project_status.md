# Project status

Last updated: 2026-09-09

## Current phase status

| Phase | Scope | Status |
|---|---|---|
| 0 | Architecture | COMPLETE |
| 1 | Market Data | COMPLETE |
| 2 | Feature Engine | COMPLETE |
| 3 | Dataset + Labels | COMPLETE |
| 4 | Quant Agent Framework | COMPLETE |
| 5 | Local Quant Model Development | COMPLETE (framework only) |
| 6+ | Later roadmap | NOT STARTED |

Phases 0–4 established the local-first contracts, UTC market-data pipeline, causal versioned feature
engine, immutable leakage-safe datasets/labels/splits, and manifest-bound Quant Agent training,
evaluation, inference, artifact, explanation, experiment-tracking, and lifecycle-registry contracts.

Phase 5 adds a separate local Quant development layer: bounded broker-history and compute inspection,
strict model/suite/walk-forward/ablation/tuning configs, content-addressed and resumable orchestration,
fold-local evaluation, machine-readable reports, calibration/HOLD/stability/trade-frequency/drift
diagnostics, advisory Challenger evidence, and completed-run comparison. Serious experiments remain
user-run work and no model was promoted.

## Verified state

- Stable Phase 4 checkpoint: `32132dd103087778fda88c1facf4159894aca653`.
- Persistent-context checkpoint and Phase 5 base: `bf896ff03d98a405c532c1b8e5bd65e8e9a6725e`.
- Phase 5 work is isolated on `codex/phase-5-quant-development`; see its final task report for fresh
  pytest, Ruff, mypy, `pip check`, dry-run, device, and Graphify evidence.
- Prior tiny real-data smoke only: 96 XAUUSD M5 rows, 52 TRAIN, 14 VALIDATION, 20 OOS, CPU Logistic
  Regression with sigmoid calibration and 60% actionable coverage.
- Serious model training has **not** been performed. Smoke metrics are pipeline diagnostics and are
  not profitability evidence.

## Current architecture

MT5 supplies UTC market data to Python ingestion, validation, immutable datasets, causal features,
labels, and local model inference. Phase 5 development tooling remains outside the Phase 4 production
trainer and cannot use immutable final OOS for model development. Future agents produce advisory
`BUY`/`SELL`/`HOLD`; deterministic Python risk and the future MQL5 EA retain veto authority.

## Important risks

- The prior real sample is tiny, class-imbalanced, and its OOS results have already been viewed.
- XGBoost, LightGBM, real CUDA/OpenCL training, large ablations, and full walk-forward results remain
  unvalidated until the user runs the documented local workflow.
- Joblib artifacts are trusted-local only; hashes detect corruption but do not sandbox pickle.
- Registry and suite-state files are not designed for concurrent writers to the same run directory.
- Broker history depth, data gaps, spread anomalies, and multi-year regime coverage remain broker-specific.
- No claim of profitability, execution-ready trading, or autonomous learning exists.

## Working principle and next task

Codex writes auditable local pipelines and runs tiny tests. The user runs serious training and returns
completed reports for analysis. The next task must be chosen only after reviewing real Phase 5 Quant
evidence. A possible Phase 6 is a separate Chart Agent framework, but its causal data representation,
model contract, and compute limits require explicit design approval. Do not start it implicitly.

## Roadmap

1. Phase 0 — Architecture
2. Phase 1 — Market Data
3. Phase 2 — Feature Engine
4. Phase 3 — Dataset + Labels
5. Phase 4 — Quant Agent Framework
6. Phase 5 — Local Quant Model Development and Evaluation
7. Phase 6+ — Remaining agents and execution roadmap, to be re-approved before implementation
