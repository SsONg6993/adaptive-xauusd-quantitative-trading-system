"""Versioned label contracts. Labels may look forward; features never may."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LabelKind(StrEnum):
    DIRECTION = "DIRECTION"
    FORWARD_RETURN = "FORWARD_RETURN"
    ATR_ADJUSTED_RETURN = "ATR_ADJUSTED_RETURN"
    TRIPLE_BARRIER = "TRIPLE_BARRIER"
    TP_BEFORE_SL = "TP_BEFORE_SL"


class ThresholdMode(StrEnum):
    ABSOLUTE = "ABSOLUTE"
    PERCENTAGE = "PERCENTAGE"
    ATR = "ATR"


class ReturnMode(StrEnum):
    SIMPLE = "SIMPLE"
    LOG = "LOG"
    ATR = "ATR"


class BarrierMode(StrEnum):
    PERCENTAGE = "PERCENTAGE"
    ATR = "ATR"
    ABSOLUTE = "ABSOLUTE"


class CollisionPolicy(StrEnum):
    PESSIMISTIC = "PESSIMISTIC"
    OPTIMISTIC = "OPTIMISTIC"
    AMBIGUOUS = "AMBIGUOUS"
    LOWER_TIMEFRAME = "LOWER_TIMEFRAME"


class TradeSide(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class EntryReference(StrEnum):
    CLOSE = "CLOSE"


class LabelDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    version: str
    kind: LabelKind
    horizon_bars: int = Field(gt=0)
    threshold_mode: ThresholdMode = ThresholdMode.PERCENTAGE
    neutral_threshold: float = Field(default=0.0, ge=0.0)
    return_mode: ReturnMode = ReturnMode.SIMPLE
    barrier_mode: BarrierMode = BarrierMode.ATR
    upper_barrier: float | None = Field(default=None, gt=0.0)
    lower_barrier: float | None = Field(default=None, gt=0.0)
    side: TradeSide = TradeSide.LONG
    collision_policy: CollisionPolicy = CollisionPolicy.AMBIGUOUS
    entry_reference: EntryReference = EntryReference.CLOSE
    atr_column: str = "vol_atr_14"

    @model_validator(mode="after")
    def barrier_parameters_are_complete(self) -> LabelDefinition:
        if self.kind in {LabelKind.TRIPLE_BARRIER, LabelKind.TP_BEFORE_SL} and (
            self.upper_barrier is None or self.lower_barrier is None
        ):
            raise ValueError("barrier labels require upper_barrier and lower_barrier")
        return self

    @property
    def required_source_columns(self) -> list[str]:
        columns = ["timestamp", "high", "low", "close"]
        uses_atr = (
            (self.kind == LabelKind.DIRECTION and self.threshold_mode == ThresholdMode.ATR)
            or (
                self.kind in {LabelKind.FORWARD_RETURN, LabelKind.ATR_ADJUSTED_RETURN}
                and (
                    self.return_mode == ReturnMode.ATR
                    or self.kind == LabelKind.ATR_ADJUSTED_RETURN
                )
            )
            or (
                self.kind in {LabelKind.TRIPLE_BARRIER, LabelKind.TP_BEFORE_SL}
                and self.barrier_mode == BarrierMode.ATR
            )
        )
        if uses_atr:
            columns.append(self.atr_column)
        return sorted(set(columns))
