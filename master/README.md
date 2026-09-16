# Master evidence fusion

Phase 7 Task 1 implements the narrow deterministic `EvidenceBundle` → `MasterProposal` boundary in
`src/axq/master/`. It is a pure, content-addressed evidence combiner; it does not authorize a trade.

The versioned `FusionPolicy` supplies one canonical weight per Phase 6 specialist, a bounded degraded
multiplier, and explicit score, confidence, uncertainty, contradiction, disagreement, and minimum-
READY gates. READY directional evidence contributes at full weight. DEGRADED directional evidence
contributes at the configured multiplier but cannot make a proposal actionable without sufficient
READY directional evidence. ABSTAINED, ERROR, terminal, zero-confidence, and non-directional context
evidence are recorded in the contribution audit and excluded from the directional score.

Cross-agent disagreement and within-agent counterevidence are separate normalized metrics. Any failed
gate produces `HOLD`; only aligned evidence passing every policy gate produces advisory `BUY` or
`SELL`. Simple majority voting is prohibited.

Phase 7 Task 2 adds the separate deterministic Discipline Guard in `src/axq/discipline/`. It consumes
the advisory proposal without changing Master fusion and is the only boundary that can mark a
proposal eligible for the Phase 7 Task 3 Risk boundary. Risk now performs deterministic financial
sizing and vetoes but does not authorize execution. Execution, MT5 connectivity, position
management, simulated brokerage, LLM reasoning, and reflection remain unimplemented.
