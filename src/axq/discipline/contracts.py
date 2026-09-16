"""Strict, content-addressed contracts for deterministic trading discipline."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.agents import HypothesisRelationship
from axq.runtime.state import UTCDateTime
from axq.schemas import Signal
from axq.versioning import canonical_hash


class DisciplineModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class DisciplineResult(StrEnum):
    PASS = "PASS"
    REJECT = "REJECT"
    PAUSE = "PAUSE"
    NO_ACTION = "NO_ACTION"


class EntryIntent(StrEnum):
    INITIAL = "INITIAL"
    REENTRY = "REENTRY"


class ReentryPolicy(StrEnum):
    DISABLED = "DISABLED"
    AFTER_EXIT_WITH_NEW_SETUP = "AFTER_EXIT_WITH_NEW_SETUP"


class LossStreakReset(StrEnum):
    AFTER_NON_LOSS_EXIT = "AFTER_NON_LOSS_EXIT"


class DuplicateStatus(StrEnum):
    NONE = "NONE"
    DUPLICATE_PROPOSAL = "DUPLICATE_PROPOSAL"
    DUPLICATE_SETUP = "DUPLICATE_SETUP"
    DUPLICATE_THESIS = "DUPLICATE_THESIS"
    ACTIVE_SETUP = "ACTIVE_SETUP"
    ACTIVE_THESIS = "ACTIVE_THESIS"


class ReentryStatus(StrEnum):
    NOT_REENTRY = "NOT_REENTRY"
    ALLOWED = "ALLOWED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    NOT_PREVIOUSLY_EXECUTED = "NOT_PREVIOUSLY_EXECUTED"
    ACTIVE_THESIS = "ACTIVE_THESIS"
    MISSING_EXIT = "MISSING_EXIT"
    COOLDOWN = "COOLDOWN"


class DisciplineReason(StrEnum):
    MASTER_HOLD = "MASTER_HOLD"
    PASSED = "PASSED"
    STATE_SCOPE_MISMATCH = "STATE_SCOPE_MISMATCH"
    POLICY_PAUSE = "POLICY_PAUSE"
    LOSS_STREAK_PAUSE = "LOSS_STREAK_PAUSE"
    MISSING_STABLE_IDENTITY = "MISSING_STABLE_IDENTITY"
    DUPLICATE_PROPOSAL = "DUPLICATE_PROPOSAL"
    DUPLICATE_SETUP = "DUPLICATE_SETUP"
    DUPLICATE_THESIS = "DUPLICATE_THESIS"
    ACTIVE_SETUP = "ACTIVE_SETUP"
    ACTIVE_THESIS = "ACTIVE_THESIS"
    REENTRY_DISABLED = "REENTRY_DISABLED"
    REENTRY_NOT_PREVIOUSLY_EXECUTED = "REENTRY_NOT_PREVIOUSLY_EXECUTED"
    REENTRY_MISSING_EXIT = "REENTRY_MISSING_EXIT"
    REENTRY_COOLDOWN = "REENTRY_COOLDOWN"
    MAX_SIMULTANEOUS_POSITIONS = "MAX_SIMULTANEOUS_POSITIONS"
    SAME_DIRECTION_POSITION_ACTIVE = "SAME_DIRECTION_POSITION_ACTIVE"
    DAILY_TRADE_CAP = "DAILY_TRADE_CAP"
    SESSION_TRADE_CAP = "SESSION_TRADE_CAP"
    STOP_LOSS_COOLDOWN = "STOP_LOSS_COOLDOWN"
    ORDINARY_COOLDOWN = "ORDINARY_COOLDOWN"
    POST_REJECTION_COOLDOWN = "POST_REJECTION_COOLDOWN"


class DisciplinePolicy(DisciplineModel):
    policy_id: str = ""
    policy_version: str = Field(min_length=1)
    max_trades_per_day: int = Field(gt=0)
    max_trades_per_session: int = Field(gt=0)
    max_simultaneous_positions: int = Field(gt=0)
    ordinary_cooldown_seconds: int = Field(ge=0)
    stop_loss_cooldown_seconds: int = Field(ge=0)
    post_rejection_cooldown_seconds: int = Field(ge=0)
    same_direction_reentry_cooldown_seconds: int = Field(ge=0)
    consecutive_loss_threshold: int = Field(gt=0)
    loss_streak_pause_seconds: int = Field(gt=0)
    loss_streak_reset: LossStreakReset
    prevent_duplicate_setup: bool
    prevent_duplicate_thesis: bool
    prevent_same_direction_position: bool
    reentry_policy: ReentryPolicy

    @model_validator(mode="after")
    def bind_identity(self) -> DisciplinePolicy:
        identity = self.model_dump(mode="json", exclude={"policy_id"})
        expected = f"dp-{canonical_hash(identity)[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match discipline policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class DisciplinePosition(DisciplineModel):
    position_ref: str = Field(min_length=1)
    direction: Signal
    setup_id: str | None = None
    thesis_id: str | None = None
    opened_at: UTCDateTime

    @model_validator(mode="after")
    def reject_hold(self) -> DisciplinePosition:
        if self.direction is Signal.HOLD:
            raise ValueError("discipline position direction cannot be HOLD")
        return self


class DisciplineState(DisciplineModel):
    state_id: str = ""
    policy_id: str = Field(min_length=1)
    as_of: UTCDateTime
    available_at: UTCDateTime
    trading_day: date
    session_id: str = Field(min_length=1)
    trades_today: int = Field(ge=0)
    trades_this_session: int = Field(ge=0)
    consecutive_losses: int = Field(ge=0)
    last_entry_at: UTCDateTime | None = None
    last_exit_at: UTCDateTime | None = None
    last_stop_loss_at: UTCDateTime | None = None
    last_rejection_at: UTCDateTime | None = None
    last_entry_direction: Signal | None = None
    paused_until: UTCDateTime | None = None
    pause_reason: str | None = Field(default=None, max_length=200)
    active_positions: tuple[DisciplinePosition, ...] = ()
    active_setup_ids: tuple[str, ...] = ()
    active_thesis_ids: tuple[str, ...] = ()
    recently_executed_setup_ids: tuple[str, ...] = ()
    recently_executed_thesis_ids: tuple[str, ...] = ()
    last_accepted_master_proposal_id: str | None = None
    last_rejected_master_proposal_id: str | None = None
    recorded_at: UTCDateTime | None = None

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> DisciplineState:
        if self.available_at > self.as_of:
            raise ValueError("discipline state cannot be available after as_of")
        for value in (
            self.last_entry_at,
            self.last_exit_at,
            self.last_stop_loss_at,
            self.last_rejection_at,
        ):
            if value is not None and value > self.as_of:
                raise ValueError("discipline history cannot be in the future")
        if self.last_entry_direction is Signal.HOLD:
            raise ValueError("last entry direction cannot be HOLD")
        positions = tuple(sorted(self.active_positions, key=lambda item: item.position_ref))
        if len({item.position_ref for item in positions}) != len(positions):
            raise ValueError("active discipline positions must be unique")
        if any(item.opened_at > self.as_of for item in positions):
            raise ValueError("discipline position cannot open after state as_of")
        object.__setattr__(self, "active_positions", positions)
        set_fields = (
            "active_setup_ids",
            "active_thesis_ids",
            "recently_executed_setup_ids",
            "recently_executed_thesis_ids",
        )
        for field_name in set_fields:
            values = tuple(sorted(getattr(self, field_name)))
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must be unique")
            object.__setattr__(self, field_name, values)
        identity = self.model_dump(mode="json", exclude={"state_id", "recorded_at"})
        expected = f"ds-{canonical_hash(identity)[:20]}"
        if self.state_id and self.state_id != expected:
            raise ValueError("state_id does not match discipline state content")
        object.__setattr__(self, "state_id", expected)
        return self


class DisciplineContext(DisciplineModel):
    context_id: str = ""
    as_of: UTCDateTime
    available_at: UTCDateTime
    trading_day: date
    session_id: str = Field(min_length=1)
    setup_id: str | None = None
    thesis_id: str | None = None
    scenario_id: str | None = None
    thesis_relationship: HypothesisRelationship | None = None
    entry_intent: EntryIntent = EntryIntent.INITIAL

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> DisciplineContext:
        if self.available_at > self.as_of:
            raise ValueError("discipline context cannot be available after as_of")
        identity = self.model_dump(mode="json", exclude={"context_id"})
        expected = f"dc-{canonical_hash(identity)[:20]}"
        if self.context_id and self.context_id != expected:
            raise ValueError("context_id does not match discipline context content")
        object.__setattr__(self, "context_id", expected)
        return self


class DisciplineCounters(DisciplineModel):
    trades_today: int = Field(ge=0)
    trades_this_session: int = Field(ge=0)
    consecutive_losses: int = Field(ge=0)
    active_positions: int = Field(ge=0)


class DisciplineOutcome(DisciplineModel):
    outcome_id: str = ""
    master_proposal_id: str = Field(min_length=1)
    evidence_bundle_id: str = Field(min_length=1)
    discipline_policy_id: str = Field(min_length=1)
    discipline_policy_version: str = Field(min_length=1)
    discipline_state_id: str = Field(min_length=1)
    discipline_context_id: str = Field(min_length=1)
    setup_id: str | None = None
    thesis_id: str | None = None
    scenario_id: str | None = None
    as_of: UTCDateTime
    available_at: UTCDateTime
    master_decision: Signal
    result: DisciplineResult
    eligible_for_risk: bool
    reason_codes: tuple[DisciplineReason, ...] = Field(min_length=1)
    counters: DisciplineCounters
    next_eligible_at: UTCDateTime | None = None
    duplicate_status: DuplicateStatus = DuplicateStatus.NONE
    reentry_status: ReentryStatus = ReentryStatus.NOT_REENTRY
    rationale: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> DisciplineOutcome:
        if self.available_at > self.as_of:
            raise ValueError("discipline outcome cannot be available after as_of")
        if self.eligible_for_risk != (self.result is DisciplineResult.PASS):
            raise ValueError("only PASS remains eligible for downstream Risk")
        if self.master_decision is Signal.HOLD and self.result is not DisciplineResult.NO_ACTION:
            raise ValueError("Master HOLD must produce NO_ACTION")
        if self.result is DisciplineResult.NO_ACTION and self.master_decision is not Signal.HOLD:
            raise ValueError("NO_ACTION requires Master HOLD")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("discipline reason codes must be unique")
        identity = self.model_dump(mode="json", exclude={"outcome_id"})
        expected = f"do-{canonical_hash(identity)[:20]}"
        if self.outcome_id and self.outcome_id != expected:
            raise ValueError("outcome_id does not match discipline outcome content")
        object.__setattr__(self, "outcome_id", expected)
        return self
