# Project status

Last updated: 2026-09-10

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
| 7 | Master, Discipline, Risk, execution, recovery, position actions, replay validation | COMPLETE |
| 8 | Controlled learning and attribution | IN PROGRESS — TASK 1 COMPLETE |
| 9+ | Optional intelligence | NOT STARTED |

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

Phase 8 Task 1 adds strict normalized experience contracts, exact-ID outcome attribution, a
content-addressed replay-outcome artifact, and an append-only SQLite Experience Store. Its first
corrected one-month baseline contains 37,183 complete experiences, including 166 completed trades;
it performs descriptive analytics only and cannot reflect, propose, tune, or mutate policy.

## Verified state

- Stable Phase 4 checkpoint: `32132dd103087778fda88c1facf4159894aca653`.
- Persistent-context checkpoint and Phase 5 base: `bf896ff03d98a405c532c1b8e5bd65e8e9a6725e`.
- Phase 5 branch checkpoint: `3e7620c12b46efd476370c03b2a639111744a218`.
- Phase 5 merge checkpoint: `9e15b750da98a484e013dea8552995d7127df428`.
- Phase 7 replay-validation and Phase 8 base: `512feefefe21f6fd2bfecd8a652bd987e795e57d`.
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
live-like and replay identically. The Phase 7 Master, Discipline, and Risk boundaries preserve this
shared-kernel rule; future execution integration must do the same.

Completed M5 bars establish or update primary theses. The implemented intrabar path consumes
causally available ticks and M1 closes to confirm or invalidate an existing
scenario and make it entry-eligible before the next M5 close. Entry eligibility never bypasses
setup/thesis identity and is evidence only; it cannot authorize or execute a trade.

The runtime journal records immutable events, states, feature/tool/agent artifacts, bundles,
thesis/scenario states, and applied/duplicate/no-op/rejected outcomes. `JournalEventSource` rebuilds
causal event order and parity tests require identical semantic traces. Database row sequences are
storage order only and are excluded from content identity.

Phase 7 Task 1 adds a pure, versioned Master evidence-fusion boundary. `FusionPolicy` deterministically
weights eligible specialist evidence and applies separate score, confidence, uncertainty,
within-agent contradiction, and cross-agent disagreement gates. `MasterProposal` is advisory and
content-addressed; failed gates produce `HOLD`.

Phase 7 Task 2 adds a pure, versioned Discipline Guard downstream of `MasterProposal`. It emits a
content-addressed `PASS`, `REJECT`, `PAUSE`, or `NO_ACTION` outcome from explicit policy, causal
discipline state, and stable setup/thesis context. It enforces duplicate, re-entry, position-count,
trade-cap, cooldown, and consecutive-loss cadence rules without performing financial Risk, sizing,
or execution. Only `PASS` is eligible for the downstream Risk boundary.

Phase 7 Task 3 adds a pure, versioned financial Risk boundary. Only a Discipline `PASS` is evaluated.
The boundary consumes bounded causal account, market, position/order-book, exposure, broker, stop,
margin, slippage, and normalized drawdown facts. It reuses the validated broker-specification sizing
primitive and emits a content-addressed `PASS`, `REJECT`, `NO_ACTION`, or `EMERGENCY_STOP` outcome.
Only Risk `PASS` is eligible for execution; Risk itself does not create or submit an order.

Phase 7 Task 4 adds a strict, versioned execution boundary. A pure builder carries only a linked
Risk `PASS` into a content-addressed `ExecutionIntent`; disabled and dry-run modes never call a
transport, and the demo-only adapter rejects live accounts and changed pre-submit conditions. The
idempotency ledger reserves an intent before submission, and `UNKNOWN` explicitly blocks retry until
future broker reconciliation. Typed execution results reuse the Phase 6 execution-feedback event and
reducer path. No direct MT5/MQL5 sender, durable reconciliation store, simulated broker, or position
management has been implemented.

Phase 7 Task 5 adds append-only SQLite execution transitions, deterministic exact-linkage broker
reconciliation, canonical broker-state refresh events, recovery checkpoints, and a separate
fail-closed safe-resume gate. Reservations and results survive process restart; terminal and UNKNOWN
intents cannot be resubmitted. Reconciliation resolutions append a new report that supersedes the
prior report. Checkpoints are recovery anchors only—the transition history remains authoritative.
Freshness, unresolved exposure anomalies, missing intrabar continuity, and expired theses block new
entries. Actual MT5/MQL5 transport and startup data acquisition remain unimplemented.

Phase 7 Task 6 adds a pure deterministic core for already-open positions. Strict policy, context,
and outcome contracts preserve original execution/setup/thesis/scenario provenance and require
fresh, exactly reconciled Task 5 state before management. Stable theses hold; configured terminal
lifecycle states request exit; and weakening may request only monotonic broker-valid protection
toward break-even. Outputs remain journal-ready requests without transport, reversal, scale-in/out,
or mutation of Master, Discipline, Risk, Execution, runtime, or thesis state.

Phase 7 Task 7 adds a separate deterministic action-time safety boundary downstream of position
management. Strict policy/context/outcome/intent contracts recheck Task 5 safe readiness, resolved
reconciliation, exact intent/result/position linkage, current ticket/symbol/side/volume, component
freshness, and action-time broker facts. HOLD creates no intent; only safety `PASS` creates a
content-addressed protective-stop modification or full-close intent. Management, safety, and intent
are recoverable through idempotent append-only runtime-journal records. No broker call is made.

Phase 7 Task 8 adds a narrow lazy-loaded `MT5Gateway`, direct MetaTrader5 Python demo adapters, and a
read-only `MT5BrokerSnapshotProvider`. Entry reuses the existing execution boundary and durable
ledger. Protective-stop and full-close actions use a dedicated append-only transport result/ledger
path. `DISABLED` is zero-touch, `DRY_RUN` performs complete preflight plus `order_check` without
mutation, and `DEMO_ENABLED` revalidates a demo account and broker facts immediately before
`order_send`. Missing or uncertain acknowledgements are durably `UNKNOWN` and never automatically
resent. No live-money mode, runtime loop, MQL5 EA, IPC bridge, or simulated broker is included.

Phase 7 Task 9 adds `RuntimeOrchestrator`, a strict operational config, structured status/operator
gates, and deterministic run summaries. Startup restores committed state/cursors/memory/thesis,
then live-like modes acquire and reduce broker truth, reconcile exact execution linkage, and require
SAFE readiness before processing. Replay, shadow, and demo use one decision-cycle port; only DEMO
may dispatch through the existing Task 8 adapters, with a fresh readiness check before every
mutation. Feedback returns through canonical runtime events. Graceful shutdown checkpoints and
flushes all append-only stores before closing MT5. There remains no live-money mode.

Phase 8 Task 1 reconstructs `DecisionExperience`, `TradeExperience`,
`RejectedDecisionExperience`, `PositionManagementExperience`, `RuntimeAnomalyExperience`, and
`AgentContributionExperience` from existing Phase 7 records. Attribution uses exact semantic IDs;
missing links remain explicit rather than inferred. The experience store rejects UPDATE/DELETE,
idempotently accepts identical content, and fails closed on conflicting content under one ID.
Counterfactual records are a separate `simulated=true` contract and are not generated in Task 1.

## Important risks

- The prior real sample is tiny, class-imbalanced, and its OOS results have already been viewed.
- XGBoost, LightGBM, real CUDA/OpenCL training, large ablations, and full walk-forward results remain
  unvalidated until the user runs the documented local workflow.
- Joblib artifacts are trusted-local only; hashes detect corruption but do not sandbox pickle.
- Registry and suite-state files are not designed for concurrent writers to the same run directory.
- Broker history depth, data gaps, spread anomalies, and multi-year regime coverage remain broker-specific.
- No claim of profitability, live-money readiness, reflection, or autonomous learning exists.
- Tick-history quality, broker event ordering, spread/slippage simulation, and deterministic replay
  of asynchronous slow-path context remain unresolved implementation risks.
- Real-terminal demo mutation has not been exercised by automated validation; fake-gateway tests
  cover transport behavior without placing trades.
- A production scheduler/service host, simulated fills/P&L, MQL5/IPC transport, automated resolution
  of unknown broker outcomes, LLMs, vision, and reflection are absent.

## Working principle and next task

Codex writes auditable local pipelines and runs bounded validation. The user runs serious training
and large replays. Phase 8 Task 1 is isolated on `codex/phase-8-reflection-experience`; it stops at
deterministic attribution and descriptive analytics. Task 2 has not begun.
Future work must preserve the shared live/replay contracts and may not infer authority for
continuous execution, live-money support, simulated brokerage, or later-phase intelligence.

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
