# Risk boundary

Phase 7 Task 3 implements the deterministic financial safety boundary in
`src/axq/risk_boundary/`. Only a Discipline `PASS` may be evaluated, and only a Risk `PASS` may be
eligible for the separate Phase 7 Task 4 execution boundary. `src/axq/risk.py` remains the
compatibility primitive layer; its
validated `calculate_volume_lots()` function is reused for risk-budget sizing and downward broker
lot-step normalization.

The boundary fails closed on stale or missing state and separately represents ordinary rejection,
no action, and emergency stop. It does not call agents, tools, models, or LLMs; it does not construct
broker orders or authorize execution. No model or LLM may override it.
