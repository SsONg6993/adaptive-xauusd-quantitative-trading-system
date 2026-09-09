# Execution boundary

Phase 7 Task 4 implements the deterministic Python-side entry boundary in
`src/axq/execution_boundary/`. Only a provenance-linked Risk `PASS` can become an immutable,
content-addressed `ExecutionIntent`. A small `ExecutionAdapter` protocol keeps the shared decision
path independent of its future live MQL5 or replay/simulated transport.

The reference `DemoExecutionAdapter` is disabled by default, has explicit dry-run and demo-enabled
modes, blocks live accounts, rechecks time/symbol/spread/slippage/price deviation immediately before
submission, and never repairs or enlarges an upstream instruction. Its ledger port reserves the
stable intent ID before transport; duplicate and uncertain submissions are not resent. The included
ledger is in-memory for deterministic tests; Task 5 provides the durable SQLite implementation and
startup reconciliation contracts required before any future unattended execution.

Typed results distinguish `NO_ACTION`, submission/acceptance, partial/full fill, rejection,
cancellation, expiry, transport failure, and dangerous `UNKNOWN` submission state. Actionable
results convert into the existing Phase 6 `EXECUTION_FEEDBACK` event and reducer path. There is no
direct MT5 order sender, simulated broker, position-management policy, or live-money capability.

Task 5 adds `SQLiteExecutionLedger`, which records immutable reservations, results, and
reconciliation reports in append-only SQLite transitions. A unique reservation constraint prevents
restart duplicates. UNKNOWN remains reconciliation-required and cannot be resent. Each later
reconciliation report explicitly supersedes the previous report; earlier anomalies are never
updated or deleted.

`BrokerRecoverySnapshot` contains canonical account, market, position, order, exposure, and broker
constraint state plus explicit intent/ticket/transport linkage. Matching never uses approximate
price, time, direction, or volume. Broker-only objects remain visible anomalies because legitimate
manual/operator trades may exist. `ResumeReadiness` stays blocked for stale critical state,
unresolved broker exposure, incomplete intrabar continuity, or expired theses. Recovery checkpoints
and WAL flush support graceful shutdown, but committed transitions—not checkpoints—remain the
source of truth after either graceful or crash recovery.

Task 6 adds `src/axq/position_management/` as a separate pure boundary for already-open positions.
It requires Task 5 safe readiness plus exact intent/result/broker-position linkage and emits only
`NO_ACTION`, `HOLD_POSITION`, `PROTECT_POSITION`, or `EXIT_POSITION`. HOLD does not submit a change;
V1 protection can only reduce risk toward break-even while satisfying stop/freeze constraints; and
EXIT is not a reversal or broker command. Real position-action safety validation and transport remain
unimplemented.
