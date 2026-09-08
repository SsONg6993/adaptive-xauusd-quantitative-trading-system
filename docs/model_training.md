# Quant model training

Phase 4 consumes an immutable Phase 3 dataset directory. Loading fails if the directory, dataset,
feature, label, or split identity is inconsistent; if content, schema, column order, chronology, or
row count differs; if timestamps duplicate; or if feature/target separation is broken.

The exact first split-manifest fold is enforced. Imputation, scaling, variance selection, and
correlation pruning fit on `TRAIN` only. The model fits on `TRAIN`; sigmoid (Platt-style) or isotonic
calibration fits on `VALIDATION`; only the frozen pipeline can evaluate `OOS`. No random split,
SMOTE, OOS calibration, or target-distribution mutation is available. Class weighting is either
`none` or `balanced` where supported.

Supported architectures are majority-class, prior-probability, logistic regression, Random Forest,
XGBoost, and LightGBM. XGBoost and LightGBM are lazy optional dependencies. Tree configs avoid
scaling. `device: auto|cpu|cuda` records availability and selection; unsupported/unavailable CUDA
falls back to CPU and records the reason. Library-specific GPU builds remain the user's
responsibility.

Every run writes a model, preprocessor, calibrator, selected feature list, exact config, metrics,
confusion matrices, class mapping, explanations, run summary, and model manifest. The manifest binds
dataset/feature/label/split IDs, ordered selection, configuration hash, Git commit, periods, seed,
hyperparameters, device, metrics, paths, and hashes. The content-derived model ID excludes creation
time and metric payload so identical reviewed inputs reproduce identity where practical.

Metrics cover accuracy, balanced accuracy, macro precision/recall/F1, confusion matrix, log loss,
multiclass Brier score, ROC-AUC/PR-AUC where valid, expected calibration error, class/prediction and
confidence distributions, BUY/SELL/HOLD coverage, opportunity utilization, confidence buckets, and
future-return/MFE/MAE summaries when label metadata exists. They are diagnostics, not evidence of
profitability.

Install CPU training support separately:

```powershell
python -m pip install -e ".[dev,dataset,ml]"
```

Run commands only after replacing `DATASET_ID` or supplying `--dataset`:

```powershell
python training/quant/train.py --config configs/quant/logistic.yaml --dataset datasets/generated/DATASET_ID
python training/quant/evaluate.py --run runtime/models/quant/RUN_ID --dataset datasets/generated/DATASET_ID --split oos
```

Phase 4 validation used only a 96-row broker sample and tiny synthetic fixtures.

## Phase 5 development layer

`axq.quant.development` surrounds rather than replaces the frozen Phase 4 path. A normal experiment
validates the immutable dataset, derives a content-addressed development run, delegates the one-model
fit to Phase 4, and writes extended prediction, calibration, stability, threshold, feature-importance,
and audit artifacts under ignored `runtime/experiments/quant/`.

Walk-forward and ablation use fresh preprocessors, selectors, estimators, and calibrators for every
fold. Their generation boundary is the start of immutable final OOS, so final OOS rows and labels
cannot enter selection. Fold models are evidence artifacts and never enter the lifecycle registry.
Optuna objectives use these development folds and structurally reject OOS scope.

Threshold sweeps are descriptive and never select a profitability threshold. Drift reports do not
retrain. Challenger evidence does not promote. See [Phase 5 local runs](phase5_local_runs.md) for the
ordered user-run commands and output locations.
