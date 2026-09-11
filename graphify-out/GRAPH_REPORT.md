# Graph Report - phase-8-reflection-experience  (2026-09-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 4019 nodes · 13294 edges · 191 communities (151 shown, 37 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 2292 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4451fd49`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- daily.py
- LabelDefinition
- reflection/__main__.py
- axq/features/registry.py
- DailyReflection
- indicators.py
- agents/__init__.py
- update_scenario
- development/config.py
- axq/config.py
- test_runtime_orchestration.py
- SQLiteImprovementProposalStore
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
- runtime/journal.py
- System architecture (Phase 0-7 baseline)
- weekly_contracts.py
- QuantAgent
- system.py
- Architecture decision log
- _deterministic.py
- README.md
- test_risk_boundary.py
- ToolResult
- service.py
- SQLiteExecutionLedger
- initial_runtime_state
- Global Constraints
- discipline/__init__.py
- Phase 0-6 runbook
- timedelta
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- SQLiteExperienceStore
- MetricScope
- ProposalEvaluationPlan
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
- ExecutionInstruction
- test_execution_boundary.py
- position.py
- MasterProposal
- snapshot.py
- .validate_and_bind_identity
- default_registry
- preflight.py
- replay_validation/__init__.py
- evaluation_contracts.py
- Global Constraints
- ReplayClock
- processor.py
- Global Constraints
- ExecutionIntent
- quant/config.py
- test_agent_tools.py
- Phase 7 deterministic runtime orchestration
- attribution.py
- test_runtime_state.py
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
- ComponentFreshness
- Position action safety
- FeatureManifest
- session_features
- test_daily_reflection.py
- evaluate_predictions
- test_datasets_phase3.py
- execution_boundary/__init__.py
- Phase 8 Task 7 Governed Candidate Replay Evaluator Design
- ExecutionTransition
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
- risk_boundary/evaluator.py
- Deterministic Weekly Reflection and Pattern Lifecycle
- Advisory Improvement Proposals
- Global Constraints
- default_shared_kernel_policy_set
- load_replay_frame
- model_validator
- MetaTrader5Gateway
- canonical_hash
- run_system_replay
- Phase 8 Task 9 Deterministic Paired Evaluation Design
- _MT5Module
- Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design
- .validate_and_bind_identity
- test_paired_evaluation_contracts.py
- ContractAndRiskTests
- Global Constraints
- .normalize_and_bind_identity
- RuntimeEvent
- LocalModelRegistry
- model_validator
- model_validator
- Proposal Evaluation
- test_system_replay.py
- .normalize_validate_and_bind_identity
- .normalize_validate_and_bind_identity
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
- EntryDecisionInputs
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
- SharedKernelPolicySet

## God Nodes (most connected - your core abstractions)
1. `canonical_hash()` - 206 edges
2. `MetricScope` - 107 edges
3. `Signal` - 92 edges
4. `RuntimeEvent` - 92 edges
5. `SQLiteProposalEvaluationStore` - 75 edges
6. `ReflectionModel` - 74 edges
7. `SQLiteImprovementProposalStore` - 66 edges
8. `ExecutionIntent` - 64 edges
9. `CanonicalMetricSampleArtifact` - 60 edges
10. `canonical_record_bytes()` - 58 edges

## Surprising Connections (you probably didn't know these)
- `test_paired_contracts_are_exported_from_reflection_package()` --uses--> `PairedEvaluationRequest`  [INFERRED]
  tests/test_paired_evaluation_contracts.py → src/axq/reflection/paired_evaluation_contracts.py
- `test_system_replay_retains_exact_attribution_journal_semantics()` --uses--> `JournalRecordType`  [INFERRED]
  tests/test_system_replay.py → src/axq/runtime/journal.py
- `test_checked_in_runtime_config_is_strict_and_disabled()` --calls--> `load_runtime_config()`  [INFERRED]
  tests/test_runtime_orchestration.py → src/axq/orchestration/config.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py

## Import Cycles
- None detected.

## Communities (191 total, 37 thin omitted)

### Community 0 - "daily.py"
Cohesion: 0.35
Nodes (20): FindingCategory, FindingSignal, StrEnum, ReflectionFinding, SampleGuardRecord, SampleGuardStatus, _agent_findings(), _average() (+12 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.09
Nodes (51): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, CollisionPolicy (+43 more)

### Community 2 - "reflection/__main__.py"
Cohesion: 0.07
Nodes (45): Any, register_candidate_replay_commands(), Any, register_execution_commands(), _build(), _days(), _emit(), _latest_records() (+37 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.11
Nodes (18): Compatibility entry point; implementation lives in the installable axq package., breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars., FeatureManifestEntry, BaseModel, multi_timeframe_features() (+10 more)

### Community 4 - "DailyReflection"
Cohesion: 0.10
Nodes (31): DailyReflection, MetricFact, ReflectionPolicy, _canonical_payload(), datetime, Path, Append-only SQLite persistence for daily reflection records., Persist policies and immutable daily revisions as semantic records. (+23 more)

### Community 5 - "indicators.py"
Cohesion: 0.12
Nodes (40): skipif, aroon(), atr(), cci(), directional_movement(), money_flow_index(), DataFrame, Series (+32 more)

### Community 6 - "agents/__init__.py"
Cohesion: 0.08
Nodes (49): AgentInput, AgentReasoningBudget, model_validator, Protocol, Small shared specialist input and output-validation boundary., Interpret supplied facts without recomputing tools or authorizing execution., Verify evidence references exact causal tool facts from its input., Validate an agent output before applying its deterministic memory transition. (+41 more)

### Community 7 - "update_scenario"
Cohesion: 0.25
Nodes (28): Apply one M5 or intrabar evidence event without consulting a clock., update_scenario(), _agent_pair(), _create(), _event(), _market(), datetime, parametrize (+20 more)

### Community 8 - "development/config.py"
Cohesion: 0.07
Nodes (46): AblationConfig, development_run_id(), EvaluationConfig, ExperimentConfig, load_ablation_config(), load_experiment_config(), _load_mapping(), load_suite_config() (+38 more)

### Community 9 - "axq/config.py"
Cohesion: 0.21
Nodes (13): main(), AppConfig, DatabaseConfig, FeatureConfig, IpcConfig, load_config(), LoggingConfig, Any (+5 more)

### Community 10 - "test_runtime_orchestration.py"
Cohesion: 0.10
Nodes (28): DecisionPlan, Existing semantic outputs assembled by an injected decision-cycle processor., FakeEntryAdapter, FakeGateway, FakePositionActionAdapter, FakeProcessor, FakeRunner, _intent() (+20 more)

### Community 11 - "SQLiteImprovementProposalStore"
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
Cohesion: 0.06
Nodes (51): CompletedProcess, main(), main(), _git_identity(), main(), _run_git(), DataFrame, Leakage-safe multi-timeframe alignment. (+43 more)

### Community 23 - "runtime/journal.py"
Cohesion: 0.08
Nodes (22): ReconciliationReport, ResumeReadiness, DeterministicDecisionProcessor, Invoke Master → Discipline → Risk and existing-position boundaries in fixed…, Compose existing pure functions; adapters provide causal context only., BrokerSnapshotProvider, DecisionCycleProcessor, PositionActionAdapter (+14 more)

### Community 24 - "System architecture (Phase 0-7 baseline)"
Cohesion: 0.10
Nodes (20): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Phase 8 governed comparison boundary (+12 more)

### Community 25 - "weekly_contracts.py"
Cohesion: 0.07
Nodes (68): build_weekly_reflection(), _build(), _emit(), handle_weekly_command(), _history(), _latest(), _policy(), date (+60 more)

### Community 26 - "QuantAgent"
Cohesion: 0.20
Nodes (11): evaluate_saved_run(), Any, Reproduce frozen split metrics without fitting or retraining., Any, datetime, ndarray, Series, QuantAgent (+3 more)

### Community 27 - "system.py"
Cohesion: 0.10
Nodes (51): execution_result_to_runtime_event(), Bridge typed execution results into the shared Phase 6 runtime path., Convert actionable execution feedback; local NO_ACTION stays local., Immutable contracts for durable execution recovery and safe resume., _event(), _fresh(), Any, datetime (+43 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.05
Nodes (40): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+32 more)

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
Cohesion: 0.09
Nodes (41): _catalog(), _snapshot(), FreshnessStatus, FeatureFactTool, datetime, Capability-focused fact tools and their small deterministic catalog., _result(), SlowContextFactTool (+33 more)

### Community 33 - "service.py"
Cohesion: 0.09
Nodes (27): create_recovery_checkpoint(), load_runtime_config(), BaseModel, Path, Strict operational configuration for the Phase 7 runtime service., RuntimeConfig, DecisionCycle, OutcomeCount (+19 more)

### Community 34 - "SQLiteExecutionLedger"
Cohesion: 0.09
Nodes (46): Connection, Path, Durable projection reconstructed only from immutable transitions., SQLiteExecutionLedger, _conflict_reason(), _finding(), _object_id(), datetime (+38 more)

### Community 35 - "initial_runtime_state"
Cohesion: 0.21
Nodes (28): initial_runtime_state(), Construct a canonical state with explicit unknown component values., account(), apply(), event(), feedback(), fresh(), market() (+20 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "discipline/__init__.py"
Cohesion: 0.18
Nodes (23): DisciplineContext, DisciplineCounters, DisciplineModel, DisciplineOutcome, DisciplinePolicy, DisciplinePosition, DisciplineReason, DisciplineResult (+15 more)

### Community 38 - "Phase 0-6 runbook"
Cohesion: 0.07
Nodes (27): Data lifecycle, Future restart and reconciliation gate, Operational checks, Phase 0-6 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development (+19 more)

### Community 39 - "timedelta"
Cohesion: 0.06
Nodes (77): _aggregate(), CanonicalMetricSamplesAdapter, EvaluationAdapterOutput, input_artifact_ref(), Closed deterministic adapter for canonical metric sample artifacts., Aggregate exact preregistered metric series without executing candidate code., _artifact(), _emit() (+69 more)

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
Cohesion: 0.07
Nodes (71): MetricScope, SemanticArtifactRef, canonical_record_bytes(), BaseModel, ProposalTargetComponent, _emit(), handle_shared_kernel_candidate_command(), _optional_scope() (+63 more)

### Community 45 - "ProposalEvaluationPlan"
Cohesion: 0.16
Nodes (24): CandidateReplayEngineKind, CandidateReplayStatus, ControlledMetricValue, ControlledReplayFixtureArtifact, ControlledReplayObservation, StrEnum, CandidateReplayEngine, CandidateReplayEngineOutput (+16 more)

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "test_evidence_kernel.py"
Cohesion: 0.28
Nodes (21): ChartAgent, _input(), parametrize, _result(), test_agent_rejects_a_tool_outside_its_access_boundary(), test_chart_agent_abstains_when_structure_is_unavailable(), test_chart_agent_interprets_directional_structure(), test_chart_agent_represents_hierarchical_mtf_conflict_as_uncertainty() (+13 more)

### Community 49 - "proposals.py"
Cohesion: 0.14
Nodes (24): ProposalEvidenceGuard, ProposalGuardKind, build_improvement_proposals(), _content(), _index_unique(), ProposalBuildResult, ProposalEligibilityAssessment, Experience (+16 more)

### Community 50 - "execution.py"
Cohesion: 0.20
Nodes (9): _PendingClose, _PendingStop, datetime, Deterministic, transport-only fill mechanics for system replay., A causal fill book; it contains no signal or policy decisions., ReplayBar, ReplayBarResult, ReplayExecutionBook (+1 more)

### Community 51 - "reflection/__init__.py"
Cohesion: 0.05
Nodes (78): Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, BaseModel, Immutable content-addressed contracts for deterministic daily reflection., ReflectionModel, Append-only persistence for preregistered proposal evaluations., Deterministic Phase 8 reflection contracts and services., _artifact_matches(), _artifacts() (+70 more)

### Community 52 - "SQLitePairedEvaluationReviewStore"
Cohesion: 0.07
Nodes (45): _emit(), handle_paired_evaluation_review_command(), _history(), Namespace, CLI handlers for append-only operator review of paired evidence., _record(), _show(), _summary() (+37 more)

### Community 53 - "Repository instructions"
Cohesion: 0.50
Nodes (3): Graphify, Repository instructions, Repository-start workflow

### Community 54 - "_context"
Cohesion: 0.06
Nodes (93): ScenarioStatus, ReconciliationKind, ResumeStatus, default_position_action_policy(), Return conservative deterministic V1 safety defaults., MissingEvidenceBehavior, PositionManagementContext, PositionManagementModel (+85 more)

### Community 55 - "SQLiteRuntimeJournal"
Cohesion: 0.15
Nodes (15): Connection, Path, Small additive SQLite implementation outside the pure decision kernel., Flush committed WAL content without changing semantic journal history., SQLiteRuntimeJournal, JournalEventSource, Canonical event source reconstructed from append-only journal records., _event() (+7 more)

### Community 68 - "evaluate_discipline"
Cohesion: 0.26
Nodes (34): default_demo_discipline_policy(), evaluate_discipline(), Apply behavioral cadence rules without financial risk or execution authority., Return intentionally permissive Demo defaults, not optimized trading truth., _context(), _policy(), _proposal(), parametrize (+26 more)

### Community 69 - "runner.py"
Cohesion: 0.08
Nodes (42): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+34 more)

### Community 70 - "Tool-Augmented Agentic Architecture"
Cohesion: 0.09
Nodes (22): Deferred risks, Event model and causality, Existing components reused, Explicitly unimplemented after Phase 7 Task 9, Explicitly untouched, Implemented shared path and future paths, Invariants, Live/replay ports (+14 more)

### Community 71 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 6 Tool-Augmented Agentic Baseline Implementation Plan, Task 1: Canonical runtime events and shared state, Task 2: Clock, event source, and causal state reducer, Task 3: Tool facts and optional predictive-model adapter, Task 4: Stateful specialist evidence contracts, Task 5: M5 thesis and intrabar scenario state machine, Task 6: Initial specialist agents and evidence bundle (+2 more)

### Community 72 - "RunStateStore"
Cohesion: 0.42
Nodes (3): Any, Path, RunStateStore

### Community 73 - "ExecutionInstruction"
Cohesion: 0.18
Nodes (8): ExecutionInstruction, MasterDecision, BaseModel, datetime, field_validator, model_validator, RiskDecision, StrictMessage

### Community 74 - "test_execution_boundary.py"
Cohesion: 0.16
Nodes (33): RuntimeError, Submission may have reached the broker and requires reconciliation., UnknownSubmissionState, _adapter(), _discipline(), _intent(), _observation(), _policy() (+25 more)

### Community 75 - "position.py"
Cohesion: 0.10
Nodes (24): _float_value(), _int_value(), MT5PositionActionAdapter, _optional_close(), _optional_price(), _positive_int(), Demo-only MetaTrader 5 transport for Task 7 position-action intents., Idempotently translate an already-safe position action to exact MT5 calls. (+16 more)

### Community 76 - "MasterProposal"
Cohesion: 0.16
Nodes (31): EvidenceDisposition, FusionPolicy, FusionReason, MasterModel, MasterProposal, BaseModel, StrEnum, Immutable contracts for deterministic specialist-evidence fusion. (+23 more)

### Community 77 - "snapshot.py"
Cohesion: 0.19
Nodes (22): BrokerObjectKind, MT5PersistedIntentLink, MT5SnapshotError, Narrow contracts isolating the optional MetaTrader5 package., A broker snapshot could not be acquired without guessing., _canonical_links(), _epoch_seconds(), MT5BrokerSnapshotProvider (+14 more)

### Community 79 - "default_registry"
Cohesion: 0.12
Nodes (19): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., price_action_features(), Any, DataFrame, default_registry() (+11 more)

### Community 80 - "preflight.py"
Cohesion: 0.16
Nodes (22): The transport failed before submission could be accepted., TransportFailure, datetime, _account_mode(), default_mt5_transport_config(), _float_value(), _int_value(), MT5EntryPreflight (+14 more)

### Community 81 - "replay_validation/__init__.py"
Cohesion: 0.18
Nodes (17): StrEnum, ReplaySide, Deterministic system-replay validation support., BaseModel, model_validator, Path, Durable content-addressed facts emitted by the deterministic replay transport., ReplayActionApplication (+9 more)

### Community 82 - "evaluation_contracts.py"
Cohesion: 0.13
Nodes (48): AcceptanceCriterion, CandidateKind, CriterionComparator, CriterionOutcome, CriterionOutcomeStatus, CriterionRole, EvaluationAggregateOutcome, FinalOOSPolicy (+40 more)

### Community 83 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 7 Task 9 Demo Runtime Orchestration Implementation Plan, Task 1: Runtime configuration, modes, status, and operator controls, Task 2: Startup recovery and fail-closed readiness, Task 3: One shared event/decision/feedback path, Task 4: Graceful shutdown and configuration factory, Task 5: Documentation and final gate

### Community 84 - "ReplayClock"
Cohesion: 0.11
Nodes (35): Collection, ScenarioTransition, ensure_utc(), datetime, Protocol, UTC clocks shared by live processing and deterministic replay., Reject naive timestamps and return a normalized UTC timestamp., Clock contract used outside the pure reducer. (+27 more)

### Community 85 - "processor.py"
Cohesion: 0.17
Nodes (29): Concrete composition of existing deterministic Phase 7 decision boundaries., PositionActionContext, PositionActionModel, PositionActionPolicy, PositionActionReason, PositionActionSafetyOutcome, PositionActionSafetyResult, PositionActionType (+21 more)

### Community 86 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Phase 7 Task 5 Execution Recovery Implementation Plan, Task 1: Canonical broker refresh events, Task 2: Recovery and reconciliation contracts, Task 3: Append-only SQLite execution ledger, Task 4: Exact-linkage reconciliation, Task 5: Fail-closed safe-resume and continuity assessment, Task 6: Refresh orchestration and recovery checkpoints (+1 more)

### Community 87 - "ExecutionIntent"
Cohesion: 0.14
Nodes (13): DemoExecutionAdapter, InMemoryExecutionLedger, datetime, Process one immutable intent idempotently., Tiny ledger reference implementation; persistent ports can implement the…, Guarded demo adapter; never permits a live-account submission., ExecutionIntent, ExecutionObservation (+5 more)

### Community 88 - "quant/config.py"
Cohesion: 0.07
Nodes (40): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+32 more)

### Community 89 - "test_agent_tools.py"
Cohesion: 0.11
Nodes (25): PredictiveModelEvidenceProvider, Any, Protocol, QuantAgentEvidenceProvider, Return label-to-probability facts without a trading decision., Narrow adapter around the existing frozen Phase 4 QuantAgent., _ExplodingTool, _FailingProvider (+17 more)

### Community 90 - "Phase 7 deterministic runtime orchestration"
Cohesion: 0.33
Nodes (5): Event and mutation sequence, Modes, Phase 7 deterministic runtime orchestration, Shutdown and replay output, Startup and recovery

### Community 91 - "attribution.py"
Cohesion: 0.07
Nodes (64): _average(), _counts(), ExperienceSummary, BaseModel, Experience, Descriptive-only analytics for persisted Phase 8 experiences., Versioned aggregate facts; no score, recommendation, or policy mutation., Return descriptive aggregates while keeping unavailable values as ``None``. (+56 more)

### Community 92 - "test_runtime_state.py"
Cohesion: 0.20
Nodes (20): account(), feedback(), freshness(), market(), order(), position(), datetime, parametrize (+12 more)

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
Cohesion: 0.15
Nodes (10): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., Feature functions and registry., candles(), DataTests, FeatureTests (+2 more)

### Community 98 - "proposal_cli.py"
Cohesion: 0.34
Nodes (13): _build(), _emit(), handle_proposal_command(), _history(), _latest(), _policy(), Namespace, Path (+5 more)

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
Cohesion: 0.10
Nodes (11): MT5Gateway, Protocol, _float_value(), _int_value(), MT5ExecutionAdapter, MT5ExecutionTransport, _positive_int(), datetime (+3 more)

### Community 104 - "PositionGateway"
Cohesion: 0.15
Nodes (14): _adapter(), _constants(), _intent(), PositionGateway, parametrize, test_close_is_exact_full_close_not_reversal(), test_disabled_is_zero_touch_and_dry_run_checks_without_send(), test_exact_ticket_volume_and_stop_are_revalidated_before_send() (+6 more)

### Community 105 - "ComponentFreshness"
Cohesion: 0.17
Nodes (17): ContinuityStatus, StrEnum, evaluate_resume_readiness(), _is_fresh(), datetime, Protocol, Pure fail-closed startup readiness evaluation., RecoveryThesis (+9 more)

### Community 106 - "Position action safety"
Cohesion: 0.40
Nodes (4): Journal and transport boundary, Position action safety, Safety behavior, V1 contracts

### Community 107 - "FeatureManifest"
Cohesion: 0.20
Nodes (10): FeatureManifest, Path, Canonical feature-manifest models., feature_ablation_variants(), Manifest-bound feature ablation plans; execution remains fold-local., fold(), frame(), DataFrame (+2 more)

### Community 108 - "session_features"
Cohesion: 0.23
Nodes (10): _local_window(), Any, DataFrame, Series, DST-aware session features. Source timestamps are interpreted as UTC., session_features(), test_london_and_new_york_dst_transitions(), test_manifest_is_reproducible_and_complete() (+2 more)

### Community 109 - "test_daily_reflection.py"
Cohesion: 0.39
Nodes (11): _agent(), _findings(), _management(), _provenance(), datetime, _rejection(), test_agent_position_and_runtime_anomaly_findings_use_exact_daily_sources(), test_daily_aggregation_detects_confidence_excursion_and_rejection_patterns() (+3 more)

### Community 110 - "evaluate_predictions"
Cohesion: 0.11
Nodes (29): evaluate_challenger_evidence(), Any, Advisory Champion/Challenger evidence contract., calibration_diagnostics(), compare_calibration_methods(), opportunity_utilization(), overfitting_report(), Any (+21 more)

### Community 111 - "test_datasets_phase3.py"
Cohesion: 0.14
Nodes (20): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only., build(), candles() (+12 more)

### Community 112 - "execution_boundary/__init__.py"
Cohesion: 0.12
Nodes (27): ExecutionAdapter, ExecutionLedger, ExecutionTransport, Protocol, Demo-safe execution adapter boundary with explicit idempotency semantics., Submit an already approved intent to the execution transport., build_execution_intent(), default_execution_policy() (+19 more)

### Community 113 - "Phase 8 Task 7 Governed Candidate Replay Evaluator Design"
Cohesion: 0.22
Nodes (8): CLI, Contracts and identity, Controlled replay engine, Exact linkage and Final OOS boundary, Persistence, service, and reuse, Phase 8 Task 7 Governed Candidate Replay Evaluator Design, Scope, Validation

### Community 115 - "SQLiteProposalEvaluationStore"
Cohesion: 0.07
Nodes (32): main(), Database, Connection, Path, _build_plan(), _emit(), handle_evaluation_command(), _input() (+24 more)

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
Cohesion: 0.14
Nodes (28): dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run(), write_json() (+20 more)

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
Cohesion: 0.15
Nodes (28): MarketRegime, StrEnum, Stable, versioned messages crossing agent, master, risk, and execution…, RiskStatus, Signal, _decision(), _provenance(), test_actual_trade_cannot_be_marked_simulated() (+20 more)

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
Cohesion: 0.16
Nodes (18): ProbabilityCalibrator, ndarray, Validation-only probability calibration without OOS access., _aggregate_fold_metrics(), completed_fold_summary(), DevelopmentFoldResult, fold_identity(), Any (+10 more)

### Community 139 - "mt5/__init__.py"
Cohesion: 0.25
Nodes (6): MT5Constants, MT5SymbolMapping, BaseModel, Optional, demo-safe MetaTrader5 gateway and adapters., test_symbol_mapping_is_explicit_auditable_and_deterministic(), _constants()

### Community 141 - "risk_boundary/evaluator.py"
Cohesion: 0.20
Nodes (20): EntryContextProvider, PositionActionContextProvider, PositionContextProvider, BaseModel, StrEnum, Strict contracts for the deterministic financial Risk boundary., RiskBoundaryModel, RiskContext (+12 more)

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
Cohesion: 0.27
Nodes (8): main(), Command-line entry point for Phase 7 system replay and result display., default_shared_kernel_policy_set(), Reproduce the exact policy composition used by Phase 7 system replay., compare_replays(), test_default_shared_kernel_policy_set_is_frozen_and_content_addressed(), test_explicit_default_policy_set_preserves_replay_bytes(), test_master_fusion_replacement_changes_only_the_reviewed_policy()

### Community 146 - "load_replay_frame"
Cohesion: 0.31
Nodes (10): market_structure_features(), Any, DataFrame, _file_sha256(), load_replay_frame(), _merge_htf_bias(), DataFrame, Path (+2 more)

### Community 148 - "MetaTrader5Gateway"
Cohesion: 0.15
Nodes (11): MT5ConnectionError, RuntimeError, The terminal package or connected terminal is unavailable., _load_mt5(), _mapping(), _mappings(), MetaTrader5Gateway, Path (+3 more)

### Community 149 - "canonical_hash"
Cohesion: 0.15
Nodes (4): model_validator, model_validator, canonical_hash(), Any

### Community 150 - "run_system_replay"
Cohesion: 0.33
Nodes (6): _identity(), ReplayClosedTrade, ReplayFill, _counts(), run_system_replay(), test_source_records_convert_existing_replay_semantics_without_reidentifying()

### Community 151 - "Phase 8 Task 9 Deterministic Paired Evaluation Design"
Cohesion: 0.25
Nodes (7): CLI and controlled validation, Contracts, Explicit exclusions, Persistence and idempotency, Phase 8 Task 9 Deterministic Paired Evaluation Design, Purpose and boundary, Validation and comparison flow

### Community 153 - "Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design"
Cohesion: 0.17
Nodes (11): Append-only persistence, Candidate contract, CLI, Evaluation result, Identity and serialization, Operator decision boundary, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Design, Preregistered plan (+3 more)

### Community 155 - "test_paired_evaluation_contracts.py"
Cohesion: 0.44
Nodes (8): _artifact(), _manifest(), datetime, _request(), test_metric_comparison_requires_canonical_decimal_and_consistent_availability(), test_paired_contracts_are_exported_from_reflection_package(), test_request_identity_excludes_operational_timestamp_and_is_immutable(), test_request_rejects_naive_time_and_final_oos_input()

### Community 156 - "ContractAndRiskTests"
Cohesion: 0.36
Nodes (7): calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext, RiskLimits, veto_reasons(), ContractAndRiskTests

### Community 157 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Global Constraints, Phase 8 Task 5 Proposal Evaluation Contract and Persistence Implementation Plan, Task 1: Evaluation contracts and protected-OOS invariants, Task 2: Pure preregistration and result evaluation, Task 3: Append-only evaluation persistence, Task 4: Evaluation CLI without execution, Task 5: Documentation and final verification

### Community 159 - "RuntimeEvent"
Cohesion: 0.06
Nodes (30): BaseModel, datetime, RuntimeEvent, JournalOutcome, JournalOutcomeStatus, EvidenceBundle, EvidenceKernel, BaseModel (+22 more)

### Community 160 - "LocalModelRegistry"
Cohesion: 0.17
Nodes (12): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., LocalModelRegistry, ModelState, Any, BaseModel (+4 more)

### Community 163 - "Proposal Evaluation"
Cohesion: 0.40
Nodes (4): CLI workflow, Governance boundary, Persistence and corrections, Proposal Evaluation

### Community 164 - "test_system_replay.py"
Cohesion: 0.36
Nodes (5): PendingReplayEntry, _bar(), test_entry_executes_at_next_m5_open_and_cannot_stop_on_fill_bar(), test_modified_stop_never_retroactively_triggers_in_modification_bar(), test_system_replay_retains_exact_attribution_journal_semantics()

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

### Community 177 - "EntryDecisionInputs"
Cohesion: 0.67
Nodes (3): EntryDecisionInputs, BaseModel, Causal contexts supplied by the runtime-specific context adapter.

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

### Community 195 - "SharedKernelPolicySet"
Cohesion: 0.29
Nodes (5): BaseModel, model_validator, Complete reviewed policy composition for one shared-kernel replay., Return a new set with only the reviewed Master-fusion policy replaced., SharedKernelPolicySet

## Knowledge Gaps
- **381 isolated node(s):** `Append-only persistence and supersession`, `Architecture`, `Baseline validation`, `CLI`, `Exact provenance validation` (+376 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1113 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `canonical_hash()` connect `canonical_hash` to `DatasetManifest`, `LabelDefinition`, `DailyReflection`, `agents/__init__.py`, `development/config.py`, `folds.py`, `SQLiteImprovementProposalStore`, `model_validator`, `risk_boundary/evaluator.py`, `model_validator`, `datasets/builder.py`, `run_system_replay`, `runtime/journal.py`, `weekly_contracts.py`, `.validate_and_bind_identity`, `system.py`, `_deterministic.py`, `.normalize_and_bind_identity`, `RuntimeEvent`, `ToolResult`, `service.py`, `model_validator`, `model_validator`, `discipline/__init__.py`, `.normalize_validate_and_bind_identity`, `timedelta`, `model_validator`, `.normalize_validate_and_bind_identity`, `SQLiteExperienceStore`, `MetricScope`, `model_validator`, `.bind_identity`, `model_validator`, `proposals.py`, `execution.py`, `reflection/__init__.py`, `.validate_and_bind_identity`, `SQLitePairedEvaluationReviewStore`, `_context`, `.validate_event`, `.validate_and_bind_identity`, `model_validator`, `.bind_identity`, `.validate_and_bind_identity`, `SharedKernelPolicySet`, `runner.py`, `position.py`, `MasterProposal`, `snapshot.py`, `.validate_and_bind_identity`, `replay_validation/__init__.py`, `evaluation_contracts.py`, `processor.py`, `quant/config.py`, `attribution.py`, `model_validator`, `execution_boundary/__init__.py`, `SQLiteProposalEvaluationStore`, `trainer.py`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `Signal` connect `Signal` to `daily.py`, `reflection/__main__.py`, `DailyReflection`, `test_runtime_orchestration.py`, `risk_boundary/evaluator.py`, `run_system_replay`, `QuantAgent`, `system.py`, `ContractAndRiskTests`, `test_risk_boundary.py`, `SQLiteExecutionLedger`, `discipline/__init__.py`, `SQLiteExperienceStore`, `proposals.py`, `_context`, `evaluate_discipline`, `ExecutionInstruction`, `test_execution_boundary.py`, `MasterProposal`, `preflight.py`, `processor.py`, `ExecutionIntent`, `attribution.py`, `test_daily_reflection.py`, `execution_boundary/__init__.py`, `EntryGateway`, `trainer.py`, `test_weekly_reflection.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `run_system_replay()` connect `run_system_replay` to `agents/__init__.py`, `logging.py`, `default_shared_kernel_policy_set`, `load_replay_frame`, `canonical_hash`, `runtime/journal.py`, `system.py`, `RuntimeEvent`, `ToolResult`, `service.py`, `SQLiteExecutionLedger`, `initial_runtime_state`, `test_system_replay.py`, `timedelta`, `MetricScope`, `execution.py`, `SQLiteRuntimeJournal`, `SharedKernelPolicySet`, `position.py`, `replay_validation/__init__.py`, `ReplayClock`, `ExecutionIntent`, `Signal`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 222 inferred relationships involving `timedelta` (e.g. with `main()` and `_create_thesis()`) actually correct?**
  _`timedelta` has 222 INFERRED edges - model-reasoned connections that need verification._
- **Are the 83 inferred relationships involving `MetricScope` (e.g. with `_fixture()` and `_run()`) actually correct?**
  _`MetricScope` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Signal` (e.g. with `DisciplineOutcome` and `DisciplinePosition`) actually correct?**
  _`Signal` has 70 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `RuntimeEvent` (e.g. with `AccountState` and `BrokerConstraints`) actually correct?**
  _`RuntimeEvent` has 25 INFERRED edges - model-reasoned connections that need verification._