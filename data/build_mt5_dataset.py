"""Explicit user-run MT5 multi-timeframe download and immutable dataset build."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pandas as pd
import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field

from axq.config import load_config
from axq.datasets import DatasetBuildConfig, assemble_dataset, write_dataset
from axq.quant.trainer import _git_identity


class HistoryBuildConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str = "XAUUSD"
    lookback_days: int = Field(gt=0)
    timeframes: list[str] = Field(min_length=1)
    raw_output_root: Path


def _mapping(mt5: Any) -> dict[str, int]:
    return {
        "M5": int(mt5.TIMEFRAME_M5),
        "M15": int(mt5.TIMEFRAME_M15),
        "H1": int(mt5.TIMEFRAME_H1),
        "H4": int(mt5.TIMEFRAME_H4),
    }


def _load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Configuration must be a YAML mapping: {path}")
    return cast(dict[str, Any], payload)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build real M5+M15+H1+H4 data only when --execute is supplied"
    )
    parser.add_argument("--history-config", required=True, type=Path)
    parser.add_argument("--dataset-config", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    history = HistoryBuildConfig.model_validate(_load(args.history_config))
    dataset = DatasetBuildConfig.model_validate(_load(args.dataset_config))
    unsupported = sorted(set(history.timeframes) - {"M5", "M15", "H1", "H4"})
    if unsupported:
        raise ValueError(f"Unsupported timeframes: {unsupported}")
    end = datetime.now(UTC)
    start = end - timedelta(days=history.lookback_days)
    plan = {
        "status": "EXECUTE_REQUIRED" if not args.execute else "RUNNING",
        "symbol": history.symbol,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "timeframes": history.timeframes,
        "raw_output_root": str(history.raw_output_root),
        "dataset_output_root": str(dataset.output_root),
        "trades_enabled": False,
    }
    if not args.execute:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise SystemExit("Install the Windows-only MetaTrader5 optional dependency") from exc
    if not mt5.initialize():
        raise SystemExit(f"MT5 initialize failed: {mt5.last_error()}")
    frames: dict[str, pd.DataFrame] = {}
    source_files: dict[str, Path] = {}
    try:
        symbols = [item.name for item in (mt5.symbols_get() or ())]
        matches = [name for name in symbols if history.symbol.upper() in name.upper()]
        symbol = history.symbol if history.symbol in symbols else (matches[0] if matches else None)
        if symbol is None or not mt5.symbol_select(symbol, True):
            raise SystemExit(f"No broker symbol matching {history.symbol!r}")
        codes = _mapping(mt5)
        for timeframe in history.timeframes:
            rates = mt5.copy_rates_range(symbol, codes[timeframe], start, end)
            if rates is None:
                raise RuntimeError(f"MT5 history failed for {timeframe}: {mt5.last_error()}")
            frame = pd.DataFrame(rates).rename(columns={"time": "timestamp"})
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
            minutes = {"M5": 5, "M15": 15, "H1": 60, "H4": 240}[timeframe]
            frame = frame[
                frame["timestamp"] + pd.Timedelta(minutes=minutes) <= pd.Timestamp(end)
            ].copy()
            output = history.raw_output_root / f"{symbol.lower()}_{timeframe.lower()}.csv"
            output.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(output, index=False)
            frames[timeframe] = frame
            source_files[timeframe] = output
    finally:
        mt5.shutdown()
    feature_config = load_config(dataset.feature_config)
    result = assemble_dataset(
        frames,
        dataset_name=dataset.dataset_name,
        symbol=history.symbol,
        base_timeframe=dataset.base_timeframe,
        feature_set_version=feature_config.features.version,
        feature_groups=feature_config.features.groups,
        feature_parameters=feature_config.features.parameters,
        label_definition=dataset.label,
        row_policy=dataset.row_policy,
        split_policy=dataset.split,
        storage_format=dataset.storage_format,
        git_commit=_git_identity(),
    )
    output_path = write_dataset(result, dataset.output_root)
    print(
        json.dumps(
            plan
            | {
                "status": "COMPLETE",
                "dataset_id": result.manifest.dataset_id,
                "dataset_path": str(output_path),
                "rows": result.manifest.row_count,
                "source_files": {key: str(value) for key, value in source_files.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
