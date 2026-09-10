# Phase 7 Task 8 Direct MT5 Transport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add demo-only direct MetaTrader5 entry/position-action transports and canonical broker
snapshot acquisition without adding a runtime loop.

**Architecture:** A lazy concrete gateway isolates the optional MetaTrader5 package. Narrow entry,
position-action, and snapshot adapters reuse Phase 4–7 immutable intents, append-only ledgers,
recovery snapshots, canonical runtime events, and reducer contracts.

**Tech Stack:** Python 3.12, Pydantic 2, optional MetaTrader5, SQLite, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-10-phase-7-task-8-mt5-transport-design.md`

## Global constraints

- Work only in `.worktrees/phase-7-decision-execution` from checkpoint `2dd80236`.
- Execution is `DISABLED` by default and `DEMO_ENABLED` accepts only a verified demo account.
- DRY_RUN performs complete validation and `order_check`, but never `order_send`.
- Reserve stable intent identity before mutation; UNKNOWN is durable and never automatically resent.
- Use explicit symbol mapping and aware UTC; never fuzzy-match symbols or use runtime paths in IDs.
- Do not add MQL5/IPC, live-money support, a runtime loop, Task 9, training, commit, push, or merge.

---

### Task 1: Gateway and normalized MT5 contracts

**Files:**
- Create: `src/axq/mt5/contracts.py`
- Create: `src/axq/mt5/gateway.py`
- Create: `src/axq/mt5/__init__.py`
- Test: `tests/test_mt5_gateway.py`

**Interfaces:**
- Produces: `MT5Gateway`, `MT5Constants`, `MT5SymbolMapping`, `MT5ConnectionError`,
  `MetaTrader5Gateway`.

- [ ] Write tests proving lazy import, normalized mapping responses, explicit symbols, and structured
  initialization/unavailable failures.
- [ ] Run focused tests and confirm missing `axq.mt5` fails for the intended reason.
- [ ] Implement the protocol and lazy wrapper without importing MetaTrader5 at module import time.
- [ ] Run focused pytest, Ruff, and mypy.

### Task 2: Canonical broker snapshots

**Files:**
- Create: `src/axq/mt5/snapshot.py`
- Modify: `src/axq/runtime/state.py`
- Test: `tests/test_mt5_snapshot.py`

**Interfaces:**
- Consumes: `MT5Gateway`, `MT5SymbolMapping`, exact persisted ticket linkages.
- Produces: `MT5BrokerSnapshotProvider.capture() -> BrokerRecoverySnapshot` and existing canonical
  runtime-event compatibility.

- [ ] Write tests with complete fake MT5 account/tick/symbol/position/order mappings and literal
  expected canonical values/events.
- [ ] Verify tests fail because the provider and canonical broker digits field do not exist.
- [ ] Implement account, market, books, exposure, constraints, exact-link rebinding, and aware-UTC
  mapping; add optional broker `digits` to existing constraints as the narrow compatibility change.
- [ ] Run focused snapshot/recovery/reducer tests, Ruff, and mypy.

### Task 3: Entry transport and complete dry-run preflight

**Files:**
- Create: `src/axq/mt5/preflight.py`
- Create: `src/axq/mt5/entry.py`
- Modify: `src/axq/execution_boundary/adapter.py`
- Test: `tests/test_mt5_entry_transport.py`

**Interfaces:**
- Produces: `MT5ExecutionPreflight`, `MT5ExecutionTransport`, `MT5ExecutionAdapter`.
- Reuses: `DemoExecutionAdapter`, `ExecutionTransport`, `SQLiteExecutionLedger`,
  `BrokerExecutionReport`.

- [ ] Write tests for disabled/default, complete dry run, demo verification, preserved request fields,
  order-check/send separation, retcode mapping, failures, fills, duplicate and UNKNOWN no-resend.
- [ ] Verify the tests fail against the absent adapter and current dry-run behavior.
- [ ] Modify `DemoExecutionAdapter` narrowly so an optional preflight callable runs in DRY_RUN and
  DEMO modes; disabled remains zero-touch.
- [ ] Implement immediate preflight, broker request construction, and canonical report mapping.
- [ ] Run focused entry plus existing execution/recovery tests, Ruff, and mypy.

### Task 4: Durable position-action transport

**Files:**
- Create: `src/axq/position_actions/transport_contracts.py`
- Create: `src/axq/position_actions/adapter.py`
- Create: `src/axq/position_actions/persistence.py`
- Create: `src/axq/position_actions/feedback.py`
- Create: `database/migrations/004_position_action_transport.sql`
- Modify: `src/axq/position_actions/__init__.py`
- Modify: `src/axq/runtime/journal.py`
- Test: `tests/test_mt5_position_action_transport.py`

**Interfaces:**
- Produces: typed action result/transition contracts, append-only ledger, `MT5PositionActionAdapter`,
  and `position_action_result_to_runtime_event()`.

- [ ] Write tests for exact-ticket stop/close requests, full-volume close, monotonic stops, demo mode,
  dry run, duplicate/UNKNOWN restart behavior, broker failures, append-only persistence, and feedback.
- [ ] Verify tests fail because transport contracts and migration are absent.
- [ ] Implement stable result/transition identities and unique reservation persistence.
- [ ] Implement action-time exact-position preflight, `TRADE_ACTION_SLTP`/position-tagged close,
  `order_check`, `order_send`, and fail-closed mapping.
- [ ] Run focused Task 7/8, journal, execution, and recovery tests, Ruff, and mypy.

### Task 5: Documentation, optional read-only smoke, and final verification

**Files:**
- Modify: `README.md`, `docs/architecture.md`, `docs/agentic_architecture.md`,
  `docs/project_status.md`, `docs/decision_log.md`, `docs/runbook.md`, `execution/README.md`,
  `mt5/README.md`
- Modify once: `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`

- [ ] Document authority boundaries, modes, exact symbol mapping, UNKNOWN/no-resend, direct MT5
  limitation, and Task 9 deferrals.
- [ ] If the local terminal/package is available, run initialization/account/symbol/tick/books read
  only; never call order_check/order_send for the smoke.
- [ ] Run full pytest, Ruff, mypy with unused-ignore suppression, pip check, and `git diff --check`.
- [ ] Refresh Graphify exactly once and rerun final diff/static checks affected by generated output.
- [ ] Verify the main checkout and the two pre-existing worktree metadata markers were not altered;
  stop without commit, push, merge, or Task 9.
