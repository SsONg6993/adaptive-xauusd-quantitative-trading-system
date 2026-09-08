# Phase 5 Quant Model-Development Design

## Purpose

Phase 5 adds a local, reproducible model-development and evaluation layer around the immutable Phase 3 dataset and Phase 4 Quant Agent contracts. It prepares commands and artifacts for serious experiments that the user will run locally; repository validation is limited to deterministic tiny fixtures and dry runs.

## Architectural boundary

The production `axq.quant.trainer.train_quant_model()` path remains focused on one manifest-bound TRAIN/VALIDATION/OOS run. Phase 5 lives in `axq.quant.development` and composes the existing dataset loader, frozen preprocessor, model factory, probability calibrator, evaluator, manifests, and registry without turning the Phase 4 trainer into an experiment monolith.

Final OOS is evaluation-only. Development selection and tuning APIs accept TRAIN/VALIDATION or explicitly generated development folds and reject an OOS objective or OOS-selected configuration. Walk-forward folds create fresh preprocessing, feature-selection, model, and calibration objects. Fold outputs are evidence artifacts and are never registered as Champion or Challenger models.

## Components

- Strict experiment and suite configuration models with canonical identities.
- Read-only MT5 history inspection and local compute-capability reporting.
- Single-run orchestration with validation, dry-run planning, atomic status, content-addressed paths, and machine-readable reports.
- Resumable suite and walk-forward orchestration that preserves completed work and isolates failures.
- Fold-local ablation and feature-reduction plans using Phase 2 feature analysis.
- Calibration, HOLD-threshold, opportunity-utilization, temporal/session, trade-metadata, overfitting, and stability diagnostics.
- Drift interfaces for PSI, KS, feature/prediction/confidence/calibration/performance/coverage comparisons.
- Challenger evidence evaluation that reports unmet requirements but never promotes a model.
- Run discovery and comparison without retraining.
- Optuna preparation whose objective split is structurally limited to validation or walk-forward validation.

## Data and control flow

1. A dataset path is resolved from a strict config and verified with `load_training_dataset()`.
2. A dry run validates identities, configuration, dependency/device support, split policy, and output locations without fitting.
3. A real user-run experiment obtains a content-addressed run ID and writes `RUNNING` state atomically.
4. Training delegates to the established Phase 4 path for ordinary frozen-split runs, then Phase 5 derives predictions and extended reports from the saved immutable model.
5. Walk-forward development constructs deterministic folds from the development region only. Each fold fits all learned components locally, writes an independent fold result, and can be skipped after artifact verification.
6. Suite aggregation and run comparison read completed artifacts only.

## Artifacts and recovery

Generated output stays below Git-ignored `runtime/experiments/quant/` and `runtime/models/quant/`. Each run records canonical config, dataset/feature/label/split identities, Git identity, device resolution, timestamps in UTC, status, and hashes. Status and JSON reports are written via temporary siblings followed by atomic replacement. A completed run/fold is reused only when its identity and required artifacts verify; failed or interrupted work retains completed fold outputs.

Expected reports include `metrics.json`, `predictions.parquet` (or a clearly reported CSV fallback when Parquet support is unavailable), `confidence_buckets.csv`, `feature_importance.json`, `calibration.json`, `stability.json`, `run_summary.json`, `model_manifest.json`, and `report.md`.

## Safety constraints

- OOS is never a tuning, feature-selection, calibration, threshold-selection, or model-choice input.
- Threshold output is descriptive; no profitability optimization or automatic choice is performed.
- Drift output is diagnostic; no autonomous retraining is performed.
- Challenger acceptance output is advisory; no registry transition occurs.
- GPU checks do not install frameworks or claim capability without a library/device probe.
- Dataset history inspection does not place trades and does not automatically download large history.
- No Phase 6 agents, scheduling, live execution, backtesting, or profitability claims are introduced.
