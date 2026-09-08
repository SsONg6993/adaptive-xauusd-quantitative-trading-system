# Architecture decision log

Dates record when the current repository baseline was ratified. Later reversals require a new entry;
do not silently rewrite earlier decisions.

## 2026-09-08 — Independent XAUUSD system

- **Decision:** Build a brand-new independent project; do not reuse unrelated previous EA code.
- **Reason:** Preserve clean assumptions, auditability, and ownership boundaries.
- **Consequence:** XAUUSD is the initial market and M5/M15/H1/H4 are the supported analysis frames.

## 2026-09-08 — Python intelligence, MQL5 safety and execution

- **Decision:** Python owns intelligence and orchestration; the future MQL5 EA owns broker-facing
  execution and hard safety checks.
- **Reason:** Use the strongest local ecosystem for analytics while retaining broker-native safety.
- **Consequence:** Deterministic risk controls and the EA may veto; agent advice never bypasses them.

## 2026-09-08 — Local-first operation

- **Decision:** Core inference is local-first with low recurring API cost. Paid LLM/news APIs remain
  optional. Serious training runs locally under user control.
- **Reason:** Reliability, privacy, cost control, and reproducibility.
- **Consequence:** Codex builds pipelines and runs tiny smoke tests unless heavier work is explicit.

## 2026-09-08 — Point-in-time market data

- **Decision:** Store internal timestamps as timezone-aware UTC. Higher-timeframe values become
  available only after their candles fully close. Features are causal at every timestamp.
- **Reason:** Prevent look-ahead leakage and broker-time ambiguity.
- **Consequence:** Swing confirmation is delayed; future-candle mutation must not change past features.

## 2026-09-08 — Versioned features and immutable datasets

- **Decision:** Bind feature manifests, label manifests, split manifests, source hashes, and Git
  identity into immutable Phase 3 dataset artifacts.
- **Reason:** Make every training input reproducible and auditable.
- **Consequence:** Incompatible identity, schema, order, chronology, or content fails loudly.

## 2026-09-08 — Conservative label ambiguity

- **Decision:** Same-bar TP/SL collision policy defaults to `AMBIGUOUS`.
- **Reason:** Candle OHLC cannot prove intrabar event ordering.
- **Consequence:** Alternative policies require explicit configuration or lower-timeframe evidence.

## 2026-09-08 — Chronological evaluation

- **Decision:** Support purge and embargo gaps; protect OOS from preprocessing, selection, fitting,
  and calibration.
- **Reason:** Overlapping forward labels and random splits otherwise leak future information.
- **Consequence:** TRAIN fits transforms/models, VALIDATION calibrates, and frozen artifacts alone
  inspect OOS.

## 2026-09-08 — Calibrated three-way Quant output

- **Decision:** Calibration uses VALIDATION only. `HOLD` is a valid outcome through the explicit
  neutral class or a configurable confidence threshold.
- **Reason:** Confidence quality matters, and forcing BUY/SELL creates false actionability.
- **Consequence:** Preserve BUY/SELL/HOLD coverage, confidence buckets, and Opportunity Utilization
  so later filters cannot silently eliminate trade frequency.

## 2026-09-08 — Explicit model lifecycle

- **Decision:** Models begin as `CANDIDATE`; Champion/Challenger promotion is explicit,
  multi-metric, evidence-based, and reversible.
- **Reason:** One metric or one OOS period cannot justify autonomous replacement.
- **Consequence:** No automatic promotion and no uncontrolled online mutation after each trade.

## 2026-09-08 — Controlled future learning and reporting

- **Decision:** Future learning uses scheduled, versioned retraining with drift review. Weekly
  reporting must retain predictions, outcomes, returns, MFE/MAE, confidence, regimes, versions, and
  success/failure attribution.
- **Reason:** Improvement must be measurable and auditable.
- **Consequence:** Online learning and full reporting remain future reviewed phases.
