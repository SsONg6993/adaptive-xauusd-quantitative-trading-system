# Quant Agent contract

The Quant Agent is frozen inference over a registered Phase 4 artifact. It never trains or updates
itself during inference. It accepts one current feature row, validates the Phase 2 feature-manifest
identity and exact ordered Phase 3 feature contract, rejects stale/missing/infinite inputs, and
returns the shared `AgentPrediction` schema.

The message carries `agent=quant`, UTC timestamp, `BUY`/`SELL`/`HOLD`, signed score, calibrated
confidence, freshness, model and feature versions, dataset and label IDs, concise reasons, class
probabilities, target, split ID, and selected-feature version. `UP`, `DOWN`, and `NEUTRAL` map to
`BUY`, `SELL`, and `HOLD`. A confidence below the configured threshold also becomes `HOLD`; this
threshold is not profitability-optimized in Phase 4.

Logistic models expose per-row standardized coefficient contributions. Tree models expose their
built-in importance when available. Saved global coefficient/importance summaries support later
review, permutation importance, and optional SHAP analysis. SHAP is not a runtime dependency.

```python
agent = QuantAgent("runtime/models/quant/qm-...")
prediction = agent.predict(
    current_features,
    symbol="XAUUSD",
    timeframe="M5",
    timestamp=utc_timestamp,
    data_freshness_ms=250,
    feature_manifest_id="fm-...",
)
```

Only load model artifacts produced locally or obtained through a separately authenticated channel.
Joblib is required for scikit-learn fidelity and is not a safe format for untrusted files; Phase 4
therefore verifies SHA-256 hashes before loading every artifact. ONNX export is deferred.

Future prediction logging should preserve prediction/outcome linkage, actual class, future return,
MFE/MAE, confidence bucket, and every model/dataset/feature/label version. This is the interface for
controlled weekly review and drift analysis, not uncontrolled online learning.

Phase 5 development reports preserve these fields in `predictions.parquet` where the Phase 3 label
manifest supplies them. Reusable summaries cover prediction counts, BUY/SELL/HOLD distribution,
actionable coverage, confidence, actual outcomes, classification/calibration metrics, return/MFE/MAE
diagnostics, version identities, drift interfaces, and prior-period comparison. Scheduling and
autonomous retraining remain out of scope.
