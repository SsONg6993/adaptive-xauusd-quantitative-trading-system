"""Exact, explicitly configured broker-symbol resolution for canonical Gold."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class CanonicalInstrument(StrEnum):
    XAUUSD = "XAUUSD"


class BrokerSymbolSelectionMode(StrEnum):
    SINGLE = "SINGLE"
    ORDERED_ALLOWLIST = "ORDERED_ALLOWLIST"


class GoldSymbolConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    configuration_id: str = ""
    canonical_instrument: Literal[CanonicalInstrument.XAUUSD] = CanonicalInstrument.XAUUSD
    mode: BrokerSymbolSelectionMode
    broker_symbols: tuple[str, ...] = Field(min_length=1)

    @classmethod
    def single(cls, broker_symbol: str) -> GoldSymbolConfiguration:
        return cls(mode=BrokerSymbolSelectionMode.SINGLE, broker_symbols=(broker_symbol,))

    @classmethod
    def aliases(cls, broker_symbols: tuple[str, ...]) -> GoldSymbolConfiguration:
        return cls(
            mode=BrokerSymbolSelectionMode.ORDERED_ALLOWLIST,
            broker_symbols=broker_symbols,
        )

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> GoldSymbolConfiguration:
        normalized = tuple(item.strip() for item in self.broker_symbols)
        if any(not item for item in normalized):
            raise ValueError("broker symbols must be non-empty")
        if normalized != self.broker_symbols:
            raise ValueError("broker symbols must already be stripped")
        if len(set(normalized)) != len(normalized):
            raise ValueError("broker symbols must be unique")
        if self.mode is BrokerSymbolSelectionMode.SINGLE and len(normalized) != 1:
            raise ValueError("single symbol mode requires exactly one broker symbol")
        identity = self.model_dump(mode="json", exclude={"configuration_id"})
        expected = f"gsc-{canonical_hash(identity)[:20]}"
        if self.configuration_id and self.configuration_id != expected:
            raise ValueError("configuration_id does not match symbol configuration")
        object.__setattr__(self, "configuration_id", expected)
        return self


class ResolvedBrokerInstrument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    resolution_id: str = ""
    configuration_id: str = Field(min_length=1)
    canonical_instrument: Literal[CanonicalInstrument.XAUUSD] = CanonicalInstrument.XAUUSD
    resolved_broker_symbol: str = Field(min_length=1)
    checked_broker_symbols: tuple[str, ...] = Field(min_length=1)
    point_size: float = Field(gt=0)
    available_at: UTCDateTime

    @model_validator(mode="after")
    def bind_identity(self) -> ResolvedBrokerInstrument:
        identity = self.model_dump(mode="json", exclude={"resolution_id", "available_at"})
        expected = f"rbi-{canonical_hash(identity)[:20]}"
        if self.resolution_id and self.resolution_id != expected:
            raise ValueError("resolution_id does not match resolved broker instrument")
        object.__setattr__(self, "resolution_id", expected)
        return self


class SymbolInfoGateway(Protocol):
    def symbol_info(self, symbol: str) -> Mapping[str, object] | None: ...


def resolve_gold_instrument(
    gateway: SymbolInfoGateway,
    configuration: GoldSymbolConfiguration,
    *,
    resolved_at: UTCDateTime,
) -> ResolvedBrokerInstrument:
    """Resolve only explicit exact names, in configured priority order."""

    checked: list[str] = []
    for broker_symbol in configuration.broker_symbols:
        checked.append(broker_symbol)
        info = gateway.symbol_info(broker_symbol)
        if info is not None and info.get("name") == broker_symbol:
            point = info.get("point")
            if (
                not isinstance(point, (int, float))
                or isinstance(point, bool)
                or float(point) <= 0
            ):
                continue
            return ResolvedBrokerInstrument(
                configuration_id=configuration.configuration_id,
                resolved_broker_symbol=broker_symbol,
                checked_broker_symbols=tuple(checked),
                point_size=float(point),
                available_at=resolved_at,
            )
    raise ValueError(
        "none of the explicitly configured Gold broker symbols is available: "
        + ", ".join(configuration.broker_symbols)
    )


__all__ = [
    "BrokerSymbolSelectionMode",
    "CanonicalInstrument",
    "GoldSymbolConfiguration",
    "ResolvedBrokerInstrument",
    "resolve_gold_instrument",
]
