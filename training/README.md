# Local training

`quant/train.py` consumes an immutable Phase 3 dataset and writes an ignored, manifest-bound local
run. `quant/evaluate.py` reproduces metrics from frozen artifacts without retraining. See
`docs/model_training.md`. Heavy training and tuning remain manual and are not run by Codex.
