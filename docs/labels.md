# Phase 3 label contract

## Decision and reference prices

MT5 candle timestamps are UTC candle-open times. For a completed-candle M5 dataset, the candle
opened at 10:00 closes at 10:05; its feature row has decision timestamp 10:05 and cannot be used
earlier. Direction and forward-return labels compare that decision candle's close with the close of
candle T+N. Future-path labels begin with candle T+1. Future open and close prices are never mixed
implicitly.

## Label families

Direction labels support horizons 1, 3, 5, 10, 20 or any positive configured horizon. Thresholds
may be absolute price, percentage, or ATR-normalized. Outputs are UP, DOWN, or NEUTRAL; incomplete
horizons remain missing.

Forward returns support simple close-to-close return, log return, and close change divided by ATR
known at decision time. Every definition has a semantic version and content-derived label manifest.

Triple-barrier labels create asymmetric upper/lower barriers from absolute, percentage, or
decision-time ATR distances. Outcomes are UPPER_FIRST, LOWER_FIRST, TIMEOUT, or AMBIGUOUS.
TP-before-SL uses the same path engine with a configured LONG or SHORT side and emits TP_FIRST,
SL_FIRST, TIMEOUT, or AMBIGUOUS.

## Same-bar collision policy

OHLC bars cannot reveal whether the high or low occurred first. The default is AMBIGUOUS, so a
favorable outcome is never silently assumed. PESSIMISTIC chooses the adverse barrier for the
configured side; OPTIMISTIC is supported only for explicit sensitivity analysis; LOWER_TIMEFRAME
scans supplied smaller bars in time order and remains ambiguous if resolution is still impossible.

Barrier metadata records the barrier, hit timestamp, bars to hit, side-normalized realized return,
and excursions up to simulated exit. Direction/return labels record excursions over their horizon.
MFE and MAE are available as raw distance, percentage, ATR units, and R units when a risk distance
exists.

## Sensitivity and balance

The label analysis utilities compare independently versioned definitions and report outcome counts
and rates. They do not optimize thresholds, resample rows, rebalance classes, or infer profitability.
