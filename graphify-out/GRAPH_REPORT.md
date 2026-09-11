# Graph Report - phase-8-reflection-experience  (2026-09-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3896 nodes · 12916 edges · 189 communities (148 shown, 39 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 2223 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bf4db277`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- reflection/contracts.py
- labels/__init__.py
- test_reflection_cli.py
- axq/features/registry.py
- QuantAgent
- indicators.py
- agents/__init__.py
- update_scenario
- development/config.py
- axq/config.py
- test_runtime_orchestration.py
- ProposalEvaluationPlan
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
- SQLiteExecutionLedger
- System architecture (Phase 0-7 baseline)
- weekly_contracts.py
- dataset.py
- RuntimeEvent
- Architecture decision log
- _deterministic.py
- README.md
- test_risk_boundary.py
- ToolResult
- service.py
- recovery_contracts.py
- timedelta
- Global Constraints
- attribution.py
- Phase 0-6 runbook
- persist_controlled_plan
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- MetricScope
- DailyReflection
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- PositionActionTransportResult
- replay_validation/__init__.py
- CanonicalMetricSampleArtifact
- reflection/__init__.py
- Repository instructions
- _context
- quant/config.py
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
- Signal
- snapshot.py
- JournalRecord
- default_registry
- preflight.py
- discipline/__init__.py
- evaluation_contracts.py
- Global Constraints
- assemble_dataset
- runtime/journal.py
- Global Constraints
- execution_boundary/__init__.py
- trainer.py
- test_agent_tools.py
- Phase 7 deterministic runtime orchestration
- experience/__init__.py
- reflection/__main__.py
- Global Constraints
- FakeMT5Module
- evidence
- features/analysis.py
- FakeRunner
- SQLiteImprovementProposalStore
- SnapshotGateway
- canonical_hash
- Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design
- Phase 7 Task 7: Position Action Safety and Journal Plan
- MT5Gateway
- PositionGateway
- position.py
- Position action safety
- AttributionSources
- session_features
- test_daily_reflection.py
- evaluate_predictions
- test_datasets_phase3.py
- ComponentFreshness
- Phase 8 Task 7 Governed Candidate Replay Evaluator Design
- LabelDefinition
- SQLiteProposalEvaluationStore
- Global Constraints
- Phase 8 Task 6 Deterministic Evaluation Execution Adapter Design
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- EntryGateway
- Global constraints
- LocalModelRegistry
- CanonicalMetricSamplesAdapter
- Phase 8 Task 4 Advisory Improvement Proposal Design
- Global Constraints
- ExperienceProvenance
- Global Constraints
- DatasetManifest
- Deterministic Evaluation Execution
- test_runtime_state.py
- Phase 8 Task 2 Deterministic Daily Reflection Design
- Global Constraints
- Global Constraints
- Governed Candidate Replay Evaluation
- Deterministic Daily Reflection
- Phase 3 dataset contract
- Global Constraints
- folds.py
- MT5Constants
- model_validator
- MasterProposal
- Deterministic Weekly Reflection and Pattern Lifecycle
- Advisory Improvement Proposals
- Global Constraints
- breakout_features
- system.py
- model_validator
- MetaTrader5Gateway
- model_validator
- comparison.py
- Phase 8 Task 9 Deterministic Paired Evaluation Design
- _MT5Module
- Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design
- .validate_and_bind_identity
- model_validator
- model_validator
- Global Constraints
- .normalize_and_bind_identity
- replay.py
- test_improvement_proposals.py
- test_runtime_journal.py
- model_validator
- Proposal Evaluation
- model_validator
- .normalize_validate_and_bind_identity
- .normalize_validate_and_bind_identity
- test_feature_formulas.py
- model_validator
- .__init__
- .bind_identity
- model_validator
- ReconciliationLedger
- .bind_identity
- .terminal_path
- .validate_and_bind_identity
- default_shared_kernel_policy_set
- ContractAndRiskTests
- .validate_event
- .validate_and_bind_identity
- build_mt5_dataset.py
- Global Constraints
- Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design
- model_validator
- Shared-Kernel Candidate Driver V1
- EventSource
- price_action_features
- .bind_identity

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 198 edges
2. `MetricScope` - 107 edges
3. `RuntimeEvent` - 92 edges
4. `Signal` - 92 edges
5. `ReflectionModel` - 70 edges
6. `SQLiteProposalEvaluationStore` - 69 edges
7. `ExecutionIntent` - 64 edges
8. `CanonicalMetricSampleArtifact` - 60 edges
9. `SQLiteImprovementProposalStore` - 60 edges
10. `ExecutionResult` - 55 edges

## Surprising Connections (you probably didn't know these)
- `test_symbol_mapping_is_explicit_auditable_and_deterministic()` --calls--> `MT5SymbolMapping`  [INFERRED]
  tests/test_mt5_gateway.py → src/axq/mt5/contracts.py
- `test_system_replay_retains_exact_attribution_journal_semantics()` --uses--> `JournalRecordType`  [INFERRED]
  tests/test_system_replay.py → src/axq/runtime/journal.py
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py

## Import Cycles
- None detected.

## Communities (189 total, 39 thin omitted)

### Community 0 - "reflection/contracts.py"
Cohesion: 0.20
Nodes (27): FindingCategory, FindingSignal, MetricFact, StrEnum, Immutable content-addressed contracts for deterministic daily reflection., ReflectionFinding, SampleGuardRecord, _agent_findings() (+19 more)

### Community 1 - "labels/__init__.py"
Cohesion: 0.15
Nodes (28): BarrierMode, CollisionPolicy, EntryReference, LabelKind, StrEnum, Versioned label contracts. Labels may look forward; features never may., ReturnMode, ThresholdMode (+20 more)

### Community 2 - "test_reflection_cli.py"
Cohesion: 0.46
Nodes (7): _decision(), _experience_store(), Path, test_build_range_is_deterministic_and_idempotent(), test_build_rejects_reversed_date_range(), test_changed_input_creates_explicit_cli_supersession(), test_show_and_report_emit_machine_readable_json()

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "QuantAgent"
Cohesion: 0.18
Nodes (11): Any, datetime, ndarray, Series, QuantAgent, AgentPrediction, Any, QuantAgentEvidenceProvider (+3 more)

### Community 5 - "indicators.py"
Cohesion: 0.15
Nodes (32): aroon(), atr(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+24 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.08
Nodes (48): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+40 more)

### Community 7 - "update_scenario"
Cohesion: 0.15
Nodes (35): HypothesisRelationship, HypothesisStatus, model_validator, Apply one M5 or intrabar evidence event without consulting a clock., _terminal_state(), ThesisState, update_scenario(), _updated_scenarios() (+27 more)

### Community 8 - "development/config.py"
Cohesion: 0.08
Nodes (41): AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+33 more)

### Community 9 - "axq/config.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.09
Nodes (36): load_runtime_config(), BaseModel, Path, RuntimeConfig, DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., build_mt5_gateway(), Build the lazy gateway; operational paths are not semantic identity. (+28 more)

### Community 11 - "ProposalEvaluationPlan"
Cohesion: 0.06
Nodes (70): _emit(), _fixture(), handle_candidate_replay_command(), Namespace, Path, CLI handlers for governed deterministic candidate replay evaluation., _run(), _show() (+62 more)

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
Cohesion: 0.10
Nodes (20): main(), main(), main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., DataFrame, Leakage-safe multi-timeframe alignment. (+12 more)

### Community 23 - "SQLiteExecutionLedger"
Cohesion: 0.12
Nodes (13): Connection, Path, Append-only SQLite execution ledger and recovery anchors., Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, CheckpointLedger, ExecutionTransition, ExecutionTransitionType (+5 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.10
Nodes (20): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Phase 8 governed comparison boundary (+12 more)

### Community 25 - "weekly_contracts.py"
Cohesion: 0.09
Nodes (51): _build(), _emit(), handle_weekly_command(), _history(), _latest(), _policy(), date, Namespace (+43 more)

### Community 26 - "dataset.py"
Cohesion: 0.18
Nodes (13): load_training_dataset(), _parse_manifest(), Any, DataFrame, Path, Strict loading and identity verification for immutable Phase 3 datasets., _read_json(), TrainingDataset (+5 more)

### Community 27 - "RuntimeEvent"
Cohesion: 0.08
Nodes (60): execution_result_to_runtime_event(), Bridge typed execution results into the shared Phase 6 runtime path., Convert actionable execution feedback; local NO_ACTION stays local., Deterministic runtime refresh and checkpoint builders for restart recovery., position_action_result_to_runtime_event(), Dedicated append-only transport contracts for safe position actions., Strict contracts for the deterministic financial Risk boundary., BaseModel (+52 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.05
Nodes (38): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+30 more)

### Community 29 - "_deterministic.py"
Cohesion: 0.19
Nodes (20): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, StrEnum, fact_map(), Interpretation, numeric() (+12 more)

### Community 30 - "README.md"
Cohesion: 0.10
Nodes (16): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance, Model registry and promotion contract, Phase 5 development layer, Quant model training (+8 more)

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.11
Nodes (35): _catalog(), FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool (+27 more)

### Community 33 - "service.py"
Cohesion: 0.11
Nodes (19): Strict operational configuration for the Phase 7 runtime service., DecisionCycle, OutcomeCount, BaseModel, StrEnum, Strict orchestration-only contracts for the shared Phase 7 runtime., Auditable classifications emitted by the existing decision boundaries., RuntimeMode (+11 more)

### Community 34 - "recovery_contracts.py"
Cohesion: 0.13
Nodes (39): _conflict_reason(), _finding(), _object_id(), datetime, Deterministic exact-linkage comparison of local and broker execution state., reconcile_execution_state(), broker_snapshot_runtime_events(), BrokerIntentLink (+31 more)

### Community 35 - "timedelta"
Cohesion: 0.22
Nodes (29): initial_runtime_state(), Construct a canonical state with explicit unknown component values., account(), apply(), event(), feedback(), fresh(), market() (+21 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "attribution.py"
Cohesion: 0.24
Nodes (16): _anomaly(), _enum_value(), _identity_context(), OutcomeAttributionBuilder, _provenance(), Any, Exact-link deterministic reconstruction of normalized Phase 8 experiences., Build experiences with exact semantic joins and explicit missing-link markers. (+8 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.08
Nodes (25): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+17 more)

### Community 39 - "persist_controlled_plan"
Cohesion: 0.07
Nodes (52): ProposalEvaluationResult, EvaluationAdapterOutput, _artifact(), _emit(), handle_execution_command(), Namespace, Path, CLI handlers for deterministic preregistered evaluation execution. (+44 more)

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

### Community 44 - "MetricScope"
Cohesion: 0.08
Nodes (51): MetricScope, _emit(), handle_shared_kernel_candidate_command(), _optional_scope(), Namespace, Path, CLI handlers for governed shared-kernel candidate evaluation., _run() (+43 more)

### Community 45 - "DailyReflection"
Cohesion: 0.18
Nodes (28): DailyReflection, build_weekly_reflection(), PatternMetricSummary, WeeklyGuardKind, _expected_dates(), _experience_index(), _guard(), _metric_summaries() (+20 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.28
Nodes (21): ChartAgent, _input(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure(), test_chart_agent_represents_hierarchical_mtf_conflict_as_uncertainty() (+13 more)

### Community 49 - "PositionActionTransportResult"
Cohesion: 0.12
Nodes (11): Path, Append-only SQLite ledger for position-action transport outcomes., SQLitePositionActionTransportLedger, InMemoryPositionActionTransportLedger, PositionActionTransportLedger, PositionActionTransportResult, PositionActionTransportTransition, PositionActionTransportTransitionType (+3 more)

### Community 50 - "replay_validation/__init__.py"
Cohesion: 0.07
Nodes (50): _identity(), _PendingClose, PendingReplayEntry, _PendingStop, datetime, StrEnum, Deterministic, transport-only fill mechanics for system replay., A causal fill book; it contains no signal or policy decisions. (+42 more)

### Community 51 - "CanonicalMetricSampleArtifact"
Cohesion: 0.06
Nodes (80): canonical_record_bytes(), input_artifact_ref(), BaseModel, CanonicalMetricSampleArtifact, _artifact_matches(), _artifacts(), _emit(), handle_paired_evaluation_command() (+72 more)

### Community 52 - "reflection/__init__.py"
Cohesion: 0.12
Nodes (34): ControlledReplayObservation, BaseModel, ReflectionModel, SampleGuardStatus, Deterministic Phase 8 reflection contracts and services., ProposalEvidenceGuard, ProposalGuardKind, ProposalTargetComponent (+26 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.06
Nodes (88): ResumeStatus, default_position_action_policy(), Return conservative deterministic V1 safety defaults., MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy (+80 more)

### Community 55 - "quant/config.py"
Cohesion: 0.10
Nodes (31): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+23 more)

### Community 68 - "evaluate_discipline"
Cohesion: 0.26
Nodes (34): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., _context(), _policy(), _proposal(), parametrize (+26 more)

### Community 69 - "runner.py"
Cohesion: 0.11
Nodes (29): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+21 more)

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
Cohesion: 0.16
Nodes (33): RuntimeError, Submission may have reached the broker and requires reconciliation., UnknownSubmissionState, _adapter(), _discipline(), _intent(), _observation(), _policy() (+25 more)

### Community 75 - "OperatorControls"
Cohesion: 0.16
Nodes (8): OperatorControls, Monotonic operator gates: callers cannot use this contract to bypass safety., BrokerSnapshotProvider, DecisionCycleProcessor, PositionActionAdapter, datetime, Protocol, test_operator_controls_only_become_more_conservative()

### Community 76 - "Signal"
Cohesion: 0.15
Nodes (32): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion., SpecialistContribution (+24 more)

### Community 77 - "snapshot.py"
Cohesion: 0.20
Nodes (21): BrokerObjectKind, MT5PersistedIntentLink, MT5SnapshotError, RuntimeError, A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider (+13 more)

### Community 78 - "JournalRecord"
Cohesion: 0.12
Nodes (10): JournalEntry, JournalRecord, BaseModel, Connection, JournalSemantic, model_validator, Path, UTCDateTime (+2 more)

### Community 79 - "default_registry"
Cohesion: 0.12
Nodes (19): multi_timeframe_features(), Any, DataFrame, fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., default_registry() (+11 more)

### Community 80 - "preflight.py"
Cohesion: 0.13
Nodes (22): The transport failed before submission could be accepted., TransportFailure, _account_mode(), _float_value(), _int_value(), _positive_float(), datetime, Fail-closed MetaTrader 5 entry preflight and request construction. (+14 more)

### Community 81 - "discipline/__init__.py"
Cohesion: 0.25
Nodes (21): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult, DisciplineState (+13 more)

### Community 82 - "evaluation_contracts.py"
Cohesion: 0.13
Nodes (52): AcceptanceCriterion, CandidateKind, CriterionComparator, CriterionOutcome, CriterionOutcomeStatus, CriterionRole, EvaluationAggregateOutcome, FinalOOSPolicy (+44 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "assemble_dataset"
Cohesion: 0.13
Nodes (25): assemble_dataset(), dataframe_hash(), DatasetBuildResult, Any, DataFrame, Path, _validate_source_frames(), write_dataset() (+17 more)

### Community 85 - "runtime/journal.py"
Cohesion: 0.12
Nodes (39): ReconciliationReport, ResumeReadiness, create_recovery_checkpoint(), Concrete composition of existing deterministic Phase 7 decision boundaries., Compose existing pure functions; adapters provide causal context only., PositionActionContext, PositionActionIntent, PositionActionModel (+31 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "execution_boundary/__init__.py"
Cohesion: 0.11
Nodes (28): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, ExecutionTransport, InMemoryExecutionLedger, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics. (+20 more)

### Community 88 - "trainer.py"
Cohesion: 0.08
Nodes (39): dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run(), write_json() (+31 more)

### Community 89 - "test_agent_tools.py"
Cohesion: 0.16
Nodes (21): PredictiveModelEvidenceProvider, Protocol, _ExplodingTool, _FailingProvider, _freshness(), _input(), Any, datetime (+13 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "experience/__init__.py"
Cohesion: 0.18
Nodes (22): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+14 more)

### Community 92 - "reflection/__main__.py"
Cohesion: 0.06
Nodes (52): Any, register_candidate_replay_commands(), ReflectionPolicy, Any, register_execution_commands(), _build(), _days(), _emit() (+44 more)

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
Cohesion: 0.25
Nodes (17): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+9 more)

### Community 98 - "SQLiteImprovementProposalStore"
Cohesion: 0.12
Nodes (29): _build(), _emit(), handle_proposal_command(), _history(), _latest(), _policy(), Namespace, Path (+21 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.15
Nodes (8): _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_creates_canonical_events_and_reduces_through_shared_path(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket(), test_snapshot_maps_account_market_books_exposure_and_constraints()

### Community 100 - "canonical_hash"
Cohesion: 0.12
Nodes (6): model_validator, model_validator, model_validator, model_validator, canonical_hash(), Any

### Community 101 - "Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design"
Cohesion: 0.13
Nodes (14): Append-only persistence and supersession, Architecture, Baseline validation, CLI, Exact provenance validation, ISO-week boundary and availability, Knowledge-status lifecycle, Pattern generation (+6 more)

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "MT5Gateway"
Cohesion: 0.09
Nodes (20): MT5Gateway, MT5SymbolMapping, Protocol, Narrow contracts isolating the optional MetaTrader5 package., _float_value(), _int_value(), MT5ExecutionAdapter, MT5ExecutionTransport (+12 more)

### Community 104 - "PositionGateway"
Cohesion: 0.16
Nodes (13): _adapter(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send(), test_modify_stop_preserves_ticket_tp_and_cannot_increase_exposure() (+5 more)

### Community 105 - "position.py"
Cohesion: 0.24
Nodes (12): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), datetime, Demo-only MetaTrader 5 transport for Task 7 position-action intents. (+4 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "AttributionSources"
Cohesion: 0.20
Nodes (12): AttributionSources, _deduplicate(), _index(), Connection, Path, T, _read_only(), _emit() (+4 more)

### Community 108 - "session_features"
Cohesion: 0.23
Nodes (10): _local_window(), Any, DataFrame, Series, DST-aware session features. Source timestamps are interpreted as UTC., session_features(), test_london_and_new_york_dst_transitions(), test_manifest_is_reproducible_and_complete() (+2 more)

### Community 109 - "test_daily_reflection.py"
Cohesion: 0.39
Nodes (11): _agent(), _findings(), _management(), _provenance(), datetime, _rejection(), test_agent_position_and_runtime_anomaly_findings_use_exact_daily_sources(), test_daily_aggregation_detects_confidence_excursion_and_rejection_patterns() (+3 more)

### Community 110 - "evaluate_predictions"
Cohesion: 0.08
Nodes (34): ProbabilityCalibrator, ndarray, Validation-only probability calibration without OOS access., evaluate_challenger_evidence(), Any, Advisory Champion/Challenger evidence contract., calibration_diagnostics(), compare_calibration_methods() (+26 more)

### Community 111 - "test_datasets_phase3.py"
Cohesion: 0.14
Nodes (20): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., build(), candles() (+12 more)

### Community 112 - "ComponentFreshness"
Cohesion: 0.12
Nodes (12): evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis, _unknown_freshness(), ComponentFreshness (+4 more)

### Community 113 - "Phase 8 Task 7 Governed Candidate Replay Evaluator Design"
Cohesion: 0.22
Nodes (8): CLI, Contracts and identity, Controlled replay engine, Exact linkage and Final OOS boundary, Persistence, service, and reuse, Phase 8 Task 7 Governed Candidate Replay Evaluator Design, Scope, Validation

### Community 114 - "LabelDefinition"
Cohesion: 0.14
Nodes (26): dataset_quality_report(), Any, DataFrame, compare_label_definitions(), label_balance(), Any, DataFrame, Series (+18 more)

### Community 115 - "SQLiteProposalEvaluationStore"
Cohesion: 0.08
Nodes (32): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Path, _build_plan(), _emit() (+24 more)

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
Cohesion: 0.13
Nodes (20): default_execution_policy(), Return the conservative, execution-disabled baseline policy., ExecutionMode, _adapter(), EntryGateway, _intent(), _policy(), datetime (+12 more)

### Community 121 - "Global constraints"
Cohesion: 0.25
Nodes (7): Global constraints, Phase 7 Task 8 Direct MT5 Transport Implementation Plan, Task 1: Gateway and normalized MT5 contracts, Task 2: Canonical broker snapshots, Task 3: Entry transport and complete dry-run preflight, Task 4: Durable position-action transport, Task 5: Documentation, optional read-only smoke, and final verification

### Community 122 - "LocalModelRegistry"
Cohesion: 0.17
Nodes (12): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., LocalModelRegistry, ModelState, Any, BaseModel (+4 more)

### Community 123 - "CanonicalMetricSamplesAdapter"
Cohesion: 0.49
Nodes (10): CanonicalMetricSamplesAdapter, Aggregate exact preregistered metric series without executing candidate code., _artifacts(), _metric(), _plan(), _request(), test_adapter_computes_only_closed_preregistered_aggregations(), test_adapter_fails_closed_for_linkage_scope_series_and_aggregation_mismatch() (+2 more)

### Community 124 - "Phase 8 Task 4 Advisory Improvement Proposal Design"
Cohesion: 0.20
Nodes (9): Append-only persistence and supersession, CLI, Contracts and identity, Deterministic advisory content, Eligibility, Phase 8 Task 4 Advisory Improvement Proposal Design, Proposal lifecycle, Scope (+1 more)

### Community 125 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 6 Deterministic Evaluation Execution Adapter Implementation Plan, Task 1: Execution and unavailable-observation contracts, Task 2: Closed deterministic metric-sample adapter, Task 3: Append-only request and audit persistence, Task 4: Execution service and idempotent recovery, Task 5: CLI, documentation, and final verification

### Community 126 - "ExperienceProvenance"
Cohesion: 0.16
Nodes (14): ExperienceProvenance, model_validator, _rejection(), test_show_and_summary_cli_emit_json(), test_summary_is_descriptive_and_preserves_unknowns(), _trade(), _decision(), _provenance() (+6 more)

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

### Community 133 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 7 Governed Candidate Replay Evaluator Implementation Plan, Task 1: Immutable replay contracts, Task 2: Allowlisted controlled replay engine, Task 3: Append-only migration and replay store, Task 4: Idempotent service and Task 6 compatibility, Task 5: CLI, documentation, and final gate

### Community 134 - "Governed Candidate Replay Evaluation"
Cohesion: 0.33
Nodes (5): Controlled CLI, Controlled input and engine, Determinism and persistence, Governed Candidate Replay Evaluation, Task 6 handoff

### Community 135 - "Deterministic Daily Reflection"
Cohesion: 0.33
Nodes (5): Causal contract, Deterministic Daily Reflection, Diagnostic families, Persistence, Verified baseline

### Community 136 - "Phase 3 dataset contract"
Cohesion: 0.29
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 137 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 4 Advisory Improvement Proposal Implementation Plan, Task 1: Proposal contracts and identities, Task 2: Pure eligibility, provenance, and proposal construction, Task 3: Append-only proposal and lifecycle persistence, Task 4: CLI integration, Task 5: Unchanged baseline and durable context

### Community 138 - "folds.py"
Cohesion: 0.14
Nodes (25): chronological_split(), IndexRange, BaseModel, Path, Deterministic chronological, purged, embargoed split definitions., SplitFold, SplitManifest, walk_forward_splits() (+17 more)

### Community 139 - "MT5Constants"
Cohesion: 0.33
Nodes (5): MT5Constants, BaseModel, _constants(), _constants(), _constants()

### Community 141 - "MasterProposal"
Cohesion: 0.20
Nodes (24): DisciplineOutcome, build_execution_intent(), RiskContext, Pure construction of provenance-bound execution intents., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links(), _progressed_to(), MasterProposal (+16 more)

### Community 142 - "Deterministic Weekly Reflection and Pattern Lifecycle"
Cohesion: 0.33
Nodes (5): Deterministic Weekly Reflection and Pattern Lifecycle, Identity, Knowledge lifecycle, Verified baseline, Weekly contract

### Community 143 - "Advisory Improvement Proposals"
Cohesion: 0.33
Nodes (5): Advisory Improvement Proposals, Eligibility and provenance, Identity and supersession, Lifecycle, Verified baseline

### Community 144 - "Global Constraints"
Cohesion: 0.22
Nodes (8): Deterministic Paired Baseline-vs-Candidate Comparison Implementation Plan, Global Constraints, Task 1: Immutable paired comparison contracts, Task 2: Pure paired comparison adapter, Task 3: Append-only migration and store, Task 4: Idempotent comparison service, Task 5: CLI and package integration, Task 6: Documentation, audits, Graphify, and final gate

### Community 145 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 146 - "system.py"
Cohesion: 0.08
Nodes (37): DeterministicDecisionProcessor, EntryDecisionInputs, BaseModel, Causal contexts supplied by the runtime-specific context adapter., Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, RuntimeRunner, main(), Command-line entry point for Phase 7 system replay and result display. (+29 more)

### Community 148 - "MetaTrader5Gateway"
Cohesion: 0.19
Nodes (8): MT5ConnectionError, The terminal package or connected terminal is unavailable., _load_mt5(), _mapping(), _mappings(), MetaTrader5Gateway, Lazy concrete wrapper around the Windows-only MetaTrader5 package., Operational gateway; paths and process state are never semantic identity.

### Community 150 - "comparison.py"
Cohesion: 0.33
Nodes (7): compare_runs(), Any, Path, Compare completed development runs without retraining or scalar ranking., _read(), main(), Compare completed Phase 5 runs without retraining.

### Community 151 - "Phase 8 Task 9 Deterministic Paired Evaluation Design"
Cohesion: 0.25
Nodes (7): CLI and controlled validation, Contracts, Explicit exclusions, Persistence and idempotency, Phase 8 Task 9 Deterministic Paired Evaluation Design, Purpose and boundary, Validation and comparison flow

### Community 153 - "Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design"
Cohesion: 0.17
Nodes (11): Append-only persistence, Candidate contract, CLI, Evaluation result, Identity and serialization, Operator decision boundary, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design, Preregistered plan (+3 more)

### Community 157 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Implementation Plan, Task 1: Evaluation contracts and protected-OOS invariants, Task 2: Pure preregistration and result evaluation, Task 3: Append-only evaluation persistence, Task 4: Evaluation CLI without execution, Task 5: Documentation and final verification

### Community 159 - "replay.py"
Cohesion: 0.09
Nodes (45): Collection, ScenarioTransition, Protocol, Clock contract used outside the pure reducer., Explicitly advanced deterministic replay clock., ReplayClock, RuntimeClock, JournalOutcome (+37 more)

### Community 160 - "test_improvement_proposals.py"
Cohesion: 0.67
Nodes (6): _sources(), test_missing_exact_experience_fails_closed(), test_recurring_guarded_patterns_build_one_deterministic_proposal_per_key(), test_rejected_pattern_status_excludes_only_that_pattern_key(), test_single_week_pattern_is_reported_insufficient_without_proposal(), _weeks()

### Community 161 - "test_runtime_journal.py"
Cohesion: 0.50
Nodes (7): _event(), datetime, _snapshot(), test_feature_snapshots_can_be_recovered_by_event_without_mutation(), test_journal_is_append_only_and_keeps_deterministic_order(), test_journal_replay_orders_events_by_causal_availability(), test_journal_round_trip_preserves_typed_semantic_identity()

### Community 163 - "Proposal Evaluation"
Cohesion: 0.40
Nodes (4): CLI workflow, Governance boundary, Persistence and corrections, Proposal Evaluation

### Community 167 - "test_feature_formulas.py"
Cohesion: 0.23
Nodes (11): skipif, money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility() (+3 more)

### Community 169 - ".__init__"
Cohesion: 0.50
Nodes (3): EntryContextProvider, PositionActionContextProvider, PositionContextProvider

### Community 176 - "default_shared_kernel_policy_set"
Cohesion: 0.17
Nodes (21): default_shared_kernel_policy_set(), Reproduce the exact policy composition used by Phase 7 system replay., data_manifest(), _ohlc_rows(), persisted_shared_kernel_inputs(), persisted_shared_kernel_plan(), DataFrame, Path (+13 more)

### Community 177 - "ContractAndRiskTests"
Cohesion: 0.36
Nodes (7): calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext, RiskLimits, veto_reasons(), ContractAndRiskTests

### Community 182 - "build_mt5_dataset.py"
Cohesion: 0.31
Nodes (8): HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel, Path, Explicit user-run MT5 multi-timeframe download and immutable dataset build.

### Community 183 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Implementation Plan, Task 1: Shared replay policy composition boundary, Task 2: Frozen candidate and governed data contracts, Task 3: Closed shared-kernel engine and metric extraction, Task 4: Append-only store and idempotent service, Task 5: CLI, documentation, and final governance gate

### Community 184 - "Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design"
Cohesion: 0.25
Nodes (7): CLI and controlled validation, Execution and metric production, Governed inputs and identity, Persistence and recovery, Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design, Purpose, Shared-kernel injection boundary

### Community 187 - "Shared-Kernel Candidate Driver V1"
Cohesion: 0.29
Nodes (6): Candidate injection boundary, Commands, Controlled V1 validation, Governance and data, Persistence and retry, Shared-Kernel Candidate Driver V1

### Community 190 - "EventSource"
Cohesion: 0.40
Nodes (4): EventSource, Protocol, Source of events already ordered for causal reduction., Yield events in canonical availability order.

### Community 194 - "price_action_features"
Cohesion: 0.50
Nodes (3): price_action_features(), Any, DataFrame

## Knowledge Gaps
- **366 isolated node(s):** `Append-only persistence and supersession`, `Architecture`, `Baseline validation`, `CLI`, `Exact provenance validation` (+361 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1073 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `reflection/contracts.py`, `labels/__init__.py`, `DatasetManifest`, `agents/__init__.py`, `update_scenario`, `development/config.py`, `folds.py`, `ProposalEvaluationPlan`, `model_validator`, `system.py`, `model_validator`, `model_validator`, `datasets/builder.py`, `weekly_contracts.py`, `.validate_and_bind_identity`, `RuntimeEvent`, `model_validator`, `_deterministic.py`, `.normalize_and_bind_identity`, `model_validator`, `replay.py`, `service.py`, `model_validator`, `recovery_contracts.py`, `model_validator`, `attribution.py`, `.normalize_validate_and_bind_identity`, `persist_controlled_plan`, `model_validator`, `.normalize_validate_and_bind_identity`, `.bind_identity`, `SQLiteExperienceStore`, `MetricScope`, `.bind_identity`, `model_validator`, `.validate_and_bind_identity`, `ToolResult`, `replay_validation/__init__.py`, `CanonicalMetricSampleArtifact`, `reflection/__init__.py`, `.validate_event`, `_context`, `quant/config.py`, `.validate_and_bind_identity`, `model_validator`, `.bind_identity`, `runner.py`, `Signal`, `JournalRecord`, `discipline/__init__.py`, `evaluation_contracts.py`, `assemble_dataset`, `runtime/journal.py`, `execution_boundary/__init__.py`, `trainer.py`, `experience/__init__.py`, `reflection/__main__.py`, `SQLiteImprovementProposalStore`, `MT5Gateway`, `ComponentFreshness`, `SQLiteProposalEvaluationStore`, `ExperienceProvenance`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `reflection/contracts.py`, `test_reflection_cli.py`, `QuantAgent`, `test_runtime_orchestration.py`, `MasterProposal`, `system.py`, `RuntimeEvent`, `test_risk_boundary.py`, `test_improvement_proposals.py`, `recovery_contracts.py`, `attribution.py`, `SQLiteExperienceStore`, `DailyReflection`, `ContractAndRiskTests`, `replay_validation/__init__.py`, `_context`, `evaluate_discipline`, `schemas.py`, `test_execution_boundary.py`, `preflight.py`, `discipline/__init__.py`, `runtime/journal.py`, `execution_boundary/__init__.py`, `trainer.py`, `experience/__init__.py`, `reflection/__main__.py`, `MT5Gateway`, `test_daily_reflection.py`, `EntryGateway`, `ExperienceProvenance`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `price_action_features`, `axq/features/registry.py`, `indicators.py`, `test_feature_formulas.py`, `axq/config.py`, `session_features`, `breakout_features`, `system.py`, `assemble_dataset`, `datasets/builder.py`, `test_agent_tools.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 212 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 212 INFERRED edges - model-reasoned connections that need verification._
- **Are the 83 inferred relationships involving `MetricScope` (e.g. with `_fixture()` and `_run()`) actually correct?**
  _`MetricScope` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 70 INFERRED edges - model-reasoned connections that need verification._