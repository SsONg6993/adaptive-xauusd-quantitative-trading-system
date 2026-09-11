# Operator-authorized proposal lifecycle bridge

Phase 8 Task 11 records explicit operator permission to request a proposal lifecycle transition. The
V1 `ProposalTransitionAuthorization` permits only `CANDIDATE -> VALIDATED` and binds the exact
proposal, evaluation candidate, preregistered plan, paired result, and current terminal
`ACCEPT_EVIDENCE` review.

Authorization is evidence and permission only. It does not append a `ProposalStatusTransition`,
change proposal status, deploy a candidate, run evaluation/replay, tune parameters, access Final
OOS, mutate runtime, or contact MT5.

## Eligibility and identity

The proposal's replayed lifecycle status must still be `CANDIDATE`. The accepted review must be the
current terminal review for its paired result and all authoritative IDs must match exactly.
`authorized_at` is strict UTC, cannot predate the review, and participates in the content-addressed
authorization identity along with operator, action, reason, requested transition, and predecessor.

## Append-only history

Migration 015 stores a strict linear history per proposal. The first authorization has no
predecessor. Every later authorization names the current terminal authorization. Identical retries
reuse the existing ID; stale or forked predecessors, reused actions with changed content, backward
times, missing authorities, and mismatched linkage fail closed. Current authorization is derived by
replaying immutable history; there is no mutable current-state table.

## Commands

```powershell
$env:PYTHONPATH = (Resolve-Path 'src')
python -m axq.reflection record-proposal-transition-authorization --store runtime/phase8-task11/governance.sqlite3 --authorization proposal-transition-authorization.json
python -m axq.reflection show-proposal-transition-authorization --store runtime/phase8-task11/governance.sqlite3 --authorization-id <authorization-id>
python -m axq.reflection show-proposal-transition-authorization-history --store runtime/phase8-task11/governance.sqlite3 --proposal-id <proposal-id>
python -m axq.reflection proposal-transition-authorization-summary --store runtime/phase8-task11/governance.sqlite3
```
