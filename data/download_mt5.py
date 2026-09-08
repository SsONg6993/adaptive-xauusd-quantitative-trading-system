"""Download bounded historical bars from a locally running MetaTrader 5 terminal."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd


def _utc(value: str) -> datetime:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamps must include a timezone, preferably Z/UTC")
    return timestamp.tz_convert("UTC").to_pydatetime()


def download(symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError("Install the Windows-only MetaTrader5 package") from exc
    mapping = {
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
    }
    if timeframe not in mapping:
        raise ValueError(f"Unsupported timeframe {timeframe}")
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"Symbol unavailable: {symbol}; error={mt5.last_error()}")
        rates = mt5.copy_rates_range(symbol, mapping[timeframe], start, end)
        if rates is None:
            raise RuntimeError(f"MT5 download failed: {mt5.last_error()}")
        frame = pd.DataFrame(rates).rename(columns={"time": "timestamp"})
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
        return frame
    finally:
        mt5.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--timeframe", choices=("M5", "M15", "H1", "H4"), required=True)
    parser.add_argument("--start", type=_utc, required=True)
    parser.add_argument("--end", type=_utc, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.start >= args.end:
        parser.error("--start must precede --end")
    frame = download(args.symbol, args.timeframe, args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    print(f"wrote {len(frame)} rows to {args.output}")


if __name__ == "__main__":
    main()
