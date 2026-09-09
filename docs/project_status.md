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
| Architecture migration | Tool-augmented agentic design + deterministic replay | APPROVED / DOCUMENTED |
| 6 | Shared runtime state, agent contracts, deterministic kernel vertical slice | COMPLETE |
| 7+ | Master, Discipline, execution, reflection, optional intelligence | NOT STARTED |

Phases 0–4 established the local-first contracts, UTC market-data pipeline, causal versioned feature
engine, immutable leakage-safe datasets/labels/splits, and manifest-bound Quant Agent training,
evaluation, inference, artifact, explanation, experiment-tracking, and lifecycle-registry contracts.

Phase 5 adds a separate local Quant development layer: bounded broker-history and compute inspection,
strict model/suite/walk-forward/ablation/tuning configs, content-addressed and resumable orchestration,
fold-local evaluation, machine-readable reports, calibration/HOLD/stability/trade-frequency/drift
diagnostics, advisory Challenger evidence, and completed-run comparison. Serious experiments remain
user-run work and no model was promoted.

Phase 6 implements the non-predictive-ML-required evidence baseline. Canonical events reduce into
immutable shared state; fact-only tools feed stateful specialists; an M5-created thesis can receive
causal tick/M1 confirmation or invalidation; and `EvidenceKernel` emits a deterministic
`EvidenceBundle`. Live-like and replay adapters use this same semantic path. Existing ML remains
intact as an optional specialist tool/Challenger and cannot become mandatory or self-promoting.

## Verified state

- Stable Phase 4 checkpoint: `32132dd103087778fda88c1facf4159894aca653`.
- Persistent-context checkpoint and Phase 5 base: `bf896ff03d98a405c532c1b8e5bd65e8e9a6725e`.
- Phase 5 branch checkpoint: `3e7620c12b46efd476370c03b2a639111744a218`.
- Phase 5 merge checkpoint: `9e15b750da98a484e013dea8552995d7127df428`.
- Prior tiny real-data smoke only: 96 XAUUSD M5 rows, 52 TRAIN, 14 VALIDATION, 20 OOS, CPU Logistic
  Regression with sigmoid calibration and 60% actionable coverage.
- Serious model training has **not** been performed. Smoke metrics are pipeline diagnostics and are
  not profitability evidence.

## Current architecture

MT5 supplies UTC market data to Python ingestion, validation, immutable datasets, causal features,
labels, and optional local model inference. Phase 6 adds versioned shared runtime state and one
deterministic evidence kernel above live-like/replay adapters. State includes market data
plus MT5 balance, equity, margin, P/L, drawdown, positions, pending orders, exposure, and execution
feedback. The implemented reducer, tools, specialists, scenario lifecycle, and evidence bundle serve
live-like and replay identically. Future Master, Discipline, Risk, and execution integrations must
preserve this shared-kernel rule.

Completed M5 bars establish or update primary theses. The implemented intrabar path consumes
causally available ticks and M1 closes to confirm or invalidate an existing
scenario and make it entry-eligible before the next M5 close. Entry eligibility never bypasses
setup/thesis identity and is evidence only; it cannot authorize or execute a trade.

The runtime journal records immutable events, states, feature/tool/agent artifacts, bundles,
thesis/scenario states, and applied/duplicate/no-op/rejected outcomes. `JournalEventSource` rebuilds
causal event order and parity tests require identical semantic traces. Database row sequences are
storage order only and are excluded from content identity.

## Important risks

- The prior real sample is tiny, class-imbalanced, and its OOS results have already been viewed.
- XGBoost, LightGBM, real CUDA/OpenCL training, large ablations, and full walk-forward results remain
  unvalidated until the user runs the documented local workflow.
- Joblib artifacts are trusted-local only; hashes detect corruption but do not sandbox pickle.
- Registry and suite-state files are not designed for concurrent writers to the same run directory.
- Broker history depth, data gaps, spread anomalies, and multi-year regime coverage remain broker-specific.
- No claim of profitability, execution-ready trading, or autonomous learning exists.
- Tick-history quality, broker event ordering, spread/slippage simulation, and deterministic replay
  of asynchronous slow-path context remain unresolved implementation risks.
- Master fusion, Discipline Guard enforcement, agentic Risk integration, MT5 execution, position
  management, simulated fills/P&L, reconciliation/restart, LLMs, vision, and reflection are absent.

## Working principle and next task

Codex writes auditable local pipelines and runs tiny tests. The user runs serious training and large
replays. Phase 6 is closed at evidence generation. The recommended first Phase 7 task is a design-and-
contract slice for deterministic Master fusion that consumes `EvidenceBundle` and emits an auditable
BUY/SELL/HOLD proposal without Discipline, Risk, sizing, or execution. Do not implement it without
explicit Phase 7 approval.

## Roadmap

1. Phase 0 — Architecture
2. Phase 1 — Market Data
3. Phase 2 — Feature Engine
4. Phase 3 — Dataset + Labels
5. Phase 4 — Quant Agent Framework
6. Phase 5 — Local Quant Model Development and Evaluation
7. Architecture migration — Tool-augmented shared deterministic kernel (documented)
8. Phase 6 — Runtime state, event/replay contracts, specialist evidence, kernel vertical slice
9. Phase 7 — Master fusion, Discipline Guard, Risk and MT5 execution integration
10. Phase 8 — Reflection, attribution, rejected-opportunity and reliability analysis
11. Phase 9 — Optional LLM, vision, ML challengers and advanced similarity
