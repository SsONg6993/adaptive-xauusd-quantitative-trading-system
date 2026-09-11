# Phase 8 Task 7 Governed Candidate Replay Evaluator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce deterministic Task 6 canonical DEVELOPMENT/VALIDATION metric-sample artifacts for one exact persisted candidate evaluation plan.

**Architecture:** Add strict replay request/fixture/audit contracts, one allowlisted in-process controlled-fixture engine, append-only SQLite persistence, an idempotent orchestration service, and CLI handlers. Task 7 outputs feed Task 6 unchanged; neither layer accesses Final OOS or changes proposal lifecycle.

**Tech Stack:** Python 3.12, Pydantic v2, SQLite migrations, argparse, pytest, existing AXQ canonical hashing and reflection stores.

**Spec:** `docs/superpowers/specs/2026-09-11-phase-8-task-7-governed-candidate-replay-design.md`

## Global Constraints

- Work only in the isolated `codex/phase-8-reflection-experience` worktree.
- Use only DEVELOPMENT and VALIDATION; reject Final OOS structurally.
- Use only the allowlisted `CONTROLLED_REPLAY_FIXTURE_V1` in-process engine.
- Compute and emit only metric keys preregistered for the matching plan scope.
- Preserve exact proposal/candidate/plan, seed/environment, input, and output linkage.
- Exclude operational timestamps and paths from semantic identity.
- Do not tune, search, promote, deploy, mutate runtime, contact a broker, or execute the seven baseline proposals.

---

### Task 1: Immutable replay contracts

**Files:**
- Create: `src/axq/reflection/candidate_replay_contracts.py`
- Create: `tests/test_candidate_replay_contracts.py`
- Modify: `src/axq/reflection/__init__.py`

**Interfaces:**
- Consumes: Task 5 `MetricScope`/`SemanticArtifactRef` and Task 6 `ExecutionInputArtifactRef`/`CanonicalMetricSampleArtifact`.
- Produces: `CandidateReplayEngineKind`, `ControlledMetricValue`, `ControlledReplayObservation`, `ControlledReplayFixtureArtifact`, `CandidateReplayRequest`, and `CandidateReplayAudit`.

- [ ] Write contract tests for immutability, strict UTC, canonical ordering, duplicate rejection, Final OOS rejection, content-bound IDs, and timestamp-excluded request/audit identity.
- [ ] Run `python -m pytest tests/test_candidate_replay_contracts.py -q` and confirm failure because the module is absent.
- [ ] Implement the smallest strict Pydantic contracts and closed literals needed by the tests.
- [ ] Re-run the focused tests and Ruff/mypy for the new module.

### Task 2: Allowlisted controlled replay engine

**Files:**
- Create: `src/axq/reflection/candidate_replay_engine.py`
- Create: `tests/test_candidate_replay_engine.py`

**Interfaces:**
- Consumes: an exact request, authoritative proposal/candidate/plan, and digest-verified fixture tuple.
- Produces: `CandidateReplayEngineOutput` containing sorted Task 6 `CanonicalMetricSampleArtifact` records and canonical bytes.

- [ ] Write failing tests proving exact stored linkage, exact per-scope plan keys, causal ordering, DEVELOPMENT/VALIDATION-only output, missing/extra metric rejection, and byte-identical output.
- [ ] Run the focused test and confirm the missing engine failure.
- [ ] Implement `CandidateReplayEngine` and `ControlledReplayFixtureEngine` without filesystem or external-process access.
- [ ] Re-run focused tests plus Ruff/mypy.

### Task 3: Append-only migration and replay store

**Files:**
- Create: `database/migrations/011_candidate_replay_evaluation.sql`
- Create: `src/axq/reflection/candidate_replay_store.py`
- Create: `tests/test_candidate_replay_store.py`

**Interfaces:**
- Consumes: authoritative proposal/evaluation stores and Task 7 request/artifact/audit contracts.
- Produces: `SQLiteCandidateReplayStore.append_request`, `append_artifacts`, `append_audit`, and deterministic query methods.

- [ ] Write failing tests for exact persisted linkage, CANDIDATE-only status, input-scope equality, idempotent identical insert, conflicts, durable canonical artifacts, and UPDATE/DELETE triggers on every new table.
- [ ] Add migration 011 with request, input-ref, artifact, output-ref, and audit tables plus append-only triggers.
- [ ] Implement the store validation/query surface and run focused tests.
- [ ] Run Ruff/mypy for the store.

### Task 4: Idempotent service and Task 6 compatibility

**Files:**
- Create: `src/axq/reflection/candidate_replay_service.py`
- Create: `tests/test_candidate_replay_service.py`

**Interfaces:**
- Consumes: store path, request, fixture artifacts, explicit UTC operational times, and optional `CandidateReplayEngine`.
- Produces: `CandidateReplayOutcome(request, artifacts, artifact_bytes, audit, reused)`.

- [ ] Write a failing controlled end-to-end test proving engine-once retry reuse with later timestamps and byte-identical output artifacts.
- [ ] Add failure tests proving digest/linkage errors create no completed audit.
- [ ] Add the Task 6 compatibility test that executes generated artifacts through `execute_evaluation_request` and checks exact result linkage and Final OOS withholding.
- [ ] Implement the minimal orchestration and recovery path, then run focused tests and static checks.

### Task 5: CLI, documentation, and final gate

**Files:**
- Create: `src/axq/reflection/candidate_replay_cli.py`
- Create: `tests/test_candidate_replay_cli.py`
- Modify: `src/axq/reflection/__main__.py`
- Create: `docs/candidate_replay_evaluation.md`
- Modify: `README.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Refresh: `graphify-out/graph.json`
- Refresh: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Consumes: reviewed request/fixture JSON and the shared append-only store.
- Produces: `run-candidate-replay`, `show-candidate-replay`, and `candidate-replay-summary`.

- [ ] Write CLI tests for run/show/summary, exact output bytes, later retry reuse, absence of a Final OOS option, and unchanged CANDIDATE proposal status.
- [ ] Implement parser/handlers that write canonical scope-named artifacts without placing paths in semantic identity.
- [ ] Document exact controlled commands, identity, governance, Task 6 handoff, and measured fixture results.
- [ ] Audit imports for replay-runtime mutation, tuning, subprocess/plugin, broker, deployment, Final OOS, and proposal promotion paths.
- [ ] Refresh Graphify once after final source/docs changes.
- [ ] Run full pytest, Ruff, strict mypy, pip check, and `git diff --check`; report without committing or beginning the next task.
