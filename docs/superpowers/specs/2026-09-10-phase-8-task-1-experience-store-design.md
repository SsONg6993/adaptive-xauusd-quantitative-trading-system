# Phase 8 Task 1 Experience Store Design

## Scope

Task 1 adds deterministic outcome attribution and an append-only SQLite Experience Store around
the frozen Phase 7 semantic runtime. It does not generate reflections, proposals, graph/vector
indexes, LLM output, or policy changes.

## Source authority

Attribution reads the Phase 7 runtime journal, execution ledger, position-action ledger, and a
content-addressed replay-outcome artifact. Joins use persisted semantic identifiers only. A missing
link produces an incomplete experience with explicit missing-link codes; timestamps are descriptive
fields and are never used as fuzzy join keys.

The replay runner will additionally persist its already-computed fills, completed trades, exact
position-action applications, and per-event session context. This changes reporting persistence
only. It does not alter evidence, Master, Discipline, Risk, execution timing, stop behavior, or
position-management policy.

For bounded baseline storage, the replay runner retains only attribution-required
`RUNTIME_EVENT` and `AGENT_EVIDENCE` records from its own semantic expansion. The orchestrator still
persists Master, Discipline, Risk, execution, and position-action records. Full expanding
`SharedRuntimeState` snapshots are excluded from this reporting run; the immutable runtime kernel
and its semantic outputs are unchanged.

## Contracts

The immutable versioned contract family contains:

- `DecisionExperience`
- `TradeExperience`
- `RejectedDecisionExperience`
- `PositionManagementExperience`
- `RuntimeAnomalyExperience`
- `AgentContributionExperience`
- `CounterfactualExperience`, which is structurally separate and always declares simulation method,
  version, assumptions, and source proposal.

Every actual experience declares `simulated=false`, includes `ExperienceProvenance`, preserves UTC
causal timestamps, distinguishes `None` from numeric zero, and binds its ID to canonical serialized
content. Runtime paths, database sequence numbers, and wall-clock creation times are excluded.

## Persistence

`SQLiteExperienceStore` appends normalized payloads to `experience_records` and exact source links to
`experience_sources`. Duplicate identical experiences are idempotent. An existing ID with different
content fails closed. SQLite triggers reject UPDATE and DELETE. Indexed projection columns cover
time, type, symbol, setup, thesis, regime, session, specialist, outcome, and source semantic ID.

## Attribution

`OutcomeAttributionBuilder` decodes source models, indexes them by their native semantic IDs, and
emits experiences in deterministic order. Decision records join Master to Discipline and Risk.
Rejected records represent blocking Discipline, Risk, and position-action safety outcomes. Agent
records join exact `AgentEvidence` IDs where those records are present. Trade records join the replay
trade to its entry intent, execution result, decision chain, and optional exact close action.

Unavailable regime, feature, or transport facts remain `None`. Counterfactual outcomes are never
created by Task 1.

## CLI and analytics

`python -m axq.experience` exposes `build-experiences`, `show-experiences`, and `summary`. Output is
deterministic JSON. Summary queries are descriptive only: counts, direction/session/regime trade
groups, R/MFE/MAE/P&L, rejection layers, and agent evidence status counts.

## Validation

Focused tests cover contracts, exact attribution, append-only/idempotent storage, incomplete links,
actual/simulated separation, analytics, and baseline reconciliation. The final gate runs the full
test suite, Ruff, strict mypy, pip integrity, diff checks, one Graphify refresh, and one corrected
one-month replay ingestion. Exactly 166 completed replay trades must become 166 `TradeExperience`
records or Task 1 stops as incomplete.

The verified baseline produced 37,183 complete experiences and exactly 166 complete
`TradeExperience` records. Its metrics artifact is byte-identical to the corrected Phase 7 replay.
