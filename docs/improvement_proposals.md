# Advisory Improvement Proposals

Phase 8 Task 4 turns recurring weekly evidence into immutable review artifacts. It does not tune,
execute, or deploy a trading change.

## Eligibility and provenance

One proposal may be built per semantic `pattern_key` when at least two distinct complete-week
observations exist. Each source week must have passed `WEEK_COMPLETENESS`,
`PROVENANCE_INTEGRITY`, `PATTERN_DAY_SUPPORT`, and `PATTERN_EXPERIENCE_SUPPORT`. The builder walks
exact weekly pattern, DailyReflection, finding, and Experience identities and fails closed on a
missing, duplicated, ambiguous, rejected, or deprecated source.

The default policy is content-addressed and contains no trading threshold. Deterministic templates
map measured categories to bounded target components and describe rationale, proposed evaluation,
expected benefit, risks, and a validation plan. They never prescribe an automatic setting change.

## Identity and supersession

`proposal_key` binds policy, target component, and stable pattern key. Evidence intervals, samples,
metrics, and source IDs do not change that semantic key. `proposal_id` binds the full canonical
record, including exact evidence and supersession, so revised evidence creates a distinct ID.

The SQLite store is append-only. Identical inserts are idempotent. Changed evidence must explicitly
supersede the latest proposal for the key; earlier content remains queryable. There is no mutable
current-state or deployment table.

## Lifecycle

All proposals begin as `OBSERVATION`. Explicit operator/evaluation actions may append:

```text
OBSERVATION -> HYPOTHESIS -> CANDIDATE -> VALIDATED
      |             |           |             |
      +-------------+-----------+-------------+-> DEPRECATED
      +-------------+-----------> REJECTED
```

Current status is reconstructed from the exact linear transition chain. Invalid edges, stale
status, missing predecessors, branches, terminal-state transitions, and time reversal fail closed.
`VALIDATED` records evaluation evidence only and supplies no deployment authority.

## Verified baseline

The unchanged one-month baseline contains 14 semantic pattern keys. Seven recur across two or more
complete weeks and produced seven advisory proposals; seven single-week keys remained insufficient.
All seven proposals remained `OBSERVATION`, with no transitions. The proposals preserve 19 weekly
pattern links, 19 weekly reflection links, 64 finding links, 64 daily-reflection links, 1,124
Experience links, and 76 weekly-guard links when counted per proposal. Those links resolve to 19
distinct patterns, four distinct weekly reflections, 64 distinct findings, 20 distinct daily
reflections, 1,077 distinct experiences, and 46 distinct weekly guards. Each proposal also embeds
three passed evidence guards, producing 21 proposal-level guards in total.

The identical second build reused all seven IDs and produced byte-identical summary JSON with
SHA-256 `00aab84076221a4fa3c6271ec9d99f45ff412ca6b30423d9daf89e4e1d44be75`.
The ignored append-only SQLite artifact is 1,208,320 bytes.
