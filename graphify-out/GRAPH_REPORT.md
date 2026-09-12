# Graph Report - phase-9-llm-reasoning  (2026-09-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 4393 nodes · 14558 edges · 209 communities (166 shown, 40 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 2479 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f7f9a62e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- daily.py
- LabelDefinition
- reflection/__main__.py
- default_registry
- _source_stores
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
- .__init__
- System architecture (Phase 0-7 baseline)
- SQLiteWeeklyReflectionStore
- reasoning/__init__.py
- runtime/__init__.py
- Architecture decision log
- kernel.py
- README.md
- test_risk_boundary.py
- ToolResult
- RuntimeOrchestrator
- SQLiteExecutionLedger
- initial_runtime_state
- Global Constraints
- processor.py
- Phase 0-6 runbook
- persist_controlled_plan
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- MetricScope
- timedelta
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- test_evidence_kernel.py
- proposals.py
- execution.py
- reflection/__init__.py
- SQLitePairedEvaluationReviewStore
- Repository instructions
- _context
- SQLiteRuntimeJournal
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
- position.py
- policies.py
- snapshot.py
- request_envelope
- features/preprocessing.py
- preflight.py
- replay_validation/__init__.py
- ReflectionModel
- Global Constraints
- replay.py
- position_actions/evaluator.py
- Global Constraints
- ExecutionIntent
- quant/config.py
- test_agent_tools.py
- Phase 7 deterministic runtime orchestration
- attribution.py
- RuntimeEvent
- Global Constraints
- FakeMT5Module
- evidence
- features/analysis.py
- test_foundation.py
- proposal_cli.py
- SnapshotGateway
- model_validator
- Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design
- Phase 7 Task 7: Position Action Safety and Journal Plan
- MT5Gateway
- PositionGateway
- execution_boundary/__init__.py
- Position action safety
- dataset.py
- session_features
- ExperienceProvenance
- evaluate_predictions
- test_datasets_phase3.py
- entry.py
- Phase 8 Task 7 Governed Candidate Replay Evaluator Design
- reasoning/contracts.py
- SQLiteProposalEvaluationStore
- Global Constraints
- Phase 8 Task 6 Deterministic Evaluation Execution Adapter Design
- Phase 8 Task 1 Experience Store Design
- Phase 7 Task 8 Direct MT5 Transport Design
- EntryGateway
- Global constraints
- trainer.py
- test_weekly_reflection.py
- Phase 8 Task 4 Advisory Improvement Proposal Design
- Global Constraints
- Signal
- Global Constraints
- DatasetManifest
- Deterministic Evaluation Execution
- OperatorControls
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
- MasterProposal
- Deterministic Weekly Reflection and Pattern Lifecycle
- Advisory Improvement Proposals
- Global Constraints
- default_shared_kernel_policy_set
- system.py
- model_validator
- MetaTrader5Gateway
- canonical_hash
- weekly_contracts.py
- Phase 8 Task 9 Deterministic Paired Evaluation Design
- _MT5Module
- Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design
- SQLiteReasoningAuditStore
- _context
- position_management/contracts.py
- Global Constraints
- Phase 9 Task 1 LLM Provider and Structured Reasoning Boundary Design
- test_ollama_provider.py
- LocalModelRegistry
- cli.py
- model_validator
- Proposal Evaluation
- main
- .normalize_validate_and_bind_identity
- model_validator
- model_validator
- Phase 8 Task 10 Governed Operator Review Bridge Design
- Phase 3 label contract
- Operator-authorized proposal lifecycle bridge
- model_validator
- Deterministic paired baseline-vs-candidate comparison
- model_validator
- .bind_identity
- Governed paired-evaluation review
- Phase 8 Task 10 Governed Operator Review Bridge Implementation Plan
- SemanticTraceStep
- generate_labels
- SQLitePositionActionTransportLedger
- .validate_and_bind_identity
- test_reasoning_service.py
- Global Constraints
- Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design
- model_validator
- .bind_identity
- Shared-Kernel Candidate Driver V1
- .validate_and_bind_identity
- utc
- orchestration/contracts.py
- test_quant_development_runner.py
- test_reasoning_boundaries.py
- File Structure
- .bind_identity
- model_validator
- Offline LLM reasoning boundary
- RuntimeConfig
- model_validator
- paired_evaluation_review_cli.py
- InMemoryExecutionLedger
- model_validator
- model_validator
- FakeRunner
- FakeGateway
- .terminal_path
- .normalize_and_bind_identity
- .validate_and_bind_identity

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 218 edges
2. `MetricScope` - 107 edges
3. `Signal` - 92 edges
4. `RuntimeEvent` - 92 edges
5. `SQLiteProposalEvaluationStore` - 76 edges
6. `ReflectionModel` - 74 edges
7. `SQLiteImprovementProposalStore` - 67 edges
8. `ExecutionIntent` - 64 edges
9. `SQLiteReasoningAuditStore` - 60 edges
10. `CanonicalMetricSampleArtifact` - 60 edges

## Surprising Connections (you probably didn't know these)
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py
- `test_system_replay_retains_exact_attribution_journal_semantics()` --uses--> `JournalRecordType`  [INFERRED]
  tests/test_system_replay.py → src/axq/runtime/journal.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_walk_forward_split_definitions_are_deterministic()` --calls--> `walk_forward_splits()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py

## Import Cycles
- None detected.

## Communities (209 total, 40 thin omitted)

### Community 0 - "daily.py"
Cohesion: 0.35
Nodes (20): FindingCategory, FindingSignal, StrEnum, ReflectionFinding, SampleGuardRecord, SampleGuardStatus, _agent_findings(), _average() (+12 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.15
Nodes (28): BarrierMode, CollisionPolicy, EntryReference, LabelDefinition, LabelKind, BaseModel, model_validator, StrEnum (+20 more)

### Community 2 - "reflection/__main__.py"
Cohesion: 0.07
Nodes (44): Any, register_candidate_replay_commands(), DailyReflection, ReflectionPolicy, Any, register_evaluation_commands(), Any, register_execution_commands() (+36 more)

### Community 3 - "default_registry"
Cohesion: 0.07
Nodes (33): Compatibility entry point; implementation lives in the installable axq package., breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars., Feature functions and registry., FeatureManifestEntry, BaseModel (+25 more)

### Community 4 - "_source_stores"
Cohesion: 0.24
Nodes (12): MetricFact, _build_args(), Path, _source_stores(), test_proposal_cli_builds_reuses_shows_and_summarizes(), test_proposal_cli_requires_explicit_transition_and_shows_history(), _finding(), _guard() (+4 more)

### Community 5 - "indicators.py"
Cohesion: 0.11
Nodes (43): skipif, aroon(), atr(), cci(), directional_movement(), money_flow_index(), DataFrame, Series (+35 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.08
Nodes (56): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+48 more)

### Community 7 - "update_scenario"
Cohesion: 0.25
Nodes (28): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), _agent_pair(), _create(), _event(), _market(), datetime, parametrize (+20 more)

### Community 8 - "development/config.py"
Cohesion: 0.08
Nodes (42): Architecture, StrEnum, AblationConfig, EvaluationConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+34 more)

### Community 9 - "axq/config.py"
Cohesion: 0.11
Nodes (25): CompletedProcess, main(), HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel (+17 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.16
Nodes (25): DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., FakeEntryAdapter, FakePositionActionAdapter, FakeProcessor, _fresh(), _intent(), _market_event() (+17 more)

### Community 11 - "ProposalEvaluationPlan"
Cohesion: 0.06
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
Cohesion: 0.33
Nodes (13): _categorical_distribution(), distribution_drift(), feature_drift_report(), _finite(), ks_statistic(), psi(), Any, DataFrame (+5 more)

### Community 22 - "datasets/builder.py"
Cohesion: 0.10
Nodes (31): main(), main(), DataFrame, Leakage-safe multi-timeframe alignment., Attach bars only when their UTC close time is at/before the base bar's UTC…, synchronize_completed_bars(), timeframe_delta(), DataFrame (+23 more)

### Community 23 - ".__init__"
Cohesion: 0.18
Nodes (5): BrokerSnapshotProvider, DecisionCycleProcessor, datetime, Protocol, RuntimeRunner

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.10
Nodes (20): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Phase 8 governed comparison boundary (+12 more)

### Community 25 - "SQLiteWeeklyReflectionStore"
Cohesion: 0.13
Nodes (31): _build(), _emit(), handle_weekly_command(), _history(), _latest(), _policy(), date, Namespace (+23 more)

### Community 26 - "reasoning/__init__.py"
Cohesion: 0.07
Nodes (47): NamedTuple, LLMAttemptStatus, LLMFailureCode, ProviderModelIdentity, Offline structured reasoning contracts., _bounded_body(), _json_object(), OllamaHTTPTransport (+39 more)

### Community 27 - "runtime/__init__.py"
Cohesion: 0.10
Nodes (44): Bridge typed execution results into the shared Phase 6 runtime path., StrEnum, Canonical runtime event envelopes for live and deterministic replay., RuntimeEventType, Versioned contracts and deterministic reduction for live and replay., Reduce a non-decision state refresh without invoking specialists., _account_update(), datetime (+36 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.05
Nodes (41): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+33 more)

### Community 29 - "kernel.py"
Cohesion: 0.20
Nodes (19): Deterministic hierarchical market-structure interpretation., AgentStatus, DirectionalBias, fact_map(), Interpretation, numeric(), ObservedFact, FactScalar (+11 more)

### Community 30 - "README.md"
Cohesion: 0.17
Nodes (7): Model registry and promotion contract, Phase 5 development layer, Quant model training, Ordered local run plan, Phase 5 local Quant experiment workflow, Returning results for review, Quant Agent contract

### Community 31 - "test_risk_boundary.py"
Cohesion: 0.16
Nodes (42): default_demo_risk_policy(), Return conservative Demo safety defaults, not optimized trading truth., _account(), _broker(), _context(), _discipline(), _evaluate(), _exposure() (+34 more)

### Community 32 - "ToolResult"
Cohesion: 0.09
Nodes (39): FreshnessStatus, FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool, ToolCatalog, AnalyticalTool (+31 more)

### Community 33 - "RuntimeOrchestrator"
Cohesion: 0.17
Nodes (5): JournalSemantic, Lift an entry pause only while all non-bypassable gates remain safe., Perform at most one read-only refresh when the bounded cadence elapsed., Own ordering and gates while delegating every trading semantic decision., RuntimeOrchestrator

### Community 34 - "SQLiteExecutionLedger"
Cohesion: 0.13
Nodes (26): Connection, Path, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, datetime, reconcile_execution_state(), _intent(), _link() (+18 more)

### Community 35 - "initial_runtime_state"
Cohesion: 0.20
Nodes (29): initial_runtime_state(), Construct a canonical state with explicit unknown component values., test_snapshot_creates_canonical_events_and_reduces_through_shared_path(), account(), apply(), event(), feedback(), fresh() (+21 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "processor.py"
Cohesion: 0.17
Nodes (26): EntryContextProvider, PositionActionContextProvider, PositionContextProvider, DisciplineContext, DisciplineCounters, DisciplineModel, DisciplinePolicy, DisciplinePosition (+18 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.07
Nodes (28): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+20 more)

### Community 39 - "persist_controlled_plan"
Cohesion: 0.07
Nodes (55): CanonicalMetricSamplesAdapter, input_artifact_ref(), Aggregate exact preregistered metric series without executing candidate code., _artifact(), _emit(), handle_execution_command(), Namespace, Path (+47 more)

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
Nodes (74): CandidateKind, MetricScope, SemanticArtifactRef, canonical_record_bytes(), BaseModel, ProposalTargetComponent, _emit(), handle_shared_kernel_candidate_command() (+66 more)

### Community 45 - "timedelta"
Cohesion: 0.10
Nodes (44): build_evaluation_plan(), UTCDateTime, Preregister a frozen plan without executing its evaluator., ImprovementProposal, ImprovementProposalPolicy, ProposalEvidenceGuard, ProposalGuardKind, ProposalStatus (+36 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.26
Nodes (22): ChartAgent, _input(), _kernel_fixture(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure() (+14 more)

### Community 49 - "proposals.py"
Cohesion: 0.13
Nodes (22): build_improvement_proposals(), _content(), _index_unique(), ProposalBuildResult, ProposalEligibilityAssessment, Experience, Pattern, T (+14 more)

### Community 50 - "execution.py"
Cohesion: 0.11
Nodes (15): _identity(), _PendingClose, PendingReplayEntry, _PendingStop, datetime, Deterministic, transport-only fill mechanics for system replay., A causal fill book; it contains no signal or policy decisions., ReplayBar (+7 more)

### Community 51 - "reflection/__init__.py"
Cohesion: 0.06
Nodes (83): CanonicalMetricSampleArtifact, Deterministic Phase 8 reflection contracts and services., _artifact_matches(), _artifacts(), _emit(), handle_paired_evaluation_command(), Namespace, CLI handlers for deterministic paired baseline/candidate comparison. (+75 more)

### Community 52 - "SQLitePairedEvaluationReviewStore"
Cohesion: 0.08
Nodes (33): PairedEvaluationReview, One immutable node in a paired-result review chain., Persist and replay one strict linear review chain per paired result., SQLitePairedEvaluationReviewStore, _emit(), handle_proposal_transition_authorization_command(), _history(), Namespace (+25 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.17
Nodes (36): default_demo_position_management_policy(), evaluate_position(), Return conservative deterministic demo defaults, not optimized strategy truth., Evaluate one open position without mutating state or invoking execution…, _broker_constraints(), _context(), _fresh(), _intent() (+28 more)

### Community 55 - "SQLiteRuntimeJournal"
Cohesion: 0.10
Nodes (21): JournalEntry, Connection, JournalSemantic, Path, Protocol, UTCDateTime, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history. (+13 more)

### Community 68 - "evaluate_discipline"
Cohesion: 0.26
Nodes (34): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., _context(), _policy(), _proposal(), parametrize (+26 more)

### Community 69 - "runner.py"
Cohesion: 0.09
Nodes (38): Device, file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic() (+30 more)

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
Cohesion: 0.08
Nodes (27): load_artifact_json(), load_manifest(), Any, datetime, ndarray, Path, Series, QuantAgent (+19 more)

### Community 74 - "test_execution_boundary.py"
Cohesion: 0.20
Nodes (30): default_execution_policy(), Return the conservative, execution-disabled baseline policy., _adapter(), _intent(), _observation(), _policy(), _proposal(), parametrize (+22 more)

### Community 75 - "position.py"
Cohesion: 0.11
Nodes (22): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), Demo-only MetaTrader 5 transport for Task 7 position-action intents., Idempotently translate an already-safe position action to exact MT5 calls. (+14 more)

### Community 76 - "policies.py"
Cohesion: 0.16
Nodes (30): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion., SpecialistContribution (+22 more)

### Community 77 - "snapshot.py"
Cohesion: 0.19
Nodes (22): BrokerObjectKind, MT5PersistedIntentLink, MT5SnapshotError, Narrow contracts isolating the optional MetaTrader5 package., A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider (+14 more)

### Community 78 - "request_envelope"
Cohesion: 0.10
Nodes (51): BoundedReasoningContextItem, ReasoningSourceReference, ReflectionExplanation, context_item(), generation_policy(), prompt_identity(), datetime, Deterministic fixtures for Phase 9 reasoning tests. (+43 more)

### Community 79 - "features/preprocessing.py"
Cohesion: 0.38
Nodes (5): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., test_scaler_fit_boundary_scaffolding()

### Community 80 - "preflight.py"
Cohesion: 0.16
Nodes (22): The transport failed before submission could be accepted., TransportFailure, datetime, _account_mode(), default_mt5_transport_config(), _float_value(), _int_value(), MT5EntryPreflight (+14 more)

### Community 81 - "replay_validation/__init__.py"
Cohesion: 0.17
Nodes (20): StrEnum, ReplayClosedTrade, ReplayFill, ReplaySide, Deterministic system-replay validation support., BaseModel, model_validator, Path (+12 more)

### Community 82 - "ReflectionModel"
Cohesion: 0.08
Nodes (57): Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, Append-only persistence for governed candidate replay evaluation., BaseModel, Immutable content-addressed contracts for deterministic daily reflection., ReflectionModel, AcceptanceCriterion, CriterionComparator, CriterionOutcome (+49 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "replay.py"
Cohesion: 0.05
Nodes (56): Collection, ScenarioTransition, ensure_utc(), datetime, Protocol, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Clock contract used outside the pure reducer. (+48 more)

### Community 85 - "position_actions/evaluator.py"
Cohesion: 0.19
Nodes (28): PositionActionContext, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, PositionActionType, BaseModel (+20 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "ExecutionIntent"
Cohesion: 0.14
Nodes (23): DemoExecutionAdapter, ExecutionAdapter, ExecutionLedger, datetime, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics., Process one immutable intent idempotently., Guarded demo adapter; never permits a live-account submission. (+15 more)

### Community 88 - "quant/config.py"
Cohesion: 0.11
Nodes (26): CalibrationConfig, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel, Path, QuantTrainingConfig (+18 more)

### Community 89 - "test_agent_tools.py"
Cohesion: 0.17
Nodes (21): PredictiveModelEvidenceProvider, Protocol, _ExplodingTool, _FailingProvider, _freshness(), _input(), Any, datetime (+13 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "attribution.py"
Cohesion: 0.08
Nodes (61): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+53 more)

### Community 92 - "RuntimeEvent"
Cohesion: 0.09
Nodes (32): Compose existing pure functions; adapters provide causal context only., BaseModel, datetime, RuntimeEvent, EventSource, InMemoryEventSource, Protocol, Deterministically ordered runtime-event sources. (+24 more)

### Community 93 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 7 Task 6 Deterministic Position Management Implementation Plan, Task 1: Strict position-management contracts, Task 2: Fail-closed evaluation and lifecycle semantics, Task 3: Purity, parity, and forbidden-authority tests, Task 4: Documentation and final validation

### Community 94 - "FakeMT5Module"
Cohesion: 0.13
Nodes (5): FakeMT5Module, test_gateway_initialization_failure_is_structured(), test_gateway_is_lazy_and_normalizes_external_named_tuples(), test_gateway_normalizes_check_send_and_constants(), test_gateway_passes_operational_terminal_path_without_semantic_identity()

### Community 95 - "evidence"
Cohesion: 0.22
Nodes (18): evidence(), datetime, parametrize, test_abstention_is_explicit_and_has_no_direction(), test_agent_evidence_has_no_execution_authorization_fields(), test_agent_evidence_identity_is_deterministic_and_round_trips(), test_agent_input_binds_tools_without_exposing_account_state(), test_agent_input_preserves_non_available_tool_semantics() (+10 more)

### Community 96 - "features/analysis.py"
Cohesion: 0.25
Nodes (17): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+9 more)

### Community 97 - "test_foundation.py"
Cohesion: 0.12
Nodes (15): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext (+7 more)

### Community 98 - "proposal_cli.py"
Cohesion: 0.26
Nodes (16): _build(), _emit(), handle_proposal_command(), _history(), _latest(), _policy(), Any, Namespace (+8 more)

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
Cohesion: 0.11
Nodes (5): MT5Gateway, Protocol, MT5ExecutionAdapter, datetime, Compose MT5 facts/transport with the existing durable demo adapter.

### Community 104 - "PositionGateway"
Cohesion: 0.15
Nodes (14): _adapter(), _constants(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send() (+6 more)

### Community 105 - "execution_boundary/__init__.py"
Cohesion: 0.08
Nodes (46): execution_result_to_runtime_event(), Convert actionable execution feedback; local NO_ACTION stays local., Deterministic entry execution boundary downstream of financial Risk., Append-only SQLite execution ledger and recovery anchors., evaluate_resume_readiness(), _is_fresh(), datetime, Protocol (+38 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "dataset.py"
Cohesion: 0.10
Nodes (21): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., FeatureManifest, Path, Canonical feature-manifest models., LabelManifest (+13 more)

### Community 108 - "session_features"
Cohesion: 0.23
Nodes (10): _local_window(), Any, DataFrame, Series, DST-aware session features. Source timestamps are interpreted as UTC., session_features(), test_london_and_new_york_dst_transitions(), test_manifest_is_reproducible_and_complete() (+2 more)

### Community 109 - "ExperienceProvenance"
Cohesion: 0.14
Nodes (21): ExperienceProvenance, model_validator, _agent(), _findings(), _management(), _provenance(), datetime, _rejection() (+13 more)

### Community 110 - "evaluate_predictions"
Cohesion: 0.08
Nodes (35): evaluate_challenger_evidence(), Any, Advisory Champion/Challenger evidence contract., calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), overfitting_report(), Any (+27 more)

### Community 111 - "test_datasets_phase3.py"
Cohesion: 0.21
Nodes (14): build(), candles(), definition(), DataFrame, Path, RecordingTransformer, test_dataset_reproducibility_config_identity_and_separation(), test_duplicate_timestamp_rejected() (+6 more)

### Community 112 - "entry.py"
Cohesion: 0.19
Nodes (13): ExecutionTransport, RuntimeError, Submission may have reached the broker and requires reconciliation., Submit an already approved intent to the execution transport., UnknownSubmissionState, BrokerExecutionReport, _float_value(), _int_value() (+5 more)

### Community 113 - "Phase 8 Task 7 Governed Candidate Replay Evaluator Design"
Cohesion: 0.22
Nodes (8): CLI, Contracts and identity, Controlled replay engine, Exact linkage and Final OOS boundary, Persistence, service, and reuse, Phase 8 Task 7 Governed Candidate Replay Evaluator Design, Scope, Validation

### Community 114 - "reasoning/contracts.py"
Cohesion: 0.10
Nodes (39): _canonical_json_bytes(), LLMFailureMetadata, LLMGenerationPolicy, LLMReusePolicy, PromptTemplateIdentity, ProviderKind, Any, BaseModel (+31 more)

### Community 115 - "SQLiteProposalEvaluationStore"
Cohesion: 0.08
Nodes (28): main(), Database, Connection, Path, Path, _build_plan(), _emit(), handle_evaluation_command() (+20 more)

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

### Community 122 - "trainer.py"
Cohesion: 0.10
Nodes (30): dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run(), write_json() (+22 more)

### Community 123 - "test_weekly_reflection.py"
Cohesion: 0.33
Nodes (11): _daily(), _experience(), _finding(), test_complete_week_builds_guarded_success_and_failure_patterns_deterministically(), test_completed_revision_supersedes_incomplete_week_without_mutating_it(), test_daily_revision_chain_selects_terminal_and_rejects_missing_or_branching_links(), test_exact_provenance_failure_and_duplicate_experience_fail_closed(), test_incomplete_week_records_five_missing_days_and_suppresses_patterns() (+3 more)

### Community 124 - "Phase 8 Task 4 Advisory Improvement Proposal Design"
Cohesion: 0.20
Nodes (9): Append-only persistence and supersession, CLI, Contracts and identity, Deterministic advisory content, Eligibility, Phase 8 Task 4 Advisory Improvement Proposal Design, Proposal lifecycle, Scope (+1 more)

### Community 125 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 6 Deterministic Evaluation Execution Adapter Implementation Plan, Task 1: Execution and unavailable-observation contracts, Task 2: Closed deterministic metric-sample adapter, Task 3: Append-only request and audit persistence, Task 4: Execution service and idempotent recovery, Task 5: CLI, documentation, and final verification

### Community 126 - "Signal"
Cohesion: 0.35
Nodes (16): Signal, _contribution(), _discipline(), _evidence(), _intent(), _master(), _of_type(), _result() (+8 more)

### Community 127 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 3 Weekly Reflection and Pattern Lifecycle Implementation Plan, Task 1: Weekly contracts and semantic identities, Task 2: Pure weekly aggregation and exact provenance, Task 3: Append-only weekly and lifecycle persistence, Task 4: Weekly CLI integration, Task 5: Corrected one-month baseline and durable context

### Community 128 - "DatasetManifest"
Cohesion: 0.25
Nodes (4): DatasetManifest, BaseModel, Path, PersistenceAndConfigTests

### Community 129 - "Deterministic Evaluation Execution"
Cohesion: 0.33
Nodes (5): Controlled CLI workflow, Deterministic Evaluation Execution, Identity and inputs, Persistence and retry, Protected Final OOS

### Community 130 - "OperatorControls"
Cohesion: 0.29
Nodes (3): OperatorControls, Monotonic operator gates: callers cannot use this contract to bypass safety., test_operator_controls_only_become_more_conservative()

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
Nodes (35): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., IndexRange, BaseModel (+27 more)

### Community 139 - "mt5/__init__.py"
Cohesion: 0.25
Nodes (6): MT5Constants, MT5SymbolMapping, BaseModel, Optional, demo-safe MetaTrader5 gateway and adapters., test_symbol_mapping_is_explicit_auditable_and_deterministic(), _constants()

### Community 141 - "MasterProposal"
Cohesion: 0.19
Nodes (25): DisciplineOutcome, build_execution_intent(), RiskContext, Pure construction of provenance-bound execution intents., Carry a fully linked Risk PASS into execution without changing it., _validate_upstream_links(), _progressed_to(), MasterProposal (+17 more)

### Community 142 - "Deterministic Weekly Reflection and Pattern Lifecycle"
Cohesion: 0.33
Nodes (5): Deterministic Weekly Reflection and Pattern Lifecycle, Identity, Knowledge lifecycle, Verified baseline, Weekly contract

### Community 143 - "Advisory Improvement Proposals"
Cohesion: 0.33
Nodes (5): Advisory Improvement Proposals, Eligibility and provenance, Identity and supersession, Lifecycle, Verified baseline

### Community 144 - "Global Constraints"
Cohesion: 0.22
Nodes (8): Deterministic Paired Baseline-vs-Candidate Comparison Implementation Plan, Global Constraints, Task 1: Immutable paired comparison contracts, Task 2: Pure paired comparison adapter, Task 3: Append-only migration and store, Task 4: Idempotent comparison service, Task 5: CLI and package integration, Task 6: Documentation, audits, Graphify, and final gate

### Community 145 - "default_shared_kernel_policy_set"
Cohesion: 0.22
Nodes (9): default_shared_kernel_policy_set(), BaseModel, Complete reviewed policy composition for one shared-kernel replay., Return a new set with only the reviewed Master-fusion policy replaced., Reproduce the exact policy composition used by Phase 7 system replay., SharedKernelPolicySet, test_default_shared_kernel_policy_set_is_frozen_and_content_addressed(), test_explicit_default_policy_set_preserves_replay_bytes() (+1 more)

### Community 146 - "system.py"
Cohesion: 0.19
Nodes (20): main(), Command-line entry point for Phase 7 system replay and result display., _catalog(), compare_replays(), _counts(), _event(), _file_sha256(), _fresh() (+12 more)

### Community 148 - "MetaTrader5Gateway"
Cohesion: 0.18
Nodes (9): MT5ConnectionError, RuntimeError, The terminal package or connected terminal is unavailable., _load_mt5(), _mapping(), _mappings(), MetaTrader5Gateway, Lazy concrete wrapper around the Windows-only MetaTrader5 package. (+1 more)

### Community 149 - "canonical_hash"
Cohesion: 0.12
Nodes (7): model_validator, model_validator, model_validator, model_validator, model_validator, canonical_hash(), Any

### Community 150 - "weekly_contracts.py"
Cohesion: 0.15
Nodes (34): build_weekly_reflection(), FailurePattern, PatternBase, PatternMetricSummary, PatternSignalClass, PatternType, StrEnum, Immutable contracts for deterministic weekly reflection and pattern lifecycle. (+26 more)

### Community 151 - "Phase 8 Task 9 Deterministic Paired Evaluation Design"
Cohesion: 0.25
Nodes (7): CLI and controlled validation, Contracts, Explicit exclusions, Persistence and idempotency, Phase 8 Task 9 Deterministic Paired Evaluation Design, Purpose and boundary, Validation and comparison flow

### Community 153 - "Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design"
Cohesion: 0.17
Nodes (11): Append-only persistence, Candidate contract, CLI, Evaluation result, Identity and serialization, Operator decision boundary, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design, Preregistered plan (+3 more)

### Community 154 - "SQLiteReasoningAuditStore"
Cohesion: 0.17
Nodes (13): ModelT, Row, LLMExecutionAttemptAudit, LLMRequestEnvelope, LLMStructuredResponseArtifact, _payload(), BaseModel, Connection (+5 more)

### Community 155 - "_context"
Cohesion: 0.16
Nodes (33): default_position_action_policy(), Return conservative deterministic V1 safety defaults., PositionSide, StrEnum, _context(), _evaluate(), _fresh(), _intent() (+25 more)

### Community 156 - "position_management/contracts.py"
Cohesion: 0.20
Nodes (19): MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel, PositionManagementOutcome, PositionManagementPolicy, PositionManagementReason, PositionManagementResult, BaseModel (+11 more)

### Community 157 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Implementation Plan, Task 1: Evaluation contracts and protected-OOS invariants, Task 2: Pure preregistration and result evaluation, Task 3: Append-only evaluation persistence, Task 4: Evaluation CLI without execution, Task 5: Documentation and final verification

### Community 158 - "Phase 9 Task 1 LLM Provider and Structured Reasoning Boundary Design"
Cohesion: 0.08
Nodes (25): Acceptance criteria, Attempt audit and failure handling, Authoritative append-only persistence, CLI boundary, Deferred work, Expected implementation validation, Generation policy, Goal (+17 more)

### Community 159 - "test_ollama_provider.py"
Cohesion: 0.12
Nodes (17): MonkeyPatch, Validate and normalize a V1 local Ollama endpoint., validate_loopback_ollama_url(), FakeOllamaTransport, _HTTPResponse, _identity_responses(), _json_bytes(), Exception (+9 more)

### Community 160 - "LocalModelRegistry"
Cohesion: 0.17
Nodes (12): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., LocalModelRegistry, ModelState, Any, BaseModel (+4 more)

### Community 161 - "cli.py"
Cohesion: 0.18
Nodes (22): Clock, ProviderFactory, _atomic_write(), _emit_bytes(), _json_bytes(), _load_controlled_input(), main(), _parser() (+14 more)

### Community 163 - "Proposal Evaluation"
Cohesion: 0.40
Nodes (4): CLI workflow, Governance boundary, Persistence and corrections, Proposal Evaluation

### Community 164 - "main"
Cohesion: 0.14
Nodes (20): main(), test_cli_has_no_final_oos_input_option(), test_cli_exposes_no_final_oos_input_option(), test_cli_has_no_final_oos_input_option(), test_cli_record_show_history_and_summary(), test_review_cli_exposes_no_final_oos_or_execution_option(), test_authorization_cli_exposes_no_execution_or_final_oos_option(), test_cli_record_show_history_summary_and_idempotent_retry() (+12 more)

### Community 168 - "Phase 8 Task 10 Governed Operator Review Bridge Design"
Cohesion: 0.33
Nodes (5): Contract, Linear-chain persistence, Phase 8 Task 10 Governed Operator Review Bridge Design, Safety boundary, Scope

### Community 169 - "Phase 3 label contract"
Cohesion: 0.40
Nodes (5): Decision and reference prices, Label families, Phase 3 label contract, Same-bar collision policy, Sensitivity and balance

### Community 170 - "Operator-authorized proposal lifecycle bridge"
Cohesion: 0.40
Nodes (4): Append-only history, Commands, Eligibility and identity, Operator-authorized proposal lifecycle bridge

### Community 172 - "Deterministic paired baseline-vs-candidate comparison"
Cohesion: 0.40
Nodes (4): Commands, Deterministic paired baseline-vs-candidate comparison, Governance, Persistence and retry behavior

### Community 175 - "Governed paired-evaluation review"
Cohesion: 0.50
Nodes (3): Commands, Governed paired-evaluation review, Identity and history

### Community 176 - "Phase 8 Task 10 Governed Operator Review Bridge Implementation Plan"
Cohesion: 0.50
Nodes (3): Constraints, Phase 8 Task 10 Governed Operator Review Bridge Implementation Plan, Test-first slices

### Community 177 - "SemanticTraceStep"
Cohesion: 0.19
Nodes (9): DeterministicDecisionProcessor, EntryDecisionInputs, BaseModel, Causal contexts supplied by the runtime-specific context adapter., Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, Any, _RecordingProcessor, _ReplayContext (+1 more)

### Community 179 - "generate_labels"
Cohesion: 0.19
Nodes (20): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., generate_labels(), DataFrame (+12 more)

### Community 180 - "SQLitePositionActionTransportLedger"
Cohesion: 0.24
Nodes (5): Path, SQLitePositionActionTransportLedger, PositionActionTransportTransition, BaseModel, model_validator

### Community 182 - "test_reasoning_service.py"
Cohesion: 0.32
Nodes (21): provider_identity(), _completion(), FakeReasoningProvider, _input_record(), _output_json(), parametrize, Path, Focused tests for offline reasoning orchestration and exact-result reuse. (+13 more)

### Community 183 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Implementation Plan, Task 1: Shared replay policy composition boundary, Task 2: Frozen candidate and governed data contracts, Task 3: Closed shared-kernel engine and metric extraction, Task 4: Append-only store and idempotent service, Task 5: CLI, documentation, and final governance gate

### Community 184 - "Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design"
Cohesion: 0.25
Nodes (7): CLI and controlled validation, Execution and metric production, Governed inputs and identity, Persistence and recovery, Phase 8 Task 8 Shared-Kernel Candidate Driver V1 Design, Purpose, Shared-kernel injection boundary

### Community 187 - "Shared-Kernel Candidate Driver V1"
Cohesion: 0.29
Nodes (6): Candidate injection boundary, Commands, Controlled V1 validation, Governance and data, Persistence and retry, Shared-Kernel Candidate Driver V1

### Community 190 - "utc"
Cohesion: 0.33
Nodes (15): CaptureFixture, utc(), FakeCLIProvider, Path, Focused tests for the offline reasoning command-line boundary., _run_args(), test_exact_reuse_emits_same_response_without_provider_call(), test_failure_output_contains_only_safe_metadata() (+7 more)

### Community 191 - "orchestration/contracts.py"
Cohesion: 0.20
Nodes (13): Strict operational configuration for the Phase 7 runtime service., DecisionCycle, OutcomeCount, BaseModel, StrEnum, Strict orchestration-only contracts for the shared Phase 7 runtime., Auditable classifications emitted by the existing decision boundaries., RuntimeMode (+5 more)

### Community 192 - "test_quant_development_runner.py"
Cohesion: 0.23
Nodes (12): compare_runs(), Any, Path, Compare completed development runs without retraining or scalar ranking., _read(), experiment(), Path, test_compare_runs_uses_multiple_evidence_dimensions() (+4 more)

### Community 193 - "test_reasoning_boundaries.py"
Cohesion: 0.27
Nodes (11): AST, _identifiers(), _matches_prefix(), _modules(), _phase8_table_counts(), Path, Executable isolation and mutation-safety audit for Phase 9 Task 1., test_fast_path_packages_do_not_import_reasoning() (+3 more)

### Community 194 - "File Structure"
Cohesion: 0.15
Nodes (12): File Structure, Global Constraints, Phase 9 Task 1 LLM Provider and Structured Reasoning Boundary Implementation Plan, Task 1: Contract foundation and canonical identities, Task 2: Code-owned prompt and provider-neutral protocol, Task 3: Loopback-only native Ollama adapter, Task 4: Append-only reasoning migration and store, Task 5: Offline reasoning service, failures, and deterministic reuse (+4 more)

### Community 196 - "model_validator"
Cohesion: 0.19
Nodes (5): JsonValue, _canonical_character_count(), _normalize_sources_and_context(), model_validator, _validate_safe_context()

### Community 197 - "Offline LLM reasoning boundary"
Cohesion: 0.20
Nodes (9): Append-only audit, CLI, Exact-result reuse and determinism, Identity and structured-output boundary, Measured controlled fixture, Non-goals, Offline LLM reasoning boundary, Optional real Ollama smoke test (+1 more)

### Community 198 - "RuntimeConfig"
Cohesion: 0.25
Nodes (9): load_runtime_config(), BaseModel, Path, RuntimeConfig, build_mt5_gateway(), Build the lazy gateway; operational paths are not semantic identity., test_checked_in_runtime_config_is_strict_and_disabled(), test_explicit_terminal_path_is_forwarded_without_entering_config_identity() (+1 more)

### Community 200 - "paired_evaluation_review_cli.py"
Cohesion: 0.56
Nodes (8): _emit(), handle_paired_evaluation_review_command(), _history(), Namespace, CLI handlers for append-only operator review of paired evidence., _record(), _show(), _summary()

## Knowledge Gaps
- **424 isolated node(s):** `Append-only persistence and supersession`, `Architecture`, `Baseline validation`, `CLI`, `Exact provenance validation` (+419 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1219 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `DatasetManifest`, `LabelDefinition`, `reflection/__main__.py`, `agents/__init__.py`, `development/config.py`, `folds.py`, `ProposalEvaluationPlan`, `model_validator`, `MasterProposal`, `system.py`, `model_validator`, `datasets/builder.py`, `weekly_contracts.py`, `SQLiteWeeklyReflectionStore`, `SQLiteReasoningAuditStore`, `runtime/__init__.py`, `position_management/contracts.py`, `kernel.py`, `ToolResult`, `model_validator`, `processor.py`, `.normalize_validate_and_bind_identity`, `persist_controlled_plan`, `model_validator`, `model_validator`, `SQLiteExperienceStore`, `MetricScope`, `model_validator`, `.bind_identity`, `timedelta`, `model_validator`, `proposals.py`, `execution.py`, `reflection/__init__.py`, `SQLitePositionActionTransportLedger`, `SQLitePairedEvaluationReviewStore`, `.validate_and_bind_identity`, `model_validator`, `.bind_identity`, `.validate_and_bind_identity`, `orchestration/contracts.py`, `test_reasoning_boundaries.py`, `.bind_identity`, `model_validator`, `runner.py`, `model_validator`, `model_validator`, `model_validator`, `policies.py`, `snapshot.py`, `position.py`, `.normalize_and_bind_identity`, `.validate_and_bind_identity`, `replay_validation/__init__.py`, `ReflectionModel`, `request_envelope`, `replay.py`, `position_actions/evaluator.py`, `ExecutionIntent`, `quant/config.py`, `attribution.py`, `model_validator`, `execution_boundary/__init__.py`, `dataset.py`, `ExperienceProvenance`, `reasoning/contracts.py`, `SQLiteProposalEvaluationStore`, `trainer.py`?**
  _High betweenness centrality (0.204) - this node is a cross-community bridge._
- **Why does `Database` connect `SQLiteProposalEvaluationStore` to `DatasetManifest`, `SQLiteExecutionLedger`, `reflection/__main__.py`, `persist_controlled_plan`, `execution_boundary/__init__.py`, `SQLiteExperienceStore`, `position.py`, `ProposalEvaluationPlan`, `timedelta`, `MetricScope`, `ReflectionModel`, `reflection/__init__.py`, `SQLitePositionActionTransportLedger`, `SQLitePairedEvaluationReviewStore`, `weekly_contracts.py`, `SQLiteWeeklyReflectionStore`, `SQLiteReasoningAuditStore`, `attribution.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `daily.py`, `_source_stores`, `test_runtime_orchestration.py`, `MasterProposal`, `system.py`, `runtime/__init__.py`, `_context`, `test_risk_boundary.py`, `SQLiteExecutionLedger`, `main`, `processor.py`, `SQLiteExperienceStore`, `SemanticTraceStep`, `proposals.py`, `_context`, `evaluate_discipline`, `schemas.py`, `test_execution_boundary.py`, `policies.py`, `preflight.py`, `position_actions/evaluator.py`, `ExecutionIntent`, `attribution.py`, `test_foundation.py`, `execution_boundary/__init__.py`, `ExperienceProvenance`, `EntryGateway`, `test_weekly_reflection.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 224 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 224 INFERRED edges - model-reasoned connections that need verification._
- **Are the 83 inferred relationships involving `MetricScope` (e.g. with `_fixture()` and `_run()`) actually correct?**
  _`MetricScope` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 70 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._