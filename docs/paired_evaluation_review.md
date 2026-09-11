# Governed paired-evaluation review

Phase 8 Task 10 adds a human evidence-review boundary after an immutable paired evaluation result.
`PairedEvaluationReview` binds the exact result, request, proposal, candidate, and plan. It records
only `ACCEPT_EVIDENCE`, `REJECT_EVIDENCE`, or `DEFER`, plus an explicit operator, action, reason, and
strict-UTC effective time. Review is audit evidence: it cannot promote a proposal, deploy a
candidate, change criteria, mutate runtime policy, access Final OOS, or contact a broker.

## Identity and history

Review identity includes every semantic field, including `effective_at`, normalized supporting
evaluation-result IDs, normalized supporting paired-result IDs, and `previous_review_id`. Supporting
IDs are sorted and deduplicated before hashing. The first review has no predecessor; every later
review must name the current terminal review. An identical retry reuses its review ID, while stale
or forked predecessors fail closed.

Migration 014 stores one append-only review table. UPDATE and DELETE are rejected. There is no
mutable current-review table: current state is derived by replaying the exact linear history. A
corrupt identity or predecessor chain fails validation.

## Commands

The JSON supplied to `record` must already contain the content-addressed review and exact links to
records in the same governance store.

```powershell
$env:PYTHONPATH = (Resolve-Path 'src')
python -m axq.reflection record-paired-evaluation-review --store runtime/phase8-task10/governance.sqlite3 --review paired-review.json
python -m axq.reflection show-paired-evaluation-review --store runtime/phase8-task10/governance.sqlite3 --review-id <review-id>
python -m axq.reflection show-paired-evaluation-review-history --store runtime/phase8-task10/governance.sqlite3 --result-id <paired-result-id>
python -m axq.reflection paired-evaluation-review-summary --store runtime/phase8-task10/governance.sqlite3
```

The CLI has no execution, Final OOS, proposal transition, deployment, runtime, or broker option.
