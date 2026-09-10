# Phase 7 Task 8 Direct MT5 Transport Design

## Scope

Task 8 adds concrete, demo-only MetaTrader5 Python adapters behind existing execution and recovery
contracts. It stops before a continuous runtime service. MetaTrader5 remains an optional Windows
dependency and is imported only by the concrete gateway.

## Boundaries

- `MT5Gateway` is the only interface shaped like the external MetaTrader5 package. Production code
  consumes normalized mappings and a typed constants record; tests use a deterministic fake.
- `MetaTrader5Gateway` lazy-loads the package and converts named-tuple responses to mappings. It
  owns connection lifecycle but contains no Master, Discipline, Risk, intent, or retry logic.
- `MT5BrokerSnapshotProvider` converts one explicit internal/broker symbol mapping into the existing
  `BrokerRecoverySnapshot`. Existing `broker_snapshot_runtime_events` then creates canonical events;
  the provider never mutates `SharedRuntimeState`.
- `MT5ExecutionTransport` implements the existing `ExecutionTransport`. `MT5ExecutionAdapter`
  composes it with `DemoExecutionAdapter` and `SQLiteExecutionLedger`.
- `MT5PositionActionAdapter` consumes only Task 7 `PositionActionIntent` values and uses a dedicated
  append-only ledger/result contract. It supports protective-stop modification and full close only.

## Safety and modes

Execution defaults to `DISABLED`. Disabled mode does not consult MT5. `DRY_RUN` performs connection,
demo-account, symbol, tick, constraint, position (when applicable), and `order_check` validation but
never calls `order_send`. `DEMO_ENABLED` repeats those checks immediately before calling
`order_send`. A successful `order_check` is only validation; the later broker response remains
authoritative.

Account trade mode must exactly equal MetaTrader5's demo constant. Unknown, contest, or live mode
fails closed. Terminal/account trading, symbol trade mode, point/digits/tick, volume grid, stop and
freeze distance, current price, exact position ticket, direction, volume, and kill-switch state are
checked from newly acquired facts. No automatic retry is implemented.

## Requests and response mapping

Entry uses `TRADE_ACTION_DEAL`, the intent's exact volume, direction, broker symbol, SL, and optional
TP. Close also uses `TRADE_ACTION_DEAL` but includes the exact `position` ticket and opposite broker
order type; this is a close request, never a new semantic entry. Protective modification uses
`TRADE_ACTION_SLTP`, exact ticket, approved tighter SL, and preserves the authoritative existing TP.

Known broker retcodes map to submitted/accepted/partial/full/rejected results with order/deal IDs,
retcode, comment, volumes, prices, and causal UTC timestamps. A failure before mutation is `FAILED`.
Any exception or missing response after `order_send` begins is `UNKNOWN`, is durably recorded, and
is never resent without reconciliation.

## Idempotency and persistence

Entry reuses `SQLiteExecutionLedger`: reserve before broker mutation and return existing terminal or
UNKNOWN results. Position actions use append-only `PositionActionTransportTransition` records with a
unique reservation per stable Task 7 intent ID. Database sequence values are operational order only
and never enter semantic identity. UPDATE and DELETE are rejected.

## Snapshots and causality

Snapshot acquisition maps account, tick, positions, pending orders, broker constraints, and derived
lot/notional exposure into existing Phase 6 state models. Missing broker values remain `None`; zero
sentinels for SL/TP become `None`. MT5 epoch values are converted to aware UTC. Observation and
availability use an injected aware-UTC clock and must not precede broker event time.

Symbol mapping is an explicit content-addressed internal/broker pair. No suffix search or fuzzy
mapping occurs. Persisted intent linkages may be rebound only through exact tickets and persisted
transport identity.

## Deferred work

Task 8 does not add an MQL5 EA, IPC bridge, continuous loop, scheduler, startup/shutdown service,
automated reconciliation workflow, simulated broker, live-money mode, or Task 9 orchestration.
Future MQL5/IPC transport can replace `MT5Gateway`/transport implementations without changing the
decision contracts.
