# Phase 8 Task 4 Advisory Improvement Proposal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic evidence-linked advisory proposals from recurring weekly patterns,
with append-only supersession and explicit proposal-status transitions.

**Architecture:** Dedicated proposal modules extend `axq.reflection` without changing daily or
weekly contracts. A pure builder revalidates exact Experience/Daily/Weekly provenance and emits one
observation-only proposal per eligible recurring pattern key; a separate SQLite store persists
immutable proposals and explicit lifecycle transitions; narrow CLI handlers expose canonical JSON.

**Tech Stack:** Python 3.12, Pydantic 2, SQLite, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-11-phase-8-task-4-improvement-proposal-design.md`

## Global Constraints

- Require at least two distinct complete-week observations for one semantic `pattern_key`.
- Require passed completeness, provenance, pattern-day, and pattern-experience guards.
- Preserve exact weekly pattern, finding, daily reflection, and experience provenance.
- Create proposals only as `OBSERVATION`; transitions require explicit append-only actions.
- Treat `VALIDATED` as evidence status only, never deployment authority.
- Do not tune policy, modify code/runtime, execute replay/challengers, or add graph/RAG/LLM work.
- Preserve Phase 3 Final OOS governance and all Phase 6/7 shared-kernel behavior.
- Do not commit, push, merge, or begin later work without an explicit request.

---

### Task 1: Proposal contracts and identities

**Files:**
- Create: `src/axq/reflection/proposal_contracts.py`
- Modify: `src/axq/reflection/__init__.py`
- Test: `tests/test_improvement_proposal_contracts.py`

**Interfaces:**
- Consumes: `FindingCategory`, `PatternType`, `PatternSignalClass`, strict UTC types, canonical hash.
- Produces: `ImprovementProposalPolicy`, `ProposalTargetComponent`, `ProposalStatus`,
  `ProposalGuardKind`, `ProposalEvidenceGuard`, `ImprovementProposal`, and
  `ProposalStatusTransition`.

- [ ] Write contract tests proving frozen strict schemas, UTC enforcement, tuple normalization,
  literal content identities, stable proposal keys across changed evidence, observation-only
  construction, required exact source sets, all-passed embedded guards, and allowed lifecycle edges.
- [ ] Run the contract tests and verify RED because `proposal_contracts` does not exist.
- [ ] Implement the smallest immutable enums/models/validators and deterministic identity binding.
- [ ] Run contract tests, targeted Ruff, and reflection-package mypy to GREEN.

### Task 2: Pure eligibility, provenance, and proposal construction

**Files:**
- Create: `src/axq/reflection/proposals.py`
- Test: `tests/test_improvement_proposals.py`

**Interfaces:**
- Consumes: terminal weekly reflections, exact daily reflections and experiences, pattern-status
  resolver, and `ImprovementProposalPolicy`.
- Produces: `build_improvement_proposals(...) -> ProposalBuildResult` containing proposals and
  deterministic eligible/insufficient/rejected assessment records.

- [ ] Write failing tests for two-week eligibility, one-week insufficiency, seven expected fixture
  groups, input-order invariance, and deterministic category/target/rationale/change/benefit/risk/
  validation templates.
- [ ] Add failing tests for incomplete weeks, stale weekly revisions, mismatched pattern guards,
  rejected/deprecated sources, missing or duplicated patterns/findings/experiences, broken daily
  chains, and fuzzy-link rejection.
- [ ] Implement exact terminal-revision resolution, guard selection by pattern signature, source
  joins, recurrence assessment, deterministic templates, canonical availability, and one proposal
  per eligible pattern key.
- [ ] Run proposal contract/builder tests plus targeted Ruff and mypy to GREEN.

### Task 3: Append-only proposal and lifecycle persistence

**Files:**
- Create: `database/migrations/008_improvement_proposals.sql`
- Create: `src/axq/reflection/proposal_store.py`
- Test: `tests/test_improvement_proposal_store.py`

**Interfaces:**
- Consumes: policies, proposals, evidence guards, and explicit status transitions.
- Produces: idempotent append/read/latest/source lookup, explicit proposal supersession,
  `append_transition`, `transition_history`, and fail-closed `current_status`.

- [ ] Write real-SQLite failing tests for policy/proposal idempotency, content conflicts, exact source
  indexes, latest-by-key lookup, explicit supersession, and UPDATE/DELETE trigger rejection.
- [ ] Add lifecycle tests for every allowed edge and rejected stale status, invalid edge, wrong
  predecessor, branch, unknown proposal, terminal transition, time reversal, and duplicate identity.
- [ ] Implement migration tables/indexes/triggers and transactional store methods. Derive current
  status by replay; never create a mutable status or deployment table.
- [ ] Run focused persistence/lifecycle tests plus targeted Ruff and mypy to GREEN.

### Task 4: CLI integration

**Files:**
- Create: `src/axq/reflection/proposal_cli.py`
- Modify: `src/axq/reflection/__main__.py`
- Test: `tests/test_improvement_proposal_cli.py`

**Interfaces:**
- Consumes: Experience, daily, weekly, and proposal stores plus explicit lifecycle arguments.
- Produces: `build-improvement-proposals`, `show-improvement-proposal`, `proposal-summary`,
  `transition-proposal`, and `show-proposal-history`.

- [ ] Write failing CLI tests with real temporary stores for seven eligible groups, canonical show,
  concise summary, identical rerun reuse, changed-evidence supersession, and explicit transitions.
- [ ] Implement parser registration and handlers with sorted compact JSON, explicit store arguments,
  optional reviewed policy JSON, and no runtime/config write path.
- [ ] Run all Task 4 focused tests plus targeted Ruff and mypy to GREEN.

### Task 5: Unchanged baseline and durable context

**Files:**
- Modify: `README.md`
- Create: `docs/improvement_proposals.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Consumes: ignored Task 1–3 baseline SQLite stores.
- Produces: ignored proposal SQLite artifact, canonical summaries, measured baseline counts, and
  current architecture/runbook documentation.

- [ ] Build proposals from the unchanged weekly baseline and verify 14 assessed keys, seven eligible
  recurring keys, seven insufficient single-week keys, and seven observation-only proposals.
- [ ] Verify exact pattern/finding/daily/experience links, passed embedded guards, target counts, no
  transitions, and no production-policy/runtime mutation.
- [ ] Rebuild identically and verify all IDs are reused and summary JSON is byte-identical.
- [ ] Update documentation with exact build/show/history commands and measured counts.
- [ ] Audit imports and symbols for tuning, code/config mutation, replay/challenger execution,
  Experience Graph, RAG, LLM, broker, and Phase 9 paths.
- [ ] Refresh Graphify once after final source and documentation changes.
- [ ] Run final full pytest, Ruff, strict mypy, pip check, and `git diff --check` once.
