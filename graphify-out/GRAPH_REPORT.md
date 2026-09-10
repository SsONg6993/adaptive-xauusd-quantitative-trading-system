# Graph Report - phase-8-reflection-experience  (2026-09-11)

## Corpus Check
- 272 files · ~131,148 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2946 nodes · 9255 edges · 150 communities (116 shown, 33 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1359 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `973151e4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_datasets_phase3.py
- LabelDefinition
- ReflectionPolicy
- axq/features/registry.py
- trainer.py
- indicators.py
- agents/__init__.py
- update_scenario
- development/config.py
- axq/config.py
- test_runtime_orchestration.py
- evaluate_predictions
- ExperimentTracker
- logging.py
- download_mt5.py
- policy.py
- data/__init__.py
- axq/__init__.py
- adaptive-xauusd-trader
- compute.py
- drift.py
- datasets/builder.py
- runtime/journal.py
- System architecture (Phase 0-7 baseline)
- QuantAgent
- folds.py
- timedelta
- Architecture decision log
- kernel.py
- README.md
- test_risk_boundary.py
- ToolResult
- RuntimeOrchestrator
- SQLiteExecutionLedger
- ReplayClock
- Global Constraints
- attribution.py
- Phase 0-6 runbook
- default_registry
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- orchestration/contracts.py
- quant/config.py
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- position.py
- system.py
- Phase 3 label contract
- execution_boundary/__init__.py
- Repository instructions
- _context
- orchestration/__init__.py
- agents/README.md
- backtest/README.md
- datasets/README.md
- evaluation/README.md
- execution/README.md
- master/README.md
- models/README.md
- monitoring/README.md
- mt5/README.md
- risk/README.md
- training/README.md
- tuning/README.md
- evaluate_discipline
- runner.py
- Tool-Augmented Agentic Architecture
- Global Constraints
- RunStateStore
- schemas.py
- EntryGateway
- OperatorControls
- test_execution_boundary.py
- snapshot.py
- SQLiteRuntimeJournal
- ensure_utc
- test_feature_formulas.py
- mt5/__init__.py
- fusion.py
- Global Constraints
- Database
- processor.py
- Global Constraints
- ExecutionIntent
- AgentEvidence
- CausalFeatureSnapshot
- Phase 7 deterministic runtime orchestration
- _context
- InMemoryPositionActionTransportLedger
- Global Constraints
- MetaTrader5Gateway
- evidence
- features/analysis.py
- FakeRunner
- position_management/contracts.py
- SnapshotGateway
- canonical_hash
- .__init__
- Phase 7 Task 7: Position Action Safety and Journal Plan
- MT5Gateway
- PositionGateway
- FakeGateway
- Position action safety
- FakeMT5Module
- daily.py
- MasterProposal
- replay.py
- _MT5Module
- test_foundation.py
- session_features
- ExperienceProvenance
- build_mt5_dataset.py
- Global Constraints
- service.py
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- DatasetManifest
- Global constraints
- Signal
- EvidenceBundle
- model_validator
- SQLitePositionActionTransportLedger
- test_daily_reflection.py
- RuntimeEvent
- Phase 5 local Quant experiment workflow
- DecisionCycle
- test_reflection_cli.py
- Phase 8 Task 2 Deterministic Daily Reflection Design
- Global Constraints
- .from_paths
- .normalize_validate_and_bind_identity
- Deterministic Daily Reflection
- Phase 3 dataset contract
- model_validator
- test_reflection_contracts.py
- model_validator
- .bind_identity
- model_validator
- .validate_and_bind_identity
- .bind_identity
- .validate_and_bind_identity
- FakeSnapshotProvider
- .validate_and_bind_identity
- .bind_identity
- .validate_event
- .validate_and_bind_identity

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 121 edges
2. `RuntimeEvent` - 92 edges
3. `Signal` - 88 edges
4. `ExecutionIntent` - 64 edges
5. `ExecutionResult` - 55 edges
6. `run_system_replay()` - 50 edges
7. `SQLiteExecutionLedger` - 48 edges
8. `reduce_state()` - 48 edges
9. `ComponentFreshness` - 47 edges
10. `ToolResult` - 46 edges

## Surprising Connections (you probably didn't know these)
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_walk_forward_split_definitions_are_deterministic()` --calls--> `walk_forward_splits()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_metric_fact_preserves_unavailable_separately_from_numeric_zero()` --calls--> `MetricFact`  [INFERRED]
  tests/test_reflection_contracts.py → src/axq/reflection/contracts.py
- `test_system_replay_retains_exact_attribution_journal_semantics()` --uses--> `JournalRecordType`  [INFERRED]
  tests/test_system_replay.py → src/axq/runtime/journal.py

## Import Cycles
- None detected.

## Communities (150 total, 33 thin omitted)

### Community 0 - "test_datasets_phase3.py"
Cohesion: 0.14
Nodes (20): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., build(), candles() (+12 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.09
Nodes (51): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, CollisionPolicy (+43 more)

### Community 2 - "ReflectionPolicy"
Cohesion: 0.13
Nodes (26): Namespace, DailyReflection, ReflectionPolicy, _build(), _days(), _emit(), _latest_records(), _load_policy() (+18 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.13
Nodes (17): Compatibility entry point; implementation lives in the installable axq package., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition, FeatureRegistry (+9 more)

### Community 4 - "trainer.py"
Cohesion: 0.06
Nodes (49): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., dump_artifact(), file_hash(), load_artifact(), Any (+41 more)

### Community 5 - "indicators.py"
Cohesion: 0.15
Nodes (32): aroon(), atr(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+24 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.11
Nodes (42): AgentReasoningBudget, Small shared specialist input and output-validation boundary., Validate an agent output before applying its deterministic memory transition., transition_agent(), AgentModel, AgentToolRequest, EvidencePolarity, EvidenceReference (+34 more)

### Community 7 - "update_scenario"
Cohesion: 0.25
Nodes (28): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), _agent_pair(), _create(), _event(), _market(), datetime, parametrize (+20 more)

### Community 8 - "development/config.py"
Cohesion: 0.08
Nodes (44): AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+36 more)

### Community 9 - "axq/config.py"
Cohesion: 0.21
Nodes (13): main(), AppConfig, DatabaseConfig, FeatureConfig, IpcConfig, load_config(), LoggingConfig, Any (+5 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.18
Nodes (22): DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., FakeEntryAdapter, FakePositionActionAdapter, FakeProcessor, _intent(), _market_event(), _position_action_intent() (+14 more)

### Community 11 - "evaluate_predictions"
Cohesion: 0.11
Nodes (29): evaluate_challenger_evidence(), Any, Advisory Champion/Challenger evidence contract., calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), overfitting_report(), Any (+21 more)

### Community 12 - "ExperimentTracker"
Cohesion: 0.27
Nodes (5): ExperimentTracker, Any, Connection, Path, Lightweight local SQLite experiment audit log.

### Community 13 - "logging.py"
Cohesion: 0.22
Nodes (8): Logger, LogRecord, configure_logging(), event(), JsonFormatter, Any, Path, Structured JSON-lines logging with correlation context.

### Community 14 - "download_mt5.py"
Cohesion: 0.48
Nodes (6): download(), main(), DataFrame, datetime, Download bounded historical bars from a locally running MetaTrader 5 terminal., _utc()

### Community 15 - "policy.py"
Cohesion: 0.50
Nodes (3): MissingValueReason, StrEnum, Feature availability and missing-value policy contracts.

### Community 20 - "compute.py"
Cohesion: 0.09
Nodes (24): main(), Inspect bounded MT5 history without downloading a production dataset., main(), Report local compute and optional ML library capabilities., compute_report(), _lightgbm_gpu_probe(), _memory_bytes(), _nvidia_probe() (+16 more)

### Community 21 - "drift.py"
Cohesion: 0.33
Nodes (13): _categorical_distribution(), distribution_drift(), feature_drift_report(), _finite(), ks_statistic(), psi(), Any, DataFrame (+5 more)

### Community 22 - "datasets/builder.py"
Cohesion: 0.06
Nodes (51): CompletedProcess, main(), main(), _git_identity(), main(), _run_git(), DataFrame, Leakage-safe multi-timeframe alignment. (+43 more)

### Community 23 - "runtime/journal.py"
Cohesion: 0.14
Nodes (15): append_position_action_chain(), Idempotent append-only journaling for the position-management action chain., Append missing deterministic chain records and return their durable entries., JournalEntry, JournalRecord, BaseModel, JournalSemantic, model_validator (+7 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "QuantAgent"
Cohesion: 0.20
Nodes (11): evaluate_saved_run(), Any, Reproduce frozen split metrics without fitting or retraining., Any, datetime, ndarray, Series, QuantAgent (+3 more)

### Community 26 - "folds.py"
Cohesion: 0.20
Nodes (17): _aggregate_fold_metrics(), completed_fold_summary(), DevelopmentFoldResult, fold_identity(), Any, DataFrame, Path, Fresh-state, fold-local development evaluation before immutable final OOS. (+9 more)

### Community 27 - "timedelta"
Cohesion: 0.06
Nodes (98): Bridge typed execution results into the shared Phase 6 runtime path., position_action_result_to_runtime_event(), Dedicated append-only transport contracts for safe position actions., datetime, StrEnum, Canonical runtime event envelopes for live and deterministic replay., RuntimeEventType, Versioned contracts and deterministic reduction for live and replay. (+90 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.06
Nodes (31): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+23 more)

### Community 29 - "kernel.py"
Cohesion: 0.20
Nodes (20): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, fact_map(), Interpretation, numeric(), ObservedFact (+12 more)

### Community 30 - "README.md"
Cohesion: 0.22
Nodes (4): Model registry and promotion contract, Phase 5 development layer, Quant model training, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.07
Nodes (60): FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool, fact_name() (+52 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.16
Nodes (7): RuntimeStatus, JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe., Perform at most one read-only refresh when the bounded cadence elapsed., Own ordering and gates while delegating every trading semantic decision., RuntimeOrchestrator, test_runtime_status_rejects_naive_time_and_is_content_addressed()

### Community 34 - "SQLiteExecutionLedger"
Cohesion: 0.13
Nodes (24): Connection, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, broker_snapshot_runtime_events(), ExecutionTransition, _intent(), _link(), _position() (+16 more)

### Community 35 - "ReplayClock"
Cohesion: 0.36
Nodes (18): Explicitly advanced deterministic replay clock., ReplayClock, JournalRecordType, _event(), _kernel(), datetime, _scenario_transition(), _snapshot() (+10 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "attribution.py"
Cohesion: 0.12
Nodes (39): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+31 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.11
Nodes (18): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+10 more)

### Community 39 - "default_registry"
Cohesion: 0.08
Nodes (27): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars., Feature functions and registry., multi_timeframe_features(), Any, DataFrame (+19 more)

### Community 40 - "Phase 2 feature contract"
Cohesion: 0.25
Nodes (8): Implemented configurable candidate families, Manifest and diagnostics, Missing-value policy, Multi-timeframe and UTC rules, Phase 2 feature contract, Point-in-time invariant, Swing and structure timing, Warm-up policy

### Community 41 - "Phase 5 Quant Model-Development Design"
Cohesion: 0.25
Nodes (7): Architectural boundary, Artifacts and recovery, Components, Data and control flow, Phase 5 Quant Model-Development Design, Purpose, Safety constraints

### Community 42 - "Project status"
Cohesion: 0.25
Nodes (7): Current architecture, Current phase status, Important risks, Project status, Roadmap, Verified state, Working principle and next task

### Community 43 - "SQLiteExperienceStore"
Cohesion: 0.12
Nodes (21): AttributionSources, ExperienceBuild, BaseModel, Experience, ExperienceType, _emit(), main(), _parser() (+13 more)

### Community 44 - "orchestration/contracts.py"
Cohesion: 0.21
Nodes (23): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+15 more)

### Community 45 - "quant/config.py"
Cohesion: 0.07
Nodes (38): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+30 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.28
Nodes (21): ChartAgent, _input(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure(), test_chart_agent_represents_hierarchical_mtf_conflict_as_uncertainty() (+13 more)

### Community 49 - "position.py"
Cohesion: 0.17
Nodes (16): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), Demo-only MetaTrader 5 transport for Task 7 position-action intents., Idempotently translate an already-safe position action to exact MT5 calls. (+8 more)

### Community 50 - "system.py"
Cohesion: 0.06
Nodes (61): EntryDecisionInputs, BaseModel, Causal contexts supplied by the runtime-specific context adapter., _identity(), _PendingClose, PendingReplayEntry, _PendingStop, datetime (+53 more)

### Community 51 - "Phase 3 label contract"
Cohesion: 0.40
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "execution_boundary/__init__.py"
Cohesion: 0.11
Nodes (42): Deterministic entry execution boundary downstream of financial Risk., Append-only SQLite execution ledger and recovery anchors., evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis (+34 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.17
Nodes (36): default_demo_position_management_policy(), evaluate_position(), Return conservative deterministic demo defaults, not optimized strategy truth., Evaluate one open position without mutating state or invoking execution…, _broker_constraints(), _context(), _fresh(), _intent() (+28 more)

### Community 55 - "orchestration/__init__.py"
Cohesion: 0.21
Nodes (13): load_runtime_config(), BaseModel, Path, Strict operational configuration for the Phase 7 runtime service., RuntimeConfig, StrEnum, RuntimeMode, StartupPhase (+5 more)

### Community 68 - "evaluate_discipline"
Cohesion: 0.26
Nodes (34): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., _context(), _policy(), _proposal(), parametrize (+26 more)

### Community 69 - "runner.py"
Cohesion: 0.08
Nodes (42): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+34 more)

### Community 70 - "Tool-Augmented Agentic Architecture"
Cohesion: 0.09
Nodes (22): Deferred risks, Event model and causality, Existing components reused, Explicitly unimplemented after Phase 7 Task 9, Explicitly untouched, Implemented shared path and future paths, Invariants, Live/replay ports (+14 more)

### Community 71 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 6 Tool-Augmented Agentic Baseline Implementation Plan, Task 1: Canonical runtime events and shared state, Task 2: Clock, event source, and causal state reducer, Task 3: Tool facts and optional predictive-model adapter, Task 4: Stateful specialist evidence contracts, Task 5: M5 thesis and intrabar scenario state machine, Task 6: Initial specialist agents and evidence bundle (+2 more)

### Community 72 - "RunStateStore"
Cohesion: 0.42
Nodes (3): Any, Path, RunStateStore

### Community 73 - "schemas.py"
Cohesion: 0.15
Nodes (12): ExecutionInstruction, MarketRegime, MasterDecision, BaseModel, datetime, field_validator, model_validator, StrEnum (+4 more)

### Community 74 - "EntryGateway"
Cohesion: 0.12
Nodes (21): default_execution_policy(), Return the conservative, execution-disabled baseline policy., ExecutionMode, _adapter(), _constants(), EntryGateway, _intent(), _policy() (+13 more)

### Community 75 - "OperatorControls"
Cohesion: 0.29
Nodes (3): OperatorControls, Monotonic operator gates: callers cannot use this contract to bypass safety., test_operator_controls_only_become_more_conservative()

### Community 76 - "test_execution_boundary.py"
Cohesion: 0.14
Nodes (32): InMemoryExecutionLedger, RuntimeError, Submission may have reached the broker and requires reconciliation., Tiny ledger reference implementation; persistent ports can implement the…, UnknownSubmissionState, execution_result_to_runtime_event(), Convert actionable execution feedback; local NO_ACTION stays local., _adapter() (+24 more)

### Community 77 - "snapshot.py"
Cohesion: 0.20
Nodes (21): BrokerObjectKind, MT5PersistedIntentLink, MT5SnapshotError, Narrow contracts isolating the optional MetaTrader5 package., A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider (+13 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.18
Nodes (13): Connection, Path, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., SQLiteRuntimeJournal, _event(), datetime, _snapshot() (+5 more)

### Community 79 - "ensure_utc"
Cohesion: 0.12
Nodes (15): Collection, ScenarioTransition, ensure_utc(), datetime, Protocol, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Clock contract used outside the pure reducer. (+7 more)

### Community 80 - "test_feature_formulas.py"
Cohesion: 0.23
Nodes (11): skipif, money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility() (+3 more)

### Community 81 - "mt5/__init__.py"
Cohesion: 0.25
Nodes (6): MT5Constants, MT5SymbolMapping, BaseModel, Optional, demo-safe MetaTrader5 gateway and adapters., test_symbol_mapping_is_explicit_auditable_and_deterministic(), _constants()

### Community 82 - "fusion.py"
Cohesion: 0.17
Nodes (29): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion., SpecialistContribution (+21 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "Database"
Cohesion: 0.13
Nodes (9): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Path, Path, Path (+1 more)

### Community 85 - "processor.py"
Cohesion: 0.16
Nodes (29): DeterministicDecisionProcessor, Concrete composition of existing deterministic Phase 7 decision boundaries., Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, Compose existing pure functions; adapters provide causal context only., PositionActionContext, PositionActionModel, PositionActionPolicy, PositionActionReason (+21 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "ExecutionIntent"
Cohesion: 0.11
Nodes (31): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, ExecutionTransport, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics., Process one immutable intent idempotently. (+23 more)

### Community 88 - "AgentEvidence"
Cohesion: 0.15
Nodes (12): AgentInput, model_validator, Protocol, Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., SpecialistAgent, validate_agent_output(), AgentEvidence (+4 more)

### Community 89 - "CausalFeatureSnapshot"
Cohesion: 0.28
Nodes (5): CausalFeatureSnapshot, Any, FactScalar, field_validator, _kernel_fixture()

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "_context"
Cohesion: 0.17
Nodes (32): default_position_action_policy(), Return conservative deterministic V1 safety defaults., PositionSide, _context(), _evaluate(), _fresh(), _intent(), _management() (+24 more)

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "MetaTrader5Gateway"
Cohesion: 0.15
Nodes (11): MT5ConnectionError, RuntimeError, The terminal package or connected terminal is unavailable., _load_mt5(), _mapping(), _mappings(), MetaTrader5Gateway, Path (+3 more)

### Community 95 - "evidence"
Cohesion: 0.15
Nodes (20): HypothesisInvalidation, model_validator, evidence(), datetime, parametrize, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields(), test_agent_evidence_identity_is_deterministic_and_round_trips() (+12 more)

### Community 96 - "features/analysis.py"
Cohesion: 0.25
Nodes (17): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+9 more)

### Community 98 - "position_management/contracts.py"
Cohesion: 0.20
Nodes (19): MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy, PositionManagementReason, PositionManagementResult, BaseModel (+11 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.15
Nodes (8): _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_creates_canonical_events_and_reduces_through_shared_path(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket(), test_snapshot_maps_account_market_books_exposure_and_constraints()

### Community 100 - "canonical_hash"
Cohesion: 0.21
Nodes (3): model_validator, canonical_hash(), Any

### Community 101 - ".__init__"
Cohesion: 0.50
Nodes (3): EntryContextProvider, PositionActionContextProvider, PositionContextProvider

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "MT5Gateway"
Cohesion: 0.08
Nodes (27): The transport failed before submission could be accepted., TransportFailure, MT5Gateway, Protocol, MT5ExecutionTransport, datetime, Translate one validated entry intent into one non-retried MT5 submission., datetime (+19 more)

### Community 104 - "PositionGateway"
Cohesion: 0.15
Nodes (14): _adapter(), _constants(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send() (+6 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "FakeMT5Module"
Cohesion: 0.13
Nodes (5): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity()

### Community 108 - "daily.py"
Cohesion: 0.26
Nodes (25): FindingCategory, FindingSignal, MetricFact, BaseModel, StrEnum, Immutable content-addressed contracts for deterministic daily reflection., ReflectionFinding, ReflectionModel (+17 more)

### Community 109 - "MasterProposal"
Cohesion: 0.14
Nodes (31): build_execution_intent(), RiskContext, Pure construction of provenance-bound execution intents., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links(), _progressed_to(), MasterProposal, BaseModel (+23 more)

### Community 110 - "replay.py"
Cohesion: 0.15
Nodes (12): JournalOutcome, JournalOutcomeStatus, StrEnum, Exception, JournalSemantic, One shared event-stream harness for live-like and replay adapters., Feed one source/clock adapter through the unchanged shared kernel., Restore durable thesis continuity before accepting a new event. (+4 more)

### Community 112 - "test_foundation.py"
Cohesion: 0.13
Nodes (14): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., Deterministic pre-trade veto and broker-specification position sizing., RiskContext, RiskLimits, veto_reasons() (+6 more)

### Community 113 - "session_features"
Cohesion: 0.23
Nodes (10): _local_window(), Any, DataFrame, Series, DST-aware session features. Source timestamps are interpreted as UTC., session_features(), test_london_and_new_york_dst_transitions(), test_manifest_is_reproducible_and_complete() (+2 more)

### Community 114 - "ExperienceProvenance"
Cohesion: 0.16
Nodes (14): ExperienceProvenance, model_validator, _rejection(), test_show_and_summary_cli_emit_json(), test_summary_is_descriptive_and_preserves_unknowns(), _trade(), _decision(), _provenance() (+6 more)

### Community 115 - "build_mt5_dataset.py"
Cohesion: 0.31
Nodes (8): HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel, Path, Explicit user-run MT5 multi-timeframe download and immutable dataset build.

### Community 116 - "Global Constraints"
Cohesion: 0.22
Nodes (8): Global Constraints, Phase 8 Task 1 Experience Store Implementation Plan, Task 1: Experience contracts, Task 2: Append-only SQLite store, Task 3: Durable replay outcome artifact, Task 4: Exact-link outcome attribution, Task 5: Descriptive analytics and CLI, Task 6: Baseline ingestion and final verification

### Community 117 - "service.py"
Cohesion: 0.14
Nodes (11): BrokerSnapshotProvider, DecisionCycleProcessor, datetime, Protocol, Deterministic composition service for the completed Phase 6/7 boundaries., RuntimeRunner, BaseModel, Expose the immutable current state for orchestration and diagnostics. (+3 more)

### Community 118 - "Phase 8 Task 1 Experience Store Design"
Cohesion: 0.22
Nodes (8): Attribution, CLI and analytics, Contracts, Persistence, Phase 8 Task 1 Experience Store Design, Scope, Source authority, Validation

### Community 119 - "Phase 7 Task 8 Direct MT5 Transport Design"
Cohesion: 0.22
Nodes (8): Boundaries, Deferred work, Idempotency and persistence, Phase 7 Task 8 Direct MT5 Transport Design, Requests and response mapping, Safety and modes, Scope, Snapshots and causality

### Community 120 - "DatasetManifest"
Cohesion: 0.25
Nodes (4): DatasetManifest, BaseModel, Path, PersistenceAndConfigTests

### Community 121 - "Global constraints"
Cohesion: 0.25
Nodes (7): Global constraints, Phase 7 Task 8 Direct MT5 Transport Implementation Plan, Task 1: Gateway and normalized MT5 contracts, Task 2: Canonical broker snapshots, Task 3: Entry transport and complete dry-run preflight, Task 4: Durable position-action transport, Task 5: Documentation, optional read-only smoke, and final verification

### Community 122 - "Signal"
Cohesion: 0.35
Nodes (16): Signal, _contribution(), _discipline(), _evidence(), _intent(), _master(), _of_type(), _result() (+8 more)

### Community 123 - "EvidenceBundle"
Cohesion: 0.18
Nodes (6): EvidenceBundle, EvidenceKernel, BaseModel, Restore committed semantic state before the next event is processed., Reduce a non-decision state refresh without invoking specialists., Reduce an event, resolve bounded facts, and update specialists in fixed order.

### Community 125 - "SQLitePositionActionTransportLedger"
Cohesion: 0.32
Nodes (6): Append-only SQLite ledger for position-action transport outcomes., SQLitePositionActionTransportLedger, PositionActionTransportTransition, PositionActionTransportTransitionType, BaseModel, StrEnum

### Community 126 - "test_daily_reflection.py"
Cohesion: 0.39
Nodes (11): _agent(), _findings(), _management(), _provenance(), datetime, _rejection(), test_agent_position_and_runtime_anomaly_findings_use_exact_daily_sources(), test_daily_aggregation_detects_confidence_excursion_and_rejection_patterns() (+3 more)

### Community 127 - "RuntimeEvent"
Cohesion: 0.16
Nodes (11): BaseModel, RuntimeEvent, JournalEventSource, Canonical event source reconstructed from append-only journal records., EventSource, InMemoryEventSource, Protocol, Deterministically ordered runtime-event sources. (+3 more)

### Community 128 - "Phase 5 local Quant experiment workflow"
Cohesion: 0.67
Nodes (3): Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review

### Community 129 - "DecisionCycle"
Cohesion: 0.38
Nodes (6): DecisionCycle, OutcomeCount, BaseModel, Auditable classifications emitted by the existing decision boundaries., RuntimeRunSummary, test_summary_is_deterministic_and_counts_existing_results()

### Community 130 - "test_reflection_cli.py"
Cohesion: 0.35
Nodes (10): main(), _parser(), ArgumentParser, _decision(), _experience_store(), Path, test_build_range_is_deterministic_and_idempotent(), test_build_rejects_reversed_date_range() (+2 more)

### Community 131 - "Phase 8 Task 2 Deterministic Daily Reflection Design"
Cohesion: 0.22
Nodes (8): Causal period rule, CLI, Contracts, Deterministic diagnostics, Persistence and supersession, Phase 8 Task 2 Deterministic Daily Reflection Design, Scope, Validation

### Community 132 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 2 Deterministic Daily Reflection Implementation Plan, Task 1: Reflection contracts and policy, Task 2: Pure daily aggregation, Task 3: Append-only reflection persistence, Task 4: Build orchestration and CLI, Task 5: Baseline validation and durable context

### Community 133 - ".from_paths"
Cohesion: 0.32
Nodes (6): _deduplicate(), _index(), Connection, Path, _read_only(), T

### Community 135 - "Deterministic Daily Reflection"
Cohesion: 0.33
Nodes (5): Causal contract, Deterministic Daily Reflection, Diagnostic families, Persistence, Verified baseline

### Community 136 - "Phase 3 dataset contract"
Cohesion: 0.33
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 138 - "test_reflection_contracts.py"
Cohesion: 0.60
Nodes (5): _finding(), _guard(), test_daily_reflection_normalizes_children_and_binds_supersession(), test_metric_fact_preserves_unavailable_separately_from_numeric_zero(), test_policy_and_nested_contracts_have_stable_content_identities()

## Knowledge Gaps
- **231 isolated node(s):** `adaptive-xauusd-trader`, `Repository-start workflow`, `Graphify`, `Current capabilities`, `Setup (Windows PowerShell)` (+226 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 809 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `LabelDefinition`, `ReflectionPolicy`, `trainer.py`, `agents/__init__.py`, `.normalize_validate_and_bind_identity`, `development/config.py`, `model_validator`, `model_validator`, `.bind_identity`, `model_validator`, `.validate_and_bind_identity`, `.bind_identity`, `.validate_and_bind_identity`, `.validate_and_bind_identity`, `.bind_identity`, `.validate_event`, `.validate_and_bind_identity`, `datasets/builder.py`, `runtime/journal.py`, `folds.py`, `timedelta`, `kernel.py`, `ToolResult`, `attribution.py`, `SQLiteExperienceStore`, `orchestration/contracts.py`, `quant/config.py`, `system.py`, `execution_boundary/__init__.py`, `runner.py`, `snapshot.py`, `fusion.py`, `processor.py`, `ExecutionIntent`, `AgentEvidence`, `evidence`, `position_management/contracts.py`, `daily.py`, `MasterProposal`, `replay.py`, `ExperienceProvenance`, `DatasetManifest`, `model_validator`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `test_reflection_cli.py`, `trainer.py`, `test_runtime_orchestration.py`, `QuantAgent`, `timedelta`, `test_risk_boundary.py`, `SQLiteExecutionLedger`, `attribution.py`, `SQLiteExperienceStore`, `orchestration/contracts.py`, `system.py`, `execution_boundary/__init__.py`, `_context`, `evaluate_discipline`, `schemas.py`, `EntryGateway`, `test_execution_boundary.py`, `fusion.py`, `processor.py`, `ExecutionIntent`, `_context`, `MT5Gateway`, `daily.py`, `MasterProposal`, `test_foundation.py`, `ExperienceProvenance`, `test_daily_reflection.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `ToolResult`, `axq/features/registry.py`, `indicators.py`, `axq/config.py`, `test_feature_formulas.py`, `session_features`, `system.py`, `test_foundation.py`, `datasets/builder.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 118 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 118 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 66 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 66 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ExecutionIntent` (e.g. with `DemoExecutionAdapter` and `ExecutionAdapter`) actually correct?**
  _`ExecutionIntent` has 9 INFERRED edges - model-reasoned connections that need verification._