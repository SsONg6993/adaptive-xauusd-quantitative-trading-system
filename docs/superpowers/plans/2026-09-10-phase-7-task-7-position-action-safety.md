# Phase 7 Task 7: Position Action Safety and Journal Plan

## Scope

Implement only the deterministic boundary between an immutable
`PositionManagementOutcome` and a future broker transport. The boundary rechecks current
authoritative position, recovery, linkage, freshness, and broker facts. It emits no broker calls.

## Contract design

1. Add `axq.position_actions` with strict frozen, versioned Pydantic contracts:
   `PositionActionPolicy`, `PositionActionContext`, `PositionActionSafetyOutcome`, and
   `PositionActionIntent`.
2. Limit actions to `NO_ACTION`, `MODIFY_PROTECTIVE_STOP`, and `CLOSE_POSITION`; only a `PASS`
   safety result can produce an intent.
3. Bind all four identities to canonical serialized content. Causal UTC timestamps are content;
   wall clocks, UUIDs, filesystem paths, process state, database sequences, and transport results
   are absent.
4. Keep linkage evidence explicit: original entry intent/result, broker-intent link, current
   authoritative position, reconciliation report, and resume readiness.

## Pure evaluator

1. Map HOLD/NO_ACTION management outcomes to safety `NO_ACTION` with no intent.
2. Fail closed on unsafe resume, unresolved or anomalous reconciliation, UNKNOWN execution,
   corrupt/missing exact linkage, identity mismatch, stale components, stale management outcomes,
   kill switch, missing position, or material volume drift.
3. Revalidate protective stops against current position state. Never remove or widen a stop.
   Allow adding a missing stop only when policy permits and the stop reduces risk relative to the
   original approved stop. Tick normalization is deterministic and only risk-reducing.
4. Validate trade availability, point/tick facts, stops/freeze distance, current price, and
   directional correctness before emitting a stop-modification intent.
5. Emit full-volume close intents only; a close is a position action, never an opposing entry.

## Journal integration

1. Extend the existing typed runtime-journal semantic union with management outcome, action-safety
   outcome, and action-intent record types.
2. Add an idempotent chain appender that reconstructs management outcome -> safety outcome ->
   optional intent through exact parent/previous identifiers.
3. Preserve the existing append-only SQLite triggers. Retry of an identical deterministic chain
   returns existing entries and does not append duplicate semantic actions. Database sequence is
   ordering metadata only.

## Test-first sequence

1. Add focused contract/evaluator tests for mapping, exact linkage, recovery gates, freshness,
   race conditions, stop monotonicity/constraints/normalization, full close, identities, purity,
   live/replay parity, and absence of transport behavior.
2. Add journal tests for typed round trip, chain reconstruction, append-only enforcement, and
   duplicate retry handling.
3. Run the focused tests red before implementation, then green after the smallest implementation.
4. Run full pytest, Ruff, mypy with the established unused-ignore suppression, pip check, and
   `git diff --check`.

## Documentation and graph

Update README, architecture, agentic architecture, project status, decision log, runbook, and
position-management/execution documentation. Refresh only durable Graphify outputs. Stop before
Task 8; do not commit, push, merge, train, replay at scale, or invoke MT5.
