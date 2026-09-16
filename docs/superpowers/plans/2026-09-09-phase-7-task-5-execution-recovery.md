# Phase 7 Task 5 Execution Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add append-only durable execution persistence, deterministic broker reconciliation, and a
fail-closed startup readiness gate without changing Tasks 1–4 decision behavior.

**Architecture:** A dedicated SQLite execution ledger implements the existing `ExecutionLedger`
port and reconstructs state exclusively from append-only semantic transitions. Strict recovery
contracts compare those local records with a causally fresh broker snapshot using exact persisted
linkage only; a separate readiness evaluator blocks entries until all critical state, execution
anomalies, and thesis continuity are safe. Recovery checkpoints are optional anchors, never the
authoritative history.

**Tech Stack:** Python 3.12, Pydantic v2 immutable models, SQLite WAL/FK conventions, pytest.

**Spec:** Approved Phase 7 Task 5 request and invariants; `docs/agentic_architecture.md` and
`docs/decision_log.md`.

## Global Constraints

- Work only in `.worktrees/phase-7-decision-execution` on
  `codex/phase-7-decision-execution`, based on `e1dc993d`.
- Do not commit, push, merge, modify main, or begin Task 6.
- Do not add MT5/MQL5 transport, live execution, position management, Master/Discipline/Risk
  changes, LLMs, reflection, dashboard behavior, training, or replay jobs.
- All timestamps are explicit timezone-aware UTC; no wall-clock reads determine semantic identity.
- Reconciliation resolution is append-only: a new record names the unresolved record it resolves;
  no earlier UNKNOWN/CONFLICT record is mutated.
- Any unresolved anomaly capable of duplicate or unknown exposure keeps readiness `BLOCKED`.
- `BROKER_ONLY` is an explicit classifiable anomaly, not assumed corruption.
- Matching uses only exact intent/client linkage, broker ticket, transport mapping, or another
  explicitly persisted deterministic link. Never infer a match from similar price/time/side/volume.
- Recovery checkpoints are optional optimization anchors. Committed transitions are authoritative.
- No mutable current-state execution table is permitted.
- Tests are written and observed failing before production code. No intermediate commits.

---

### Task 1: Canonical broker refresh events

**Files:**
- Modify: `src/axq/runtime/events.py`
- Modify: `src/axq/runtime/reducer.py`
- Test: `tests/test_execution_recovery.py`

**Interfaces:**
- Produces `RuntimeEventType.EXPOSURE_UPDATED` and `BROKER_CONSTRAINTS_UPDATED` using existing
  `ExposureState` and `BrokerConstraints` payloads.

- [ ] Write tests proving exposure and constraints update only through canonical events/reducer.
- [ ] Run focused tests and observe missing enum members.
- [ ] Add payload typing, validation mapping, and reducer branches.
- [ ] Run focused tests green.

### Task 2: Recovery and reconciliation contracts

**Files:**
- Create: `src/axq/execution_boundary/recovery_contracts.py`
- Modify: `src/axq/execution_boundary/__init__.py`
- Test: `tests/test_execution_recovery.py`

**Interfaces:**
- Produces `ExecutionTransition`, `ExecutionTransitionType`, `BrokerIntentLink`,
  `BrokerRecoverySnapshot`, `ReconciliationFinding`, `ReconciliationReport`,
  `ReconciliationKind`, `ResolutionStatus`, `ResumeReadiness`, `ResumeStatus`,
  `ResumeBlockReason`, and `RecoveryCheckpoint`.
- Every semantic model is frozen, extra-forbid, versioned, UTC validated, and content-addressed.
- `ReconciliationReport.supersedes_report_id` is required when resolving prior unresolved findings.

- [ ] Write contract tests for deterministic IDs, UTC rejection, immutable records, and append-only
  supersession linkage.
- [ ] Observe failures because contracts do not exist.
- [ ] Implement the minimal strict models and validators.
- [ ] Run focused tests green.

### Task 3: Append-only SQLite execution ledger

**Files:**
- Create: `database/migrations/003_execution_recovery.sql`
- Create: `src/axq/execution_boundary/persistence.py`
- Modify: `src/axq/execution_boundary/__init__.py`
- Test: `tests/test_execution_recovery.py`

**Interfaces:**
- `SQLiteExecutionLedger(path)` implements `get`, `reserve`, `is_reserved`, and `record`.
- Adds `append_reconciliation`, `transitions`, `latest_reconciliation`,
  `requires_reconciliation`, `append_checkpoint`, `latest_checkpoint`, and `sync`.
- Tables contain append-only transition/checkpoint rows with deterministic semantic IDs and
  operational autoincrement sequence only. UPDATE/DELETE triggers reject mutation. A unique
  reservation constraint makes reserve atomic across processes.

- [ ] Write real SQLite tests for adapter reconstruction, process-style reopen, terminal/UNKNOWN
  no-resend, history ordering, mutation rejection, and checkpoint reload.
- [ ] Observe failures because durable ledger and migration do not exist.
- [ ] Implement migration and ledger transactions using WAL, foreign keys, busy timeout, and
  canonical JSON payloads.
- [ ] Run focused tests green.

### Task 4: Exact-linkage reconciliation

**Files:**
- Create: `src/axq/execution_boundary/reconciliation.py`
- Modify: `src/axq/execution_boundary/__init__.py`
- Test: `tests/test_execution_recovery.py`

**Interfaces:**
- `reconcile_execution_state(ledger, snapshot, *, as_of, prior_report=None) -> ReconciliationReport`.
- Compares local latest results with broker positions/orders using only `BrokerIntentLink` evidence.
- Emits `MATCHED`, `BROKER_ONLY`, `LOCAL_ONLY`, `CONFLICT`, or `UNKNOWN`; conflict reason codes
  distinguish ticket, direction, and material volume mismatch.

- [ ] Write tests for UNKNOWN match/no-evidence, broker-only and local-only objects, exact ticket,
  direction and volume conflicts, deterministic IDs, and refusal to fuzzy-match.
- [ ] Observe failures because reconciliation is absent.
- [ ] Implement deterministic sorted matching and findings.
- [ ] Run focused tests green.

### Task 5: Fail-closed safe-resume and continuity assessment

**Files:**
- Create: `src/axq/execution_boundary/readiness.py`
- Modify: `src/axq/execution_boundary/__init__.py`
- Test: `tests/test_execution_recovery.py`

**Interfaces:**
- `evaluate_resume_readiness(runtime_state, reconciliation, theses, *, as_of) -> ResumeReadiness`.
- Requires AVAILABLE, age-valid market/account/positions/orders/exposure/broker constraints;
  resolved execution findings; and complete, non-expired continuity for any execution-relevant
  thesis. It never mutates or revives a thesis.

- [ ] Write tests for every critical stale component, all unresolved anomaly classes, a fully fresh
  safe case, missing intrabar continuity, and expired thesis non-revival.
- [ ] Observe failures because readiness evaluation is absent.
- [ ] Implement pure deterministic reason accumulation in canonical order.
- [ ] Run focused tests green.

### Task 6: Refresh orchestration and recovery checkpoints

**Files:**
- Create: `src/axq/execution_boundary/recovery.py`
- Modify: `src/axq/execution_boundary/__init__.py`
- Test: `tests/test_execution_recovery.py`

**Interfaces:**
- `broker_snapshot_runtime_events(snapshot, *, source_sequence_start) -> tuple[RuntimeEvent, ...]`
  emits market/account/position/order/exposure/constraint events for the existing reducer.
- `create_recovery_checkpoint(...) -> RecoveryCheckpoint` accepts all causal timestamps; no wall
  clock is consulted. `recover_execution_state(ledger)` reconstructs from transitions first and may
  expose the latest checkpoint only as an anchor.

- [ ] Write tests for reducer refresh, deterministic event order, graceful checkpoint/sync, crash
  recovery without a checkpoint, source cursor preservation, and no wall-clock identity noise.
- [ ] Observe failures because recovery orchestration is absent.
- [ ] Implement the minimal pure builders and ledger-backed recovery summary.
- [ ] Run focused tests green.

### Task 7: Documentation and complete validation

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/agentic_architecture.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `execution/README.md`

- [ ] Document ledger authority, reconciliation classifications, safe-resume requirements,
  checkpoint limitations, and unimplemented Task 6 scope.
- [ ] Run focused Task 5 tests.
- [ ] Run full pytest, Ruff, mypy, pip check, and `git diff --check`.
- [ ] Report known unrelated `quant/models.py` unused-ignore warnings without editing that file.
- [ ] Verify main remains untouched and stop without commit/push/merge/Task 6.
