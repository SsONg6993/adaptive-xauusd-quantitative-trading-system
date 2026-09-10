# Deterministic Daily Reflection

Phase 8 Task 2 turns immutable Experience Store facts into offline daily observations. It does not
change a trade, threshold, runtime state, model, or production policy.

## Causal contract

Each `DailyReflection` covers `[00:00:00Z, next 00:00:00Z)` and selects experiences by
`available_at`. All timestamps are strict UTC. The content-addressed reflection identity binds the
policy, exact sorted experience IDs, findings, guards, period, and optional predecessor. Wall-clock
build time and SQLite sequence numbers are excluded.

`ReflectionPolicy` is versioned, immutable, and limited to diagnostic sample sizes and descriptive
thresholds. `ReflectionFinding` contains a category, signal, stable reason code, scope, measured
facts, and exact supporting experience IDs. It is not a recommendation. `SampleGuardRecord` makes
each suppressed or supported diagnostic visible as `PASSED`, `INSUFFICIENT`, or `UNAVAILABLE`.
Unknown values remain `None`; known numeric zero remains zero.

## Diagnostic families

- completed-trade R/P&L/win rate by BUY/SELL, known session, and known regime;
- Master confidence versus realized win-rate gap;
- MFE/MAE adverse-to-favorable excursion imbalance;
- concentrated Discipline, Risk, or action rejection reason;
- specialist support joined to completed trades through exact evidence IDs;
- position-protection behavior and runtime anomalies.

No finding is produced below its configured minimum sample. There is no fuzzy temporal attribution,
counterfactual claim, causal claim, or automatic policy response.

## Persistence

`SQLiteReflectionStore` writes policies, reflections, findings, guards, and exact source links.
Triggers reject UPDATE and DELETE. Identical semantic writes are idempotent; an ID/content conflict
fails closed. A changed record for the same UTC day and policy must explicitly name the latest
reflection in `supersedes_reflection_id`. The previous record remains authoritative history.

Canonical JSON stored in each immutable record is the source of truth. The CLI `report` command is
a compact deterministic projection; `show-daily-reflection` returns the full record.

## Verified baseline

The corrected one-month Experience Store (2026-08-10 through 2026-09-08) produced 30 daily records,
122 findings, and 378 sample guards. Guard results were 161 passed, 151 insufficient, and 66
unavailable. The findings comprised 30 agent-reliability, 25 session, 20 rejection, 17 direction,
16 position-management, seven confidence-gap, and seven excursion observations. No regime finding
was asserted because the required source fact was unavailable. Rebuilding the same range reused all
30 IDs and produced byte-identical report JSON.
