# Graph Report - phase-8-reflection-experience  (2026-09-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3757 nodes · 12389 edges · 196 communities (154 shown, 41 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 2117 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a3271eb8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- daily.py
- LabelDefinition
- reflection/__main__.py
- axq/features/registry.py
- inference.py
- indicators.py
- agents/__init__.py
- update_scenario
- development/config.py
- axq/config.py
- test_runtime_orchestration.py
- reflection/__init__.py
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
- RuntimeOrchestrator
- recovery_contracts.py
- reduce_state
- Global Constraints
- attribution.py
- Phase 0-6 runbook
- timedelta
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- MetricScope
- DailyReflection
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- position.py
- replay_validation/__init__.py
- Phase 3 label contract
- service.py
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
- default_registry
- preflight.py
- discipline/__init__.py
- ReflectionModel
- Global Constraints
- execution_boundary/__init__.py
- position_actions/evaluator.py
- Global Constraints
- ExecutionIntent
- trainer.py
- test_agent_tools.py
- Phase 7 deterministic runtime orchestration
- _context
- ReflectionPolicy
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
- RuntimeStreamRunner
- Position action safety
- .validate_and_bind_identity
- session_features
- Signal
- evaluate_predictions
- datasets/__init__.py
- model_validator
- Phase 8 Task 7 Governed Candidate Replay Evaluator Design
- generate_labels
- SQLiteProposalEvaluationStore
- Global Constraints
- Phase 8 Task 6 Deterministic Evaluation Execution Adapter Design
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- EntryGateway
- Global constraints
- LocalModelRegistry
- position_management/evaluator.py
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
- mt5/__init__.py
- model_validator
- policies.py
- Deterministic Weekly Reflection and Pattern Lifecycle
- Advisory Improvement Proposals
- execution.py
- breakout_features
- system.py
- model_validator
- MetaTrader5Gateway
- model_validator
- test_quant_development_runner.py
- .bind_identity
- _MT5Module
- Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design
- .validate_and_bind_identity
- processor.py
- replay.py
- Global Constraints
- .normalize_and_bind_identity
- ReplayClock
- FeatureManifest
- CausalFeatureSnapshot
- canonical_hash
- Proposal Evaluation
- proposal_cli.py
- .normalize_validate_and_bind_identity
- model_validator
- test_feature_formulas.py
- ensure_utc
- recovery.py
- .bind_identity
- model_validator
- FakeGateway
- atr
- .terminal_path
- _ReplayContext
- default_shared_kernel_policy_set
- ContractAndRiskTests
- runtime/journal.py
- .validate_event
- .validate_and_bind_identity
- .validate_and_bind_identity
- build_mt5_dataset.py
- Global Constraints
- Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design
- model_validator
- test_system_replay.py
- Shared-Kernel Candidate Driver V1
- InMemoryExecutionLedger
- EvidenceBundle
- EventSource
- model_validator
- model_validator
- multi_timeframe_features
- price_action_features
- .bind_identity

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 187 edges
2. `Signal` - 92 edges
3. `RuntimeEvent` - 92 edges
4. `MetricScope` - 88 edges
5. `SQLiteProposalEvaluationStore` - 64 edges
6. `ExecutionIntent` - 64 edges
7. `ReflectionModel` - 63 edges
8. `SQLiteImprovementProposalStore` - 57 edges
9. `ExecutionResult` - 55 edges
10. `run_system_replay()` - 50 edges

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

## Communities (196 total, 41 thin omitted)

### Community 0 - "daily.py"
Cohesion: 0.35
Nodes (20): FindingCategory, FindingSignal, StrEnum, ReflectionFinding, SampleGuardRecord, SampleGuardStatus, _agent_findings(), _average() (+12 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.15
Nodes (28): BarrierMode, CollisionPolicy, EntryReference, LabelDefinition, LabelKind, BaseModel, model_validator, StrEnum (+20 more)

### Community 2 - "reflection/__main__.py"
Cohesion: 0.10
Nodes (34): Any, register_candidate_replay_commands(), Any, register_execution_commands(), _build(), _days(), _emit(), _latest_records() (+26 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.17
Nodes (12): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifestEntry, BaseModel, FeatureDefinition, FeatureRegistry, _integer(), _output_lookback() (+4 more)

### Community 4 - "inference.py"
Cohesion: 0.09
Nodes (31): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., dump_artifact(), file_hash(), load_artifact(), Any (+23 more)

### Community 5 - "indicators.py"
Cohesion: 0.21
Nodes (23): aroon(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1., Wilder average (RMA): SMA seed followed by alpha=1/period recursion. (+15 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.11
Nodes (41): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+33 more)

### Community 7 - "update_scenario"
Cohesion: 0.17
Nodes (37): _create_thesis(), _new_scenarios(), UTCDateTime, Apply one M5 or intrabar evidence event without consulting a clock., _scenario_id(), ScenarioDefinition, ScenarioPolicy, _thesis_id() (+29 more)

### Community 8 - "development/config.py"
Cohesion: 0.08
Nodes (44): AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+36 more)

### Community 9 - "axq/config.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.14
Nodes (27): DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., FakeEntryAdapter, FakePositionActionAdapter, FakeProcessor, FakeSnapshotProvider, _fresh(), _intent() (+19 more)

### Community 11 - "reflection/__init__.py"
Cohesion: 0.07
Nodes (69): _emit(), _fixture(), handle_candidate_replay_command(), Namespace, Path, CLI handlers for governed deterministic candidate replay evaluation., _run(), _show() (+61 more)

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
Nodes (28): main(), main(), main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., DataFrame, Leakage-safe multi-timeframe alignment. (+20 more)

### Community 23 - "SQLiteExecutionLedger"
Cohesion: 0.13
Nodes (22): Connection, Path, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, ExecutionTransition, _intent(), _link(), _position() (+14 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.11
Nodes (19): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Primary and intrabar paths (+11 more)

### Community 25 - "weekly_contracts.py"
Cohesion: 0.08
Nodes (51): _build(), _emit(), handle_weekly_command(), _history(), _latest(), _policy(), date, Namespace (+43 more)

### Community 26 - "dataset.py"
Cohesion: 0.09
Nodes (28): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., LabelManifest, BaseModel, Path, load_training_dataset() (+20 more)

### Community 27 - "RuntimeEvent"
Cohesion: 0.08
Nodes (59): execution_result_to_runtime_event(), Bridge typed execution results into the shared Phase 6 runtime path., Convert actionable execution feedback; local NO_ACTION stays local., Strict contracts for deterministic management of already-open positions., BaseModel, datetime, StrEnum, Canonical runtime event envelopes for live and deterministic replay. (+51 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.05
Nodes (37): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+29 more)

### Community 29 - "_deterministic.py"
Cohesion: 0.18
Nodes (21): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, DeterministicSpecialistAgent, fact_map(), Interpretation, numeric() (+13 more)

### Community 30 - "README.md"
Cohesion: 0.17
Nodes (7): Model registry and promotion contract, Phase 5 development layer, Quant model training, Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.13
Nodes (33): FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool, fact_name() (+25 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.17
Nodes (6): RuntimeStatus, JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe., Perform at most one read-only refresh when the bounded cadence elapsed., Own ordering and gates while delegating every trading semantic decision., RuntimeOrchestrator

### Community 34 - "recovery_contracts.py"
Cohesion: 0.13
Nodes (29): evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis, _conflict_reason(), _finding() (+21 more)

### Community 35 - "reduce_state"
Cohesion: 0.17
Nodes (35): broker_snapshot_runtime_events(), initial_runtime_state(), datetime, Apply one causally available event without consulting a wall clock., Construct a canonical state with explicit unknown component values., reduce_state(), test_expired_thesis_blocks_resume_without_mutating_or_reviving_it(), test_runtime_refresh_uses_canonical_exposure_and_constraint_events() (+27 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "attribution.py"
Cohesion: 0.07
Nodes (61): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+53 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.08
Nodes (24): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+16 more)

### Community 39 - "timedelta"
Cohesion: 0.07
Nodes (67): _aggregate(), CanonicalMetricSamplesAdapter, EvaluationAdapterOutput, input_artifact_ref(), Closed deterministic adapter for canonical metric sample artifacts., Aggregate exact preregistered metric series without executing candidate code., _artifact(), _emit() (+59 more)

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
Cohesion: 0.22
Nodes (10): Experience, Path, Durable semantic records; sequence numbers never participate in identity., SQLiteExperienceStore, _decision(), test_conflicting_same_id_content_fails_closed(), test_duplicate_semantic_insert_is_idempotent(), test_sqlite_update_and_delete_are_rejected() (+2 more)

### Community 44 - "MetricScope"
Cohesion: 0.06
Nodes (75): CandidateKind, MetricScope, SemanticArtifactRef, canonical_record_bytes(), BaseModel, _emit(), handle_shared_kernel_candidate_command(), _optional_scope() (+67 more)

### Community 45 - "DailyReflection"
Cohesion: 0.09
Nodes (50): DecisionExperience, DailyReflection, build_improvement_proposals(), _content(), _index_unique(), ProposalBuildResult, ProposalEligibilityAssessment, Experience (+42 more)

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
Cohesion: 0.09
Nodes (28): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), datetime, Demo-only MetaTrader 5 transport for Task 7 position-action intents. (+20 more)

### Community 50 - "replay_validation/__init__.py"
Cohesion: 0.17
Nodes (20): StrEnum, ReplayClosedTrade, ReplayFill, ReplaySide, Deterministic system-replay validation support., BaseModel, model_validator, Path (+12 more)

### Community 51 - "Phase 3 label contract"
Cohesion: 0.40
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 52 - "service.py"
Cohesion: 0.20
Nodes (7): BrokerSnapshotProvider, DecisionCycleProcessor, PositionActionAdapter, datetime, Protocol, Deterministic composition service for the completed Phase 6/7 boundaries., RuntimeRunner

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.17
Nodes (37): ResumeStatus, default_demo_position_management_policy(), evaluate_position(), Return conservative deterministic demo defaults, not optimized strategy truth., Evaluate one open position without mutating state or invoking execution…, _broker_constraints(), _context(), _fresh() (+29 more)

### Community 55 - "orchestration/contracts.py"
Cohesion: 0.14
Nodes (20): load_runtime_config(), BaseModel, Path, Strict operational configuration for the Phase 7 runtime service., RuntimeConfig, DecisionCycle, OutcomeCount, BaseModel (+12 more)

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
Cohesion: 0.18
Nodes (31): RuntimeError, Submission may have reached the broker and requires reconciliation., UnknownSubmissionState, _adapter(), _discipline(), _intent(), _observation(), _policy() (+23 more)

### Community 75 - "OperatorControls"
Cohesion: 0.29
Nodes (3): OperatorControls, Monotonic operator gates: callers cannot use this contract to bypass safety., test_operator_controls_only_become_more_conservative()

### Community 76 - "MasterProposal"
Cohesion: 0.16
Nodes (31): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, MasterProposal, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion. (+23 more)

### Community 77 - "snapshot.py"
Cohesion: 0.22
Nodes (18): BrokerObjectKind, MT5SnapshotError, A broker snapshot could not be acquired without guessing., _epoch_seconds(), MT5BrokerSnapshotProvider, _optional_float(), _optional_int(), _optional_price() (+10 more)

### Community 78 - "SQLiteRuntimeJournal"
Cohesion: 0.18
Nodes (8): JournalEntry, Connection, Path, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., SQLiteRuntimeJournal, JournalEventSource, Canonical event source reconstructed from append-only journal records.

### Community 79 - "default_registry"
Cohesion: 0.16
Nodes (16): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., default_registry(), Any, DataFrame, statistical_features() (+8 more)

### Community 80 - "preflight.py"
Cohesion: 0.23
Nodes (17): The transport failed before submission could be accepted., TransportFailure, _account_mode(), _float_value(), _int_value(), MT5EntryPreflight, _positive_float(), datetime (+9 more)

### Community 81 - "discipline/__init__.py"
Cohesion: 0.18
Nodes (23): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+15 more)

### Community 82 - "ReflectionModel"
Cohesion: 0.10
Nodes (59): Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Append-only persistence for governed candidate replay evaluation., BaseModel, Immutable content-addressed contracts for deterministic daily reflection., ReflectionModel, AcceptanceCriterion, CriterionComparator, CriterionOutcome (+51 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "execution_boundary/__init__.py"
Cohesion: 0.19
Nodes (20): Demo-safe execution adapter boundary with explicit idempotency semantics., build_execution_intent(), default_execution_policy(), RiskContext, Pure construction of provenance-bound execution intents., Return the conservative, execution-disabled baseline policy., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links() (+12 more)

### Community 85 - "position_actions/evaluator.py"
Cohesion: 0.18
Nodes (26): PositionActionContext, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, BaseModel, StrEnum (+18 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "ExecutionIntent"
Cohesion: 0.17
Nodes (16): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, ExecutionTransport, datetime, Protocol, Process one immutable intent idempotently., Submit an already approved intent to the execution transport. (+8 more)

### Community 88 - "trainer.py"
Cohesion: 0.07
Nodes (45): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+37 more)

### Community 89 - "test_agent_tools.py"
Cohesion: 0.11
Nodes (23): PredictiveModelEvidenceProvider, Any, Protocol, QuantAgentEvidenceProvider, Return label-to-probability facts without a trading decision., Narrow adapter around the existing frozen Phase 4 QuantAgent., _ExplodingTool, _FailingProvider (+15 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "_context"
Cohesion: 0.17
Nodes (33): default_position_action_policy(), Return conservative deterministic V1 safety defaults., PositionSide, _context(), _evaluate(), _fresh(), _intent(), _management() (+25 more)

### Community 92 - "ReflectionPolicy"
Cohesion: 0.10
Nodes (30): MetricFact, ReflectionPolicy, _canonical_payload(), datetime, Path, Append-only SQLite persistence for daily reflection records., Persist policies and immutable daily revisions as semantic records., SQLiteReflectionStore (+22 more)

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "FakeMT5Module"
Cohesion: 0.12
Nodes (6): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity(), test_symbol_mapping_is_explicit_auditable_and_deterministic()

### Community 95 - "evidence"
Cohesion: 0.15
Nodes (20): HypothesisInvalidation, model_validator, evidence(), datetime, parametrize, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields(), test_agent_evidence_identity_is_deterministic_and_round_trips() (+12 more)

### Community 96 - "features/analysis.py"
Cohesion: 0.25
Nodes (17): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+9 more)

### Community 98 - "SQLiteImprovementProposalStore"
Cohesion: 0.13
Nodes (28): ImprovementProposal, ImprovementProposalPolicy, ProposalEvidenceGuard, ProposalGuardKind, ProposalStatusTransition, ProposalTargetComponent, StrEnum, _payload() (+20 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.14
Nodes (8): MT5PersistedIntentLink, _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket(), test_snapshot_maps_account_market_books_exposure_and_constraints()

### Community 101 - "Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design"
Cohesion: 0.13
Nodes (14): Append-only persistence and supersession, Architecture, Baseline validation, CLI, Exact provenance validation, ISO-week boundary and availability, Knowledge-status lifecycle, Pattern generation (+6 more)

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "MT5Gateway"
Cohesion: 0.09
Nodes (16): MT5Gateway, MT5SymbolMapping, Protocol, _float_value(), _int_value(), MT5ExecutionAdapter, MT5ExecutionTransport, _positive_int() (+8 more)

### Community 104 - "PositionGateway"
Cohesion: 0.16
Nodes (13): _adapter(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send(), test_modify_stop_preserves_ticket_tp_and_cannot_increase_exposure() (+5 more)

### Community 105 - "RuntimeStreamRunner"
Cohesion: 0.12
Nodes (12): JournalOutcome, JournalRecord, BaseModel, model_validator, JournalSemantic, Feed one source/clock adapter through the unchanged shared kernel., Expose the immutable current state for orchestration and diagnostics., Restore durable thesis continuity before accepting a new event. (+4 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 108 - "session_features"
Cohesion: 0.23
Nodes (10): _local_window(), Any, DataFrame, Series, DST-aware session features. Source timestamps are interpreted as UTC., session_features(), test_london_and_new_york_dst_transitions(), test_manifest_is_reproducible_and_complete() (+2 more)

### Community 109 - "Signal"
Cohesion: 0.35
Nodes (16): Signal, _contribution(), _discipline(), _evidence(), _intent(), _master(), _of_type(), _result() (+8 more)

### Community 110 - "evaluate_predictions"
Cohesion: 0.16
Nodes (21): calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), overfitting_report(), Any, DataFrame, ndarray, Series (+13 more)

### Community 111 - "datasets/__init__.py"
Cohesion: 0.15
Nodes (21): DatasetBuildResult, Path, write_dataset(), DatasetBuildConfig, BaseModel, RowPolicy, SplitPolicy, build() (+13 more)

### Community 113 - "Phase 8 Task 7 Governed Candidate Replay Evaluator Design"
Cohesion: 0.22
Nodes (8): CLI, Contracts and identity, Controlled replay engine, Exact linkage and Final OOS boundary, Persistence, service, and reuse, Phase 8 Task 7 Governed Candidate Replay Evaluator Design, Scope, Validation

### Community 114 - "generate_labels"
Cohesion: 0.19
Nodes (20): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., generate_labels(), DataFrame (+12 more)

### Community 115 - "SQLiteProposalEvaluationStore"
Cohesion: 0.08
Nodes (27): main(), Database, Connection, Path, Path, _build_plan(), _emit(), handle_evaluation_command() (+19 more)

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
Nodes (17): _adapter(), EntryGateway, _intent(), _policy(), datetime, Exception, parametrize, test_broker_partial_fill_maps_without_resubmitting_remainder() (+9 more)

### Community 121 - "Global constraints"
Cohesion: 0.25
Nodes (7): Global constraints, Phase 7 Task 8 Direct MT5 Transport Implementation Plan, Task 1: Gateway and normalized MT5 contracts, Task 2: Canonical broker snapshots, Task 3: Entry transport and complete dry-run preflight, Task 4: Durable position-action transport, Task 5: Documentation, optional read-only smoke, and final verification

### Community 122 - "LocalModelRegistry"
Cohesion: 0.38
Nodes (5): LocalModelRegistry, Any, BaseModel, Path, RegistryEntry

### Community 123 - "position_management/evaluator.py"
Cohesion: 0.20
Nodes (18): MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy, PositionManagementReason, PositionManagementResult, BaseModel (+10 more)

### Community 124 - "Phase 8 Task 4 Advisory Improvement Proposal Design"
Cohesion: 0.20
Nodes (9): Append-only persistence and supersession, CLI, Contracts and identity, Deterministic advisory content, Eligibility, Phase 8 Task 4 Advisory Improvement Proposal Design, Proposal lifecycle, Scope (+1 more)

### Community 125 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 6 Deterministic Evaluation Execution Adapter Implementation Plan, Task 1: Execution and unavailable-observation contracts, Task 2: Closed deterministic metric-sample adapter, Task 3: Append-only request and audit persistence, Task 4: Execution service and idempotent recovery, Task 5: CLI, documentation, and final verification

### Community 126 - "ExperienceProvenance"
Cohesion: 0.14
Nodes (21): ExperienceProvenance, model_validator, _agent(), _findings(), _management(), _provenance(), datetime, _rejection() (+13 more)

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
Cohesion: 0.33
Nodes (6): Commands, Missing rows, Phase 3 dataset contract, Reproducibility and separation, Splits, purge, and embargo, Storage and immutability

### Community 137 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 4 Advisory Improvement Proposal Implementation Plan, Task 1: Proposal contracts and identities, Task 2: Pure eligibility, provenance, and proposal construction, Task 3: Append-only proposal and lifecycle persistence, Task 4: CLI integration, Task 5: Unchanged baseline and durable context

### Community 138 - "folds.py"
Cohesion: 0.09
Nodes (30): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., chronological_split(), IndexRange (+22 more)

### Community 139 - "mt5/__init__.py"
Cohesion: 0.16
Nodes (12): MT5ConnectionError, MT5Constants, BaseModel, RuntimeError, Narrow contracts isolating the optional MetaTrader5 package., The terminal package or connected terminal is unavailable., _load_mt5(), Lazy concrete wrapper around the Windows-only MetaTrader5 package. (+4 more)

### Community 141 - "policies.py"
Cohesion: 0.18
Nodes (21): EntryContextProvider, PositionActionContextProvider, PositionContextProvider, Immutable composition policy set for the shared Phase 6/7 replay kernel., BaseModel, StrEnum, Strict contracts for the deterministic financial Risk boundary., RiskBoundaryModel (+13 more)

### Community 142 - "Deterministic Weekly Reflection and Pattern Lifecycle"
Cohesion: 0.33
Nodes (5): Deterministic Weekly Reflection and Pattern Lifecycle, Identity, Knowledge lifecycle, Verified baseline, Weekly contract

### Community 143 - "Advisory Improvement Proposals"
Cohesion: 0.33
Nodes (5): Advisory Improvement Proposals, Eligibility and provenance, Identity and supersession, Lifecycle, Verified baseline

### Community 144 - "execution.py"
Cohesion: 0.17
Nodes (9): _identity(), _PendingClose, _PendingStop, datetime, Deterministic, transport-only fill mechanics for system replay., A causal fill book; it contains no signal or policy decisions., ReplayBar, ReplayBarResult (+1 more)

### Community 145 - "breakout_features"
Cohesion: 0.40
Nodes (4): breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars.

### Community 146 - "system.py"
Cohesion: 0.23
Nodes (17): main(), Command-line entry point for Phase 7 system replay and result display., _catalog(), compare_replays(), _counts(), _file_sha256(), load_replay_frame(), _merge_htf_bias() (+9 more)

### Community 148 - "MetaTrader5Gateway"
Cohesion: 0.25
Nodes (4): _mapping(), _mappings(), MetaTrader5Gateway, Operational gateway; paths and process state are never semantic identity.

### Community 150 - "test_quant_development_runner.py"
Cohesion: 0.23
Nodes (13): compare_runs(), Any, Path, Compare completed development runs without retraining or scalar ranking., _read(), experiment(), Path, test_compare_runs_uses_multiple_evidence_dimensions() (+5 more)

### Community 153 - "Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design"
Cohesion: 0.17
Nodes (11): Append-only persistence, Candidate contract, CLI, Evaluation result, Identity and serialization, Operator decision boundary, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design, Preregistered plan (+3 more)

### Community 155 - "processor.py"
Cohesion: 0.16
Nodes (11): ResumeReadiness, DeterministicDecisionProcessor, EntryDecisionInputs, BaseModel, Concrete composition of existing deterministic Phase 7 decision boundaries., Causal contexts supplied by the runtime-specific context adapter., Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, Compose existing pure functions; adapters provide causal context only. (+3 more)

### Community 156 - "replay.py"
Cohesion: 0.14
Nodes (13): Collection, ScenarioTransition, Protocol, Clock contract used outside the pure reducer., RuntimeClock, Protocol, RuntimeJournal, Exception (+5 more)

### Community 157 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Implementation Plan, Task 1: Evaluation contracts and protected-OOS invariants, Task 2: Pure preregistration and result evaluation, Task 3: Append-only evaluation persistence, Task 4: Evaluation CLI without execution, Task 5: Documentation and final verification

### Community 159 - "ReplayClock"
Cohesion: 0.37
Nodes (17): Explicitly advanced deterministic replay clock., ReplayClock, _event(), _kernel(), datetime, _scenario_transition(), _snapshot(), test_duplicate_event_is_journaled_without_second_decision_record() (+9 more)

### Community 160 - "FeatureManifest"
Cohesion: 0.18
Nodes (12): FeatureManifest, Path, Canonical feature-manifest models., feature_ablation_variants(), Manifest-bound feature ablation plans; execution remains fold-local., fold(), frame(), DataFrame (+4 more)

### Community 161 - "CausalFeatureSnapshot"
Cohesion: 0.19
Nodes (12): CausalFeatureSnapshot, Any, FactScalar, field_validator, _event(), datetime, _snapshot(), test_feature_snapshots_can_be_recovered_by_event_without_mutation() (+4 more)

### Community 162 - "canonical_hash"
Cohesion: 0.14
Nodes (6): model_validator, model_validator, model_validator, model_validator, canonical_hash(), Any

### Community 163 - "Proposal Evaluation"
Cohesion: 0.40
Nodes (4): CLI workflow, Governance boundary, Persistence and corrections, Proposal Evaluation

### Community 164 - "proposal_cli.py"
Cohesion: 0.34
Nodes (13): _build(), _emit(), handle_proposal_command(), _history(), _latest(), _policy(), Namespace, Path (+5 more)

### Community 167 - "test_feature_formulas.py"
Cohesion: 0.23
Nodes (11): skipif, money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility() (+3 more)

### Community 168 - "ensure_utc"
Cohesion: 0.21
Nodes (7): ensure_utc(), datetime, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Return the current instant in UTC., Live clock backed by the host system clock., SystemUTCClock

### Community 169 - "recovery.py"
Cohesion: 0.30
Nodes (9): CheckpointLedger, RecoveryCheckpoint, create_recovery_checkpoint(), persist_graceful_shutdown(), Protocol, Deterministic runtime refresh and checkpoint builders for restart recovery., Persist the recovery anchor, then flush both durable append-only stores., SyncJournal (+1 more)

### Community 173 - "atr"
Cohesion: 0.29
Nodes (9): atr(), true_range(), market_structure_features(), Any, DataFrame, Causal market-structure features. A candidate pivot at position p is emitted at…, Any, DataFrame (+1 more)

### Community 175 - "_ReplayContext"
Cohesion: 0.22
Nodes (6): ReplayPosition, _event(), _fresh(), Any, datetime, _ReplayContext

### Community 176 - "default_shared_kernel_policy_set"
Cohesion: 0.22
Nodes (9): default_shared_kernel_policy_set(), BaseModel, Complete reviewed policy composition for one shared-kernel replay., Return a new set with only the reviewed Master-fusion policy replaced., Reproduce the exact policy composition used by Phase 7 system replay., SharedKernelPolicySet, test_default_shared_kernel_policy_set_is_frozen_and_content_addressed(), test_explicit_default_policy_set_preserves_replay_bytes() (+1 more)

### Community 177 - "ContractAndRiskTests"
Cohesion: 0.36
Nodes (7): calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext, RiskLimits, veto_reasons(), ContractAndRiskTests

### Community 178 - "runtime/journal.py"
Cohesion: 0.31
Nodes (8): JournalOutcomeStatus, JournalRecordType, JournalSemantic, StrEnum, UTCDateTime, Typed append-only runtime journal for deterministic replay., _record_type(), _semantic_id()

### Community 182 - "build_mt5_dataset.py"
Cohesion: 0.31
Nodes (8): HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel, Path, Explicit user-run MT5 multi-timeframe download and immutable dataset build.

### Community 183 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Implementation Plan, Task 1: Shared replay policy composition boundary, Task 2: Frozen candidate and governed data contracts, Task 3: Closed shared-kernel engine and metric extraction, Task 4: Append-only store and idempotent service, Task 5: CLI, documentation, and final governance gate

### Community 184 - "Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design"
Cohesion: 0.25
Nodes (7): CLI and controlled validation, Execution and metric production, Governed inputs and identity, Persistence and recovery, Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design, Purpose, Shared-kernel injection boundary

### Community 186 - "test_system_replay.py"
Cohesion: 0.36
Nodes (5): PendingReplayEntry, _bar(), test_entry_executes_at_next_m5_open_and_cannot_stop_on_fill_bar(), test_modified_stop_never_retroactively_triggers_in_modification_bar(), test_system_replay_retains_exact_attribution_journal_semantics()

### Community 187 - "Shared-Kernel Candidate Driver V1"
Cohesion: 0.29
Nodes (6): Candidate injection boundary, Commands, Controlled V1 validation, Governance and data, Persistence and retry, Shared-Kernel Candidate Driver V1

### Community 190 - "EventSource"
Cohesion: 0.40
Nodes (4): EventSource, Protocol, Source of events already ordered for causal reduction., Yield events in canonical availability order.

### Community 193 - "multi_timeframe_features"
Cohesion: 0.50
Nodes (3): multi_timeframe_features(), Any, DataFrame

### Community 194 - "price_action_features"
Cohesion: 0.50
Nodes (3): price_action_features(), Any, DataFrame

## Knowledge Gaps
- **348 isolated node(s):** `Append-only persistence and supersession`, `Architecture`, `Baseline validation`, `CLI`, `Exact provenance validation` (+343 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1034 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `DatasetManifest`, `LabelDefinition`, `inference.py`, `agents/__init__.py`, `update_scenario`, `development/config.py`, `folds.py`, `mt5/__init__.py`, `reflection/__init__.py`, `model_validator`, `policies.py`, `execution.py`, `system.py`, `model_validator`, `model_validator`, `datasets/builder.py`, `.bind_identity`, `weekly_contracts.py`, `.validate_and_bind_identity`, `dataset.py`, `RuntimeEvent`, `_deterministic.py`, `.normalize_and_bind_identity`, `replay.py`, `ToolResult`, `recovery_contracts.py`, `attribution.py`, `.normalize_validate_and_bind_identity`, `timedelta`, `model_validator`, `.bind_identity`, `SQLiteExperienceStore`, `MetricScope`, `DailyReflection`, `model_validator`, `position.py`, `replay_validation/__init__.py`, `.validate_event`, `runtime/journal.py`, `.validate_and_bind_identity`, `.validate_and_bind_identity`, `orchestration/contracts.py`, `model_validator`, `model_validator`, `model_validator`, `.bind_identity`, `runner.py`, `MasterProposal`, `discipline/__init__.py`, `ReflectionModel`, `execution_boundary/__init__.py`, `position_actions/evaluator.py`, `trainer.py`, `ReflectionPolicy`, `evidence`, `SQLiteImprovementProposalStore`, `model_validator`, `RuntimeStreamRunner`, `.validate_and_bind_identity`, `model_validator`, `SQLiteProposalEvaluationStore`, `position_management/evaluator.py`, `ExperienceProvenance`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `daily.py`, `reflection/__main__.py`, `inference.py`, `test_runtime_orchestration.py`, `policies.py`, `system.py`, `SQLiteExecutionLedger`, `RuntimeEvent`, `test_risk_boundary.py`, `recovery_contracts.py`, `attribution.py`, `SQLiteExperienceStore`, `DailyReflection`, `_ReplayContext`, `ContractAndRiskTests`, `_context`, `evaluate_discipline`, `schemas.py`, `test_execution_boundary.py`, `MasterProposal`, `preflight.py`, `discipline/__init__.py`, `execution_boundary/__init__.py`, `position_actions/evaluator.py`, `ExecutionIntent`, `_context`, `ReflectionPolicy`, `EntryGateway`, `ExperienceProvenance`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `run_system_replay()` connect `system.py` to `update_scenario`, `logging.py`, `execution.py`, `SQLiteExecutionLedger`, `processor.py`, `RuntimeEvent`, `ReplayClock`, `RuntimeOrchestrator`, `canonical_hash`, `reduce_state`, `timedelta`, `MetricScope`, `_ReplayContext`, `default_shared_kernel_policy_set`, `position.py`, `replay_validation/__init__.py`, `orchestration/contracts.py`, `test_system_replay.py`, `SQLiteRuntimeJournal`, `ExecutionIntent`, `RuntimeStreamRunner`, `Signal`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 204 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 204 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 70 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 67 inferred relationships involving `MetricScope` (e.g. with `_fixture()` and `_run()`) actually correct?**
  _`MetricScope` has 67 INFERRED edges - model-reasoned connections that need verification._