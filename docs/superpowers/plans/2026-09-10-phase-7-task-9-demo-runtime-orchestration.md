# Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compose the completed Phase 6/7 boundaries into one deterministic, restart-safe,
non-live-money runtime service for disabled, replay, shadow, and demo operation.

**Architecture:** A narrow orchestrator owns ordering, startup recovery, readiness, journaling,
feedback routing, bounded refresh, operator gates, and shutdown. Existing pure components remain
behind injected typed ports; live-like and replay invoke the same decision-cycle port and only their
clock, source, snapshot provider, and execution adapters differ.

**Tech Stack:** Python 3.12, Pydantic 2, SQLite WAL, existing AXQ runtime and Phase 7 contracts,
pytest, Ruff, mypy.

**Spec:** User-approved Phase 7 Task 9 specification attached on 2026-09-10.

## Global Constraints

- Work only in `.worktrees/phase-7-decision-execution` at `bf07e4c6`.
- No new trading, agent, indicator, risk, broker, or position-management semantics.
- No live-money mode, MQL5/IPC, slow path, Phase 8, training, commit, push, or merge.
- Unknown broker operations are durable and never automatically retried.
- Broker state is authoritative at startup; unsafe reconciliation blocks autonomous mutation.
- Graphify is refreshed once only at the final gate.

---

### Task 1: Runtime configuration, modes, status, and operator controls

**Files:**
- Create: `src/axq/orchestration/contracts.py`
- Create: `src/axq/orchestration/config.py`
- Create: `src/axq/orchestration/__init__.py`
- Test: `tests/test_runtime_orchestration.py`

**Interfaces:**
- Produces: `RuntimeMode`, `StartupPhase`, `RuntimeReadiness`, `RuntimeConfig`, `RuntimeStatus`,
  `OperatorControls`, `DecisionCycle`, and strict callable/ledger/snapshot protocols.
- Path and polling configuration is operational and never included in content-addressed trading IDs.

- [ ] Write failing contract tests for default non-mutation, strict config, UTC status, operator
  pause/disable/kill monotonicity, no live mode, and explicit symbol/path propagation.
- [ ] Run the focused test and confirm import failure for the absent package.
- [ ] Implement frozen versioned schemas and narrow protocols with no generic mutable dictionaries.
- [ ] Run focused pytest, Ruff, and mypy.

### Task 2: Startup recovery and fail-closed readiness

**Files:**
- Create: `src/axq/orchestration/service.py`
- Modify: `src/axq/runtime/replay.py`
- Test: `tests/test_runtime_orchestration.py`

**Interfaces:**
- Produces: `RuntimeOrchestrator.startup()` and `RuntimeOrchestrator.status`.
- Consumes: broker snapshot provider, `broker_snapshot_runtime_events`, execution reconciliation,
  `evaluate_resume_readiness`, runtime runner, journal, execution ledger, and action ledger.

- [ ] Write failing tests for safe startup, broker unavailable, UNKNOWN/local-only/broker-only
  blocking, missing continuity, thesis expiry, graceful and crash-style restoration.
- [ ] Implement startup phases in fixed order; process snapshot events without decisions, restore the
  latest journaled thesis, reconcile exact linkage, and remain blocked unless readiness is SAFE.
- [ ] Add only the minimal runner thesis restoration accessor required for restart continuity.
- [ ] Run focused tests and targeted static checks.

### Task 3: One shared event/decision/feedback path

**Files:**
- Modify: `src/axq/orchestration/service.py`
- Modify: `src/axq/runtime/journal.py`
- Test: `tests/test_runtime_orchestration.py`

**Interfaces:**
- Produces: `process_event()`, `run_source()`, bounded snapshot refresh, decision-cycle journaling,
  entry/action transport dispatch, feedback reduction, and `RuntimeRunSummary`.
- Consumes: one `DecisionCycleProcessor` used unchanged in replay, shadow, and demo.

- [ ] Write failing tests for M5 full chain, HOLD/Discipline/Risk stops, intrabar existing-thesis
  path, replay/shadow/demo mode behavior, feedback, duplicate/UNKNOWN no-resend, position actions,
  operator pause, kill switch, and deterministic parity/count summaries.
- [ ] Extend the journal union with existing Master, Discipline, Risk, execution, reconciliation,
  readiness, and checkpoint semantic types.
- [ ] Implement orchestration-only sequencing; all decision/context construction remains in the
  injected processor and all broker behavior remains in existing adapters.
- [ ] Run focused tests and targeted static checks.

### Task 4: Graceful shutdown and configuration factory

**Files:**
- Modify: `src/axq/orchestration/service.py`
- Create: `configs/runtime/demo.yaml`
- Test: `tests/test_runtime_orchestration.py`

**Interfaces:**
- Produces: `shutdown()` and `build_mt5_gateway(config)`.
- Shutdown stops intake, appends a recovery checkpoint, syncs journal and both ledgers, then closes
  the gateway; crash recovery treats committed history as authoritative without requiring a checkpoint.

- [ ] Write failing tests for flush order, final checkpoint/cursors, close, disabled/replay no broker
  connection, and explicit terminal-path forwarding.
- [ ] Implement shutdown and the lazy gateway factory without putting terminal path in semantic IDs.
- [ ] Run focused tests and targeted static checks.

### Task 5: Documentation and final gate

**Files:**
- Modify: `README.md`, `docs/architecture.md`, `docs/agentic_architecture.md`,
  `docs/project_status.md`, `docs/decision_log.md`, `docs/runbook.md`, `execution/README.md`
- Create: `docs/runtime_orchestration.md`
- Refresh once: `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`

- [ ] Document actual startup, processing, modes, readiness, restart, shutdown, operator, and replay
  behavior plus explicit exclusions.
- [ ] Run focused Task 9 tests and targeted Ruff/mypy.
- [ ] Run full pytest, Ruff, mypy with unused-ignore suppression, pip check, and diff check once.
- [ ] Refresh Graphify once, verify durable outputs, and rerun only checks affected by generation.
- [ ] Report remaining Phase 7 gaps and stop before Phase 8 without commit or push.
