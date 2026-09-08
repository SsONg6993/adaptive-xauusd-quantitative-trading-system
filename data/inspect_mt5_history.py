"""Inspect bounded MT5 history without downloading a production dataset."""

from __future__ import annotations

import argparse
import json

import pandas as pd

from axq.quant.development.history import TIMEFRAME_MINUTES, inspect_history_frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--bars", type=int, default=5000)
    parser.add_argument("--abnormal-spread", type=float)
    args = parser.parse_args()
    if args.bars <= 0:
        parser.error("--bars must be positive")
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise SystemExit("Install the Windows-only MetaTrader5 optional dependency") from exc
    if not mt5.initialize():
        raise SystemExit(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        symbols = [item.name for item in (mt5.symbols_get() or ())]
        matches = [name for name in symbols if args.symbol.upper() in name.upper()]
        selected = args.symbol if args.symbol in symbols else (matches[0] if matches else None)
        if selected is None or not mt5.symbol_select(selected, True):
            raise SystemExit(f"No broker symbol matching {args.symbol!r}")
        mapping = {
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
        }
        frames: dict[str, pd.DataFrame] = {}
        for name, code in mapping.items():
            rates = mt5.copy_rates_from_pos(selected, code, 1, args.bars)
            frame = pd.DataFrame(rates if rates is not None else [])
            if not frame.empty:
                frame = frame.rename(columns={"time": "timestamp"})
                frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="s", utc=True)
            frames[name] = frame
        info = mt5.symbol_info(selected)
        report = inspect_history_frames(
            frames, abnormal_spread=args.abnormal_spread
        ) | {
            "requested_symbol": args.symbol,
            "broker_symbol": selected,
            "bounded_rows_requested_per_timeframe": args.bars,
            "timeframe_minutes": TIMEFRAME_MINUTES,
            "symbol_metadata": info._asdict() if info is not None else None,
            "note": "Earliest/latest and row counts describe the bounded terminal sample.",
        }
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
