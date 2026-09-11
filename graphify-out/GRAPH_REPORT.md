# Graph Report - phase-8-reflection-experience  (2026-09-11)

## Corpus Check
- 308 files · ~158,403 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3349 nodes · 10756 edges · 182 communities (141 shown, 40 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 1741 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4cc0cefc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- DailyReflection
- labels/__init__.py
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
- JournalRecord
- System architecture (Phase 0-7 baseline)
- versioning.py
- dataset.py
- RuntimeEvent
- Architecture decision log
- kernel.py
- README.md
- test_risk_boundary.py
- ToolResult
- RuntimeOrchestrator
- SQLiteExecutionLedger
- timedelta
- Global Constraints
- attribution.py
- Phase 0-6 runbook
- default_registry
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- OutcomeAttributionBuilder
- quant/config.py
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- runtime/journal.py
- system.py
- Phase 3 label contract
- execution_boundary/__init__.py
- Repository instructions
- _context
- orchestration/contracts.py
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
- test_execution_boundary.py
- OperatorControls
- MasterProposal
- snapshot.py
- SQLiteRuntimeJournal
- datetime
- test_feature_formulas.py
- discipline/__init__.py
- reflection/__init__.py
- Global Constraints
- Database
- processor.py
- Global Constraints
- ExecutionIntent
- folds.py
- test_agent_tools.py
- Phase 7 deterministic runtime orchestration
- _context
- ReflectionModel
- Global Constraints
- FakeMT5Module
- evidence
- features/analysis.py
- FakeRunner
- SQLiteImprovementProposalStore
- SnapshotGateway
- model_validator
- Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design
- Phase 7 Task 7: Position Action Safety and Journal Plan
- MT5Gateway
- PositionGateway
- ReplayClock
- Position action safety
- .probabilities
- daily.py
- Signal
- RuntimeStreamRunner
- datasets/__init__.py
- LabelDefinition
- session_features
- test_experience_contracts.py
- SQLiteProposalEvaluationStore
- Global Constraints
- CausalFeatureSnapshot
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- EntryGateway
- Global constraints
- LocalModelRegistry
- position_management/contracts.py
- Phase 8 Task 4 Advisory Improvement Proposal Design
- ComponentFreshness
- ExperienceProvenance
- Global Constraints
- test_foundation.py
- models.py
- PositionState
- Phase 8 Task 2 Deterministic Daily Reflection Design
- Global Constraints
- ExperienceType
- run_event_stream
- Deterministic Daily Reflection
- Phase 3 dataset contract
- Global Constraints
- SplitManifest
- test_runtime_journal.py
- DecisionCycle
- risk_boundary/evaluator.py
- Deterministic Weekly Reflection and Pattern Lifecycle
- Advisory Improvement Proposals
- test_experience_analytics_cli.py
- breakout_features
- .evaluate
- price_action_features
- MetaTrader5Gateway
- canonical_hash
- test_quant_development_runner.py
- .bind_identity
- _MT5Module
- Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design
- replay.py
- EvidenceBundle
- ContractAndRiskTests
- Global Constraints
- test_quant_development_config.py
- MT5ConnectionError
- MT5Constants
- model_validator
- model_validator
- Proposal Evaluation
- model_validator
- .normalize_validate_and_bind_identity
- .normalize_validate_and_bind_identity
- EventSource
- model_validator
- .validate_and_bind_identity
- .bind_identity
- model_validator
- FakeGateway
- .bind_identity
- .terminal_path
- .validate_and_bind_identity
- FakeSnapshotProvider
- .validate_and_bind_identity
- .normalize_and_bind_identity
- .validate_event
- .validate_and_bind_identity
- .validate_and_bind_identity

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 157 edges
2. `RuntimeEvent` - 92 edges
3. `Signal` - 92 edges
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
- `test_symbol_mapping_is_explicit_auditable_and_deterministic()` --calls--> `MT5SymbolMapping`  [INFERRED]
  tests/test_mt5_gateway.py → src/axq/mt5/contracts.py
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py

## Import Cycles
- None detected.

## Communities (182 total, 40 thin omitted)

### Community 0 - "DailyReflection"
Cohesion: 0.15
Nodes (31): DailyReflection, build_weekly_reflection(), PatternMetricSummary, PatternSignalClass, StrEnum, WeeklyGuardKind, WeeklySampleGuard, _expected_dates() (+23 more)

### Community 1 - "labels/__init__.py"
Cohesion: 0.18
Nodes (24): BarrierMode, CollisionPolicy, EntryReference, LabelKind, StrEnum, Versioned label contracts. Labels may look forward; features never may., ReturnMode, ThresholdMode (+16 more)

### Community 2 - "ReflectionPolicy"
Cohesion: 0.08
Nodes (46): ReflectionPolicy, _build(), _days(), _emit(), _latest_records(), _load_policy(), main(), _parser() (+38 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "trainer.py"
Cohesion: 0.08
Nodes (43): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., dump_artifact(), file_hash(), load_artifact(), Any (+35 more)

### Community 5 - "indicators.py"
Cohesion: 0.15
Nodes (32): aroon(), atr(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+24 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.08
Nodes (54): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+46 more)

### Community 7 - "update_scenario"
Cohesion: 0.23
Nodes (30): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), StrEnum, RuntimeEventType, _agent_pair(), _create(), _event(), _market() (+22 more)

### Community 8 - "development/config.py"
Cohesion: 0.09
Nodes (33): AblationConfig, EvaluationConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config(), load_tuning_config(), load_walk_forward_config() (+25 more)

### Community 9 - "axq/config.py"
Cohesion: 0.10
Nodes (25): CompletedProcess, main(), HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel (+17 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.16
Nodes (25): DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., FakeEntryAdapter, FakePositionActionAdapter, FakeProcessor, _fresh(), _intent(), _market_event() (+17 more)

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

### Community 22 - "datasets/builder.py"
Cohesion: 0.13
Nodes (20): main(), main(), DataFrame, Leakage-safe multi-timeframe alignment., Attach bars only when their UTC close time is at/before the base bar's UTC…, synchronize_completed_bars(), timeframe_delta(), DataFrame (+12 more)

### Community 23 - "JournalRecord"
Cohesion: 0.17
Nodes (9): JournalEntry, JournalRecord, BaseModel, JournalSemantic, model_validator, Protocol, UTCDateTime, RuntimeJournal (+1 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "versioning.py"
Cohesion: 0.09
Nodes (46): _build(), _emit(), handle_weekly_command(), _history(), _latest(), _policy(), date, Namespace (+38 more)

### Community 26 - "dataset.py"
Cohesion: 0.09
Nodes (23): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., LabelManifest, BaseModel, Path, Canonical label manifests. (+15 more)

### Community 27 - "RuntimeEvent"
Cohesion: 0.12
Nodes (42): BaseModel, datetime, Canonical runtime event envelopes for live and deterministic replay., RuntimeEvent, Versioned contracts and deterministic reduction for live and replay., Reduce a non-decision state refresh without invoking specialists., _account_update(), datetime (+34 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.06
Nodes (34): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+26 more)

### Community 29 - "kernel.py"
Cohesion: 0.20
Nodes (20): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, fact_map(), Interpretation, numeric(), ObservedFact (+12 more)

### Community 30 - "README.md"
Cohesion: 0.17
Nodes (7): Model registry and promotion contract, Phase 5 development layer, Quant model training, Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.15
Nodes (31): FreshnessStatus, FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool (+23 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.17
Nodes (6): RuntimeStatus, JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe., Perform at most one read-only refresh when the bounded cadence elapsed., Own ordering and gates while delegating every trading semantic decision., RuntimeOrchestrator

### Community 34 - "SQLiteExecutionLedger"
Cohesion: 0.12
Nodes (26): Connection, Path, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, broker_snapshot_runtime_events(), ExecutionTransition, _fresh(), _intent() (+18 more)

### Community 35 - "timedelta"
Cohesion: 0.22
Nodes (29): initial_runtime_state(), Construct a canonical state with explicit unknown component values., account(), apply(), event(), feedback(), fresh(), market() (+21 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "attribution.py"
Cohesion: 0.17
Nodes (27): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+19 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.10
Nodes (21): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+13 more)

### Community 39 - "default_registry"
Cohesion: 0.12
Nodes (19): multi_timeframe_features(), Any, DataFrame, fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., default_registry() (+11 more)

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
Cohesion: 0.17
Nodes (12): _canonical_payload(), Experience, Path, Append-only SQLite persistence for normalized experience objects., Durable semantic records; sequence numbers never participate in identity., SQLiteExperienceStore, _decision(), test_conflicting_same_id_content_fails_closed() (+4 more)

### Community 44 - "OutcomeAttributionBuilder"
Cohesion: 0.25
Nodes (13): _anomaly(), _enum_value(), _identity_context(), OutcomeAttributionBuilder, _progressed_to(), _provenance(), Any, Build experiences with exact semantic joins and explicit missing-link markers. (+5 more)

### Community 45 - "quant/config.py"
Cohesion: 0.09
Nodes (37): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+29 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.26
Nodes (22): ChartAgent, _input(), _kernel_fixture(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure() (+14 more)

### Community 49 - "runtime/journal.py"
Cohesion: 0.07
Nodes (34): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), datetime, Demo-only MetaTrader 5 transport for Task 7 position-action intents. (+26 more)

### Community 50 - "system.py"
Cohesion: 0.06
Nodes (61): EntryDecisionInputs, BaseModel, Causal contexts supplied by the runtime-specific context adapter., _identity(), _PendingClose, PendingReplayEntry, _PendingStop, datetime (+53 more)

### Community 51 - "Phase 3 label contract"
Cohesion: 0.40
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "execution_boundary/__init__.py"
Cohesion: 0.11
Nodes (40): Deterministic entry execution boundary downstream of financial Risk., Append-only SQLite execution ledger and recovery anchors., evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis (+32 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.17
Nodes (36): default_demo_position_management_policy(), evaluate_position(), Return conservative deterministic demo defaults, not optimized strategy truth., Evaluate one open position without mutating state or invoking execution…, _broker_constraints(), _context(), _fresh(), _intent() (+28 more)

### Community 55 - "orchestration/contracts.py"
Cohesion: 0.18
Nodes (16): load_runtime_config(), BaseModel, Path, Strict operational configuration for the Phase 7 runtime service., RuntimeConfig, OutcomeCount, StrEnum, Strict orchestration-only contracts for the shared Phase 7 runtime. (+8 more)

### Community 68 - "evaluate_discipline"
Cohesion: 0.26
Nodes (34): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., _context(), _policy(), _proposal(), parametrize (+26 more)

### Community 69 - "runner.py"
Cohesion: 0.11
Nodes (32): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+24 more)

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

### Community 74 - "test_execution_boundary.py"
Cohesion: 0.11
Nodes (46): RuntimeError, Submission may have reached the broker and requires reconciliation., UnknownSubmissionState, build_execution_intent(), default_execution_policy(), RiskContext, Pure construction of provenance-bound execution intents., Return the conservative, execution-disabled baseline policy. (+38 more)

### Community 75 - "OperatorControls"
Cohesion: 0.29
Nodes (3): OperatorControls, Monotonic operator gates: callers cannot use this contract to bypass safety., test_operator_controls_only_become_more_conservative()

### Community 76 - "MasterProposal"
Cohesion: 0.15
Nodes (32): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, MasterProposal, BaseModel, model_validator, StrEnum (+24 more)

### Community 77 - "snapshot.py"
Cohesion: 0.20
Nodes (22): BrokerObjectKind, MT5PersistedIntentLink, MT5SnapshotError, A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider, _optional_float() (+14 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.18
Nodes (7): Connection, Path, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., SQLiteRuntimeJournal, JournalEventSource, Canonical event source reconstructed from append-only journal records.

### Community 79 - "datetime"
Cohesion: 0.22
Nodes (4): datetime, Return the current instant in UTC., Live clock backed by the host system clock., SystemUTCClock

### Community 80 - "test_feature_formulas.py"
Cohesion: 0.23
Nodes (11): skipif, money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility() (+3 more)

### Community 81 - "discipline/__init__.py"
Cohesion: 0.18
Nodes (23): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+15 more)

### Community 82 - "reflection/__init__.py"
Cohesion: 0.14
Nodes (50): AcceptanceCriterion, CandidateKind, CriterionComparator, CriterionOutcome, CriterionOutcomeStatus, CriterionRole, EvaluationAggregateOutcome, FinalOOSPolicy (+42 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "Database"
Cohesion: 0.15
Nodes (8): main(), Database, Connection, Path, Path, Path, Path, Path

### Community 85 - "processor.py"
Cohesion: 0.17
Nodes (29): Concrete composition of existing deterministic Phase 7 decision boundaries., PositionActionContext, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, PositionActionType (+21 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "ExecutionIntent"
Cohesion: 0.12
Nodes (24): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, ExecutionTransport, InMemoryExecutionLedger, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics. (+16 more)

### Community 88 - "folds.py"
Cohesion: 0.19
Nodes (16): ProbabilityCalibrator, ndarray, Validation-only probability calibration without OOS access., _aggregate_fold_metrics(), completed_fold_summary(), DevelopmentFoldResult, fold_identity(), Any (+8 more)

### Community 89 - "test_agent_tools.py"
Cohesion: 0.17
Nodes (21): PredictiveModelEvidenceProvider, Protocol, _ExplodingTool, _FailingProvider, _freshness(), _input(), Any, datetime (+13 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "_context"
Cohesion: 0.16
Nodes (33): default_position_action_policy(), Return conservative deterministic V1 safety defaults., PositionSide, StrEnum, _context(), _evaluate(), _fresh(), _intent() (+25 more)

### Community 92 - "ReflectionModel"
Cohesion: 0.10
Nodes (35): BaseModel, ReflectionModel, ProposalEvidenceGuard, ProposalGuardKind, ProposalTargetComponent, StrEnum, Immutable contracts for advisory improvement proposals., build_improvement_proposals() (+27 more)

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "FakeMT5Module"
Cohesion: 0.12
Nodes (6): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity(), test_symbol_mapping_is_explicit_auditable_and_deterministic()

### Community 95 - "evidence"
Cohesion: 0.15
Nodes (21): EvidenceKernel, Restore committed semantic state before the next event is processed., Reduce an event, resolve bounded facts, and update specialists in fixed order., evidence(), datetime, parametrize, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields() (+13 more)

### Community 96 - "features/analysis.py"
Cohesion: 0.25
Nodes (17): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+9 more)

### Community 98 - "SQLiteImprovementProposalStore"
Cohesion: 0.12
Nodes (37): Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, _build(), _emit(), handle_proposal_command(), _history(), _latest(), _policy(), Any (+29 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.15
Nodes (8): _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_creates_canonical_events_and_reduces_through_shared_path(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket(), test_snapshot_maps_account_market_books_exposure_and_constraints()

### Community 101 - "Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design"
Cohesion: 0.13
Nodes (14): Append-only persistence and supersession, Architecture, Baseline validation, CLI, Exact provenance validation, ISO-week boundary and availability, Knowledge-status lifecycle, Pattern generation (+6 more)

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "MT5Gateway"
Cohesion: 0.07
Nodes (38): The transport failed before submission could be accepted., TransportFailure, MT5Gateway, MT5SymbolMapping, Protocol, Narrow contracts isolating the optional MetaTrader5 package., _float_value(), _int_value() (+30 more)

### Community 104 - "PositionGateway"
Cohesion: 0.16
Nodes (13): _adapter(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send(), test_modify_stop_preserves_ticket_tp_and_cannot_increase_exposure() (+5 more)

### Community 105 - "ReplayClock"
Cohesion: 0.37
Nodes (17): Explicitly advanced deterministic replay clock., ReplayClock, _event(), _kernel(), datetime, _scenario_transition(), _snapshot(), test_duplicate_event_is_journaled_without_second_decision_record() (+9 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 108 - "daily.py"
Cohesion: 0.21
Nodes (28): FindingCategory, FindingSignal, MetricFact, StrEnum, Immutable content-addressed contracts for deterministic daily reflection., ReflectionFinding, SampleGuardRecord, SampleGuardStatus (+20 more)

### Community 109 - "Signal"
Cohesion: 0.35
Nodes (16): Signal, _contribution(), _discipline(), _evidence(), _intent(), _master(), _of_type(), _result() (+8 more)

### Community 110 - "RuntimeStreamRunner"
Cohesion: 0.15
Nodes (9): JournalSemantic, Feed one source/clock adapter through the unchanged shared kernel., Expose the immutable current state for orchestration and diagnostics., Restore durable thesis continuity before accepting a new event., Restore reducer cursors and specialist memory before event intake., Apply a state refresh while preserving specialist memory unchanged., RuntimeStreamRunner, SemanticTraceStep (+1 more)

### Community 111 - "datasets/__init__.py"
Cohesion: 0.16
Nodes (20): DatasetBuildResult, Path, write_dataset(), DatasetBuildConfig, BaseModel, RowPolicy, SplitPolicy, build() (+12 more)

### Community 112 - "LabelDefinition"
Cohesion: 0.16
Nodes (23): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., LabelDefinition, BaseModel (+15 more)

### Community 113 - "session_features"
Cohesion: 0.23
Nodes (10): _local_window(), Any, DataFrame, Series, DST-aware session features. Source timestamps are interpreted as UTC., session_features(), test_london_and_new_york_dst_transitions(), test_manifest_is_reproducible_and_complete() (+2 more)

### Community 114 - "test_experience_contracts.py"
Cohesion: 0.36
Nodes (8): _decision(), _provenance(), test_actual_trade_cannot_be_marked_simulated(), test_counterfactual_is_separate_and_requires_explicit_assumptions(), test_equivalent_decision_content_has_deterministic_identity(), test_experience_rejects_naive_timestamp(), test_trade_preserves_none_separately_from_numeric_zero(), _trade()

### Community 115 - "SQLiteProposalEvaluationStore"
Cohesion: 0.14
Nodes (22): _build_plan(), _emit(), handle_evaluation_command(), _input(), Any, Namespace, Path, CLI handlers for preregistered proposal evaluation evidence. (+14 more)

### Community 116 - "Global Constraints"
Cohesion: 0.22
Nodes (8): Global Constraints, Phase 8 Task 1 Experience Store Implementation Plan, Task 1: Experience contracts, Task 2: Append-only SQLite store, Task 3: Durable replay outcome artifact, Task 4: Exact-link outcome attribution, Task 5: Descriptive analytics and CLI, Task 6: Baseline ingestion and final verification

### Community 117 - "CausalFeatureSnapshot"
Cohesion: 0.09
Nodes (9): RuntimeRunner, CausalFeatureSnapshot, Any, FactScalar, field_validator, model_validator, Protocol, Return causal distributional evidence without interpreting direction. (+1 more)

### Community 118 - "Phase 8 Task 1 Experience Store Design"
Cohesion: 0.22
Nodes (8): Attribution, CLI and analytics, Contracts, Persistence, Phase 8 Task 1 Experience Store Design, Scope, Source authority, Validation

### Community 119 - "Phase 7 Task 8 Direct MT5 Transport Design"
Cohesion: 0.22
Nodes (8): Boundaries, Deferred work, Idempotency and persistence, Phase 7 Task 8 Direct MT5 Transport Design, Requests and response mapping, Safety and modes, Scope, Snapshots and causality

### Community 120 - "EntryGateway"
Cohesion: 0.14
Nodes (17): _adapter(), EntryGateway, _intent(), _policy(), datetime, Exception, parametrize, test_broker_partial_fill_maps_without_resubmitting_remainder() (+9 more)

### Community 121 - "Global constraints"
Cohesion: 0.25
Nodes (7): Global constraints, Phase 7 Task 8 Direct MT5 Transport Implementation Plan, Task 1: Gateway and normalized MT5 contracts, Task 2: Canonical broker snapshots, Task 3: Entry transport and complete dry-run preflight, Task 4: Durable position-action transport, Task 5: Documentation, optional read-only smoke, and final verification

### Community 122 - "LocalModelRegistry"
Cohesion: 0.25
Nodes (8): LocalModelRegistry, ModelState, Any, BaseModel, Path, StrEnum, Explicit local lifecycle registry; promotion is never automatic., RegistryEntry

### Community 123 - "position_management/contracts.py"
Cohesion: 0.20
Nodes (19): MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy, PositionManagementReason, PositionManagementResult, BaseModel (+11 more)

### Community 124 - "Phase 8 Task 4 Advisory Improvement Proposal Design"
Cohesion: 0.20
Nodes (9): Append-only persistence and supersession, CLI, Contracts and identity, Deterministic advisory content, Eligibility, Phase 8 Task 4 Advisory Improvement Proposal Design, Proposal lifecycle, Scope (+1 more)

### Community 125 - "ComponentFreshness"
Cohesion: 0.17
Nodes (4): _unknown_freshness(), ComponentFreshness, model_validator, _fresh()

### Community 126 - "ExperienceProvenance"
Cohesion: 0.33
Nodes (12): ExperienceProvenance, _agent(), _findings(), _management(), _provenance(), datetime, _rejection(), test_agent_position_and_runtime_anomaly_findings_use_exact_daily_sources() (+4 more)

### Community 127 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 3 Weekly Reflection and Pattern Lifecycle Implementation Plan, Task 1: Weekly contracts and semantic identities, Task 2: Pure weekly aggregation and exact provenance, Task 3: Append-only weekly and lifecycle persistence, Task 4: Weekly CLI integration, Task 5: Corrected one-month baseline and durable context

### Community 128 - "test_foundation.py"
Cohesion: 0.11
Nodes (13): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., DatasetManifest, BaseModel, Path, candles() (+5 more)

### Community 129 - "models.py"
Cohesion: 0.22
Nodes (7): build_model(), MajorityClassifier, ProbabilisticClassifier, Any, ndarray, Protocol, Simple baselines and lazy optional model adapters.

### Community 130 - "PositionState"
Cohesion: 0.18
Nodes (21): PositionState, account(), feedback(), freshness(), market(), order(), position(), datetime (+13 more)

### Community 131 - "Phase 8 Task 2 Deterministic Daily Reflection Design"
Cohesion: 0.22
Nodes (8): Causal period rule, CLI, Contracts, Deterministic diagnostics, Persistence and supersession, Phase 8 Task 2 Deterministic Daily Reflection Design, Scope, Validation

### Community 132 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 2 Deterministic Daily Reflection Implementation Plan, Task 1: Reflection contracts and policy, Task 2: Pure daily aggregation, Task 3: Append-only reflection persistence, Task 4: Build orchestration and CLI, Task 5: Baseline validation and durable context

### Community 133 - "ExperienceType"
Cohesion: 0.15
Nodes (16): AttributionSources, _deduplicate(), ExperienceBuild, _index(), BaseModel, Connection, Experience, Path (+8 more)

### Community 134 - "run_event_stream"
Cohesion: 0.22
Nodes (9): Collection, ScenarioTransition, Protocol, Clock contract used outside the pure reducer., RuntimeClock, BaseModel, Run an adapter-provided stream through the one shared semantic path., run_event_stream() (+1 more)

### Community 135 - "Deterministic Daily Reflection"
Cohesion: 0.33
Nodes (5): Causal contract, Deterministic Daily Reflection, Diagnostic families, Persistence, Verified baseline

### Community 136 - "Phase 3 dataset contract"
Cohesion: 0.33
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 137 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 4 Advisory Improvement Proposal Implementation Plan, Task 1: Proposal contracts and identities, Task 2: Pure eligibility, provenance, and proposal construction, Task 3: Append-only proposal and lifecycle persistence, Task 4: CLI integration, Task 5: Unchanged baseline and durable context

### Community 138 - "SplitManifest"
Cohesion: 0.17
Nodes (15): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., chronological_split(), IndexRange (+7 more)

### Community 139 - "test_runtime_journal.py"
Cohesion: 0.50
Nodes (7): _event(), datetime, _snapshot(), test_feature_snapshots_can_be_recovered_by_event_without_mutation(), test_journal_is_append_only_and_keeps_deterministic_order(), test_journal_replay_orders_events_by_causal_availability(), test_journal_round_trip_preserves_typed_semantic_identity()

### Community 140 - "DecisionCycle"
Cohesion: 0.43
Nodes (5): DecisionCycle, BaseModel, Auditable classifications emitted by the existing decision boundaries., RuntimeRunSummary, test_summary_is_deterministic_and_counts_existing_results()

### Community 141 - "risk_boundary/evaluator.py"
Cohesion: 0.26
Nodes (17): BaseModel, StrEnum, Strict contracts for the deterministic financial Risk boundary., RiskBoundaryModel, RiskContext, RiskOutcome, RiskPolicy, RiskReason (+9 more)

### Community 142 - "Deterministic Weekly Reflection and Pattern Lifecycle"
Cohesion: 0.33
Nodes (5): Deterministic Weekly Reflection and Pattern Lifecycle, Identity, Knowledge lifecycle, Verified baseline, Weekly contract

### Community 143 - "Advisory Improvement Proposals"
Cohesion: 0.33
Nodes (5): Advisory Improvement Proposals, Eligibility and provenance, Identity and supersession, Lifecycle, Verified baseline

### Community 144 - "test_experience_analytics_cli.py"
Cohesion: 0.80
Nodes (4): _rejection(), test_show_and_summary_cli_emit_json(), test_summary_is_descriptive_and_preserves_unknowns(), _trade()

### Community 145 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 146 - ".evaluate"
Cohesion: 0.25
Nodes (6): EntryContextProvider, PositionActionContextProvider, PositionContextProvider, DeterministicDecisionProcessor, Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, Compose existing pure functions; adapters provide causal context only.

### Community 147 - "price_action_features"
Cohesion: 0.50
Nodes (3): price_action_features(), Any, DataFrame

### Community 148 - "MetaTrader5Gateway"
Cohesion: 0.24
Nodes (4): _mapping(), _mappings(), MetaTrader5Gateway, Operational gateway; paths and process state are never semantic identity.

### Community 149 - "canonical_hash"
Cohesion: 0.18
Nodes (3): model_validator, canonical_hash(), Any

### Community 150 - "test_quant_development_runner.py"
Cohesion: 0.23
Nodes (13): compare_runs(), Any, Path, Compare completed development runs without retraining or scalar ranking., _read(), experiment(), Path, test_compare_runs_uses_multiple_evidence_dimensions() (+5 more)

### Community 153 - "Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design"
Cohesion: 0.17
Nodes (11): Append-only persistence, Candidate contract, CLI, Evaluation result, Identity and serialization, Operator decision boundary, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design, Preregistered plan (+3 more)

### Community 154 - "replay.py"
Cohesion: 0.26
Nodes (8): JournalOutcome, JournalOutcomeStatus, JournalRecordType, StrEnum, Exception, One shared event-stream harness for live-like and replay adapters., _reason_code(), test_rejection_outcome_is_structured_and_does_not_replace_event()

### Community 156 - "ContractAndRiskTests"
Cohesion: 0.36
Nodes (7): calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext, RiskLimits, veto_reasons(), ContractAndRiskTests

### Community 157 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Implementation Plan, Task 1: Evaluation contracts and protected-OOS invariants, Task 2: Pure preregistration and result evaluation, Task 3: Append-only evaluation persistence, Task 4: Evaluation CLI without execution, Task 5: Documentation and final verification

### Community 158 - "test_quant_development_config.py"
Cohesion: 0.39
Nodes (7): experiment_payload(), parametrize, Path, test_experiment_config_is_strict_and_content_addressed(), test_loader_resolves_paths_relative_to_config(), test_run_state_recovers_interrupted_run_and_preserves_identity(), test_tuning_config_rejects_any_oos_objective()

### Community 159 - "MT5ConnectionError"
Cohesion: 0.33
Nodes (5): MT5ConnectionError, RuntimeError, The terminal package or connected terminal is unavailable., _load_mt5(), Lazy concrete wrapper around the Windows-only MetaTrader5 package.

### Community 160 - "MT5Constants"
Cohesion: 0.29
Nodes (5): MT5Constants, BaseModel, _constants(), _constants(), _constants()

### Community 163 - "Proposal Evaluation"
Cohesion: 0.40
Nodes (4): CLI workflow, Governance boundary, Persistence and corrections, Proposal Evaluation

### Community 167 - "EventSource"
Cohesion: 0.40
Nodes (4): EventSource, Protocol, Source of events already ordered for causal reduction., Yield events in canonical availability order.

## Knowledge Gaps
- **294 isolated node(s):** `adaptive-xauusd-trader`, `Repository-start workflow`, `Graphify`, `Current capabilities`, `Setup (Windows PowerShell)` (+289 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 914 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `test_foundation.py`, `ReflectionPolicy`, `PositionState`, `trainer.py`, `agents/__init__.py`, `development/config.py`, `SplitManifest`, `risk_boundary/evaluator.py`, `datasets/builder.py`, `.bind_identity`, `JournalRecord`, `versioning.py`, `dataset.py`, `RuntimeEvent`, `replay.py`, `kernel.py`, `ToolResult`, `model_validator`, `model_validator`, `model_validator`, `attribution.py`, `.normalize_validate_and_bind_identity`, `.normalize_validate_and_bind_identity`, `model_validator`, `.validate_and_bind_identity`, `.bind_identity`, `SQLiteExperienceStore`, `model_validator`, `.bind_identity`, `quant/config.py`, `.validate_and_bind_identity`, `.validate_and_bind_identity`, `runtime/journal.py`, `.normalize_and_bind_identity`, `execution_boundary/__init__.py`, `system.py`, `.validate_event`, `orchestration/contracts.py`, `.validate_and_bind_identity`, `.validate_and_bind_identity`, `runner.py`, `MasterProposal`, `discipline/__init__.py`, `reflection/__init__.py`, `processor.py`, `ExecutionIntent`, `folds.py`, `ReflectionModel`, `SQLiteImprovementProposalStore`, `model_validator`, `MT5Gateway`, `daily.py`, `SQLiteProposalEvaluationStore`, `CausalFeatureSnapshot`, `position_management/contracts.py`, `ComponentFreshness`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `DailyReflection`, `ReflectionPolicy`, `trainer.py`, `test_runtime_orchestration.py`, `risk_boundary/evaluator.py`, `test_experience_analytics_cli.py`, `RuntimeEvent`, `ContractAndRiskTests`, `test_risk_boundary.py`, `SQLiteExecutionLedger`, `attribution.py`, `SQLiteExperienceStore`, `OutcomeAttributionBuilder`, `system.py`, `execution_boundary/__init__.py`, `_context`, `evaluate_discipline`, `schemas.py`, `test_execution_boundary.py`, `MasterProposal`, `discipline/__init__.py`, `processor.py`, `ExecutionIntent`, `_context`, `ReflectionModel`, `MT5Gateway`, `daily.py`, `test_experience_contracts.py`, `EntryGateway`, `ExperienceProvenance`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `RuntimeEvent` connect `RuntimeEvent` to `PositionState`, `agents/__init__.py`, `update_scenario`, `test_runtime_orchestration.py`, `test_runtime_journal.py`, `.evaluate`, `JournalRecord`, `replay.py`, `kernel.py`, `RuntimeOrchestrator`, `SQLiteExecutionLedger`, `timedelta`, `attribution.py`, `EventSource`, `OutcomeAttributionBuilder`, `test_evidence_kernel.py`, `runtime/journal.py`, `system.py`, `.validate_event`, `execution_boundary/__init__.py`, `test_execution_boundary.py`, `SQLiteRuntimeJournal`, `discipline/__init__.py`, `processor.py`, `test_agent_tools.py`, `evidence`, `ReplayClock`, `RuntimeStreamRunner`, `CausalFeatureSnapshot`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 160 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 160 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 70 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ExecutionIntent` (e.g. with `DemoExecutionAdapter` and `ExecutionAdapter`) actually correct?**
  _`ExecutionIntent` has 9 INFERRED edges - model-reasoned connections that need verification._