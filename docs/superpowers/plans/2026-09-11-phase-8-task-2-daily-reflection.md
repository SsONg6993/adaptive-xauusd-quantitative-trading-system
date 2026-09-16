# Phase 8 Task 2 Deterministic Daily Reflection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic, append-only UTC daily reflections from exact Task 1 experiences.

**Architecture:** A separate `axq.reflection` package defines immutable policies, guards, findings,
and daily records. A pure aggregator consumes experiences selected by causal `available_at`; a
separate SQLite store enforces immutable supersession; a narrow CLI exposes canonical JSON and a
concise projection.

**Tech Stack:** Python 3.12, Pydantic 2, SQLite, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-11-phase-8-task-2-daily-reflection-design.md`

## Global Constraints

- Preserve every Phase 7 policy and all runtime behavior unchanged.
- Select daily input only by timezone-aware UTC `available_at` in a half-open UTC day.
- Use content-addressed IDs without random or wall-clock identity fields.
- Record insufficient/unavailable diagnostics explicitly; never fabricate values.
- Generate no WeeklyReflection, ImprovementProposal, tuning, Experience Graph, RAG, LLM, or
  runtime mutation.
- Do not commit, push, merge, or modify another worktree.

---

### Task 1: Reflection contracts and policy

**Files:**
- Create: `src/axq/reflection/contracts.py`
- Create: `src/axq/reflection/__init__.py`
- Test: `tests/test_reflection_contracts.py`

**Interfaces:**
- Consumes: `UTCDateTime`, finite metric values, exact experience IDs.
- Produces: `ReflectionPolicy`, `SampleGuardRecord`, `ReflectionFinding`, `DailyReflection`.

- [x] Write failing tests for strict UTC, deterministic identity, normalized ordering, policy
  bounds, immutable models, `None` versus zero, and supersession identity.
- [x] Run the contract tests and confirm missing imports/behavior.
- [x] Implement minimal strict contracts and canonical identity validation.
- [x] Run focused tests and targeted Ruff/mypy.

### Task 2: Pure daily aggregation

**Files:**
- Create: `src/axq/reflection/daily.py`
- Test: `tests/test_daily_reflection.py`

**Interfaces:**
- Consumes: `Iterable[Experience]`, UTC `date`, `ReflectionPolicy`, optional predecessor ID.
- Produces: `build_daily_reflection(...) -> DailyReflection`.

- [x] Write literal-fixture failing tests for UTC availability boundaries and direction,
  session/regime, confidence, excursion, rejection, agent, position-management, and anomaly
  diagnostics.
- [x] Write failing tests proving guards suppress unsupported findings while recording why.
- [x] Implement deterministic grouping, metrics, findings, and guard records.
- [x] Run focused tests and targeted Ruff/mypy.

### Task 3: Append-only reflection persistence

**Files:**
- Create: `database/migrations/006_daily_reflection.sql`
- Create: `src/axq/reflection/store.py`
- Test: `tests/test_reflection_store.py`

**Interfaces:**
- Consumes: `ReflectionPolicy`, `DailyReflection`.
- Produces: append/idempotent/latest/list/source lookup and explicit supersession validation.

- [x] Write real-SQLite failing tests for policy persistence, idempotency, same-ID conflict,
  UPDATE/DELETE rejection, exact source indexes, latest lookup, and predecessor enforcement.
- [x] Add migration and minimal transactional store.
- [x] Run focused tests and targeted Ruff/mypy.

### Task 4: Build orchestration and CLI

**Files:**
- Create: `src/axq/reflection/__main__.py`
- Test: `tests/test_reflection_cli.py`

**Interfaces:**
- Consumes: existing Experience Store and reflection-store paths, one UTC date or inclusive range.
- Produces: canonical build/show JSON and deterministic concise summary.

- [x] Write failing CLI tests for single/range build, identical rerun, changed-input supersession,
  show, concise summary, and invalid dates.
- [x] Implement CLI and deterministic build-or-reuse orchestration.
- [x] Run all Task 2 focused tests and targeted Ruff/mypy.

### Task 5: Baseline validation and durable context

**Files:**
- Modify: `README.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Consumes: corrected one-month Task 1 Experience Store.
- Produces: ignored daily-reflection SQLite artifact and auditable descriptive baseline report.

- [x] Build daily reflections for the corrected one-month UTC range without changing policy.
- [x] Display finding/guard counts and representative measured findings.
- [x] Update documentation with contracts, commands, verified counts, and remaining scope.
- [x] Audit forbidden-scope absence.
- [x] Refresh Graphify exactly once.
- [x] Run the final full pytest, Ruff, strict mypy, pip check, and `git diff --check` once.
