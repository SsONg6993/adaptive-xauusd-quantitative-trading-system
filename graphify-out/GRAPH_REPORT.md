# Graph Report - phase-5-quant-development  (2026-09-09)

## Corpus Check
- 141 files · ~40,635 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 942 nodes · 2053 edges · 68 communities (52 shown, 15 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 173 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bf896ff0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_datasets_phase3.py
- LabelDefinition
- LocalModelRegistry
- axq/features/registry.py
- quant/config.py
- indicators.py
- test_foundation.py
- inference.py
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
- assemble_dataset
- System architecture (Phase 0-5 baseline)
- canonical_hash
- folds.py
- SplitManifest
- Architecture decision log
- FeatureManifest
- README.md
- models.py
- session_features
- evaluate_predictions
- trainer.py
- build_mt5_dataset.py
- Global Constraints
- FrozenPreprocessor
- Phase 0-5 runbook
- default_registry
- Phase 2 feature contract
- Phase 5 Quant Model-Development Design
- Project status
- datasets/preprocessing.py
- multi_timeframe_features
- ProbabilityCalibrator
- Indicator and quantitative-feature candidate research
- Adaptive XAUUSD Multi-Agent Trading System
- features/preprocessing.py
- test_quant_phase4.py
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

## God Nodes (most connected - your core abstractions)
1. `LabelDefinition` - 31 edges
2. `train_quant_model()` - 29 edges
3. `default_registry()` - 25 edges
4. `canonical_hash()` - 25 edges
5. `assemble_dataset()` - 24 edges
6. `run_experiment()` - 24 edges
7. `load_training_dataset()` - 22 edges
8. `generate_labels()` - 21 edges
9. `SplitManifest` - 19 edges
10. `run_walk_forward()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_split_chronology_purge_and_embargo()` --calls--> `chronological_split()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_walk_forward_split_definitions_are_deterministic()` --calls--> `walk_forward_splits()`  [INFERRED]
  tests/test_datasets_phase3.py → src/axq/datasets/splits.py
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `test_majority_and_prior_baselines()` --uses--> `MajorityClassifier`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/quant/models.py
- `main()` --calls--> `quality_report()`  [INFERRED]
  data/build_features.py → src/axq/features/analysis.py

## Import Cycles
- None detected.

## Communities (68 total, 15 thin omitted)

### Community 0 - "test_datasets_phase3.py"
Cohesion: 0.21
Nodes (14): build(), candles(), definition(), DataFrame, Path, RecordingTransformer, test_dataset_reproducibility_config_identity_and_separation(), test_duplicate_timestamp_rejected() (+6 more)

### Community 1 - "LabelDefinition"
Cohesion: 0.09
Nodes (51): compare_label_definitions(), label_balance(), Any, DataFrame, Series, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, CollisionPolicy (+43 more)

### Community 2 - "LocalModelRegistry"
Cohesion: 0.17
Nodes (12): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., LocalModelRegistry, ModelState, Any, BaseModel (+4 more)

### Community 3 - "axq/features/registry.py"
Cohesion: 0.21
Nodes (9): Compatibility entry point; implementation lives in the installable axq package., FeatureDefinition, FeatureRegistry, _integer(), _output_lookback(), Any, DataFrame, Explicit, versioned feature registration and reproducible manifests. (+1 more)

### Community 4 - "quant/config.py"
Cohesion: 0.17
Nodes (14): CalibrationConfig, Device, HoldPolicyConfig, load_quant_config(), BaseModel, Path, QuantTrainingConfig, Strict, hashable configuration for Quant Agent training. (+6 more)

### Community 5 - "indicators.py"
Cohesion: 0.11
Nodes (43): skipif, aroon(), atr(), cci(), directional_movement(), money_flow_index(), DataFrame, Series (+35 more)

### Community 6 - "test_foundation.py"
Cohesion: 0.12
Nodes (15): main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., calculate_volume_lots(), Deterministic pre-trade veto and broker-specification position sizing., Size from broker specs and round down; return zero when minimum volume is…, RiskContext (+7 more)

### Community 7 - "inference.py"
Cohesion: 0.08
Nodes (37): field_validator, dump_artifact(), file_hash(), load_artifact(), Any, Path, Trusted-local model artifact persistence and integrity verification., verify_run() (+29 more)

### Community 8 - "development/config.py"
Cohesion: 0.05
Nodes (65): Architecture, StrEnum, load_training_dataset(), _parse_manifest(), Any, DataFrame, Path, Strict loading and identity verification for immutable Phase 3 datasets. (+57 more)

### Community 9 - "features/analysis.py"
Cohesion: 0.25
Nodes (17): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+9 more)

### Community 10 - "axq/config.py"
Cohesion: 0.07
Nodes (26): CompletedProcess, main(), _git_identity(), main(), _run_git(), main(), AppConfig, DatabaseConfig (+18 more)

### Community 11 - "runner.py"
Cohesion: 0.06
Nodes (56): file_hash(), Any, Path, Atomic, hash-verified Phase 5 development reports., verify_development_run(), write_development_manifest(), write_json_atomic(), write_text_atomic() (+48 more)

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
Cohesion: 0.18
Nodes (12): main(), main(), DataFrame, Leakage-safe multi-timeframe alignment., Attach bars only when their UTC close time is at/before the base bar's UTC…, synchronize_completed_bars(), timeframe_delta(), DataFrame (+4 more)

### Community 23 - "assemble_dataset"
Cohesion: 0.22
Nodes (15): assemble_dataset(), dataframe_hash(), DatasetBuildResult, Any, DataFrame, Path, _validate_source_frames(), write_dataset() (+7 more)

### Community 24 - "System architecture (Phase 0-5 baseline)"
Cohesion: 0.12
Nodes (16): Data pipeline and synchronization, Database architecture, Dataset and label versioning, Failure states, Feature layer, IPC decision, Model registry, Python and MT5 boundaries (+8 more)

### Community 25 - "canonical_hash"
Cohesion: 0.14
Nodes (7): DatasetManifest, BaseModel, Path, Immutable, content-derived Phase 3 dataset contract., canonical_hash(), Any, Content-derived dataset and configuration identities.

### Community 26 - "folds.py"
Cohesion: 0.26
Nodes (13): _aggregate_fold_metrics(), completed_fold_summary(), DevelopmentFoldResult, fold_identity(), Any, DataFrame, Path, Fresh-state, fold-local development evaluation before immutable final OOS. (+5 more)

### Community 27 - "SplitManifest"
Cohesion: 0.23
Nodes (11): dataset_quality_report(), Any, DataFrame, chronological_split(), IndexRange, BaseModel, Path, Deterministic chronological, purged, embargoed split definitions. (+3 more)

### Community 28 - "Architecture decision log"
Cohesion: 0.14
Nodes (13): 2026-09-08 — Calibrated three-way Quant output, 2026-09-08 — Chronological evaluation, 2026-09-08 — Conservative label ambiguity, 2026-09-08 — Controlled future learning and reporting, 2026-09-08 — Explicit model lifecycle, 2026-09-08 — Independent XAUUSD system, 2026-09-08 — Local-first operation, 2026-09-08 — Point-in-time market data (+5 more)

### Community 29 - "FeatureManifest"
Cohesion: 0.22
Nodes (9): Feature functions and registry., FeatureManifest, FeatureManifestEntry, BaseModel, Path, Canonical feature-manifest models., feature_ablation_variants(), Manifest-bound feature ablation plans; execution remains fold-local. (+1 more)

### Community 30 - "README.md"
Cohesion: 0.24
Nodes (4): Model registry and promotion contract, Phase 5 development layer, Quant model training, Quant Agent contract

### Community 31 - "models.py"
Cohesion: 0.22
Nodes (7): build_model(), MajorityClassifier, ProbabilisticClassifier, Any, ndarray, Protocol, Simple baselines and lazy optional model adapters.

### Community 32 - "session_features"
Cohesion: 0.23
Nodes (10): _local_window(), Any, DataFrame, Series, DST-aware session features. Source timestamps are interpreted as UTC., session_features(), test_london_and_new_york_dst_transitions(), test_manifest_is_reproducible_and_complete() (+2 more)

### Community 33 - "evaluate_predictions"
Cohesion: 0.23
Nodes (11): _confidence_bucket(), evaluate_predictions(), label_to_signal(), Any, DataFrame, ndarray, Series, Classification, calibration, trading-context, and coverage diagnostics. (+3 more)

### Community 34 - "trainer.py"
Cohesion: 0.29
Nodes (11): _git_identity(), _metadata(), metrics_json(), _model_explanation(), _period(), Any, DataFrame, Leakage-safe Quant Agent training orchestration. (+3 more)

### Community 35 - "build_mt5_dataset.py"
Cohesion: 0.24
Nodes (9): HistoryBuildConfig, _load(), main(), _mapping(), Any, BaseModel, Path, Explicit user-run MT5 multi-timeframe download and immutable dataset build. (+1 more)

### Community 36 - "Global Constraints"
Cohesion: 0.18
Nodes (10): Global Constraints, Phase 5 Quant Model Development Implementation Plan, Task 1: Strict development configuration and identities, Task 2: History and compute inspection, Task 3: Diagnostics, drift, and Challenger evidence, Task 4: Fold-local walk-forward and ablation planning, Task 5: Experiment orchestration, artifacts, and comparison, Task 6: User-facing configs and CLIs (+2 more)

### Community 37 - "FrozenPreprocessor"
Cohesion: 0.38
Nodes (7): FeatureSelectionConfig, PreprocessingConfig, FrozenPreprocessor, DataFrame, ndarray, Training-only feature selection, imputation, and scaling., test_training_only_preprocessing_and_nan_inf_policy()

### Community 38 - "Phase 0-5 runbook"
Cohesion: 0.22
Nodes (9): Data lifecycle, Operational checks, Phase 0-5 runbook, Phase 2 lightweight verification, Phase 3 dataset lifecycle, Phase 4 Quant Agent lifecycle, Phase 5 local model development, Readiness gates for Phase 3 (+1 more)

### Community 39 - "default_registry"
Cohesion: 0.44
Nodes (8): default_registry(), candles(), DataFrame, test_labels_are_not_feature_inputs(), test_multi_timeframe_future_bar_and_all_boundaries(), test_prefix_invariance_and_future_candle_mutation(), test_rolling_window_is_right_aligned(), test_swing_confirmation_is_delayed_and_not_backdated()

### Community 40 - "Phase 2 feature contract"
Cohesion: 0.25
Nodes (8): Implemented configurable candidate families, Manifest and diagnostics, Missing-value policy, Multi-timeframe and UTC rules, Phase 2 feature contract, Point-in-time invariant, Swing and structure timing, Warm-up policy

### Community 41 - "Phase 5 Quant Model-Development Design"
Cohesion: 0.25
Nodes (7): Architectural boundary, Artifacts and recovery, Components, Data and control flow, Phase 5 Quant Model-Development Design, Purpose, Safety constraints

### Community 42 - "Project status"
Cohesion: 0.25
Nodes (7): Current architecture, Current phase status, Important risks, Project status, Roadmap, Verified state, Working principle and next task

### Community 43 - "datasets/preprocessing.py"
Cohesion: 0.36
Nodes (6): fit_on_training_only(), FitTransformComponent, Any, DataFrame, Protocol, Guards that force future preprocessing components to fit on training rows only.

### Community 44 - "multi_timeframe_features"
Cohesion: 0.21
Nodes (6): multi_timeframe_features(), Any, DataFrame, price_action_features(), Any, DataFrame

### Community 45 - "ProbabilityCalibrator"
Cohesion: 0.32
Nodes (5): ProbabilityCalibrator, ndarray, Validation-only probability calibration without OOS access., parametrize, test_calibration_pipeline()

### Community 46 - "Indicator and quantitative-feature candidate research"
Cohesion: 0.29
Nodes (6): Candidate matrix, Indicator and quantitative-feature candidate research, Phase 2 implementation and formula verification, Redundancy and experiment plan, Research stance, XAUUSD-specific priorities

### Community 47 - "Adaptive XAUUSD Multi-Agent Trading System"
Cohesion: 0.29
Nodes (7): Adaptive XAUUSD Multi-Agent Trading System, Current capabilities, Download and validate a small sample, Lightweight verification, Non-negotiable development rules, Repository map, Setup (Windows PowerShell)

### Community 48 - "features/preprocessing.py"
Cohesion: 0.38
Nodes (5): fit_standardizer(), FittedStandardizer, DataFrame, Small fit-boundary scaffold for leakage-safe downstream preprocessing., test_scaler_fit_boundary_scaffolding()

### Community 49 - "test_quant_phase4.py"
Cohesion: 0.48
Nodes (6): config(), Path, test_dataset_manifest_compatibility_and_exact_feature_order(), test_logistic_tiny_fit_serialization_inference_and_oos_scope(), test_majority_and_prior_baselines(), test_model_registry_requires_explicit_promotion_evidence()

### Community 50 - "Phase 3 dataset contract"
Cohesion: 0.33
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

## Knowledge Gaps
- **102 isolated node(s):** `adaptive-xauusd-trader`, `Repository-start workflow`, `Graphify`, `Current capabilities`, `Setup (Windows PowerShell)` (+97 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 317 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `default_registry()` connect `default_registry` to `session_features`, `axq/features/registry.py`, `indicators.py`, `test_foundation.py`, `axq/config.py`, `multi_timeframe_features`, `breakout_features`, `builder.py`, `assemble_dataset`, `statistical_features`, `FeatureManifest`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `assemble_dataset()` connect `assemble_dataset` to `test_datasets_phase3.py`, `LabelDefinition`, `build_mt5_dataset.py`, `default_registry`, `axq/config.py`, `runner.py`, `builder.py`, `canonical_hash`, `SplitManifest`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `FeatureManifest` connect `FeatureManifest` to `development/config.py`, `axq/features/registry.py`, `builder.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `LabelDefinition` (e.g. with `compare_label_definitions()` and `direction_labels()`) actually correct?**
  _`LabelDefinition` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `train_quant_model()` (e.g. with `ProbabilityCalibrator` and `QuantTrainingConfig`) actually correct?**
  _`train_quant_model()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `default_registry()` (e.g. with `main()` and `breakout_features()`) actually correct?**
  _`default_registry()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `assemble_dataset()` (e.g. with `main()` and `main()`) actually correct?**
  _`assemble_dataset()` has 7 INFERRED edges - model-reasoned connections that need verification._