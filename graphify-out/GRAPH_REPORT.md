# Graph Report - phase-8-reflection-experience  (2026-09-11)

## Corpus Check
- 284 files · ~140,659 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3090 nodes · 9746 edges · 156 communities (117 shown, 38 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1468 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6c262ff8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- build_weekly_reflection
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
- inference.py
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
- .validate_and_bind_identity
- System architecture (Phase 0-7 baseline)
- SQLiteWeeklyReflectionStore
- dataset.py
- RuntimeEvent
- Architecture decision log
- _deterministic.py
- README.md
- test_risk_boundary.py
- ToolResult
- RuntimeOrchestrator
- SQLiteExecutionLedger
- timedelta
- Global Constraints
- experience/__init__.py
- Phase 0-6 runbook
- default_registry
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- attribution.py
- folds.py
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- position.py
- system.py
- Phase 3 label contract
- recovery_contracts.py
- Repository instructions
- ComponentFreshness
- service.py
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
- Signal
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
- preflight.py
- Global Constraints
- transport.py
- position_actions/evaluator.py
- Global Constraints
- execution_boundary/__init__.py
- test_runtime_state.py
- test_agent_tools.py
- Phase 7 deterministic runtime orchestration
- _context
- InMemoryPositionActionTransportLedger
- Global Constraints
- MetaTrader5Gateway
- evidence
- features/analysis.py
- FakeRunner
- weekly_cli.py
- SnapshotGateway
- canonical_hash
- Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design
- Phase 7 Task 7: Position Action Safety and Journal Plan
- MT5Gateway
- PositionGateway
- FakeGateway
- Position action safety
- FakeMT5Module
- reflection/__init__.py
- execution_boundary/builder.py
- runtime/journal.py
- _MT5Module
- test_foundation.py
- session_features
- ExperienceProvenance
- build_mt5_dataset.py
- Global Constraints
- RuntimeRunner
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- DatasetManifest
- Global constraints
- LocalModelRegistry
- test_weekly_reflection.py
- model_validator
- model_validator
- test_daily_reflection.py
- Global Constraints
- Phase 5 local Quant experiment workflow
- InMemoryExecutionLedger
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
- Deterministic Weekly Reflection and Pattern Lifecycle
- .bind_identity
- .validate_and_bind_identity
- breakout_features
- .validate_and_bind_identity
- .bind_identity
- .validate_event
- .validate_and_bind_identity
- model_validator
- ExperienceBuild
- multi_timeframe_features
- .terminal_path
- build_mt5_gateway
- .validate_and_bind_identity

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 132 edges
2. `RuntimeEvent` - 92 edges
3. `Signal` - 90 edges
4. `ExecutionIntent` - 64 edges
5. `ExecutionResult` - 55 edges
6. `run_system_replay()` - 50 edges
7. `SQLiteExecutionLedger` - 48 edges
8. `reduce_state()` - 48 edges
9. `ComponentFreshness` - 47 edges
10. `ToolResult` - 46 edges

## Surprising Connections (you probably didn't know these)
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py
- `test_metric_fact_preserves_unavailable_separately_from_numeric_zero()` --calls--> `MetricFact`  [INFERRED]
  tests/test_reflection_contracts.py → src/axq/reflection/contracts.py
- `test_system_replay_retains_exact_attribution_journal_semantics()` --uses--> `JournalRecordType`  [INFERRED]
  tests/test_system_replay.py → src/axq/runtime/journal.py
- `main()` --calls--> `quality_report()`  [INFERRED]
  data/build_features.py → src/axq/features/analysis.py

## Import Cycles
- None detected.

## Communities (156 total, 38 thin omitted)

### Community 0 - "build_weekly_reflection"
Cohesion: 0.16
Nodes (32): build_weekly_reflection(), FailurePattern, PatternBase, PatternMetricSummary, PatternSignalClass, PatternType, StrEnum, Immutable contracts for deterministic weekly reflection and pattern lifecycle. (+24 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.10
Nodes (48): compare_label_definitions(), DataFrame, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, CollisionPolicy, EntryReference, LabelDefinition, LabelKind (+40 more)

### Community 2 - "ReflectionPolicy"
Cohesion: 0.11
Nodes (33): DailyReflection, ReflectionPolicy, _build(), _days(), _emit(), _latest_records(), _load_policy(), main() (+25 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.17
Nodes (12): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifestEntry, BaseModel, FeatureDefinition, FeatureRegistry, _integer(), _output_lookback() (+4 more)

### Community 4 - "trainer.py"
Cohesion: 0.08
Nodes (38): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., dump_artifact(), file_hash(), load_artifact(), Any (+30 more)

### Community 5 - "indicators.py"
Cohesion: 0.15
Nodes (32): aroon(), atr(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+24 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.09
Nodes (50): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+42 more)

### Community 7 - "update_scenario"
Cohesion: 0.25
Nodes (28): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), _agent_pair(), _create(), _event(), _market(), datetime, parametrize (+20 more)

### Community 8 - "development/config.py"
Cohesion: 0.06
Nodes (53): AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+45 more)

### Community 9 - "axq/config.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.16
Nodes (23): FakeEntryAdapter, FakePositionActionAdapter, FakeProcessor, _fresh(), _intent(), _market_event(), _position_action_intent(), datetime (+15 more)

### Community 11 - "inference.py"
Cohesion: 0.07
Nodes (41): ProbabilityCalibrator, ndarray, Validation-only probability calibration without OOS access., calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), overfitting_report(), Any (+33 more)

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
Cohesion: 0.17
Nodes (20): evaluate_challenger_evidence(), Any, Advisory Champion/Challenger evidence contract., _categorical_distribution(), distribution_drift(), feature_drift_report(), _finite(), ks_statistic() (+12 more)

### Community 22 - "datasets/builder.py"
Cohesion: 0.05
Nodes (62): main(), main(), DataFrame, Leakage-safe multi-timeframe alignment., Attach bars only when their UTC close time is at/before the base bar's UTC…, synchronize_completed_bars(), timeframe_delta(), DataFrame (+54 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "SQLiteWeeklyReflectionStore"
Cohesion: 0.16
Nodes (21): Pattern, BaseModel, ReflectionModel, KnowledgeStatus, PatternStatusTransition, WeeklyReflection, WeeklyReflectionPolicy, _pattern_from_json() (+13 more)

### Community 26 - "dataset.py"
Cohesion: 0.12
Nodes (18): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., FeatureManifest, Path, Canonical feature-manifest models., load_training_dataset() (+10 more)

### Community 27 - "RuntimeEvent"
Cohesion: 0.11
Nodes (45): BaseModel, datetime, StrEnum, Canonical runtime event envelopes for live and deterministic replay., RuntimeEvent, RuntimeEventType, Versioned contracts and deterministic reduction for live and replay., _account_update() (+37 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.06
Nodes (32): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+24 more)

### Community 29 - "_deterministic.py"
Cohesion: 0.15
Nodes (24): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, EvidencePolarity, EvidenceReference, StrEnum, DeterministicSpecialistAgent (+16 more)

### Community 30 - "README.md"
Cohesion: 0.22
Nodes (4): Model registry and promotion contract, Phase 5 development layer, Quant model training, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.08
Nodes (66): BaseModel, StrEnum, Strict contracts for the deterministic financial Risk boundary., RiskBoundaryModel, RiskContext, RiskOutcome, RiskPolicy, RiskReason (+58 more)

### Community 32 - "ToolResult"
Cohesion: 0.11
Nodes (35): FreshnessStatus, FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool (+27 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.18
Nodes (6): RuntimeStatus, JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe., Perform at most one read-only refresh when the bounded cadence elapsed., Own ordering and gates while delegating every trading semantic decision., RuntimeOrchestrator

### Community 34 - "SQLiteExecutionLedger"
Cohesion: 0.12
Nodes (26): Connection, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, broker_snapshot_runtime_events(), ExecutionTransition, _fresh(), _intent(), _link() (+18 more)

### Community 35 - "timedelta"
Cohesion: 0.22
Nodes (29): initial_runtime_state(), Construct a canonical state with explicit unknown component values., account(), apply(), event(), feedback(), fresh(), market() (+21 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "experience/__init__.py"
Cohesion: 0.16
Nodes (25): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+17 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.11
Nodes (19): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+11 more)

### Community 39 - "default_registry"
Cohesion: 0.12
Nodes (19): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., price_action_features(), Any, DataFrame, default_registry() (+11 more)

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
Cohesion: 0.14
Nodes (19): AttributionSources, ExperienceType, _emit(), main(), _parser(), ArgumentParser, Command-line interface for deterministic Phase 8 experience reconstruction., _canonical_payload() (+11 more)

### Community 44 - "attribution.py"
Cohesion: 0.25
Nodes (15): _anomaly(), _enum_value(), _identity_context(), OutcomeAttributionBuilder, _progressed_to(), _provenance(), Any, Exact-link deterministic reconstruction of normalized Phase 8 experiences. (+7 more)

### Community 45 - "folds.py"
Cohesion: 0.09
Nodes (38): Architecture, CalibrationConfig, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel, Path (+30 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.26
Nodes (22): ChartAgent, _input(), _kernel_fixture(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure() (+14 more)

### Community 49 - "position.py"
Cohesion: 0.16
Nodes (17): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), datetime, Demo-only MetaTrader 5 transport for Task 7 position-action intents. (+9 more)

### Community 50 - "system.py"
Cohesion: 0.05
Nodes (65): DeterministicDecisionProcessor, EntryDecisionInputs, BaseModel, Causal contexts supplied by the runtime-specific context adapter., Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, _identity(), _PendingClose, PendingReplayEntry (+57 more)

### Community 51 - "Phase 3 label contract"
Cohesion: 0.40
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "recovery_contracts.py"
Cohesion: 0.11
Nodes (28): _conflict_reason(), _finding(), _object_id(), datetime, Protocol, Deterministic exact-linkage comparison of local and broker execution state., reconcile_execution_state(), ReconciliationLedger (+20 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "ComponentFreshness"
Cohesion: 0.08
Nodes (71): evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis, StrEnum, ReconciliationKind (+63 more)

### Community 55 - "service.py"
Cohesion: 0.13
Nodes (25): load_runtime_config(), BaseModel, Path, Strict operational configuration for the Phase 7 runtime service., RuntimeConfig, DecisionCycle, DecisionPlan, OutcomeCount (+17 more)

### Community 68 - "Signal"
Cohesion: 0.06
Nodes (109): EntryContextProvider, PositionActionContextProvider, PositionContextProvider, DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy (+101 more)

### Community 69 - "runner.py"
Cohesion: 0.09
Nodes (40): Device, file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic() (+32 more)

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
Cohesion: 0.19
Nodes (29): _adapter(), _fresh(), _intent(), _observation(), _policy(), Exception, parametrize, RiskContext (+21 more)

### Community 77 - "snapshot.py"
Cohesion: 0.19
Nodes (22): BrokerObjectKind, MT5PersistedIntentLink, MT5SnapshotError, Narrow contracts isolating the optional MetaTrader5 package., A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider (+14 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.11
Nodes (19): JournalEntry, Connection, JournalSemantic, Path, UTCDateTime, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., _semantic_id() (+11 more)

### Community 79 - "ensure_utc"
Cohesion: 0.21
Nodes (7): ensure_utc(), datetime, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Return the current instant in UTC., Live clock backed by the host system clock., SystemUTCClock

### Community 80 - "test_feature_formulas.py"
Cohesion: 0.23
Nodes (11): skipif, money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility() (+3 more)

### Community 81 - "mt5/__init__.py"
Cohesion: 0.25
Nodes (6): MT5Constants, MT5SymbolMapping, BaseModel, Optional, demo-safe MetaTrader5 gateway and adapters., test_symbol_mapping_is_explicit_auditable_and_deterministic(), _constants()

### Community 82 - "preflight.py"
Cohesion: 0.24
Nodes (15): The transport failed before submission could be accepted., TransportFailure, _account_mode(), _float_value(), _int_value(), _positive_float(), datetime, Fail-closed MetaTrader 5 entry preflight and request construction. (+7 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "transport.py"
Cohesion: 0.09
Nodes (17): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Path, Path, Append-only SQLite ledger for position-action transport outcomes. (+9 more)

### Community 85 - "position_actions/evaluator.py"
Cohesion: 0.14
Nodes (33): Compose existing pure functions; adapters provide causal context only., PositionActionContext, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, PositionActionType (+25 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "execution_boundary/__init__.py"
Cohesion: 0.12
Nodes (29): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, ExecutionTransport, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics., Process one immutable intent idempotently. (+21 more)

### Community 88 - "test_runtime_state.py"
Cohesion: 0.20
Nodes (20): account(), feedback(), freshness(), market(), order(), position(), datetime, parametrize (+12 more)

### Community 89 - "test_agent_tools.py"
Cohesion: 0.10
Nodes (27): Any, PredictiveModelEvidenceProvider, Any, Protocol, QuantAgentEvidenceProvider, Return label-to-probability facts without a trading decision., Narrow adapter around the existing frozen Phase 4 QuantAgent., _ExplodingTool (+19 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "_context"
Cohesion: 0.18
Nodes (30): PositionSide, StrEnum, _context(), _evaluate(), _fresh(), _intent(), _management(), _position() (+22 more)

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "MetaTrader5Gateway"
Cohesion: 0.18
Nodes (9): MT5ConnectionError, RuntimeError, The terminal package or connected terminal is unavailable., _load_mt5(), _mapping(), _mappings(), MetaTrader5Gateway, Lazy concrete wrapper around the Windows-only MetaTrader5 package. (+1 more)

### Community 95 - "evidence"
Cohesion: 0.22
Nodes (18): evidence(), datetime, parametrize, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields(), test_agent_evidence_identity_is_deterministic_and_round_trips(), test_agent_input_binds_tools_without_exposing_account_state(), test_agent_input_preserves_non_available_tool_semantics() (+10 more)

### Community 96 - "features/analysis.py"
Cohesion: 0.25
Nodes (17): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+9 more)

### Community 98 - "weekly_cli.py"
Cohesion: 0.23
Nodes (18): _build(), _emit(), handle_weekly_command(), _history(), _latest(), _policy(), Any, date (+10 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.15
Nodes (7): _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket(), test_snapshot_maps_account_market_books_exposure_and_constraints()

### Community 100 - "canonical_hash"
Cohesion: 0.16
Nodes (3): model_validator, canonical_hash(), Any

### Community 101 - "Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design"
Cohesion: 0.13
Nodes (14): Append-only persistence and supersession, Architecture, Baseline validation, CLI, Exact provenance validation, ISO-week boundary and availability, Knowledge-status lifecycle, Pattern generation (+6 more)

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "MT5Gateway"
Cohesion: 0.09
Nodes (19): RuntimeError, Submission may have reached the broker and requires reconciliation., UnknownSubmissionState, MT5Gateway, Protocol, _float_value(), _int_value(), MT5ExecutionAdapter (+11 more)

### Community 104 - "PositionGateway"
Cohesion: 0.15
Nodes (14): _adapter(), _constants(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send() (+6 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "FakeMT5Module"
Cohesion: 0.13
Nodes (5): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity()

### Community 108 - "reflection/__init__.py"
Cohesion: 0.29
Nodes (23): FindingCategory, FindingSignal, MetricFact, StrEnum, Immutable content-addressed contracts for deterministic daily reflection., ReflectionFinding, SampleGuardRecord, SampleGuardStatus (+15 more)

### Community 109 - "execution_boundary/builder.py"
Cohesion: 0.43
Nodes (6): build_execution_intent(), RiskContext, Pure construction of provenance-bound execution intents., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links(), ExecutionOrderType

### Community 110 - "runtime/journal.py"
Cohesion: 0.06
Nodes (57): Collection, ScenarioTransition, Protocol, Clock contract used outside the pure reducer., Explicitly advanced deterministic replay clock., ReplayClock, RuntimeClock, JournalOutcome (+49 more)

### Community 112 - "test_foundation.py"
Cohesion: 0.17
Nodes (9): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., candles(), DataTests, FeatureTests, DataFrame (+1 more)

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

### Community 122 - "LocalModelRegistry"
Cohesion: 0.24
Nodes (9): LocalModelRegistry, ModelState, Any, BaseModel, Path, StrEnum, Explicit local lifecycle registry; promotion is never automatic., RegistryEntry (+1 more)

### Community 123 - "test_weekly_reflection.py"
Cohesion: 0.33
Nodes (11): _daily(), _experience(), _finding(), test_complete_week_builds_guarded_success_and_failure_patterns_deterministically(), test_completed_revision_supersedes_incomplete_week_without_mutating_it(), test_daily_revision_chain_selects_terminal_and_rejects_missing_or_branching_links(), test_exact_provenance_failure_and_duplicate_experience_fail_closed(), test_incomplete_week_records_five_missing_days_and_suppresses_patterns() (+3 more)

### Community 126 - "test_daily_reflection.py"
Cohesion: 0.39
Nodes (11): _agent(), _findings(), _management(), _provenance(), datetime, _rejection(), test_agent_position_and_runtime_anomaly_findings_use_exact_daily_sources(), test_daily_aggregation_detects_confidence_excursion_and_rejection_patterns() (+3 more)

### Community 127 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 3 Weekly Reflection and Pattern Lifecycle Implementation Plan, Task 1: Weekly contracts and semantic identities, Task 2: Pure weekly aggregation and exact provenance, Task 3: Append-only weekly and lifecycle persistence, Task 4: Weekly CLI integration, Task 5: Corrected one-month baseline and durable context

### Community 128 - "Phase 5 local Quant experiment workflow"
Cohesion: 0.67
Nodes (3): Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review

### Community 130 - "test_reflection_cli.py"
Cohesion: 0.46
Nodes (7): _decision(), _experience_store(), Path, test_build_range_is_deterministic_and_idempotent(), test_build_rejects_reversed_date_range(), test_changed_input_creates_explicit_cli_supersession(), test_show_and_report_emit_machine_readable_json()

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
Cohesion: 0.48
Nodes (6): _finding(), _guard(), test_contracts_reject_naive_or_non_daily_periods_and_are_frozen(), test_daily_reflection_normalizes_children_and_binds_supersession(), test_metric_fact_preserves_unavailable_separately_from_numeric_zero(), test_policy_and_nested_contracts_have_stable_content_identities()

### Community 142 - "Deterministic Weekly Reflection and Pattern Lifecycle"
Cohesion: 0.33
Nodes (5): Deterministic Weekly Reflection and Pattern Lifecycle, Identity, Knowledge lifecycle, Verified baseline, Weekly contract

### Community 145 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 151 - "ExperienceBuild"
Cohesion: 0.50
Nodes (3): ExperienceBuild, BaseModel, Experience

### Community 152 - "multi_timeframe_features"
Cohesion: 0.50
Nodes (3): multi_timeframe_features(), Any, DataFrame

### Community 154 - "build_mt5_gateway"
Cohesion: 0.67
Nodes (3): build_mt5_gateway(), Build the lazy gateway; operational paths are not semantic identity., test_explicit_terminal_path_is_forwarded_without_entering_config_identity()

## Knowledge Gaps
- **255 isolated node(s):** `adaptive-xauusd-trader`, `Repository-start workflow`, `Graphify`, `Current capabilities`, `Setup (Windows PowerShell)` (+250 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 847 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **38 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `build_weekly_reflection`, `LabelDefinition`, `ReflectionPolicy`, `trainer.py`, `agents/__init__.py`, `.normalize_validate_and_bind_identity`, `development/config.py`, `model_validator`, `model_validator`, `.bind_identity`, `model_validator`, `.bind_identity`, `.validate_and_bind_identity`, `.validate_and_bind_identity`, `.bind_identity`, `.validate_event`, `.validate_and_bind_identity`, `model_validator`, `datasets/builder.py`, `.validate_and_bind_identity`, `SQLiteWeeklyReflectionStore`, `dataset.py`, `RuntimeEvent`, `.validate_and_bind_identity`, `_deterministic.py`, `test_risk_boundary.py`, `ToolResult`, `experience/__init__.py`, `SQLiteExperienceStore`, `attribution.py`, `folds.py`, `system.py`, `recovery_contracts.py`, `ComponentFreshness`, `service.py`, `Signal`, `snapshot.py`, `transport.py`, `position_actions/evaluator.py`, `execution_boundary/__init__.py`, `reflection/__init__.py`, `runtime/journal.py`, `ExperienceProvenance`, `DatasetManifest`, `model_validator`, `model_validator`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `test_reflection_cli.py`, `ReflectionPolicy`, `test_runtime_orchestration.py`, `inference.py`, `RuntimeEvent`, `test_risk_boundary.py`, `SQLiteExecutionLedger`, `experience/__init__.py`, `SQLiteExperienceStore`, `attribution.py`, `system.py`, `recovery_contracts.py`, `ComponentFreshness`, `schemas.py`, `EntryGateway`, `test_execution_boundary.py`, `preflight.py`, `position_actions/evaluator.py`, `execution_boundary/__init__.py`, `_context`, `MT5Gateway`, `reflection/__init__.py`, `ExperienceProvenance`, `test_weekly_reflection.py`, `test_daily_reflection.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `axq/features/registry.py`, `indicators.py`, `axq/config.py`, `test_feature_formulas.py`, `breakout_features`, `session_features`, `system.py`, `test_foundation.py`, `datasets/builder.py`, `multi_timeframe_features`, `test_agent_tools.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 138 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 138 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 68 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 68 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ExecutionIntent` (e.g. with `DemoExecutionAdapter` and `ExecutionAdapter`) actually correct?**
  _`ExecutionIntent` has 9 INFERRED edges - model-reasoned connections that need verification._