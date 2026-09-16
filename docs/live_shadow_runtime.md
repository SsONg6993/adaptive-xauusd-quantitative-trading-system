# Live Shadow Runtime MVP

The Live Shadow Runtime observes one explicitly configured MT5 symbol and never submits,
modifies, or closes broker orders. It uses completed M5 bars, causally closed M15 context,
the Phase 2 feature registry, and the existing Phase 6/7 specialist, Master, Discipline, and
Risk contracts.

The runtime enforces one process per resolved output directory using an OS-held lock. Managed runs
also publish operational lifecycle events to an append-only controller database. These heartbeat,
start, stop, and error timestamps never participate in trading semantic identities. Stop requests
are addressed to an exact runtime instance ID, so a stale request cannot stop a later replacement
instance.

The active scan window is `[20:00, 23:00)` in `Asia/Kuala_Lumpur`. Each completed M5 bar is observed
by the deterministic candidate scanner and then enters the same evidence kernel used by replay.
`OUTSIDE_WINDOW`, `UNAVAILABLE`, and `NO_SETUP` produce descriptive quiet Shadow cycles but do not
bypass tools, specialists, or scenario lifecycle. `CANDIDATE` and `CANDIDATE_CONFLICTED` retain the
same scanner meaning. M15 `SUPPORTS`, `OPPOSES`, and `NEUTRAL` classifications are descriptive and
never change kernel eligibility.

The canonical instrument is `XAUUSD`. A single configured broker symbol remains strict, while the
optional ordered allowlist checks only those exact names with `symbol_info` and resolves once at
startup. There is no broad discovery, fuzzy/suffix matching, `symbol_select`, or quote-driven
fallback. Both identities are recorded in the runtime journal. MT5 Gold feeds that report a valid
bid/ask with `last <= 0` retain the literal broker fact as `last=None`; AXQ does not relabel the
midpoint as a broker last-trade price.

Vantage and some other MT5 environments encode market-data epochs in broker server time rather
than canonical UTC. Live Shadow resolves `MT5_BROKER_TIME_TO_UTC_V1` once per MT5 session from a
fresh tick and the local UTC arrival time. The resolver explicitly selects the nearest plausible
whole-hour offset and rejects ambiguous, fractional, or excessive-residual values. The frozen
offset is then applied consistently to tick, M5, and M15 market-data timestamps before freshness,
completed-bar, feature, or scanner logic. The journal retains the raw timestamp, normalized UTC
timestamp, offset, exact instrument/server/account/terminal environment identity, and normalization
version. A stale startup may reuse only an exactly compatible persisted resolution; a detected
mid-session offset change fails closed until restart. Position and order timestamps are not
normalized in V1 because their broker-clock encoding has not yet been proven equivalent.

Runtime and replay contracts remain UTC-only. Replay inputs are never transformed. Forming bars are
excluded after normalization, M5 decisions use the normalized completed-bar close, and the selected
M15 close must be no later than that M5 decision time.

Stale quotes keep SHADOW operational but waiting. Their exact broker tick time is recorded, while no
completed-M5 event, scan, specialist evaluation, decision, or hypothetical execution is performed.
Fresh tick data plus a newly completed M5 bar resumes processing without a process restart. DEMO
readiness remains fail-closed and unchanged.

After a stopped runtime has processed the latest completed M5, restarting before the next completed
M5 may fail closed with `stale source sequence` because the source cursor already contains that bar.
For operator-managed restarts, wait for the next genuinely completed M5. A newer-bar restart has
been verified to process naturally; no runtime, journal, replay, ordering, or decision semantic is
relaxed for same-bar reuse.

The runtime journal writes `ShadowRuntimeCycle` V2. Its reader also supports immutable legacy V1
cycles without rewriting their payloads or IDs; unknown versions and corrupt records fail closed.
See `docs/journal_compatibility.md`.

Run continuously from the Phase 9 worktree:

```powershell
& '..\..\.venv\Scripts\python.exe' -m axq.orchestration.shadow_runtime --broker-symbol XAUUSD.sc --output-dir .\runtime\live-shadow
```

For normal operator use, double-click `Start AXQ Dashboard.cmd`, then use the Overview START/STOP
controls. The managed default uses the exact configured allowlist `XAUUSD,XAUUSD.sc,GOLD`, terminal
`C:\Program Files\MetaTrader\terminal64.exe`, output `runtime/live-shadow`, and a two-second poll.
There are no DEMO or live-money execution controls.

Run once using the ordered explicit alias list:

```powershell
$env:PYTHONPATH=(Resolve-Path '.\src').Path
& '..\..\.venv\Scripts\python.exe' -m axq.orchestration.shadow_runtime --gold-symbols "XAUUSD,XAUUSD.sc,GOLD" --output-dir .\runtime\live-shadow --once
```

Use `--once` for a single read-only poll. The MT5 terminal must already be running, connected, and
logged in; AXQ does not supply credentials or perform account login.

Inspect the latest persisted shadow facts:

```powershell
& '..\..\.venv\Scripts\python.exe' -m axq.orchestration.shadow_report --journal .\runtime\live-shadow\shadow-runtime.sqlite3
```

Launch the read-only dashboard against the same journal:

```powershell
& '..\..\.venv\Scripts\python.exe' -m streamlit run src\axq\dashboard\app.py -- --runtime-db .\runtime\live-shadow\shadow-runtime.sqlite3 --mt5-symbol XAUUSD.sc
```

If broker daily/total drawdown facts required by the deterministic Risk contract are unavailable,
the runtime preserves specialist/Master evidence but does not invent those values or create a
trade plan. The dashboard reports downstream gates as waiting for live runtime facts.

## Evidence-bound interaction

Candidate cycles persist a Master conflict assessment before the final decision. Interaction is
created only when the unchanged fusion result contains `HIGH_DISAGREEMENT`, using the existing
`FusionPolicy.maximum_actionable_disagreement` threshold. Aligned evidence creates no round.

For material directional disagreement, V1 selects at most three directional contributors in
canonical specialist order and records exactly one Master challenge plus one deterministic rebuttal
per participant. A rebuttal can only restate its original `AgentEvidence`: stance and confidence are
unchanged, the only allowed citation is the original evidence ID, and no new fact or memory update is
permitted. The final Master, Discipline, and Risk evaluation still consumes the original immutable
bundle. Consequently, `HIGH_DISAGREEMENT` remains `HOLD`.

The journal stores the conflict assessment, round, chronological turns, and terminal resolution as
append-only semantic records. Malformed or timed-out responses end the interaction fail-closed and
leave Master to use the original evidence. No runtime Ollama call is part of V1. The dashboard labels
the exchange as evidence-bound, renders only persisted turns, and explicitly reports skipped,
unavailable, or incomplete interaction rather than inventing dialogue.
