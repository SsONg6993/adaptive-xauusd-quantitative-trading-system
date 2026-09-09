# Phase 6 Tool-Augmented Agentic Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic live/replay vertical slice from versioned runtime events and shared state through causal tools, stateful specialist evidence, intrabar scenario transitions, and an auditable evidence bundle without implementing Phase 7 trade authorization.

**Architecture:** Live-like and replay adapters emit the same canonical events into one state reducer and evidence kernel. Completed M5 events establish/update theses; tick or completed-M1 events may confirm/invalidate an existing scenario. The slice stops at an `EvidenceBundle`; Master fusion, Discipline Guard, Risk integration, and execution sinks retain explicit ports and are Phase 7 work.

**Tech Stack:** Python 3.12, Pydantic v2, pandas/NumPy, SQLite, pytest, existing `axq` feature/dataset/versioning contracts.

**Spec:** `docs/agentic_architecture.md`

**Completion status (2026-09-09):** Tasks 1–7 are implemented and Task 8 closes documentation and
lightweight verification. The implemented vertical slice stops at `EvidenceBundle`; none of the
Phase 7 authorization or execution boundaries described below should be read as implemented.

## Global Constraints

- Store every timestamp internally as timezone-aware UTC.
- Process only information whose `available_at` is at or before the current event.
- Live and replay share state reduction, tools, agents, scenario transitions, and evidence output.
- Only clock, event/data source, external-state adapter, journal backend, and execution sink may vary.
- Completed M5 bars establish/update primary theses; intrabar events reference an existing thesis.
- Predictive ML is optional evidence and cannot be required by any Phase 6 agent.
- Final OOS remains unavailable to selection, tuning, calibration, thresholds, ablations, and choice.
- No online policy mutation, automatic model promotion, trade execution, or heavy experiment runs.
- Preserve existing Phase 3–5 contracts; schema changes are additive.

---

### Task 1: Canonical runtime events and shared state

**Files:**
- Create: `src/axq/runtime/__init__.py`
- Create: `src/axq/runtime/events.py`
- Create: `src/axq/runtime/state.py`
- Test: `tests/test_runtime_state.py`

**Interfaces:**
- Consumes: `axq.versioning.canonical_hash(value: Any) -> str`.
- Produces: `RuntimeEvent`, `RuntimeEventType`, `MarketSnapshot`, `AccountState`, `PositionState`, `PendingOrderState`, `ExposureState`, `ExecutionFeedback`, and `RuntimeState`.

- [ ] **Step 1: Write failing UTC, validation, and deterministic-identity tests**

```python
def test_runtime_event_identity_excludes_ingestion_wall_clock() -> None:
    left = RuntimeEvent.model_validate(EVENT | {"ingested_at": UTC_A})
    right = RuntimeEvent.model_validate(EVENT | {"ingested_at": UTC_B})
    assert left.event_id == right.event_id

def test_runtime_state_contains_account_positions_orders_and_feedback() -> None:
    state = RuntimeState.model_validate(COMPLETE_STATE)
    assert state.account.free_margin == 9_000.0
    assert state.exposure.net_lots_by_symbol["XAUUSD"] == 0.2
    assert state.execution_feedback[-1].status == "FILLED"
```

- [ ] **Step 2: Run tests and verify contract failures**

Run: `python -m pytest tests/test_runtime_state.py -v`

Expected: collection fails because `axq.runtime` does not exist.

- [ ] **Step 3: Implement strict immutable schemas**

Define `RuntimeEventType` values `M5_CLOSED`, `HTF_CLOSED`, `TICK`, `M1_CLOSED`,
`ACCOUNT_UPDATED`, `POSITIONS_UPDATED`, `ORDERS_UPDATED`, `EXECUTION_FEEDBACK`, and
`SLOW_CONTEXT_UPDATED`. `RuntimeEvent.event_id` is `ev-` plus the first 20 characters of a canonical
hash over event type, `observed_at`, `available_at`, source/version/sequence, symbol, and payload;
exclude `ingested_at`. Require aware UTC-normalizable timestamps and `available_at >= observed_at`.

Model the complete account and broker state from the spec using finite numeric validation. Keep
missing optional broker values as `None`; do not coerce them to zero. Make `RuntimeState.state_id`
content-derived while excluding persistence timestamps.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_runtime_state.py -v`

Expected: all runtime state tests pass.

- [ ] **Step 5: Commit the isolated contract**

```powershell
git add src/axq/runtime tests/test_runtime_state.py
git commit -m "Add deterministic runtime event and state contracts"
```

### Task 2: Clock, event source, and causal state reducer

**Files:**
- Create: `src/axq/runtime/clock.py`
- Create: `src/axq/runtime/source.py`
- Create: `src/axq/runtime/reducer.py`
- Test: `tests/test_runtime_reducer.py`

**Interfaces:**
- Consumes: Task 1 runtime contracts.
- Produces: `Clock.now() -> datetime`, `SystemUTCClock`, `ReplayClock.advance_to(datetime)`, `EventSource.events() -> Iterator[RuntimeEvent]`, `InMemoryEventSource`, and `reduce_state(previous, event) -> RuntimeState`.

- [ ] **Step 1: Write failing causal-order and immutable-reduction tests**

```python
def test_source_orders_by_availability_sequence_and_identity() -> None:
    ordered = list(InMemoryEventSource(REVERSED_EVENTS).events())
    assert ordered == sorted(ordered, key=lambda e: (e.available_at, e.source_sequence, e.event_id))

def test_reducer_does_not_mutate_previous_state() -> None:
    updated = reduce_state(BASE_STATE, ACCOUNT_EVENT)
    assert updated.account.equity != BASE_STATE.account.equity
    assert BASE_STATE.account.equity == 10_000.0
```

- [ ] **Step 2: Verify tests fail for missing reducer**

Run: `python -m pytest tests/test_runtime_reducer.py -v`

- [ ] **Step 3: Implement explicit clocks, ordered source, and pure reducer**

Reject events older than the state's last applied source sequence for the same source. Apply event
payloads by type, update freshness/last-event metadata, and derive a new `state_id`. Never call
`datetime.now()` from replay or reduction code.

- [ ] **Step 4: Verify reducer and existing data tests**

Run: `python -m pytest tests/test_runtime_reducer.py tests/test_foundation.py -v`

- [ ] **Step 5: Commit**

```powershell
git add src/axq/runtime tests/test_runtime_reducer.py
git commit -m "Add causal runtime state reduction"
```

### Task 3: Tool facts and optional predictive-model adapter

**Files:**
- Create: `src/axq/tools/__init__.py`
- Create: `src/axq/tools/contracts.py`
- Create: `src/axq/tools/catalog.py`
- Create: `src/axq/tools/optional_ml.py`
- Test: `tests/test_agent_tools.py`

**Interfaces:**
- Consumes: `RuntimeState`, existing Phase 2 feature registry, and optional Phase 4 `QuantAgent`.
- Produces: `ToolFact`, `ToolRequest`, `ToolResult`, `ToolCatalog.evaluate(names, state)`, and `OptionalPredictiveModelTool.evaluate(state)`.

- [ ] **Step 1: Write failing fact provenance and no-model tests**

```python
def test_tool_fact_binds_state_and_availability() -> None:
    fact = catalog.evaluate(["market.rsi"], STATE)[0]
    assert fact.state_id == STATE.state_id
    assert fact.available_at <= STATE.as_of

def test_optional_ml_absence_returns_unavailable_not_failure() -> None:
    result = OptionalPredictiveModelTool(None).evaluate(STATE)
    assert result.status == "UNAVAILABLE"
```

- [ ] **Step 2: Verify tests fail**

Run: `python -m pytest tests/test_agent_tools.py -v`

- [ ] **Step 3: Implement fact-only adapters**

Wrap existing causal outputs without recomputing formulas. Each result records tool/version,
parameters, state/feature-manifest identity, availability, value, units, quality, and missing reason.
The ML adapter converts a verified Phase 4 prediction to evidence data but never emits execution
permission and never becomes a required catalog dependency.

- [ ] **Step 4: Verify tool and Phase 2 compatibility**

Run: `python -m pytest tests/test_agent_tools.py tests/test_features_phase2.py -v`

- [ ] **Step 5: Commit**

```powershell
git add src/axq/tools tests/test_agent_tools.py
git commit -m "Expose causal facts through tool contracts"
```

### Task 4: Stateful specialist evidence contracts

**Files:**
- Create: `src/axq/agents/__init__.py`
- Create: `src/axq/agents/contracts.py`
- Create: `src/axq/agents/state.py`
- Create: `src/axq/agents/base.py`
- Test: `tests/test_agent_contracts.py`

**Interfaces:**
- Consumes: runtime state and tool results.
- Produces: `AgentEvidence`, `AgentStatus`, `ScenarioStatus`, `Invalidation`, `AgentMemory`, `SpecialistAgent.observe(state, facts, previous) -> tuple[AgentEvidence, AgentMemory]`.

- [ ] **Step 1: Write failing hypothesis, abstention, and previous-state tests**

```python
def test_agent_can_abstain_without_direction() -> None:
    evidence = AgentEvidence.model_validate(ABSTAINING_EVIDENCE)
    assert evidence.direction is None
    assert evidence.status == "INSUFFICIENT_EVIDENCE"

def test_agent_output_references_previous_hypothesis() -> None:
    assert UPDATED_EVIDENCE.previous_hypothesis_id == PRIOR_MEMORY.hypothesis_id
```

- [ ] **Step 2: Verify tests fail**

Run: `python -m pytest tests/test_agent_contracts.py -v`

- [ ] **Step 3: Implement strict evidence and memory contracts**

Require objective/version, agent/state IDs, hypothesis, optional BUY/SELL direction, confidence,
evidence for/against, uncertainty, invalidation, freshness, scenario/setup/thesis IDs, requested
tools, prior hypothesis, and abstention reason. Reject position size, lot, and risk override fields.

- [ ] **Step 4: Verify agent contracts**

Run: `python -m pytest tests/test_agent_contracts.py tests/test_foundation.py -v`

- [ ] **Step 5: Commit**

```powershell
git add src/axq/agents tests/test_agent_contracts.py
git commit -m "Add stateful specialist evidence contracts"
```

### Task 5: M5 thesis and intrabar scenario state machine

**Files:**
- Create: `src/axq/agents/scenarios.py`
- Test: `tests/test_intrabar_scenarios.py`

**Interfaces:**
- Consumes: `RuntimeEvent`, `RuntimeState`, `AgentEvidence`, `AgentMemory`.
- Produces: `update_scenario(event, evidence, previous) -> AgentMemory`.

- [ ] **Step 1: Write failing transition and leakage tests**

```python
def test_m5_close_can_establish_thesis() -> None:
    memory = update_scenario(M5_EVENT, M5_EVIDENCE, None)
    assert memory.scenario_status == "DEVELOPING"

def test_intrabar_event_can_confirm_but_not_create_thesis() -> None:
    assert update_scenario(TICK_EVENT, CONFIRMATION, EXISTING).scenario_status == "CONFIRMED"
    with pytest.raises(ValueError, match="existing thesis"):
        update_scenario(TICK_EVENT, CONFIRMATION, None)

def test_future_intrabar_mutation_does_not_change_prior_trace() -> None:
    assert replay(BASE_EVENTS).traces[:3] == replay(MUTATED_FUTURE_EVENTS).traces[:3]
```

- [ ] **Step 2: Verify tests fail**

Run: `python -m pytest tests/test_intrabar_scenarios.py -v`

- [ ] **Step 3: Implement the explicit state machine**

Allow completed M5 events to establish/update/invalidate theses. Allow tick and completed-M1 events
only to transition an existing thesis among `DEVELOPING`, `CONFIRMED`, `ENTRY_ELIGIBLE`,
`INVALIDATED`, and `EXPIRED`. Derive stable thesis/setup IDs from symbol, primary M5 availability,
agent/version, direction, and structural anchor—not wall clock or output path.

- [ ] **Step 4: Verify scenario causality**

Run: `python -m pytest tests/test_intrabar_scenarios.py tests/test_leakage.py -v`

- [ ] **Step 5: Commit**

```powershell
git add src/axq/agents/scenarios.py tests/test_intrabar_scenarios.py
git commit -m "Add causal intrabar scenario lifecycle"
```

### Task 6: Initial specialist agents and evidence bundle

**Files:**
- Create: `src/axq/agents/chart.py`
- Create: `src/axq/agents/quantitative.py`
- Create: `src/axq/agents/regime.py`
- Create: `src/axq/agents/historical.py`
- Create: `src/axq/agents/news.py`
- Create: `src/axq/runtime/kernel.py`
- Test: `tests/test_evidence_kernel.py`

**Interfaces:**
- Consumes: Tasks 1–5 contracts.
- Produces: deterministic Chart/Quant/Regime evidence, abstaining Historical/News interfaces when
  data is unavailable, `EvidenceBundle`, and `EvidenceKernel.process(event) -> EvidenceBundle`.

- [ ] **Step 1: Write failing no-ML, optional-failure, and deterministic-bundle tests**

```python
def test_quant_agent_operates_without_predictive_model() -> None:
    bundle = kernel_without_ml.process(M5_EVENT)
    assert bundle.by_agent("quant").status != "FAILED"

def test_optional_news_failure_does_not_block_bundle() -> None:
    bundle = kernel_with_failed_news.process(M5_EVENT)
    assert bundle.by_agent("news").status == "UNAVAILABLE"

def test_same_state_and_memory_produce_same_bundle_id() -> None:
    assert build_bundle().bundle_id == build_bundle().bundle_id
```

- [ ] **Step 2: Verify tests fail**

Run: `python -m pytest tests/test_evidence_kernel.py -v`

- [ ] **Step 3: Implement conservative deterministic agents and kernel**

Chart consumes existing structure/multi-timeframe facts; Quant consumes statistical facts and
optional ML evidence; Regime emits context without forced direction. Historical and News publish
`UNAVAILABLE`/abstaining evidence until an as-of provider exists. Kernel reduces the event, resolves
facts, updates memories in fixed agent order, and emits a content-addressed bundle. It does not issue
a trade, size, or execution instruction.

- [ ] **Step 4: Verify evidence behavior and old Quant contracts**

Run: `python -m pytest tests/test_evidence_kernel.py tests/test_quant_phase4.py -v --basetemp=.pytest_tmp`

- [ ] **Step 5: Commit**

```powershell
git add src/axq/agents src/axq/runtime/kernel.py tests/test_evidence_kernel.py
git commit -m "Add deterministic specialist evidence kernel"
```

### Task 7: Live-like/replay parity harness and journal

**Files:**
- Create: `src/axq/runtime/replay.py`
- Create: `src/axq/runtime/journal.py`
- Create: `database/migrations/002_agentic_runtime.sql`
- Test: `tests/test_live_replay_parity.py`
- Test: `tests/test_runtime_journal.py`

**Interfaces:**
- Consumes: canonical event source and evidence kernel.
- Produces: `run_event_stream(source, kernel, clock) -> list[EvidenceBundle]`, `RuntimeJournal.append_event`, `append_state`, `append_evidence`, and immutable replay readers.

- [ ] **Step 1: Write failing adapter-parity and journal-roundtrip tests**

```python
def test_live_like_and_replay_adapters_produce_identical_evidence() -> None:
    assert run_live_like(CANONICAL_EVENTS) == run_replay(CANONICAL_EVENTS)

def test_journal_roundtrip_preserves_event_order_and_hashes(tmp_path: Path) -> None:
    journal = RuntimeJournal(tmp_path / "runtime.sqlite3")
    journal.append_events(CANONICAL_EVENTS)
    assert journal.read_events() == CANONICAL_EVENTS
```

- [ ] **Step 2: Verify tests fail**

Run: `python -m pytest tests/test_live_replay_parity.py tests/test_runtime_journal.py -v`

- [ ] **Step 3: Implement one shared stream runner and additive storage**

The live-like fixture preserves arrival order while the replay reader restores canonical causal
order. Both invoke the same kernel. Migration 002 adds runtime events/states, richer agent evidence,
scenario transitions, and evidence bundles without modifying Phase 4 tables.

- [ ] **Step 4: Verify parity, migrations, and replay prefix invariance**

Run: `python -m pytest tests/test_live_replay_parity.py tests/test_runtime_journal.py tests/test_database_migrations.py -v`

- [ ] **Step 5: Commit**

```powershell
git add src/axq/runtime/replay.py src/axq/runtime/journal.py database/migrations/002_agentic_runtime.sql tests/test_live_replay_parity.py tests/test_runtime_journal.py
git commit -m "Add deterministic replay parity and runtime journal"
```

### Task 8: Phase 6 documentation and lightweight verification (completion)

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`
- Modify: `docs/runbook.md`
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Consumes: completed Phase 6 contracts and tests.
- Produces: exact local smoke/replay commands and refreshed durable project context.

- [ ] **Step 1: Document the implemented event/state schemas and tiny parity fixture**

Record exact event ordering, M5/intrabar rules, missing broker-state behavior, optional-agent failure
behavior, journal paths, and the boundary that leaves Master/Discipline/Risk/execution for Phase 7.

- [ ] **Step 2: Run all lightweight checks**

```powershell
python -m pytest --basetemp=.pytest_tmp
python -m ruff check .
python -m mypy src/axq
python -m pip check
git diff --check
```

Expected: every command exits zero; tests use only synthetic event streams and tiny temporary data.

- [ ] **Step 3: Refresh Graphify incrementally**

```powershell
graphify update .
graphify query "How do live and replay share the Phase 6 evidence kernel?" --budget 2500
```

- [ ] **Step 4: Audit scope and artifacts**

Confirm no runtime databases, replay outputs, broker data, model artifacts, credentials, or temporary
files are staged. Confirm Phase 3–5 source changes are absent unless required by a reviewed additive
compatibility fix.

- [ ] **Step 5: Commit the Phase 6 vertical slice checkpoint**

```powershell
git add README.md docs graphify-out/graph.json graphify-out/GRAPH_REPORT.md
git commit -m "Complete Phase 6 deterministic agentic baseline"
```
