# Phase 8 Task 3 Weekly Reflection and Pattern Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic ISO-week reflections, guarded success/failure patterns, and an
explicit append-only knowledge-status lifecycle from immutable daily reflections and experiences.

**Architecture:** Dedicated weekly modules extend `axq.reflection` without changing the daily
contracts. A pure builder resolves daily revision chains, validates exact provenance, suppresses
incomplete weeks, and creates observation-only patterns; a separate SQLite store persists weekly
records and explicit lifecycle transitions; narrow CLI handlers expose canonical JSON.

**Tech Stack:** Python 3.12, Pydantic 2, SQLite, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-09-11-phase-8-task-3-weekly-reflection-design.md`

## Global Constraints

- Preserve Phase 7 runtime behavior and all Task 1–2 contracts.
- Use ISO Monday 00:00 UTC to following Monday 00:00 UTC intervals.
- Persist incomplete weeks with `WEEK_COMPLETENESS` and no patterns.
- Validate exact DailyReflection, finding, and Experience IDs; use no fuzzy joins.
- Create patterns only as `OBSERVATION`; transitions require explicit append-only actions.
- Pattern keys bind exactly pattern type, category, signal class, reason, scope, and scope value.
- Do not implement ImprovementProposal, tuning, graph/RAG, LLMs, runtime mutation, or Phase 9.
- Do not commit, push, or merge without a separate explicit request.

---

### Task 1: Weekly contracts and semantic identities

**Files:**
- Create: `src/axq/reflection/weekly_contracts.py`
- Modify: `src/axq/reflection/__init__.py`
- Test: `tests/test_weekly_reflection_contracts.py`

**Interfaces:**
- Consumes: Task 2 `FindingCategory`, `FindingSignal`, `MetricFact`, and strict UTC types.
- Produces: `WeeklyReflectionPolicy`, `WeeklySampleGuard`, `PatternMetricSummary`,
  `SuccessPattern`, `FailurePattern`, `WeeklyReflection`, `PatternStatusTransition`, and enums.

- [ ] Write contract tests with literal identities proving strict ISO boundaries, frozen schemas,
  normalized source ordering, incomplete-week pattern rejection, OBSERVATION-only construction,
  exact six-field pattern-key stability across weeks, and transition identity/UTC validation.
- [ ] Run `pytest tests/test_weekly_reflection_contracts.py -q` and confirm import failure because
  `weekly_contracts` does not exist.
- [ ] Implement strict Pydantic contracts and canonical identity validators with no wall-clock or
  storage sequence fields.
- [ ] Run the focused contract test, Ruff on the new module/test, and mypy on `axq.reflection`.

### Task 2: Pure weekly aggregation and exact provenance

**Files:**
- Create: `src/axq/reflection/weekly.py`
- Test: `tests/test_weekly_reflection.py`

**Interfaces:**
- Consumes: `Iterable[DailyReflection]`, `Iterable[Experience]`, Monday `date`,
  `WeeklyReflectionPolicy`, optional superseded ID.
- Produces: `build_weekly_reflection(...) -> WeeklyReflection`.

- [ ] Write literal-fixture tests proving ISO Monday/week boundaries, terminal daily-revision
  selection without sequence dependence, seven present periods, exact five missing periods for the
  two-day baseline tail, and input-order invariant identity.
- [ ] Run the aggregation tests and confirm failure because `build_weekly_reflection` is absent.
- [ ] Add tests proving incomplete weeks retain completeness/provenance guards and zero patterns,
  while a later complete input creates a distinct explicitly superseding reflection.
- [ ] Add tests proving repeated positive findings create SuccessPattern, negative/warning findings
  create FailurePattern, neutral/under-sampled findings do not, and metrics summarize literal
  count/min/max/mean values.
- [ ] Add tests proving a missing exact Experience ID, duplicate Experience ID, invalid daily
  provenance, branched/cyclic/missing daily revision chain, or mixed daily policy fails closed.
- [ ] Implement pure revision resolution, exact provenance validation, guard creation, pattern
  grouping, metric summaries, and observation-only weekly construction.
- [ ] Run weekly contract/aggregation tests plus targeted Ruff and mypy.

### Task 3: Append-only weekly and lifecycle persistence

**Files:**
- Create: `database/migrations/007_weekly_reflection.sql`
- Create: `src/axq/reflection/weekly_store.py`
- Test: `tests/test_weekly_reflection_store.py`

**Interfaces:**
- Consumes: weekly policies/reflections/patterns/transitions.
- Produces: idempotent append/read/latest/source lookup, explicit weekly supersession,
  `append_transition`, `transition_history`, and fail-closed `current_status`.

- [ ] Write real-SQLite tests for policy/reflection idempotency, conflicting same-ID rejection,
  latest weekly lookup, exact source lookup, explicit same-week supersession, and UPDATE/DELETE
  trigger rejection.
- [ ] Run store tests and confirm import failure because `weekly_store` does not exist.
- [ ] Add lifecycle tests for every allowed edge and for rejected stale status, invalid edge,
  incorrect predecessor, branch, unknown pattern, terminal transition, and conflicting identity.
- [ ] Implement migration tables/indexes/triggers and transactional store methods. Derive status by
  replay from `OBSERVATION`; never store or update a mutable current-status row.
- [ ] Run focused store/lifecycle tests plus targeted Ruff and mypy.

### Task 4: Weekly CLI integration

**Files:**
- Create: `src/axq/reflection/weekly_cli.py`
- Modify: `src/axq/reflection/__main__.py`
- Test: `tests/test_weekly_reflection_cli.py`

**Interfaces:**
- Consumes: daily store, experience store, weekly store, explicit lifecycle action arguments.
- Produces: `build-weekly-reflections`, `show-weekly-reflection`, `weekly-summary`,
  `transition-pattern`, and `show-pattern-history` commands.

- [ ] Write CLI tests with real temporary SQLite stores for complete/incomplete builds, canonical
  show output, concise summary counts, identical rerun reuse, changed-input supersession, invalid
  non-Monday dates, explicit transition append, and immutable history output.
- [ ] Run CLI tests and confirm failure because weekly commands are not registered.
- [ ] Implement parser registration and command handlers in `weekly_cli.py`; keep daily command
  behavior unchanged and emit sorted compact JSON.
- [ ] Run every Task 3 focused test plus targeted Ruff and mypy.

### Task 5: Corrected one-month baseline and durable context

**Files:**
- Modify: `README.md`
- Modify: `docs/daily_reflection.md`
- Create: `docs/weekly_reflection.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Consumes: Task 1 Experience Store and Task 2 daily-reflection store.
- Produces: ignored weekly SQLite artifact, canonical report JSON, documented measured counts.

- [ ] Build weeks starting 2026-08-10 through 2026-09-07 from unchanged baseline stores.
- [ ] Verify four complete and one incomplete weekly record, zero incomplete-week patterns, exact
  present/missing dates, observation-only pattern statuses, and no lifecycle transitions.
- [ ] Rebuild identically and verify all weekly IDs are reused and summary JSON is byte-identical.
- [ ] Record measured success/failure pattern and guard counts without tuning the policy.
- [ ] Update architecture/status/decision/runbook documentation with exact commands and scope.
- [ ] Audit imports and symbols for forbidden proposals, graph/RAG, LLM, runtime mutation, and Phase 9.
- [ ] Refresh Graphify once after final source/document changes.
- [ ] Run one final full pytest, Ruff, strict mypy, pip check, and `git diff --check` gate.
