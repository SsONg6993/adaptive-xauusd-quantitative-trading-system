# Repository instructions

This is an independent XAUUSD Multi-Agent Trading System. The repository, Git history, tests,
configuration, and versioned manifests are the source of truth. Do not reuse unrelated previous EA
code.

The approved post-Phase-5 direction is a tool-augmented agentic system: tools calculate facts,
specialist agents form hypotheses, the Master fuses evidence, the Discipline Guard controls repeated
or impulsive behavior, deterministic risk controls survival, and MT5 executes. Predictive ML is an
optional specialist tool/Challenger, not a mandatory V1 decision dependency.

Python is the intelligence layer. The future MQL5 EA is the broker-facing execution and hard-safety
layer. Core production inference remains local-first; paid LLM and news APIs are optional and must
not be required. Deterministic risk controls have final veto authority.

Live operation and historical replay must share one deterministic decision kernel. Market tools,
agent contracts and state transitions, Master fusion, Discipline Guard, and Risk logic must not be
reimplemented as a simplified backtest strategy. Only clocks, event/data sources, broker/account
adapters, and execution sinks may differ. Shared state includes market snapshots, MT5 account state,
positions, pending orders, exposure, P/L/drawdown, and execution feedback. Completed M5 bars establish
or update primary theses; tick/M1/microstructure events may causally confirm or invalidate an existing
scenario between M5 closes, and replay must support the same event path.

Serious ML/DL training, tuning, large backtests, walk-forward experiments, large indexing, and
GPU-heavy jobs are run locally by the user unless explicitly requested otherwise. Codex should
build pipelines and scripts and use tiny smoke tests by default.

Prevent data leakage at all times. Preserve chronological TRAIN/VALIDATION/OOS boundaries. Never
expose OOS during fitting, feature selection, preprocessing, or calibration. Models start as
CANDIDATE; never promote them automatically. Future learning must be controlled, versioned
retraining—not uncontrolled per-trade online mutation.

Every major phase ends with tests, documentation, a Git checkpoint, and a stop before the next
phase. Before architecture changes, inspect `docs/project_status.md`, the relevant entries in
`docs/decision_log.md`, tests, manifests, recent commits, and Graphify context when present.

Phase 6 now implements the deterministic evidence vertical slice: canonical runtime events and
shared state, clocks and ordered sources, a pure reducer, causal fact tools, specialist evidence and
memory, the M5/intrabar thesis lifecycle, deterministic specialist baselines, `EvidenceKernel`, and
an append-only journal with live-like/replay parity. The shared semantic path is
`RuntimeEvent -> reducer -> tools -> specialists -> scenario lifecycle -> EvidenceBundle`.
Master fusion, Discipline Guard enforcement, agentic Risk integration, broker/simulated execution,
position management, restart recovery, LLM reasoning, reflection, and autonomous evolution are not
implemented. Do not infer those capabilities from their documented future interfaces.

## Repository-start workflow

1. Read `AGENTS.md`.
2. Read `docs/project_status.md`.
3. Read the relevant portion of `docs/decision_log.md`.
4. If `graphify-out/graph.json` exists, query it before broad source reading.
5. Open only the relevant source files for implementation detail.
6. Inspect the latest Git commits and working-tree status.

## Graphify

Graphify 0.9.56 is installed through pipx. Code extraction is local and uses no API key. The Codex
PreToolUse hook is intentionally not installed because this Graphify version documents it as a no-op
in Codex Desktop; this file provides the durable graph-first guidance instead.

Tracked: `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md`. The HTML visualization and
internal Graphify caches are ignored because they are generated, comparatively noisy, and easily
rebuilt.

Use these verified commands from the repository root:

```powershell
graphify query "What code is relevant to this task?" --budget 2000
graphify update .
graphify cluster-only . --no-label
```

For a clean full rebuild:

```powershell
graphify extract . --code-only --out .
graphify cluster-only . --no-label
```

Open a new terminal after the initial pipx setup if `graphify` is not yet on `PATH`.
