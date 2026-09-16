# Phase 8 Task 1 Experience Store Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic normalized outcome experiences and an append-only analytics-ready
SQLite store from exact Phase 7 semantic records.

**Architecture:** A typed replay-outcome artifact closes the existing reporting gap for completed
trade facts. A pure attribution builder joins that artifact to runtime and execution records by
semantic ID, while a separate store persists immutable experience payloads and indexed provenance.

**Tech Stack:** Python 3.12, Pydantic 2, SQLite, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-10-phase-8-task-1-experience-store-design.md`

## Global Constraints

- Preserve Phase 7 trading policies and execution behavior unchanged.
- Use exact semantic linkage only; never fuzzy timestamp/price/volume joins.
- Preserve `None` separately from zero and mark missing required links explicitly.
- Use deterministic content identities with strict UTC timestamps and no wall-clock metadata.
- Store actual and counterfactual outcomes in separate contracts.
- Generate no Reflection, ImprovementProposal, LLM, RAG, Experience Graph, or Phase 9 code.
- Do not commit, push, merge, or modify other worktrees.

---

### Task 1: Experience contracts

**Files:**
- Create: `src/axq/experience/contracts.py`
- Create: `src/axq/experience/__init__.py`
- Test: `tests/test_experience_contracts.py`

**Interfaces:**
- Consumes: Phase 7 semantic ID strings, `Signal`, `AgentStatus`, `UTCDateTime`.
- Produces: immutable experience models and `Experience` discriminated union.

- [x] Write failing tests for deterministic IDs, strict UTC, `None` versus zero, exact provenance,
  and actual/counterfactual separation.
- [x] Run the contract tests and confirm import/behavior failures.
- [x] Implement the minimal strict Pydantic models and canonical identity validators.
- [x] Run contract tests and targeted Ruff/mypy.

### Task 2: Append-only SQLite store

**Files:**
- Create: `database/migrations/005_experience_store.sql`
- Create: `src/axq/experience/store.py`
- Test: `tests/test_experience_store.py`

**Interfaces:**
- Consumes: `Experience` objects and their provenance source IDs.
- Produces: `SQLiteExperienceStore.append`, `.append_many`, `.experiences`, `.counts`, and `.sync`.

- [x] Write failing real-SQLite tests for insert, identical duplicate idempotency, conflicting payload
  failure, UPDATE/DELETE rejection, source lookup, and deterministic read order.
- [x] Run store tests and confirm the missing store/schema failures.
- [x] Add the migration and minimal store implementation with transactional source projection.
- [x] Run store tests and targeted Ruff/mypy.

### Task 3: Durable replay outcome artifact

**Files:**
- Create: `src/axq/replay_validation/outcomes.py`
- Modify: `src/axq/replay_validation/system.py`
- Modify: `src/axq/replay_validation/__init__.py`
- Test: `tests/test_system_replay.py`

**Interfaces:**
- Consumes: existing `ReplayFill`, `ReplayClosedTrade`, exact applied position-action IDs, event IDs,
  session IDs, and fixed replay conventions.
- Produces: `ReplayOutcomeArtifact` at `replay-outcomes.json` without changing semantic decisions.

- [x] Write failing tests for deterministic artifact identity, exact close-action linkage, and
  serialization that preserves zero and `None`.
- [x] Run focused replay tests and confirm the missing artifact behavior.
- [x] Implement typed source records, wire the existing runner journal, and write canonical JSON.
- [x] Run focused replay/causality tests and targeted Ruff/mypy.

### Task 4: Exact-link outcome attribution

**Files:**
- Create: `src/axq/experience/attribution.py`
- Test: `tests/test_outcome_attribution.py`

**Interfaces:**
- Consumes: `SQLiteRuntimeJournal`, `SQLiteExecutionLedger`,
  `SQLitePositionActionTransportLedger`, and `ReplayOutcomeArtifact`.
- Produces: `ExperienceBuild` containing deterministically ordered normalized experiences.

- [x] Write failing tests for completed trades, HOLD decisions, Discipline/Risk/action-safety
  rejection, position management, agent evidence, runtime anomalies, provenance, and incomplete
  exact linkage.
- [x] Run attribution tests and confirm missing builder behavior.
- [x] Implement native-ID indexes and pure builders without timestamp joins.
- [x] Run attribution tests and targeted Ruff/mypy.

### Task 5: Descriptive analytics and CLI

**Files:**
- Create: `src/axq/experience/analytics.py`
- Create: `src/axq/experience/__main__.py`
- Test: `tests/test_experience_cli.py`

**Interfaces:**
- Consumes: persisted experience records.
- Produces: deterministic count/display/summary JSON and CLI exit status.

- [x] Write failing CLI tests for build, counts, concise metrics, baseline reconciliation failure,
  and absence of reflection/proposal output.
- [x] Run CLI tests and confirm missing command behavior.
- [x] Implement `build-experiences`, `show-experiences`, and `summary`.
- [x] Run all focused Phase 8 Task 1 tests and targeted Ruff/mypy.

### Task 6: Baseline ingestion and final verification

**Files:**
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Consumes: corrected one-month XAUUSD replay inputs and Task 1 CLI.
- Produces: ignored replay/experience artifacts plus auditable Task 1 documentation.

- [x] Run one corrected one-month replay into a fresh ignored Phase 8 runtime directory.
- [x] Build the Experience Store and require exactly 166 completed trade experiences.
- [x] Display counts and descriptive metrics immediately through the CLI.
- [x] Run full pytest, Ruff, strict mypy, pip check, and `git diff --check` once.
- [x] Refresh Graphify exactly once and verify its tracked outputs.
- [x] Audit that no Reflection, proposal generation, graph/vector store, LLM dependency, policy
  mutation, commit, or push was introduced.
