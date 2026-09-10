# Graph Report - phase-7-decision-execution  (2026-09-10)

## Corpus Check
- 231 files · ~105,093 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2389 nodes · 7270 edges · 127 communities (109 shown, 17 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 1084 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2dd80236`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- datasets/__init__.py
- LabelDefinition
- LocalModelRegistry
- axq/features/registry.py
- inference.py
- indicators.py
- canonical_hash
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
- runtime/__init__.py
- Architecture decision log
- _deterministic.py
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
- ExecutionIntent
- CausalFeatureSnapshot
- quant/config.py
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- position.py
- Phase 3 dataset contract
- Phase 3 label contract
- .from_semantic
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
- AgentEvidence
- EntryGateway
- RuntimeStreamRunner
- test_execution_boundary.py
- snapshot.py
- SQLiteRuntimeJournal
- ensure_utc
- test_feature_formulas.py
- entry.py
- fusion.py
- PositionGateway
- Database
- position_actions/evaluator.py
- Global Constraints
- risk_boundary/evaluator.py
- statistical_features
- main
- discipline/contracts.py
- _context
- SplitManifest
- Global Constraints
- MetaTrader5Gateway
- evidence
- update_scenario
- schemas.py
- test_runtime_state.py
- SnapshotGateway
- ComponentFreshness
- ContractAndRiskTests
- Phase 7 Task 7: Position Action Safety and Journal Plan
- preflight.py
- MT5Gateway
- model_validator
- Position action safety
- FakeMT5Module
- breakout_features
- generate_labels
- RuntimeEvent
- _MT5Module
- run_event_stream
- labels/analysis.py
- atr
- ToolCatalog
- EvidenceBundle
- SemanticTraceStep
- PredictiveModelEvidenceProvider
- Phase 7 Task 8 Direct MT5 Transport Design
- DatasetManifest
- Global constraints
- test_runtime_journal.py
- AgentToolRequest
- MT5SymbolMapping
- multi_timeframe_features
- price_action_features

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 96 edges
2. `RuntimeEvent` - 71 edges
3. `Signal` - 57 edges
4. `ExecutionIntent` - 53 edges
5. `reduce_state()` - 46 edges
6. `ToolResult` - 46 edges
7. `_context()` - 46 edges
8. `ExecutionResult` - 45 edges
9. `_context()` - 43 edges
10. `evaluate_discipline()` - 42 edges

## Surprising Connections (you probably didn't know these)
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py
- `main()` --calls--> `quality_report()`  [INFERRED]
  data/build_features.py → src/axq/features/analysis.py
- `main()` --calls--> `default_registry()`  [INFERRED]
  data/build_features.py → src/axq/features/registry.py
- `main()` --calls--> `assemble_dataset()`  [INFERRED]
  data/build_mt5_dataset.py → src/axq/datasets/builder.py

## Import Cycles
- None detected.

## Communities (127 total, 17 thin omitted)

### Community 0 - "datasets/__init__.py"
Cohesion: 0.13
Nodes (22): DatasetBuildResult, Path, write_dataset(), DatasetBuildConfig, BaseModel, RowPolicy, SplitPolicy, DatasetManifest (+14 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.13
Nodes (31): BarrierMode, CollisionPolicy, EntryReference, LabelDefinition, LabelKind, BaseModel, model_validator, StrEnum (+23 more)

### Community 2 - "LocalModelRegistry"
Cohesion: 0.17
Nodes (12): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., LocalModelRegistry, ModelState, Any, BaseModel (+4 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "inference.py"
Cohesion: 0.13
Nodes (24): dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run(), write_json() (+16 more)

### Community 5 - "indicators.py"
Cohesion: 0.19
Nodes (25): skipif, aroon(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+17 more)

### Community 6 - "canonical_hash"
Cohesion: 0.10
Nodes (26): Shared specialist-agent evidence and persistent-memory contracts., ContinuityStatus, _create_thesis(), EntryEligibility, _new_scenarios(), model_validator, StrEnum, UTCDateTime (+18 more)

### Community 7 - "timedelta"
Cohesion: 0.23
Nodes (29): initial_runtime_state(), Construct a canonical state with explicit unknown component values., account(), apply(), event(), feedback(), fresh(), market() (+21 more)

### Community 8 - "development/config.py"
Cohesion: 0.07
Nodes (46): Architecture, StrEnum, AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config() (+38 more)

### Community 9 - "features/analysis.py"
Cohesion: 0.13
Nodes (27): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+19 more)

### Community 10 - "axq/config.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 11 - "evaluate_predictions"
Cohesion: 0.08
Nodes (34): ProbabilityCalibrator, ndarray, Validation-only probability calibration without OOS access., evaluate_challenger_evidence(), Any, Advisory Champion/Challenger evidence contract., calibration_diagnostics(), compare_calibration_methods() (+26 more)

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

### Community 23 - "test_agent_tools.py"
Cohesion: 0.21
Nodes (20): FeatureFactTool, _ExplodingTool, _FailingProvider, _freshness(), _input(), Any, datetime, _SimilarityProvider (+12 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "dataset.py"
Cohesion: 0.22
Nodes (11): load_training_dataset(), _parse_manifest(), Any, Path, Strict loading and identity verification for immutable Phase 3 datasets., _read_json(), evaluate_saved_run(), Any (+3 more)

### Community 26 - "folds.py"
Cohesion: 0.10
Nodes (27): QuantTrainingConfig, _aggregate_fold_metrics(), completed_fold_summary(), DevelopmentFoldResult, fold_identity(), Any, DataFrame, Path (+19 more)

### Community 27 - "runtime/__init__.py"
Cohesion: 0.15
Nodes (39): Bridge typed execution results into the shared Phase 6 runtime path., position_action_result_to_runtime_event(), Dedicated append-only transport contracts for safe position actions., Strict contracts for the deterministic financial Risk boundary., StrEnum, Canonical runtime event envelopes for live and deterministic replay., RuntimeEventType, Versioned contracts and deterministic reduction for live and replay. (+31 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.07
Nodes (28): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+20 more)

### Community 29 - "_deterministic.py"
Cohesion: 0.19
Nodes (23): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, EvidencePolarity, StrEnum, Strict, replay-safe specialist-agent evidence contracts., ReasoningMode (+15 more)

### Community 30 - "README.md"
Cohesion: 0.24
Nodes (4): Model registry and promotion contract, Phase 5 development layer, Quant model training, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.20
Nodes (28): FreshnessStatus, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, fact_name(), FeatureValue, BaseModel (+20 more)

### Community 33 - "Signal"
Cohesion: 0.26
Nodes (35): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., Signal, _context(), _policy(), _proposal() (+27 more)

### Community 34 - "execution_boundary/__init__.py"
Cohesion: 0.06
Nodes (68): Deterministic entry execution boundary downstream of financial Risk., Connection, Append-only SQLite execution ledger and recovery anchors., Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, evaluate_resume_readiness(), _is_fresh(), datetime (+60 more)

### Community 35 - "test_live_replay_parity.py"
Cohesion: 0.39
Nodes (15): Explicitly advanced deterministic replay clock., ReplayClock, JournalRecordType, _event(), _kernel(), datetime, _scenario_transition(), _snapshot() (+7 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "trainer.py"
Cohesion: 0.12
Nodes (23): Device, load_quant_config(), Path, DataFrame, TrainingDataset, Any, Conservative local device discovery with safe CPU fallback., resolve_device() (+15 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.13
Nodes (15): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+7 more)

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
Nodes (22): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, InMemoryExecutionLedger, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics., Process one immutable intent idempotently. (+14 more)

### Community 44 - "CausalFeatureSnapshot"
Cohesion: 0.12
Nodes (9): CausalFeatureSnapshot, Any, FactScalar, field_validator, model_validator, Protocol, Return causal distributional evidence without interpreting direction., SimilarityEvidence (+1 more)

### Community 45 - "quant/config.py"
Cohesion: 0.16
Nodes (20): CalibrationConfig, FeatureSelectionConfig, HoldPolicyConfig, PreprocessingConfig, BaseModel, Strict, hashable configuration for Quant Agent training., FrozenPreprocessor, DataFrame (+12 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.27
Nodes (21): ChartAgent, _input(), _kernel_fixture(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure() (+13 more)

### Community 49 - "position.py"
Cohesion: 0.12
Nodes (18): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), datetime, Demo-only MetaTrader 5 transport for Task 7 position-action intents. (+10 more)

### Community 50 - "Phase 3 dataset contract"
Cohesion: 0.29
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 51 - "Phase 3 label contract"
Cohesion: 0.33
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - ".from_semantic"
Cohesion: 0.32
Nodes (5): JournalSemantic, model_validator, UTCDateTime, _record_type(), _semantic_id()

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
Cohesion: 0.11
Nodes (29): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+21 more)

### Community 70 - "Tool-Augmented Agentic Architecture"
Cohesion: 0.10
Nodes (21): Deferred risks, Event model and causality, Existing components reused, Explicitly unimplemented after Phase 7 Task 8, Explicitly untouched, Implemented shared path and future paths, Invariants, Live/replay ports (+13 more)

### Community 71 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 6 Tool-Augmented Agentic Baseline Implementation Plan, Task 1: Canonical runtime events and shared state, Task 2: Clock, event source, and causal state reducer, Task 3: Tool facts and optional predictive-model adapter, Task 4: Stateful specialist evidence contracts, Task 5: M5 thesis and intrabar scenario state machine, Task 6: Initial specialist agents and evidence bundle (+2 more)

### Community 72 - "RunStateStore"
Cohesion: 0.42
Nodes (3): Any, Path, RunStateStore

### Community 73 - "AgentEvidence"
Cohesion: 0.12
Nodes (25): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+17 more)

### Community 74 - "EntryGateway"
Cohesion: 0.12
Nodes (21): default_execution_policy(), Return the conservative, execution-disabled baseline policy., ExecutionMode, _adapter(), _constants(), EntryGateway, _intent(), _policy() (+13 more)

### Community 75 - "RuntimeStreamRunner"
Cohesion: 0.19
Nodes (12): JournalOutcome, JournalOutcomeStatus, JournalRecord, BaseModel, StrEnum, Exception, JournalSemantic, Feed one source/clock adapter through the unchanged shared kernel. (+4 more)

### Community 76 - "test_execution_boundary.py"
Cohesion: 0.17
Nodes (33): build_execution_intent(), RiskContext, Carry a fully linked Risk PASS into execution without changing it., execution_result_to_runtime_event(), Convert actionable execution feedback; local NO_ACTION stays local., _adapter(), _intent(), _observation() (+25 more)

### Community 77 - "snapshot.py"
Cohesion: 0.19
Nodes (22): BrokerObjectKind, MT5PersistedIntentLink, MT5SnapshotError, Narrow contracts isolating the optional MetaTrader5 package., A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider (+14 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.18
Nodes (8): JournalEntry, Connection, Path, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., SQLiteRuntimeJournal, JournalEventSource, Canonical event source reconstructed from append-only journal records.

### Community 79 - "ensure_utc"
Cohesion: 0.21
Nodes (7): ensure_utc(), datetime, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Return the current instant in UTC., Live clock backed by the host system clock., SystemUTCClock

### Community 80 - "test_feature_formulas.py"
Cohesion: 0.27
Nodes (9): money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility(), test_stochastic_williams_roc_cci_obv_mfi_smoke() (+1 more)

### Community 81 - "entry.py"
Cohesion: 0.12
Nodes (21): ExecutionTransport, RuntimeError, Submission may have reached the broker and requires reconciliation., Submit an already approved intent to the execution transport., UnknownSubmissionState, BrokerExecutionReport, _float_value(), _int_value() (+13 more)

### Community 82 - "fusion.py"
Cohesion: 0.17
Nodes (29): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion., SpecialistContribution (+21 more)

### Community 83 - "PositionGateway"
Cohesion: 0.15
Nodes (14): _adapter(), _constants(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send() (+6 more)

### Community 84 - "Database"
Cohesion: 0.12
Nodes (13): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Path, Path, Append-only SQLite ledger for position-action transport outcomes. (+5 more)

### Community 85 - "position_actions/evaluator.py"
Cohesion: 0.15
Nodes (30): PositionActionContext, PositionActionIntent, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, PositionActionType (+22 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "risk_boundary/evaluator.py"
Cohesion: 0.18
Nodes (21): DisciplineOutcome, Pure construction of provenance-bound execution intents., _validate_upstream_links(), MasterProposal, BaseModel, model_validator, StrEnum, RiskBoundaryModel (+13 more)

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
Cohesion: 0.16
Nodes (34): default_position_action_policy(), Return conservative deterministic V1 safety defaults., PositionSide, StrEnum, _context(), _evaluate(), _fresh(), _intent() (+26 more)

### Community 92 - "SplitManifest"
Cohesion: 0.15
Nodes (16): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., chronological_split(), IndexRange (+8 more)

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "MetaTrader5Gateway"
Cohesion: 0.18
Nodes (9): MT5ConnectionError, RuntimeError, The terminal package or connected terminal is unavailable., _load_mt5(), _mapping(), _mappings(), MetaTrader5Gateway, Lazy concrete wrapper around the Windows-only MetaTrader5 package. (+1 more)

### Community 95 - "evidence"
Cohesion: 0.23
Nodes (15): evidence(), datetime, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields(), test_agent_evidence_identity_is_deterministic_and_round_trips(), test_agent_input_binds_tools_without_exposing_account_state(), test_confidence_cannot_exceed_evidence_quality(), test_degraded_evidence_cannot_claim_high_confidence() (+7 more)

### Community 96 - "update_scenario"
Cohesion: 0.23
Nodes (29): HypothesisRelationship, HypothesisStatus, Apply one M5 or intrabar evidence event without consulting a clock., _terminal_state(), ThesisState, update_scenario(), _updated_scenarios(), _agent_pair() (+21 more)

### Community 97 - "schemas.py"
Cohesion: 0.15
Nodes (12): ExecutionInstruction, MarketRegime, MasterDecision, BaseModel, datetime, field_validator, model_validator, StrEnum (+4 more)

### Community 98 - "test_runtime_state.py"
Cohesion: 0.20
Nodes (20): account(), feedback(), freshness(), market(), order(), position(), datetime, parametrize (+12 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.15
Nodes (8): _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_creates_canonical_events_and_reduces_through_shared_path(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket(), test_snapshot_maps_account_market_books_exposure_and_constraints()

### Community 100 - "ComponentFreshness"
Cohesion: 0.15
Nodes (4): _unknown_freshness(), ComponentFreshness, model_validator, _fresh()

### Community 101 - "ContractAndRiskTests"
Cohesion: 0.36
Nodes (7): calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext, RiskLimits, veto_reasons(), ContractAndRiskTests

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "preflight.py"
Cohesion: 0.24
Nodes (15): The transport failed before submission could be accepted., TransportFailure, _account_mode(), _float_value(), _int_value(), _positive_float(), datetime, Fail-closed MetaTrader 5 entry preflight and request construction. (+7 more)

### Community 104 - "MT5Gateway"
Cohesion: 0.11
Nodes (6): MT5Constants, MT5Gateway, BaseModel, Protocol, Optional, demo-safe MetaTrader5 gateway and adapters., _constants()

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "FakeMT5Module"
Cohesion: 0.13
Nodes (5): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity()

### Community 108 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 109 - "generate_labels"
Cohesion: 0.32
Nodes (14): generate_labels(), DataFrame, barrier_definition(), bars(), DataFrame, parametrize, test_direction_horizons(), test_direction_threshold_modes_and_neutral() (+6 more)

### Community 110 - "RuntimeEvent"
Cohesion: 0.12
Nodes (14): BaseModel, datetime, model_validator, RuntimeEvent, EvidenceKernel, Reduce an event, resolve bounded facts, and update specialists in fixed order., EventSource, InMemoryEventSource (+6 more)

### Community 112 - "run_event_stream"
Cohesion: 0.20
Nodes (8): ScenarioTransition, Protocol, Clock contract used outside the pure reducer., RuntimeClock, Protocol, RuntimeJournal, Run an adapter-provided stream through the one shared semantic path., run_event_stream()

### Community 113 - "labels/analysis.py"
Cohesion: 0.24
Nodes (9): dataset_quality_report(), Any, DataFrame, compare_label_definitions(), label_balance(), Any, DataFrame, Series (+1 more)

### Community 114 - "atr"
Cohesion: 0.29
Nodes (9): atr(), true_range(), market_structure_features(), Any, DataFrame, Causal market-structure features. A candidate pivot at position p is emitted at…, Any, DataFrame (+1 more)

### Community 115 - "ToolCatalog"
Cohesion: 0.24
Nodes (4): ToolCatalog, AnalyticalTool, Protocol, Return deterministic facts for one causal input.

### Community 116 - "EvidenceBundle"
Cohesion: 0.36
Nodes (3): EvidenceBundle, BaseModel, model_validator

### Community 117 - "SemanticTraceStep"
Cohesion: 0.33
Nodes (4): BaseModel, model_validator, SemanticTraceStep, StreamRun

### Community 118 - "PredictiveModelEvidenceProvider"
Cohesion: 0.20
Nodes (6): PredictiveModelEvidenceProvider, Any, Protocol, QuantAgentEvidenceProvider, Return label-to-probability facts without a trading decision., Narrow adapter around the existing frozen Phase 4 QuantAgent.

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
Cohesion: 0.50
Nodes (7): _event(), datetime, _snapshot(), test_feature_snapshots_can_be_recovered_by_event_without_mutation(), test_journal_is_append_only_and_keeps_deterministic_order(), test_journal_replay_orders_events_by_causal_availability(), test_journal_round_trip_preserves_typed_semantic_identity()

### Community 123 - "AgentToolRequest"
Cohesion: 0.29
Nodes (3): AgentToolRequest, model_validator, ReasoningRecord

### Community 124 - "MT5SymbolMapping"
Cohesion: 0.29
Nodes (3): MT5SymbolMapping, model_validator, test_symbol_mapping_is_explicit_auditable_and_deterministic()

### Community 125 - "multi_timeframe_features"
Cohesion: 0.50
Nodes (3): multi_timeframe_features(), Any, DataFrame

### Community 126 - "price_action_features"
Cohesion: 0.50
Nodes (3): price_action_features(), Any, DataFrame

## Knowledge Gaps
- **186 isolated node(s):** `adaptive-xauusd-trader`, `Repository-start workflow`, `Graphify`, `Current capabilities`, `Setup (Windows PowerShell)` (+181 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 666 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `datasets/__init__.py`, `LabelDefinition`, `inference.py`, `development/config.py`, `datasets/builder.py`, `folds.py`, `runtime/__init__.py`, `_deterministic.py`, `ToolResult`, `execution_boundary/__init__.py`, `ExecutionIntent`, `CausalFeatureSnapshot`, `quant/config.py`, `.from_semantic`, `_context`, `runner.py`, `AgentEvidence`, `snapshot.py`, `fusion.py`, `Database`, `position_actions/evaluator.py`, `risk_boundary/evaluator.py`, `discipline/contracts.py`, `SplitManifest`, `ComponentFreshness`, `model_validator`, `RuntimeEvent`, `EvidenceBundle`, `SemanticTraceStep`, `DatasetManifest`, `AgentToolRequest`, `MT5SymbolMapping`?**
  _High betweenness centrality (0.178) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `schemas.py`, `execution_boundary/__init__.py`, `inference.py`, `ContractAndRiskTests`, `preflight.py`, `EntryGateway`, `ExecutionIntent`, `test_execution_boundary.py`, `_context`, `entry.py`, `fusion.py`, `position_actions/evaluator.py`, `_context`, `risk_boundary/evaluator.py`, `discipline/contracts.py`, `runtime/__init__.py`, `test_risk_boundary.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `axq/features/registry.py`, `indicators.py`, `features/analysis.py`, `axq/config.py`, `breakout_features`, `test_feature_formulas.py`, `atr`, `datasets/builder.py`, `test_agent_tools.py`, `statistical_features`, `multi_timeframe_features`, `price_action_features`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ExecutionIntent` (e.g. with `DemoExecutionAdapter` and `ExecutionAdapter`) actually correct?**
  _`ExecutionIntent` has 8 INFERRED edges - model-reasoned connections that need verification._