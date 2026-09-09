# Phase 7 Task 6 Deterministic Position Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure deterministic decision core for already-open positions that can hold, protect,
or request exit without submitting broker commands or reusing entry decisions as position actions.

**Architecture:** A new `axq.position_management` package owns strict content-addressed contracts and
a pure evaluator. The context binds one authoritative broker/replay position to its original
execution and thesis/scenario provenance, current evidence, Task 5 reconciliation/readiness, and
fresh account/position/broker state. The evaluator fails closed before applying explicit lifecycle
and conservative break-even rules; outputs are immutable journal-ready facts, not transport intents.

**Tech Stack:** Python 3.12, Pydantic v2 immutable models, existing AXQ runtime/agent/execution
contracts, pytest.

**Spec:** User-approved Phase 7 Task 6 request dated 2026-09-10; `docs/agentic_architecture.md` and
`docs/decision_log.md`.

## Global Constraints

- Work only in `.worktrees/phase-7-decision-execution` on
  `codex/phase-7-decision-execution` from checkpoint `114f723`.
- Do not commit, push, merge, modify main, or begin Task 7.
- Do not add MT5 transport, scale-in/out, reversal, dynamic trailing, partial profit taking,
  simulated brokerage, LLM/model calls, reflection, Experience Graph, Dashboard, or Phase 8 work.
- Preserve Tasks 1–5 and Final OOS governance; only narrow compatibility fixes proven by a failing
  invariant are allowed.
- Every contract is frozen, extra-forbid, schema-versioned, strict-UTC, serializable, and
  content-addressed without wall-clock or random identity input.
- Task 5 `SAFE` readiness and exact persisted execution-to-position linkage are mandatory before
  autonomous HOLD/PROTECT/EXIT evaluation of an open position.
- Position management emits no broker command and does not mutate Master, Discipline, Risk,
  Execution, thesis/scenario, runtime, or reconciliation state.
- Tests are written and observed failing before production code.

---

### Task 1: Strict position-management contracts

**Files:**
- Create: `src/axq/position_management/contracts.py`
- Create: `src/axq/position_management/__init__.py`
- Test: `tests/test_position_management.py`

**Interfaces:**
- Produces `PositionManagementPolicy`, `PositionManagementContext`,
  `PositionManagementOutcome`, `PositionManagementResult`, and `PositionManagementReason`.
- Context consumes at most one `PositionState`, original `ExecutionIntent`/`ExecutionResult`, exact
  `BrokerIntentLink`, `ThesisState`, optional `EvidenceBundle`, account/position/broker freshness,
  `ReconciliationReport`, `ResumeReadiness`, optional deterministic R/MFE/MAE, and causal timestamps.

- [ ] Write tests that reject naive/future timestamps, mismatched provenance, non-exact linkage,
  mutable/extra fields, malformed result payloads, and supplied IDs that disagree with content.
- [ ] Run `pytest tests/test_position_management.py -v` and confirm failure because the package is
  absent.
- [ ] Implement the enums and strict models with canonical ID prefixes `pmp-`, `pmc-`, and `pmo-`.
- [ ] Run the focused contract tests and confirm they pass.

### Task 2: Fail-closed evaluation and lifecycle semantics

**Files:**
- Create: `src/axq/position_management/evaluator.py`
- Modify: `src/axq/position_management/__init__.py`
- Test: `tests/test_position_management.py`

**Interfaces:**
- Produces `default_demo_position_management_policy() -> PositionManagementPolicy` and
  `evaluate_position(context, policy) -> PositionManagementOutcome`.
- `NO_ACTION` covers no position or unsafe/unlinked/stale inputs; `HOLD_POSITION` preserves an open
  position without modification; `EXIT_POSITION` is only an explicit lifecycle/safety request;
  `PROTECT_POSITION` requests only a broker-valid monotonic break-even stop.

- [ ] Write failing behavior tests for no position, ACTIVE/CONFIRMED hold, WEAKENING policy,
  INVALIDATED/EXPIRED/scenario-invalidated exits, missing thesis/evidence/continuity, stale state,
  blocked readiness, unresolved anomalies, and exact restart linkage.
- [ ] Implement ordered fail-closed gates followed by lifecycle rules; do not consume Master output.
- [ ] Write failing tests for long/short monotonicity, broker stop/freeze constraints, minimum age,
  maximum configured stop movement, and no-op when existing protection is already stronger.
- [ ] Implement the minimal break-even candidate function and validate the output again in the
  outcome model so protection cannot increase risk even if constructed directly.
- [ ] Run all focused tests green.

### Task 3: Purity, parity, and forbidden-authority tests

**Files:**
- Modify: `tests/test_position_management.py`

**Interfaces:**
- Equivalent serialized inputs produce identical contexts/outcomes in live-like and replay callers.
- Evaluation has no transport, model, Master/Discipline/Risk mutation, thesis mutation, scale, or
  reversal side effect.

- [ ] Add tests for deterministic policy/context/outcome identity and serialization round-trip.
- [ ] Add a live/replay-equivalence test using the same canonical bounded context.
- [ ] Add mutation-snapshot tests proving every input remains unchanged and bearish evidence cannot
  create a reverse entry or broker instruction.
- [ ] Run focused tests green.

### Task 4: Documentation and final validation

**Files:**
- Modify: `README.md`
- Modify: `docs/agentic_architecture.md`
- Modify: `docs/architecture.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/project_status.md`
- Modify: `docs/runbook.md`
- Modify: `execution/README.md`

- [ ] Document Task 6 scope, four outcomes, exact restart linkage, fail-closed readiness,
  monotonic protection, journal compatibility, and explicitly deferred Task 7/transport work.
- [ ] Run focused Task 6 tests.
- [ ] Run full pytest, Ruff, mypy with `--no-warn-unused-ignores`, pip check, and
  `git diff --check`.
- [ ] Verify Task 1–5 paths have no unintended semantic change, main remains untouched, and stop
  without commit/push/merge/Task 7.
