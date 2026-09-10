# Graph Report - phase-8-reflection-experience  (2026-09-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2821 nodes · 8860 edges · 132 communities (109 shown, 22 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 1276 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `512feefe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- datasets/__init__.py
- LabelDefinition
- LocalModelRegistry
- axq/features/registry.py
- trainer.py
- indicators.py
- system.py
- timedelta
- development/config.py
- axq/config.py
- test_runtime_orchestration.py
- diagnostics.py
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
- RuntimeEvent
- Architecture decision log
- _deterministic.py
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
- ExecutionIntent
- processor.py
- quant/config.py
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- position.py
- run_system_replay
- Phase 3 label contract
- recovery_contracts.py
- Repository instructions
- _context
- RuntimeConfig
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
- momentum_features
- MT5SymbolMapping
- Signal
- Global Constraints
- SQLitePositionActionTransportLedger
- position_actions/evaluator.py
- Global Constraints
- execution_boundary/__init__.py
- statistical_features
- CausalFeatureSnapshot
- Phase 7 deterministic runtime orchestration
- _context
- InMemoryPositionActionTransportLedger
- Global Constraints
- MetaTrader5Gateway
- FreshnessStatus
- features/analysis.py
- FakeRunner
- test_agent_tools.py
- SnapshotGateway
- canonical_hash
- .__init__
- Phase 7 Task 7: Position Action Safety and Journal Plan
- MT5Gateway
- PositionGateway
- FakeGateway
- Position action safety
- FakeMT5Module
- breakout_features
- MasterProposal
- RuntimeStreamRunner
- _MT5Module
- test_labels_phase3.py
- session_features
- run_event_stream
- build_mt5_dataset.py
- Global Constraints
- service.py
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- DatasetManifest
- Global constraints
- test_runtime_journal.py
- dataset_quality_report
- model_validator
- multi_timeframe_features
- volume_features
- EventSource
- Phase 5 local Quant experiment workflow
- .from_cycles
- .terminal_path
- _fresh

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 113 edges
2. `RuntimeEvent` - 92 edges
3. `Signal` - 81 edges
4. `ExecutionIntent` - 64 edges
5. `ExecutionResult` - 55 edges
6. `run_system_replay()` - 50 edges
7. `SQLiteExecutionLedger` - 48 edges
8. `reduce_state()` - 48 edges
9. `ComponentFreshness` - 47 edges
10. `ToolResult` - 46 edges

## Surprising Connections (you probably didn't know these)
- `test_system_replay_retains_exact_attribution_journal_semantics()` --uses--> `JournalRecordType`  [INFERRED]
  tests/test_system_replay.py → src/axq/runtime/journal.py
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_walk_forward_split_definitions_are_deterministic()` --calls--> `walk_forward_splits()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `tiny_dataset()` --calls--> `RowPolicy`  [INFERRED]
  tests/test_quant_development_runner.py → src/axq/datasets/config.py

## Import Cycles
- None detected.

## Communities (132 total, 22 thin omitted)

### Community 0 - "datasets/__init__.py"
Cohesion: 0.11
Nodes (25): DatasetBuildResult, Path, write_dataset(), DatasetBuildConfig, BaseModel, RowPolicy, SplitPolicy, DatasetManifest (+17 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.11
Nodes (35): compare_label_definitions(), DataFrame, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, EntryReference, LabelDefinition, LabelKind, BaseModel (+27 more)

### Community 2 - "LocalModelRegistry"
Cohesion: 0.17
Nodes (12): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., LocalModelRegistry, ModelState, Any, BaseModel (+4 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "trainer.py"
Cohesion: 0.06
Nodes (53): dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run(), write_json() (+45 more)

### Community 5 - "indicators.py"
Cohesion: 0.17
Nodes (28): aroon(), atr(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+20 more)

### Community 6 - "system.py"
Cohesion: 0.09
Nodes (48): AgentInput, AgentReasoningBudget, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition., SpecialistAgent (+40 more)

### Community 7 - "timedelta"
Cohesion: 0.09
Nodes (75): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), _agent_pair(), _create(), _event(), _market(), datetime, parametrize (+67 more)

### Community 8 - "development/config.py"
Cohesion: 0.09
Nodes (35): AblationConfig, EvaluationConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config(), load_tuning_config(), load_walk_forward_config() (+27 more)

### Community 9 - "axq/config.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.16
Nodes (23): DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., FakeEntryAdapter, FakePositionActionAdapter, FakeProcessor, FakeSnapshotProvider, _intent(), _market_event() (+15 more)

### Community 11 - "diagnostics.py"
Cohesion: 0.12
Nodes (23): ProbabilityCalibrator, ndarray, evaluate_challenger_evidence(), Any, Advisory Champion/Challenger evidence contract., calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization() (+15 more)

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
Cohesion: 0.09
Nodes (25): main(), main(), main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., DataFrame, Leakage-safe multi-timeframe alignment. (+17 more)

### Community 23 - "runtime/journal.py"
Cohesion: 0.10
Nodes (20): PositionActionModel, PositionActionSafetyOutcome, BaseModel, Immutable contracts for safe actions on authoritative open positions., append_position_action_chain(), Idempotent append-only journaling for the position-management action chain., Append missing deterministic chain records and return their durable entries., Dedicated append-only transport contracts for safe position actions. (+12 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "QuantAgent"
Cohesion: 0.28
Nodes (8): Any, datetime, ndarray, Series, QuantAgent, AgentPrediction, QuantAgentEvidenceProvider, Narrow adapter around the existing frozen Phase 4 QuantAgent.

### Community 26 - "folds.py"
Cohesion: 0.08
Nodes (37): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., chronological_split(), IndexRange (+29 more)

### Community 27 - "RuntimeEvent"
Cohesion: 0.09
Nodes (61): execution_result_to_runtime_event(), Bridge typed execution results into the shared Phase 6 runtime path., Convert actionable execution feedback; local NO_ACTION stays local., broker_snapshot_runtime_events(), Strict contracts for the deterministic financial Risk boundary., BaseModel, datetime, StrEnum (+53 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.06
Nodes (30): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+22 more)

### Community 29 - "_deterministic.py"
Cohesion: 0.15
Nodes (27): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, EvidencePolarity, EvidenceReference, HypothesisRelationship, StrEnum (+19 more)

### Community 30 - "README.md"
Cohesion: 0.14
Nodes (10): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability, Model registry and promotion contract, Phase 5 development layer (+2 more)

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.08
Nodes (66): BaseModel, model_validator, StrEnum, RiskBoundaryModel, RiskContext, RiskOutcome, RiskPolicy, RiskReason (+58 more)

### Community 32 - "ToolResult"
Cohesion: 0.15
Nodes (29): datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool, fact_name(), FeatureValue (+21 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.17
Nodes (6): RuntimeStatus, JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe., Perform at most one read-only refresh when the bounded cadence elapsed., Own ordering and gates while delegating every trading semantic decision., RuntimeOrchestrator

### Community 34 - "SQLiteExecutionLedger"
Cohesion: 0.13
Nodes (21): Connection, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, ExecutionTransition, _fresh(), _intent(), _link(), _position() (+13 more)

### Community 35 - "ReplayClock"
Cohesion: 0.27
Nodes (20): Explicitly advanced deterministic replay clock., ReplayClock, JournalRecordType, InMemoryEventSource, Small deterministic source used by replay and contract tests., _event(), _kernel(), datetime (+12 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "attribution.py"
Cohesion: 0.05
Nodes (81): ArgumentParser, _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation. (+73 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.12
Nodes (17): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+9 more)

### Community 39 - "default_registry"
Cohesion: 0.16
Nodes (16): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., price_action_features(), Any, DataFrame, default_registry() (+8 more)

### Community 40 - "Phase 2 feature contract"
Cohesion: 0.25
Nodes (8): Implemented configurable candidate families, Manifest and diagnostics, Missing-value policy, Multi-timeframe and UTC rules, Phase 2 feature contract, Point-in-time invariant, Swing and structure timing, Warm-up policy

### Community 41 - "Phase 5 Quant Model-Development Design"
Cohesion: 0.25
Nodes (7): Architectural boundary, Artifacts and recovery, Components, Data and control flow, Phase 5 Quant Model-Development Design, Purpose, Safety constraints

### Community 42 - "Project status"
Cohesion: 0.25
Nodes (7): Current architecture, Current phase status, Important risks, Project status, Roadmap, Verified state, Working principle and next task

### Community 43 - "ExecutionIntent"
Cohesion: 0.15
Nodes (11): DemoExecutionAdapter, ExecutionLedger, InMemoryExecutionLedger, datetime, Process one immutable intent idempotently., Tiny ledger reference implementation; persistent ports can implement the…, Guarded demo adapter; never permits a live-account submission., ExecutionIntent (+3 more)

### Community 44 - "processor.py"
Cohesion: 0.14
Nodes (28): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+20 more)

### Community 45 - "quant/config.py"
Cohesion: 0.07
Nodes (40): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+32 more)

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
Cohesion: 0.15
Nodes (17): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), datetime, Demo-only MetaTrader 5 transport for Task 7 position-action intents. (+9 more)

### Community 50 - "run_system_replay"
Cohesion: 0.05
Nodes (65): _identity(), _PendingClose, PendingReplayEntry, _PendingStop, datetime, StrEnum, Deterministic, transport-only fill mechanics for system replay., A causal fill book; it contains no signal or policy decisions. (+57 more)

### Community 51 - "Phase 3 label contract"
Cohesion: 0.33
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "recovery_contracts.py"
Cohesion: 0.11
Nodes (34): evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis, _conflict_reason(), _finding() (+26 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.10
Nodes (55): StrEnum, ReconciliationKind, ResumeStatus, MissingEvidenceBehavior, PositionManagementContext, PositionManagementPolicy, PositionManagementReason, PositionManagementResult (+47 more)

### Community 55 - "RuntimeConfig"
Cohesion: 0.25
Nodes (9): load_runtime_config(), BaseModel, Path, RuntimeConfig, build_mt5_gateway(), Build the lazy gateway; operational paths are not semantic identity., test_checked_in_runtime_config_is_strict_and_disabled(), test_explicit_terminal_path_is_forwarded_without_entering_config_identity() (+1 more)

### Community 68 - "evaluate_discipline"
Cohesion: 0.26
Nodes (34): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., _context(), _policy(), _proposal(), parametrize (+26 more)

### Community 69 - "runner.py"
Cohesion: 0.09
Nodes (38): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+30 more)

### Community 70 - "Tool-Augmented Agentic Architecture"
Cohesion: 0.09
Nodes (22): Deferred risks, Event model and causality, Existing components reused, Explicitly unimplemented after Phase 7 Task 9, Explicitly untouched, Implemented shared path and future paths, Invariants, Live/replay ports (+14 more)

### Community 71 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 6 Tool-Augmented Agentic Baseline Implementation Plan, Task 1: Canonical runtime events and shared state, Task 2: Clock, event source, and causal state reducer, Task 3: Tool facts and optional predictive-model adapter, Task 4: Stateful specialist evidence contracts, Task 5: M5 thesis and intrabar scenario state machine, Task 6: Initial specialist agents and evidence bundle (+2 more)

### Community 72 - "RunStateStore"
Cohesion: 0.18
Nodes (11): Any, Path, Atomic, identity-bound state for resumable local experiments., RunStateStore, experiment_payload(), parametrize, Path, test_experiment_config_is_strict_and_content_addressed() (+3 more)

### Community 73 - "schemas.py"
Cohesion: 0.14
Nodes (13): ExecutionInstruction, MarketRegime, MasterDecision, BaseModel, datetime, field_validator, model_validator, StrEnum (+5 more)

### Community 74 - "EntryGateway"
Cohesion: 0.14
Nodes (18): _adapter(), _constants(), EntryGateway, _intent(), _policy(), datetime, Exception, parametrize (+10 more)

### Community 75 - "OperatorControls"
Cohesion: 0.29
Nodes (3): OperatorControls, Monotonic operator gates: callers cannot use this contract to bypass safety., test_operator_controls_only_become_more_conservative()

### Community 76 - "test_execution_boundary.py"
Cohesion: 0.23
Nodes (25): _adapter(), _intent(), _observation(), _policy(), Exception, parametrize, _report(), ScriptedTransport (+17 more)

### Community 77 - "snapshot.py"
Cohesion: 0.19
Nodes (21): BrokerObjectKind, MT5SnapshotError, RuntimeError, A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider, _optional_float() (+13 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.13
Nodes (11): JournalEntry, Connection, JournalSemantic, Path, UTCDateTime, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., _semantic_id() (+3 more)

### Community 79 - "ensure_utc"
Cohesion: 0.25
Nodes (6): ensure_utc(), datetime, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Live clock backed by the host system clock., SystemUTCClock

### Community 80 - "momentum_features"
Cohesion: 0.26
Nodes (11): skipif, rsi(), momentum_features(), Any, DataFrame, fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility() (+3 more)

### Community 81 - "MT5SymbolMapping"
Cohesion: 0.25
Nodes (4): MT5SymbolMapping, BaseModel, model_validator, test_symbol_mapping_is_explicit_auditable_and_deterministic()

### Community 82 - "Signal"
Cohesion: 0.15
Nodes (31): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, BaseModel, model_validator, StrEnum, Immutable contracts for deterministic specialist-evidence fusion. (+23 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "SQLitePositionActionTransportLedger"
Cohesion: 0.10
Nodes (14): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Path, Path, Path (+6 more)

### Community 85 - "position_actions/evaluator.py"
Cohesion: 0.20
Nodes (25): PositionActionContext, PositionActionPolicy, PositionActionReason, PositionActionSafetyResult, PositionActionType, StrEnum, _age_is_valid(), build_position_action_intent() (+17 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "execution_boundary/__init__.py"
Cohesion: 0.14
Nodes (28): ExecutionAdapter, ExecutionTransport, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics., Submission may have reached the broker and requires reconciliation., Submit an already approved intent to the execution transport., UnknownSubmissionState, BrokerExecutionReport (+20 more)

### Community 88 - "statistical_features"
Cohesion: 0.50
Nodes (3): Any, DataFrame, statistical_features()

### Community 89 - "CausalFeatureSnapshot"
Cohesion: 0.12
Nodes (9): _snapshot(), CausalFeatureSnapshot, Any, FactScalar, field_validator, model_validator, Protocol, Return causal distributional evidence without interpreting direction. (+1 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "_context"
Cohesion: 0.19
Nodes (29): PositionSide, StrEnum, _context(), _evaluate(), _fresh(), _intent(), _management(), _position() (+21 more)

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "MetaTrader5Gateway"
Cohesion: 0.16
Nodes (11): MT5ConnectionError, MT5Constants, Narrow contracts isolating the optional MetaTrader5 package., The terminal package or connected terminal is unavailable., _load_mt5(), _mapping(), _mappings(), MetaTrader5Gateway (+3 more)

### Community 95 - "FreshnessStatus"
Cohesion: 0.21
Nodes (19): FreshnessStatus, evidence(), datetime, parametrize, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields(), test_agent_evidence_identity_is_deterministic_and_round_trips(), test_agent_input_binds_tools_without_exposing_account_state() (+11 more)

### Community 96 - "features/analysis.py"
Cohesion: 0.25
Nodes (17): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+9 more)

### Community 98 - "test_agent_tools.py"
Cohesion: 0.13
Nodes (26): _catalog(), FeatureFactTool, PredictiveModelEvidenceProvider, Any, Protocol, Return label-to-probability facts without a trading decision., _ExplodingTool, _FailingProvider (+18 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.13
Nodes (9): MT5PersistedIntentLink, _constants(), _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket() (+1 more)

### Community 100 - "canonical_hash"
Cohesion: 0.07
Nodes (10): model_validator, model_validator, model_validator, model_validator, model_validator, model_validator, model_validator, model_validator (+2 more)

### Community 101 - ".__init__"
Cohesion: 0.50
Nodes (3): EntryContextProvider, PositionActionContextProvider, PositionContextProvider

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "MT5Gateway"
Cohesion: 0.08
Nodes (27): RuntimeError, The transport failed before submission could be accepted., TransportFailure, MT5Gateway, Protocol, MT5ExecutionAdapter, datetime, Compose MT5 facts/transport with the existing durable demo adapter. (+19 more)

### Community 104 - "PositionGateway"
Cohesion: 0.15
Nodes (14): _adapter(), _constants(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send() (+6 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "FakeMT5Module"
Cohesion: 0.13
Nodes (5): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity()

### Community 108 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 109 - "MasterProposal"
Cohesion: 0.22
Nodes (13): build_execution_intent(), default_execution_policy(), RiskContext, Pure construction of provenance-bound execution intents., Return the conservative, execution-disabled baseline policy., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links(), _progressed_to() (+5 more)

### Community 110 - "RuntimeStreamRunner"
Cohesion: 0.11
Nodes (15): JournalOutcome, JournalOutcomeStatus, JournalRecord, BaseModel, model_validator, StrEnum, Exception, JournalSemantic (+7 more)

### Community 112 - "test_labels_phase3.py"
Cohesion: 0.31
Nodes (13): CollisionPolicy, barrier_definition(), bars(), DataFrame, parametrize, test_direction_horizons(), test_direction_threshold_modes_and_neutral(), test_forward_simple_log_and_atr_returns() (+5 more)

### Community 113 - "session_features"
Cohesion: 0.23
Nodes (10): _local_window(), Any, DataFrame, Series, DST-aware session features. Source timestamps are interpreted as UTC., session_features(), test_london_and_new_york_dst_transitions(), test_manifest_is_reproducible_and_complete() (+2 more)

### Community 114 - "run_event_stream"
Cohesion: 0.22
Nodes (8): Collection, ScenarioTransition, Protocol, Clock contract used outside the pure reducer., Return the current instant in UTC., RuntimeClock, Run an adapter-provided stream through the one shared semantic path., run_event_stream()

### Community 115 - "build_mt5_dataset.py"
Cohesion: 0.31
Nodes (8): HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel, Path, Explicit user-run MT5 multi-timeframe download and immutable dataset build.

### Community 116 - "Global Constraints"
Cohesion: 0.22
Nodes (8): Global Constraints, Phase 8 Task 1 Experience Store Implementation Plan, Task 1: Experience contracts, Task 2: Append-only SQLite store, Task 3: Durable replay outcome artifact, Task 4: Exact-link outcome attribution, Task 5: Descriptive analytics and CLI, Task 6: Baseline ingestion and final verification

### Community 117 - "service.py"
Cohesion: 0.07
Nodes (31): Strict operational configuration for the Phase 7 runtime service., DecisionCycle, OutcomeCount, BaseModel, StrEnum, Strict orchestration-only contracts for the shared Phase 7 runtime., Auditable classifications emitted by the existing decision boundaries., RuntimeMode (+23 more)

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

### Community 122 - "test_runtime_journal.py"
Cohesion: 0.44
Nodes (8): _event(), datetime, _snapshot(), test_feature_snapshots_can_be_recovered_by_event_without_mutation(), test_journal_is_append_only_and_keeps_deterministic_order(), test_journal_replay_orders_events_by_causal_availability(), test_journal_round_trip_preserves_typed_semantic_identity(), test_rejection_outcome_is_structured_and_does_not_replace_event()

### Community 123 - "dataset_quality_report"
Cohesion: 0.33
Nodes (6): dataset_quality_report(), Any, DataFrame, label_balance(), Any, Series

### Community 125 - "multi_timeframe_features"
Cohesion: 0.50
Nodes (3): multi_timeframe_features(), Any, DataFrame

### Community 126 - "volume_features"
Cohesion: 0.50
Nodes (4): money_flow_index(), Any, DataFrame, volume_features()

### Community 127 - "EventSource"
Cohesion: 0.40
Nodes (4): EventSource, Protocol, Source of events already ordered for causal reduction., Yield events in canonical availability order.

### Community 128 - "Phase 5 local Quant experiment workflow"
Cohesion: 0.67
Nodes (3): Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review

### Community 131 - "_fresh"
Cohesion: 0.67
Nodes (3): _fresh(), datetime, test_runtime_status_rejects_naive_time_and_is_content_addressed()

## Knowledge Gaps
- **213 isolated node(s):** `Contract design`, `Documentation and graph`, `Journal integration`, `Pure evaluator`, `Scope` (+208 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 774 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `datasets/__init__.py`, `LabelDefinition`, `trainer.py`, `system.py`, `development/config.py`, `datasets/builder.py`, `runtime/journal.py`, `folds.py`, `RuntimeEvent`, `_deterministic.py`, `test_risk_boundary.py`, `ToolResult`, `attribution.py`, `processor.py`, `quant/config.py`, `run_system_replay`, `recovery_contracts.py`, `_context`, `runner.py`, `MT5SymbolMapping`, `Signal`, `SQLitePositionActionTransportLedger`, `execution_boundary/__init__.py`, `CausalFeatureSnapshot`, `MetaTrader5Gateway`, `RuntimeStreamRunner`, `service.py`, `DatasetManifest`, `model_validator`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `trainer.py`, `system.py`, `test_runtime_orchestration.py`, `QuantAgent`, `RuntimeEvent`, `test_risk_boundary.py`, `SQLiteExecutionLedger`, `attribution.py`, `ExecutionIntent`, `processor.py`, `run_system_replay`, `recovery_contracts.py`, `_context`, `evaluate_discipline`, `schemas.py`, `EntryGateway`, `test_execution_boundary.py`, `position_actions/evaluator.py`, `execution_boundary/__init__.py`, `_context`, `MT5Gateway`, `MasterProposal`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `RuntimeEvent` connect `RuntimeEvent` to `RuntimeOrchestrator`, `test_agent_tools.py`, `ReplayClock`, `canonical_hash`, `attribution.py`, `system.py`, `timedelta`, `test_runtime_orchestration.py`, `processor.py`, `SQLiteRuntimeJournal`, `RuntimeStreamRunner`, `recovery_contracts.py`, `service.py`, `runtime/journal.py`, `test_runtime_journal.py`, `EventSource`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 107 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 107 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ExecutionIntent` (e.g. with `DemoExecutionAdapter` and `ExecutionAdapter`) actually correct?**
  _`ExecutionIntent` has 9 INFERRED edges - model-reasoned connections that need verification._