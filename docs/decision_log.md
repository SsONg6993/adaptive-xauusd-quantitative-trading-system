# Architecture decision log

Dates record when the current repository baseline was ratified. Later reversals require a new entry;
do not silently rewrite earlier decisions.

## 2026-09-08 — Independent XAUUSD system

- **Decision:** Build a brand-new independent project; do not reuse unrelated previous EA code.
- **Reason:** Preserve clean assumptions, auditability, and ownership boundaries.
- **Consequence:** XAUUSD is the initial market and M5/M15/H1/H4 are the supported analysis frames.

## 2026-09-08 — Python intelligence, MQL5 safety and execution

- **Decision:** Python owns intelligence and orchestration; the future MQL5 EA owns broker-facing
  execution and hard safety checks.
- **Reason:** Use the strongest local ecosystem for analytics while retaining broker-native safety.
- **Consequence:** Deterministic risk controls and the EA may veto; agent advice never bypasses them.

## 2026-09-08 — Local-first operation

- **Decision:** Core inference is local-first with low recurring API cost. Paid LLM/news APIs remain
  optional. Serious training runs locally under user control.
- **Reason:** Reliability, privacy, cost control, and reproducibility.
- **Consequence:** Codex builds pipelines and runs tiny smoke tests unless heavier work is explicit.

## 2026-09-08 — Point-in-time market data

- **Decision:** Store internal timestamps as timezone-aware UTC. Higher-timeframe values become
  available only after their candles fully close. Features are causal at every timestamp.
- **Reason:** Prevent look-ahead leakage and broker-time ambiguity.
- **Consequence:** Swing confirmation is delayed; future-candle mutation must not change past features.

## 2026-09-08 — Versioned features and immutable datasets

- **Decision:** Bind feature manifests, label manifests, split manifests, source hashes, and Git
  identity into immutable Phase 3 dataset artifacts.
- **Reason:** Make every training input reproducible and auditable.
- **Consequence:** Incompatible identity, schema, order, chronology, or content fails loudly.

## 2026-09-08 — Conservative label ambiguity

- **Decision:** Same-bar TP/SL collision policy defaults to `AMBIGUOUS`.
- **Reason:** Candle OHLC cannot prove intrabar event ordering.
- **Consequence:** Alternative policies require explicit configuration or lower-timeframe evidence.

## 2026-09-08 — Chronological evaluation

- **Decision:** Support purge and embargo gaps; protect OOS from preprocessing, selection, fitting,
  and calibration.
- **Reason:** Overlapping forward labels and random splits otherwise leak future information.
- **Consequence:** TRAIN fits transforms/models, VALIDATION calibrates, and frozen artifacts alone
  inspect OOS.

## 2026-09-08 — Calibrated three-way Quant output

- **Decision:** Calibration uses VALIDATION only. `HOLD` is a valid outcome through the explicit
  neutral class or a configurable confidence threshold.
- **Reason:** Confidence quality matters, and forcing BUY/SELL creates false actionability.
- **Consequence:** Preserve BUY/SELL/HOLD coverage, confidence buckets, and Opportunity Utilization
  so later filters cannot silently eliminate trade frequency.

## 2026-09-08 — Explicit model lifecycle

- **Decision:** Models begin as `CANDIDATE`; Champion/Challenger promotion is explicit,
  multi-metric, evidence-based, and reversible.
- **Reason:** One metric or one OOS period cannot justify autonomous replacement.
- **Consequence:** No automatic promotion and no uncontrolled online mutation after each trade.

## 2026-09-08 — Controlled future learning and reporting

- **Decision:** Future learning uses scheduled, versioned retraining with drift review. Weekly
  reporting must retain predictions, outcomes, returns, MFE/MAE, confidence, regimes, versions, and
  success/failure attribution.
- **Reason:** Improvement must be measurable and auditable.
- **Consequence:** Online learning and full reporting remain future reviewed phases.

## 2026-09-09 — Separate Quant development layer

- **Decision:** Place experiment suites, walk-forward evaluation, ablation, drift, comparison, and
  tuning in `axq.quant.development` around the Phase 3–4 contracts rather than expanding the
  production trainer.
- **Reason:** Model-development orchestration has different recovery, reporting, and comparison
  responsibilities from one frozen production training run.
- **Consequence:** Phase 4 remains the ordinary manifest-bound training/inference path; Phase 5 jobs
  are content-addressed, atomic, resumable, auditable, and locally user-run.

## 2026-09-09 — Immutable final OOS is evaluation-only

- **Decision:** Final OOS cannot participate in tuning, feature selection, calibration, threshold
  selection, ablation choice, or model choice. Walk-forward development folds end before final OOS.
- **Reason:** Repeatedly consulting final OOS converts it into development data and invalidates the
  claimed generalization estimate.
- **Consequence:** Every development fold fits fresh preprocessing, selection, model, and calibration;
  fold models remain unregistered evidence. Optuna accepts only validation or walk-forward-validation
  objectives, and model promotion stays manual.

## 2026-09-09 — Tool-augmented agentic baseline; ML becomes optional

- **Decision:** V1 decisions must not require predictive ML. Tools produce facts, stateful specialist
  agents interpret them, and Phase 4/5 models remain optional `OptionalPredictiveModelTool` evidence
  and Challenger artifacts.
- **Reason:** Current experiments have not demonstrated stable enough temporal edge to make ML a
  mandatory runtime dependency, while the causal data and governance work remains valuable.
- **Consequence:** No current model is promoted automatically. The runtime remains useful when ML,
  an LLM, news, or the internet is unavailable.

## 2026-09-09 — One deterministic kernel for live and replay

- **Decision:** Live and historical replay share tools, agent contracts/state transitions, Master
  fusion, Discipline Guard, Risk logic, policy versions, and decision logging. Only clock,
  event/data sources, external-state adapters, and execution sinks may differ.
- **Reason:** A simplified parallel backtest strategy would drift from production behavior.
- **Consequence:** Events are replayed in causal availability order. Simulated execution models
  broker behavior and returns normal execution feedback; it contains no alternative strategy logic.

## 2026-09-09 — Shared runtime state includes broker/account truth

- **Decision:** Kernel state contains market snapshots and available MT5 balance, equity, free
  margin, floating and daily realized/unrealized P/L, drawdown, positions, pending orders, exposure,
  broker constraints, and execution feedback.
- **Reason:** Master, Discipline, and Risk decisions cannot be faithfully reproduced from candles.
- **Consequence:** State is versioned, UTC-timestamped, freshness-aware, and persisted with decision
  traces. Missing mandatory broker state fails closed for execution.

## 2026-09-09 — M5 thesis cadence with causal intrabar confirmation

- **Decision:** Completed M5 candles normally establish/update the primary thesis. Causally available
  ticks, completed M1 bars, or microstructure events may confirm or invalidate an existing scenario
  and make it entry-eligible before the next M5 close.
- **Reason:** Candle-close-only execution loses valid confirmation opportunities; unconstrained
  tick-level thesis creation increases noise, duplicates, and replay mismatch.
- **Consequence:** Intrabar events reference an existing `thesis_id`/`setup_id`, cannot see future
  M1/M5 values, and traverse the same Master, Discipline, Risk, and logging path.

## 2026-09-09 — Master, Discipline, Risk, and Reflection stay separate

- **Decision:** Master is structured evidence fusion, real-time Discipline is deterministic, Risk is
  an independent final veto, and Reflection may propose but never automatically apply changes.
- **Reason:** Interpretation, behavioral control, survival constraints, and offline learning require
  distinct authority and audit boundaries.
- **Consequence:** HOLD/ABSTAIN is valid, rejected opportunities are logged, and changes follow
  candidate → deterministic replay/walk-forward → explicit promotion.

## 2026-09-09 — Phase 6 closes at deterministic evidence

- **Decision:** The implemented shared semantic path is `RuntimeEvent -> reducer -> tools ->
  specialists -> scenario lifecycle -> EvidenceBundle`; live-like and journal replay use the same
  reducer, tools, specialists, scenario transitions, and trace identities.
- **Reason:** Closing at evidence establishes causal live/replay parity without prematurely coupling
  interpretation to trade authorization or broker behavior.
- **Consequence:** Master fusion, Discipline Guard, agentic Risk, execution, position management, and
  broker/P&L simulation remain explicitly unimplemented Phase 7+ work. Replay-only strategy logic is
  prohibited.

## 2026-09-09 — Append-only semantic runtime journal

- **Decision:** Persist content-addressed `JournalRecord` payloads with event, parent, and previous
  linkage plus explicit applied/duplicate/no-op/rejected outcomes. SQLite UPDATE and DELETE are
  blocked; database row IDs do not affect semantic identity.
- **Reason:** Live/replay parity and diagnosis require the exact causal facts, memory, evidence,
  thesis/scenario states, and outcomes that existed at decision time.
- **Consequence:** Exact duplicates are auditable no-ops, snapshot mismatches reject, and journal
  replay can reconstruct Phase 6 traces without revising history.

## 2026-09-09 — Phase 7 Risk is a separate deterministic final veto

- **Decision:** Only Discipline `PASS` enters the versioned financial Risk boundary. Risk consumes
  bounded causal runtime/account/broker facts, performs deterministic safety vetoes and sizing, and
  emits `PASS`, `REJECT`, `NO_ACTION`, or `EMERGENCY_STOP`; it never creates a broker instruction.
- **Reason:** Behavioral cadence, financial survival, and broker execution require separate
  authorities and independently auditable outcomes.
- **Consequence:** Missing or stale state fails closed, sizing reuses the established broker-spec
  primitive, equivalent live/replay inputs have identical identities, and only Risk `PASS` can reach
  a future execution boundary.

## 2026-09-09 — Phase 7 execution is provenance-bound and demo-safe

- **Decision:** Only a linked Risk `PASS` becomes a content-addressed `ExecutionIntent`. The shared
  adapter contract is disabled by default; the reference adapter permits demo accounts only and
  rechecks bounded pre-submit facts without altering direction, volume, stop, or thesis identity.
- **Reason:** Transport retries, changed broker conditions, and uncertain acknowledgements must not
  bypass Master, Discipline, Risk, or produce duplicate orders.
- **Consequence:** Stable intent IDs are reserved before submission. Duplicate and `UNKNOWN`
  submissions are never resent without future reconciliation; partial remainders are reported, not
  automatically resubmitted. Results enter the existing runtime execution-feedback path. Direct
  MT5/MQL5 transport and durable recovery remain unimplemented.

## 2026-09-09 — Execution recovery is append-only and fail-closed

- **Decision:** Durable execution state is reconstructed from append-only SQLite transitions.
  Reconciliation uses exact persisted linkage only; every later report explicitly supersedes the
  previous report, and checkpoints are recovery anchors rather than authority.
- **Reason:** Mutating UNKNOWN/CONFLICT history or heuristically pairing broker objects could hide
  duplicate exposure after a crash or lost acknowledgement.
- **Consequence:** UNKNOWN, broker-only/local-only objects, and ticket/direction/material-volume
  conflicts block safe resume until a new semantic reconciliation record resolves them. Broker-only
  remains a classifiable anomaly because manual trades may be legitimate. No mutable current-state
  execution table exists.

## 2026-09-09 — Restart recovery is a future safety gate

- **Decision:** Unattended runtime may resume only after journal flush/cursor restoration, MT5
  account/position/order reconciliation, missing-candle backfill, explicit continuity handling, TTL
  evaluation, and freshness validation.
- **Reason:** A process restart cannot safely infer broker truth or silently bridge missing intrabar
  history.
- **Consequence:** Phase 6 does not claim restart recovery; Phase 7+ entries must fail closed until the
  reconciliation gate is implemented and satisfied.

## 2026-09-09 — Local reasoning and self-improvement remain governed candidates

- **Decision:** A future local LLM may sit behind stable evidence/memory contracts with bounded modes,
  timeout, structured validation, provenance checks, and deterministic fallback. Evolution follows
  experience → reflection → proposal → replay/shadow comparison → explicit promotion.
- **Reason:** Reasoning experiments and agent/tool proposals must not mutate production behavior or
  weaken deterministic fallbacks.
- **Consequence:** No LLM, vision, reflection, automatic gap detection, or autonomous deployment is a
  Phase 6 dependency. Final OOS governance and manual promotion remain intact.

## 2026-09-10 — Open-position management is a separate deterministic boundary

- **Decision:** Manage an already-open position through a strict content-addressed context and pure
  evaluator that emits only `NO_ACTION`, `HOLD_POSITION`, `PROTECT_POSITION`, or `EXIT_POSITION`.
  Task 5 safe readiness and exact execution-to-position linkage are mandatory. V1 protection is
  limited to a monotonic, policy-enabled, broker-valid move toward break-even.
- **Reason:** Entry evidence cannot safely double as an exit, reversal, or trailing strategy, and
  uncertain broker state must never trigger autonomous position changes.
- **Consequence:** HOLD creates no modification, bearish evidence cannot silently reverse a long,
  and protection/exit outcomes remain append-only journal facts that require a future dedicated
  safety validation and transport. Scale-in/out, dynamic trailing, and broker submission are absent.

## 2026-09-10 — Position actions require independent action-time safety

- **Decision:** A `PositionManagementOutcome` cannot be transported directly. A separate immutable
  action context rechecks current authoritative position, exact execution/broker linkage, Task 5
  reconciliation/readiness, freshness, volume, and broker constraints. Only safety `PASS` creates a
  content-addressed `MODIFY_PROTECTIVE_STOP` or full `CLOSE_POSITION` intent.
- **Reason:** Broker/manual changes and elapsed time can invalidate an otherwise valid management
  recommendation before transport. A close is not an opposing entry, and stop normalization must
  never widen risk.
- **Consequence:** HOLD produces no intent; uncertain facts fail closed as `REJECT` or
  `EMERGENCY_BLOCK`. The runtime journal stores an idempotent append-only management → safety →
  intent chain. Position-action transport/results, reversal, scale-in/out, and broker calls remain
  unimplemented.

## 2026-09-10 — Task 8 uses a swappable direct MetaTrader5 demo gateway

- **Decision:** Implement a narrow lazy-loaded `MT5Gateway` with direct Python `order_check` then
  `order_send` adapters for demo entries, monotonic protective-stop changes, and exact full closes.
  Broker snapshots enter the existing recovery snapshot, runtime-event, and reducer path. Execution
  remains `DISABLED` by default; `DRY_RUN` performs the complete preflight and `order_check` but no
  mutating broker call.
- **Reason:** This closes the smallest testable broker boundary while preserving all upstream
  Master, Discipline, Risk, intent, recovery, reconciliation, and journaling contracts for a future
  MQL5/IPC transport.
- **Consequence:** Demo mode must be proven from the current account immediately before mutation.
  Broker acceptance is authoritative even after a passing check. An exception, absent response, or
  uninterpretable acknowledgement after submission becomes append-only `UNKNOWN` and is never
  resent automatically. Position actions have their own durable reservation/result transitions and
  can only address an exact ticket; live money, fuzzy symbol/ticket matching, reversal, scale-in,
  runtime orchestration, MQL5/IPC, and a simulated broker remain absent.

## 2026-09-10 — Task 9 composes one restart-safe replay/shadow/demo runtime

- **Decision:** Add a narrow `RuntimeOrchestrator` that restores committed semantic state, acquires
  broker truth in live-like modes, performs exact reconciliation/readiness, invokes one injected
  decision-cycle processor, dispatches only in DEMO, routes results through canonical events, and
  coordinates checkpoint/flush/close. `DISABLED` is the checked-in default; there is no live mode.
- **Reason:** Continuous demo operation and daily host restarts require deterministic sequencing,
  but duplicating Master, Discipline, Risk, position-management, or broker semantics inside a loop
  would break live/replay parity and auditability.
- **Consequence:** Replay, shadow, and demo share semantic contracts. Shadow journals would-act
  intents without mutation. DEMO reacquires readiness before every action; UNKNOWN or reconciliation
  anomalies block autonomy. Runtime paths and terminal location remain operational metadata.

## 2026-09-10 — Phase 8 experiences are exact, immutable facts before reflection

- **Decision:** Normalize Phase 7 journal, ledger, and replay outcomes into content-addressed actual
  experience records joined only by persisted semantic IDs, then store them in append-only SQLite.
  Counterfactual experiences use a separate explicitly simulated contract.
- **Reason:** Reliability analysis and future reflection need queryable causal facts without fuzzy
  timestamp inference, fabricated values, mutable history, or accidental mixing of actual and
  simulated outcomes.
- **Consequence:** Missing exact links produce explicit incomplete attribution. Replay validation
  retains only fixed-size `RUNTIME_EVENT` and `AGENT_EVIDENCE` runner records needed by attribution,
  while downstream Phase 7 semantics remain journaled by the orchestrator. Task 1 exposes only
  deterministic descriptive analytics; Reflection, proposals, graph/vector indexing, LLMs, tuning,
  and policy mutation remain outside scope.

## 2026-09-11 — Daily reflection is causal, guarded, and append-only

- **Decision:** Aggregate immutable experiences by half-open UTC day using `available_at`, under a
  content-addressed diagnostic `ReflectionPolicy`. Persist immutable findings and explicit
  `PASSED`, `INSUFFICIENT`, or `UNAVAILABLE` sample guards; revisions must append and name the latest
  same-day reflection they supersede.
- **Reason:** Reflection must distinguish knowledge time from trade time, avoid invented conclusions
  from weak or missing samples, and retain an auditable history when source attribution is revised.
- **Consequence:** Canonical JSON and exact experience IDs determine identity. Identical reruns are
  idempotent. Daily findings remain descriptive and cannot tune Master, Discipline, Risk,
  execution, or position-management behavior. Weekly reflection, proposals, graphs, RAG, LLMs, and
  runtime mutation remain outside Task 2.

## 2026-09-11 — Weekly patterns begin as observations and advance only explicitly

- **Decision:** Aggregate terminal Daily Reflections into ISO Monday-to-Monday UTC records, validate
  every exact Experience source, and suppress patterns for incomplete weeks. New success/failure
  patterns always start as `OBSERVATION`; later status changes are explicit immutable operator or
  evaluation actions replayed as a linear chain.
- **Reason:** Repeated evidence should be queryable without turning descriptive recurrence into
  hidden truth, while incomplete coverage and revised daily attribution must remain auditable.
- **Consequence:** Pattern keys bind only stable semantics and recur across weeks, while observation
  IDs bind interval and evidence. Weekly revisions and lifecycle transitions append and supersede;
  no mutable status, automatic validation, proposal, tuning, or runtime mutation exists.

## 2026-09-11 — Improvement proposals are recurring-evidence advisories

- **Decision:** Create one immutable advisory proposal only when a semantic pattern key recurs in at
  least two complete weeks and every required completeness, provenance, day-support, and
  experience-support guard passes. Revalidate every exact pattern/finding/daily/Experience link.
- **Reason:** A single observation or copied identifier is insufficient authority for a change,
  while repeated guarded evidence should be reviewable through a stable, auditable artifact.
- **Consequence:** Proposals use deterministic templates, start as `OBSERVATION`, supersede rather
  than overwrite when evidence changes, and advance only through explicit append-only actions.
  `VALIDATED` means evidence status only; no code, config, runtime, replay, or broker mutation occurs.

## 2026-09-11 — Proposal evaluation is preregistered evidence, not deployment authority

- **Decision:** Register an immutable evaluation candidate and plan only for an exact proposal whose
  replayed lifecycle status is `CANDIDATE`. Persist supplied observations, plan-derived criterion
  outcomes, and a separate operator evidence decision as append-only content-addressed records.
- **Reason:** Criteria defined after seeing results permit selection leakage, while combining an
  evidence judgment with proposal promotion or deployment would erase the operator boundary.
- **Consequence:** Plans precede results and copy the proposal's exact canonical provenance. Final
  OOS observations are retained only for reporting and cannot influence selection, tuning,
  calibration, or acceptance. `ACCEPT_EVIDENCE`, `REJECT_EVIDENCE`, and `DEFER` never transition a
  proposal or mutate code, configuration, models, runtime, or deployment state.
