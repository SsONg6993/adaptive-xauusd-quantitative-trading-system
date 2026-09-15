"""Auditable MT5 broker-clock to canonical-UTC normalization for live market data."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash

NORMALIZATION_VERSION = "MT5_BROKER_TIME_TO_UTC_V1"


class MT5TimeNormalizationError(RuntimeError):
    """Raised when broker time cannot be mapped to canonical UTC safely."""


def _strict_utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise MT5TimeNormalizationError(f"{field} must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise MT5TimeNormalizationError(f"{field} must already be UTC")
    return value


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MT5BrokerTimePolicy(_FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    normalization_version: Literal["MT5_BROKER_TIME_TO_UTC_V1"] = (
        "MT5_BROKER_TIME_TO_UTC_V1"
    )
    minimum_offset_hours: int = -12
    maximum_offset_hours: int = 14
    inference_residual_tolerance_seconds: int = Field(default=15, ge=0, le=120)
    future_tolerance_seconds: int = Field(default=1, ge=0, le=10)

    @model_validator(mode="after")
    def validate_range(self) -> MT5BrokerTimePolicy:
        if self.minimum_offset_hours >= self.maximum_offset_hours:
            raise ValueError("minimum offset must be below maximum offset")
        return self


class MT5BrokerEnvironmentIdentity(_FrozenModel):
    """Safe identity fields that prevent clock reuse across broker environments."""

    schema_version: Literal["1.0"] = "1.0"
    environment_id: str = ""
    broker_server: str | None = None
    account_login_digest: str | None = None
    account_trade_mode: int | None = None
    terminal_company: str | None = None
    terminal_build: int | None = None

    @model_validator(mode="after")
    def bind_identity(self) -> MT5BrokerEnvironmentIdentity:
        identity = self.model_dump(mode="json", exclude={"environment_id"})
        expected = f"mt5env-{canonical_hash(identity)[:20]}"
        if self.environment_id and self.environment_id != expected:
            raise ValueError("environment_id does not match MT5 environment content")
        object.__setattr__(self, "environment_id", expected)
        return self


class MT5BrokerTimeOffsetResolution(_FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    resolution_id: str = ""
    normalization_version: Literal["MT5_BROKER_TIME_TO_UTC_V1"] = (
        "MT5_BROKER_TIME_TO_UTC_V1"
    )
    canonical_instrument: Literal["XAUUSD"]
    resolved_broker_symbol: str = Field(min_length=1)
    instrument_resolution_id: str = Field(min_length=1)
    environment: MT5BrokerEnvironmentIdentity
    offset_seconds: int
    raw_tick_time: int
    raw_tick_time_msc: int | None = None
    raw_tick_at: UTCDateTime
    normalized_tick_at: UTCDateTime
    observed_at: UTCDateTime
    resolved_at: UTCDateTime
    resolution_source: Literal["FRESH_BROKER_TICK"] = "FRESH_BROKER_TICK"

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> MT5BrokerTimeOffsetResolution:
        if self.offset_seconds % 3_600:
            raise ValueError("broker time offset must be a whole number of hours")
        if self.normalized_tick_at > self.observed_at + timedelta(seconds=1):
            raise ValueError("normalized broker tick cannot be in the future")
        identity = self.model_dump(mode="json", exclude={"resolution_id"})
        expected = f"mt5time-{canonical_hash(identity)[:20]}"
        if self.resolution_id and self.resolution_id != expected:
            raise ValueError("resolution_id does not match broker time resolution content")
        object.__setattr__(self, "resolution_id", expected)
        return self


class MT5TimestampNormalizationTrace(_FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    trace_id: str = ""
    normalization_version: Literal["MT5_BROKER_TIME_TO_UTC_V1"] = (
        "MT5_BROKER_TIME_TO_UTC_V1"
    )
    resolution_id: str = Field(min_length=1)
    canonical_instrument: Literal["XAUUSD"]
    resolved_broker_symbol: str = Field(min_length=1)
    source_kind: Literal["TICK", "M1", "M5", "M15", "H1", "H4"]
    raw_epoch_seconds: int
    normalized_at: UTCDateTime
    offset_seconds: int

    @model_validator(mode="after")
    def bind_identity(self) -> MT5TimestampNormalizationTrace:
        if self.offset_seconds % 3_600:
            raise ValueError("normalization trace offset must be whole-hour")
        identity = self.model_dump(mode="json", exclude={"trace_id"})
        expected = f"mt5ts-{canonical_hash(identity)[:20]}"
        if self.trace_id and self.trace_id != expected:
            raise ValueError("trace_id does not match normalized timestamp content")
        object.__setattr__(self, "trace_id", expected)
        return self


def _raw_tick_datetime(raw_tick_time: int, raw_tick_time_msc: int | None) -> datetime:
    if raw_tick_time <= 0:
        raise MT5TimeNormalizationError("broker tick time must be positive")
    if raw_tick_time_msc is not None:
        if raw_tick_time_msc <= 0:
            raise MT5TimeNormalizationError("broker tick time_msc must be positive")
        return datetime.fromtimestamp(raw_tick_time_msc / 1_000, tz=UTC)
    return datetime.fromtimestamp(raw_tick_time, tz=UTC)


def _nearest_whole_hour(delta_seconds: float) -> tuple[int, float]:
    """Select explicitly between adjacent hours; never use Python round()."""
    lower_hours = math.floor(delta_seconds / 3_600)
    upper_hours = lower_hours + 1
    lower_seconds = lower_hours * 3_600
    upper_seconds = upper_hours * 3_600
    lower_distance = abs(delta_seconds - lower_seconds)
    upper_distance = abs(upper_seconds - delta_seconds)
    if lower_distance == upper_distance:
        raise MT5TimeNormalizationError("broker offset is ambiguous between whole-hour values")
    if lower_distance < upper_distance:
        return lower_seconds, lower_distance
    return upper_seconds, upper_distance


def _candidate_offset(
    raw_at: datetime,
    observed_at: datetime,
    policy: MT5BrokerTimePolicy,
) -> int:
    delta_seconds = (raw_at - observed_at).total_seconds()
    candidate, residual = _nearest_whole_hour(delta_seconds)
    minimum = policy.minimum_offset_hours * 3_600
    maximum = policy.maximum_offset_hours * 3_600
    if candidate < minimum or candidate > maximum:
        raise MT5TimeNormalizationError("broker offset is outside the plausible UTC range")
    if residual > policy.inference_residual_tolerance_seconds:
        raise MT5TimeNormalizationError(
            "broker offset residual exceeds whole-hour inference tolerance"
        )
    return candidate


def infer_broker_time_offset(
    *,
    raw_tick_time: int,
    raw_tick_time_msc: int | None,
    observed_at: UTCDateTime,
    canonical_instrument: Literal["XAUUSD"],
    resolved_broker_symbol: str,
    instrument_resolution_id: str,
    environment: MT5BrokerEnvironmentIdentity,
    policy: MT5BrokerTimePolicy | None = None,
) -> MT5BrokerTimeOffsetResolution:
    selected_policy = policy or MT5BrokerTimePolicy()
    observed_at = _strict_utc(observed_at, "observed_at")
    raw_at = _raw_tick_datetime(raw_tick_time, raw_tick_time_msc)
    offset_seconds = _candidate_offset(raw_at, observed_at, selected_policy)
    normalized = raw_at - timedelta(seconds=offset_seconds)
    if normalized > observed_at + timedelta(seconds=selected_policy.future_tolerance_seconds):
        raise MT5TimeNormalizationError("normalized broker tick is in the future")
    return MT5BrokerTimeOffsetResolution(
        canonical_instrument=canonical_instrument,
        resolved_broker_symbol=resolved_broker_symbol,
        instrument_resolution_id=instrument_resolution_id,
        environment=environment,
        offset_seconds=offset_seconds,
        raw_tick_time=raw_tick_time,
        raw_tick_time_msc=raw_tick_time_msc,
        raw_tick_at=raw_at,
        normalized_tick_at=normalized,
        observed_at=observed_at,
        resolved_at=observed_at,
    )


class MT5BrokerTimeNormalizer:
    """Frozen per-session normalizer shared by live tick and rate ingress."""

    def __init__(
        self,
        resolution: MT5BrokerTimeOffsetResolution,
        *,
        policy: MT5BrokerTimePolicy | None = None,
    ) -> None:
        self.resolution = resolution
        self.policy = policy or MT5BrokerTimePolicy()

    @classmethod
    def from_persisted(
        cls,
        resolution: MT5BrokerTimeOffsetResolution,
        *,
        canonical_instrument: str,
        resolved_broker_symbol: str,
        instrument_resolution_id: str,
        environment: MT5BrokerEnvironmentIdentity,
        policy: MT5BrokerTimePolicy | None = None,
    ) -> MT5BrokerTimeNormalizer:
        selected_policy = policy or MT5BrokerTimePolicy()
        if resolution.normalization_version != selected_policy.normalization_version:
            raise MT5TimeNormalizationError("persisted normalization version is incompatible")
        if resolution.canonical_instrument != canonical_instrument:
            raise MT5TimeNormalizationError("persisted canonical instrument is incompatible")
        if resolution.resolved_broker_symbol != resolved_broker_symbol:
            raise MT5TimeNormalizationError("persisted broker symbol is incompatible")
        if resolution.instrument_resolution_id != instrument_resolution_id:
            raise MT5TimeNormalizationError("persisted instrument resolution is incompatible")
        if resolution.environment.environment_id != environment.environment_id:
            raise MT5TimeNormalizationError("persisted broker environment is incompatible")
        return cls(resolution, policy=selected_policy)

    def normalize_epoch_seconds(self, raw_epoch_seconds: int) -> datetime:
        if raw_epoch_seconds <= 0:
            raise MT5TimeNormalizationError("broker timestamp must be positive")
        raw_at = datetime.fromtimestamp(raw_epoch_seconds, tz=UTC)
        return raw_at - timedelta(seconds=self.resolution.offset_seconds)

    def trace(
        self,
        *,
        raw_epoch_seconds: int,
        source_kind: Literal["TICK", "M1", "M5", "M15", "H1", "H4"],
    ) -> MT5TimestampNormalizationTrace:
        return MT5TimestampNormalizationTrace(
            resolution_id=self.resolution.resolution_id,
            canonical_instrument=self.resolution.canonical_instrument,
            resolved_broker_symbol=self.resolution.resolved_broker_symbol,
            source_kind=source_kind,
            raw_epoch_seconds=raw_epoch_seconds,
            normalized_at=self.normalize_epoch_seconds(raw_epoch_seconds),
            offset_seconds=self.resolution.offset_seconds,
        )

    def normalize_tick(
        self,
        *,
        raw_tick_time: int,
        raw_tick_time_msc: int | None,
        observed_at: UTCDateTime,
    ) -> MT5TimestampNormalizationTrace:
        observed_at = _strict_utc(observed_at, "observed_at")
        raw_at = _raw_tick_datetime(raw_tick_time, raw_tick_time_msc)
        try:
            candidate = _candidate_offset(raw_at, observed_at, self.policy)
        except MT5TimeNormalizationError:
            candidate = None
        if candidate is not None and candidate != self.resolution.offset_seconds:
            raise MT5TimeNormalizationError("broker time offset changed during the MT5 session")
        normalized = raw_at - timedelta(seconds=self.resolution.offset_seconds)
        if normalized > observed_at + timedelta(seconds=self.policy.future_tolerance_seconds):
            raise MT5TimeNormalizationError("normalized broker tick is in the future")
        raw_seconds = raw_tick_time_msc // 1_000 if raw_tick_time_msc else raw_tick_time
        return MT5TimestampNormalizationTrace(
            resolution_id=self.resolution.resolution_id,
            canonical_instrument=self.resolution.canonical_instrument,
            resolved_broker_symbol=self.resolution.resolved_broker_symbol,
            source_kind="TICK",
            raw_epoch_seconds=raw_seconds,
            normalized_at=normalized,
            offset_seconds=self.resolution.offset_seconds,
        )


__all__ = [
    "NORMALIZATION_VERSION",
    "MT5BrokerEnvironmentIdentity",
    "MT5BrokerTimeNormalizer",
    "MT5BrokerTimeOffsetResolution",
    "MT5BrokerTimePolicy",
    "MT5TimeNormalizationError",
    "MT5TimestampNormalizationTrace",
    "infer_broker_time_offset",
]
