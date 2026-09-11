# Phase 8 Task 10 Governed Operator Review Bridge Design

## Scope

Task 10 appends explicit human evidence judgments to an already-persisted immutable paired result.
It adds no evaluation, tuning, proposal lifecycle transition, deployment, runtime mutation, Final
OOS input, or broker path.

## Contract

`PairedEvaluationReview` is frozen and content-addressed. Its identity binds exact result/request/
proposal/candidate/plan IDs; `ACCEPT_EVIDENCE`, `REJECT_EVIDENCE`, or `DEFER`; operator/action/reason;
strict-UTC `effective_at`; normalized supporting evaluation and paired-result IDs; and its optional
predecessor. Because `effective_at` is a semantic operator fact, it participates in identity.

## Linear-chain persistence

Migration 014 contains a single append-only review table. The first review requires no predecessor.
Every later review names the current terminal review for the same paired result. Identical retries
reuse the same ID before terminal-chain validation; stale parents, forks, backward effective times,
missing authorities, approximate linkage, and corrupt history fail closed. There is no mutable
current-state table; replay derives the terminal review.

## Safety boundary

The store verifies immutable paired-result/request linkage and any supporting result links. It never
writes proposal lifecycle or paired-result records. Tests snapshot proposal status and canonical
paired-result bytes across review insertion. Task 10 imports no execution, replay, Final OOS, runtime,
or MT5 boundary.
