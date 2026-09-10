# Phase 8 Task 2 Deterministic Daily Reflection Design

## Scope

Task 2 adds deterministic UTC-day reflection over immutable Task 1 experiences. It produces measured
observations and explicit sample guards only. It does not produce weekly reflections, improvement
proposals, trading-policy changes, graphs/vector indexes, RAG, LLM output, or runtime mutations.

## Causal period rule

A daily period is the half-open UTC interval `[00:00:00Z, next 00:00:00Z)`. Experiences enter the
period by `available_at`, not by entry time or database insertion time. This ensures every fact was
available within the reflected day. Input experience IDs are sorted, deduplicated, and bound into
the reflection identity.

## Contracts

`ReflectionPolicy` is immutable, versioned, and content-addressed. It contains diagnostic minimum
sample sizes and finding thresholds only; it cannot contain Master, Discipline, Risk, execution, or
position-management trading parameters.

`SampleGuardRecord` records the diagnostic, scope, observed sample size, required sample size, and
`PASSED`, `INSUFFICIENT`, or `UNAVAILABLE` outcome. A suppressed finding therefore remains
auditable. `ReflectionFinding` contains a typed finding category and signal, stable reason code,
scope, measured metrics, threshold facts, and exact supporting experience IDs. It is an
observation, never a recommendation.

`DailyReflection` binds one UTC period, policy ID, exact input experience IDs, deterministic
findings and guards, causal availability, and optional `supersedes_reflection_id`. All IDs exclude
wall-clock generation time and database row IDs.

## Deterministic diagnostics

The daily aggregator measures:

- BUY/SELL trade outcome by direction;
- outcome by known session and regime;
- Master-confidence versus realized win-rate gaps on completed trades;
- average MFE/MAE and adverse-to-favorable excursion ratio;
- concentrated Discipline, Risk, and position-action rejection reasons;
- exact-evidence-linked specialist directional support and realized outcome;
- position-management outcome/protection rates;
- runtime anomaly counts and severities.

Each diagnostic emits a finding only when its policy guard passes. Missing regime or other facts are
`UNAVAILABLE`, not the string zero and not an inferred category. Metrics preserve `None` separately
from numeric zero. No counterfactual is calculated.

## Persistence and supersession

`SQLiteReflectionStore` stores immutable policies, daily reflections, findings, guards, and exact
experience source links. SQLite triggers reject UPDATE and DELETE. An identical semantic insert is
idempotent; the same ID with different content fails closed.

For one UTC day and policy, the first reflection has no predecessor. A changed revision must name
the latest stored reflection in `supersedes_reflection_id`. The prior row remains immutable. An
identical rerun returns the existing reflection and does not manufacture a supersession.

## CLI

`python -m axq.reflection` exposes machine-readable `build-daily-reflections`,
`show-daily-reflection`, and `report` commands. Builds target a bounded inclusive date range.
Canonical JSON is authoritative; concise output is a deterministic projection of stored contracts.

## Validation

Focused tests cover UTC availability boundaries, identities, guards, every diagnostic family,
actual experience provenance, idempotency, conflict rejection, append-only triggers, supersession,
CLI JSON, and forbidden-scope absence. The corrected one-month Experience Store is the real
validation source. Final validation is pytest, Ruff, strict mypy, pip integrity, diff checks, and one
Graphify refresh.
