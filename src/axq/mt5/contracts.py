"""Narrow contracts isolating the optional MetaTrader5 package."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.execution_boundary import BrokerObjectKind
from axq.versioning import canonical_hash


class MT5ConnectionError(RuntimeError):
    """The terminal package or connected terminal is unavailable."""


class MT5Constants(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    account_trade_mode_demo: int
    account_trade_mode_contest: int
    account_trade_mode_real: int
    symbol_trade_mode_disabled: int
    position_type_buy: int
    position_type_sell: int
    order_type_buy: int
    order_type_sell: int
    order_type_buy_limit: int
    order_type_sell_limit: int
    order_type_buy_stop: int
    order_type_sell_stop: int
    order_type_buy_stop_limit: int
    order_type_sell_stop_limit: int
    trade_action_deal: int
    trade_action_sltp: int
    order_time_gtc: int
    order_filling_ioc: int
    trade_retcode_requote: int
    trade_retcode_placed: int
    trade_retcode_done: int
    trade_retcode_done_partial: int


class MT5SymbolMapping(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "1.0"
    mapping_id: str = ""
    internal_symbol: str = Field(min_length=1)
    broker_symbol: str = Field(min_length=1)

    @model_validator(mode="after")
    def bind_identity(self) -> MT5SymbolMapping:
        identity = self.model_dump(mode="json", exclude={"mapping_id"})
        expected = f"msm-{canonical_hash(identity)[:20]}"
        if self.mapping_id and self.mapping_id != expected:
            raise ValueError("mapping_id does not match MT5 symbol mapping content")
        object.__setattr__(self, "mapping_id", expected)
        return self

    def to_broker(self, symbol: str) -> str:
        if symbol != self.internal_symbol:
            raise ValueError(f"internal symbol {symbol!r} is not configured")
        return self.broker_symbol

    def to_internal(self, symbol: str) -> str:
        if symbol != self.broker_symbol:
            raise ValueError(f"broker symbol {symbol!r} is not configured")
        return self.internal_symbol


class MT5PersistedIntentLink(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    linkage_id: str = ""
    intent_id: str = Field(min_length=1)
    object_kind: BrokerObjectKind
    broker_ticket: int = Field(gt=0)
    transport_execution_id: str = Field(min_length=1)
    setup_id: str | None = None
    thesis_id: str | None = None

    @model_validator(mode="after")
    def bind_identity(self) -> MT5PersistedIntentLink:
        identity = self.model_dump(mode="json", exclude={"linkage_id"})
        expected = f"mpl-{canonical_hash(identity)[:20]}"
        if self.linkage_id and self.linkage_id != expected:
            raise ValueError("linkage_id does not match persisted MT5 linkage content")
        object.__setattr__(self, "linkage_id", expected)
        return self


class MT5SnapshotError(RuntimeError):
    """A broker snapshot could not be acquired without guessing."""


class MT5Gateway(Protocol):
    @property
    def constants(self) -> MT5Constants: ...

    def connect(self) -> None: ...

    def close(self) -> None: ...

    def last_error(self) -> object: ...

    def terminal_info(self) -> Mapping[str, object] | None: ...

    def account_info(self) -> Mapping[str, object] | None: ...

    def symbol_select(self, symbol: str, enabled: bool) -> bool: ...

    def symbol_info(self, symbol: str) -> Mapping[str, object] | None: ...

    def symbol_info_tick(self, symbol: str) -> Mapping[str, object] | None: ...

    def positions_get(self, symbol: str | None = None) -> tuple[Mapping[str, object], ...]: ...

    def orders_get(self, symbol: str | None = None) -> tuple[Mapping[str, object], ...]: ...

    def order_check(self, request: Mapping[str, object]) -> Mapping[str, object] | None: ...

    def order_send(self, request: Mapping[str, object]) -> Mapping[str, object] | None: ...
