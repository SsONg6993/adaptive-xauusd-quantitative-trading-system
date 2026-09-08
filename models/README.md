# Model artifacts

Generated model artifacts are intentionally ignored and should live under `runtime/models/quant`.
Keep only documentation and reviewed configuration in Git. Phase 4 hashes every local artifact and
registers it as a CANDIDATE; joblib files must never be accepted from an untrusted source.
