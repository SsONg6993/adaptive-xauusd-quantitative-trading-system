# System architecture (Phase 0-7 baseline)

## Safety invariant

The system is an evidence pipeline, not an autonomous risk authority. Python may propose a
`BUY`, `SELL`, or `HOLD`; deterministic risk code may only approve or veto it; the MT5 EA
independently revalidates every approved instruction. Any ambiguity, stale data, missing model,
unhealthy dependency, malformed message, or broken heartbeat produces **no new trade**. Existing
positions retain broker-side SL/TP protection.

## Runtime flow and trust boundaries

```text
live MT5 adapters -----------┐
                             ├-> shared runtime state -> deterministic decision kernel
historical replay adapters --┘                              |
                              tools -> specialist agents -> scenario lifecycle
                                                         -> EvidenceBundle
                                                         -> MasterProposal (Phase 7 Task 1)
                                                         -> DisciplineOutcome (Phase 7 Task 2)
                                                         -> RiskOutcome (Phase 7 Task 3)
                                                         -> ExecutionIntent (Phase 7 Task 4)
                                                         -> ExecutionAdapter -> ExecutionResult
                                                                  |
                                    live MT5 sink or simulated execution sink
                                                                  |
                           execution feedback -> state + decision journal

authoritative open position + exact execution/thesis linkage + safe readiness
                           -> PositionManagementOutcome (Phase 7 Task 6)
                              [NO_ACTION | HOLD | PROTECT | EXIT]
                           -> future dedicated safety validation and transport
```

Agent execution will use bounded timeouts and independent failures. The master excludes stale or
failed agents and may emit `HOLD`; it never fills in fabricated evidence. External news is data,
never an instruction channel. Paid LLM and news integrations are disabled by default.

Each decision chain carries snapshot, prediction, master-decision, risk-decision, instruction,
order, and broker-ticket identifiers. JSON logs and database rows reconstruct the chain.

Shared runtime state is broader than price data. It contains the causal market snapshot; MT5
balance, equity, free margin, floating P/L, daily realized/unrealized P/L, and drawdown; open
positions; pending orders; directional/aggregate exposure; broker constraints; component freshness;
and execution acknowledgements, rejections, and fills where available.

## Shared deterministic kernel and replay invariant

There is one analytical implementation. Live-like and replay inject ordered events into the same
kernel and receive the same typed semantic trace. The implemented shared path is:

`RuntimeEvent -> reducer -> tools -> specialists -> scenario lifecycle -> EvidenceBundle`

Only the clock, source, external adapters, persistence backend, and execution transport may differ.
Replay-only strategy logic is forbidden. The pure Phase 7 Master, Discipline, and Risk boundaries
consume the same evidence, policies, causal contexts, and states in either mode. Future execution
must be added after this shared path and used unchanged by both modes.

Every event records observation time, causal availability time, source sequence/version, and a
content-derived identity. Replay orders by availability and stable sequence; it never reconstructs
future context from final data. Slow-path news/LLM/historical context is replayed as the exact as-of
snapshot available live. The fast path reads the latest valid snapshot and never waits for it.

A simulated execution sink is not implemented. When added, it must consume the shared
`ExecutionIntent`, return the normal execution-feedback contract, and contain no alternative entry,
Master, Discipline, or Risk logic. The Task 4 demo adapter is a guarded boundary around an injected
transport, not a broker simulator or direct MT5 implementation.

Phase 7 Task 5 persists execution reservations/results/reconciliation as immutable SQLite
transitions. Current execution state is reconstructed from those transitions; no mutable projection
table exists. Broker reconciliation uses only exact persisted intent, ticket, transport, or client
linkage. New reports append and supersede older reports rather than rewriting UNKNOWN or CONFLICT.
`BROKER_ONLY` remains an operator-visible anomaly, not presumed corruption.

Startup readiness is a distinct operational gate after reconciliation. It requires fresh canonical
market/account/position/order/exposure/broker-constraint state, resolved execution anomalies, and
valid thesis continuity. Broker snapshots refresh shared state through normal `RuntimeEvent` and
reducer paths. Recovery checkpoints accelerate restart but never replace transition history.

Phase 7 Task 6 adds a separate pure decision core for already-open positions. It binds one
authoritative position to its original intent/result and exact persisted broker linkage, current
thesis/scenario state, optional evidence, fresh account/position/broker facts, reconciliation, and
safe-resume state. Entry decisions are never interpreted as position actions. `HOLD_POSITION`
generates no modification; `PROTECT_POSITION` can only request a monotonic broker-valid stop change;
and `EXIT_POSITION` is an explicit request that still requires future safety validation and
transport. Equivalent live/replay contexts use the same evaluator.

## Primary and intrabar paths

A completed M5 candle is the default primary-decision cadence and may create, replace, or invalidate
a thesis. Higher-timeframe facts remain available only after candle close. Between M5 closes,
causally available ticks, completed M1 bars, and later microstructure facts may update an existing
scenario as developing, confirmed, invalidated, expired, or entry-eligible; they may not silently
create an unrelated thesis.

An intrabar update references the existing thesis/hypothesis identities. A reversal requires a
distinct hypothesis identity; invalidated or expired theses cannot be revived. `ENTRY_ELIGIBLE` is
evidence state, not a proposal or execution permission. `ContinuityStatus` preserves whether the
intrabar path is complete or missing, and replay uses the identical transition function.

## Tool-augmented agents and optional ML

Tools are fact producers: indicators, structure, sessions, similarity, event proximity, spread, and
context. Agents have bounded objectives/observations, persistent hypotheses,
evidence for and against, confidence, invalidation, freshness, previous-state comparison, and
abstention. Master is structured evidence fusion, not majority voting or an unconstrained LLM.

The Phase 4/5 Quant stack remains intact as an optional predictive-model tool. It may contribute
structured Quant evidence only after reviewed results, is not required for V1, and cannot bypass
Master, Discipline, Risk, registry governance, or immutable final OOS. See
[agentic architecture](agentic_architecture.md).

Ordinary `AgentInput` is deliberately account-free. Market specialists cannot inspect balance,
equity, margin, P/L, positions, orders, or exposure; those values remain in shared runtime state for
the Discipline/Risk components with explicit authority.

## Technology choices

| Concern | V1 choice | Reason |
|---|---|---|
| Intelligence | Python 3.11+, pandas/NumPy, Pydantic | mature local analytics and strict message validation |
| ML later | scikit-learn; optional XGBoost/LightGBM/PyTorch/ONNX Runtime | CPU baselines plus local GPU training and portable inference |
| Broker data | official `MetaTrader5` Python package | direct bounded bar retrieval from the local terminal |
| Execution | MQL5 EA | broker-native order checks, SL/TP, trailing, and protection after Python fails |
| Persistence | SQLite in WAL mode behind a small adapter | zero-service V1 deployment; explicit repository boundaries allow PostgreSQL later |
| Configuration | YAML + environment overrides | reviewable defaults; secrets remain environment-only |
| Contracts | Pydantic schema v1 messages | reject unknown/malformed fields and constrain ranges |
| Logs | JSON Lines | searchable, append-friendly, correlation-ready |
| IPC | atomic files in MT5 Common Files, ACK/state files | no DLL, port, or WebRequest allow-list; durable and debuggable at M5 cadence |

MetaQuotes documents that MT5 bar times are UTC and that availability is limited by terminal chart
history, so ingestion uses timezone-aware UTC inputs and validates returned coverage
([MT5 `copy_rates_range`](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py)).

## Quant development boundary

Phase 5 adds `axq.quant.development` around, not inside, the Phase 4 production trainer. Ordinary
manifest-bound runs continue through the frozen Phase 4 TRAIN/VALIDATION/final-OOS path. Experiment
suites, walk-forward folds, ablations, drift reports, comparison, and tuning preparation live in the
separate development layer.

The immutable final OOS partition is evaluation-only. Development fold generation stops at its
starting index, every fold independently fits preprocessing, feature selection, model, and
calibration, and fold models never enter the lifecycle registry. Content-derived run/fold identities,
atomic status, artifact hashes, and skip-on-verified-completion make local jobs auditable and
resumable without introducing autonomous model choice.

## Python and MT5 boundaries

Python owns data retrieval/normalization, feature computation, local model inference, agent
performance, regime classification, master aggregation, deterministic account-level risk policy,
instruction persistence, experiments, and observability. Python never assumes an order executed.

The EA owns final symbol/account inspection, instruction age/idempotency validation, current spread,
broker stop/freeze levels, deterministic volume recalculation/capping, `OrderCheck`, placement,
broker result logging, SL/TP, trailing/breakeven, and protection of open positions during a Python
outage. The EA rejects rather than repairs materially invalid instructions.

## IPC decision

| Option | Deployment | Recovery/audit | V1 assessment |
|---|---|---|---|
| Atomic file queue | built into Python/MQL5; shared Common Files directory | durable, inspectable, replay-protected | **selected** |
| Local HTTP | simple Python server; MT5 URL allow-list and request lifecycle | good APIs, extra service/configuration | viable V2 |
| Native socket | low latency | framing, reconnect, auth, partial-message handling | unnecessary at bar cadence |
| Named pipe | Windows-local and fast | reconnect/overlapped I/O complexity | viable if throughput grows |
| ZeroMQ | strong messaging patterns | external DLL/binding/deployment dependency | defer |

Protocol: Python writes a versioned JSON document to a temporary file, flushes it, then atomically
renames it to `<idempotency_key>.ready.json`. The EA processes each key at most once and emits an
immutable ACK/result file. Both sides write heartbeat state; an instruction expires quickly and is
never replayed after restart. Directories are access-controlled to the VPS service account. Future
implementation must add schema fixtures shared with MQL5 and chaos tests for partial writes, clock
skew, duplicates, and restarts.

## Data pipeline and synchronization

Raw files are append-only and identified by checksums in a dataset manifest. Cleaning normalizes
UTC/types/order and resolves exact duplicate timestamps under an explicit policy; it never imputes
OHLC. Validation checks schema, chronology, duplicates, OHLC invariants, positivity, spread/volume,
and interval gaps. Weekend, holiday, session, and outage gaps remain reported until classified.

MT5 timestamps identify bar opens. For a base M5 row at time `t`, an H1 row opened at `h` is usable
only when `h + 1 hour <= t`; likewise for every timeframe. `merge_asof` joins on this `available_at`
time. This intentionally delays higher-timeframe information until the candle is complete.

Time-series splits are chronological with optional gaps/purging for overlapping labels. Scalers,
feature selection, correlations, and imputers fit on training data only. Scikit-learn explicitly
warns that fitting preprocessing on test data leaks information and provides ordered
`TimeSeriesSplit` for time data ([common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html),
[`TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)).

## Feature layer

Phase 2 is a deterministic, versioned, causal transformation layer. Each registered family declares
source columns, implementation version, parameters, conservative lookback, and causal status.
Canonical per-output manifests are written beside built datasets. Early invalid values and
data-dependent undefined values remain NaN. Confirmed pivots are emitted only after their configured
right-side confirmation delay. See [the feature contract](features.md).

M15/H1/H4 input values are joined on candle close availability, with source-open and available-at
timestamps retained. Session features convert UTC timestamps through IANA Asia/Tokyo,
Europe/London, and America/New_York zones, so DST and cross-region transition mismatches are
represented without static UTC-hour assumptions.

## Database architecture

Migration `001_initial.sql` defines candles, snapshots, feature values, agent predictions, regimes,
master/risk decisions, signals, orders, positions, trades, news, model registry, performance,
health, errors, backtests, and experiments. Foreign keys and uniqueness constraints preserve the
decision chain and signal idempotency. SQLite uses WAL, foreign keys, busy timeout, short
transactions, one writer queue, backups, and integrity checks. PostgreSQL migration will replace
SQLite-specific pragmas/row IDs while repositories retain parameterized queries and transactions.

## Risk architecture

The Python risk gate receives only typed master decisions and fresh broker/account context. It
checks confidence, risk/trade, daily loss, drawdown, exposures, positions, lot cap, spread, stop
distance, loss cooldown, consecutive losses, news windows, freshness, agent health, Python health,
and MT5 health. Volume is derived from equity-at-risk divided by stop loss per lot using live tick
size/value and rounded **down** to broker volume step. Missing specifications mean rejection.

The EA repeats all checks it can observe and calls broker preflight validation. Risk rules only
tighten across boundaries: neither master confidence nor an agent-provided value can bypass a cap.

## Schemas

`AgentPrediction`, `MasterDecision`, `RiskDecision`, and `ExecutionInstruction` live in
`src/axq/schemas.py`. They are strict and versioned. Confidence is `[0,1]`, scores are `[-1,1]`,
signals are enumerated, timestamps are explicit, and `HOLD` cannot become an execution instruction.
Schema evolution uses additive minor versions; breaking changes require a new major version and a
dual-read migration window.

## Model registry

Every immutable model record includes agent/architecture, chronological train/validation/OOS
periods, feature and dataset versions, canonical config hash, metrics, artifact/ONNX/scaler paths,
ordered feature list, creation time, Git commit, and lifecycle state. A deployment configuration
selects an active model ID; engine source is unchanged. Activation requires compatibility checks,
artifact hashes, smoke inference, and explicit promotion. Rollback selects the prior record.

## Dataset and label versioning

A dataset version is a SHA-256-derived identity over source checksums, row counts, time range,
symbol/timeframes, cleaning version, feature version, label version, and config hash. Creation time
is excluded so identical inputs reproduce the identity. Manifests are immutable JSON sidecars.

Labels have independent semantic versions and declare kind, horizon, neutral threshold, and barrier
parameters. Supported designs are N-bar direction (1/3/5/10/20), forward return, ATR-adjusted
return, triple barrier, and TP-before-SL. A feature row at `t` may use only data available at `t`;
labels may look forward solely to create targets. Boundary samples without a complete future window
are dropped.

Phase 3 implements these contracts. Dataset rows carry both UTC candle-open and decision timestamps;
for completed M5 candles the decision timestamp is open plus five minutes. Ordered feature,
target, and label-metadata allowlists prevent target leakage. Content-derived dataset identity binds
source data, configuration, feature/label/split manifests, and Git commit.

Chronological and reusable walk-forward definitions use half-open ranges, label-horizon purging,
and optional embargo. All fitted preprocessing is guarded to training rows. Parquet is the immutable
production storage format; gzip CSV is debug-only. See [datasets](datasets.md) and [labels](labels.md).

## Quant Agent model boundary

Phase 4 adds a frozen Quant inference boundary over Phase 3 artifacts. Dataset loading verifies all
manifest identities, payload hash, schema/order, chronology, split row count, and feature/target
separation. TRAIN alone fits feature selection, imputation, scaling, and the estimator. VALIDATION
alone fits optional calibration. OOS labels are unavailable to fitting and are read only by the
final frozen evaluator.

Artifacts and their SHA-256 hashes are bound by a content-addressed model manifest. Inference checks
feature and optional dataset identity, exact required columns, NaN/inf policy, UTC-aware timestamp,
and freshness before producing the shared `AgentPrediction`. Lifecycle changes are explicit registry
transitions; no model can promote or update itself. See [Quant Agent](quant_agent.md),
[training](model_training.md), and [registry](model_registry.md).

## Failure states

- `HEALTHY`: all mandatory components fresh; trading may still be vetoed.
- `DEGRADED`: optional evidence unavailable; master normally holds or uses configured exclusions.
- `PAUSED`: intentional no-new-trade state; position protection remains active.
- `ERROR`: critical component unsafe; no new trade.

The watchdog will monitor Python, MT5 connectivity, agents, database, models, data age, execution,
disk capacity, and provider status. A news-provider failure is noncritical when news is optional;
unknown high-impact-event coverage can still be configured to block trading.
