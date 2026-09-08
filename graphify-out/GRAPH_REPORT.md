# Graph Report - Adaptive XAUUSD Quantitative Trading System  (2026-09-08)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 579 nodes · 1311 edges · 20 communities (16 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 121 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `32132dd1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 17
- Community 18
- Community 19

## God Nodes (most connected - your core abstractions)
1. `LabelDefinition` - 30 edges
2. `train_quant_model()` - 27 edges
3. `default_registry()` - 25 edges
4. `assemble_dataset()` - 22 edges
5. `generate_labels()` - 21 edges
6. `canonical_hash()` - 17 edges
7. `load_training_dataset()` - 16 edges
8. `ModelManifest` - 15 edges
9. `QuantAgent` - 15 edges
10. `SplitManifest` - 14 edges

## Surprising Connections (you probably didn't know these)
- `test_manifest_is_reproducible_and_complete()` --calls--> `default_registry()`  [INFERRED]
  tests/test_sessions_manifest_analysis.py → src/axq/features/registry.py
- `dataset_dir()` --calls--> `RowPolicy`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/datasets/config.py
- `dataset_dir()` --calls--> `SplitPolicy`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/datasets/config.py
- `dataset_dir()` --calls--> `LabelDefinition`  [INFERRED]
  tests/test_quant_phase4.py → src/axq/labels/base.py
- `main()` --uses--> `Database`  [INFERRED]
  scripts/init_db.py → src/axq/database.py

## Import Cycles
- None detected.

## Communities (20 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (54): assemble_dataset(), dataframe_hash(), DatasetBuildResult, Any, DataFrame, Path, Leakage-safe Phase 3 dataset assembly., _validate_source_frames() (+46 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (48): compare_label_definitions(), DataFrame, Label balance and definition-sensitivity reporting; never resamples data., BarrierMode, CollisionPolicy, EntryReference, LabelDefinition, LabelKind (+40 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (45): ModelRecord, BaseModel, Path, Immutable model metadata; activation is data, not a source-code edit., dump_artifact(), file_hash(), load_artifact(), Any (+37 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (38): Compatibility entry point; implementation lives in the installable axq package., breakout_features(), Any, DataFrame, Donchian and breakout-state candidates using only past/current bars., Feature functions and registry., FeatureManifestEntry, BaseModel (+30 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (39): Architecture, CalibrationConfig, Device, FeatureSelectionConfig, HoldPolicyConfig, load_quant_config(), PreprocessingConfig, BaseModel (+31 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (43): skipif, aroon(), atr(), cci(), directional_movement(), money_flow_index(), DataFrame, Series (+35 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (27): main(), main(), main(), clean_candles(), DataFrame, Normalize types/order and deterministically keep the last duplicate bar., DataFrame, Leakage-safe multi-timeframe alignment. (+19 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (23): field_validator, load_artifact_json(), Any, datetime, ndarray, Path, Series, QuantAgent (+15 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (26): FeatureManifest, Path, Canonical feature-manifest models., load_training_dataset(), _parse_manifest(), Any, DataFrame, Path (+18 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (27): correlation_matrix(), duplicate_features(), feature_group_ablations(), feature_stability(), FeatureQuality, highly_correlated_features(), missing_value_rate(), _optional_float() (+19 more)

### Community 10 - "Community 10"
Cohesion: 0.16
Nodes (17): CompletedProcess, main(), _git_identity(), main(), _run_git(), AppConfig, DatabaseConfig, FeatureConfig (+9 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (9): main(), Database, Connection, Path, Small SQLite adapter with transactional migrations and PostgreSQL-friendly SQL…, DatasetManifest, BaseModel, Path (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.27
Nodes (5): ExperimentTracker, Any, Connection, Path, Lightweight local SQLite experiment audit log.

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (8): Logger, LogRecord, configure_logging(), event(), JsonFormatter, Any, Path, Structured JSON-lines logging with correlation context.

### Community 14 - "Community 14"
Cohesion: 0.48
Nodes (6): download(), main(), DataFrame, datetime, Download bounded historical bars from a locally running MetaTrader 5 terminal., _utc()

### Community 15 - "Community 15"
Cohesion: 0.50
Nodes (3): MissingValueReason, StrEnum, Feature availability and missing-value policy contracts.

## Knowledge Gaps
- **1 isolated node(s):** `adaptive-xauusd-trader`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 156 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `default_registry()` connect `Community 3` to `Community 0`, `Community 5`, `Community 6`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.191) - this node is a cross-community bridge._
- **Why does `assemble_dataset()` connect `Community 0` to `Community 1`, `Community 3`, `Community 4`, `Community 6`, `Community 10`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `FeatureManifest` connect `Community 8` to `Community 0`, `Community 3`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `LabelDefinition` (e.g. with `compare_label_definitions()` and `direction_labels()`) actually correct?**
  _`LabelDefinition` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `train_quant_model()` (e.g. with `ProbabilityCalibrator` and `QuantTrainingConfig`) actually correct?**
  _`train_quant_model()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `default_registry()` (e.g. with `main()` and `breakout_features()`) actually correct?**
  _`default_registry()` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `assemble_dataset()` (e.g. with `main()` and `SplitPolicy`) actually correct?**
  _`assemble_dataset()` has 5 INFERRED edges - model-reasoned connections that need verification._