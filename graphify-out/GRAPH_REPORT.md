# Graph Report - phase-8-reflection-experience  (2026-09-11)

## Corpus Check
- 323 files · ~165,604 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3475 nodes · 11247 edges · 165 communities (129 shown, 35 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 1872 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ef969459`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- weekly_contracts.py
- labels/__init__.py
- reflection/__main__.py
- axq/features/registry.py
- trainer.py
- default_registry
- agents/__init__.py
- timedelta
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
- .validate_and_bind_identity
- System architecture (Phase 0-7 baseline)
- SQLiteWeeklyReflectionStore
- dataset.py
- runtime/__init__.py
- Architecture decision log
- AgentStatus
- README.md
- test_risk_boundary.py
- ToolResult
- RuntimeOrchestrator
- SQLiteExecutionLedger
- reduce_state
- Global Constraints
- experience/__init__.py
- Phase 0-6 runbook
- MetricScope
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- attribution.py
- quant/config.py
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- PositionActionIntent
- system.py
- Phase 3 label contract
- ComponentFreshness
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
- MT5SnapshotError
- SQLiteRuntimeJournal
- ensure_utc
- preflight.py
- discipline/__init__.py
- reflection/__init__.py
- Global Constraints
- Database
- position_actions/evaluator.py
- Global Constraints
- ExecutionIntent
- folds.py
- test_agent_tools.py
- Phase 7 deterministic runtime orchestration
- _context
- execution_boundary/__init__.py
- Global Constraints
- FakeMT5Module
- evidence
- features/analysis.py
- FakeRunner
- SQLiteImprovementProposalStore
- mt5/__init__.py
- model_validator
- Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design
- Phase 7 Task 7: Position Action Safety and Journal Plan
- MT5Gateway
- PositionGateway
- runtime/journal.py
- Position action safety
- position.py
- ExecutionTransition
- Signal
- QuantAgent
- datasets/__init__.py
- LabelDefinition
- build_mt5_dataset.py
- ExperienceProvenance
- SQLiteProposalEvaluationStore
- Global Constraints
- Phase 8 Task 6 Deterministic Evaluation Execution Adapter Design
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- EntryGateway
- Global constraints
- LocalModelRegistry
- processor.py
- Phase 8 Task 4 Advisory Improvement Proposal Design
- Global Constraints
- test_daily_reflection.py
- Global Constraints
- DatasetManifest
- Deterministic Evaluation Execution
- test_runtime_state.py
- Phase 8 Task 2 Deterministic Daily Reflection Design
- Global Constraints
- AttributionSources
- Deterministic Daily Reflection
- Phase 3 dataset contract
- Global Constraints
- datasets/preprocessing.py
- risk_boundary/evaluator.py
- Deterministic Weekly Reflection and Pattern Lifecycle
- Advisory Improvement Proposals
- .__init__
- MetaTrader5Gateway
- canonical_hash
- test_quant_development_runner.py
- .bind_identity
- _MT5Module
- Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design
- Global Constraints
- model_validator
- model_validator
- Proposal Evaluation
- model_validator
- .normalize_validate_and_bind_identity
- .normalize_validate_and_bind_identity
- RuntimeEvent
- .bind_identity
- model_validator
- FakeGateway
- .bind_identity
- .terminal_path
- .validate_and_bind_identity
- .validate_event
- .validate_and_bind_identity
- .validate_and_bind_identity

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 166 edges
2. `RuntimeEvent` - 92 edges
3. `Signal` - 92 edges
4. `ExecutionIntent` - 64 edges
5. `ExecutionResult` - 55 edges
6. `SQLiteProposalEvaluationStore` - 53 edges
7. `run_system_replay()` - 50 edges
8. `ReflectionModel` - 49 edges
9. `SQLiteExecutionLedger` - 48 edges
10. `reduce_state()` - 48 edges

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

## Communities (165 total, 35 thin omitted)

### Community 0 - "weekly_contracts.py"
Cohesion: 0.08
Nodes (75): DecisionExperience, TradeExperience, FindingCategory, FindingSignal, MetricFact, StrEnum, Immutable content-addressed contracts for deterministic daily reflection., ReflectionFinding (+67 more)

### Community 1 - "labels/__init__.py"
Cohesion: 0.15
Nodes (28): BarrierMode, CollisionPolicy, EntryReference, LabelKind, StrEnum, Versioned label contracts. Labels may look forward; features never may., ReturnMode, ThresholdMode (+20 more)

### Community 2 - "reflection/__main__.py"
Cohesion: 0.06
Nodes (60): DailyReflection, ReflectionPolicy, Any, register_evaluation_commands(), Any, register_execution_commands(), _build(), _days() (+52 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "trainer.py"
Cohesion: 0.07
Nodes (43): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., dump_artifact(), file_hash(), load_artifact(), Any (+35 more)

### Community 5 - "default_registry"
Cohesion: 0.05
Nodes (69): skipif, breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars., aroon(), atr(), cci() (+61 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.08
Nodes (57): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+49 more)

### Community 7 - "timedelta"
Cohesion: 0.26
Nodes (29): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), _agent_pair(), _create(), _event(), _market(), datetime, parametrize (+21 more)

### Community 8 - "development/config.py"
Cohesion: 0.08
Nodes (44): AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+36 more)

### Community 9 - "axq/config.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.16
Nodes (24): DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., FakeEntryAdapter, FakePositionActionAdapter, FakeProcessor, FakeSnapshotProvider, _intent(), _market_event() (+16 more)

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
Cohesion: 0.08
Nodes (29): main(), main(), main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., DataFrame, Leakage-safe multi-timeframe alignment. (+21 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "SQLiteWeeklyReflectionStore"
Cohesion: 0.09
Nodes (42): _build(), _emit(), handle_weekly_command(), _history(), _latest(), _policy(), date, Namespace (+34 more)

### Community 26 - "dataset.py"
Cohesion: 0.10
Nodes (28): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., load_training_dataset(), _parse_manifest(), Any, DataFrame (+20 more)

### Community 27 - "runtime/__init__.py"
Cohesion: 0.12
Nodes (42): BrokerIntentLink, BrokerObjectKind, Immutable contracts for durable execution recovery and safe resume., _provenance_by_ticket(), Read-only MT5 broker snapshot acquisition into canonical recovery state., Immutable contracts for safe actions on authoritative open positions., Strict contracts for deterministic management of already-open positions., Strict contracts for the deterministic financial Risk boundary. (+34 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.06
Nodes (35): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+27 more)

### Community 29 - "AgentStatus"
Cohesion: 0.20
Nodes (17): Deterministic hierarchical market-structure interpretation., AgentStatus, DirectionalBias, fact_map(), Interpretation, numeric(), ObservedFact, FactScalar (+9 more)

### Community 30 - "README.md"
Cohesion: 0.18
Nodes (7): Model registry and promotion contract, Phase 5 development layer, Quant model training, Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.09
Nodes (39): _catalog(), FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool (+31 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.17
Nodes (5): JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe., Perform at most one read-only refresh when the bounded cadence elapsed., Own ordering and gates while delegating every trading semantic decision., RuntimeOrchestrator

### Community 34 - "SQLiteExecutionLedger"
Cohesion: 0.08
Nodes (48): Connection, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, _conflict_reason(), _finding(), _object_id(), datetime, Protocol (+40 more)

### Community 35 - "reduce_state"
Cohesion: 0.20
Nodes (32): initial_runtime_state(), datetime, Apply one causally available event without consulting a wall clock., Construct a canonical state with explicit unknown component values., reduce_state(), test_snapshot_creates_canonical_events_and_reduces_through_shared_path(), account(), apply() (+24 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "experience/__init__.py"
Cohesion: 0.18
Nodes (21): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+13 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.09
Nodes (22): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+14 more)

### Community 39 - "MetricScope"
Cohesion: 0.07
Nodes (71): MetricScope, ProposalEvaluationPlan, SemanticArtifactRef, _aggregate(), canonical_record_bytes(), CanonicalMetricSamplesAdapter, EvaluationAdapterOutput, input_artifact_ref() (+63 more)

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
Cohesion: 0.13
Nodes (17): ExperienceBuild, BaseModel, Experience, ExperienceType, StrEnum, _canonical_payload(), Experience, Path (+9 more)

### Community 44 - "attribution.py"
Cohesion: 0.24
Nodes (17): _anomaly(), _enum_value(), _identity_context(), OutcomeAttributionBuilder, _progressed_to(), _provenance(), Any, Exact-link deterministic reconstruction of normalized Phase 8 experiences. (+9 more)

### Community 45 - "quant/config.py"
Cohesion: 0.10
Nodes (22): Architecture, CalibrationConfig, Device, HoldPolicyConfig, load_quant_config(), BaseModel, Path, StrEnum (+14 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.28
Nodes (21): ChartAgent, _input(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure(), test_chart_agent_represents_hierarchical_mtf_conflict_as_uncertainty() (+13 more)

### Community 49 - "PositionActionIntent"
Cohesion: 0.11
Nodes (13): MT5PositionActionAdapter, Idempotently translate an already-safe position action to exact MT5 calls., PositionActionAdapter, PositionActionIntent, Path, SQLitePositionActionTransportLedger, InMemoryPositionActionTransportLedger, PositionActionTransportLedger (+5 more)

### Community 50 - "system.py"
Cohesion: 0.05
Nodes (64): DeterministicDecisionProcessor, EntryDecisionInputs, BaseModel, Causal contexts supplied by the runtime-specific context adapter., Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, Compose existing pure functions; adapters provide causal context only., _identity(), _PendingClose (+56 more)

### Community 51 - "Phase 3 label contract"
Cohesion: 0.33
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "ComponentFreshness"
Cohesion: 0.06
Nodes (22): evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis, StrEnum, ResolutionStatus (+14 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.16
Nodes (39): ReconciliationKind, ResumeStatus, default_demo_position_management_policy(), evaluate_position(), Return conservative deterministic demo defaults, not optimized strategy truth., Evaluate one open position without mutating state or invoking execution…, _broker_constraints(), _context() (+31 more)

### Community 55 - "orchestration/contracts.py"
Cohesion: 0.14
Nodes (22): load_runtime_config(), BaseModel, Path, Strict operational configuration for the Phase 7 runtime service., RuntimeConfig, DecisionCycle, OutcomeCount, BaseModel (+14 more)

### Community 68 - "evaluate_discipline"
Cohesion: 0.26
Nodes (34): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., _context(), _policy(), _proposal(), parametrize (+26 more)

### Community 69 - "runner.py"
Cohesion: 0.11
Nodes (30): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+22 more)

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
Cohesion: 0.20
Nodes (29): RuntimeError, Submission may have reached the broker and requires reconciliation., UnknownSubmissionState, _adapter(), _intent(), _observation(), _policy(), parametrize (+21 more)

### Community 75 - "OperatorControls"
Cohesion: 0.22
Nodes (5): OperatorControls, Monotonic operator gates: callers cannot use this contract to bypass safety., DecisionCycleProcessor, datetime, test_operator_controls_only_become_more_conservative()

### Community 76 - "MasterProposal"
Cohesion: 0.15
Nodes (32): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, MasterProposal, BaseModel, model_validator, StrEnum (+24 more)

### Community 77 - "MT5SnapshotError"
Cohesion: 0.23
Nodes (15): MT5SnapshotError, A broker snapshot could not be acquired without guessing., _epoch_seconds(), MT5BrokerSnapshotProvider, _optional_float(), _optional_int(), _optional_price(), _optional_str() (+7 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.14
Nodes (15): Connection, Path, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., SQLiteRuntimeJournal, JournalEventSource, Canonical event source reconstructed from append-only journal records., _event() (+7 more)

### Community 79 - "ensure_utc"
Cohesion: 0.17
Nodes (10): ensure_utc(), datetime, Protocol, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Clock contract used outside the pure reducer., Return the current instant in UTC., Live clock backed by the host system clock. (+2 more)

### Community 80 - "preflight.py"
Cohesion: 0.21
Nodes (17): The transport failed before submission could be accepted., TransportFailure, _account_mode(), _float_value(), _int_value(), MT5EntryPreflight, _positive_float(), datetime (+9 more)

### Community 81 - "discipline/__init__.py"
Cohesion: 0.16
Nodes (26): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+18 more)

### Community 82 - "reflection/__init__.py"
Cohesion: 0.11
Nodes (57): Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, BaseModel, ReflectionModel, AcceptanceCriterion, CandidateKind, CriterionComparator, CriterionOutcome, CriterionOutcomeStatus (+49 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "Database"
Cohesion: 0.11
Nodes (10): main(), Database, Connection, Path, Path, Path, Path, Path (+2 more)

### Community 85 - "position_actions/evaluator.py"
Cohesion: 0.13
Nodes (34): PositionActionContext, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, PositionActionType, BaseModel (+26 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "ExecutionIntent"
Cohesion: 0.13
Nodes (16): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, InMemoryExecutionLedger, datetime, Protocol, Process one immutable intent idempotently., Tiny ledger reference implementation; persistent ports can implement the… (+8 more)

### Community 88 - "folds.py"
Cohesion: 0.10
Nodes (32): chronological_split(), IndexRange, BaseModel, Path, Deterministic chronological, purged, embargoed split definitions., SplitFold, SplitManifest, walk_forward_splits() (+24 more)

### Community 89 - "test_agent_tools.py"
Cohesion: 0.11
Nodes (25): PredictiveModelEvidenceProvider, Any, Protocol, QuantAgentEvidenceProvider, Return label-to-probability facts without a trading decision., Narrow adapter around the existing frozen Phase 4 QuantAgent., _ExplodingTool, _FailingProvider (+17 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "_context"
Cohesion: 0.20
Nodes (28): PositionSide, _context(), _evaluate(), _fresh(), _intent(), _management(), _position(), datetime (+20 more)

### Community 92 - "execution_boundary/__init__.py"
Cohesion: 0.21
Nodes (18): Demo-safe execution adapter boundary with explicit idempotency semantics., build_execution_intent(), default_execution_policy(), Pure construction of provenance-bound execution intents., Return the conservative, execution-disabled baseline policy., Carry a fully linked Risk PASS into execution without changing it., ExecutionAccountMode, ExecutionMode (+10 more)

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "FakeMT5Module"
Cohesion: 0.12
Nodes (6): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity(), test_symbol_mapping_is_explicit_auditable_and_deterministic()

### Community 95 - "evidence"
Cohesion: 0.22
Nodes (18): evidence(), datetime, parametrize, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields(), test_agent_evidence_identity_is_deterministic_and_round_trips(), test_agent_input_binds_tools_without_exposing_account_state(), test_agent_input_preserves_non_available_tool_semantics() (+10 more)

### Community 96 - "features/analysis.py"
Cohesion: 0.13
Nodes (27): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+19 more)

### Community 98 - "SQLiteImprovementProposalStore"
Cohesion: 0.10
Nodes (45): _build(), _emit(), handle_proposal_command(), _history(), _latest(), _policy(), Namespace, Path (+37 more)

### Community 99 - "mt5/__init__.py"
Cohesion: 0.11
Nodes (12): MT5Constants, MT5PersistedIntentLink, Narrow contracts isolating the optional MetaTrader5 package., Optional, demo-safe MetaTrader5 gateway and adapters., _constants(), _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure() (+4 more)

### Community 101 - "Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design"
Cohesion: 0.13
Nodes (14): Append-only persistence and supersession, Architecture, Baseline validation, CLI, Exact provenance validation, ISO-week boundary and availability, Knowledge-status lifecycle, Pattern generation (+6 more)

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "MT5Gateway"
Cohesion: 0.07
Nodes (22): ExecutionTransport, Submit an already approved intent to the execution transport., BrokerExecutionReport, MT5Gateway, MT5SymbolMapping, BaseModel, Protocol, _float_value() (+14 more)

### Community 104 - "PositionGateway"
Cohesion: 0.15
Nodes (14): _adapter(), _constants(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send() (+6 more)

### Community 105 - "runtime/journal.py"
Cohesion: 0.07
Nodes (49): Collection, ScenarioTransition, Explicitly advanced deterministic replay clock., ReplayClock, JournalEntry, JournalOutcome, JournalOutcomeStatus, JournalRecord (+41 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "position.py"
Cohesion: 0.33
Nodes (9): _float_value(), _int_value(), _optional_close(), _optional_price(), _positive_int(), Demo-only MetaTrader 5 transport for Task 7 position-action intents., _required_positive(), _truthy() (+1 more)

### Community 109 - "Signal"
Cohesion: 0.35
Nodes (16): Signal, _contribution(), _discipline(), _evidence(), _intent(), _master(), _of_type(), _result() (+8 more)

### Community 110 - "QuantAgent"
Cohesion: 0.40
Nodes (6): Any, datetime, ndarray, Series, QuantAgent, AgentPrediction

### Community 111 - "datasets/__init__.py"
Cohesion: 0.15
Nodes (21): DatasetBuildResult, Path, write_dataset(), DatasetBuildConfig, BaseModel, RowPolicy, SplitPolicy, build() (+13 more)

### Community 112 - "LabelDefinition"
Cohesion: 0.16
Nodes (23): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., LabelDefinition, BaseModel (+15 more)

### Community 113 - "build_mt5_dataset.py"
Cohesion: 0.31
Nodes (8): HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel, Path, Explicit user-run MT5 multi-timeframe download and immutable dataset build.

### Community 114 - "ExperienceProvenance"
Cohesion: 0.16
Nodes (14): ExperienceProvenance, model_validator, _rejection(), test_show_and_summary_cli_emit_json(), test_summary_is_descriptive_and_preserves_unknowns(), _trade(), _decision(), _provenance() (+6 more)

### Community 115 - "SQLiteProposalEvaluationStore"
Cohesion: 0.15
Nodes (19): _build_plan(), _emit(), handle_evaluation_command(), _input(), Namespace, Path, CLI handlers for preregistered proposal evaluation evidence., _record_decision() (+11 more)

### Community 116 - "Global Constraints"
Cohesion: 0.22
Nodes (8): Global Constraints, Phase 8 Task 1 Experience Store Implementation Plan, Task 1: Experience contracts, Task 2: Append-only SQLite store, Task 3: Durable replay outcome artifact, Task 4: Exact-link outcome attribution, Task 5: Descriptive analytics and CLI, Task 6: Baseline ingestion and final verification

### Community 117 - "Phase 8 Task 6 Deterministic Evaluation Execution Adapter Design"
Cohesion: 0.22
Nodes (8): Append-only persistence, CLI, Contracts, Exact linkage and execution, Phase 8 Task 6 Deterministic Evaluation Execution Adapter Design, Result artifact and determinism, Scope, Validation

### Community 118 - "Phase 8 Task 1 Experience Store Design"
Cohesion: 0.22
Nodes (8): Attribution, CLI and analytics, Contracts, Persistence, Phase 8 Task 1 Experience Store Design, Scope, Source authority, Validation

### Community 119 - "Phase 7 Task 8 Direct MT5 Transport Design"
Cohesion: 0.22
Nodes (8): Boundaries, Deferred work, Idempotency and persistence, Phase 7 Task 8 Direct MT5 Transport Design, Requests and response mapping, Safety and modes, Scope, Snapshots and causality

### Community 120 - "EntryGateway"
Cohesion: 0.14
Nodes (18): _adapter(), _constants(), EntryGateway, _intent(), _policy(), datetime, Exception, parametrize (+10 more)

### Community 121 - "Global constraints"
Cohesion: 0.25
Nodes (7): Global constraints, Phase 7 Task 8 Direct MT5 Transport Implementation Plan, Task 1: Gateway and normalized MT5 contracts, Task 2: Canonical broker snapshots, Task 3: Entry transport and complete dry-run preflight, Task 4: Durable position-action transport, Task 5: Documentation, optional read-only smoke, and final verification

### Community 122 - "LocalModelRegistry"
Cohesion: 0.38
Nodes (5): LocalModelRegistry, Any, BaseModel, Path, RegistryEntry

### Community 123 - "processor.py"
Cohesion: 0.18
Nodes (19): Concrete composition of existing deterministic Phase 7 decision boundaries., MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy, PositionManagementReason, PositionManagementResult (+11 more)

### Community 124 - "Phase 8 Task 4 Advisory Improvement Proposal Design"
Cohesion: 0.20
Nodes (9): Append-only persistence and supersession, CLI, Contracts and identity, Deterministic advisory content, Eligibility, Phase 8 Task 4 Advisory Improvement Proposal Design, Proposal lifecycle, Scope (+1 more)

### Community 125 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 6 Deterministic Evaluation Execution Adapter Implementation Plan, Task 1: Execution and unavailable-observation contracts, Task 2: Closed deterministic metric-sample adapter, Task 3: Append-only request and audit persistence, Task 4: Execution service and idempotent recovery, Task 5: CLI, documentation, and final verification

### Community 126 - "test_daily_reflection.py"
Cohesion: 0.39
Nodes (11): _agent(), _findings(), _management(), _provenance(), datetime, _rejection(), test_agent_position_and_runtime_anomaly_findings_use_exact_daily_sources(), test_daily_aggregation_detects_confidence_excursion_and_rejection_patterns() (+3 more)

### Community 127 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 3 Weekly Reflection and Pattern Lifecycle Implementation Plan, Task 1: Weekly contracts and semantic identities, Task 2: Pure weekly aggregation and exact provenance, Task 3: Append-only weekly and lifecycle persistence, Task 4: Weekly CLI integration, Task 5: Corrected one-month baseline and durable context

### Community 128 - "DatasetManifest"
Cohesion: 0.25
Nodes (4): DatasetManifest, BaseModel, Path, PersistenceAndConfigTests

### Community 129 - "Deterministic Evaluation Execution"
Cohesion: 0.33
Nodes (5): Controlled CLI workflow, Deterministic Evaluation Execution, Identity and inputs, Persistence and retry, Protected Final OOS

### Community 130 - "test_runtime_state.py"
Cohesion: 0.20
Nodes (20): account(), feedback(), freshness(), market(), order(), position(), datetime, parametrize (+12 more)

### Community 131 - "Phase 8 Task 2 Deterministic Daily Reflection Design"
Cohesion: 0.22
Nodes (8): Causal period rule, CLI, Contracts, Deterministic diagnostics, Persistence and supersession, Phase 8 Task 2 Deterministic Daily Reflection Design, Scope, Validation

### Community 132 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 2 Deterministic Daily Reflection Implementation Plan, Task 1: Reflection contracts and policy, Task 2: Pure daily aggregation, Task 3: Append-only reflection persistence, Task 4: Build orchestration and CLI, Task 5: Baseline validation and durable context

### Community 133 - "AttributionSources"
Cohesion: 0.20
Nodes (12): AttributionSources, _deduplicate(), _index(), Connection, Path, T, _read_only(), _emit() (+4 more)

### Community 135 - "Deterministic Daily Reflection"
Cohesion: 0.33
Nodes (5): Causal contract, Deterministic Daily Reflection, Diagnostic families, Persistence, Verified baseline

### Community 136 - "Phase 3 dataset contract"
Cohesion: 0.29
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 137 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 4 Advisory Improvement Proposal Implementation Plan, Task 1: Proposal contracts and identities, Task 2: Pure eligibility, provenance, and proposal construction, Task 3: Append-only proposal and lifecycle persistence, Task 4: CLI integration, Task 5: Unchanged baseline and durable context

### Community 138 - "datasets/preprocessing.py"
Cohesion: 0.36
Nodes (6): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only.

### Community 141 - "risk_boundary/evaluator.py"
Cohesion: 0.16
Nodes (22): BaseModel, StrEnum, RiskBoundaryModel, RiskContext, RiskPolicy, RiskReason, RiskResult, _deduplicate() (+14 more)

### Community 142 - "Deterministic Weekly Reflection and Pattern Lifecycle"
Cohesion: 0.33
Nodes (5): Deterministic Weekly Reflection and Pattern Lifecycle, Identity, Knowledge lifecycle, Verified baseline, Weekly contract

### Community 143 - "Advisory Improvement Proposals"
Cohesion: 0.33
Nodes (5): Advisory Improvement Proposals, Eligibility and provenance, Identity and supersession, Lifecycle, Verified baseline

### Community 146 - ".__init__"
Cohesion: 0.50
Nodes (3): EntryContextProvider, PositionActionContextProvider, PositionContextProvider

### Community 148 - "MetaTrader5Gateway"
Cohesion: 0.18
Nodes (9): MT5ConnectionError, RuntimeError, The terminal package or connected terminal is unavailable., _load_mt5(), _mapping(), _mappings(), MetaTrader5Gateway, Lazy concrete wrapper around the Windows-only MetaTrader5 package. (+1 more)

### Community 149 - "canonical_hash"
Cohesion: 0.18
Nodes (4): model_validator, model_validator, canonical_hash(), Any

### Community 150 - "test_quant_development_runner.py"
Cohesion: 0.23
Nodes (13): compare_runs(), Any, Path, Compare completed development runs without retraining or scalar ranking., _read(), experiment(), Path, test_compare_runs_uses_multiple_evidence_dimensions() (+5 more)

### Community 153 - "Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design"
Cohesion: 0.17
Nodes (11): Append-only persistence, Candidate contract, CLI, Evaluation result, Identity and serialization, Operator decision boundary, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design, Preregistered plan (+3 more)

### Community 157 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Implementation Plan, Task 1: Evaluation contracts and protected-OOS invariants, Task 2: Pure preregistration and result evaluation, Task 3: Append-only evaluation persistence, Task 4: Evaluation CLI without execution, Task 5: Documentation and final verification

### Community 163 - "Proposal Evaluation"
Cohesion: 0.40
Nodes (4): CLI workflow, Governance boundary, Persistence and corrections, Proposal Evaluation

### Community 167 - "RuntimeEvent"
Cohesion: 0.08
Nodes (25): execution_result_to_runtime_event(), Bridge typed execution results into the shared Phase 6 runtime path., Convert actionable execution feedback; local NO_ACTION stays local., Deterministic composition service for the completed Phase 6/7 boundaries., position_action_result_to_runtime_event(), Dedicated append-only transport contracts for safe position actions., BaseModel, datetime (+17 more)

## Knowledge Gaps
- **312 isolated node(s):** `adaptive-xauusd-trader`, `Repository-start workflow`, `Graphify`, `Current capabilities`, `Setup (Windows PowerShell)` (+307 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 952 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `weekly_contracts.py`, `labels/__init__.py`, `reflection/__main__.py`, `DatasetManifest`, `trainer.py`, `agents/__init__.py`, `development/config.py`, `datasets/builder.py`, `.bind_identity`, `.validate_and_bind_identity`, `SQLiteWeeklyReflectionStore`, `dataset.py`, `runtime/__init__.py`, `ToolResult`, `model_validator`, `model_validator`, `SQLiteExecutionLedger`, `model_validator`, `experience/__init__.py`, `.normalize_validate_and_bind_identity`, `RuntimeEvent`, `MetricScope`, `.normalize_validate_and_bind_identity`, `.bind_identity`, `SQLiteExperienceStore`, `attribution.py`, `.bind_identity`, `quant/config.py`, `model_validator`, `.validate_and_bind_identity`, `PositionActionIntent`, `system.py`, `.validate_event`, `.validate_and_bind_identity`, `.validate_and_bind_identity`, `orchestration/contracts.py`, `ComponentFreshness`, `runner.py`, `MasterProposal`, `discipline/__init__.py`, `reflection/__init__.py`, `folds.py`, `execution_boundary/__init__.py`, `SQLiteImprovementProposalStore`, `mt5/__init__.py`, `model_validator`, `runtime/journal.py`, `ExperienceProvenance`, `SQLiteProposalEvaluationStore`, `processor.py`?**
  _High betweenness centrality (0.169) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `weekly_contracts.py`, `reflection/__main__.py`, `trainer.py`, `test_runtime_orchestration.py`, `risk_boundary/evaluator.py`, `runtime/__init__.py`, `test_risk_boundary.py`, `SQLiteExecutionLedger`, `experience/__init__.py`, `SQLiteExperienceStore`, `attribution.py`, `system.py`, `_context`, `evaluate_discipline`, `schemas.py`, `test_execution_boundary.py`, `MasterProposal`, `preflight.py`, `discipline/__init__.py`, `position_actions/evaluator.py`, `ExecutionIntent`, `_context`, `execution_boundary/__init__.py`, `QuantAgent`, `ExperienceProvenance`, `EntryGateway`, `test_daily_reflection.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `features/analysis.py`, `axq/features/registry.py`, `axq/config.py`, `system.py`, `datasets/builder.py`, `test_agent_tools.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 177 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 177 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 70 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ExecutionIntent` (e.g. with `DemoExecutionAdapter` and `ExecutionAdapter`) actually correct?**
  _`ExecutionIntent` has 9 INFERRED edges - model-reasoned connections that need verification._