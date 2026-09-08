"""Explicit, versioned feature registration and reproducible manifests."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from axq.features.manifest import FeatureManifest, FeatureManifestEntry

FeatureFunction = Callable[[pd.DataFrame, Mapping[str, Any]], pd.DataFrame]
LookbackFunction = Callable[[Mapping[str, Any]], int]


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    group: str
    version: str
    function: FeatureFunction
    required_columns: tuple[str, ...]
    lookback: LookbackFunction
    causal_status: str = "causal"


def _synthetic_frame(rows: int = 512) -> pd.DataFrame:
    x = np.arange(rows, dtype=float)
    close = 2600.0 + 0.03 * x + 2.0 * np.sin(x / 4.0) + 0.5 * np.cos(x / 11.0)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=rows, freq="5min", tz="UTC"),
            "open": close - 0.1 * np.sin(x),
            "high": close + 0.8 + 0.1 * np.cos(x),
            "low": close - 0.8 - 0.1 * np.sin(x),
            "close": close,
            "tick_volume": 100.0 + x % 31,
            "spread": 20.0 + x % 3,
            "close_m15": close - 0.1,
            "close_h1": close - 0.2,
            "close_h4": close - 0.3,
        }
    )


class FeatureRegistry:
    def __init__(self) -> None:
        self._features: dict[str, FeatureDefinition] = {}

    def register(self, definition: FeatureDefinition) -> None:
        if definition.name in self._features:
            raise ValueError(f"Duplicate feature: {definition.name}")
        self._features[definition.name] = definition

    def definitions(self) -> tuple[FeatureDefinition, ...]:
        return tuple(self._features.values())

    def compute(
        self,
        frame: pd.DataFrame,
        *,
        enabled_groups: Iterable[str],
        parameters: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> pd.DataFrame:
        result = frame.copy()
        groups = set(enabled_groups)
        settings = parameters or {}
        for definition in self._features.values():
            if definition.group not in groups:
                continue
            missing = set(definition.required_columns) - set(result.columns)
            if missing:
                raise ValueError(f"{definition.name} missing source columns: {sorted(missing)}")
            additions = definition.function(result, settings.get(definition.name, {}))
            overlap = set(additions.columns) & set(result.columns)
            if overlap:
                raise ValueError(f"Feature overwrites source columns: {sorted(overlap)}")
            result = result.join(additions)
        return result

    def manifest(
        self,
        *,
        feature_set_version: str,
        enabled_groups: Iterable[str],
        parameters: Mapping[str, Mapping[str, Any]] | None = None,
        available_source_columns: Iterable[str] | None = None,
    ) -> FeatureManifest:
        groups = set(enabled_groups)
        settings = parameters or {}
        sample = _synthetic_frame()
        available = (
            set(available_source_columns)
            if available_source_columns is not None
            else set(sample.columns)
        )
        entries: list[FeatureManifestEntry] = []
        for definition in self._features.values():
            params = dict(settings.get(definition.name, {}))
            outputs = definition.function(sample, params)
            for column in outputs.columns:
                lookback = _output_lookback(definition, str(column), params)
                required_columns = list(definition.required_columns)
                if definition.group == "multi_timeframe":
                    timeframe = str(column).rsplit("_", maxsplit=1)[-1]
                    required_columns.append(f"close_{timeframe}")
                entries.append(
                    FeatureManifestEntry(
                        feature_name=str(column),
                        feature_group=definition.group,
                        parameters=params,
                        implementation_version=definition.version,
                        enabled=definition.group in groups
                        and set(required_columns).issubset(available),
                        minimum_lookback=lookback,
                        warmup_rows=max(lookback - 1, 0),
                        valid_from_row=max(lookback - 1, 0),
                        required_source_columns=required_columns,
                        output_dtype=str(outputs[column].dtype),
                        causal_status=definition.causal_status,
                    )
                )
        return FeatureManifest(feature_set_version=feature_set_version, entries=entries)


def _integer(params: Mapping[str, Any], key: str, default: int) -> int:
    return int(params.get(key, default))


def _output_lookback(
    definition: FeatureDefinition, column: str, params: Mapping[str, Any]
) -> int:
    group = definition.group
    if group == "price_action":
        delayed = {
            "pa_gap", "pa_return_1", "pa_log_return_1", "pa_higher_high", "pa_higher_low"
        }
        return 2 if column in delayed else 1
    if group == "trend":
        if "_sma_" in column or "_ema_" in column or "_wma_" in column:
            return int(column.rsplit("_", maxsplit=1)[-1])
        if "_plus_di_" in column or "_minus_di_" in column:
            return _integer(params, "dmi_period", 14) + 1
        if "_adx_" in column:
            return 2 * _integer(params, "dmi_period", 14)
        if "_aroon_" in column:
            return _integer(params, "aroon_period", 14) + 1
        if "supertrend" in column:
            return _integer(params, "supertrend_period", 10) + 1
        return _integer(params, "slope_period", 10) + 1
    if group == "momentum":
        if "_rsi_" in column:
            return _integer(params, "rsi_period", 14) + 1
        if "_macd_signal_" in column or "_macd_hist_" in column:
            return _integer(params, "macd_slow", 26) + _integer(params, "macd_signal", 9) - 1
        if "_macd_" in column:
            return _integer(params, "macd_slow", 26)
        if "_stoch_d_" in column:
            return (
                _integer(params, "stochastic_period", 14)
                + _integer(params, "stochastic_smooth_k", 3)
                + _integer(params, "stochastic_smooth_d", 3)
                - 2
            )
        if "_stoch_k_" in column:
            return (
                _integer(params, "stochastic_period", 14)
                + _integer(params, "stochastic_smooth_k", 3)
                - 1
            )
        if "_cci_" in column:
            return _integer(params, "cci_period", 20)
        if "_roc_" in column:
            return _integer(params, "roc_period", 10) + 1
        return _integer(params, "williams_period", 14)
    if group == "volatility":
        atr_lookback = _integer(params, "atr_period", 14) + 1
        rolling = _integer(params, "rolling_period", 20)
        if "_atr_" in column:
            return atr_lookback
        if "_realized_" in column:
            return rolling + 1
        if "_parkinson_" in column or "_bb_" in column or "_range_zscore_" in column:
            return rolling
        if "_keltner_mid_" in column:
            return rolling
        return max(rolling, atr_lookback)
    if group == "volume":
        if column == "volume_obv":
            return 1
        if "_mfi_" in column:
            return _integer(params, "mfi_period", 14) + 1
        if "_roc_" in column:
            return _integer(params, "period", 20) + 1
        return _integer(params, "period", 20)
    if group == "statistical":
        period = _integer(params, "period", 20)
        if "_autocorr_" in column:
            return period + 2
        if "_return_" in column or "_efficiency_" in column:
            return period + 1
        return period
    if group == "market_structure":
        pivot = _integer(params, "left_bars", 2) + _integer(params, "right_bars", 2) + 1
        if "range_expansion" in column or "compression" in column:
            return _integer(params, "level_lookback", 20)
        if "distance_" in column:
            if "recent_" in column:
                return max(
                    _integer(params, "level_lookback", 20),
                    _integer(params, "atr_period", 14) + 1,
                )
            return max(pivot, _integer(params, "atr_period", 14) + 1)
        if "_bos_" in column or "_choch_" in column:
            return pivot + 1
        return pivot
    return definition.lookback(params)


def default_registry() -> FeatureRegistry:
    from axq.features.breakout import breakout_features
    from axq.features.market_structure import market_structure_features
    from axq.features.momentum import momentum_features
    from axq.features.multi_timeframe import multi_timeframe_features
    from axq.features.price_action import price_action_features
    from axq.features.session import session_features
    from axq.features.statistical import statistical_features
    from axq.features.trend import trend_features
    from axq.features.volatility import volatility_features
    from axq.features.volume import volume_features

    registry = FeatureRegistry()
    definitions = (
        FeatureDefinition("price_action_v2", "price_action", "2.0.0", price_action_features,
                          ("open", "high", "low", "close"), lambda _: 2),
        FeatureDefinition(
            "trend_v2", "trend", "2.0.0", trend_features, ("high", "low", "close"),
            lambda p: max(max([int(v) for v in p.get("ma_periods", [20, 50, 200])]),
                          2 * _integer(p, "dmi_period", 14),
                          _integer(p, "aroon_period", 14) + 1,
                          _integer(p, "supertrend_period", 10) + 1),
        ),
        FeatureDefinition(
            "momentum_v2", "momentum", "2.0.0", momentum_features, ("high", "low", "close"),
            lambda p: max(_integer(p, "rsi_period", 14) + 1,
                          _integer(p, "macd_slow", 26) + _integer(p, "macd_signal", 9) - 1,
                          _integer(p, "stochastic_period", 14)
                          + _integer(p, "stochastic_smooth_k", 3)
                          + _integer(p, "stochastic_smooth_d", 3) - 2,
                          _integer(p, "cci_period", 20), _integer(p, "roc_period", 10) + 1,
                          _integer(p, "williams_period", 14)),
        ),
        FeatureDefinition(
            "volatility_v2", "volatility", "2.0.0", volatility_features,
            ("high", "low", "close"),
            lambda p: max(_integer(p, "atr_period", 14) + 1,
                          _integer(p, "rolling_period", 20) + 1),
        ),
        FeatureDefinition(
            "volume_v2", "volume", "2.0.0", volume_features,
            ("high", "low", "close", "tick_volume"),
            lambda p: max(_integer(p, "period", 20) + 1, _integer(p, "mfi_period", 14) + 1),
        ),
        FeatureDefinition(
            "breakout_v2", "breakout", "2.0.0", breakout_features,
            ("high", "low", "close"), lambda p: _integer(p, "period", 20) + 1,
        ),
        FeatureDefinition(
            "statistical_v2", "statistical", "2.0.0", statistical_features,
            ("high", "low", "close"), lambda p: _integer(p, "period", 20) + 2,
        ),
        FeatureDefinition("session_v2", "session", "2.0.0", session_features,
                          ("timestamp",), lambda _: 1),
        FeatureDefinition(
            "market_structure_v1", "market_structure", "1.0.0", market_structure_features,
            ("high", "low", "close"),
            lambda p: max(_integer(p, "left_bars", 2) + _integer(p, "right_bars", 2) + 1,
                          _integer(p, "level_lookback", 20),
                          _integer(p, "atr_period", 14) + 1),
            causal_status="causal_with_declared_confirmation_delay",
        ),
        FeatureDefinition(
            "multi_timeframe_v2", "multi_timeframe", "2.0.0", multi_timeframe_features,
            ("close",), lambda _: 1,
            causal_status="causal_if_input_is_completed-bar-synchronized",
        ),
    )
    for definition in definitions:
        registry.register(definition)
    return registry
