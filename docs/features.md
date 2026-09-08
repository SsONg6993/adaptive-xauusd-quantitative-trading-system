# Phase 2 feature contract

## Point-in-time invariant

Every output on row T uses only source values whose availability timestamp is less than or equal to
T. Rolling windows are right aligned. No feature uses a centered window, backward fill, global
normalization, label column, or a higher-timeframe candle before that candle closes.

## Implemented configurable candidate families

- Trend: SMA, TA-Lib-seeded EMA, WMA, +DI, -DI, ADX, Aroon up/down/oscillator,
  Supertrend, average distances, and velocity.
- Momentum: Wilder RSI, MACD/signal/histogram, slow stochastic, CCI, ROC, and Williams %R.
- Volatility/channels: Wilder ATR/NATR, Bollinger bands/width/%B, Keltner channels,
  squeeze state, realized volatility, Parkinson volatility, and range z-score.
- Volume: OBV, relative tick volume, volume ROC, and MFI. MT5 tick volume is broker activity,
  not centralized exchange volume.
- Breakout/structure: prior-bar Donchian bounds, breakout, failed breakout, retest,
  confirmed swing high/low, HH/HL/LH/LL, BOS, CHoCH, expansion/compression, recent-extreme
  distance, and confirmed support/resistance distance.
- Statistical/time: rolling return moments, skew, kurtosis, z-score, lag-one autocorrelation,
  efficiency ratio, rolling extrema/median/quantiles, and DST-aware sessions.

These are candidates, not a recommendation to use every column. The manifest records enabled
families; Phase 3 selection must use training-fold-only correlation, stability, and ablation tools.
Stochastic and Williams %R, channel-location features, moving-average variants, and volatility
estimators are intentionally retained as configurable redundant candidates.

## Swing and structure timing

For left-bars L and right-bars R, the pivot candidate at row P is inspected over
[P-L, P+R] and is first emitted at row P+R. The default R=2 therefore has a two-candle
confirmation delay. The pivot is never written back to row P. HH/LH and HL/LL compare newly
confirmed pivots with the preceding confirmed pivot of the same type. BOS compares the current
close with the prior row's last confirmed level. CHoCH is a BOS against the current structure bias.

## Warm-up policy

The feature manifest declares minimum lookback, warm-up rows, and zero-based valid-from row for
every output. Insufficient history remains NaN; event flags do not become false until their
inputs are available. Recursive indicators use an SMA seed:

| Family | Default conservative valid-from rule |
|---|---|
| Price action | row 1 |
| SMA/EMA/WMA | period - 1 |
| RSI/ATR/MFI | period (a prior close/direction is required) |
| ADX | 2 * period - 1 |
| MACD signal | slow + signal - 2 |
| Stochastic D | period + smooth-K + smooth-D - 3 |
| Bollinger/rolling statistics | period - 1, or period where returns need a prior close |
| Prior Donchian breakout | period |
| Confirmed swing | left + right; level distances may remain NaN until a level exists |
| Sessions/MTF ratios | row 0 if their required synchronized inputs are present |

The manifest records an output-specific formula lookback. Data-dependent mathematical
unavailability (zero channel width, no confirmed level, zero variance) can continue after warm-up
and remains NaN.

## Missing-value policy

| Reason | Handling |
|---|---|
| Mathematically unavailable | retain NaN; never turn zero denominators into invented values |
| Insufficient history | retain NaN until declared valid-from point |
| Missing market data | retain NaN, report gaps, never impute OHLC |
| Missing broker data | retain NaN and report the missing source/provider |
| Optional unavailable feature | disable explicitly in the manifest or retain NaN |

Any imputer used later is a fitted preprocessing object and must fit only on a training prefix.
The Phase 2 standardizer scaffold stores its exclusive training boundary.

## Multi-timeframe and UTC rules

All timestamps are stored internally in UTC. MT5 timestamps are candle-open times. A candle opened
at H for duration D becomes available at H+D. Synchronization uses a backward as-of join on that
availability time and permits equality, so an H1 candle opened at 00:00 first appears on the 01:00
base row. Auditable source-open and available-at columns are retained for M15/H1/H4.

Sessions use IANA timezone rules: Asia is 09:00-17:00 Asia/Tokyo, London is 08:00-17:00
Europe/London, and New York is 08:00-17:00 America/New_York on weekdays. Overlap is the actual
intersection, including the weeks when U.S. and European DST transition dates differ.

## Manifest and diagnostics

Feature manifests contain output name, group, parameters, implementation version, enabled state,
minimum lookback, warm-up, valid-from row, required source columns, dtype, and causal status. Their
ID is a SHA-256-derived identity over canonical JSON. The build command writes an adjacent
.features.json file by default.

The analysis module provides Pearson/Spearman matrices, high-correlation and exact-duplicate
detection, variance/near-zero-variance checks, missing rates, compatibility checks for permutation
importance and SHAP, group/single-feature ablation column sets, period stability summaries, and a
quality report. Compatibility means shape/type readiness only; model, imputer, permutation
importance, and SHAP fitting remain Phase 3 work and must occur inside training folds.
