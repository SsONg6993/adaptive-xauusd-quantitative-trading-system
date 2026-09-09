# Execution boundary

Phase 7 Task 4 implements the deterministic Python-side entry boundary in
`src/axq/execution_boundary/`. Only a provenance-linked Risk `PASS` can become an immutable,
content-addressed `ExecutionIntent`. A small `ExecutionAdapter` protocol keeps the shared decision
path independent of its future live MQL5 or replay/simulated transport.

The reference `DemoExecutionAdapter` is disabled by default, has explicit dry-run and demo-enabled
modes, blocks live accounts, rechecks time/symbol/spread/slippage/price deviation immediately before
submission, and never repairs or enlarges an upstream instruction. Its ledger port reserves the
stable intent ID before transport; duplicate and uncertain submissions are not resent. The included
ledger is in-memory for deterministic tests. Durable persistence and startup broker reconciliation
remain required before unattended execution.

Typed results distinguish `NO_ACTION`, submission/acceptance, partial/full fill, rejection,
cancellation, expiry, transport failure, and dangerous `UNKNOWN` submission state. Actionable
results convert into the existing Phase 6 `EXECUTION_FEEDBACK` event and reducer path. There is no
direct MT5 order sender, simulated broker, position-management policy, or live-money capability.
