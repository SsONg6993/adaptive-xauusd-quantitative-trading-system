# Operator dashboard and managed Shadow Runtime

The optional Streamlit dashboard is a local operator view over explicitly selected AXQ artifacts.
Its data projections are read-only. The Overview can start or stop the existing
`axq.orchestration.shadow_runtime` subprocess, but contains no scanner, agent, Master, Discipline,
Risk, execution, or broker-mutation logic. Missing fields are shown as **Not available yet**.

## One-click launch

With the optional dashboard dependency installed, double-click:

```text
Start AXQ Dashboard.cmd
```

The launcher selects the existing project virtual environment, starts Streamlit at
`http://127.0.0.1:8501`, and opens the browser. A durable append-only registry records the exact
Streamlit PID, Windows creation identity, and executable. A repeated launch reuses only that exact
healthy process; an unregistered process occupying the endpoint fails closed. Browser refreshes do
not own, start, or stop either Streamlit or Shadow Runtime.

If a newly spawned Dashboard fails durable registration or readiness, the launcher revalidates its
PID, creation token, and executable and terminates only that exact process. The Shadow controller
applies the same exact-identity cleanup if durable instance registration or initial lifecycle
persistence fails, closing the spawn-before-registration orphan window.

The Overview offers **START** and **STOP**, with **RESTART** under advanced control. The controller
uses `runtime/live-shadow/shadow-control.sqlite3`; it never uses Streamlit session state as process
ownership. Shadow Runtime itself owns an OS lock for its resolved output directory, so a manual
duplicate also fails closed.

The Overview does not open MT5 implicitly while rendering. In a stopped/error state,
**CHECK MT5 CONNECTION** performs an explicit read-only probe; otherwise the UI reports **Not
checked**. While the managed runtime is starting, running, waiting for market, or stopping, the
Dashboard reports **Managed by Shadow** and reads persisted runtime facts instead of competing for
the terminal IPC connection.

STOP appends a request bound to the current runtime instance ID. The runtime observes that exact
request, performs its existing graceful shutdown, and records the lifecycle transition. Forced
termination is attempted only after the controller revalidates PID, Windows creation identity, and
executable. A forced stop records `FORCED_STOP_AFTER_TIMEOUT` and RESTART does not proceed until the
operator issues a later explicit START.

If the stopped instance already processed the latest completed M5, an immediate START before a newer
completed M5 exists may fail closed with `stale source sequence`. Wait for the next genuinely
completed M5 before restarting. This preserves causal duplicate protection; it is a known
operational constraint, not a reason to relax runtime, journal, replay, ordering, or decision
semantics.

## Manual development launch

From the Phase 9 worktree, install the optional dashboard dependency into the existing project
environment:

```powershell
& '..\..\.venv\Scripts\python.exe' -m pip install 'streamlit>=1.40,<2'
```

Launch against the current local AXQ smoke artifacts:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& '..\..\.venv\Scripts\python.exe' -m streamlit run `
  'src\axq\dashboard\app.py' `
  --server.address 127.0.0.1 `
  --server.port 8501 `
  -- `
  --reasoning-db 'runtime\phase9\citation-v2-smoke\reasoning.sqlite3' `
  --runtime-db '..\phase-8-reflection-experience\runtime\phase8-task1\baseline-c\runtime.sqlite3' `
  --metrics-json '..\phase-8-reflection-experience\runtime\phase8-task1\baseline-c\metrics.json' `
  --ollama-endpoint 'http://127.0.0.1:11434' `
  --ollama-model 'llama3.2:latest' `
  --mt5-symbol 'XAUUSD.sc'
```

Open `http://127.0.0.1:8501`. Technical paths and configuration stay under the collapsed
**Advanced / Data Sources** section; no filesystem scanning is performed.

## Read-only smoke check

The companion check command reads the same sources without starting Streamlit and emits canonical
JSON suitable for operator verification:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& '..\..\.venv\Scripts\python.exe' -m axq.dashboard check `
  --reasoning-db 'runtime\phase9\citation-v2-smoke\reasoning.sqlite3' `
  --runtime-db '..\phase-8-reflection-experience\runtime\phase8-task1\baseline-c\runtime.sqlite3' `
  --metrics-json '..\phase-8-reflection-experience\runtime\phase8-task1\baseline-c\metrics.json' `
  --ollama-endpoint 'http://127.0.0.1:11434' `
  --ollama-model 'llama3.2:latest' `
  --attempt-limit 10
```

SQLite inputs are opened with `mode=ro` and `query_only=ON`. Ollama status uses only loopback HTTP
GET requests to `/api/version` and `/api/tags`; it never invokes generation. The optional live MT5
reader initializes the already logged-in local terminal only after **CHECK MT5 CONNECTION**, without
login credentials, and exposes no trading operations. It requests only the explicitly configured
broker symbol, without discovery, selection, or fallback.

## Pages and availability semantics

- **Overview** controls and reports the managed Shadow Runtime as `STOPPED`, `STARTING`, `RUNNING`,
  `WAITING_FOR_MARKET`, `ERROR`, or `STOPPING`, then shows live market/account and persisted
  decision-cycle facts where present.
- **Reasoning** displays the latest N immutable attempts, their bounded evidence/context, structured
  response, citations, provider usage, duration, and audit status.
- **Performance** reports the covered date range whenever known, replay/trade metrics, and an equity
  curve only when that series exists in the supplied artifact.
- **Audit** shows reasoning failures and persisted Discipline/Risk rejection or veto facts where the
  supplied runtime journal exposes them.

`STALE` is an observation about the latest persisted timestamp, not a runtime mutation or health
intervention. `ONLINE` is reserved for a successful live status probe such as loopback Ollama.
