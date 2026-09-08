# Repository instructions

This is an independent XAUUSD Multi-Agent Trading System. The repository, Git history, tests,
configuration, and versioned manifests are the source of truth. Do not reuse unrelated previous EA
code.

Python is the intelligence layer. The future MQL5 EA is the broker-facing execution and hard-safety
layer. Core production inference remains local-first; paid LLM and news APIs are optional and must
not be required. Deterministic risk controls have final veto authority.

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
