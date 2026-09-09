# Graph Report - Adaptive XAUUSD Quantitative Trading System  (2026-09-09)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1508 nodes · 4108 edges · 88 communities (71 shown, 16 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 555 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9e15b750`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_datasets_phase3.py
- labels/__init__.py
- LocalModelRegistry
- axq/features/registry.py
- trainer.py
- indicators.py
- agents/__init__.py
- test_foundation.py
- development/config.py
- features/analysis.py
- axq/config.py
- runner.py
- ExperimentTracker
- logging.py
- download_mt5.py
- policy.py
- data/__init__.py
- axq/__init__.py
- adaptive-xauusd-trader
- compute.py
- drift.py
- builder.py
- datasets/__init__.py
- System architecture (Phase 0-6 baseline)
- canonical_hash
- folds.py
- timedelta
- Architecture decision log
- ToolResult
- README.md
- models.py
- tools/__init__.py
- test_quant_phase4.py
- test_agent_tools.py
- load_training_dataset
- Global Constraints
- quant/config.py
- Phase 0-6 runbook
- default_registry
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- LabelDefinition
- multi_timeframe_features
- replay.py
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- RuntimeEvent
- Phase 3 dataset contract
- Phase 3 label contract
- breakout_features
- Repository instructions
- statistical_features
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
- test_quant_development_config.py
- Tool-Augmented Agentic Architecture
- Global Constraints
- RunStateStore
- run_event_stream
- labels/analysis.py
- journal.py
- SQLiteRuntimeJournal
- test_live_replay_parity.py
- kernel.py
- atr
- test_feature_formulas.py
- ToolCatalog
- PredictiveModelEvidenceProvider
- EvidenceBundle
- LabelManifest
- model_validator
- SimilarityEvidenceProvider
- price_action_features

## God Nodes (most connected - your core abstractions)
1. `RuntimeEvent` - 63 edges
2. `canonical_hash()` - 55 edges
3. `ToolResult` - 46 edges
4. `reduce_state()` - 39 edges
5. `DeterministicSpecialistAgent` - 35 edges
6. `LabelDefinition` - 31 edges
7. `AgentEvidence` - 30 edges
8. `AgentMemory` - 29 edges
9. `initial_runtime_state()` - 29 edges
10. `train_quant_model()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_walk_forward_split_definitions_are_deterministic()` --calls--> `walk_forward_splits()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `main()` --uses--> `Database`  [INFERRED]
  scripts/init_db.py → src/axq/database.py

## Import Cycles
- None detected.

## Communities (88 total, 16 thin omitted)

### Community 0 - "test_datasets_phase3.py"
Cohesion: 0.21
Nodes (14): build(), candles(), definition(), DataFrame, Path, RecordingTransformer, test_dataset_reproducibility_config_identity_and_separation(), test_duplicate_timestamp_rejected() (+6 more)

### Community 1 - "labels/__init__.py"
Cohesion: 0.18
Nodes (24): BarrierMode, CollisionPolicy, EntryReference, LabelKind, StrEnum, Versioned label contracts. Labels may look forward; features never may., ReturnMode, ThresholdMode (+16 more)

### Community 2 - "LocalModelRegistry"
Cohesion: 0.16
Nodes (13): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., LocalModelRegistry, ModelState, Any, BaseModel (+5 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "trainer.py"
Cohesion: 0.13
Nodes (30): dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run(), write_json() (+22 more)

### Community 5 - "indicators.py"
Cohesion: 0.19
Nodes (25): skipif, aroon(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+17 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.05
Nodes (92): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+84 more)

### Community 7 - "test_foundation.py"
Cohesion: 0.06
Nodes (34): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., Any, datetime, ndarray, Series (+26 more)

### Community 8 - "development/config.py"
Cohesion: 0.08
Nodes (39): AblationConfig, EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config(), load_tuning_config() (+31 more)

### Community 9 - "features/analysis.py"
Cohesion: 0.13
Nodes (27): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+19 more)

### Community 10 - "axq/config.py"
Cohesion: 0.06
Nodes (34): CompletedProcess, main(), HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel (+26 more)

### Community 11 - "runner.py"
Cohesion: 0.16
Nodes (24): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+16 more)

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

### Community 22 - "builder.py"
Cohesion: 0.15
Nodes (17): main(), main(), DataFrame, Leakage-safe multi-timeframe alignment., Attach bars only when their UTC close time is at/before the base bar's UTC…, synchronize_completed_bars(), timeframe_delta(), DataFrame (+9 more)

### Community 23 - "datasets/__init__.py"
Cohesion: 0.22
Nodes (16): DatasetBuildResult, Path, write_dataset(), DatasetBuildConfig, BaseModel, RowPolicy, SplitPolicy, experiment() (+8 more)

### Community 24 - "System architecture (Phase 0-6 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "canonical_hash"
Cohesion: 0.08
Nodes (25): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., fit_on_training_only(), FitTransformComponent, Any, DataFrame (+17 more)

### Community 26 - "folds.py"
Cohesion: 0.19
Nodes (19): WalkForwardConfig, _aggregate_fold_metrics(), completed_fold_summary(), development_split_manifest(), DevelopmentFoldResult, Any, DataFrame, Path (+11 more)

### Community 27 - "timedelta"
Cohesion: 0.06
Nodes (92): StrEnum, Canonical runtime event envelopes for live and deterministic replay., RuntimeEventType, Versioned contracts and deterministic reduction for live and replay., _account_update(), initial_runtime_state(), datetime, Pure, validated reduction of runtime events into shared state. (+84 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.09
Nodes (22): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+14 more)

### Community 29 - "ToolResult"
Cohesion: 0.19
Nodes (23): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, Strict, replay-safe specialist-agent evidence contracts., fact_map(), Interpretation, numeric() (+15 more)

### Community 30 - "README.md"
Cohesion: 0.24
Nodes (4): Model registry and promotion contract, Phase 5 development layer, Quant model training, Quant Agent contract

### Community 31 - "models.py"
Cohesion: 0.22
Nodes (7): build_model(), MajorityClassifier, ProbabilisticClassifier, Any, ndarray, Protocol, Simple baselines and lazy optional model adapters.

### Community 32 - "tools/__init__.py"
Cohesion: 0.21
Nodes (25): FreshnessStatus, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, fact_name(), FeatureValue, BaseModel (+17 more)

### Community 33 - "test_quant_phase4.py"
Cohesion: 0.11
Nodes (27): ProbabilityCalibrator, ndarray, Validation-only probability calibration without OOS access., calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), Any, DataFrame (+19 more)

### Community 34 - "test_agent_tools.py"
Cohesion: 0.18
Nodes (20): FeatureFactTool, _ExplodingTool, _FailingProvider, _freshness(), _input(), Any, datetime, _SimilarityProvider (+12 more)

### Community 35 - "load_training_dataset"
Cohesion: 0.19
Nodes (14): load_training_dataset(), _parse_manifest(), Any, Path, _read_json(), evaluate_saved_run(), Any, Reproduce frozen split metrics without fitting or retraining. (+6 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "quant/config.py"
Cohesion: 0.13
Nodes (24): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+16 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.18
Nodes (11): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+3 more)

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

### Community 43 - "LabelDefinition"
Cohesion: 0.21
Nodes (19): compare_label_definitions(), DataFrame, LabelDefinition, BaseModel, model_validator, generate_labels(), DataFrame, barrier_definition() (+11 more)

### Community 44 - "multi_timeframe_features"
Cohesion: 0.50
Nodes (3): multi_timeframe_features(), Any, DataFrame

### Community 45 - "replay.py"
Cohesion: 0.17
Nodes (12): Exception, JournalOutcome, BaseModel, JournalSemantic, model_validator, One shared event-stream harness for live-like and replay adapters., Feed one source/clock adapter through the unchanged shared kernel., _reason_code() (+4 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.29
Nodes (20): ChartAgent, _input(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure(), test_chart_agent_represents_hierarchical_mtf_conflict_as_uncertainty() (+12 more)

### Community 49 - "RuntimeEvent"
Cohesion: 0.12
Nodes (13): BaseModel, datetime, model_validator, RuntimeEvent, JournalEventSource, Canonical event source reconstructed from append-only journal records., EventSource, InMemoryEventSource (+5 more)

### Community 50 - "Phase 3 dataset contract"
Cohesion: 0.29
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 51 - "Phase 3 label contract"
Cohesion: 0.33
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "statistical_features"
Cohesion: 0.50
Nodes (3): Any, DataFrame, statistical_features()

### Community 55 - "Phase 5 local Quant experiment workflow"
Cohesion: 0.67
Nodes (3): Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review

### Community 68 - "comparison.py"
Cohesion: 0.33
Nodes (7): compare_runs(), Any, Path, Compare completed development runs without retraining or scalar ranking., _read(), main(), Compare completed Phase 5 runs without retraining.

### Community 69 - "test_quant_development_config.py"
Cohesion: 0.29
Nodes (8): Atomic, identity-bound state for resumable local experiments., experiment_payload(), parametrize, Path, test_experiment_config_is_strict_and_content_addressed(), test_loader_resolves_paths_relative_to_config(), test_run_state_recovers_interrupted_run_and_preserves_identity(), test_tuning_config_rejects_any_oos_objective()

### Community 70 - "Tool-Augmented Agentic Architecture"
Cohesion: 0.12
Nodes (17): Deferred risks, Event model and causality, Existing components reused, Explicitly unimplemented after Phase 6, Explicitly untouched, Implemented shared path and future paths, Invariants, Live/replay ports (+9 more)

### Community 71 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 6 Tool-Augmented Agentic Baseline Implementation Plan, Task 1: Canonical runtime events and shared state, Task 2: Clock, event source, and causal state reducer, Task 3: Tool facts and optional predictive-model adapter, Task 4: Stateful specialist evidence contracts, Task 5: M5 thesis and intrabar scenario state machine, Task 6: Initial specialist agents and evidence bundle (+2 more)

### Community 72 - "RunStateStore"
Cohesion: 0.42
Nodes (3): Any, Path, RunStateStore

### Community 73 - "run_event_stream"
Cohesion: 0.13
Nodes (13): ScenarioTransition, ensure_utc(), datetime, Protocol, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Clock contract used outside the pure reducer., Return the current instant in UTC. (+5 more)

### Community 74 - "labels/analysis.py"
Cohesion: 0.28
Nodes (7): dataset_quality_report(), Any, DataFrame, label_balance(), Any, Series, Label balance and definition-sensitivity reporting; never resamples data.

### Community 75 - "journal.py"
Cohesion: 0.17
Nodes (11): JournalEntry, JournalRecord, BaseModel, JournalSemantic, model_validator, Protocol, UTCDateTime, Typed append-only runtime journal for deterministic replay. (+3 more)

### Community 76 - "SQLiteRuntimeJournal"
Cohesion: 0.20
Nodes (12): Connection, Path, Small additive SQLite implementation outside the pure decision kernel., SQLiteRuntimeJournal, _event(), datetime, _snapshot(), test_feature_snapshots_can_be_recovered_by_event_without_mutation() (+4 more)

### Community 77 - "test_live_replay_parity.py"
Cohesion: 0.33
Nodes (17): Explicitly advanced deterministic replay clock., ReplayClock, JournalOutcomeStatus, JournalRecordType, StrEnum, _event(), _kernel(), datetime (+9 more)

### Community 78 - "kernel.py"
Cohesion: 0.17
Nodes (8): EvidenceKernel, Shared deterministic specialist-evidence kernel for live and replay., Reduce an event, resolve bounded facts, and update specialists in fixed order., CausalFeatureSnapshot, Any, FactScalar, field_validator, _kernel_fixture()

### Community 79 - "atr"
Cohesion: 0.29
Nodes (9): atr(), true_range(), market_structure_features(), Any, DataFrame, Causal market-structure features. A candidate pivot at position p is emitted at…, Any, DataFrame (+1 more)

### Community 80 - "test_feature_formulas.py"
Cohesion: 0.27
Nodes (9): money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility(), test_stochastic_williams_roc_cci_obv_mfi_smoke() (+1 more)

### Community 81 - "ToolCatalog"
Cohesion: 0.24
Nodes (4): ToolCatalog, AnalyticalTool, Protocol, Return deterministic facts for one causal input.

### Community 82 - "PredictiveModelEvidenceProvider"
Cohesion: 0.20
Nodes (6): PredictiveModelEvidenceProvider, Any, Protocol, QuantAgentEvidenceProvider, Return label-to-probability facts without a trading decision., Narrow adapter around the existing frozen Phase 4 QuantAgent.

### Community 83 - "EvidenceBundle"
Cohesion: 0.36
Nodes (3): EvidenceBundle, BaseModel, model_validator

### Community 84 - "LabelManifest"
Cohesion: 0.33
Nodes (4): LabelManifest, BaseModel, Path, LabelResult

### Community 86 - "SimilarityEvidenceProvider"
Cohesion: 0.40
Nodes (3): Protocol, Return causal distributional evidence without interpreting direction., SimilarityEvidenceProvider

### Community 87 - "price_action_features"
Cohesion: 0.50
Nodes (3): price_action_features(), Any, DataFrame

## Knowledge Gaps
- **140 isolated node(s):** `adaptive-xauusd-trader`, `Data pipeline and synchronization`, `Database architecture`, `Dataset and label versioning`, `Failure states` (+135 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 441 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `labels/__init__.py`, `trainer.py`, `agents/__init__.py`, `development/config.py`, `axq/config.py`, `runner.py`, `builder.py`, `folds.py`, `timedelta`, `ToolResult`, `tools/__init__.py`, `quant/config.py`, `replay.py`, `RuntimeEvent`, `journal.py`, `kernel.py`, `EvidenceBundle`, `LabelManifest`, `model_validator`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `test_agent_tools.py`, `axq/features/registry.py`, `indicators.py`, `test_foundation.py`, `features/analysis.py`, `axq/config.py`, `multi_timeframe_features`, `atr`, `test_feature_formulas.py`, `breakout_features`, `builder.py`, `price_action_features`, `statistical_features`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `assemble_dataset()` connect `builder.py` to `test_datasets_phase3.py`, `default_registry`, `axq/config.py`, `labels/analysis.py`, `LabelDefinition`, `datasets/__init__.py`, `canonical_hash`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `ExecutionFeedbackState`) actually correct?**
  _`RuntimeEvent` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ToolResult` (e.g. with `FeatureFactTool` and `SlowContextFactTool`) actually correct?**
  _`ToolResult` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `reduce_state()` (e.g. with `RuntimeEvent` and `RuntimeEventType`) actually correct?**
  _`reduce_state()` has 24 INFERRED edges - model-reasoned connections that need verification._