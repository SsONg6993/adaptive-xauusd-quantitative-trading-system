# Phase 7 deterministic runtime orchestration

`RuntimeOrchestrator` is the narrow composition boundary for the Phase 6/7 fast path. It does not
calculate features, fuse evidence, apply discipline, calculate risk, form execution requests, or
implement broker rules. A typed `DecisionCycleProcessor` composes those existing pure boundaries;
the orchestrator orders their outputs, journals them, applies operator/readiness gates, dispatches
the already-approved intent, and routes feedback through canonical `RuntimeEvent` reduction.

## Modes

| Mode | Event and decision path | Broker reads | Broker mutation |
|---|---|---|---|
| `DISABLED` | available for controlled diagnostics | no | never |
| `REPLAY` | complete shared semantic processor with replay clock/source | no | never |
| `SHADOW` | complete live-like decision path and intent journaling | yes | never |
| `DEMO` | complete path | yes | only through Task 8 demo-safe adapters |

There is deliberately no live-money mode. The checked-in configuration defaults to `DISABLED`.
The MT5 terminal path is optional operational configuration and is excluded from semantic IDs.

## Startup and recovery

Startup opens injected append-only stores, reconstructs the latest committed runtime state, source
cursors, specialist memories, and thesis state, and optionally invokes a bounded market-data
backfill/continuity callback. `SHADOW` and `DEMO` then connect the gateway, acquire one authoritative
broker snapshot, translate it to canonical events, reduce those events, perform exact execution
reconciliation, and evaluate `ResumeReadiness`. Any broker failure, stale component, missing
intrabar continuity, expired thesis, broker-only/local-only/conflicting object, UNKNOWN entry, or
unresolved position-action transport leaves startup `BLOCKED`. No decision is accepted while
startup is blocked.

The runtime journal and execution/action ledgers are authoritative append-only histories. A
checkpoint is a recovery anchor, not a replacement for those histories. Crash-style recovery does
not require a final checkpoint when committed journal records exist.

## Event and mutation sequence

Every accepted market event uses the existing `RuntimeStreamRunner` and `EvidenceKernel`. The same
injected decision processor is used in replay, shadow, and demo; only clock, source, snapshots, and
execution sinks differ. M5 and intrabar thesis restrictions remain in the existing scenario
lifecycle rather than in this service.

For DEMO entry, stop modification, or close, the service reacquires broker truth and re-evaluates
reconciliation/readiness immediately before dispatch. Task 8 adapters retain their independent
demo-account, current-fact, exact-ticket, idempotency, and UNKNOWN no-resend checks. Results are
journaled and converted to `EXECUTION_FEEDBACK`; the reducer is the only route into shared state.
A bounded snapshot refresh follows transport. There is no tight polling loop or automatic retry of
UNKNOWN operations.

An entry pause blocks new entries but does not block an already-open position's risk-reducing
protection or exit. Execution-disable and kill-switch gates block every broker mutation. Safety
gates cannot be bypassed by operator controls; resuming entries is permitted only while current
readiness is SAFE and execution/kill gates are inactive.

## Shutdown and replay output

Graceful shutdown stops intake, appends a content-addressed recovery checkpoint containing source
cursors and thesis linkage, flushes the runtime journal and both ledgers, and closes the gateway.
`RuntimeRunSummary` deterministically reports Master, Discipline, Risk, execution-intent/result,
position-management, and position-action counts from decision-cycle identities.

Task 9 excludes live money, new strategy or risk semantics, a simulated broker/P&L engine,
MQL5/IPC, cloud LLMs, reflection, experience stores, dashboards, and Phase 8 learning systems.
