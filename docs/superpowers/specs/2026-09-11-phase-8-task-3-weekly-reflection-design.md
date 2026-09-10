# Phase 8 Task 3 Deterministic Weekly Reflection and Pattern Lifecycle Design

## Scope

Task 3 adds deterministic ISO-week reflection and an explicit immutable knowledge-status lifecycle
inside `axq.reflection`. It consumes Task 2 `DailyReflection` records and Task 1 exact Experience
records. It produces descriptive weekly patterns and sample guards only. It cannot propose, tune,
promote, or mutate trading behavior.

Improvement proposals, automatic tuning, Experience Graph, vector RAG, LLMs, runtime mutation, and
Phase 9 are outside scope.

## Architecture

Weekly behavior is split into four focused modules while preserving the existing daily modules:

- `weekly_contracts.py` defines immutable weekly policy, guard, pattern, reflection, and lifecycle
  transition contracts.
- `weekly.py` performs pure ISO-week selection, exact provenance validation, guarded grouping, and
  deterministic pattern generation.
- `weekly_store.py` persists weekly policies, reflections, patterns, source links, and lifecycle
  transitions in append-only SQLite tables.
- `weekly_cli.py` contributes weekly build/show/summary and explicit transition commands to the
  existing `python -m axq.reflection` entry point.

Task 2 `ReflectionPolicy`, `DailyReflection`, daily aggregation, and daily persistence remain intact.
The weekly implementation may reuse canonical JSON and hashing helpers but will not refactor the
already-green daily path.

## ISO-week boundary and availability

Every weekly period is the half-open interval `[week_start, week_end)` where `week_start` is Monday
00:00 UTC and `week_end` is the next Monday 00:00 UTC. A weekly identity binds this interval, its
weekly policy, exact semantic inputs, guards, patterns, and optional superseded record.

The builder accepts immutable daily reflections and selects one terminal revision for each of the
seven UTC dates. A terminal revision is a record not superseded by another supplied record in the
same day and daily policy chain. A missing predecessor, branch, cycle, duplicate terminal revision,
or mixed daily policy fails closed. Database sequence numbers never determine semantic selection.

An incomplete week is a valid immutable observation. Its `available_at` is the maximum available
time of the present daily inputs, or `week_start` when none are present. A complete week's
`available_at` is at least `week_end`. Wall-clock build time is never read or included in identity.

## Weekly policy

`WeeklyReflectionPolicy` is strict, immutable, schema-versioned, and content-addressed. It binds the
required daily policy ID and diagnostic-only controls:

- required daily periods, fixed at seven;
- minimum supporting daily periods for a repeated pattern;
- minimum exact supporting Experience records;
- supported daily finding signals for success and failure classification.

The policy contains no Master, Discipline, Risk, execution, position-management, feature, model, or
runtime parameters. Changing a weekly diagnostic policy creates a new policy identity.

## Weekly sample guards

`WeeklySampleGuard` uses a typed guard kind and records observed support, required support, status,
present daily periods, missing daily periods, supporting daily reflection IDs, supporting finding
IDs, and supporting Experience IDs.

At minimum, Task 3 defines:

- `WEEK_COMPLETENESS`: exactly seven expected dates, with every present and missing date explicit;
- `PATTERN_DAY_SUPPORT`: repeated semantic finding support across the minimum daily periods;
- `PATTERN_EXPERIENCE_SUPPORT`: exact Experience support meets the configured minimum;
- `PROVENANCE_INTEGRITY`: every claimed finding/Experience link exists and belongs to the selected
  immutable inputs.

Guard status remains `PASSED`, `INSUFFICIENT`, or `UNAVAILABLE`. Missing or unresolved inputs never
become zero, inferred evidence, or a hidden pattern.

If `WEEK_COMPLETENESS` does not pass, the WeeklyReflection contains the completeness and provenance
guards but no `SuccessPattern` or `FailurePattern`. When missing Daily Reflections later arrive, a
new WeeklyReflection must explicitly supersede the prior incomplete record.

## Exact provenance validation

The weekly builder receives exact Experience records in addition to Daily Reflections. It verifies:

1. every selected daily input belongs to one expected UTC date and the configured daily policy;
2. every finding source ID is present in that DailyReflection's exact input Experience IDs;
3. every supporting Experience ID resolves to exactly one supplied Experience record;
4. each Experience's `available_at` falls within the corresponding daily period;
5. no fuzzy time, price, direction, setup, or text matching is used.

Any conflict or broken exact link fails closed. Genuine absence is represented by a guard and does
not create a pattern.

## Pattern generation

Complete weeks group eligible Daily Reflection findings by an exact semantic signature:

`finding category + finding signal class + reason code + scope + scope value`.

Positive findings may produce `SuccessPattern`. Negative and warning findings may produce
`FailurePattern`. Neutral findings remain available in the WeeklyReflection's source provenance but
do not become success or failure patterns.

A pattern is created only when both its day-support and Experience-support guards pass. Metrics with
the same name and unit are summarized deterministically as count, minimum, maximum, and arithmetic
mean. Unavailable metrics remain unavailable; unlike units are never combined.

Each immutable pattern records:

- content-addressed `pattern_id`;
- stable semantic `pattern_key` derived only from `pattern_type`, `category`, `signal_class`,
  `reason_code`, `scope`, and `scope_value`;
- pattern type, category, signal, reason, scope, and scope value;
- sample days and exact sample count;
- summarized measured metrics;
- exact supporting Daily Reflection IDs;
- exact supporting finding IDs;
- exact supporting Experience IDs;
- initial knowledge status `OBSERVATION`.

Equivalent inputs in any iteration order produce identical patterns and WeeklyReflection JSON.
The pattern key excludes week interval, sample count, aggregated metrics, and all supporting IDs.
Repeated patterns in later weeks therefore retain the same semantic key but receive distinct
content-addressed observation IDs because their interval and evidence differ.

## Knowledge-status lifecycle

`KnowledgeStatus` contains:

- `OBSERVATION`
- `HYPOTHESIS`
- `CANDIDATE`
- `VALIDATED`
- `REJECTED`
- `DEPRECATED`

Weekly aggregation creates only `OBSERVATION`. It never emits a transition.

`PatternStatusTransition` is an explicit append-only operator or evaluation action containing:

- content-addressed transition ID;
- exact source pattern ID and semantic pattern key;
- `from_status` and `to_status`;
- explicitly supplied timezone-aware UTC effective time;
- action kind (`OPERATOR` or `EVALUATION`);
- stable actor/action identity and reason code;
- exact supporting evaluation IDs where applicable;
- exact previous transition ID, or `None` for the first transition.

Allowed transitions are:

- `OBSERVATION -> HYPOTHESIS | REJECTED | DEPRECATED`
- `HYPOTHESIS -> CANDIDATE | REJECTED | DEPRECATED`
- `CANDIDATE -> VALIDATED | REJECTED | DEPRECATED`
- `VALIDATED -> DEPRECATED`

`REJECTED` and `DEPRECATED` are terminal. No transition is automatic. The current status is a derived
projection obtained by replaying the immutable transition chain from the pattern's initial
`OBSERVATION` status.

Lifecycle replay fails closed on an unknown pattern, stale `from_status`, missing or incorrect
previous transition, invalid edge, duplicate branch, cycle, non-UTC time, or same transition ID with
different content. No prior pattern or transition row is overwritten.

## Weekly contract

`WeeklyReflection` records:

- strict schema version and content-addressed reflection ID;
- ISO UTC week boundaries and deterministic availability;
- weekly policy and required daily policy IDs;
- present and missing daily periods;
- exact selected Daily Reflection IDs;
- exact input Experience IDs;
- weekly guards;
- success and failure patterns;
- optional `supersedes_weekly_reflection_id`.

Children and source IDs are normalized into deterministic order. The contract rejects an invalid
week boundary, overlapping present/missing periods, non-observation pattern, duplicate child ID, or
pattern generation in an incomplete week.

## Append-only persistence and supersession

A new SQLite migration adds tables for weekly policies, weekly reflections, guards, patterns, exact
daily/finding/Experience source links, and pattern transitions. UPDATE and DELETE triggers protect
every new table.

`SQLiteWeeklyReflectionStore` provides policy append/read, weekly append/list/latest, source lookup,
pattern lookup, transition append/history, and derived lifecycle status. Identical semantic inserts
are idempotent; a same ID with different content fails closed.

The first record for a week and weekly policy has no predecessor. Any changed record for that week
must name the latest terminal weekly revision in `supersedes_weekly_reflection_id`. The previous
record remains immutable. Identical rebuilds reuse the current record and do not create a synthetic
revision.

## CLI

The existing module entry point adds:

- `build-weekly-reflections`: consumes daily and Experience stores plus an inclusive Monday range;
- `show-weekly-reflection`: emits one latest authoritative weekly JSON record;
- `weekly-summary`: emits counts for complete/incomplete weeks, guards, patterns, and statuses;
- `transition-pattern`: appends one explicitly supplied lifecycle action;
- `show-pattern-history`: emits the pattern and immutable ordered transition chain.

All outputs use canonical sorted JSON. CLI date arguments must be ISO dates and weekly start dates
must be Mondays. A lifecycle command requires all transition facts explicitly; it does not invent an
actor, timestamp, rationale, or evaluation identity.

## Baseline validation

The corrected one-month baseline spans 2026-08-10 through 2026-09-08. Task 3 will build four complete
ISO weeks beginning 2026-08-10, 2026-08-17, 2026-08-24, and 2026-08-31, plus the explicitly requested
incomplete week beginning 2026-09-07. That fifth record must list the five missing daily periods and
contain no patterns.

The baseline run records weekly, complete/incomplete, success/failure pattern, guard, and initial
status counts. A second identical run must reuse all weekly identities and produce byte-identical
canonical summary JSON. No lifecycle transition is generated during baseline aggregation.

## Testing and final gate

Focused tests cover contract validation, ISO boundaries, deterministic ordering, daily-revision
resolution, incomplete-week suppression and later supersession, exact provenance, pattern guards,
metric aggregation, success/failure classification, OBSERVATION-only creation, all lifecycle edges,
fail-closed replay, SQLite append-only enforcement, CLI JSON, and idempotent reruns.

The final gate is one full pytest run, Ruff, strict mypy, pip integrity, `git diff --check`, forbidden
scope audit, and one Graphify refresh. No broker access, model training, policy tuning, replay rerun,
or runtime mutation is required.
