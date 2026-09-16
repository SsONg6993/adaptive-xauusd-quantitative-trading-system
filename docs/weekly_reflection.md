# Deterministic Weekly Reflection and Pattern Lifecycle

Phase 8 Task 3 aggregates immutable Daily Reflections and exact Experience records into ISO-week
observations. It is offline analytical infrastructure and has no import path into trading policy or
runtime mutation.

## Weekly contract

A week is `[Monday 00:00 UTC, following Monday 00:00 UTC)`. The builder resolves explicit daily
supersession chains without using database row order, then validates every finding source against
the selected Daily Reflection and exact Experience Store record.

`WEEK_COMPLETENESS` lists every present and missing daily period. Incomplete weeks are persisted but
cannot contain a `SuccessPattern` or `FailurePattern`. Later input completion creates a new weekly
record that explicitly supersedes the incomplete one.

Patterns require both repeated-day and exact-Experience sample guards. Positive findings may create
success observations; negative or warning findings may create failure observations. Neutral,
insufficient, unavailable, or broken provenance does not become a pattern. Pattern metrics preserve
units and deterministically summarize count, minimum, maximum, and mean.

## Identity

`pattern_key` binds exactly:

- pattern type;
- finding category;
- signal class;
- reason code;
- scope;
- scope value.

It excludes week interval, samples, metrics, and supporting IDs, so the same semantic pattern keeps
one key across weeks. Each weekly observation has a distinct content-addressed `pattern_id` bound to
its interval and evidence. Weekly reflection IDs bind policy, exact inputs, guards, patterns, and
supersession.

## Knowledge lifecycle

Aggregation creates every pattern as `OBSERVATION`. A later status is possible only through an
explicit immutable `PatternStatusTransition` supplied by an operator or evaluation action:

```text
OBSERVATION -> HYPOTHESIS -> CANDIDATE -> VALIDATED
      |             |           |             |
      +-------------+-----------+-------------+-> DEPRECATED
      +-------------+-----------> REJECTED
```

`REJECTED` and `DEPRECATED` are terminal. Current status is derived by replaying the exact linear
transition chain. Unknown patterns, stale source status, invalid edges, missing predecessors,
branches, and time reversal fail closed. No mutable current-status table exists, and no status is
automatically promoted.

## Verified baseline

The unchanged 2026-08-10 through 2026-09-08 baseline produced five weekly records: four complete and
one incomplete. Complete weeks produced five success and 21 failure observations. All 26 patterns
remained `OBSERVATION`; no lifecycle transition was generated. Guards comprised 92 passed and 32
insufficient records. The incomplete week contained September 7–8, explicitly listed September
9–13 as missing, and produced zero patterns.

An identical rebuild reused all five weekly IDs and produced byte-identical summary JSON with
SHA-256 `c1a00c77c9940184165cf9edf44a85c28df8bcffbb3af5028eebefbad6f90fba`.
