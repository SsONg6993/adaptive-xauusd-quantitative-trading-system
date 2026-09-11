# Deterministic Paired Baseline-vs-Candidate Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compare exact baseline and candidate DEVELOPMENT/VALIDATION evidence under one preregistered plan without executing either side or creating new acceptance rules.

**Architecture:** Add immutable paired-comparison contracts, a pure comparison adapter that reuses Task 6 aggregation and Task 5 criteria, an append-only SQLite store/service, and reflection CLI commands. Exact policy/config, manifest, artifact, seed, environment, and plan linkage is checked before candidate-only criterion evaluation.

**Tech Stack:** Python 3.12, Pydantic 2, `decimal.Decimal`, SQLite migrations, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-11-phase-8-task-9-paired-evaluation-design.md`

## Global Constraints

- DEVELOPMENT and VALIDATION inputs only; Final OOS input references are structurally forbidden.
- Reuse the exact persisted `ProposalEvaluationPlan` and its unchanged `AcceptanceCriterion` records.
- Baseline value and candidate-minus-baseline delta are evidence only.
- Do not execute a replay, tune/search, promote, deploy, mutate runtime, contact broker/MT5, or evaluate the seven real proposals.
- Operational timestamps are strict UTC and excluded from request/audit semantic identity.
- No commits, pushes, merges, or next-task work during implementation.

---

### Task 1: Immutable paired comparison contracts

**Files:**
- Create: `src/axq/reflection/paired_evaluation_contracts.py`
- Test: `tests/test_paired_evaluation_contracts.py`

**Interfaces:**
- Consumes: `MetricScope`, `SemanticArtifactRef`, `CriterionRole`, `UTCDateTime`, `canonical_hash`.
- Produces: `PairedArtifactRef`, `PairedEvaluationRequest`, `PairedMetricComparison`, `PairedCriterionOutcome`, `PairedEvaluationResult`, and `PairedEvaluationAudit`.

- [ ] Write failing tests for immutability, strict UTC, Final OOS rejection, timestamp-independent request/audit IDs, normalized ordering, and canonical decimal strings.
- [ ] Run `python -m pytest tests/test_paired_evaluation_contracts.py -v` and verify failures are caused by missing contracts.
- [ ] Implement only the validated schemas and identity rules.
- [ ] Re-run the contract tests and verify they pass.

### Task 2: Pure paired comparison adapter

**Files:**
- Create: `src/axq/reflection/paired_evaluation.py`
- Modify: `src/axq/reflection/execution_adapter.py`
- Test: `tests/test_paired_evaluation.py`

**Interfaces:**
- Consumes: exact plan, request, baseline/candidate `CanonicalMetricSampleArtifact` tuples.
- Produces: canonical `PairedEvaluationResult` bytes and explicit parity/criterion outcomes.

- [ ] Write failing tests proving identical scope/manifest/seed/environment enforcement, `candidate - baseline` decimal serialization, candidate-only unchanged GE/LE/BETWEEN semantics, missing-side UNAVAILABLE behavior, and Final OOS withholding.
- [ ] Run the focused adapter tests and verify expected missing-function failures.
- [ ] Extract a public Task 6 aggregation helper without changing existing adapter output.
- [ ] Implement the minimal paired adapter using that helper and existing criterion evaluation behavior.
- [ ] Run Task 6 adapter tests plus paired adapter tests and verify both pass.

### Task 3: Append-only migration and store

**Files:**
- Create: `database/migrations/013_paired_evaluation.sql`
- Create: `src/axq/reflection/paired_evaluation_store.py`
- Test: `tests/test_paired_evaluation_store.py`

**Interfaces:**
- Consumes: paired request/result/audit contracts and existing proposal/evaluation/shared-kernel stores.
- Produces: idempotent append/read/list operations with immutable database history.

- [ ] Write failing tests for exact authoritative linkage, content conflicts, append-only UPDATE/DELETE rejection, result-before-audit ordering, and source-digest validation.
- [ ] Run store tests and verify failure because migration/store are absent.
- [ ] Add migration 013 tables, indexes, foreign keys, and no-update/no-delete triggers.
- [ ] Implement the narrow store and exact-link validations.
- [ ] Re-run store tests and migration regression tests.

### Task 4: Idempotent comparison service

**Files:**
- Create: `src/axq/reflection/paired_evaluation_service.py`
- Test: `tests/test_paired_evaluation_service.py`
- Create: `tests/paired_evaluation_test_support.py`

**Interfaces:**
- Consumes: persisted request authorities plus supplied baseline/candidate artifacts.
- Produces: `PairedEvaluationOutcome` with request, result, canonical bytes, audit, and `reused` flag.

- [ ] Write a controlled fixture and failing test for first execution plus later-timestamp retry.
- [ ] Verify the test fails because the service does not exist.
- [ ] Implement append-request, completed-audit recovery, one adapter invocation, result/audit persistence, and digest verification.
- [ ] Verify identical retries preserve request/result/audit IDs and bytes and do not invoke the adapter again.

### Task 5: CLI and package integration

**Files:**
- Create: `src/axq/reflection/paired_evaluation_cli.py`
- Modify: `src/axq/reflection/__init__.py`
- Modify: `src/axq/reflection/__main__.py`
- Test: `tests/test_paired_evaluation_cli.py`

**Interfaces:**
- Produces: `run-paired-evaluation`, `show-paired-evaluation`, and `paired-evaluation-summary`.

- [ ] Write failing CLI tests for canonical JSON, result-file bytes, summary counts, retry reuse, and absence of a Final OOS argument.
- [ ] Run the CLI tests and verify the commands are missing.
- [ ] Implement command registration/dispatch and concise deterministic summaries.
- [ ] Re-run focused CLI and reflection entry-point tests.

### Task 6: Documentation, audits, Graphify, and final gate

**Files:**
- Create: `docs/paired_evaluation.md`
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/project_status.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

- [ ] Run the controlled fixture and capture baseline/candidate values, deltas, criterion outcomes, IDs, artifact/database sizes, and exact CLI commands.
- [ ] Audit imports and command options for Final OOS, replay execution, tuning/search, promotion, deployment/runtime mutation, and broker/MT5 paths.
- [ ] Update docs with measured controlled-fixture results and explicit exclusions.
- [ ] Run `graphify update .` once and `graphify cluster-only . --no-label` once.
- [ ] Run full pytest, Ruff, strict mypy, pip check, and `git diff --check` once.
- [ ] Report results without committing, pushing, merging, or starting another task.
