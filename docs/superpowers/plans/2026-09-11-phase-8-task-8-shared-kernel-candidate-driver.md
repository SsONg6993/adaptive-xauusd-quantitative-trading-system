# Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evaluate one frozen Master-fusion configuration through the existing shared replay kernel and emit governed DEVELOPMENT/VALIDATION canonical metric artifacts.

**Architecture:** Add one immutable `SharedKernelPolicySet` to the existing replay composition root, then resolve a content-addressed Master-fusion candidate into that set. A dedicated append-only driver verifies exact governance and CSV manifests, runs the unchanged kernel, extracts only allowlisted preregistered metrics, and emits Task 6/7 artifacts.

**Tech Stack:** Python 3.12, Pydantic v2, SQLite, pandas, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-11-phase-8-task-8-shared-kernel-candidate-driver-design.md`

## Global Constraints

- DEVELOPMENT and VALIDATION only; Final OOS has no input path.
- V1 accepts only a frozen `CONFIGURATION` candidate targeting `MASTER_FUSION`.
- The candidate replaces only `fusion_policy` in one immutable policy set.
- Existing Phase 6/7 kernel, orchestration, replay transport, and trading semantics remain shared.
- No tuning, search, seven-proposal execution, broker/MT5 access, promotion, deployment, or runtime mutation.
- Operational timestamps and paths are excluded from content identity.

---

### Task 1: Shared replay policy composition boundary

**Files:**
- Create: `src/axq/replay_validation/policies.py`
- Modify: `src/axq/replay_validation/system.py`
- Modify: `src/axq/replay_validation/__init__.py`
- Test: `tests/test_shared_kernel_policy_set.py`

**Interfaces:**
- Produces: `SharedKernelPolicySet`, `default_shared_kernel_policy_set()`, and optional `policy_set` on `run_system_replay`.
- Preserves: omitted `policy_set` produces byte-identical metrics and semantic IDs.

- [ ] **Step 1: Write failing tests** proving policy sets are immutable/content-addressed, an explicit default set is byte-identical to the omitted default, and a changed Fusion policy changes only the Fusion policy identity.
- [ ] **Step 2: Run** `python -m pytest tests/test_shared_kernel_policy_set.py -v` and confirm missing-contract failures.
- [ ] **Step 3: Implement** the policy-set contract and thread it through the replay composition, scenario callback, Discipline state, and Position Action context without altering default values.
- [ ] **Step 4: Rerun** the focused test and existing system replay tests until green.

### Task 2: Frozen candidate and governed data contracts

**Files:**
- Create: `src/axq/reflection/shared_kernel_candidate_contracts.py`
- Test: `tests/test_shared_kernel_candidate_contracts.py`

**Interfaces:**
- Produces: `FrozenSharedKernelCandidateConfig`, `SharedKernelReplayDataManifest`, `SharedKernelCandidateRequest`, `SharedKernelCandidateAudit`, scoped file/result references, and V1 enums.
- Consumes: `FusionPolicy`, `MetricScope`, `SemanticArtifactRef`, and strict UTC types.

- [ ] **Step 1: Write failing contract tests** for strict UTC, deterministic IDs, operational timestamp exclusion, exact four-file manifests, scope sorting, Final OOS rejection, and fixed Master-fusion target.
- [ ] **Step 2: Run** the contract test and confirm imports/types are absent.
- [ ] **Step 3: Implement** frozen strict schemas with canonical normalization and content-addressed identities.
- [ ] **Step 4: Rerun** the contract tests until green.

### Task 3: Closed shared-kernel engine and metric extraction

**Files:**
- Create: `src/axq/reflection/shared_kernel_candidate_engine.py`
- Test: `tests/test_shared_kernel_candidate_engine.py`
- Create: `tests/shared_kernel_candidate_test_support.py`

**Interfaces:**
- Produces: `SharedKernelCandidateEngine` protocol, `SharedKernelMasterFusionEngineV1`, manifest verification, and `CanonicalMetricSampleArtifact` output.
- Consumes: existing `run_system_replay`, exact stored plan/config, and operational scope-to-directory mappings.

- [ ] **Step 1: Add deterministic synthetic M5/M15/H1/H4 CSV fixture helpers and failing tests** for exact digest verification, single Fusion replacement, closed metric keys, Task 6 artifact shape, and Final OOS absence.
- [ ] **Step 2: Run** the engine tests and confirm the missing engine failures.
- [ ] **Step 3: Implement** the engine as a transport/orchestration adapter over `run_system_replay`; map only the seven allowlisted metrics and never import broker adapters.
- [ ] **Step 4: Rerun** engine and Phase 7 replay tests until green.

### Task 4: Append-only store and idempotent service

**Files:**
- Create: `database/migrations/012_shared_kernel_candidate_driver.sql`
- Create: `src/axq/reflection/shared_kernel_candidate_store.py`
- Create: `src/axq/reflection/shared_kernel_candidate_service.py`
- Test: `tests/test_shared_kernel_candidate_store.py`
- Test: `tests/test_shared_kernel_candidate_service.py`

**Interfaces:**
- Produces: `SQLiteSharedKernelCandidateStore`, `execute_shared_kernel_candidate()`, persisted requests/manifests/results/artifacts/audits, and completed-request reuse.
- Consumes: existing proposal/evaluation stores and Task 6 canonical artifact contracts.

- [ ] **Step 1: Write failing tests** for append-only triggers, identical append reuse, conflict rejection, exact authoritative linkage, CANDIDATE-only first execution, and later-timestamp completed reuse without engine reinvocation.
- [ ] **Step 2: Run** store/service tests and confirm missing migration/service failures.
- [ ] **Step 3: Implement** migration, store, and service with exact digest revalidation and fail-closed partial-run handling.
- [ ] **Step 4: Rerun** focused tests and verify Task 6 consumes the produced artifacts unchanged.

### Task 5: CLI, documentation, and final governance gate

**Files:**
- Create: `src/axq/reflection/shared_kernel_candidate_cli.py`
- Modify: `src/axq/reflection/__init__.py`
- Modify: `src/axq/reflection/__main__.py`
- Create: `tests/test_shared_kernel_candidate_cli.py`
- Create: `docs/shared_kernel_candidate_driver.md`
- Modify: `README.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Produces: `run-shared-kernel-candidate`, `show-shared-kernel-candidate`, and `shared-kernel-candidate-summary`.

- [ ] **Step 1: Write failing CLI tests** for controlled execution, show/summary output, forbidden Final OOS arguments, and stable retry output.
- [ ] **Step 2: Implement** narrow CLI parsing and canonical JSON reporting.
- [ ] **Step 3: Run** all focused shared-kernel candidate tests, Task 6/7 compatibility tests, and Phase 7 replay parity tests.
- [ ] **Step 4: Update** architecture/status/runbook/decision documentation with measured controlled-fixture results and exact commands.
- [ ] **Step 5: Audit** imports and behavior for broker, MT5, tuning, search, promotion, deployment, runtime mutation, and baseline proposal execution.
- [ ] **Step 6: Refresh** Graphify once.
- [ ] **Step 7: Run** full pytest, Ruff, strict mypy, pip check, and `git diff --check`; report without committing or starting another task.
