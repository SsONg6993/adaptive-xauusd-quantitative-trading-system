# Tool-Augmented Agentic Architecture

## Status and scope

This document describes the implemented Phase 6 deterministic evidence baseline and the approved
future direction. It does not rewrite Phase 4/5 history or delete their contracts. Predictive ML,
local LLMs, external news providers, and chart vision are optional evidence sources; only the
predictive-model adapter contract exists today.

## Invariants

- Tools calculate facts; agents interpret facts and maintain falsifiable hypotheses.
- Master fuses evidence. It is not majority voting and an LLM cannot freely authorize a trade.
- Discipline Guard is deterministic and separate from Master and Risk.
- Deterministic Risk is the final Python veto; the MQL5 EA repeats broker-observable safety checks.
- Live and replay execute one shared decision kernel. No simplified backtest strategy is allowed.
- Final OOS remains excluded from tuning, selection, calibration, thresholds, ablations, and choice.
- All state/events use timezone-aware UTC and causal `available_at` semantics.
- Missing mandatory state fails closed; HOLD/ABSTAIN is a valid outcome.

## Shared runtime state

Each kernel step receives an immutable, versioned `SharedRuntimeState` assembled only from events available
at that step. It contains:

- `MarketSnapshot`: completed M5/M15/H1/H4 bars, current tick/M1 facts when supplied, causal features,
  sessions, spread, freshness, and manifest/version identities.
- `AccountState`: balance, equity, free/used margin, margin level, floating P/L, daily realized and
  unrealized P/L, daily starting equity, peak equity, daily/total drawdown, currency, and freshness.
- `PositionState`: broker/position ID, symbol, side, volume, open/current price, SL/TP, floating P/L,
  swap/commission, open time, setup/thesis linkage, and exposure.
- `PendingOrderState`: order ID/type, price, volume, SL/TP, expiry, setup/thesis linkage, and status.
- `ExposureState`: gross/net lots and notional by symbol/direction plus portfolio totals.
- `ExecutionFeedback`: submitted/accepted/rejected/filled/partially-filled/cancelled/closed status,
  broker codes, prices, volume, slippage, costs, timestamps, and idempotency linkage.
- `BrokerConstraints`, `ComponentFreshness`, source/event cursors, slow-path context, and the latest
  execution feedback.

Unavailable optional fields remain explicit. Execution-relevant account/broker state has configured
freshness limits and cannot be silently defaulted.

## Event model and causality

Events carry `event_id`, `event_type`, `observed_at`, `available_at`, source, source version, stable
source sequence, and payload hash. The kernel orders them by `(available_at, source_sequence,
event_id)`. A replay clock advances to event availability; production uses a UTC system clock.

`RuntimeEventType` currently includes `M5_CLOSED`, `HTF_CLOSED`, `TICK`, `M1_CLOSED`,
`ACCOUNT_UPDATED`, `POSITIONS_UPDATED`, `ORDERS_UPDATED`, `EXECUTION_FEEDBACK`, and
`SLOW_CONTEXT_UPDATED`. Identity hashes event type/times, source/version/sequence, symbol, and payload;
arrival-only `ingested_at` is excluded. Strict schemas reject naive timestamps and require
`event_time <= observed_at <= available_at`. A partial M1 candle is never a completed-bar fact.
`SystemUTCClock` and `ReplayClock` implement the live-like/replay clock boundary;
`InMemoryEventSource` provides deterministic causal ordering, and the pure deterministic
`reduce_state` function creates a new state without mutating its predecessor.

## Thesis and intrabar scenario lifecycle

A completed M5 candle establishes or updates a primary `thesis_id` and bounded scenario branches.
The scenario lifecycle is `DEVELOPING`, `CONFIRMED`, `ENTRY_ELIGIBLE`,
`INVALIDATED`, or `EXPIRED`.

Between M5 closes, completed M1 or tick events may confirm or invalidate an existing scenario. They
cannot create an unrelated primary thesis. Reversal requires a distinct hypothesis/thesis identity,
and an invalidated or expired thesis cannot be revived. `EntryEligibility` is evidence state only;
it creates no trade proposal or instruction. `ContinuityStatus` explicitly records missing intrabar
history. Replay invokes the same transition function and event types.

## Tools and specialist agents

The fact-only tool contracts are `CausalFeatureSnapshot`, `ToolInput`, `ToolFact`, `ToolResult`, and
`ToolCatalog`. Feature tools expose existing causal values without recomputing formulas, and every
result binds provenance, availability, freshness, quality, state, and snapshot identity. The
`OptionalPredictiveModelTool` returns unavailable evidence when no verified Phase 4 model is present;
it never emits execution permission. `HistoricalSimilarityTool` is likewise provider-driven.

The deterministic specialist baselines enforce these exact observation boundaries:

- Chart: structure, breakout, volatility, and session/context.
- Quant: trend, momentum, volatility, statistics, volume, and optional predictive-model facts.
- Historical: historical similarity and session/context.
- Regime: trend, volatility, breakout, statistics, and session/context.
- News: supplied slow context only.

Ordinary `AgentInput` is account-free. These market specialists cannot inspect balance, equity,
margin, P/L, positions, pending orders, exposure, or execution feedback.

Every agent output includes objective/version, snapshot/state IDs, hypothesis, optional direction,
confidence, evidence for/against, invalidation conditions, uncertainty, freshness, scenario status,
requested tools, previous-hypothesis reference, and abstention reason. Agents never size positions or
bypass downstream controls.

`AgentMemory` persists the prior hypothesis and transition state. `AgentEvidence` and memory are
content-addressed. `EvidenceKernel` evaluates tools, invokes specialists in fixed order, updates
memories, and emits a deterministic `EvidenceBundle`. An optional-agent failure degrades or abstains
through structured evidence; it does not fabricate facts. Phase 6 stops here.

## Master, Discipline, and Risk baselines and downstream authority

Phase 7 Task 1 implements pure deterministic Master evidence fusion. It produces normalized bullish
and bearish support, within-agent contradiction, cross-agent disagreement, uncertainty, confidence,
and an advisory BUY/SELL/HOLD `MasterProposal`. `FusionPolicy` weights and gates are fixed, versioned,
and content-addressed; they cannot adapt online.

Phase 7 Task 2 implements the deterministic Discipline Guard as a pure boundary downstream of
`MasterProposal`. Explicit versioned policy and causal state govern stable proposal/setup/thesis
duplicates, simultaneous positions, daily/session trade caps, ordinary and stop-loss cooldowns,
consecutive-loss pauses, and tightly bounded re-entry. It emits `PASS`, `REJECT`, `PAUSE`, or
`NO_ACTION`; only `PASS` may proceed to downstream Risk. It does not calculate financial risk, size a
position, or authorize execution. Demo policy content explicitly declares that a non-loss exit resets
the loss streak; applying that recorded transition belongs to the future event/state integration and
is not hidden inside the pure evaluator.

Phase 7 Task 3 implements the separate deterministic financial Risk boundary. Only Discipline
`PASS` enters evaluation. Versioned policy gates causal freshness, account completeness and
consistency, free margin, margin level, normalized drawdown, position/order commitments, projected
lot exposure, spread/slippage, stop direction/distance, broker stop/freeze constraints, and the kill
switch. Broker-specification sizing reuses the established risk-budget and downward lot-step
normalization primitive. Risk `PASS` is merely eligible for the separate execution boundary; Risk
creates no broker instruction. The future EA retains final broker validation and protection.

## Implemented shared path and future paths

The implemented live-like/replay semantic path is:

`RuntimeEvent -> reducer -> tools -> specialists -> scenario lifecycle -> EvidenceBundle`

`EvidenceBundle -> MasterProposal -> DisciplineOutcome -> RiskOutcome -> ExecutionIntent -> ExecutionResult`

`RuntimeStreamRunner` remains the Phase 6 harness. Only clocks, event sources, external adapters,
persistence backends, and execution transports may differ. Replay-only strategy logic is rejected.
Task 4 establishes the shared intent/result contract and feeds results back through the runtime
event reducer; later orchestration may append the adapter without changing upstream decisions.

The slow path performs news/macro enrichment, similarity work, attribution, reflection, and candidate
change generation. It publishes immutable, effective-at snapshots. It cannot mutate live policies or
production models. Candidate changes require offline replay/walk-forward comparison and explicit
promotion.

## Runtime journal and replay parity

`JournalRecord` stores an immutable semantic payload with causal availability, event linkage, optional
parent linkage, and optional previous-version linkage. Its supported record types are runtime event,
runtime state, feature snapshot, tool result, agent input, agent evidence, agent memory, evidence
bundle, thesis state, scenario state, and outcome. `JournalOutcome` records `APPLIED`, `DUPLICATE`,
`NO_OP`, or `REJECTED` with a reason code.

The SQLite implementation is append-only: additive migration `002_agentic_runtime.sql` creates the
journal and UPDATE/DELETE triggers reject mutation. Database row sequence is storage ordering and is
excluded from semantic identity. Exact duplicate event/snapshot input returns the original semantic
step and records a duplicate outcome; a changed snapshot for the same event is rejected. Rejections
and scenario/thesis transitions are journaled without erasing previous state.

`JournalEventSource` reconstructs events in causal order. Live-like and journal replay tests require
identical state, tool, input, evidence, memory, bundle, thesis/scenario, eligibility, and trace IDs.
`ContinuityStatus` survives journaling, so missing intrabar history is not silently healed. This is
replay-from-journal readiness, not a broker/P&L backtest engine.

## Live/replay ports

| Shared core | Replaceable port |
|---|---|
| State reducer, tools, agents, scenario lifecycle, evidence/trace writer | `Clock` |
| Same | market/account/order/context `EventSource` |
| Same through `ExecutionIntent`/`ExecutionResult` | MQL5 or deterministic simulated execution transport (future) |
| Same | durable live journal or immutable replay input reader |

Parity tests feed identical canonical events through live-like and journal-replay adapters and
require identical Phase 6 semantic trace IDs. Phase 7 must extend parity through proposals, vetoes,
and execution feedback.

## Operational restart requirement (future)

Unattended operation must eventually support daily shutdown/restart through graceful shutdown,
journal flush, last processed cursor persistence, startup MT5/account/position/order reconciliation,
open-position resync, missing-candle backfill, explicit missing-intrabar continuity, thesis/scenario
TTLs, stale-state checks, and safe resume only after reconciliation and freshness validation. None of
this recovery workflow is implemented in Phase 6.

## Optional local reasoning and controlled evolution (future)

Specialists may later use a local LLM behind the stable `AgentEvidence`/`AgentMemory` contracts. The
backend must support a fast reasoning mode, a deep reasoning mode, latency and token/output budgets,
timeout, structured-
output validation, deterministic fallback, and fact/provenance consistency checks. Llama, Qwen, and
DeepSeek experiments are exploratory; no specific model is an implemented dependency.

Controlled improvement follows `live/demo experience -> reflection -> meta-reflection -> candidate
proposal -> recent replay/shadow -> compare -> explicit promotion`. Agents may propose new or changed
tools, changed/merged specialists, or a new specialist, but cannot deploy them autonomously. Improve
a tool or existing specialist before adding another specialist where practical.

Traditional large backtesting is not the sole development authority. Live Demo experience is an
important future learning source, recent rolling replay validates candidates, and shadow mode is the
intended challenger path. Historical replay remains essential for safety, regression, and parity.
Phase 3–5 Final OOS governance remains unchanged.

## Existing components reused

- UTC validation, completed-bar synchronization, MT5 ingestion, and missing-data policy.
- Phase 2 causal feature registry, manifests, warm-up, sessions, and market structure.
- Phase 3 immutable datasets, labels, chronological splits, and replay-safe identities.
- `AgentPrediction`, `MasterDecision`, `RiskDecision`, and `ExecutionInstruction` as compatibility
  contracts while additive agent-evidence/runtime-state schemas are introduced.
- Deterministic risk sizing/veto functions and SQLite decision-chain tables.
- Phase 4 Quant artifacts/inference/registry as an optional predictive tool.
- Phase 5 experiment, walk-forward, ablation, drift, and Challenger evidence tooling.

## Explicitly untouched

Phase 3 datasets and final OOS governance, Phase 4 trainer/inference identity, Phase 5 development
orchestration, registry promotion rules, current feature formulas, and future MQL5 hard-safety
authority are not weakened or replaced by this migration.

## Phase 7 Task 4 execution-entry boundary

Only a linked Risk `PASS` may become a deterministic `ExecutionIntent`. That contract retains the
EvidenceBundle, Master, Discipline, Risk, setup, thesis, scenario, symbol, direction, approved size,
entry, stop, causal times, policy, and broker-symbol provenance. Execution cannot invent direction,
increase volume, widen the approved stop, or add an unapproved target.

`ExecutionAdapter.execute(intent)` is shared by live and replay orchestration. Its transport is the
replaceable port. The demo reference adapter is disabled by default, blocks live-account submission,
rechecks bounded pre-submit observations, reserves the intent ID before transport, and returns an
explicit `UNKNOWN` state when acknowledgement is uncertain. It never retries a partial remainder or
an unknown submission. Results convert to the existing runtime `EXECUTION_FEEDBACK` event.

Task 5 supplies durable append-only execution transitions and recovery anchors. Reconciliation uses
only exact persisted broker linkage, treats broker-only objects as explicit classifiable anomalies,
and appends superseding resolution reports. A separate safe-resume contract blocks new entries until
canonical broker/runtime components are fresh, execution ambiguity is resolved, and thesis/intrabar
continuity is valid. Neither reconciliation nor readiness changes Master, Discipline, or Risk.

## Phase 7 Task 6 position-management core

Position management is separate from entry selection. A strict content-addressed context binds one
authoritative open position to its original execution intent/result, exact broker-object linkage,
setup/thesis/scenario provenance, current lifecycle, optional evidence, component freshness,
reconciliation, and safe-resume result. Missing linkage, stale state, incomplete continuity,
UNKNOWN execution, or unresolved broker anomalies produce `NO_ACTION` rather than guessed management.

The pure evaluator emits only `NO_ACTION`, `HOLD_POSITION`, `PROTECT_POSITION`, or `EXIT_POSITION`.
HOLD creates no modification. V1 protection is limited to a policy-enabled, age-qualified,
broker-valid stop movement toward break-even and cannot widen risk for either long or short
positions. Invalidation/expiry can request exit, but neither protection nor exit is sent to a broker;
a future dedicated safety boundary and transport must still validate it. Bearish evidence against a
long may request exit but never silently reverses it into a short.

## Phase 7 Task 7 position-action safety boundary

`PositionManagementOutcome` says what should happen to an open position; it is not a broker action.
Task 7 independently binds that recommendation to current authoritative position, account, broker,
reconciliation, readiness, and exact execution-linkage facts. The pure boundary emits `NO_ACTION`,
`PASS`, `REJECT`, or `EMERGENCY_BLOCK`. Only `PASS` can produce a `PositionActionIntent`.

V1 position-action intents are limited to `MODIFY_PROTECTIVE_STOP` and `CLOSE_POSITION`. Stop
modification rechecks current SL, directional monotonicity, original approved risk when no SL is
present, point/tick normalization, stops/freeze distance, tradability, and fresh bid/ask facts.
Normalization may only tighten risk. Close targets the exact linked broker position and its full
current volume; it is never represented as a new opposing entry. Stable content identities and the
typed runtime-journal chain are shared by live and replay.

`PositionActionIntent` remains semantic input to a future transport. It is neither broker
authorization nor evidence that a modification or close occurred.

## Explicitly unimplemented after Phase 7 Task 7

MT5/MQL5 entry or position-action transport and transport result; broker snapshot acquisition; a simulated
broker/trade-P&L model; missing-candle backfill; persistent orchestration around restart restoration;
Ollama/local-LLM integration; chart vision; reflection/weekly learning; autonomous tool- or
agent-gap detection; and autonomous architecture evolution.

## Deferred risks

- Broker tick ordering, missing ticks/M1 bars, clock skew, and restart recovery.
- Conservative deterministic fill/slippage/latency modeling without false precision.
- State reconciliation after partial fills, manual broker actions, or connection gaps.
- Stable setup/thesis identity across process restarts and harmless data revisions.
- Bounded agent latency and deterministic handling of stale/failed optional evidence.
- Recording exact slow-path context so replay does not use revised future knowledge.
- Database evolution from direction-centric `agent_predictions` to richer evidence without breaking
  Phase 4 consumers.
