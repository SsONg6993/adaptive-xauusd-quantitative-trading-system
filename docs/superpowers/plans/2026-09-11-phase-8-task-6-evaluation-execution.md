# Phase 8 Task 6 Deterministic Evaluation Execution Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute exact persisted proposal-evaluation plans over content-digested DEVELOPMENT and
VALIDATION metric samples while structurally withholding Final OOS.

**Architecture:** New focused modules extend `axq.reflection` with immutable execution contracts, a
closed deterministic metric-sample adapter, and append-only audit persistence. The service loads
Task 5 plan/candidate truth, verifies exact canonical inputs, builds results through the existing
result builder, and reuses completed request identities without evaluator replay.

**Tech Stack:** Python 3.12, Pydantic 2, SQLite, hashlib, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-11-phase-8-task-6-evaluation-execution-design.md`

## Global Constraints

- Adapter kind is exactly `CANONICAL_METRIC_SAMPLES_V1`, implementation version `1.0`.
- Input scopes are only `DEVELOPMENT` and `VALIDATION`; no Final OOS path or CLI argument exists.
- Compute only plan metric keys with aggregations `MEAN`, `MIN`, `MAX`, `SUM`, or `COUNT`.
- Final OOS observations are `UNAVAILABLE` with `FINAL_OOS_NOT_ACCESSED` and zero samples.
- Load exact plan/candidate state from Task 5 persistence and preserve all Task 5 criteria unchanged.
- Identical completed requests reuse the exact persisted result/audit without adapter execution.
- Exclude `requested_at` from request identity and `started_at`/`completed_at` from audit identity;
  retain all three as strict UTC serialized audit metadata.
- Persist request/audit metadata append-only under migration `010_evaluation_execution.sql`.
- Do not tune, replay, invoke subprocess/plugins, promote, deploy, mutate runtime, or contact brokers.
- Do not run the seven Task 4 baseline proposals.
- Do not commit, push, merge, or begin another task without explicit instruction.

---

### Task 1: Execution and unavailable-observation contracts

**Files:**
- Create: `src/axq/reflection/execution_contracts.py`
- Modify: `src/axq/reflection/evaluation_contracts.py`
- Modify: `src/axq/reflection/__init__.py`
- Test: `tests/test_evaluation_execution_contracts.py`

**Interfaces:**
- Produces: `ExecutionInputArtifactRef`, `MetricSampleSeries`,
  `CanonicalMetricSampleArtifact`, `EvaluationExecutionRequest`, `EvaluationExecutionAudit`,
  `EvaluationAdapterKind`, and `EvaluationExecutionStatus`.
- Extends: `MetricObservation.reason_code: str | None = None` with available/unavailable invariants.

- [ ] Write failing tests that construct strict frozen schemas, reject naive/non-UTC timestamps,
  reject Final OOS input references, reject invalid SHA-256 and duplicate sample keys, and prove
  identity/order invariance with hand-checked semantic prefixes.
- [ ] Add retry-time tests proving different `requested_at`, `started_at`, and `completed_at` values
  preserve request/audit IDs when all semantic linkage and artifact digests are identical.
- [ ] Write failing tests proving AVAILABLE observations reject reason codes and UNAVAILABLE
  observations require null value, zero samples, and a non-empty reason code.
- [ ] Run `python -m pytest tests/test_evaluation_execution_contracts.py -q` and verify failure due
  to the absent module/new field behavior.
- [ ] Implement the minimal contracts and observation validation; export public symbols.
- [ ] Rerun the focused test, Ruff the touched files, and mypy the reflection package to GREEN.

### Task 2: Closed deterministic metric-sample adapter

**Files:**
- Create: `src/axq/reflection/execution_adapter.py`
- Test: `tests/test_evaluation_execution_adapter.py`

**Interfaces:**
- Produces: `CanonicalMetricSamplesAdapter.execute(request, plan, artifacts, available_at)` returning
  `ProposalEvaluationResult` and compact canonical result bytes.
- Consumes: exact immutable request/plan and a scope-keyed tuple of verified sample artifacts.

- [ ] Write failing literal tests for `MEAN`, `MIN`, `MAX`, `SUM`, and `COUNT`, exact sample counts,
  and deterministic result bytes under reordered input series.
- [ ] Add failing tests for missing/extra/undeclared series, wrong scope, unsupported aggregation,
  seed/environment/linkage mismatch, and any Final OOS input artifact.
- [ ] Add a spy-free filesystem boundary test proving no Final OOS path is requested: the adapter
  receives only in-memory DEVELOPMENT/VALIDATION artifacts and produces explicit
  `FINAL_OOS_NOT_ACCESSED` observations.
- [ ] Implement exact closed aggregation and call only `build_evaluation_result`; do not import
  replay, quant trainer, runtime, MT5, subprocess, plugin, or proposal-transition modules.
- [ ] Run focused adapter tests, Ruff, and mypy to GREEN.

### Task 3: Append-only request and audit persistence

**Files:**
- Create: `database/migrations/010_evaluation_execution.sql`
- Create: `src/axq/reflection/execution_store.py`
- Test: `tests/test_evaluation_execution_store.py`

**Interfaces:**
- Produces: `append_request`, `request`, `requests`, `append_audit`, `audit`, `audits`, and `sync`.
- Consumes: `SQLiteProposalEvaluationStore` for exact plan/candidate/result validation.

- [ ] Write failing real-SQLite tests for exact stored plan/candidate linkage, request input scope
  equality, idempotent identical requests, same-ID conflict, and plan-before-request order.
- [ ] Write failing tests for result/run/plan/candidate linkage, result artifact digest equality,
  one completed audit per request, idempotent audit replay, and every UPDATE/DELETE trigger.
- [ ] Implement migration `010` and transactional fail-closed validation without mutable state.
- [ ] Run store tests, migration tests, Ruff, and mypy to GREEN.

### Task 4: Execution service and idempotent recovery

**Files:**
- Create: `src/axq/reflection/execution_service.py`
- Test: `tests/test_evaluation_execution_service.py`

**Interfaces:**
- Produces: `execute_evaluation_request(store_path, request, artifacts, available_at)` returning
  `EvaluationExecutionOutcome(result, result_bytes, audit, reused)`.
- Consumes: Task 5 evaluation store, Task 6 execution store, and the closed adapter.

- [ ] Write a failing controlled-fixture test that persists one CANDIDATE proposal/candidate/plan,
  executes DEVELOPMENT/VALIDATION samples, and asserts exact observations and result linkage.
- [ ] Add a failing rerun test that wraps the adapter with a counting seam, then proves the second
  identical completed request returns byte-identical content without a second adapter call.
- [ ] Add failure tests for digest mismatch, missing required scope, added scope, and absent stored
  plan/candidate/result links; assert no completed audit is appended.
- [ ] Implement load/verify/execute/result-append/audit-append ordering and crash-safe deterministic
  reuse of an already persisted result.
- [ ] Run all Task 6 focused tests, Ruff, and mypy to GREEN.

### Task 5: CLI, documentation, and final verification

**Files:**
- Create: `src/axq/reflection/execution_cli.py`
- Modify: `src/axq/reflection/__main__.py`
- Test: `tests/test_evaluation_execution_cli.py`
- Create: `docs/evaluation_execution.md`
- Modify: `README.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Produces: `run-evaluation-execution`, `show-evaluation-execution`, and
  `evaluation-execution-summary` CLI commands.

- [ ] Write a failing CLI test using one reviewed request JSON plus canonical DEVELOPMENT and
  VALIDATION artifact files; assert canonical result output, counts, and unchanged `CANDIDATE`
  proposal status.
- [ ] Add a later-timestamp rerun assertion proving the same request/result/audit IDs and
  byte-identical output with `reused=true`; assert the parser exposes no Final OOS, tuning,
  deployment, or promotion option.
- [ ] Implement CLI handlers with only `--development-input` and `--validation-input` file options;
  paths remain outside semantic identity.
- [ ] Document schemas, exact input JSON, Final OOS withholding, audit/recovery, and local commands.
- [ ] Audit imports and CLI surface for every forbidden execution path, refresh Graphify once, then
  run full pytest, Ruff, strict mypy, pip check, and `git diff --check` once.
