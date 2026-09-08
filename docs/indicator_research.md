# Indicator and quantitative-feature candidate research

## Phase 2 implementation and formula verification

The Phase 2 implementation uses explicit causal primitives rather than pandas EWM defaults.
EMA, Wilder RSI, ATR, and DMI/ADX are SMA-seeded; Bollinger dispersion uses population standard
deviation; ROC is a fractional return; CCI uses mean absolute deviation; stochastic and Williams
%R share the same right-aligned high/low range. Reference behavior was checked against the official
TA-Lib function catalogue and C sources, including its RSI recursive update and documented ROC
scales:

- [Official TA-Lib core repository](https://github.com/TA-Lib/ta-lib)
- [TA-Lib Python function catalogue](https://ta-lib.github.io/ta-lib-python/funcs.html)
- [TA-Lib RSI implementation](https://github.com/TA-Lib/ta-lib/blob/main/src/ta_func/ta_RSI.c)
- [pandas EWM semantics](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html)

Mandatory hand-calculated fixtures cover SMA/WMA/EMA, Wilder RSI/ATR, Bollinger bands, realized
volatility, stochastic, Williams %R, ROC, CCI, OBV, and MFI. An optional test compares EMA, RSI,
and ATR directly with TA-Lib when the Python wrapper is installed. It is intentionally not a core
dependency.

## Research stance

This is a candidate pool, not a claim of profitability. Classical indicator families are often
different filters of the same OHLC series and can be highly redundant. Retention requires
chronological out-of-sample and walk-forward results, feature stability, correlation/redundancy and
ablation analysis, calibration, and simulated expectancy after spread, slippage, and commission.

TA-Lib's maintained reference groups more than 150 functions into overlap, momentum, volume,
volatility, price, cycle, pattern, and statistical families and documents their warm-up/unstable
period behavior ([TA-Lib function groups](https://ta-lib.github.io/ta-lib-python/)). MetaTrader also
describes ADX as trend strength rather than direction and cautions against treating a Bollinger Band
touch as a reversal by itself ([MetaTrader indicator guide](https://www.metatrader.com/en/help/indicators)).
Those caveats shape this registry: raw components and distances are preferred over opaque trade rules.

Legend: cost `L/M/H`; leakage risk `R` means rolling-right/current-only is safe, while centered
windows, future pivots, session-final values, or full-sample normalization are unsafe. Suitability is
`M5/M15/H1/H4` unless narrowed. Tick volume is broker activity, not centralized gold volume.

## Candidate matrix

| Candidate | Category | Formula / source | Data | Purpose | Redundancy | Cost | Leakage risk | XAUUSD/timeframe suitability |
|---|---|---|---|---|---|---|---|---|
| SMA(n) | trend | mean(C,t-n+1:t) / TA-Lib | C | smooth level/slope | EMA/WMA/HMA | L | R | all; longer n on H1/H4 |
| EMA(n) | trend | recursive alpha=2/(n+1) / TA-Lib | C | responsive trend/distance | other MAs | L | warm-up state | all |
| WMA(n) | trend | weighted recent closes / TA-Lib | C | linear recency weighting | EMA/HMA | L | R | all, candidate |
| Hull MA | trend | WMA(2WMA(C,n/2)-WMA(C,n),sqrt(n)) | C | low-lag smoother | WMA/EMA | L | R | M15-H4 candidate; noise on M5 |
| Supertrend | trend/vol | ATR bands with stateful flips | HLC | trend state/trailing distance | ATR, channel breakout | L | final-bar state only | all candidate, whipsaw risk |
| Ichimoku components | trend/location | rolling 9/26 midranges, 52 span | HLC | multi-horizon location | Donchian/MAs | L | plotted forward span must **not** be shifted into features | H1/H4 strongest candidate |
| ADX | trend strength | Wilder-smoothed DX from +DI/-DI / TA-Lib | HLC | strength/regime, not direction | DMI, efficiency ratio | L | warm-up | all; useful regime input |
| +DI / -DI | trend direction | directional movement / ATR / TA-Lib | HLC | directional pressure | ADX, ROC | L | warm-up | all |
| Aroon | trend | time since rolling high/low | HL | trend emergence | Donchian | L | current/past window only | M15-H4 candidate |
| RSI | momentum | 100-100/(1+smoothed gains/losses) | C | bounded momentum/state | stochastic, Williams %R | L | warm-up | all; thresholds not assumed universal |
| MACD + signal | momentum/trend | EMA12-EMA26; EMA9(MACD) | C | band-pass-like trend momentum | EMA slopes, PPO | L | warm-up | M15-H4; normalized form for cross-regime use |
| ROC | momentum | C/C[n]-1 / TA-Lib | C | scale-free momentum | return, momentum | L | R | all |
| Momentum | momentum | C-C[n] | C | absolute impulse | ROC | L | R | normalize by ATR for XAUUSD |
| Stochastic | momentum/location | (C-LLn)/(HHn-LLn) | HLC | range location | Williams %R, Donchian position | L | R | ranging regimes, all |
| CCI | momentum | (typical-SMA)/(0.015 mean deviation) | HLC | normalized deviation | z-score | L | R | all candidate |
| Williams %R | momentum/location | -100(HHn-C)/(HHn-LLn) | HLC | range location | stochastic | L | R | redundant candidate |
| ATR / NATR | volatility | Wilder mean true range; ATR/C | HLC | stops, sizing, regime | range std | L | warm-up | essential all; price-normalize comparisons |
| Bollinger width/%B | volatility/location | SMA +/- k sigma; width/mean | C | dispersion and price location | z-score, rolling std | L | R | all; touch is not standalone reversal |
| Keltner channels | volatility/trend | EMA +/- k ATR | HLC | ATR envelope | Bollinger, Supertrend | L | warm-up | all candidate |
| Rolling std | volatility | std(return,n) | C | close-to-close volatility | realized vol | L | R | all |
| Historical volatility | volatility | annualized std(log returns) | C | comparable volatility | rolling std | L | annualization depends on timeframe | all |
| Realized volatility | volatility | sqrt(sum intraperiod r²)) | intrabar/ticks preferred | observed variation | rolling std | M | aggregation must end by t | best with M5/ticks; useful H1/H4 context |
| Donchian channels | breakout | rolling HH/LL | HL | breakout/range bounds | Aroon, stochastic | L | shift bounds by one bar for breakout tests | all |
| Distance to rolling high/low | breakout/location | (C-HHn)/ATR, (C-LLn)/ATR | HLC | proximity without hard rule | Donchian | L | no future extrema | all |
| Range expansion/compression | breakout/vol | TR / rolling median(TR) | HLC | volatility transition | ATR z-score | L | R | M5-H1 especially |
| Bollinger-Keltner squeeze | breakout/vol, popular candidate | BB inside KC + momentum | HLC | compression candidate | BB/KC/range ratio | L | R | all; label as unproven composite |
| Tick volume | volume | MT5 tick count | tick_volume | activity/liquidity proxy | relative volume | L | broker-dependent | M5/M15 strongest; validate broker stability |
| OBV | volume | cumulative sign(delta C)*volume / TA-Lib | CV | price-volume confirmation | volume ROC | L | seed/window state | candidate; tick-volume caveat |
| MFI | volume/momentum | signed typical-price money flow | HLCV | bounded volume-weighted pressure | RSI/OBV | L | warm-up | candidate, tick-volume caveat |
| Volume ROC | volume | V/V[n]-1 | V | activity change | relative volume | L | zero handling | M5/M15 |
| Relative volume | volume | V/rolling mean(V,n) | V | unusual activity | volume z-score | L | use past/right window; seasonality | M5/M15; condition on session |
| Session VWAP | location/volume | cumulative sum(PV)/sum(V) since session open | HLCV | intraday fair-value distance | moving averages | L | never use final session VWAP early | M5/M15; tick-volume proxy limitation |
| Anchored VWAP | location, popular candidate | cumulative PV/V from predeclared anchor | HLCV | event/level-relative value | session VWAP | L | anchor must be known at t, not hindsight pivot | M5-H1 candidate |
| EMA distances | location | (C-EMA20/50/200)/ATR or percent | C/HLC | scale-normalized trend location | raw EMAs | L | R | all |
| Support/resistance distance | structure | distance to confirmed past-only level / ATR | HLC | context and stop space | rolling extrema | M | pivot confirmation can leak if backdated | all; store confirmation timestamp |
| Simple/log return | statistical | C/C[-1]-1; log(C/C[-1]) | C | stationary price change | ROC(1) | L | R | essential all |
| Rolling mean/variance | statistical | moments over right-aligned returns | C | local drift/dispersion | MA/std | L | no centered window | all |
| Rolling skew/kurtosis | statistical | standardized third/fourth moments | C | tail/asymmetry regime | jump metrics | L | enough samples required | M15-H4; noisy on short M5 windows |
| Return z-score | statistical | (r-rolling mean)/rolling std | C | standardized shock | Bollinger %B | L | train-only clipping/scaling | all |
| Autocorrelation | statistical | corr(r_t,r_t-k) in rolling window | C | persistence/mean reversion | trend metrics | M | right-aligned window | H1/H4 more stable; candidate |
| Rolling cross-asset correlation | statistical/macro | corr(XAU returns, DXY/yield returns) | aligned external data | macro co-movement | beta | M | release/alignment and missing-data risk | H1/H4; optional data source |
| Price velocity/acceleration | statistical | r(n); delta r(n) | C | first/second change | ROC/MACD | L | R | all after volatility normalization |
| Parkinson range volatility | statistical/vol | mean(log(H/L)^2)/(4log2) | HL | range-efficient volatility | ATR/RV | L | R | all candidate; gap limitation |
| Garman-Klass volatility | statistical/vol | OHLC range/open-close estimator | OHLC | efficient bar volatility | Parkinson/RV | L | R | all candidate; assumptions need validation |
| Efficiency ratio | regime, modern candidate | abs(C-C[n])/sum(abs(delta C)) | C | trend vs noise | ADX/Hurst | L | R | all, interpretable regime input |
| Hurst exponent | regime, modern candidate | scaling estimate of increments | C | persistence diagnostic | autocorrelation/efficiency | M/H | short-window estimator bias; no global fit | H1/H4 research candidate |
| Permutation entropy | regime, modern candidate | entropy of ordinal return patterns | C | complexity/abnormality | Hurst/volatility | M | right-aligned window only | M15-H4 candidate, tune cautiously |
| Bipower/jump variation | regime/vol, modern quant candidate | realized variance vs adjacent absolute-return product | intrabar returns | separate jumps from continuous variation | RV/range expansion | M | completed aggregation only | H1/H4 from M5/ticks |
| Spread / percentile | microstructure | current spread; rolling empirical rank | bid/ask or MT5 spread | cost/liquidity gate | volatility/activity | L/M | percentile fit/rolling past only | M5/M15 essential for risk |
| Tick activity / price velocity | microstructure | ticks per interval; abs move/time | ticks or bars | activity and shock state | tick volume/RV | L | completed interval only | M5 strongest |
| Hour/day/session/overlap | time | UTC calendar flags | timestamp | intraday seasonality | volume/spread profiles | L | DST-aware market definitions | all; session flags most relevant M5/M15 |
| Scheduled-event proximity | news/regime | minutes to/from known release | calendar | news-risk window | session/volatility | L | actual/revised result unavailable before release | all; key for XAUUSD |

## XAUUSD-specific priorities

The first experiments should emphasize ATR/NATR, realized/range volatility, spread, session and
London-New York overlap, scheduled USD event proximity, multi-horizon EMA/ADX or efficiency ratio,
breakout distances, tick activity, and price-action features normalized by ATR. Gold's nominal price
and volatility change over time, so absolute distances should normally be normalized. DXY/yields are
optional external inputs and require point-in-time availability auditing.

## Redundancy and experiment plan

Test `PRICE_ONLY`, `PRICE_ACTION_ONLY`, each price-plus-family group, `MULTI_TIMEFRAME`, and
`ALL_FEATURES`. Within every training fold: remove constants, inspect missingness, Spearman/Pearson
clusters, permutation/SHAP importance where appropriate, and run group/drop-one ablations. Compare
probability calibration and forward returns by score bucket, regime, session, volatility, and news
state. Final selection is based on stable OOS trading expectancy after costs, not in-sample feature
importance.

No implementation may backfill a pivot value to the pivot bar, use a completed H1/H4 value before
its close, compute a session-final VWAP on earlier rows, center a rolling window, globally normalize,
or use revised economic data as if it were the first release.
