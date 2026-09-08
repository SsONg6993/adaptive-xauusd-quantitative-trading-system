"""Label definitions only; dataset construction belongs to Phase 3."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LabelKind(StrEnum):
    DIRECTION = "DIRECTION"
    FORWARD_RETURN = "FORWARD_RETURN"
    ATR_ADJUSTED_RETURN = "ATR_ADJUSTED_RETURN"
    TRIPLE_BARRIER = "TRIPLE_BARRIER"
    TP_BEFORE_SL = "TP_BEFORE_SL"


class LabelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    kind: LabelKind
    horizon_bars: int = Field(gt=0)
    neutral_threshold: float = Field(default=0.0, ge=0.0)
    take_profit_atr: float | None = Field(default=None, gt=0)
    stop_loss_atr: float | None = Field(default=None, gt=0)
    max_holding_bars: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def barrier_parameters_are_complete(self) -> LabelConfig:
        if self.kind in {LabelKind.TRIPLE_BARRIER, LabelKind.TP_BEFORE_SL} and (
            self.take_profit_atr is None or self.stop_loss_atr is None
        ):
            raise ValueError("barrier labels require take_profit_atr and stop_loss_atr")
        return self
