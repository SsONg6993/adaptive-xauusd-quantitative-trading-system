# Graph Report - phase-7-decision-execution  (2026-09-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2071 nodes · 6365 edges · 118 communities (91 shown, 26 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 1030 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1762fa23`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_datasets_phase3.py
- LabelDefinition
- ModelManifest
- axq/features/registry.py
- inference.py
- indicators.py
- agents/__init__.py
- timedelta
- development/config.py
- features/analysis.py
- axq/config.py
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
- test_agent_tools.py
- System architecture (Phase 0-7 baseline)
- dataset.py
- folds.py
- RuntimeEvent
- Architecture decision log
- _deterministic.py
- README.md
- test_risk_boundary.py
- ToolResult
- evaluate_discipline
- execution_boundary/__init__.py
- test_live_replay_parity.py
- Global Constraints
- trainer.py
- Phase 0-6 runbook
- default_registry
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- ExecutionResult
- model_validator
- canonical_hash
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- SQLiteExecutionLedger
- Phase 3 dataset contract
- Phase 3 label contract
- runtime/journal.py
- Repository instructions
- _context
- Phase 5 local Quant experiment workflow
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
- comparison.py
- runner.py
- Tool-Augmented Agentic Architecture
- Global Constraints
- RunStateStore
- AgentEvidence
- datasets/__init__.py
- replay.py
- test_execution_boundary.py
- reconciliation.py
- SQLiteRuntimeJournal
- clock.py
- momentum_features
- RuntimeError
- fusion.py
- features/preprocessing.py
- Database
- position_actions/evaluator.py
- Global Constraints
- risk_boundary/evaluator.py
- statistical_features
- main
- discipline/contracts.py
- _context
- datasets/preprocessing.py
- Global Constraints
- position_management/contracts.py
- evidence
- update_scenario
- Signal
- test_runtime_state.py
- test_foundation.py
- ComponentFreshness
- ContractAndRiskTests
- Phase 7 Task 7: Position Action Safety and Journal Plan
- test_quant_development_runner.py
- .validate_and_bind_identity
- model_validator
- Position action safety
- _snapshot
- breakout_features
- model_validator
- EventSource
- model_validator
- InMemoryEventSource
- .validate_bindings_and_identity
- .validate_and_bind_identity
- .validate_event
- .validate_and_bind_identity
- .validate_and_bind_identity

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 90 edges
2. `RuntimeEvent` - 69 edges
3. `Signal` - 52 edges
4. `ToolResult` - 46 edges
5. `_context()` - 46 edges
6. `reduce_state()` - 45 edges
7. `ExecutionResult` - 43 edges
8. `ExecutionIntent` - 42 edges
9. `evaluate_discipline()` - 42 edges
10. `SQLiteExecutionLedger` - 41 edges

## Surprising Connections (you probably didn't know these)
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_walk_forward_split_definitions_are_deterministic()` --calls--> `walk_forward_splits()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `tiny_dataset()` --calls--> `LabelDefinition`  [INFERRED]
  tests/test_quant_development_runner.py → src/axq/labels/base.py

## Import Cycles
- None detected.

## Communities (118 total, 26 thin omitted)

### Community 0 - "test_datasets_phase3.py"
Cohesion: 0.21
Nodes (14): build(), candles(), definition(), DataFrame, Path, RecordingTransformer, test_dataset_reproducibility_config_identity_and_separation(), test_duplicate_timestamp_rejected() (+6 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.09
Nodes (51): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, CollisionPolicy (+43 more)

### Community 2 - "ModelManifest"
Cohesion: 0.13
Nodes (17): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., load_model_manifest(), ModelManifest, BaseModel, Path (+9 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "inference.py"
Cohesion: 0.18
Nodes (18): dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run(), write_json() (+10 more)

### Community 5 - "indicators.py"
Cohesion: 0.19
Nodes (25): aroon(), atr(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+17 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.16
Nodes (33): AgentReasoningBudget, AgentModel, AgentToolRequest, EvidencePolarity, EvidenceReference, HypothesisRelationship, HypothesisStatus, BaseModel (+25 more)

### Community 7 - "timedelta"
Cohesion: 0.21
Nodes (33): initial_runtime_state(), datetime, Apply one causally available event without consulting a wall clock., Construct a canonical state with explicit unknown component values., reduce_state(), test_slow_context_tool_uses_reducer_availability_cursor(), account(), apply() (+25 more)

### Community 8 - "development/config.py"
Cohesion: 0.07
Nodes (42): Architecture, StrEnum, AblationConfig, EvaluationConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+34 more)

### Community 9 - "features/analysis.py"
Cohesion: 0.13
Nodes (27): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+19 more)

### Community 10 - "axq/config.py"
Cohesion: 0.15
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 11 - "evaluate_predictions"
Cohesion: 0.19
Nodes (19): calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), Any, DataFrame, ndarray, Series, Descriptive Quant diagnostics that never select or promote a model. (+11 more)

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

### Community 22 - "datasets/builder.py"
Cohesion: 0.13
Nodes (20): main(), main(), DataFrame, Leakage-safe multi-timeframe alignment., Attach bars only when their UTC close time is at/before the base bar's UTC…, synchronize_completed_bars(), timeframe_delta(), DataFrame (+12 more)

### Community 23 - "test_agent_tools.py"
Cohesion: 0.11
Nodes (25): PredictiveModelEvidenceProvider, Any, Protocol, QuantAgentEvidenceProvider, Return label-to-probability facts without a trading decision., Narrow adapter around the existing frozen Phase 4 QuantAgent., _ExplodingTool, _FailingProvider (+17 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "dataset.py"
Cohesion: 0.14
Nodes (22): load_training_dataset(), _parse_manifest(), Any, Path, Strict loading and identity verification for immutable Phase 3 datasets., _read_json(), evaluate_saved_run(), Any (+14 more)

### Community 26 - "folds.py"
Cohesion: 0.10
Nodes (33): chronological_split(), IndexRange, BaseModel, Path, Deterministic chronological, purged, embargoed split definitions., SplitFold, SplitManifest, walk_forward_splits() (+25 more)

### Community 27 - "RuntimeEvent"
Cohesion: 0.13
Nodes (41): execution_result_to_runtime_event(), Bridge typed execution results into the shared Phase 6 runtime path., Convert actionable execution feedback; local NO_ACTION stays local., BaseModel, datetime, StrEnum, Canonical runtime event envelopes for live and deterministic replay., RuntimeEvent (+33 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.07
Nodes (27): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+19 more)

### Community 29 - "_deterministic.py"
Cohesion: 0.20
Nodes (20): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, fact_map(), Interpretation, numeric(), ObservedFact (+12 more)

### Community 30 - "README.md"
Cohesion: 0.22
Nodes (4): Model registry and promotion contract, Phase 5 development layer, Quant model training, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.10
Nodes (37): FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool, CausalFeatureSnapshot (+29 more)

### Community 33 - "evaluate_discipline"
Cohesion: 0.26
Nodes (34): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., _context(), _policy(), _proposal(), parametrize (+26 more)

### Community 34 - "execution_boundary/__init__.py"
Cohesion: 0.13
Nodes (31): Deterministic entry execution boundary downstream of financial Risk., Append-only SQLite execution ledger and recovery anchors., evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis (+23 more)

### Community 35 - "test_live_replay_parity.py"
Cohesion: 0.29
Nodes (19): Explicitly advanced deterministic replay clock., ReplayClock, JournalOutcomeStatus, JournalRecordType, StrEnum, Run an adapter-provided stream through the one shared semantic path., run_event_stream(), _event() (+11 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "trainer.py"
Cohesion: 0.09
Nodes (36): CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel, Path (+28 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.14
Nodes (14): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+6 more)

### Community 39 - "default_registry"
Cohesion: 0.14
Nodes (17): market_structure_features(), Any, DataFrame, multi_timeframe_features(), Any, DataFrame, price_action_features(), Any (+9 more)

### Community 40 - "Phase 2 feature contract"
Cohesion: 0.25
Nodes (8): Implemented configurable candidate families, Manifest and diagnostics, Missing-value policy, Multi-timeframe and UTC rules, Phase 2 feature contract, Point-in-time invariant, Swing and structure timing, Warm-up policy

### Community 41 - "Phase 5 Quant Model-Development Design"
Cohesion: 0.25
Nodes (7): Architectural boundary, Artifacts and recovery, Components, Data and control flow, Phase 5 Quant Model-Development Design, Purpose, Safety constraints

### Community 42 - "Project status"
Cohesion: 0.25
Nodes (7): Current architecture, Current phase status, Important risks, Project status, Roadmap, Verified state, Working principle and next task

### Community 43 - "ExecutionResult"
Cohesion: 0.12
Nodes (27): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, ExecutionTransport, InMemoryExecutionLedger, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics. (+19 more)

### Community 45 - "canonical_hash"
Cohesion: 0.17
Nodes (3): model_validator, canonical_hash(), Any

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.27
Nodes (21): ChartAgent, _input(), _kernel_fixture(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure() (+13 more)

### Community 49 - "SQLiteExecutionLedger"
Cohesion: 0.15
Nodes (19): Connection, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, _intent(), _link(), _position(), parametrize, _result() (+11 more)

### Community 50 - "Phase 3 dataset contract"
Cohesion: 0.33
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 51 - "Phase 3 label contract"
Cohesion: 0.40
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "runtime/journal.py"
Cohesion: 0.16
Nodes (12): JournalEntry, JournalOutcome, JournalRecord, BaseModel, JournalSemantic, model_validator, Protocol, UTCDateTime (+4 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.18
Nodes (36): default_demo_position_management_policy(), evaluate_position(), Return conservative deterministic demo defaults, not optimized strategy truth., Evaluate one open position without mutating state or invoking execution…, PositionSide, _broker_constraints(), _context(), _fresh() (+28 more)

### Community 55 - "Phase 5 local Quant experiment workflow"
Cohesion: 0.67
Nodes (3): Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review

### Community 68 - "comparison.py"
Cohesion: 0.33
Nodes (7): compare_runs(), Any, Path, Compare completed development runs without retraining or scalar ranking., _read(), main(), Compare completed Phase 5 runs without retraining.

### Community 69 - "runner.py"
Cohesion: 0.11
Nodes (32): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+24 more)

### Community 70 - "Tool-Augmented Agentic Architecture"
Cohesion: 0.10
Nodes (20): Deferred risks, Event model and causality, Existing components reused, Explicitly unimplemented after Phase 7 Task 7, Explicitly untouched, Implemented shared path and future paths, Invariants, Live/replay ports (+12 more)

### Community 71 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 6 Tool-Augmented Agentic Baseline Implementation Plan, Task 1: Canonical runtime events and shared state, Task 2: Clock, event source, and causal state reducer, Task 3: Tool facts and optional predictive-model adapter, Task 4: Stateful specialist evidence contracts, Task 5: M5 thesis and intrabar scenario state machine, Task 6: Initial specialist agents and evidence bundle (+2 more)

### Community 72 - "RunStateStore"
Cohesion: 0.42
Nodes (3): Any, Path, RunStateStore

### Community 73 - "AgentEvidence"
Cohesion: 0.15
Nodes (17): AgentInput, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition., SpecialistAgent, transition_agent() (+9 more)

### Community 74 - "datasets/__init__.py"
Cohesion: 0.21
Nodes (11): DatasetBuildResult, Path, write_dataset(), DatasetBuildConfig, BaseModel, RowPolicy, SplitPolicy, DatasetManifest (+3 more)

### Community 75 - "replay.py"
Cohesion: 0.10
Nodes (19): ScenarioTransition, Protocol, Clock contract used outside the pure reducer., Return the current instant in UTC., RuntimeClock, EvidenceBundle, EvidenceKernel, BaseModel (+11 more)

### Community 76 - "test_execution_boundary.py"
Cohesion: 0.15
Nodes (36): The transport failed before submission could be accepted., Submission may have reached the broker and requires reconciliation., TransportFailure, UnknownSubmissionState, default_execution_policy(), Return the conservative, execution-disabled baseline policy., ExecutionMode, _adapter() (+28 more)

### Community 77 - "reconciliation.py"
Cohesion: 0.28
Nodes (13): _conflict_reason(), _finding(), _object_id(), datetime, Protocol, Deterministic exact-linkage comparison of local and broker execution state., reconcile_execution_state(), ReconciliationLedger (+5 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.14
Nodes (15): Connection, Path, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., SQLiteRuntimeJournal, JournalEventSource, Canonical event source reconstructed from append-only journal records., _event() (+7 more)

### Community 79 - "clock.py"
Cohesion: 0.25
Nodes (6): ensure_utc(), datetime, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Live clock backed by the host system clock., SystemUTCClock

### Community 80 - "momentum_features"
Cohesion: 0.18
Nodes (15): skipif, money_flow_index(), rsi(), momentum_features(), Any, DataFrame, Any, DataFrame (+7 more)

### Community 81 - "RuntimeError"
Cohesion: 0.21
Nodes (8): RuntimeError, build_model(), MajorityClassifier, ProbabilisticClassifier, Any, ndarray, Protocol, Simple baselines and lazy optional model adapters.

### Community 82 - "fusion.py"
Cohesion: 0.17
Nodes (29): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion., SpecialistContribution (+21 more)

### Community 83 - "features/preprocessing.py"
Cohesion: 0.38
Nodes (5): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., test_scaler_fit_boundary_scaffolding()

### Community 84 - "Database"
Cohesion: 0.13
Nodes (10): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Path, DatasetManifest, BaseModel (+2 more)

### Community 85 - "position_actions/evaluator.py"
Cohesion: 0.19
Nodes (29): PositionActionContext, PositionActionIntent, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, PositionActionType (+21 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "risk_boundary/evaluator.py"
Cohesion: 0.20
Nodes (24): DisciplineOutcome, build_execution_intent(), RiskContext, Pure construction of provenance-bound execution intents., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links(), MasterProposal, BaseModel (+16 more)

### Community 88 - "statistical_features"
Cohesion: 0.50
Nodes (3): Any, DataFrame, statistical_features()

### Community 89 - "main"
Cohesion: 0.31
Nodes (8): HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel, Path, Explicit user-run MT5 multi-timeframe download and immutable dataset build.

### Community 90 - "discipline/contracts.py"
Cohesion: 0.17
Nodes (23): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult, DisciplineState (+15 more)

### Community 91 - "_context"
Cohesion: 0.18
Nodes (29): default_position_action_policy(), Return conservative deterministic V1 safety defaults., _context(), _evaluate(), _fresh(), _intent(), _management(), _position() (+21 more)

### Community 92 - "datasets/preprocessing.py"
Cohesion: 0.36
Nodes (6): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only.

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "position_management/contracts.py"
Cohesion: 0.20
Nodes (19): MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy, PositionManagementReason, PositionManagementResult, BaseModel (+11 more)

### Community 95 - "evidence"
Cohesion: 0.15
Nodes (20): HypothesisInvalidation, model_validator, evidence(), datetime, parametrize, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields(), test_agent_evidence_identity_is_deterministic_and_round_trips() (+12 more)

### Community 96 - "update_scenario"
Cohesion: 0.26
Nodes (24): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), _agent_pair(), _create(), _event(), _market(), datetime, parametrize (+16 more)

### Community 97 - "Signal"
Cohesion: 0.15
Nodes (13): ExecutionInstruction, MarketRegime, MasterDecision, BaseModel, datetime, field_validator, model_validator, StrEnum (+5 more)

### Community 98 - "test_runtime_state.py"
Cohesion: 0.20
Nodes (20): account(), feedback(), freshness(), market(), order(), position(), datetime, parametrize (+12 more)

### Community 99 - "test_foundation.py"
Cohesion: 0.17
Nodes (9): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., candles(), DataTests, FeatureTests, DataFrame (+1 more)

### Community 100 - "ComponentFreshness"
Cohesion: 0.13
Nodes (6): _unknown_freshness(), _updated_freshness(), ComponentFreshness, model_validator, _fresh(), _fresh()

### Community 101 - "ContractAndRiskTests"
Cohesion: 0.36
Nodes (7): calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext, RiskLimits, veto_reasons(), ContractAndRiskTests

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "test_quant_development_runner.py"
Cohesion: 0.67
Nodes (6): experiment(), Path, test_compare_runs_uses_multiple_evidence_dimensions(), test_dry_run_validates_dataset_without_creating_or_fitting(), test_tiny_run_writes_required_verified_artifacts(), tiny_dataset()

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "_snapshot"
Cohesion: 0.60
Nodes (5): broker_snapshot_runtime_events(), _snapshot(), test_expired_thesis_blocks_resume_without_mutating_or_reviving_it(), test_runtime_refresh_uses_canonical_exposure_and_constraint_events(), test_safe_resume_requires_fresh_state_and_resolved_reconciliation()

### Community 108 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 110 - "EventSource"
Cohesion: 0.40
Nodes (4): EventSource, Protocol, Source of events already ordered for causal reduction., Yield events in canonical availability order.

## Knowledge Gaps
- **171 isolated node(s):** `Contract design`, `Documentation and graph`, `Journal integration`, `Pure evaluator`, `Scope` (+166 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 544 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `LabelDefinition`, `ModelManifest`, `agents/__init__.py`, `development/config.py`, `datasets/builder.py`, `folds.py`, `RuntimeEvent`, `_deterministic.py`, `ToolResult`, `execution_boundary/__init__.py`, `trainer.py`, `ExecutionResult`, `model_validator`, `runtime/journal.py`, `runner.py`, `AgentEvidence`, `datasets/__init__.py`, `replay.py`, `fusion.py`, `Database`, `position_actions/evaluator.py`, `risk_boundary/evaluator.py`, `discipline/contracts.py`, `position_management/contracts.py`, `evidence`, `ComponentFreshness`, `.validate_and_bind_identity`, `model_validator`, `model_validator`, `model_validator`, `.validate_bindings_and_identity`, `.validate_and_bind_identity`, `.validate_event`, `.validate_and_bind_identity`, `.validate_and_bind_identity`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `axq/features/registry.py`, `test_foundation.py`, `indicators.py`, `features/analysis.py`, `axq/config.py`, `breakout_features`, `momentum_features`, `datasets/builder.py`, `test_agent_tools.py`, `statistical_features`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `assemble_dataset()` connect `datasets/builder.py` to `test_datasets_phase3.py`, `LabelDefinition`, `default_registry`, `test_quant_development_runner.py`, `axq/config.py`, `datasets/__init__.py`, `canonical_hash`, `main`, `folds.py`, `dataset.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 85 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 85 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ToolResult` (e.g. with `FeatureFactTool` and `SlowContextFactTool`) actually correct?**
  _`ToolResult` has 6 INFERRED edges - model-reasoned connections that need verification._