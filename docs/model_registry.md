# Model registry and promotion contract

New runs register as `CANDIDATE`. A reviewer may explicitly move a candidate to `CHALLENGER`.
Promotion to `CHAMPION` requires a non-empty evidence record; the framework never promotes or
replaces a model automatically. Valid lifecycle paths are:

```text
CANDIDATE -> CHALLENGER -> CHAMPION -> RETIRED
        \---------------------------> RETIRED
                    CHALLENGER ------> RETIRED
```

Future promotion evidence must compare the challenger with the current champion across OOS
classification metrics, calibration, return/MFE/MAE diagnostics, temporal stability,
trade-frequency and opportunity utilization, regime behavior when available, and later
walk-forward results. One metric is never sufficient. Promotion and rollback are deployment
configuration changes, never model mutation.

The local JSON registry is an auditable index pointing to immutable model manifests. Full run
metadata stays in each manifest; SHA-256 hashes protect artifacts. The local SQLite experiment log
records run ID, model, dataset, config, start/end time, status, device, metrics, and failures.
Generated registries, experiments, and model binaries live under ignored `runtime/` paths.

Later autonomous-learning work must remain scheduled, versioned, reversible, and approval-gated:
prediction/outcome logging, weekly review, drift detection, controlled retraining, challenger
evaluation, then explicit promotion. Models must not update after each trade.
