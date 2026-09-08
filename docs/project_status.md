# Project status

Last updated: 2026-09-08

## Current phase status

| Phase | Scope | Status |
|---|---|---|
| 0 | Architecture | COMPLETE |
| 1 | Market Data | COMPLETE |
| 2 | Feature Engine | COMPLETE |
| 3 | Dataset + Labels | COMPLETE |
| 4 | Quant Agent Framework | COMPLETE |
| 5+ | Later roadmap | NOT STARTED |

Phase 0 established the independent repository, strict contracts, local-first architecture,
persistence boundaries, and deterministic risk foundation. Phase 1 added bounded MT5 ingestion,
UTC cleaning/validation, and completed-bar multi-timeframe synchronization. Phase 2 delivered the
causal feature engine, manifests, warm-up/missing policies, DST sessions, analysis tools, and
leakage tests. Phase 3 added versioned labels, immutable datasets, chronological purge/embargo
splits, quality reports, and dataset/feature/label/split manifests. Phase 4 added the Quant Agent's
config-driven baselines, train-only preprocessing/selection, validation-only calibration, frozen
OOS evaluation, HOLD policy, explanations, hashed artifacts, inference, experiment tracking, and
explicit model lifecycle registry.

## Verified state

- Latest Phase checkpoint: `32132dd103087778fda88c1facf4159894aca653` — Complete Phase 4 Quant
  Agent training and inference framework.
- Tests at that checkpoint: 59 passed; Ruff, strict mypy, `pip check`, and `git diff --check` passed.
- Tiny real-data smoke only: 96 XAUUSD M5 rows, 52 TRAIN, 14 VALIDATION, 20 OOS, CPU Logistic
  Regression with sigmoid calibration and 60% actionable coverage.
- Serious model training has **not** been performed. Smoke metrics are pipeline diagnostics and are
  not profitability evidence.

## Current architecture

MT5 supplies UTC market data to Python ingestion, validation, immutable datasets, causal features,
labels, and local model inference. Agents will produce advisory `BUY`/`SELL`/`HOLD` messages. The
future master combines evidence, deterministic Python risk retains final veto, and an MQL5 EA will
independently revalidate and execute broker-facing instructions. Failures block new positions.

## Important risks

- The real Phase 4 sample is tiny, class-imbalanced, and its OOS results have already been viewed.
- XGBoost, LightGBM, CUDA, large ablations, and walk-forward evaluation remain unvalidated.
- Joblib artifacts are trusted-local only; hashes detect corruption but do not sandbox pickle.
- Registry files are not designed for concurrent writers.
- No claim of profitability, production readiness for live execution, or autonomous learning exists.

## Working principle and next task

Codex writes auditable local pipelines and runs tiny tests. The user runs serious training and
compute-heavy work locally after review. The next recommended task is Phase 5: define the Chart
Agent framework and reconcile its reviewed model-development responsibilities with the existing
Quant Agent boundary before implementation. Do not start it implicitly.

## Roadmap

1. Phase 0 — Architecture
2. Phase 1 — Market Data
3. Phase 2 — Feature Engine
4. Phase 3 — Dataset + Labels
5. Phase 4 — Quant Agent Framework
6. Phase 5 — Chart Agent Framework / reviewed model-development scope under the current architecture
7. Phase 6 — Historical Similarity
8. Phase 7 — Market Regime
9. Phase 8 — News/Macro
10. Phase 9 — Master Decision Engine
11. Phase 10 — Risk Manager
12. Phase 11 — MQL5 Execution EA
13. Phase 12 — Backtest / Walk-forward
14. Phase 13 — Paper Trading
15. Phase 14 — VPS Deployment
16. Phase 15 — Optional LLM-enhanced News
