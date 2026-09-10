# Graph Report - phase-7-decision-execution  (2026-09-10)

## Corpus Check
- 239 files · ~111,154 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2561 nodes · 7847 edges · 118 communities (96 shown, 21 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1149 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bf07e4c6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- versioning.py
- LabelDefinition
- LocalModelRegistry
- axq/features/registry.py
- trainer.py
- indicators.py
- agents/__init__.py
- reduce_state
- development/config.py
- features/analysis.py
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
- schemas.py
- position_management/contracts.py
- System architecture (Phase 0-7 baseline)
- QuantAgent
- folds.py
- runtime/__init__.py
- Architecture decision log
- _deterministic.py
- README.md
- timedelta
- ToolResult
- RuntimeOrchestrator
- SQLiteExecutionLedger
- test_live_replay_parity.py
- Global Constraints
- tuning.py
- Phase 0-6 runbook
- default_registry
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- ExecutionIntent
- orchestration/__init__.py
- quant/config.py
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- kernel.py
- position.py
- Phase 3 dataset contract
- Phase 3 label contract
- runtime/journal.py
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
- PositionState
- runner.py
- Tool-Augmented Agentic Architecture
- Global Constraints
- RunStateStore
- AgentEvidence
- EntryGateway
- OperatorControls
- test_execution_boundary.py
- snapshot.py
- SQLiteRuntimeJournal
- ensure_utc
- test_feature_formulas.py
- MT5Gateway
- EvidenceBundle
- Global Constraints
- PositionGateway
- processor.py
- Global Constraints
- execution_boundary/__init__.py
- statistical_features
- InMemoryExecutionLedger
- Phase 7 deterministic runtime orchestration
- _context
- InMemoryPositionActionTransportLedger
- Global Constraints
- MetaTrader5Gateway
- evidence
- update_scenario
- FakeRunner
- ComponentFreshness
- SnapshotGateway
- model_validator
- .__init__
- Phase 7 Task 7: Position Action Safety and Journal Plan
- preflight.py
- mt5/__init__.py
- FakeGateway
- Position action safety
- FakeMT5Module
- breakout_features
- RuntimeEvent
- _MT5Module
- atr
- service.py
- Phase 7 Task 8 Direct MT5 Transport Design
- Global constraints
- canonical_hash
- multi_timeframe_features
- price_action_features

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 100 edges
2. `RuntimeEvent` - 81 edges
3. `ExecutionIntent` - 59 edges
4. `Signal` - 58 edges
5. `ExecutionResult` - 51 edges
6. `reduce_state()` - 47 edges
7. `SQLiteExecutionLedger` - 46 edges
8. `ToolResult` - 46 edges
9. `_context()` - 46 edges
10. `evaluate_discipline()` - 44 edges

## Surprising Connections (you probably didn't know these)
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_symbol_mapping_is_explicit_auditable_and_deterministic()` --calls--> `MT5SymbolMapping`  [INFERRED]
  tests/test_mt5_gateway.py → src/axq/mt5/contracts.py
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py
- `main()` --calls--> `default_registry()`  [INFERRED]
  data/build_features.py → src/axq/features/registry.py
- `main()` --calls--> `assemble_dataset()`  [INFERRED]
  data/build_mt5_dataset.py → src/axq/datasets/builder.py

## Import Cycles
- None detected.

## Communities (118 total, 21 thin omitted)

### Community 0 - "versioning.py"
Cohesion: 0.06
Nodes (55): assemble_dataset(), dataframe_hash(), DatasetBuildResult, Any, DataFrame, Path, Leakage-safe Phase 3 dataset assembly., _validate_source_frames() (+47 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.09
Nodes (51): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, CollisionPolicy (+43 more)

### Community 2 - "LocalModelRegistry"
Cohesion: 0.17
Nodes (12): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., LocalModelRegistry, ModelState, Any, BaseModel (+4 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "trainer.py"
Cohesion: 0.06
Nodes (49): dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run(), write_json() (+41 more)

### Community 5 - "indicators.py"
Cohesion: 0.19
Nodes (25): skipif, aroon(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+17 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.11
Nodes (38): AgentReasoningBudget, Small shared specialist input and output-validation boundary., AgentModel, AgentToolRequest, EvidencePolarity, EvidenceReference, HypothesisRelationship, HypothesisStatus (+30 more)

### Community 7 - "reduce_state"
Cohesion: 0.20
Nodes (31): initial_runtime_state(), datetime, Apply one causally available event without consulting a wall clock., Construct a canonical state with explicit unknown component values., reduce_state(), account(), apply(), event() (+23 more)

### Community 8 - "development/config.py"
Cohesion: 0.10
Nodes (33): AblationConfig, EvaluationConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config(), load_tuning_config(), load_walk_forward_config() (+25 more)

### Community 9 - "features/analysis.py"
Cohesion: 0.06
Nodes (52): CompletedProcess, main(), HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel (+44 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.14
Nodes (27): DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., FakeEntryAdapter, FakePositionActionAdapter, FakeProcessor, FakeSnapshotProvider, _fresh(), _intent() (+19 more)

### Community 11 - "evaluate_predictions"
Cohesion: 0.17
Nodes (20): calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), overfitting_report(), Any, DataFrame, ndarray, Series (+12 more)

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
Cohesion: 0.16
Nodes (21): evaluate_challenger_evidence(), Any, Advisory Champion/Challenger evidence contract., _categorical_distribution(), distribution_drift(), feature_drift_report(), _finite(), ks_statistic() (+13 more)

### Community 22 - "schemas.py"
Cohesion: 0.05
Nodes (40): main(), main(), main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., DataFrame, Leakage-safe multi-timeframe alignment. (+32 more)

### Community 23 - "position_management/contracts.py"
Cohesion: 0.20
Nodes (19): MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy, PositionManagementReason, PositionManagementResult, BaseModel (+11 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "QuantAgent"
Cohesion: 0.21
Nodes (10): evaluate_saved_run(), Any, Reproduce frozen split metrics without fitting or retraining., Any, datetime, ndarray, Series, QuantAgent (+2 more)

### Community 26 - "folds.py"
Cohesion: 0.20
Nodes (17): _aggregate_fold_metrics(), completed_fold_summary(), DevelopmentFoldResult, fold_identity(), Any, DataFrame, Path, Fresh-state, fold-local development evaluation before immutable final OOS. (+9 more)

### Community 27 - "runtime/__init__.py"
Cohesion: 0.12
Nodes (39): execution_result_to_runtime_event(), Bridge typed execution results into the shared Phase 6 runtime path., Convert actionable execution feedback; local NO_ACTION stays local., Immutable contracts for durable execution recovery and safe resume., position_action_result_to_runtime_event(), Dedicated append-only transport contracts for safe position actions., Strict contracts for the deterministic financial Risk boundary., StrEnum (+31 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.07
Nodes (29): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+21 more)

### Community 29 - "_deterministic.py"
Cohesion: 0.20
Nodes (21): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, DeterministicSpecialistAgent, fact_map(), Interpretation, numeric() (+13 more)

### Community 30 - "README.md"
Cohesion: 0.18
Nodes (7): Model registry and promotion contract, Phase 5 development layer, Quant model training, Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review, Quant Agent contract

### Community 31 - "timedelta"
Cohesion: 0.06
Nodes (120): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+112 more)

### Community 32 - "ToolResult"
Cohesion: 0.06
Nodes (62): FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool, CausalFeatureSnapshot (+54 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.17
Nodes (6): RuntimeStatus, JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe., Perform at most one read-only refresh when the bounded cadence elapsed., Own ordering and gates while delegating every trading semantic decision., RuntimeOrchestrator

### Community 34 - "SQLiteExecutionLedger"
Cohesion: 0.12
Nodes (28): Connection, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, datetime, reconcile_execution_state(), broker_snapshot_runtime_events(), BrokerRecoverySnapshot, ExecutionTransition (+20 more)

### Community 35 - "test_live_replay_parity.py"
Cohesion: 0.19
Nodes (24): UTC clocks shared by live processing and deterministic replay., Live clock backed by the host system clock., Explicitly advanced deterministic replay clock., ReplayClock, SystemUTCClock, JournalOutcomeStatus, JournalRecordType, StrEnum (+16 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "tuning.py"
Cohesion: 0.14
Nodes (18): DataFrame, TrainingDataset, model_validator, TuningConfig, _parameters(), Any, Path, Optuna execution support constrained to pre-final-OOS development folds. (+10 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.12
Nodes (16): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+8 more)

### Community 39 - "default_registry"
Cohesion: 0.22
Nodes (13): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., default_registry(), candles(), DataFrame, test_labels_are_not_feature_inputs() (+5 more)

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
Cohesion: 0.12
Nodes (17): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, datetime, Protocol, Process one immutable intent idempotently., Guarded demo adapter; never permits a live-account submission., ExecutionBoundaryModel (+9 more)

### Community 44 - "orchestration/__init__.py"
Cohesion: 0.17
Nodes (11): DecisionCycle, OutcomeCount, BaseModel, model_validator, Auditable classifications emitted by the existing decision boundaries., RuntimeRunSummary, Deterministic orchestration of existing Phase 6/7 runtime boundaries., EntryDecisionInputs (+3 more)

### Community 45 - "quant/config.py"
Cohesion: 0.13
Nodes (24): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, PreprocessingConfig, BaseModel, StrEnum (+16 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "kernel.py"
Cohesion: 0.25
Nodes (21): ChartAgent, Shared deterministic specialist-evidence kernel for live and replay., _input(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure() (+13 more)

### Community 49 - "position.py"
Cohesion: 0.13
Nodes (20): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), datetime, Demo-only MetaTrader 5 transport for Task 7 position-action intents. (+12 more)

### Community 50 - "Phase 3 dataset contract"
Cohesion: 0.29
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 51 - "Phase 3 label contract"
Cohesion: 0.33
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "runtime/journal.py"
Cohesion: 0.15
Nodes (21): evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis, CheckpointLedger, BaseModel (+13 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.17
Nodes (37): ResumeStatus, default_demo_position_management_policy(), evaluate_position(), Return conservative deterministic demo defaults, not optimized strategy truth., Evaluate one open position without mutating state or invoking execution…, _broker_constraints(), _context(), _fresh() (+29 more)

### Community 55 - "RuntimeConfig"
Cohesion: 0.19
Nodes (12): load_runtime_config(), BaseModel, Path, Strict operational configuration for the Phase 7 runtime service., RuntimeConfig, StrEnum, RuntimeMode, build_mt5_gateway() (+4 more)

### Community 68 - "PositionState"
Cohesion: 0.36
Nodes (11): _conflict_reason(), _finding(), _object_id(), Deterministic exact-linkage comparison of local and broker execution state., StrEnum, ReconciliationFinding, ReconciliationKind, ResolutionStatus (+3 more)

### Community 69 - "runner.py"
Cohesion: 0.10
Nodes (39): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+31 more)

### Community 70 - "Tool-Augmented Agentic Architecture"
Cohesion: 0.09
Nodes (22): Deferred risks, Event model and causality, Existing components reused, Explicitly unimplemented after Phase 7 Task 9, Explicitly untouched, Implemented shared path and future paths, Invariants, Live/replay ports (+14 more)

### Community 71 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 6 Tool-Augmented Agentic Baseline Implementation Plan, Task 1: Canonical runtime events and shared state, Task 2: Clock, event source, and causal state reducer, Task 3: Tool facts and optional predictive-model adapter, Task 4: Stateful specialist evidence contracts, Task 5: M5 thesis and intrabar scenario state machine, Task 6: Initial specialist agents and evidence bundle (+2 more)

### Community 72 - "RunStateStore"
Cohesion: 0.32
Nodes (4): Any, Path, Atomic, identity-bound state for resumable local experiments., RunStateStore

### Community 73 - "AgentEvidence"
Cohesion: 0.14
Nodes (14): AgentInput, model_validator, Protocol, Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition., SpecialistAgent, transition_agent() (+6 more)

### Community 74 - "EntryGateway"
Cohesion: 0.14
Nodes (17): _adapter(), EntryGateway, _intent(), _policy(), datetime, Exception, parametrize, test_broker_partial_fill_maps_without_resubmitting_remainder() (+9 more)

### Community 75 - "OperatorControls"
Cohesion: 0.23
Nodes (5): OperatorControls, Monotonic operator gates: callers cannot use this contract to bypass safety., DeterministicDecisionProcessor, Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, test_operator_controls_only_become_more_conservative()

### Community 76 - "test_execution_boundary.py"
Cohesion: 0.19
Nodes (31): RuntimeError, Submission may have reached the broker and requires reconciliation., UnknownSubmissionState, _adapter(), _intent(), _observation(), _policy(), _proposal() (+23 more)

### Community 77 - "snapshot.py"
Cohesion: 0.20
Nodes (20): BrokerIntentLink, BrokerObjectKind, MT5SnapshotError, A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider, _optional_float() (+12 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.14
Nodes (17): JournalEntry, Connection, JournalSemantic, Path, UTCDateTime, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., _semantic_id() (+9 more)

### Community 79 - "ensure_utc"
Cohesion: 0.28
Nodes (4): ensure_utc(), datetime, Reject naive timestamps and return a normalized UTC timestamp., Return the current instant in UTC.

### Community 80 - "test_feature_formulas.py"
Cohesion: 0.27
Nodes (9): money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility(), test_stochastic_williams_roc_cci_obv_mfi_smoke() (+1 more)

### Community 81 - "MT5Gateway"
Cohesion: 0.08
Nodes (16): ExecutionTransport, Submit an already approved intent to the execution transport., BrokerExecutionReport, MT5Gateway, MT5SymbolMapping, Protocol, _float_value(), _int_value() (+8 more)

### Community 82 - "EvidenceBundle"
Cohesion: 0.13
Nodes (32): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion., SpecialistContribution (+24 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "PositionGateway"
Cohesion: 0.06
Nodes (30): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Path, Path, Append-only SQLite ledger for position-action transport outcomes. (+22 more)

### Community 85 - "processor.py"
Cohesion: 0.14
Nodes (31): Concrete composition of existing deterministic Phase 7 decision boundaries., PositionActionContext, PositionActionIntent, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult (+23 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "execution_boundary/__init__.py"
Cohesion: 0.20
Nodes (19): Demo-safe execution adapter boundary with explicit idempotency semantics., build_execution_intent(), default_execution_policy(), RiskContext, Pure construction of provenance-bound execution intents., Return the conservative, execution-disabled baseline policy., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links() (+11 more)

### Community 88 - "statistical_features"
Cohesion: 0.50
Nodes (3): Any, DataFrame, statistical_features()

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

### Community 96 - "update_scenario"
Cohesion: 0.26
Nodes (24): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), _agent_pair(), _create(), _event(), _market(), datetime, parametrize (+16 more)

### Community 98 - "ComponentFreshness"
Cohesion: 0.14
Nodes (28): _unknown_freshness(), ComponentFreshness, FreshnessStatus, _freshness(), _state(), test_slow_context_tool_uses_reducer_availability_cursor(), _fresh(), _fresh() (+20 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.14
Nodes (9): MT5PersistedIntentLink, _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_creates_canonical_events_and_reduces_through_shared_path(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket() (+1 more)

### Community 101 - ".__init__"
Cohesion: 0.50
Nodes (3): EntryContextProvider, PositionActionContextProvider, PositionContextProvider

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "preflight.py"
Cohesion: 0.21
Nodes (17): The transport failed before submission could be accepted., TransportFailure, _account_mode(), _float_value(), _int_value(), MT5EntryPreflight, _positive_float(), datetime (+9 more)

### Community 104 - "mt5/__init__.py"
Cohesion: 0.22
Nodes (7): MT5Constants, BaseModel, Narrow contracts isolating the optional MetaTrader5 package., Optional, demo-safe MetaTrader5 gateway and adapters., _constants(), _constants(), _constants()

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "FakeMT5Module"
Cohesion: 0.12
Nodes (6): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity(), test_symbol_mapping_is_explicit_auditable_and_deterministic()

### Community 108 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 110 - "RuntimeEvent"
Cohesion: 0.06
Nodes (30): ScenarioTransition, Protocol, Clock contract used outside the pure reducer., RuntimeClock, BaseModel, datetime, model_validator, RuntimeEvent (+22 more)

### Community 114 - "atr"
Cohesion: 0.29
Nodes (9): atr(), true_range(), market_structure_features(), Any, DataFrame, Causal market-structure features. A candidate pivot at position p is emitted at…, Any, DataFrame (+1 more)

### Community 117 - "service.py"
Cohesion: 0.08
Nodes (19): Strict orchestration-only contracts for the shared Phase 7 runtime., StartupPhase, Compose existing pure functions; adapters provide causal context only., BrokerSnapshotProvider, DecisionCycleProcessor, PositionActionAdapter, datetime, Protocol (+11 more)

### Community 119 - "Phase 7 Task 8 Direct MT5 Transport Design"
Cohesion: 0.22
Nodes (8): Boundaries, Deferred work, Idempotency and persistence, Phase 7 Task 8 Direct MT5 Transport Design, Requests and response mapping, Safety and modes, Scope, Snapshots and causality

### Community 121 - "Global constraints"
Cohesion: 0.25
Nodes (7): Global constraints, Phase 7 Task 8 Direct MT5 Transport Implementation Plan, Task 1: Gateway and normalized MT5 contracts, Task 2: Canonical broker snapshots, Task 3: Entry transport and complete dry-run preflight, Task 4: Durable position-action transport, Task 5: Documentation, optional read-only smoke, and final verification

### Community 124 - "canonical_hash"
Cohesion: 0.13
Nodes (5): model_validator, model_validator, model_validator, canonical_hash(), Any

### Community 125 - "multi_timeframe_features"
Cohesion: 0.50
Nodes (3): multi_timeframe_features(), Any, DataFrame

### Community 126 - "price_action_features"
Cohesion: 0.50
Nodes (3): price_action_features(), Any, DataFrame

## Knowledge Gaps
- **198 isolated node(s):** `adaptive-xauusd-trader`, `Repository-start workflow`, `Graphify`, `Current capabilities`, `Setup (Windows PowerShell)` (+193 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 720 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `versioning.py`, `LabelDefinition`, `trainer.py`, `agents/__init__.py`, `development/config.py`, `position_management/contracts.py`, `folds.py`, `runtime/__init__.py`, `_deterministic.py`, `timedelta`, `ToolResult`, `ExecutionIntent`, `orchestration/__init__.py`, `quant/config.py`, `kernel.py`, `runtime/journal.py`, `runner.py`, `AgentEvidence`, `EvidenceBundle`, `PositionGateway`, `processor.py`, `execution_boundary/__init__.py`, `evidence`, `model_validator`, `mt5/__init__.py`, `RuntimeEvent`, `service.py`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Why does `Signal` connect `timedelta` to `SQLiteExecutionLedger`, `PositionState`, `trainer.py`, `preflight.py`, `EntryGateway`, `ExecutionIntent`, `test_execution_boundary.py`, `_context`, `test_runtime_orchestration.py`, `EvidenceBundle`, `processor.py`, `schemas.py`, `execution_boundary/__init__.py`, `_context`, `QuantAgent`, `runtime/__init__.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `RuntimeOrchestrator` connect `RuntimeOrchestrator` to `SQLiteExecutionLedger`, `test_live_replay_parity.py`, `test_runtime_orchestration.py`, `OperatorControls`, `orchestration/__init__.py`, `RuntimeEvent`, `position.py`, `PositionGateway`, `service.py`, `RuntimeConfig`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 94 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 94 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ExecutionIntent` (e.g. with `DemoExecutionAdapter` and `ExecutionAdapter`) actually correct?**
  _`ExecutionIntent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 41 INFERRED edges - model-reasoned connections that need verification._