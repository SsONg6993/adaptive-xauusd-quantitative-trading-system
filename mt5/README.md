# MT5 transport boundary

Phase 7 Task 8 implements an optional lazy-loaded direct MetaTrader5 Python gateway in
`src/axq/mt5/`. It supports read-only canonical broker snapshots plus disabled, dry-run, and
demo-only execution modes. No live-money mode exists. Dry-run may call `order_check` but never
`order_send`; uncertain submission is durably UNKNOWN and cannot be automatically retried.

No custom MQL5 EA or IPC bridge is shipped in Task 8. A future broker-native implementation must be
swappable behind the same entry/position-action transport, recovery, reconciliation, and runtime
feedback contracts; it may not add alternative Master, Discipline, or Risk logic.
