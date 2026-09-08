# Phase 3 dataset contract

## Reproducibility and separation

Each immutable dataset records its deterministic ID, source-data hash, configuration hash, feature
and label manifest IDs, split manifest ID, Git commit, UTC period, decision convention, ordered
feature/target/metadata allowlists, timeframes, row counts, and storage format. Creation time is
excluded from identity. Changing source content, features, labels, split policy, configuration, or
Git commit changes the ID.

Clean builds record the exact Git commit. Development smoke builds from a dirty tree append a
deterministic dirty-content suffix, including untracked source files, so they cannot be mistaken for
artifacts reproduced from the prior clean commit.

Feature columns and target/label-metadata columns are disjoint. Dataset assembly computes features
before labels and never supplies target columns to the feature registry. Duplicate timestamps and
invalid broker market fields fail the build.

## Missing rows

The row policy can remove the declared maximum feature warm-up, drop explicitly critical missing
features, retain optional/structural NaNs, or require complete features. Incomplete label horizons
are normally removed. Reports distinguish warm-up removal, structurally unavailable cells,
rejected broker-data nulls, optional disabled features, and missing MTF context. Zero imputation is
never automatic.

## Splits, purge, and embargo

Chronological train, validation, and OOS ranges are half-open positional intervals. Effective purge
is at least the label horizon. It removes samples at the end of train and validation whose future
label path would cross the next boundary. Optional embargo removes rows at the beginning of
validation and OOS. Reusable expanding and rolling walk-forward generators produce deterministic
split manifests but do not run experiments.

All future preprocessors must use the training-only fitting guard. Validation and OOS transforms
reuse already-fitted state.

## Storage and immutability

Parquet with PyArrow is the production format: it preserves typed columns and is efficient for
local medium/large analytical datasets. Gzip CSV is available only for debugging. Artifacts live
under an ID-named directory with dataset, feature, label, split, and quality manifests. An existing
ID is never overwritten; mismatched content raises an error.

## Commands

Build from the reviewed configuration:

    python datasets/build_dataset.py --config configs/datasets/xauusd_m5.yaml

Inspect an artifact:

    python datasets/inspect_dataset.py --dataset-manifest datasets/generated/DATASET_ID/dataset.manifest.json

Generated datasets are ignored by Git and should be backed up with their manifests as immutable
artifacts.
