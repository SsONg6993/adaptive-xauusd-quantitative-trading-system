# Phase 5 local Quant experiment workflow

These commands are for the user to run after reviewing the Phase 5 branch. They do not place trades. Run them from the repository or Phase 5 worktree root with the project environment activated.

When reusing the clean parent checkout's virtual environment from the isolated worktree:

```powershell
$pythonExe = (Resolve-Path '..\..\.venv\Scripts\python.exe').Path
$env:PYTHONPATH = (Resolve-Path 'src').Path
```

After merging into `main`, an activated project environment can use `python` in place of `& $pythonExe`.

## Ordered local run plan

1. Inspect bounded MT5 history — LIGHT, CPU/broker terminal, run immediately. No artifact is written unless PowerShell output is redirected.

   ```powershell
   & $pythonExe data/inspect_mt5_history.py --symbol XAUUSD --bars 5000
   ```

2. Build a real one-year M5/M15/H1/H4 immutable dataset — HEAVY, CPU/broker terminal, run only after reviewing history coverage. Raw files go to `data/raw/mt5/xauusd-one-year/`; the immutable dataset goes to `datasets/generated/<DATASET_ID>/`.

   ```powershell
   & $pythonExe data/build_mt5_dataset.py --history-config configs/datasets/history/one_year.yaml --dataset-config configs/datasets/xauusd_m5.yaml --execute
   ```

   Substitute `six_months.yaml` for a smaller first build or `two_years.yaml` only after the one-year quality report is acceptable. The command omits the still-open bar on every timeframe.

3. Inspect the immutable dataset — LIGHT, CPU, run immediately after the build. Replace `DATASET_ID` with the printed ID.

   ```powershell
   $datasetPath = (Resolve-Path 'datasets/generated/DATASET_ID').Path
   & $pythonExe datasets/inspect_dataset.py --dataset-manifest "$datasetPath/dataset.manifest.json"
   ```

4. Majority baseline — LIGHT, CPU, run after dataset approval. Artifacts: `runtime/models/quant/` and `runtime/experiments/quant/`.

   ```powershell
   & $pythonExe training/quant/run_experiment.py --config configs/quant/experiments/majority.yaml --dataset $datasetPath
   ```

5. Prior-probability baseline — LIGHT, CPU, run with the majority baseline.

   ```powershell
   & $pythonExe training/quant/run_experiment.py --config configs/quant/experiments/prior.yaml --dataset $datasetPath
   ```

6. Logistic Regression — MEDIUM, CPU, run after both naive baselines.

   ```powershell
   & $pythonExe training/quant/run_experiment.py --config configs/quant/experiments/logistic.yaml --dataset $datasetPath
   ```

7. Random Forest — MEDIUM, CPU, run after reviewing Logistic calibration, stability, and coverage.

   ```powershell
   & $pythonExe training/quant/run_experiment.py --config configs/quant/experiments/random_forest.yaml --dataset $datasetPath
   ```

8. XGBoost CPU — HEAVY, CPU, run only if simpler baselines show credible development evidence.

   ```powershell
   & $pythonExe training/quant/run_experiment.py --config configs/quant/experiments/xgboost_cpu.yaml --dataset $datasetPath
   ```

9. XGBoost CUDA — HEAVY, GPU, run only when `scripts/check_compute.py` reports `xgboost.gpu_capable: true`.

   ```powershell
   & $pythonExe training/quant/run_experiment.py --config configs/quant/experiments/xgboost_cuda.yaml --dataset $datasetPath
   ```

10. LightGBM CPU — HEAVY, CPU, run only after reviewing simpler models.

    ```powershell
    & $pythonExe training/quant/run_experiment.py --config configs/quant/experiments/lightgbm_cpu.yaml --dataset $datasetPath
    ```

11. LightGBM GPU — HEAVY, GPU/OpenCL on Windows, run only when `scripts/check_compute.py` reports `lightgbm.gpu_capable: true`. Do not assume the ordinary wheel supports GPU.

    ```powershell
    & $pythonExe training/quant/run_experiment.py --config configs/quant/experiments/lightgbm_gpu.yaml --dataset $datasetPath
    ```

12. Compare completed runs — LIGHT, CPU, run after at least majority, prior, and Logistic complete. Replace each path with a printed `qdev-*` directory. Output: `runtime/experiments/quant/comparison.json`.

    ```powershell
    & $pythonExe training/quant/compare_runs.py --runs runtime/experiments/quant/qdev-majority-RUN_ID runtime/experiments/quant/qdev-prior-RUN_ID runtime/experiments/quant/qdev-logistic-RUN_ID --output runtime/experiments/quant/comparison.json
    ```

13. Limited walk-forward — HEAVY, CPU, run only for a promising reviewed model. Output: `runtime/experiments/quant/walk_forward/`. Every fold independently fits preprocessing, selection, model, and calibration and stops before immutable final OOS.

    ```powershell
    & $pythonExe training/quant/run_walk_forward.py --config configs/quant/experiments/logistic.yaml --policy configs/quant/walk_forward/limited.yaml --dataset $datasetPath --output runtime/experiments/quant/walk_forward/logistic
    ```

14. Feature-group ablation — HEAVY, CPU, run only on a walk-forward finalist. Output: `runtime/experiments/quant/ablations/`.

    ```powershell
    & $pythonExe training/quant/run_ablation.py --config configs/quant/experiments/logistic.yaml --ablation configs/quant/ablations/feature_groups.yaml --policy configs/quant/walk_forward/limited.yaml --dataset $datasetPath --output runtime/experiments/quant/ablations/logistic
    ```

15. Optuna — HEAVY, CPU by the supplied experiment config, run only after baseline, walk-forward, and ablation review. Omit `--execute` first to inspect the protected study plan. Output: `runtime/experiments/quant/tuning/xgboost/`.

    ```powershell
    & $pythonExe training/quant/run_optuna.py --tuning configs/quant/tuning/xgboost.yaml --experiment configs/quant/experiments/xgboost_cpu.yaml --policy configs/quant/walk_forward/limited.yaml --dataset $datasetPath --output runtime/experiments/quant/tuning/xgboost
    & $pythonExe training/quant/run_optuna.py --tuning configs/quant/tuning/xgboost.yaml --experiment configs/quant/experiments/xgboost_cpu.yaml --policy configs/quant/walk_forward/limited.yaml --dataset $datasetPath --output runtime/experiments/quant/tuning/xgboost --execute
    ```

Before any GPU command, run:

```powershell
& $pythonExe scripts/check_compute.py
```

## Returning results for review

Do not send broker credentials or the full generated dataset. Return the relevant `development.manifest.json`, `metrics.json`, `run_summary.json`, `calibration.json`, `stability.json`, `feature_importance.json`, and comparison/walk-forward summaries from `runtime/experiments/quant/`. Keep `predictions.parquet` locally unless row-level diagnosis is needed. Codex can compare completed artifacts without retraining.

**CODEX HAS NOT RUN THE REAL TRAINING. THESE COMMANDS ARE FOR THE USER TO RUN LOCALLY.**
