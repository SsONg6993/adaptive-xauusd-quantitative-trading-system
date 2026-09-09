# Adaptive XAUUSD Quantitative Trading System

Local-first Python framework for developing and evaluating quantitative machine-learning workflows for XAUUSD.

## About

This is a quantitative engineering research project that connects market-data pipelines, feature and label generation, machine-learning experiments, model evaluation, risk controls, and clearly separated system components. It is designed for local experimentation with auditable configurations and leakage-aware time-series workflows.

## Key Features

- Downloads and validates historical MT5 market data.
- Synchronizes completed M5, M15, H1, and H4 bars.
- Builds versioned technical, statistical, session, and market-structure features.
- Creates direction, return, triple-barrier, and TP-before-SL labels.
- Supports chronological splits, walk-forward evaluation, feature ablation, and model comparison.
- Provides baseline, logistic regression, random forest, and optional XGBoost and LightGBM experiment configurations.
- Tracks model artifacts and experiment metadata locally.
- Separates data, feature, dataset, training, risk, and execution responsibilities through documented architecture boundaries.

## Tech Stack

- Python 3.12
- Pandas and NumPy
- scikit-learn
- Pydantic and PyYAML
- SQLite
- MetaTrader 5 (optional, Windows)
- Pytest, Ruff, and mypy

## Getting Started

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,dataset,ml,mt5]"
Copy-Item .env.example .env
python -m pytest
```

MetaTrader 5 is optional and is only required for downloading broker history on Windows.

## Status

Framework Prototype — the local data, feature, dataset, and quantitative experiment components are implemented. Live-production operation and profitability have not been validated.
