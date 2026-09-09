# Position action safety

Phase 7 Task 7 is the semantic boundary between an open-position management recommendation and a
future broker adapter:

`PositionManagementOutcome -> PositionActionSafetyOutcome -> PositionActionIntent`

These are deliberately different facts. A management outcome records what policy recommends. The
safety outcome records whether current authoritative state still permits that recommendation. A
position-action intent records a transportable request, but is not broker authorization or proof of
execution.

## V1 contracts

- `PositionActionPolicy` versions freshness, volume-tolerance, missing-stop, and safe-normalization
  rules.
- `PositionActionContext` binds the immutable recommendation to the current position, original entry
  intent/result, persisted broker link, reconciliation, safe-resume status, account, broker
  constraints, market price, component freshness, kill switch, and UTC causal time.
- `PositionActionSafetyOutcome` is `NO_ACTION`, `PASS`, `REJECT`, or `EMERGENCY_BLOCK`.
- `PositionActionIntent` exists only for `PASS` and is either `MODIFY_PROTECTIVE_STOP` or
  `CLOSE_POSITION`.

All identities use canonical content serialization. Runtime paths, random IDs, database sequences,
and wall-clock generation timestamps are excluded. Equivalent live and replay inputs therefore
produce identical semantic IDs.

## Safety behavior

Exact persisted intent/result/ticket/transport linkage is mandatory; approximate price, time,
direction, or volume similarity is never used. Unsafe recovery, UNKNOWN submission, unresolved
anomalies, kill switch, and corrupt linkage hard-block action. Missing/stale state, a disappeared or
changed position, material volume change, disabled trading, and broker-invalid stop requests reject
without an intent.

Protective stops cannot be removed or widened. A newly added stop requires explicit policy and must
reduce risk relative to the originally approved stop. Tick normalization rounds only in the
risk-reducing direction and must still satisfy directional, stop-level, and freeze-level rules.

V1 close uses the full current volume of the exact authoritative open position. It cannot increase
volume, partially close, reverse, or create an entry.

## Journal and transport boundary

`append_position_action_chain` adds typed management, safety, and optional intent records to the
existing SQLite runtime journal. It preserves parent/previous semantic links, rejects conflicting
linkage for the same semantic ID, and returns existing entries on an equivalent retry. UPDATE and
DELETE remain forbidden; storage sequence never becomes semantic identity.

Task 7 stops at the intent. There is no MetaTrader5 call, MQL5 message, broker ticket creation,
modification result, or close result.
