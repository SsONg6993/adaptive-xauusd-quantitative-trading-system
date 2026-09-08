# Phase 5 Quant Model Development Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a leakage-safe, deterministic, resumable local Quant experiment and evaluation workflow without running serious training.

**Architecture:** Add a focused `axq.quant.development` package around the immutable Phase 3 loader and Phase 4 model components. Keep final OOS evaluation-only, fit all learned state independently inside each walk-forward fold, and store content-addressed auditable artifacts under ignored runtime paths.

**Tech Stack:** Python 3.12, Pydantic 2, pandas, NumPy, scikit-learn, optional MetaTrader5/XGBoost/LightGBM/Optuna, pytest, Ruff, mypy.

**Spec:** `docs/phase5_quant_development.md`

## Global Constraints

- Do not run serious training, a large dataset build, Optuna, a full walk-forward suite, GPU-heavy work, a backtest, or Phase 6.
- Final OOS is evaluation-only and cannot drive tuning, feature selection, calibration, threshold selection, or model choice.
- Every walk-forward fold independently fits preprocessing, feature selection, model, and calibration.
- Experiments are deterministic, content-addressed, resumable, and auditable.
- Fold models are evidence only and are not automatically registered.
- Keep the clean `main` checkout untouched and work on `codex/phase-5-quant-development`.

---

### Task 1: Strict development configuration and identities

**Files:**
- Create: `src/axq/quant/development/__init__.py`
- Create: `src/axq/quant/development/config.py`
- Create: `src/axq/quant/development/state.py`
- Test: `tests/test_quant_development_config.py`

**Interfaces:**
- Produces `ExperimentConfig`, `SuiteConfig`, `WalkForwardConfig`, `AblationConfig`, `TuningConfig`, `load_experiment_config()`, `development_run_id()`, and atomic `RunStateStore`.
- `TuningConfig.objective_scope` accepts only `validation` or `walk_forward_validation`.

- [ ] Write tests proving strict parsing, deterministic IDs, OOS-objective rejection, atomic state transitions, and interrupted-run recovery.
- [ ] Run `pytest tests/test_quant_development_config.py -v` and confirm failures are caused by the missing package.
- [ ] Implement the minimal strict models, canonical identity generation, and state store.
- [ ] Re-run the focused tests and retain a green result.

### Task 2: History and compute inspection

**Files:**
- Create: `src/axq/quant/development/history.py`
- Create: `src/axq/quant/development/compute.py`
- Create: `data/inspect_mt5_history.py`
- Create: `scripts/check_compute.py`
- Test: `tests/test_quant_development_inspection.py`

**Interfaces:**
- Produces `inspect_history_frames()` for deterministic broker-frame checks and `compute_report()` with injectable command/module probes.
- CLIs serialize reports and never download large history or fit a model.

- [ ] Write tests with hand-built OHLC fixtures for earliest/latest bars, gaps, duplicates, zero volume, abnormal spread, UTC/completed-bar semantics, and device fallback.
- [ ] Run the focused tests and confirm expected missing-interface failures.
- [ ] Implement pure inspection functions, then thin optional-MT5 and compute CLIs.
- [ ] Re-run focused tests and CLI `--help` smoke checks.

### Task 3: Diagnostics, drift, and Challenger evidence

**Files:**
- Create: `src/axq/quant/development/diagnostics.py`
- Create: `src/axq/quant/development/drift.py`
- Create: `src/axq/quant/development/challenger.py`
- Test: `tests/test_quant_development_diagnostics.py`

**Interfaces:**
- Produces threshold, calibration, temporal/session, trade-metadata, opportunity-utilization, overfitting, and stability reports.
- Produces PSI/KS and distribution drift reports plus `evaluate_challenger_evidence()` without registry mutation.

- [ ] Write literal-expectation tests for coverage, segmentation, calibration bins, PSI/KS edge cases, collapse flags, and unmet Challenger requirements.
- [ ] Run focused tests and confirm missing-interface failures.
- [ ] Implement deterministic dataframe/array diagnostics with JSON-safe outputs.
- [ ] Re-run focused tests.

### Task 4: Fold-local walk-forward and ablation planning

**Files:**
- Create: `src/axq/quant/development/folds.py`
- Create: `src/axq/quant/development/ablation.py`
- Test: `tests/test_quant_development_folds.py`

**Interfaces:**
- Produces `run_development_fold()` and `run_walk_forward()` using fresh Phase 4 components per fold.
- Produces group and single-feature ablation variants from manifest groups; no global OOS-informed selection.

- [ ] Write tests using two tiny folds that prove fit-row isolation, fresh object identities, calibration-on-validation only, OOS exclusion from development folds, completed-fold skipping, and ablation membership.
- [ ] Run focused tests and confirm missing-interface failures.
- [ ] Implement fold slicing, local fitting/evaluation, per-fold artifacts, resume verification, aggregation, and ablation planning.
- [ ] Re-run focused tests.

### Task 5: Experiment orchestration, artifacts, and comparison

**Files:**
- Create: `src/axq/quant/development/artifacts.py`
- Create: `src/axq/quant/development/runner.py`
- Create: `src/axq/quant/development/suite.py`
- Create: `src/axq/quant/development/comparison.py`
- Test: `tests/test_quant_development_runner.py`

**Interfaces:**
- Produces dry-run plans, single-run execution, resumable suites, required reports, run discovery, and comparison rows.
- Existing Phase 4 model registration remains limited to ordinary completed model runs; fold artifacts bypass it.

- [ ] Write tests for dry-run no-fit behavior, deterministic paths, required artifact serialization, fail-one-suite-member continuation, resume/skip behavior, comparison output, and artifact identity rejection.
- [ ] Run focused tests and confirm missing-interface failures.
- [ ] Implement orchestration and report writers, delegating normal model fitting to Phase 4.
- [ ] Re-run focused tests.

### Task 6: User-facing configs and CLIs

**Files:**
- Create: `configs/quant/experiments/*.yaml`
- Create: `configs/quant/suites/baseline_suite.yaml`
- Create: `configs/quant/walk_forward/limited.yaml`
- Create: `configs/quant/ablations/feature_groups.yaml`
- Create: `configs/quant/tuning/{random_forest,xgboost,lightgbm}.yaml`
- Create: `configs/datasets/history/{six_months,one_year,two_years}.yaml`
- Create: `training/quant/run_experiment.py`
- Create: `training/quant/run_suite.py`
- Create: `training/quant/run_walk_forward.py`
- Create: `training/quant/run_ablation.py`
- Create: `training/quant/compare_runs.py`
- Create: `training/quant/prepare_optuna.py`
- Test: `tests/test_quant_development_cli.py`

**Interfaces:**
- All costly CLIs support `--dry-run`; Optuna preparation validates/writes a study plan but does not execute a study by default.

- [ ] Write subprocess-level tests for config loading, dry-run output, compare output, CUDA fallback, and OOS-tuning refusal.
- [ ] Run focused tests and confirm missing-script failures.
- [ ] Add conservative configs and thin CLIs over the development package.
- [ ] Re-run focused tests and all CLI `--help`/config-validation smoke checks.

### Task 7: Documentation and context

**Files:**
- Modify: `README.md`
- Modify: `docs/model_training.md`
- Modify: `docs/quant_agent.md`
- Modify: `docs/runbook.md`
- Modify: `docs/project_status.md`
- Modify: `docs/decision_log.md`

**Interfaces:**
- Documents exact PowerShell commands, compute classes, artifact locations, protected-OOS policy, return-to-Codex workflow, and no-real-training statement.

- [ ] Update documentation to match executable CLI names and defaults.
- [ ] Record the separate development-layer and protected-OOS decisions.
- [ ] Review every documented command against `--help` output.

### Task 8: Full lightweight verification and Graphify refresh

**Files:**
- Modify: `graphify-out/graph.json`
- Modify: `graphify-out/GRAPH_REPORT.md`

**Interfaces:**
- Produces fresh repository-wide validation evidence and an incrementally updated source graph.

- [ ] Run `python -m pytest` using the shared project interpreter.
- [ ] Run `python -m ruff check .`.
- [ ] Run `python -m mypy src/axq`.
- [ ] Run `python -m pip check`.
- [ ] Run only tiny dry-run, serialization, and compute-capability checks.
- [ ] Run the documented incremental `graphify update .` workflow and verify graph freshness.
- [ ] Inspect `git diff --check`, `git status`, ignored runtime output, and the clean parent `main` checkout.
