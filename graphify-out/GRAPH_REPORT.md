# Graph Report - phase-8-reflection-experience  (2026-09-12)

## Corpus Check
- 383 files · ~192,348 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3964 nodes · 13092 edges · 192 communities (152 shown, 37 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 2250 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e5804765`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ReflectionPolicy
- LabelDefinition
- test_reflection_cli.py
- axq/features/registry.py
- QuantAgentEvidenceProvider
- indicators.py
- agents/__init__.py
- timedelta
- development/config.py
- axq/config.py
- test_runtime_orchestration.py
- SQLiteCandidateReplayStore
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
- _context
- System architecture (Phase 0-7 baseline)
- ReflectionModel
- dataset.py
- runtime/__init__.py
- Architecture decision log
- _deterministic.py
- README.md
- test_risk_boundary.py
- ToolResult
- RuntimeOrchestrator
- execution_boundary/__init__.py
- reduce_state
- Global Constraints
- attribution.py
- Phase 0-6 runbook
- versioning.py
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- MetricScope
- SQLitePairedEvaluationStore
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- SQLitePositionActionTransportLedger
- ReplayExecutionBook
- paired_evaluation_contracts.py
- SQLitePairedEvaluationReviewStore
- Repository instructions
- _context
- persisted_review_fixture
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
- test_execution_boundary.py
- PositionActionIntent
- policies.py
- snapshot.py
- .validate_and_bind_identity
- default_registry
- preflight.py
- replay_validation/__init__.py
- reflection/__init__.py
- Global Constraints
- ensure_utc
- position_actions/evaluator.py
- Global Constraints
- ExecutionIntent
- trainer.py
- test_agent_tools.py
- Phase 7 deterministic runtime orchestration
- experience/__init__.py
- persisted_paired_fixture
- Global Constraints
- FakeMT5Module
- evidence
- features/analysis.py
- candles
- SQLiteImprovementProposalStore
- SnapshotGateway
- model_validator
- Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design
- Phase 7 Task 7: Position Action Safety and Journal Plan
- MT5Gateway
- PositionGateway
- position.py
- Position action safety
- ExperienceType
- session_features
- test_daily_reflection.py
- evaluate_predictions
- test_datasets_phase3.py
- MasterProposal
- Phase 8 Task 7 Governed Candidate Replay Evaluator Design
- generate_labels
- SQLiteProposalEvaluationStore
- Global Constraints
- Phase 8 Task 6 Deterministic Evaluation Execution Adapter Design
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- EntryGateway
- Global constraints
- inference.py
- test_evaluation_execution_adapter.py
- Phase 8 Task 4 Advisory Improvement Proposal Design
- Global Constraints
- DecisionExperience
- Global Constraints
- DatasetManifest
- Deterministic Evaluation Execution
- ReplayOutcomeArtifact
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
- system.py
- Deterministic Weekly Reflection and Pattern Lifecycle
- Advisory Improvement Proposals
- Global Constraints
- breakout_features
- run_system_replay
- model_validator
- MetaTrader5Gateway
- model_validator
- execution.py
- Phase 8 Task 9 Deterministic Paired Evaluation Design
- _MT5Module
- Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design
- .validate_and_bind_identity
- test_paired_evaluation_contracts.py
- model_validator
- Global Constraints
- .normalize_and_bind_identity
- RuntimeEvent
- LocalModelRegistry
- paired_evaluation_cli.py
- canonical_hash
- Proposal Evaluation
- InMemoryExecutionLedger
- .normalize_validate_and_bind_identity
- .normalize_validate_and_bind_identity
- test_feature_formulas.py
- Phase 8 Task 10 Governed Operator Review Bridge Design
- Phase 3 label contract
- .bind_identity
- model_validator
- Deterministic paired baseline-vs-candidate comparison
- test_experience_analytics_cli.py
- .terminal_path
- Governed paired-evaluation review
- Phase 8 Task 10 Governed Operator Review Bridge Implementation Plan
- .validate_and_bind_identity
- .validate_event
- .validate_and_bind_identity
- .validate_and_bind_identity
- build_mt5_dataset.py
- Global Constraints
- Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design
- model_validator
- .bind_identity
- Shared-Kernel Candidate Driver V1
- .validate_and_bind_identity
- price_action_features
- SharedKernelPolicySet

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 202 edges
2. `MetricScope` - 107 edges
3. `RuntimeEvent` - 92 edges
4. `Signal` - 92 edges
5. `ReflectionModel` - 72 edges
6. `SQLiteProposalEvaluationStore` - 72 edges
7. `ExecutionIntent` - 64 edges
8. `SQLiteImprovementProposalStore` - 61 edges
9. `CanonicalMetricSampleArtifact` - 60 edges
10. `ExecutionResult` - 55 edges

## Surprising Connections (you probably didn't know these)
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_walk_forward_split_definitions_are_deterministic()` --calls--> `walk_forward_splits()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_symbol_mapping_is_explicit_auditable_and_deterministic()` --calls--> `MT5SymbolMapping`  [INFERRED]
  tests/test_mt5_gateway.py → src/axq/mt5/contracts.py
- `test_paired_contracts_are_exported_from_reflection_package()` --uses--> `PairedEvaluationRequest`  [INFERRED]
  tests/test_paired_evaluation_contracts.py → src/axq/reflection/paired_evaluation_contracts.py

## Import Cycles
- None detected.

## Communities (192 total, 37 thin omitted)

### Community 0 - "ReflectionPolicy"
Cohesion: 0.16
Nodes (34): FindingCategory, FindingSignal, MetricFact, StrEnum, ReflectionFinding, ReflectionPolicy, SampleGuardRecord, _agent_findings() (+26 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.13
Nodes (31): BarrierMode, CollisionPolicy, EntryReference, LabelDefinition, LabelKind, BaseModel, model_validator, StrEnum (+23 more)

### Community 2 - "test_reflection_cli.py"
Cohesion: 0.46
Nodes (7): _decision(), _experience_store(), Path, test_build_range_is_deterministic_and_idempotent(), test_build_rejects_reversed_date_range(), test_changed_input_creates_explicit_cli_supersession(), test_show_and_report_emit_machine_readable_json()

### Community 3 - "axq/features/registry.py"
Cohesion: 0.12
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., FeatureDefinition (+10 more)

### Community 4 - "QuantAgentEvidenceProvider"
Cohesion: 0.29
Nodes (4): Any, QuantAgentEvidenceProvider, Return label-to-probability facts without a trading decision., Narrow adapter around the existing frozen Phase 4 QuantAgent.

### Community 5 - "indicators.py"
Cohesion: 0.15
Nodes (32): aroon(), atr(), cci(), directional_movement(), DataFrame, Series, Causal technical-indicator primitives with explicit warm-up semantics. All…, EMA seeded with the first period's SMA; invalid until index period-1. (+24 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.08
Nodes (50): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+42 more)

### Community 7 - "timedelta"
Cohesion: 0.17
Nodes (36): _agent_pair(), _create(), _event(), _market(), datetime, parametrize, test_delayed_older_market_time_is_accepted_at_later_availability(), test_explicit_intrabar_expiry_evidence_is_terminal() (+28 more)

### Community 8 - "development/config.py"
Cohesion: 0.06
Nodes (51): AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+43 more)

### Community 9 - "axq/config.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.05
Nodes (52): load_runtime_config(), BaseModel, Path, Strict operational configuration for the Phase 7 runtime service., RuntimeConfig, DecisionPlan, OperatorControls, StrEnum (+44 more)

### Community 11 - "SQLiteCandidateReplayStore"
Cohesion: 0.07
Nodes (60): _emit(), _fixture(), handle_candidate_replay_command(), Namespace, Path, CLI handlers for governed deterministic candidate replay evaluation., _run(), _show() (+52 more)

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
Cohesion: 0.12
Nodes (24): main(), main(), DataFrame, Leakage-safe multi-timeframe alignment., Attach bars only when their UTC close time is at/before the base bar's UTC…, synchronize_completed_bars(), timeframe_delta(), DataFrame (+16 more)

### Community 23 - "_context"
Cohesion: 0.17
Nodes (31): default_position_action_policy(), Return conservative deterministic V1 safety defaults., _context(), _evaluate(), _fresh(), _intent(), _management(), _position() (+23 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.10
Nodes (20): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Phase 8 governed comparison boundary (+12 more)

### Community 25 - "ReflectionModel"
Cohesion: 0.04
Nodes (129): Any, register_candidate_replay_commands(), DailyReflection, BaseModel, Immutable content-addressed contracts for deterministic daily reflection., ReflectionModel, SampleGuardStatus, Any (+121 more)

### Community 26 - "dataset.py"
Cohesion: 0.12
Nodes (17): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., load_training_dataset(), _parse_manifest(), Any, DataFrame (+9 more)

### Community 27 - "runtime/__init__.py"
Cohesion: 0.06
Nodes (73): Bridge typed execution results into the shared Phase 6 runtime path., Immutable contracts for safe actions on authoritative open positions., position_action_result_to_runtime_event(), Dedicated append-only transport contracts for safe position actions., Strict contracts for deterministic management of already-open positions., datetime, StrEnum, Canonical runtime event envelopes for live and deterministic replay. (+65 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.05
Nodes (39): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+31 more)

### Community 29 - "_deterministic.py"
Cohesion: 0.17
Nodes (26): Deterministic hierarchical market-structure interpretation., AbstentionReason, AgentStatus, DirectionalBias, EvidencePolarity, EvidenceReference, StrEnum, Strict, replay-safe specialist-agent evidence contracts. (+18 more)

### Community 30 - "README.md"
Cohesion: 0.17
Nodes (7): Model registry and promotion contract, Phase 5 development layer, Quant model training, Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.11
Nodes (33): datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool, fact_name(), FeatureValue (+25 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.12
Nodes (13): DecisionCycle, OutcomeCount, BaseModel, Auditable classifications emitted by the existing decision boundaries., RuntimeRunSummary, RuntimeStatus, JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe. (+5 more)

### Community 34 - "execution_boundary/__init__.py"
Cohesion: 0.06
Nodes (71): ContinuityStatus, execution_result_to_runtime_event(), Convert actionable execution feedback; local NO_ACTION stays local., Deterministic entry execution boundary downstream of financial Risk., Connection, Path, Append-only SQLite execution ledger and recovery anchors., Durable projection reconstructed only from immutable transitions. (+63 more)

### Community 35 - "reduce_state"
Cohesion: 0.14
Nodes (33): initial_runtime_state(), datetime, Apply one causally available event without consulting a wall clock., Construct a canonical state with explicit unknown component values., reduce_state(), test_snapshot_creates_canonical_events_and_reduces_through_shared_path(), FakeRunner, account() (+25 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "attribution.py"
Cohesion: 0.22
Nodes (16): _anomaly(), _enum_value(), _identity_context(), OutcomeAttributionBuilder, _progressed_to(), _provenance(), Any, Exact-link deterministic reconstruction of normalized Phase 8 experiences. (+8 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.08
Nodes (26): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+18 more)

### Community 39 - "versioning.py"
Cohesion: 0.05
Nodes (69): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, ProposalEvaluationResult, Append-only persistence for preregistered proposal evaluations., CanonicalMetricSamplesAdapter (+61 more)

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
Cohesion: 0.05
Nodes (91): CandidateReplayEngine, CandidateReplayEngineOutput, ControlledReplayFixtureEngine, Protocol, Allowlisted deterministic engine for controlled candidate replay fixtures., Replay a tiny canonical observation stream without external side effects., EvaluationCandidateSpec, MetricScope (+83 more)

### Community 45 - "SQLitePairedEvaluationStore"
Cohesion: 0.13
Nodes (18): PairedEvaluationAudit, PairedEvaluationRequest, PairedEvaluationResult, PairedEvaluationOutput, CanonicalPairedEvaluationAdapter, execute_paired_evaluation(), PairedEvaluationAdapter, PairedEvaluationServiceOutcome (+10 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.28
Nodes (21): ChartAgent, _input(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure(), test_chart_agent_represents_hierarchical_mtf_conflict_as_uncertainty() (+13 more)

### Community 49 - "SQLitePositionActionTransportLedger"
Cohesion: 0.23
Nodes (7): Path, Append-only SQLite ledger for position-action transport outcomes., SQLitePositionActionTransportLedger, PositionActionTransportTransition, PositionActionTransportTransitionType, BaseModel, StrEnum

### Community 50 - "ReplayExecutionBook"
Cohesion: 0.19
Nodes (9): PendingReplayEntry, A causal fill book; it contains no signal or policy decisions., ReplayBar, ReplayExecutionBook, ReplayPosition, _bar(), test_entry_executes_at_next_m5_open_and_cannot_stop_on_fill_bar(), test_modified_stop_never_retroactively_triggers_in_modification_bar() (+1 more)

### Community 51 - "paired_evaluation_contracts.py"
Cohesion: 0.16
Nodes (31): compare_paired_evidence(), canonical_decimal(), PairedCriterionOutcome, PairedCriterionStatus, PairedEvaluationAdapterKind, PairedEvaluationStatus, PairedMetricComparison, PairedMetricStatus (+23 more)

### Community 52 - "SQLitePairedEvaluationReviewStore"
Cohesion: 0.21
Nodes (13): _emit(), handle_paired_evaluation_review_command(), _history(), Namespace, CLI handlers for append-only operator review of paired evidence., _record(), _show(), _summary() (+5 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.09
Nodes (57): EntryContextProvider, PositionActionContextProvider, PositionContextProvider, MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy (+49 more)

### Community 55 - "persisted_review_fixture"
Cohesion: 0.19
Nodes (13): PairedEvaluationReviewDecision, StrEnum, Evidence-only decisions available to an operator., persisted_review_fixture(), test_cli_record_show_history_and_summary(), test_review_cli_exposes_no_final_oos_or_execution_option(), _review(), test_review_identity_is_content_addressed_and_support_ids_are_normalized() (+5 more)

### Community 68 - "Signal"
Cohesion: 0.10
Nodes (73): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+65 more)

### Community 69 - "runner.py"
Cohesion: 0.09
Nodes (39): Device, file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic() (+31 more)

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
Cohesion: 0.10
Nodes (21): calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext, RiskLimits, veto_reasons(), AgentPrediction, ExecutionInstruction (+13 more)

### Community 74 - "test_execution_boundary.py"
Cohesion: 0.20
Nodes (28): RuntimeError, Submission may have reached the broker and requires reconciliation., UnknownSubmissionState, _adapter(), _intent(), _observation(), _policy(), Exception (+20 more)

### Community 75 - "PositionActionIntent"
Cohesion: 0.17
Nodes (8): MT5PositionActionAdapter, Idempotently translate an already-safe position action to exact MT5 calls., PositionActionAdapter, PositionActionIntent, InMemoryPositionActionTransportLedger, PositionActionTransportLedger, PositionActionTransportResult, Protocol

### Community 76 - "policies.py"
Cohesion: 0.16
Nodes (30): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion., SpecialistContribution (+22 more)

### Community 77 - "snapshot.py"
Cohesion: 0.21
Nodes (20): BrokerObjectKind, MT5PersistedIntentLink, MT5SnapshotError, A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider, _optional_float() (+12 more)

### Community 79 - "default_registry"
Cohesion: 0.12
Nodes (19): multi_timeframe_features(), Any, DataFrame, fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., default_registry() (+11 more)

### Community 80 - "preflight.py"
Cohesion: 0.23
Nodes (17): The transport failed before submission could be accepted., TransportFailure, _account_mode(), _float_value(), _int_value(), MT5EntryPreflight, _positive_float(), datetime (+9 more)

### Community 81 - "replay_validation/__init__.py"
Cohesion: 0.28
Nodes (13): StrEnum, ReplayClosedTrade, ReplayFill, ReplaySide, Deterministic system-replay validation support., BaseModel, Durable content-addressed facts emitted by the deterministic replay transport., ReplayActionApplication (+5 more)

### Community 82 - "reflection/__init__.py"
Cohesion: 0.14
Nodes (49): AcceptanceCriterion, CandidateKind, CriterionComparator, CriterionOutcome, CriterionOutcomeStatus, CriterionRole, EvaluationAggregateOutcome, FinalOOSPolicy (+41 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "ensure_utc"
Cohesion: 0.17
Nodes (10): ensure_utc(), datetime, Protocol, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Clock contract used outside the pure reducer., Return the current instant in UTC., Live clock backed by the host system clock. (+2 more)

### Community 85 - "position_actions/evaluator.py"
Cohesion: 0.19
Nodes (27): PositionActionContext, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, PositionActionType, BaseModel (+19 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "ExecutionIntent"
Cohesion: 0.14
Nodes (24): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, ExecutionTransport, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics., Process one immutable intent idempotently. (+16 more)

### Community 88 - "trainer.py"
Cohesion: 0.06
Nodes (49): Architecture, CalibrationConfig, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel, Path (+41 more)

### Community 89 - "test_agent_tools.py"
Cohesion: 0.15
Nodes (23): _catalog(), FeatureFactTool, PredictiveModelEvidenceProvider, Protocol, _ExplodingTool, _FailingProvider, _freshness(), _input() (+15 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "experience/__init__.py"
Cohesion: 0.15
Nodes (26): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+18 more)

### Community 92 - "persisted_paired_fixture"
Cohesion: 0.24
Nodes (7): persisted_paired_fixture(), test_cli_has_no_final_oos_input_option(), test_cli_run_show_summary_and_idempotent_reuse(), CountingAdapter, test_completed_retry_reuses_result_and_audit_without_recomparison(), test_store_is_append_only_and_exact_linked(), test_store_rejects_missing_authoritative_config()

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

### Community 97 - "candles"
Cohesion: 0.17
Nodes (8): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., candles(), DataTests, FeatureTests, DataFrame

### Community 98 - "SQLiteImprovementProposalStore"
Cohesion: 0.09
Nodes (55): _build(), _emit(), handle_proposal_command(), _history(), _latest(), _policy(), Any, Namespace (+47 more)

### Community 99 - "SnapshotGateway"
Cohesion: 0.15
Nodes (7): _provider(), SnapshotGateway, test_disconnected_terminal_returns_structured_snapshot_failure(), test_snapshot_does_not_mutate_shared_state_or_call_broker_transport(), test_snapshot_exact_persisted_ticket_link_rebinds_to_canonical_object(), test_snapshot_linkage_never_fuzzy_matches_missing_ticket(), test_snapshot_maps_account_market_books_exposure_and_constraints()

### Community 101 - "Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design"
Cohesion: 0.13
Nodes (14): Append-only persistence and supersession, Architecture, Baseline validation, CLI, Exact provenance validation, ISO-week boundary and availability, Knowledge-status lifecycle, Pattern generation (+6 more)

### Community 102 - "Phase 7 Task 7: Position Action Safety and Journal Plan"
Cohesion: 0.25
Nodes (7): Contract design, Documentation and graph, Journal integration, Phase 7 Task 7: Position Action Safety and Journal Plan, Pure evaluator, Scope, Test-first sequence

### Community 103 - "MT5Gateway"
Cohesion: 0.08
Nodes (18): MT5Gateway, MT5SymbolMapping, BaseModel, Protocol, _float_value(), _int_value(), MT5ExecutionAdapter, MT5ExecutionTransport (+10 more)

### Community 104 - "PositionGateway"
Cohesion: 0.16
Nodes (13): _adapter(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send(), test_modify_stop_preserves_ticket_tp_and_cannot_increase_exposure() (+5 more)

### Community 105 - "position.py"
Cohesion: 0.33
Nodes (9): _float_value(), _int_value(), _optional_close(), _optional_price(), _positive_int(), Demo-only MetaTrader 5 transport for Task 7 position-action intents., _required_positive(), _truthy() (+1 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "ExperienceType"
Cohesion: 0.15
Nodes (16): AttributionSources, _deduplicate(), ExperienceBuild, _index(), BaseModel, Connection, Experience, Path (+8 more)

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
Cohesion: 0.21
Nodes (14): build(), candles(), definition(), DataFrame, Path, RecordingTransformer, test_dataset_reproducibility_config_identity_and_separation(), test_duplicate_timestamp_rejected() (+6 more)

### Community 112 - "MasterProposal"
Cohesion: 0.22
Nodes (14): build_execution_intent(), default_execution_policy(), RiskContext, Pure construction of provenance-bound execution intents., Return the conservative, execution-disabled baseline policy., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links(), ExecutionOrderType (+6 more)

### Community 113 - "Phase 8 Task 7 Governed Candidate Replay Evaluator Design"
Cohesion: 0.22
Nodes (8): CLI, Contracts and identity, Controlled replay engine, Exact linkage and Final OOS boundary, Persistence, service, and reuse, Phase 8 Task 7 Governed Candidate Replay Evaluator Design, Scope, Validation

### Community 114 - "generate_labels"
Cohesion: 0.16
Nodes (23): dataset_quality_report(), Any, DataFrame, compare_label_definitions(), label_balance(), Any, DataFrame, Series (+15 more)

### Community 115 - "SQLiteProposalEvaluationStore"
Cohesion: 0.09
Nodes (25): Path, _build_plan(), _emit(), handle_evaluation_command(), _input(), Any, Namespace, Path (+17 more)

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
Nodes (18): ExecutionMode, _adapter(), EntryGateway, _intent(), _policy(), datetime, Exception, parametrize (+10 more)

### Community 121 - "Global constraints"
Cohesion: 0.25
Nodes (7): Global constraints, Phase 7 Task 8 Direct MT5 Transport Implementation Plan, Task 1: Gateway and normalized MT5 contracts, Task 2: Canonical broker snapshots, Task 3: Entry transport and complete dry-run preflight, Task 4: Durable position-action transport, Task 5: Documentation, optional read-only smoke, and final verification

### Community 122 - "inference.py"
Cohesion: 0.10
Nodes (29): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., dump_artifact(), file_hash(), load_artifact(), Any (+21 more)

### Community 123 - "test_evaluation_execution_adapter.py"
Cohesion: 0.61
Nodes (8): _artifacts(), _metric(), _plan(), _request(), test_adapter_computes_only_closed_preregistered_aggregations(), test_adapter_fails_closed_for_linkage_scope_series_and_aggregation_mismatch(), test_adapter_is_byte_deterministic_under_reordered_artifacts_and_series(), test_final_oos_is_unavailable_without_an_input_artifact()

### Community 124 - "Phase 8 Task 4 Advisory Improvement Proposal Design"
Cohesion: 0.20
Nodes (9): Append-only persistence and supersession, CLI, Contracts and identity, Deterministic advisory content, Eligibility, Phase 8 Task 4 Advisory Improvement Proposal Design, Proposal lifecycle, Scope (+1 more)

### Community 125 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 6 Deterministic Evaluation Execution Adapter Implementation Plan, Task 1: Execution and unavailable-observation contracts, Task 2: Closed deterministic metric-sample adapter, Task 3: Append-only request and audit persistence, Task 4: Execution service and idempotent recovery, Task 5: CLI, documentation, and final verification

### Community 126 - "DecisionExperience"
Cohesion: 0.31
Nodes (9): DecisionExperience, _decision(), _provenance(), test_actual_trade_cannot_be_marked_simulated(), test_counterfactual_is_separate_and_requires_explicit_assumptions(), test_equivalent_decision_content_has_deterministic_identity(), test_experience_rejects_naive_timestamp(), test_trade_preserves_none_separately_from_numeric_zero() (+1 more)

### Community 127 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 3 Weekly Reflection and Pattern Lifecycle Implementation Plan, Task 1: Weekly contracts and semantic identities, Task 2: Pure weekly aggregation and exact provenance, Task 3: Append-only weekly and lifecycle persistence, Task 4: Weekly CLI integration, Task 5: Corrected one-month baseline and durable context

### Community 128 - "DatasetManifest"
Cohesion: 0.25
Nodes (4): DatasetManifest, BaseModel, Path, PersistenceAndConfigTests

### Community 129 - "Deterministic Evaluation Execution"
Cohesion: 0.33
Nodes (5): Controlled CLI workflow, Deterministic Evaluation Execution, Identity and inputs, Persistence and retry, Protected Final OOS

### Community 130 - "ReplayOutcomeArtifact"
Cohesion: 0.24
Nodes (7): model_validator, Path, ReplayOutcomeArtifact, _outcomes(), _artifact(), test_replay_outcome_artifact_is_deterministic_and_serializable(), test_trade_preserves_exact_close_action_and_none_vs_zero()

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
Cohesion: 0.10
Nodes (31): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., chronological_split(), IndexRange (+23 more)

### Community 139 - "mt5/__init__.py"
Cohesion: 0.19
Nodes (11): MT5ConnectionError, MT5Constants, RuntimeError, Narrow contracts isolating the optional MetaTrader5 package., The terminal package or connected terminal is unavailable., _load_mt5(), Lazy concrete wrapper around the Windows-only MetaTrader5 package., Optional, demo-safe MetaTrader5 gateway and adapters. (+3 more)

### Community 141 - "system.py"
Cohesion: 0.10
Nodes (31): Strict orchestration-only contracts for the shared Phase 7 runtime., EntryDecisionInputs, BaseModel, Concrete composition of existing deterministic Phase 7 decision boundaries., Causal contexts supplied by the runtime-specific context adapter., _event(), _fresh(), Any (+23 more)

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

### Community 146 - "run_system_replay"
Cohesion: 0.28
Nodes (12): main(), Command-line entry point for Phase 7 system replay and result display., compare_replays(), _counts(), _file_sha256(), load_replay_frame(), _merge_htf_bias(), DataFrame (+4 more)

### Community 148 - "MetaTrader5Gateway"
Cohesion: 0.25
Nodes (4): _mapping(), _mappings(), MetaTrader5Gateway, Operational gateway; paths and process state are never semantic identity.

### Community 150 - "execution.py"
Cohesion: 0.22
Nodes (6): _identity(), _PendingClose, _PendingStop, datetime, Deterministic, transport-only fill mechanics for system replay., ReplayBarResult

### Community 151 - "Phase 8 Task 9 Deterministic Paired Evaluation Design"
Cohesion: 0.25
Nodes (7): CLI and controlled validation, Contracts, Explicit exclusions, Persistence and idempotency, Phase 8 Task 9 Deterministic Paired Evaluation Design, Purpose and boundary, Validation and comparison flow

### Community 153 - "Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design"
Cohesion: 0.17
Nodes (11): Append-only persistence, Candidate contract, CLI, Evaluation result, Identity and serialization, Operator decision boundary, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design, Preregistered plan (+3 more)

### Community 155 - "test_paired_evaluation_contracts.py"
Cohesion: 0.18
Nodes (10): PairedArtifactRef, model_validator, _artifact(), _manifest(), datetime, _request(), test_metric_comparison_requires_canonical_decimal_and_consistent_availability(), test_paired_contracts_are_exported_from_reflection_package() (+2 more)

### Community 157 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Implementation Plan, Task 1: Evaluation contracts and protected-OOS invariants, Task 2: Pure preregistration and result evaluation, Task 3: Append-only evaluation persistence, Task 4: Evaluation CLI without execution, Task 5: Documentation and final verification

### Community 159 - "RuntimeEvent"
Cohesion: 0.04
Nodes (80): Collection, ScenarioTransition, Explicitly advanced deterministic replay clock., ReplayClock, BaseModel, RuntimeEvent, JournalEntry, JournalOutcome (+72 more)

### Community 160 - "LocalModelRegistry"
Cohesion: 0.38
Nodes (5): LocalModelRegistry, Any, BaseModel, Path, RegistryEntry

### Community 161 - "paired_evaluation_cli.py"
Cohesion: 0.53
Nodes (8): _artifacts(), _emit(), handle_paired_evaluation_command(), Namespace, CLI handlers for deterministic paired baseline/candidate comparison., _run(), _show(), _summary()

### Community 162 - "canonical_hash"
Cohesion: 0.13
Nodes (6): model_validator, model_validator, model_validator, model_validator, canonical_hash(), Any

### Community 163 - "Proposal Evaluation"
Cohesion: 0.40
Nodes (4): CLI workflow, Governance boundary, Persistence and corrections, Proposal Evaluation

### Community 167 - "test_feature_formulas.py"
Cohesion: 0.23
Nodes (11): skipif, money_flow_index(), Any, DataFrame, volume_features(), fixture(), DataFrame, test_bollinger_population_std_and_realized_volatility() (+3 more)

### Community 168 - "Phase 8 Task 10 Governed Operator Review Bridge Design"
Cohesion: 0.33
Nodes (5): Contract, Linear-chain persistence, Phase 8 Task 10 Governed Operator Review Bridge Design, Safety boundary, Scope

### Community 169 - "Phase 3 label contract"
Cohesion: 0.40
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 172 - "Deterministic paired baseline-vs-candidate comparison"
Cohesion: 0.40
Nodes (4): Commands, Deterministic paired baseline-vs-candidate comparison, Governance, Persistence and retry behavior

### Community 173 - "test_experience_analytics_cli.py"
Cohesion: 0.80
Nodes (4): _rejection(), test_show_and_summary_cli_emit_json(), test_summary_is_descriptive_and_preserves_unknowns(), _trade()

### Community 175 - "Governed paired-evaluation review"
Cohesion: 0.50
Nodes (3): Commands, Governed paired-evaluation review, Identity and history

### Community 176 - "Phase 8 Task 10 Governed Operator Review Bridge Implementation Plan"
Cohesion: 0.50
Nodes (3): Constraints, Phase 8 Task 10 Governed Operator Review Bridge Implementation Plan, Test-first slices

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

### Community 194 - "price_action_features"
Cohesion: 0.50
Nodes (3): price_action_features(), Any, DataFrame

### Community 195 - "SharedKernelPolicySet"
Cohesion: 0.29
Nodes (5): BaseModel, model_validator, Complete reviewed policy composition for one shared-kernel replay., Return a new set with only the reviewed Master-fusion policy replaced., SharedKernelPolicySet

## Knowledge Gaps
- **376 isolated node(s):** `adaptive-xauusd-trader`, `Repository-start workflow`, `Graphify`, `Current capabilities`, `Setup (Windows PowerShell)` (+371 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1099 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `DatasetManifest`, `LabelDefinition`, `ReplayOutcomeArtifact`, `agents/__init__.py`, `development/config.py`, `folds.py`, `mt5/__init__.py`, `SQLiteCandidateReplayStore`, `system.py`, `model_validator`, `run_system_replay`, `model_validator`, `model_validator`, `datasets/builder.py`, `execution.py`, `ReflectionModel`, `.validate_and_bind_identity`, `dataset.py`, `runtime/__init__.py`, `_deterministic.py`, `test_paired_evaluation_contracts.py`, `.normalize_and_bind_identity`, `model_validator`, `RuntimeEvent`, `execution_boundary/__init__.py`, `ToolResult`, `attribution.py`, `.normalize_validate_and_bind_identity`, `versioning.py`, `.normalize_validate_and_bind_identity`, `.bind_identity`, `SQLiteExperienceStore`, `MetricScope`, `SQLitePairedEvaluationStore`, `model_validator`, `.validate_and_bind_identity`, `paired_evaluation_contracts.py`, `.validate_and_bind_identity`, `SQLitePairedEvaluationReviewStore`, `_context`, `.validate_event`, `.validate_and_bind_identity`, `model_validator`, `.bind_identity`, `.validate_and_bind_identity`, `SharedKernelPolicySet`, `Signal`, `policies.py`, `.validate_and_bind_identity`, `replay_validation/__init__.py`, `reflection/__init__.py`, `ExecutionIntent`, `trainer.py`, `experience/__init__.py`, `SQLiteImprovementProposalStore`, `model_validator`, `SQLiteProposalEvaluationStore`, `inference.py`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `ReflectionPolicy`, `test_reflection_cli.py`, `timedelta`, `test_runtime_orchestration.py`, `system.py`, `run_system_replay`, `_context`, `ReflectionModel`, `runtime/__init__.py`, `test_risk_boundary.py`, `execution_boundary/__init__.py`, `attribution.py`, `SQLiteExperienceStore`, `test_experience_analytics_cli.py`, `_context`, `schemas.py`, `test_execution_boundary.py`, `policies.py`, `preflight.py`, `position_actions/evaluator.py`, `ExecutionIntent`, `experience/__init__.py`, `SQLiteImprovementProposalStore`, `test_daily_reflection.py`, `MasterProposal`, `EntryGateway`, `inference.py`, `DecisionExperience`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `default_registry()` connect `default_registry` to `candles`, `price_action_features`, `axq/features/registry.py`, `indicators.py`, `test_feature_formulas.py`, `axq/config.py`, `session_features`, `system.py`, `breakout_features`, `run_system_replay`, `datasets/builder.py`, `test_agent_tools.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 216 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 216 INFERRED edges - model-reasoned connections that need verification._
- **Are the 83 inferred relationships involving `MetricScope` (e.g. with `_fixture()` and `_run()`) actually correct?**
  _`MetricScope` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 70 INFERRED edges - model-reasoned connections that need verification._