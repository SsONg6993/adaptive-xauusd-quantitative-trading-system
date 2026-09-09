"""Immutable contracts for safe actions on authoritative open positions."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.execution_boundary import (
    BrokerIntentLink,
    ExecutionIntent,
    ExecutionResult,
    ReconciliationReport,
    ResumeReadiness,
)
from axq.position_management import PositionManagementOutcome
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    MarketState,
    PositionSide,
    PositionState,
)
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class PositionActionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class PositionActionType(StrEnum):
    NO_ACTION = "NO_ACTION"
    MODIFY_PROTECTIVE_STOP = "MODIFY_PROTECTIVE_STOP"
    CLOSE_POSITION = "CLOSE_POSITION"


class PositionActionSafetyResult(StrEnum):
    NO_ACTION = "NO_ACTION"
    PASS = "PASS"
    REJECT = "REJECT"
    EMERGENCY_BLOCK = "EMERGENCY_BLOCK"


class PositionActionReason(StrEnum):
    MANAGEMENT_DID_NOT_REQUEST_ACTION = "MANAGEMENT_DID_NOT_REQUEST_ACTION"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    MANAGEMENT_OUTCOME_STALE = "MANAGEMENT_OUTCOME_STALE"
    RUNTIME_NOT_SAFE = "RUNTIME_NOT_SAFE"
    RECONCILIATION_UNRESOLVED = "RECONCILIATION_UNRESOLVED"
    UNKNOWN_EXECUTION_STATE = "UNKNOWN_EXECUTION_STATE"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    POSITION_MISSING = "POSITION_MISSING"
    POSITION_SNAPSHOT_CHANGED = "POSITION_SNAPSHOT_CHANGED"
    EXACT_LINKAGE_MISMATCH = "EXACT_LINKAGE_MISMATCH"
    RECONCILIATION_POSITION_STALE = "RECONCILIATION_POSITION_STALE"
    TICKET_MISMATCH = "TICKET_MISMATCH"
    SYMBOL_MISMATCH = "SYMBOL_MISMATCH"
    DIRECTION_MISMATCH = "DIRECTION_MISMATCH"
    VOLUME_MISMATCH = "VOLUME_MISMATCH"
    SETUP_LINKAGE_MISMATCH = "SETUP_LINKAGE_MISMATCH"
    THESIS_LINKAGE_MISMATCH = "THESIS_LINKAGE_MISMATCH"
    SCENARIO_LINKAGE_MISMATCH = "SCENARIO_LINKAGE_MISMATCH"
    ACCOUNT_NOT_FRESH = "ACCOUNT_NOT_FRESH"
    POSITION_NOT_FRESH = "POSITION_NOT_FRESH"
    BROKER_CONSTRAINTS_NOT_FRESH = "BROKER_CONSTRAINTS_NOT_FRESH"
    RECONCILIATION_NOT_FRESH = "RECONCILIATION_NOT_FRESH"
    MARKET_PRICE_NOT_FRESH = "MARKET_PRICE_NOT_FRESH"
    BROKER_TRADING_DISABLED = "BROKER_TRADING_DISABLED"
    BROKER_CONSTRAINTS_UNAVAILABLE = "BROKER_CONSTRAINTS_UNAVAILABLE"
    CURRENT_STOP_CHANGED = "CURRENT_STOP_CHANGED"
    MISSING_STOP_NOT_ALLOWED = "MISSING_STOP_NOT_ALLOWED"
    PROTECTION_NOT_RISK_REDUCING = "PROTECTION_NOT_RISK_REDUCING"
    PROTECTION_EXCEEDS_ORIGINAL_RISK = "PROTECTION_EXCEEDS_ORIGINAL_RISK"
    BROKER_STOP_DIRECTION_INVALID = "BROKER_STOP_DIRECTION_INVALID"
    BROKER_STOP_DISTANCE_VIOLATION = "BROKER_STOP_DISTANCE_VIOLATION"
    SAFE_NORMALIZATION_IMPOSSIBLE = "SAFE_NORMALIZATION_IMPOSSIBLE"
    MODIFY_PROTECTIVE_STOP_SAFE = "MODIFY_PROTECTIVE_STOP_SAFE"
    CLOSE_POSITION_SAFE = "CLOSE_POSITION_SAFE"


class PositionActionPolicy(PositionActionModel):
    policy_id: str = ""
    policy_version: str = Field(min_length=1)
    max_management_outcome_age_seconds: float = Field(gt=0.0)
    max_component_age_seconds: float = Field(gt=0.0)
    volume_tolerance_lots: FiniteFloat = Field(ge=0.0)
    allow_add_protective_stop_when_missing: bool
    allow_risk_reducing_tick_normalization: bool

    @model_validator(mode="after")
    def bind_identity(self) -> PositionActionPolicy:
        expected = f"pap-{canonical_hash(self.model_dump(mode='json', exclude={'policy_id'}))[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match position-action policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class PositionActionContext(PositionActionModel):
    context_id: str = ""
    policy_id: str = Field(min_length=1)
    management_outcome: PositionManagementOutcome
    position: PositionState | None
    original_execution_intent: ExecutionIntent
    original_execution_result: ExecutionResult
    broker_intent_link: BrokerIntentLink
    reconciliation: ReconciliationReport
    resume_readiness: ResumeReadiness
    account: AccountState
    position_freshness: ComponentFreshness
    broker_constraints: BrokerConstraints
    market: MarketState
    symbol_digits: int = Field(ge=0, le=12)
    kill_switch_active: bool
    as_of: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PositionActionContext:
        if self.available_at > self.as_of:
            raise ValueError("position-action context cannot be available after as_of")
        if self.resume_readiness.reconciliation_report_id != self.reconciliation.report_id:
            raise ValueError("readiness references a different reconciliation report")
        causal_times = (
            self.management_outcome.available_at,
            self.original_execution_result.available_at,
            self.reconciliation.available_at,
            self.resume_readiness.as_of,
            self.account.as_of,
            self.broker_constraints.as_of,
            self.market.as_of,
        )
        if any(value > self.as_of for value in causal_times):
            raise ValueError("position-action context cannot contain future state")
        freshness_values = (
            self.account.freshness,
            self.position_freshness,
            self.broker_constraints.freshness,
            self.market.freshness,
        )
        if any(
            item.available_at is not None and item.available_at > self.as_of
            for item in freshness_values
        ):
            raise ValueError("position-action context cannot contain future availability")
        identity = self.model_dump(mode="json", exclude={"context_id"})
        expected = f"pac-{canonical_hash(identity)[:20]}"
        if self.context_id and self.context_id != expected:
            raise ValueError("context_id does not match position-action context content")
        object.__setattr__(self, "context_id", expected)
        return self


class PositionActionSafetyOutcome(PositionActionModel):
    safety_outcome_id: str = ""
    policy_id: str = Field(min_length=1)
    context_id: str = Field(min_length=1)
    position_management_outcome_id: str = Field(min_length=1)
    position_id: str | None = None
    result: PositionActionSafetyResult
    requested_action: PositionActionType
    reason_codes: tuple[PositionActionReason, ...] = Field(min_length=1)
    eligible_for_intent: bool
    normalized_protective_stop_loss: FiniteFloat | None = Field(default=None, gt=0.0)
    requested_close_volume_lots: FiniteFloat | None = Field(default=None, gt=0.0)
    as_of: UTCDateTime
    available_at: UTCDateTime
    rationale: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PositionActionSafetyOutcome:
        if self.available_at > self.as_of:
            raise ValueError("position-action safety outcome cannot be available after as_of")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("position-action reason codes must be unique")
        if self.eligible_for_intent != (self.result is PositionActionSafetyResult.PASS):
            raise ValueError("only PASS may be eligible for a position-action intent")
        if self.result is PositionActionSafetyResult.NO_ACTION:
            if self.requested_action is not PositionActionType.NO_ACTION:
                raise ValueError("NO_ACTION safety result cannot request an action")
        elif self.requested_action is PositionActionType.NO_ACTION:
            raise ValueError("action safety result requires the requested action")
        if self.requested_action is PositionActionType.MODIFY_PROTECTIVE_STOP:
            if self.result is PositionActionSafetyResult.PASS and (
                self.normalized_protective_stop_loss is None
            ):
                raise ValueError("passed protective modification requires a normalized stop")
            if self.requested_close_volume_lots is not None:
                raise ValueError("protective modification cannot request close volume")
        elif self.normalized_protective_stop_loss is not None:
            raise ValueError("only protective modification may contain a normalized stop")
        if self.requested_action is PositionActionType.CLOSE_POSITION:
            if self.result is PositionActionSafetyResult.PASS and (
                self.requested_close_volume_lots is None
            ):
                raise ValueError("passed close requires an explicit close volume")
        elif self.requested_close_volume_lots is not None:
            raise ValueError("only close action may contain close volume")
        identity = self.model_dump(mode="json", exclude={"safety_outcome_id"})
        expected = f"pas-{canonical_hash(identity)[:20]}"
        if self.safety_outcome_id and self.safety_outcome_id != expected:
            raise ValueError("safety_outcome_id does not match safety outcome content")
        object.__setattr__(self, "safety_outcome_id", expected)
        return self


class PositionActionIntent(PositionActionModel):
    intent_id: str = ""
    policy_id: str = Field(min_length=1)
    safety_outcome_id: str = Field(min_length=1)
    position_management_outcome_id: str = Field(min_length=1)
    position_id: str = Field(min_length=1)
    broker_ticket: int | None = Field(default=None, gt=0)
    original_execution_intent_id: str = Field(min_length=1)
    original_execution_result_id: str = Field(min_length=1)
    broker_intent_link_id: str = Field(min_length=1)
    reconciliation_report_id: str = Field(min_length=1)
    resume_readiness_id: str = Field(min_length=1)
    setup_id: str = Field(min_length=1)
    thesis_id: str = Field(min_length=1)
    scenario_id: str | None = None
    action_type: PositionActionType
    symbol: str = Field(min_length=1)
    position_side: PositionSide
    current_volume_lots: FiniteFloat = Field(gt=0.0)
    requested_close_volume_lots: FiniteFloat | None = Field(default=None, gt=0.0)
    existing_stop_loss: FiniteFloat | None = Field(default=None, gt=0.0)
    requested_new_stop_loss: FiniteFloat | None = Field(default=None, gt=0.0)
    audit_reason_codes: tuple[PositionActionReason, ...] = Field(min_length=1)
    as_of: UTCDateTime
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PositionActionIntent:
        if self.available_at > self.as_of:
            raise ValueError("position-action intent cannot be available after as_of")
        if self.action_type is PositionActionType.NO_ACTION:
            raise ValueError("NO_ACTION cannot become a position-action intent")
        if len(self.audit_reason_codes) != len(set(self.audit_reason_codes)):
            raise ValueError("position-action audit reasons must be unique")
        if self.action_type is PositionActionType.MODIFY_PROTECTIVE_STOP:
            if self.requested_new_stop_loss is None:
                raise ValueError("protective modification requires a new stop")
            if self.requested_close_volume_lots is not None:
                raise ValueError("protective modification cannot request close volume")
            if self.existing_stop_loss is not None:
                increases_risk = (
                    self.position_side is PositionSide.BUY
                    and self.requested_new_stop_loss < self.existing_stop_loss
                ) or (
                    self.position_side is PositionSide.SELL
                    and self.requested_new_stop_loss > self.existing_stop_loss
                )
                if increases_risk and not math.isclose(
                    self.requested_new_stop_loss,
                    self.existing_stop_loss,
                    abs_tol=1e-10,
                    rel_tol=0.0,
                ):
                    raise ValueError("protective stop cannot increase risk")
        else:
            if self.requested_new_stop_loss is not None:
                raise ValueError("close action cannot request a new stop")
            if self.requested_close_volume_lots is None:
                raise ValueError("close action requires close volume")
            if self.requested_close_volume_lots > self.current_volume_lots and not math.isclose(
                self.requested_close_volume_lots,
                self.current_volume_lots,
                abs_tol=1e-10,
                rel_tol=0.0,
            ):
                raise ValueError("close volume cannot exceed current position volume")
            if not math.isclose(
                self.requested_close_volume_lots,
                self.current_volume_lots,
                abs_tol=1e-10,
                rel_tol=0.0,
            ):
                raise ValueError("V1 position action supports full close only")
        identity = self.model_dump(mode="json", exclude={"intent_id"})
        expected = f"pai-{canonical_hash(identity)[:20]}"
        if self.intent_id and self.intent_id != expected:
            raise ValueError("intent_id does not match position-action intent content")
        object.__setattr__(self, "intent_id", expected)
        return self
