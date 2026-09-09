# Graph Report - phase-7-decision-execution  (2026-09-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1985 nodes · 6041 edges · 95 communities (78 shown, 16 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 973 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `114f723b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_datasets_phase3.py
- LabelDefinition
- LocalModelRegistry
- axq/features/registry.py
- inference.py
- atr
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
- test_foundation.py
- FreshnessStatus
- System architecture (Phase 0-7 baseline)
- dataset.py
- folds.py
- RuntimeEvent
- Architecture decision log
- ObservedFact
- README.md
- test_risk_boundary.py
- ToolResult
- Signal
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
- CausalFeatureSnapshot
- canonical_hash
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- SQLiteExecutionLedger
- Phase 3 dataset contract
- Phase 3 label contract
- JournalOutcome
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
- test_quant_development_runner.py
- runner.py
- Tool-Augmented Agentic Architecture
- Global Constraints
- RunStateStore
- run_event_stream
- datasets/builder.py
- RuntimeStreamRunner
- test_execution_boundary.py
- reconciliation.py
- SQLiteRuntimeJournal
- ensure_utc
- indicators.py
- ProbabilisticClassifier
- test_runtime_journal.py
- features/preprocessing.py
- Database
- price_action_features
- Global Constraints
- execution_boundary/builder.py
- statistical_features
- main
- QuantAgent
- .probabilities
- datasets/preprocessing.py
- Global Constraints
- volatility_features

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 85 edges
2. `RuntimeEvent` - 69 edges
3. `Signal` - 49 edges
4. `ToolResult` - 46 edges
5. `_context()` - 46 edges
6. `reduce_state()` - 45 edges
7. `evaluate_discipline()` - 42 edges
8. `SQLiteExecutionLedger` - 41 edges
9. `ExecutionResult` - 40 edges
10. `ExecutionIntent` - 38 edges

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

## Communities (95 total, 16 thin omitted)

### Community 0 - "test_datasets_phase3.py"
Cohesion: 0.21
Nodes (14): build(), candles(), definition(), DataFrame, Path, RecordingTransformer, test_dataset_reproducibility_config_identity_and_separation(), test_duplicate_timestamp_rejected() (+6 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.09
Nodes (51): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, CollisionPolicy (+43 more)

### Community 2 - "LocalModelRegistry"
Cohesion: 0.25
Nodes (8): LocalModelRegistry, ModelState, Any, BaseModel, Path, StrEnum, Explicit local lifecycle registry; promotion is never automatic., RegistryEntry

### Community 3 - "axq/features/registry.py"
Cohesion: 0.11
Nodes (20): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+12 more)

### Community 4 - "inference.py"
Cohesion: 0.15
Nodes (21): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., dump_artifact(), file_hash(), load_artifact(), Any (+13 more)

### Community 5 - "atr"
Cohesion: 0.19
Nodes (20): aroon(), atr(), directional_movement(), DataFrame, Series, Wilder average (RMA): SMA seed followed by alpha=1/period recursion., sma(), supertrend() (+12 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.05
Nodes (100): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+92 more)

### Community 7 - "timedelta"
Cohesion: 0.12
Nodes (49): initial_runtime_state(), Construct a canonical state with explicit unknown component values., account(), apply(), event(), feedback(), fresh(), market() (+41 more)

### Community 8 - "development/config.py"
Cohesion: 0.07
Nodes (45): AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+37 more)

### Community 9 - "features/analysis.py"
Cohesion: 0.13
Nodes (27): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+19 more)

### Community 10 - "axq/config.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 11 - "evaluate_predictions"
Cohesion: 0.16
Nodes (21): calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), overfitting_report(), Any, DataFrame, ndarray, Series (+13 more)

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

### Community 22 - "test_foundation.py"
Cohesion: 0.09
Nodes (20): main(), main(), main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., DataFrame, Leakage-safe multi-timeframe alignment. (+12 more)

### Community 23 - "FreshnessStatus"
Cohesion: 0.15
Nodes (24): _unknown_freshness(), FreshnessStatus, PredictiveModelEvidenceProvider, Protocol, _ExplodingTool, _FailingProvider, _freshness(), _input() (+16 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "dataset.py"
Cohesion: 0.10
Nodes (25): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., load_training_dataset(), _parse_manifest(), Any, DataFrame (+17 more)

### Community 26 - "folds.py"
Cohesion: 0.19
Nodes (16): ProbabilityCalibrator, ndarray, Validation-only probability calibration without OOS access., _aggregate_fold_metrics(), completed_fold_summary(), DevelopmentFoldResult, fold_identity(), Any (+8 more)

### Community 27 - "RuntimeEvent"
Cohesion: 0.09
Nodes (53): Bridge typed execution results into the shared Phase 6 runtime path., UTC clocks shared by live processing and deterministic replay., BaseModel, datetime, StrEnum, Canonical runtime event envelopes for live and deterministic replay., RuntimeEvent, RuntimeEventType (+45 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.07
Nodes (26): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+18 more)

### Community 29 - "ObservedFact"
Cohesion: 0.20
Nodes (15): Deterministic hierarchical market-structure interpretation., fact_map(), Interpretation, numeric(), ObservedFact, FactScalar, Return deterministic last-by-tool-order values for named factual inputs., HistoricalSimilarityAgent (+7 more)

### Community 30 - "README.md"
Cohesion: 0.22
Nodes (4): Model registry and promotion contract, Phase 5 development layer, Quant model training, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.08
Nodes (66): BaseModel, StrEnum, Strict contracts for the deterministic financial Risk boundary., RiskBoundaryModel, RiskContext, RiskOutcome, RiskPolicy, RiskReason (+58 more)

### Community 32 - "ToolResult"
Cohesion: 0.15
Nodes (30): FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool, fact_name() (+22 more)

### Community 33 - "Signal"
Cohesion: 0.06
Nodes (104): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+96 more)

### Community 34 - "execution_boundary/__init__.py"
Cohesion: 0.12
Nodes (34): Deterministic entry execution boundary downstream of financial Risk., Append-only SQLite execution ledger and recovery anchors., evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis (+26 more)

### Community 35 - "test_live_replay_parity.py"
Cohesion: 0.25
Nodes (19): Explicitly advanced deterministic replay clock., ReplayClock, JournalOutcomeStatus, JournalRecordType, StrEnum, InMemoryEventSource, Small deterministic source used by replay and contract tests., _event() (+11 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "trainer.py"
Cohesion: 0.08
Nodes (43): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+35 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.15
Nodes (13): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+5 more)

### Community 39 - "default_registry"
Cohesion: 0.16
Nodes (15): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars., multi_timeframe_features(), Any, DataFrame, default_registry() (+7 more)

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
Cohesion: 0.16
Nodes (22): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, ExecutionTransport, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics., Process one immutable intent idempotently. (+14 more)

### Community 44 - "CausalFeatureSnapshot"
Cohesion: 0.12
Nodes (8): CausalFeatureSnapshot, Any, FactScalar, field_validator, model_validator, Protocol, Return causal distributional evidence without interpreting direction., SimilarityEvidenceProvider

### Community 45 - "canonical_hash"
Cohesion: 0.05
Nodes (12): model_validator, model_validator, model_validator, model_validator, model_validator, model_validator, model_validator, model_validator (+4 more)

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
Cohesion: 0.13
Nodes (24): Connection, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, broker_snapshot_runtime_events(), ExecutionTransition, _intent(), _link(), _position() (+16 more)

### Community 50 - "Phase 3 dataset contract"
Cohesion: 0.33
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 51 - "Phase 3 label contract"
Cohesion: 0.40
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "JournalOutcome"
Cohesion: 0.21
Nodes (9): JournalEntry, JournalOutcome, JournalRecord, BaseModel, JournalSemantic, model_validator, UTCDateTime, _record_type() (+1 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.10
Nodes (56): MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy, PositionManagementReason, PositionManagementResult, BaseModel (+48 more)

### Community 55 - "Phase 5 local Quant experiment workflow"
Cohesion: 0.67
Nodes (3): Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review

### Community 68 - "test_quant_development_runner.py"
Cohesion: 0.23
Nodes (13): compare_runs(), Any, Path, Compare completed development runs without retraining or scalar ranking., _read(), experiment(), Path, test_compare_runs_uses_multiple_evidence_dimensions() (+5 more)

### Community 69 - "runner.py"
Cohesion: 0.13
Nodes (27): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+19 more)

### Community 70 - "Tool-Augmented Agentic Architecture"
Cohesion: 0.11
Nodes (19): Deferred risks, Event model and causality, Existing components reused, Explicitly unimplemented after Phase 7 Task 6, Explicitly untouched, Implemented shared path and future paths, Invariants, Live/replay ports (+11 more)

### Community 71 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 6 Tool-Augmented Agentic Baseline Implementation Plan, Task 1: Canonical runtime events and shared state, Task 2: Clock, event source, and causal state reducer, Task 3: Tool facts and optional predictive-model adapter, Task 4: Stateful specialist evidence contracts, Task 5: M5 thesis and intrabar scenario state machine, Task 6: Initial specialist agents and evidence bundle (+2 more)

### Community 72 - "RunStateStore"
Cohesion: 0.42
Nodes (3): Any, Path, RunStateStore

### Community 73 - "run_event_stream"
Cohesion: 0.20
Nodes (8): ScenarioTransition, Protocol, Clock contract used outside the pure reducer., RuntimeClock, Protocol, RuntimeJournal, Run an adapter-provided stream through the one shared semantic path., run_event_stream()

### Community 74 - "datasets/builder.py"
Cohesion: 0.13
Nodes (26): assemble_dataset(), dataframe_hash(), DatasetBuildResult, Any, DataFrame, Path, Leakage-safe Phase 3 dataset assembly., _validate_source_frames() (+18 more)

### Community 75 - "RuntimeStreamRunner"
Cohesion: 0.16
Nodes (11): EvidenceBundle, BaseModel, BaseModel, Exception, JournalSemantic, Feed one source/clock adapter through the unchanged shared kernel., _reason_code(), RuntimeStreamRunner (+3 more)

### Community 76 - "test_execution_boundary.py"
Cohesion: 0.13
Nodes (34): RuntimeError, InMemoryExecutionLedger, The transport failed before submission could be accepted., Submission may have reached the broker and requires reconciliation., Tiny ledger reference implementation; persistent ports can implement the…, TransportFailure, UnknownSubmissionState, execution_result_to_runtime_event() (+26 more)

### Community 77 - "reconciliation.py"
Cohesion: 0.28
Nodes (13): _conflict_reason(), _finding(), _object_id(), datetime, Protocol, Deterministic exact-linkage comparison of local and broker execution state., reconcile_execution_state(), ReconciliationLedger (+5 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.19
Nodes (7): Connection, Path, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., SQLiteRuntimeJournal, JournalEventSource, Canonical event source reconstructed from append-only journal records.

### Community 79 - "ensure_utc"
Cohesion: 0.22
Nodes (6): ensure_utc(), datetime, Reject naive timestamps and return a normalized UTC timestamp., Return the current instant in UTC., Live clock backed by the host system clock., SystemUTCClock

### Community 80 - "indicators.py"
Cohesion: 0.16
Nodes (20): skipif, cci(), money_flow_index(), Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1., rsi(), seeded_ema(), stochastic() (+12 more)

### Community 81 - "ProbabilisticClassifier"
Cohesion: 0.24
Nodes (5): MajorityClassifier, ProbabilisticClassifier, Any, ndarray, Protocol

### Community 82 - "test_runtime_journal.py"
Cohesion: 0.44
Nodes (8): _event(), datetime, _snapshot(), test_feature_snapshots_can_be_recovered_by_event_without_mutation(), test_journal_is_append_only_and_keeps_deterministic_order(), test_journal_replay_orders_events_by_causal_availability(), test_journal_round_trip_preserves_typed_semantic_identity(), test_rejection_outcome_is_structured_and_does_not_replace_event()

### Community 83 - "features/preprocessing.py"
Cohesion: 0.38
Nodes (5): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., test_scaler_fit_boundary_scaffolding()

### Community 84 - "Database"
Cohesion: 0.12
Nodes (10): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Path, DatasetManifest, BaseModel (+2 more)

### Community 85 - "price_action_features"
Cohesion: 0.50
Nodes (3): price_action_features(), Any, DataFrame

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "execution_boundary/builder.py"
Cohesion: 0.29
Nodes (10): build_execution_intent(), default_execution_policy(), RiskContext, Pure construction of provenance-bound execution intents., Return the conservative, execution-disabled baseline policy., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links(), ExecutionOrderType (+2 more)

### Community 88 - "statistical_features"
Cohesion: 0.50
Nodes (3): Any, DataFrame, statistical_features()

### Community 89 - "main"
Cohesion: 0.31
Nodes (8): HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel, Path, Explicit user-run MT5 multi-timeframe download and immutable dataset build.

### Community 90 - "QuantAgent"
Cohesion: 0.30
Nodes (7): Any, datetime, ndarray, Series, QuantAgent, QuantAgentEvidenceProvider, Narrow adapter around the existing frozen Phase 4 QuantAgent.

### Community 92 - "datasets/preprocessing.py"
Cohesion: 0.36
Nodes (6): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only.

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "volatility_features"
Cohesion: 0.67
Nodes (3): Any, DataFrame, volatility_features()

## Knowledge Gaps
- **159 isolated node(s):** `adaptive-xauusd-trader`, `Data pipeline and synchronization`, `Database architecture`, `Dataset and label versioning`, `Failure states` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 521 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `LabelDefinition`, `inference.py`, `agents/__init__.py`, `development/config.py`, `dataset.py`, `folds.py`, `RuntimeEvent`, `test_risk_boundary.py`, `ToolResult`, `Signal`, `execution_boundary/__init__.py`, `trainer.py`, `ExecutionResult`, `CausalFeatureSnapshot`, `JournalOutcome`, `_context`, `runner.py`, `datasets/builder.py`, `Database`?**
  _High betweenness centrality (0.158) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `axq/features/registry.py`, `atr`, `features/analysis.py`, `axq/config.py`, `datasets/builder.py`, `indicators.py`, `price_action_features`, `test_foundation.py`, `FreshnessStatus`, `statistical_features`, `volatility_features`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `assemble_dataset()` connect `datasets/builder.py` to `test_datasets_phase3.py`, `LabelDefinition`, `test_quant_development_runner.py`, `default_registry`, `axq/config.py`, `canonical_hash`, `test_foundation.py`, `main`, `dataset.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ToolResult` (e.g. with `FeatureFactTool` and `SlowContextFactTool`) actually correct?**
  _`ToolResult` has 6 INFERRED edges - model-reasoned connections that need verification._