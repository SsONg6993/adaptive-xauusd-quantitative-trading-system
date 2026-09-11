# Phase 8 Task 5 Proposal Evaluation Contract and Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preregister exact proposal evaluation plans, append externally supplied evaluation
evidence, and record explicit non-promoting operator evidence decisions.

**Architecture:** New evaluation modules extend `axq.reflection` without importing runtime or
execution components. Strict contracts freeze candidate, metric, criterion, plan, result, and
operator-decision semantics; a pure result builder applies only preregistered criteria; an
append-only SQLite store enforces exact Task 4 proposal linkage and chronology; CLI commands ingest
reviewed JSON but never execute an evaluator.

**Tech Stack:** Python 3.12, Pydantic 2, SQLite, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-11-phase-8-task-5-proposal-evaluation-design.md`

## Global Constraints

- Register plans only for proposals whose replayed status is exactly `CANDIDATE`.
- Require a persisted immutable candidate spec linked to the exact proposal ID/key/target.
- Define every metric and criterion before any result exists.
- Make every Final OOS metric and criterion reporting-only.
- Derive result outcomes only from the exact stored plan; reject undeclared or missing metrics.
- Keep operator evidence decisions separate from proposal lifecycle and deployment authority.
- Persist every record and correction append-only with deterministic content identities.
- Do not execute replay/challengers, tune, deploy, promote proposals, or mutate runtime behavior.
- Preserve Phase 3 Final OOS governance and all Phase 6/7 shared-kernel behavior.
- Do not commit, push, merge, or begin later work without explicit instruction.

---

### Task 1: Evaluation contracts and protected-OOS invariants

**Files:**
- Create: `src/axq/reflection/evaluation_contracts.py`
- Modify: `src/axq/reflection/__init__.py`
- Test: `tests/test_proposal_evaluation_contracts.py`

**Interfaces:**
- Produces: `EvaluationCandidateSpec`, `ValidationMetricSpec`, `AcceptanceCriterion`,
  `ProposalEvaluationPlan`, `MetricObservation`, `CriterionOutcome`,
  `ProposalEvaluationResult`, `OperatorEvaluationDecision`, and their closed enums.

- [ ] Write literal contract tests proving frozen/strict/versioned schemas, aware UTC, normalized
  identity inputs, candidate/proposal compatibility, and stable content-addressed IDs.
- [ ] Run the contract test and verify RED because `evaluation_contracts` does not exist.
- [ ] Add failing tests proving plans reject observed values, duplicate metric/criterion keys, no
  decision criterion, and any Final OOS criterion whose role is not `REPORTING_ONLY`.
- [ ] Add failing tests proving results cannot carry criteria, decisions require exact decision
  criterion IDs, and all records reject tampered IDs.
- [ ] Implement the smallest enums and immutable contracts needed to satisfy the tests.
- [ ] Run focused contracts, targeted Ruff, and reflection-package mypy to GREEN.

### Task 2: Pure preregistration and result evaluation

**Files:**
- Create: `src/axq/reflection/evaluations.py`
- Test: `tests/test_proposal_evaluations.py`

**Interfaces:**
- Produces: `build_evaluation_plan(...) -> ProposalEvaluationPlan` and
  `build_evaluation_result(...) -> ProposalEvaluationResult`.
- Consumes: exact proposal/candidate, reviewed metric/criteria definitions, observations, and
  evidence digests; it performs no evaluator execution.

- [ ] Write failing tests for `CANDIDATE`-only plan creation, exact equality with all canonical
  proposal source collections,
  candidate target binding, and deterministic plan identity under reordered inputs.
- [ ] Write failing tests for `GE`, `LE`, and `BETWEEN`, minimum samples, unavailable evidence,
  complete metric sets, and exact plan/candidate/proposal/result linkage.
- [ ] Add tests proving Final OOS results are retained but cannot affect `SUPPORTED`,
  `NOT_SUPPORTED`, or `INCONCLUSIVE` aggregate outcomes.
- [ ] Implement pure validation-plan and result builders with no file, subprocess, training, replay,
  registry, or runtime calls.
- [ ] Run focused builder tests plus targeted Ruff and mypy to GREEN.

### Task 3: Append-only evaluation persistence

**Files:**
- Create: `database/migrations/009_proposal_evaluation.sql`
- Create: `src/axq/reflection/evaluation_store.py`
- Test: `tests/test_proposal_evaluation_store.py`

**Interfaces:**
- Produces: candidate/plan/result/decision append and lookup, latest explicit supersession,
  exact-source queries, operator-decision replay, and `sync()`.
- Consumes: `SQLiteImprovementProposalStore` only for exact proposal/status/source validation.

- [ ] Write real-SQLite failing tests for candidate idempotency/conflicts, CANDIDATE plan gate,
  missing proposal/source rejection, and plan-before-result ordering.
- [ ] Add failing tests for exact metric/criterion equality, corrected-result and plan
  supersession, decision-after-result, linear decision history, and all UPDATE/DELETE triggers.
- [ ] Implement migration tables/indexes/triggers and transactional store validation without a
  mutable current-state, proposal-status, or deployment table.
- [ ] Run store tests plus targeted Ruff and mypy to GREEN.

### Task 4: Evaluation CLI without execution

**Files:**
- Create: `src/axq/reflection/evaluation_cli.py`
- Modify: `src/axq/reflection/__main__.py`
- Test: `tests/test_proposal_evaluation_cli.py`

**Interfaces:**
- Produces: candidate registration, plan build, result evidence append, operator decision append,
  plan/result/history show, and evaluation summary commands.
- Consumes: reviewed JSON inputs and existing proposal/evaluation stores only.

- [ ] Write failing CLI tests with temporary SQLite stores and an explicitly transitioned synthetic
  proposal for registration, plan build, result recording, canonical show/summary, and idempotency.
- [ ] Add a test proving the CLI rejects an `OBSERVATION` proposal and has no command that runs
  replay, challenger, training, tuning, deployment, or proposal promotion.
- [ ] Implement compact sorted-JSON handlers that validate reviewed inputs and call only pure
  builders/store methods.
- [ ] Run all Task 5 focused tests plus targeted Ruff and mypy to GREEN.

### Task 5: Documentation and final verification

**Files:**
- Modify: `README.md`
- Create: `docs/proposal_evaluation.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Produces: documented preregistration/result/decision workflow and exact local CLI examples.

- [ ] Document candidate/plan/result/decision schemas, CANDIDATE gate, Final OOS reporting-only
  semantics, append-only corrections, and `VALIDATED != deployed`.
- [ ] Document that the seven real baseline proposals remain `OBSERVATION` and are not promoted or
  evaluated by Task 5.
- [ ] Audit evaluation modules for replay, challenger, training, tuning, deployment, proposal
  transition, runtime, broker, Experience Graph, RAG, LLM, and Phase 9 paths.
- [ ] Refresh Graphify once after final source and documentation changes.
- [ ] Run final full pytest, Ruff, strict mypy, pip check, and `git diff --check` once.
