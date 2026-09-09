"""Strict contracts for deterministic management of already-open positions."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.agents import ContinuityStatus, HypothesisStatus, ThesisState
from axq.execution_boundary import (
    BrokerIntentLink,
    BrokerObjectKind,
    ExecutionIntent,
    ExecutionResult,
    ReconciliationReport,
    ResumeReadiness,
)
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ComponentFreshness,
    PositionSide,
    PositionState,
)
from axq.runtime.kernel import EvidenceBundle
from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.versioning import canonical_hash


class PositionManagementModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class PositionManagementResult(StrEnum):
    NO_ACTION = "NO_ACTION"
    HOLD_POSITION = "HOLD_POSITION"
    PROTECT_POSITION = "PROTECT_POSITION"
    EXIT_POSITION = "EXIT_POSITION"


class MissingEvidenceBehavior(StrEnum):
    NO_ACTION = "NO_ACTION"
    HOLD_POSITION = "HOLD_POSITION"


class PositionManagementReason(StrEnum):
    NO_OPEN_POSITION = "NO_OPEN_POSITION"
    THESIS_ACTIVE = "THESIS_ACTIVE"
    THESIS_CONFIRMED = "THESIS_CONFIRMED"
    THESIS_WEAKENING = "THESIS_WEAKENING"
    THESIS_INVALIDATED = "THESIS_INVALIDATED"
    THESIS_EXPIRED = "THESIS_EXPIRED"
    SCENARIO_INVALIDATED = "SCENARIO_INVALIDATED"
    MISSING_THESIS_LINKAGE = "MISSING_THESIS_LINKAGE"
    MISSING_SCENARIO_LINKAGE = "MISSING_SCENARIO_LINKAGE"
    MISSING_EXECUTION_PROVENANCE = "MISSING_EXECUTION_PROVENANCE"
    MISSING_EXACT_EXECUTION_LINKAGE = "MISSING_EXACT_EXECUTION_LINKAGE"
    EXECUTION_PROVENANCE_MISMATCH = "EXECUTION_PROVENANCE_MISMATCH"
    UNKNOWN_EXECUTION_STATE = "UNKNOWN_EXECUTION_STATE"
    RECONCILIATION_UNRESOLVED = "RECONCILIATION_UNRESOLVED"
    RUNTIME_NOT_SAFE = "RUNTIME_NOT_SAFE"
    ACCOUNT_STATE_NOT_FRESH = "ACCOUNT_STATE_NOT_FRESH"
    POSITION_STATE_NOT_FRESH = "POSITION_STATE_NOT_FRESH"
    BROKER_CONSTRAINTS_NOT_FRESH = "BROKER_CONSTRAINTS_NOT_FRESH"
    INTRABAR_CONTINUITY_MISSING = "INTRABAR_CONTINUITY_MISSING"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    POSITION_TOO_YOUNG_FOR_PROTECTION = "POSITION_TOO_YOUNG_FOR_PROTECTION"
    BREAK_EVEN_DISABLED = "BREAK_EVEN_DISABLED"
    CURRENT_PRICE_UNAVAILABLE = "CURRENT_PRICE_UNAVAILABLE"
    BROKER_PROTECTION_CONSTRAINT = "BROKER_PROTECTION_CONSTRAINT"
    ALREADY_PROTECTED = "ALREADY_PROTECTED"
    PROTECTION_NOT_RISK_REDUCING = "PROTECTION_NOT_RISK_REDUCING"
    BREAK_EVEN_PROTECTION = "BREAK_EVEN_PROTECTION"


class PositionManagementPolicy(PositionManagementModel):
    policy_id: str = ""
    policy_version: str = Field(min_length=1)
    exit_on_thesis_invalidated: bool = True
    exit_on_thesis_expired: bool = True
    exit_on_scenario_invalidated: bool = True
    protect_on_thesis_weakening: bool = True
    break_even_enabled: bool = True
    minimum_position_age_seconds: float = Field(ge=0.0)
    max_protective_sl_change_points: float = Field(gt=0.0)
    max_component_age_seconds: float = Field(gt=0.0)
    missing_evidence_behavior: MissingEvidenceBehavior

    @model_validator(mode="after")
    def bind_identity(self) -> PositionManagementPolicy:
        expected = f"pmp-{canonical_hash(self.model_dump(mode='json', exclude={'policy_id'}))[:20]}"
        if self.policy_id and self.policy_id != expected:
            raise ValueError("policy_id does not match position-management policy content")
        object.__setattr__(self, "policy_id", expected)
        return self


class PositionManagementContext(PositionManagementModel):
    context_id: str = ""
    runtime_state_id: str = Field(min_length=1)
    as_of: UTCDateTime
    available_at: UTCDateTime
    position: PositionState | None = None
    original_execution_intent: ExecutionIntent | None = None
    original_execution_result: ExecutionResult | None = None
    broker_intent_link: BrokerIntentLink | None = None
    thesis: ThesisState | None = None
    evidence_bundle: EvidenceBundle | None = None
    account: AccountState
    position_freshness: ComponentFreshness
    broker_constraints: BrokerConstraints
    reconciliation: ReconciliationReport
    resume_readiness: ResumeReadiness
    intrabar_continuity: ContinuityStatus
    unrealized_r_multiple: FiniteFloat | None = None
    mfe_points: FiniteFloat | None = Field(default=None, ge=0.0)
    mae_points: FiniteFloat | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PositionManagementContext:
        if self.available_at > self.as_of:
            raise ValueError("position-management context cannot be available after as_of")
        if self.account.as_of > self.as_of or self.broker_constraints.as_of > self.as_of:
            raise ValueError("position-management context cannot contain future state")
        for freshness in (
            self.account.freshness,
            self.position_freshness,
            self.broker_constraints.freshness,
        ):
            if freshness.available_at is not None and freshness.available_at > self.as_of:
                raise ValueError("position-management context cannot contain future availability")
        if self.reconciliation.as_of > self.as_of or self.reconciliation.available_at > self.as_of:
            raise ValueError("position-management context cannot contain future reconciliation")
        if self.resume_readiness.as_of > self.as_of:
            raise ValueError("position-management context cannot contain future readiness")
        if self.resume_readiness.runtime_state_id != self.runtime_state_id:
            raise ValueError("readiness references a different runtime state")
        if self.resume_readiness.reconciliation_report_id != self.reconciliation.report_id:
            raise ValueError("readiness references a different reconciliation report")

        provenance = (
            self.original_execution_intent,
            self.original_execution_result,
            self.broker_intent_link,
            self.thesis,
            self.evidence_bundle,
        )
        if self.position is None:
            if any(item is not None for item in provenance):
                raise ValueError("context without a position cannot contain position provenance")
        else:
            if self.position.opened_at > self.as_of:
                raise ValueError("position cannot open after context as_of")
            if self.position.symbol != self.broker_constraints.symbol:
                raise ValueError("position and broker symbols differ")
            self._validate_execution_provenance()
            self._validate_thesis_provenance()
            if self.evidence_bundle is not None:
                if self.evidence_bundle.runtime_state_id != self.runtime_state_id:
                    raise ValueError("evidence references a different runtime state")
                if self.evidence_bundle.as_of > self.as_of:
                    raise ValueError("context cannot contain future evidence")

        identity = self.model_dump(mode="json", exclude={"context_id"})
        expected = f"pmc-{canonical_hash(identity)[:20]}"
        if self.context_id and self.context_id != expected:
            raise ValueError("context_id does not match position-management context content")
        object.__setattr__(self, "context_id", expected)
        return self

    def _validate_execution_provenance(self) -> None:
        intent = self.original_execution_intent
        result = self.original_execution_result
        link = self.broker_intent_link
        position = self.position
        assert position is not None
        if intent is not None:
            if intent.symbol != position.symbol:
                raise ValueError("execution intent and position symbols differ")
            if intent.setup_id != position.setup_id:
                raise ValueError("execution intent and position setup linkage differ")
            if intent.thesis_id != position.thesis_id:
                raise ValueError("execution intent and position thesis linkage differ")
            expected_side = (
                PositionSide.BUY if intent.direction.value == "BUY" else PositionSide.SELL
            )
            if expected_side is not position.side:
                raise ValueError("execution intent and position directions differ")
        if result is not None and intent is not None:
            if result.execution_intent_id != intent.intent_id:
                raise ValueError("execution result references a different intent")
            if result.available_at > self.as_of:
                raise ValueError("context cannot contain a future execution result")
        if link is not None:
            if link.object_kind is not BrokerObjectKind.POSITION:
                raise ValueError("broker linkage must identify a position")
            if link.broker_object_id != position.position_id:
                raise ValueError("broker linkage references a different position")
            if intent is not None and link.intent_id != intent.intent_id:
                raise ValueError("broker linkage references a different execution intent")
            if (
                link.broker_ticket is not None
                and position.broker_ticket is not None
                and link.broker_ticket != position.broker_ticket
            ):
                raise ValueError("broker linkage ticket differs from position")

    def _validate_thesis_provenance(self) -> None:
        position = self.position
        thesis = self.thesis
        intent = self.original_execution_intent
        assert position is not None
        if thesis is None:
            return
        if thesis.thesis_id != position.thesis_id:
            raise ValueError("thesis does not belong to position")
        if thesis.updated_at > self.as_of or thesis.latest_evidence_available_at > self.as_of:
            raise ValueError("context cannot contain future thesis state")
        if intent is not None and intent.thesis_id != thesis.thesis_id:
            raise ValueError("execution intent and current thesis differ")
        if (
            intent is not None
            and intent.scenario_id is not None
            and not any(item.scenario_id == intent.scenario_id for item in thesis.scenarios)
        ):
            raise ValueError("execution scenario is absent from current thesis")


class PositionManagementOutcome(PositionManagementModel):
    outcome_id: str = ""
    policy_id: str = Field(min_length=1)
    position_management_context_id: str = Field(min_length=1)
    position_id: str | None = None
    original_execution_intent_id: str | None = None
    original_execution_result_id: str | None = None
    setup_id: str | None = None
    thesis_id: str | None = None
    scenario_id: str | None = None
    current_thesis_lifecycle: HypothesisStatus | None = None
    position_side: PositionSide | None = None
    entry_price: FiniteFloat | None = Field(default=None, gt=0.0)
    existing_stop_loss: FiniteFloat | None = Field(default=None, gt=0.0)
    result: PositionManagementResult
    reason_codes: tuple[PositionManagementReason, ...] = Field(min_length=1)
    eligible_for_position_action: bool
    requested_protective_stop_loss: FiniteFloat | None = Field(default=None, gt=0.0)
    as_of: UTCDateTime
    available_at: UTCDateTime
    rationale: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> PositionManagementOutcome:
        if self.available_at > self.as_of:
            raise ValueError("position-management outcome cannot be available after as_of")
        actionable = self.result in {
            PositionManagementResult.PROTECT_POSITION,
            PositionManagementResult.EXIT_POSITION,
        }
        if self.eligible_for_position_action != actionable:
            raise ValueError("only PROTECT_POSITION or EXIT_POSITION may request a position action")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("position-management reason codes must be unique")
        if self.result is PositionManagementResult.PROTECT_POSITION:
            self._validate_protection()
        elif self.requested_protective_stop_loss is not None:
            raise ValueError("only PROTECT_POSITION may request a protective stop")
        if actionable and any(
            value is None
            for value in (
                self.position_id,
                self.original_execution_intent_id,
                self.original_execution_result_id,
                self.setup_id,
                self.thesis_id,
                self.position_side,
                self.entry_price,
            )
        ):
            raise ValueError("position action requires complete position and execution provenance")
        identity = self.model_dump(mode="json", exclude={"outcome_id"})
        expected = f"pmo-{canonical_hash(identity)[:20]}"
        if self.outcome_id and self.outcome_id != expected:
            raise ValueError("outcome_id does not match position-management outcome content")
        object.__setattr__(self, "outcome_id", expected)
        return self

    def _validate_protection(self) -> None:
        if self.requested_protective_stop_loss is None or self.position_side is None:
            raise ValueError("PROTECT_POSITION requires a stop and position side")
        if self.existing_stop_loss is None:
            return
        increases_risk = (
            self.position_side is PositionSide.BUY
            and self.requested_protective_stop_loss < self.existing_stop_loss
        ) or (
            self.position_side is PositionSide.SELL
            and self.requested_protective_stop_loss > self.existing_stop_loss
        )
        if increases_risk and not math.isclose(
            self.requested_protective_stop_loss, self.existing_stop_loss, abs_tol=1e-10
        ):
            raise ValueError("protective stop cannot increase risk")
