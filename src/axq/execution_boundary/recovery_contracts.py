"""Immutable contracts for durable execution recovery and safe resume."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.execution_boundary.contracts import ExecutionIntent, ExecutionResult
from axq.runtime import (
    AccountState,
    BrokerConstraints,
    ExposureState,
    MarketState,
    OrderBookState,
    PositionBookState,
    SourceCursor,
)
from axq.runtime.state import UTCDateTime
from axq.versioning import canonical_hash


class RecoveryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class BrokerObjectKind(StrEnum):
    POSITION = "POSITION"
    ORDER = "ORDER"


class ReconciliationKind(StrEnum):
    MATCHED = "MATCHED"
    BROKER_ONLY = "BROKER_ONLY"
    LOCAL_ONLY = "LOCAL_ONLY"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"


class ResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class ResumeStatus(StrEnum):
    STARTING = "STARTING"
    RECONCILING = "RECONCILING"
    SAFE = "SAFE"
    BLOCKED = "BLOCKED"


class ResumeBlockReason(StrEnum):
    MARKET_NOT_FRESH = "MARKET_NOT_FRESH"
    ACCOUNT_NOT_FRESH = "ACCOUNT_NOT_FRESH"
    POSITIONS_NOT_FRESH = "POSITIONS_NOT_FRESH"
    ORDERS_NOT_FRESH = "ORDERS_NOT_FRESH"
    EXPOSURE_NOT_FRESH = "EXPOSURE_NOT_FRESH"
    BROKER_CONSTRAINTS_NOT_FRESH = "BROKER_CONSTRAINTS_NOT_FRESH"
    RECONCILIATION_INCOMPLETE = "RECONCILIATION_INCOMPLETE"
    UNRESOLVED_EXECUTION_ANOMALY = "UNRESOLVED_EXECUTION_ANOMALY"
    MISSING_INTRABAR_CONTINUITY = "MISSING_INTRABAR_CONTINUITY"
    THESIS_EXPIRED = "THESIS_EXPIRED"


class BrokerIntentLink(RecoveryModel):
    link_id: str = ""
    intent_id: str = Field(min_length=1)
    object_kind: BrokerObjectKind
    broker_object_id: str = Field(min_length=1)
    broker_ticket: int | None = Field(default=None, gt=0)
    transport_execution_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def bind_identity(self) -> BrokerIntentLink:
        if self.broker_ticket is None and self.transport_execution_id is None:
            raise ValueError("broker intent link requires exact persisted linkage")
        expected = f"bil-{canonical_hash(self.model_dump(mode='json', exclude={'link_id'}))[:20]}"
        if self.link_id and self.link_id != expected:
            raise ValueError("link_id does not match broker linkage content")
        object.__setattr__(self, "link_id", expected)
        return self


class BrokerRecoverySnapshot(RecoveryModel):
    snapshot_id: str = ""
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    as_of: UTCDateTime
    observed_at: UTCDateTime
    available_at: UTCDateTime
    account: AccountState
    market: MarketState
    positions: PositionBookState
    orders: OrderBookState
    exposure: ExposureState
    broker_constraints: BrokerConstraints
    intent_links: tuple[BrokerIntentLink, ...] = ()

    @model_validator(mode="after")
    def validate_and_bind(self) -> BrokerRecoverySnapshot:
        if not self.as_of <= self.observed_at <= self.available_at:
            raise ValueError("broker snapshot timestamps must be causally ordered")
        states = (
            self.account,
            self.market,
            self.positions,
            self.orders,
            self.exposure,
            self.broker_constraints,
        )
        if any(state.as_of > self.as_of for state in states):
            raise ValueError("broker snapshot contains future component state")
        object_ids = {item.position_id for item in self.positions.positions} | {
            item.order_id for item in self.orders.orders
        }
        if any(link.broker_object_id not in object_ids for link in self.intent_links):
            raise ValueError("broker intent link references an absent broker object")
        expected = (
            f"brs-{canonical_hash(self.model_dump(mode='json', exclude={'snapshot_id'}))[:20]}"
        )
        if self.snapshot_id and self.snapshot_id != expected:
            raise ValueError("snapshot_id does not match broker snapshot content")
        object.__setattr__(self, "snapshot_id", expected)
        return self


class ReconciliationFinding(RecoveryModel):
    finding_id: str = ""
    kind: ReconciliationKind
    status: ResolutionStatus
    intent_id: str | None = None
    broker_object_id: str | None = None
    broker_ticket: int | None = Field(default=None, gt=0)
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_and_bind(self) -> ReconciliationFinding:
        if self.kind is ReconciliationKind.MATCHED and self.status is not ResolutionStatus.RESOLVED:
            raise ValueError("matched finding must be resolved")
        if self.kind is not ReconciliationKind.MATCHED and self.status is ResolutionStatus.RESOLVED:
            raise ValueError("anomaly finding cannot silently resolve itself")
        expected = f"rf-{canonical_hash(self.model_dump(mode='json', exclude={'finding_id'}))[:20]}"
        if self.finding_id and self.finding_id != expected:
            raise ValueError("finding_id does not match finding content")
        object.__setattr__(self, "finding_id", expected)
        return self


class ReconciliationReport(RecoveryModel):
    report_id: str = ""
    snapshot_id: str = Field(min_length=1)
    as_of: UTCDateTime
    available_at: UTCDateTime
    status: ResolutionStatus
    findings: tuple[ReconciliationFinding, ...]
    supersedes_report_id: str | None = None

    @model_validator(mode="after")
    def validate_and_bind(self) -> ReconciliationReport:
        if self.available_at > self.as_of:
            raise ValueError("reconciliation cannot be available after as_of")
        expected_status = (
            ResolutionStatus.RESOLVED
            if all(item.status is ResolutionStatus.RESOLVED for item in self.findings)
            else ResolutionStatus.RECONCILIATION_REQUIRED
        )
        if self.status is not expected_status:
            raise ValueError("report status does not match findings")
        expected = f"rr-{canonical_hash(self.model_dump(mode='json', exclude={'report_id'}))[:20]}"
        if self.report_id and self.report_id != expected:
            raise ValueError("report_id does not match reconciliation content")
        object.__setattr__(self, "report_id", expected)
        return self


class ResumeReadiness(RecoveryModel):
    readiness_id: str = ""
    runtime_state_id: str = Field(min_length=1)
    reconciliation_report_id: str = Field(min_length=1)
    as_of: UTCDateTime
    status: ResumeStatus
    reason_codes: tuple[ResumeBlockReason, ...]

    @model_validator(mode="after")
    def validate_and_bind(self) -> ResumeReadiness:
        if self.status is ResumeStatus.SAFE and self.reason_codes:
            raise ValueError("safe readiness cannot contain block reasons")
        if self.status is ResumeStatus.BLOCKED and not self.reason_codes:
            raise ValueError("blocked readiness requires reasons")
        expected = (
            f"ready-{canonical_hash(self.model_dump(mode='json', exclude={'readiness_id'}))[:20]}"
        )
        if self.readiness_id and self.readiness_id != expected:
            raise ValueError("readiness_id does not match readiness content")
        object.__setattr__(self, "readiness_id", expected)
        return self


class RecoveryCheckpoint(RecoveryModel):
    checkpoint_id: str = ""
    runtime_state_id: str = Field(min_length=1)
    source_cursors: tuple[SourceCursor, ...]
    reconciliation_report_id: str | None = None
    readiness_id: str | None = None
    thesis_state_ids: tuple[str, ...]
    available_at: UTCDateTime

    @model_validator(mode="after")
    def bind_identity(self) -> RecoveryCheckpoint:
        expected = (
            f"rcp-{canonical_hash(self.model_dump(mode='json', exclude={'checkpoint_id'}))[:20]}"
        )
        if self.checkpoint_id and self.checkpoint_id != expected:
            raise ValueError("checkpoint_id does not match checkpoint content")
        object.__setattr__(self, "checkpoint_id", expected)
        return self


class ExecutionTransitionType(StrEnum):
    RESERVED = "RESERVED"
    RESULT_RECORDED = "RESULT_RECORDED"
    RECONCILIATION_RECORDED = "RECONCILIATION_RECORDED"


class ExecutionTransition(RecoveryModel):
    transition_id: str = ""
    transition_type: ExecutionTransitionType
    intent_id: str | None = None
    intent: ExecutionIntent | None = None
    result: ExecutionResult | None = None
    reconciliation: ReconciliationReport | None = None
    available_at: UTCDateTime

    @model_validator(mode="after")
    def validate_and_bind(self) -> ExecutionTransition:
        present = sum(item is not None for item in (self.intent, self.result, self.reconciliation))
        if present != 1:
            raise ValueError("transition requires exactly one semantic payload")
        expected_type = (
            ExecutionTransitionType.RESERVED
            if self.intent is not None
            else ExecutionTransitionType.RESULT_RECORDED
            if self.result is not None
            else ExecutionTransitionType.RECONCILIATION_RECORDED
        )
        if self.transition_type is not expected_type:
            raise ValueError("transition type does not match payload")
        payload_intent = (
            self.intent.intent_id
            if self.intent
            else (self.result.execution_intent_id if self.result else None)
        )
        if self.intent_id != payload_intent:
            raise ValueError("transition intent_id does not match payload")
        expected = (
            f"xt-{canonical_hash(self.model_dump(mode='json', exclude={'transition_id'}))[:20]}"
        )
        if self.transition_id and self.transition_id != expected:
            raise ValueError("transition_id does not match transition content")
        object.__setattr__(self, "transition_id", expected)
        return self
