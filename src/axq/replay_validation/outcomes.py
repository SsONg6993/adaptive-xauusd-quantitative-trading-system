"""Durable content-addressed facts emitted by the deterministic replay transport."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.position_actions import PositionActionType
from axq.replay_validation.execution import ReplayClosedTrade, ReplayFill, ReplaySide
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class ReplayOutcomeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class ReplayFillOutcome(ReplayOutcomeModel):
    replay_fill_id: str = Field(min_length=1)
    execution_intent_id: str = Field(min_length=1)
    execution_result_id: str = Field(min_length=1)
    position_id: str = Field(min_length=1)
    direction: ReplaySide
    volume_lots: FiniteFloat = Field(gt=0.0)
    fill_price: FiniteFloat = Field(gt=0.0)
    executed_at: UTCDateTime

    @classmethod
    def from_replay(
        cls,
        fill: ReplayFill,
        *,
        execution_result_id: str,
    ) -> ReplayFillOutcome:
        return cls(
            replay_fill_id=fill.semantic_id,
            execution_intent_id=fill.instruction_id,
            execution_result_id=execution_result_id,
            position_id=fill.position_id,
            direction=fill.side,
            volume_lots=fill.volume_lots,
            fill_price=fill.price,
            executed_at=fill.executed_at,
        )


class ReplayTradeOutcome(ReplayOutcomeModel):
    replay_trade_id: str = Field(min_length=1)
    source_execution_intent_id: str = Field(min_length=1)
    position_id: str = Field(min_length=1)
    direction: ReplaySide
    volume_lots: FiniteFloat = Field(gt=0.0)
    opened_at: UTCDateTime
    closed_at: UTCDateTime
    entry_price: FiniteFloat = Field(gt=0.0)
    exit_price: FiniteFloat = Field(gt=0.0)
    initial_stop_loss: FiniteFloat = Field(gt=0.0)
    exit_reason: str = Field(min_length=1)
    source_position_action_intent_id: str | None = None
    mfe_points: FiniteFloat = Field(ge=0.0)
    mae_points: FiniteFloat = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_times_and_exit_link(self) -> ReplayTradeOutcome:
        if self.closed_at < self.opened_at:
            raise ValueError("replay trade cannot close before it opens")
        explicit = self.exit_reason == "POSITION_ACTION_CLOSE"
        if explicit != (self.source_position_action_intent_id is not None):
            raise ValueError("explicit replay exit requires its exact position-action intent")
        return self

    @classmethod
    def from_replay(
        cls,
        trade: ReplayClosedTrade,
        *,
        source_position_action_intent_id: str | None = None,
    ) -> ReplayTradeOutcome:
        return cls(
            replay_trade_id=trade.semantic_id,
            source_execution_intent_id=trade.source_intent_id,
            position_id=trade.position_id,
            direction=trade.side,
            volume_lots=trade.volume_lots,
            opened_at=trade.opened_at,
            closed_at=trade.closed_at,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            initial_stop_loss=trade.initial_stop_loss,
            exit_reason=trade.exit_reason,
            source_position_action_intent_id=source_position_action_intent_id,
            mfe_points=trade.mfe_points,
            mae_points=trade.mae_points,
        )


class ReplayActionApplication(ReplayOutcomeModel):
    position_action_intent_id: str = Field(min_length=1)
    position_id: str = Field(min_length=1)
    action_type: PositionActionType
    applied_at: UTCDateTime


class ReplayEventContext(ReplayOutcomeModel):
    runtime_event_id: str = Field(min_length=1)
    available_at: UTCDateTime
    session: str | None = None
    regime: str | None = None


class ReplayOutcomeArtifact(ReplayOutcomeModel):
    artifact_id: str = ""
    source_metrics_id: str = Field(min_length=1)
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    entry_model: str = Field(min_length=1)
    stop_model: str = Field(min_length=1)
    spread_model: str = Field(min_length=1)
    slippage_points: FiniteFloat = Field(ge=0.0)
    fills: tuple[ReplayFillOutcome, ...] = ()
    trades: tuple[ReplayTradeOutcome, ...] = ()
    action_applications: tuple[ReplayActionApplication, ...] = ()
    event_contexts: tuple[ReplayEventContext, ...] = ()

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> ReplayOutcomeArtifact:
        fields_and_keys = (
            ("fills", "replay_fill_id"),
            ("trades", "replay_trade_id"),
            ("action_applications", "position_action_intent_id"),
            ("event_contexts", "runtime_event_id"),
        )
        for field_name, key_name in fields_and_keys:
            values = tuple(
                sorted(
                    getattr(self, field_name),
                    key=lambda item: getattr(item, key_name),
                )
            )
            keys = tuple(getattr(item, key_name) for item in values)
            if len(keys) != len(set(keys)):
                raise ValueError(f"{field_name} must have unique semantic IDs")
            object.__setattr__(self, field_name, values)
        identity = self.model_dump(mode="json", exclude={"artifact_id"})
        expected = f"replay-outcomes-{canonical_hash(identity)[:20]}"
        if self.artifact_id and self.artifact_id != expected:
            raise ValueError("artifact_id does not match replay outcome content")
        object.__setattr__(self, "artifact_id", expected)
        return self

    def write(self, path: str | Path) -> None:
        payload = json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        Path(path).write_text(payload + "\n", encoding="utf-8")

    @classmethod
    def read(cls, path: str | Path) -> ReplayOutcomeArtifact:
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))
