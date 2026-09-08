# Adaptive XAUUSD Multi-Agent Trading System

Production-oriented, local-first foundation for a measurable multi-agent MT5 trading system. The
current repository intentionally stops after the Phase 4 Quant Agent framework. There is no
production-trained model, autonomous strategy, live execution EA, or claim of trading
profitability.

## Current capabilities

- Strict agent, master, risk, and execution contracts with `BUY`/`SELL`/`HOLD` semantics.
- Bounded MT5 historical downloader for XAUUSD M5/M15/H1/H4 using UTC.
- Cleaning and validation for duplicates, chronology, OHLC integrity, missing intervals, spread,
  and volume.
- Leakage-safe completed-bar M5/M15/H1/H4 synchronization with auditable availability timestamps.
- Versioned feature library covering trend, momentum, volatility, channels, volume, rolling
  statistics, DST-aware sessions, and causally delayed market structure.
- Canonical per-output feature manifests, formal warm-up/missing policies, leakage tests, and
  lightweight correlation/stability/quality diagnostics.
- Versioned direction, return, triple-barrier, and TP-before-SL labels with explicit same-bar
  ambiguity and MFE/MAE metadata.
- Immutable Parquet-oriented dataset contracts with UTC decision timestamps, feature/target
  allowlists, deterministic manifests, chronological purging/embargo, and walk-forward definitions.
- Manifest-bound Quant Agent training/evaluation/inference with majority/prior and logistic
  baselines, Random Forest plus optional XGBoost/LightGBM adapters, train-only preprocessing,
  validation-only calibration, explicit HOLD policy, metrics, explanations, and artifact hashes.
- Candidate/Challenger/Champion/Retired local registry with evidence-required manual promotion and
  a lightweight SQLite experiment audit trail.
- SQLite WAL schema and transactional migrations, with PostgreSQL migration boundaries documented.
- Dataset manifests, label definitions, immutable model metadata, JSON logging, YAML configuration,
  and deterministic risk-veto foundation.
- Local-first defaults: LLM and external-news integrations are off.

Read [the architecture](docs/architecture.md), [indicator research](docs/indicator_research.md),
[feature contract](docs/features.md), [dataset contract](docs/datasets.md),
[label contract](docs/labels.md), [Quant Agent](docs/quant_agent.md),
[model training](docs/model_training.md), [model registry](docs/model_registry.md), and
[runbook](docs/runbook.md) before running models.

## Setup (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,mt5]"
python -m pip install -e ".[dataset]"
python -m pip install -e ".[ml]"
Copy-Item .env.example .env
```

Do not put broker credentials or API keys in tracked files.

## Lightweight verification

```powershell
python -m pytest
python -m ruff check .
python -m mypy src/axq
python scripts/init_db.py --path runtime/smoke.sqlite3
```

These checks do not connect to a broker or train a model. Phase 4 tests use only tiny deterministic
fits.

## Download and validate a small sample

Start and log in to a local MT5 terminal, ensure XAUUSD history is available, then use a short UTC
interval first:

```powershell
python data/download_mt5.py --symbol XAUUSD --timeframe M5 --start 2026-08-03T00:00:00Z --end 2026-08-03T06:00:00Z --output data/raw/xauusd_m5_sample.csv
python data/clean.py --input data/raw/xauusd_m5_sample.csv --output data/processed/xauusd_m5_sample.csv
python data/validate.py --input data/processed/xauusd_m5_sample.csv --timeframe M5
python data/build_features.py --input data/processed/xauusd_m5_sample.csv --output data/processed/xauusd_m5_features.csv --config configs/base.yaml --quality-report runtime/feature-quality-smoke.json
```

Download M15/H1/H4 separately and synchronize only completed higher-timeframe bars:

```powershell
python data/synchronization.py --m5 data/processed/xauusd_m5.csv --m15 data/processed/xauusd_m15.csv --h1 data/processed/xauusd_h1.csv --h4 data/processed/xauusd_h4.csv --output data/processed/xauusd_multitimeframe.csv
```

The broker may use `XAUUSDm`, `GOLD`, or another alias. Pass the actual Market Watch symbol; store it
with the canonical XAUUSD mapping in the dataset manifest. MT5 returns only history currently
available in the terminal, so validate the requested coverage.

## Repository map

```text
configs/                 reviewable runtime, feature, label, risk, regime, master defaults
data/                    downloader and pipeline command-line entry points
database/migrations/     versioned SQLite schema
docs/                    architecture, research, runbook
src/axq/data/            reusable cleaning, validation, synchronization
src/axq/features/        versioned feature definitions and registry
src/axq/                 contracts, config, logs, database, risk, versioning, model metadata
tests/                   deterministic tiny-data tests
agents/ master/ risk/    reserved boundaries for later phased implementations
execution/ mt5/          reserved for Phase 11 execution protocol and EA
datasets/                immutable Phase 3 dataset build/inspection commands
training/quant/          Phase 4 config-driven training and frozen evaluation CLIs
tuning/ evaluation/      reserved for local experiments; never run automatically
backtest/ models/        reserved for Phase 12 and registered artifacts
monitoring/              reserved for health/watchdog services
```

## Non-negotiable development rules

Use chronological splits, fit preprocessing on training data only, and account for overlapping label
horizons with gaps/purging. Every feature must be available at prediction time. All model output is
advisory; deterministic risk controls and the EA retain veto power. Failures block new positions.
Serious training, large tuning, DTW indexing, image generation, and multi-year backtests are
user-run local jobs in later reviewed phases.
