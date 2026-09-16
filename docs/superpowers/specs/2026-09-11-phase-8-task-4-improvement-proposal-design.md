# Phase 8 Task 4 Advisory Improvement Proposal Design

## Scope

Task 4 converts recurring, sufficiently guarded weekly patterns into immutable advisory
`ImprovementProposal` records. It adds no trading-policy update, code generation, replay execution,
challenger evaluation, runtime import, Experience Graph, RAG, or LLM dependency.

The source of truth remains the immutable Experience, DailyReflection, and WeeklyReflection stores.
Proposal construction revalidates exact provenance rather than trusting copied identifiers or using
time/price similarity.

## Eligibility

The builder groups terminal weekly observations by `pattern_key`. A group is eligible when:

- it contains at least two distinct pattern observations from distinct complete ISO weeks;
- every source weekly reflection is the terminal record in its explicit supersession chain;
- every source pattern is present in that weekly reflection and has the shared `pattern_key`;
- every source pattern remains in an active knowledge state (`OBSERVATION`, `HYPOTHESIS`,
  `CANDIDATE`, or `VALIDATED`), derived by replaying explicit pattern transitions;
- the source reflection's `WEEK_COMPLETENESS` and `PROVENANCE_INTEGRITY` guards pass;
- the pattern-signature-specific `PATTERN_DAY_SUPPORT` and `PATTERN_EXPERIENCE_SUPPORT` guards pass;
- every supporting finding exists in an exact selected DailyReflection source; and
- every supporting experience exists in the Experience Store and is linked by the source finding,
  pattern, daily reflection, and weekly reflection.

`REJECTED` and `DEPRECATED` source patterns cannot support a new proposal. A group with insufficient
recurrence or any unavailable, insufficient, missing, conflicting, or ambiguous source is recorded
in the deterministic build report as ineligible and produces no proposal.

The unchanged Task 3 baseline contains 14 semantic pattern keys. Seven recur in two or more complete
weeks and therefore should create seven advisory proposals; seven single-week keys remain
ineligible.

## Contracts and identity

`ImprovementProposalPolicy` is immutable and content-addressed. Its default minimum recurrence is
two complete-week observations. The policy contains a versioned deterministic category-to-target
mapping, never numeric trading thresholds.

`ProposalTargetComponent` is a closed enum:

- `MASTER_FUSION`
- `DISCIPLINE_GUARD`
- `RISK_BOUNDARY`
- `POSITION_MANAGEMENT`
- `SPECIALIST_AGENT`
- `RUNTIME_ORCHESTRATION`

`ProposalEvidenceGuard` records the recurrence and exact-provenance checks used by an accepted
proposal. Every guard embedded in an `ImprovementProposal` must be `PASSED`; failed assessments are
reported by the builder but are not misrepresented as proposals.

`ImprovementProposal` contains:

- `proposal_id` and stable `proposal_key`;
- `policy_id`, target component, category, pattern type, signal class, reason, scope, and value;
- deterministic rationale, proposed-change description, expected benefit, risks, and validation
  plan;
- exact weekly reflection, weekly pattern, daily reflection, finding, experience, and weekly-guard
  IDs;
- the source week interval and availability boundary;
- evidence guards;
- `status=OBSERVATION`; and
- optional `supersedes_proposal_id`.

`proposal_key` identifies the durable advisory subject and derives from policy version, target
component, and `pattern_key`. It excludes source-week intervals, metrics, samples, evidence IDs, and
supersession. `proposal_id` is content-addressed over the complete canonical record except the ID,
so changed evidence creates a new proposal ID while retaining its proposal key.

All tuples are deduplicated and sorted before identity is bound. Timestamps must be aware UTC.
Storage sequence numbers, filesystem paths, insertion order, and wall-clock creation time are never
identity inputs.

## Deterministic advisory content

The builder uses reviewed, versioned templates keyed by finding category and pattern type. Templates
describe a bounded hypothesis to evaluate; they do not select a new threshold or prescribe direct
production edits.

Examples:

- repeated `REJECTION_ANOMALY` targets `DISCIPLINE_GUARD` and proposes evaluating the named rejection
  path for false or excessive blocking;
- repeated `POSITION_MANAGEMENT_ANOMALY` targets `POSITION_MANAGEMENT` and proposes evaluating the
  named lifecycle behavior;
- repeated `AGENT_RELIABILITY` targets `SPECIALIST_AGENT` and proposes evaluating the named
  specialist evidence behavior;
- repeated `CONFIDENCE_CALIBRATION` targets `MASTER_FUSION` and proposes an offline calibration
  diagnostic;
- repeated `EXCURSION_IMBALANCE` targets `RISK_BOUNDARY` and proposes evaluating the stated
  risk/excursion relationship.

Direction, session, and regime outcomes target `MASTER_FUSION`. Runtime anomalies target
`RUNTIME_ORCHESTRATION`. Every template includes risks of overfitting, small samples, regime
dependence, and unintended downstream effects. Every validation plan requires a separately approved
causal replay/walk-forward or shadow comparison with protected Final OOS and explicit promotion.

## Proposal lifecycle

Proposal lifecycle is separate from pattern lifecycle:

```text
OBSERVATION -> HYPOTHESIS -> CANDIDATE -> VALIDATED
      |             |           |             |
      +-------------+-----------+-------------+-> DEPRECATED
      +-------------+-----------> REJECTED
```

Every transition is an immutable `ProposalStatusTransition` with proposal ID/key, from/to status,
aware UTC effective time, action kind (`OPERATOR` or `EVALUATION`), actor/action identity, reason,
optional evaluation IDs, and exact previous transition ID. No automatic transition is emitted by
the builder.

`VALIDATED` means only that evidence or a future validation plan has met an explicitly recorded
criterion. It grants no deployment authority and has no path to code, configuration, registry,
runtime, or broker mutation. Current status is derived by replaying one exact linear chain. Invalid
edges, stale source status, missing predecessors, branches, time reversal, and terminal-state
transitions fail closed.

## Append-only persistence and supersession

Migration `008_improvement_proposals.sql` creates append-only tables for proposal policies,
proposals, evidence guards, exact source links, and proposal status transitions. UPDATE and DELETE
triggers protect every table. There is no mutable current-state table.

Identical content is idempotent. A same-ID content mismatch fails closed. For one `proposal_key` and
policy, changed eligible evidence must append a proposal whose `supersedes_proposal_id` equals the
latest stored proposal. Earlier proposals and lifecycle transitions remain immutable. Lifecycle is
tracked per proposal ID; a superseding proposal starts at `OBSERVATION` and does not inherit a prior
proposal's status silently.

## CLI

The existing `python -m axq.reflection` entry point gains:

- `build-improvement-proposals`
- `show-improvement-proposal`
- `proposal-summary`
- `transition-proposal`
- `show-proposal-history`

Build requires explicit paths to the Experience, DailyReflection, WeeklyReflection, and proposal
stores. It emits compact sorted JSON with assessed keys, eligible keys, insufficient keys, created,
reused, superseded, proposal IDs, guard counts, target counts, and lifecycle counts. Show commands
emit canonical machine-readable JSON. Transition commands require complete explicit transition
metadata.

## Validation

Tests cover strict contracts, literal identities, input-order invariance, exact provenance,
recurrence, guard matching, rejected/deprecated source exclusion, deterministic templates,
supersession, append-only triggers, lifecycle replay, idempotent CLI output, and forbidden mutation
boundaries.

The unchanged one-month baseline must produce seven eligible recurring keys and seven proposals,
all at `OBSERVATION`, with no transitions. A second identical build must reuse all proposal IDs and
produce byte-identical summary JSON. Full pytest, Ruff, strict mypy, pip integrity, diff checks, and
one final Graphify refresh close Task 4.
