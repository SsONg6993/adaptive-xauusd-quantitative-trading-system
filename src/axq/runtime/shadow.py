"""Immutable semantic records for the deterministic live shadow funnel."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from axq.runtime.state import FiniteFloat, UTCDateTime
from axq.tools.contracts import FactScalar
from axq.versioning import canonical_hash


class ShadowModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"


class CandidateResult(StrEnum):
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"
    UNAVAILABLE = "UNAVAILABLE"
    NO_SETUP = "NO_SETUP"
    CANDIDATE = "CANDIDATE"
    CANDIDATE_CONFLICTED = "CANDIDATE_CONFLICTED"


class CandidateDirection(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    CONFLICTED = "CONFLICTED"


class LiveMarketStatus(StrEnum):
    BAR_READY = "BAR_READY"
    WAITING_FOR_NEXT_M5 = "WAITING_FOR_NEXT_M5"
    STALE_QUOTE = "STALE_QUOTE"
    UNAVAILABLE = "UNAVAILABLE"


class ShadowMarketAvailability(ShadowModel):
    availability_id: str = ""
    canonical_instrument: Literal["XAUUSD"] = "XAUUSD"
    resolved_broker_symbol: str = Field(min_length=1)
    instrument_resolution_id: str = Field(min_length=1)
    time_offset_resolution_id: str | None = None
    observed_at: UTCDateTime
    available_at: UTCDateTime
    raw_broker_tick_at: UTCDateTime | None = None
    broker_tick_at: UTCDateTime | None = None
    latest_completed_m5_at: UTCDateTime | None = None
    status: LiveMarketStatus
    reason_code: str = Field(min_length=1)

    @model_validator(mode="after")
    def bind_identity(self) -> ShadowMarketAvailability:
        identity = self.model_dump(mode="json", exclude={"availability_id"})
        expected = f"sma-{canonical_hash(identity)[:20]}"
        if self.availability_id and self.availability_id != expected:
            raise ValueError("availability_id does not match market availability content")
        object.__setattr__(self, "availability_id", expected)
        return self


class M15Structure(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class M15Regime(StrEnum):
    BREAKOUT = "BREAKOUT"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    TRANSITION = "TRANSITION"


class ScanReason(StrEnum):
    OUTSIDE_ACTIVE_WINDOW = "OUTSIDE_ACTIVE_WINDOW"
    SYMBOL_MISMATCH = "SYMBOL_MISMATCH"
    M5_NOT_COMPLETED = "M5_NOT_COMPLETED"
    M15_CONTEXT_NOT_COMPLETED = "M15_CONTEXT_NOT_COMPLETED"
    FEATURE_MANIFEST_MISMATCH = "FEATURE_MANIFEST_MISMATCH"
    REQUIRED_FEATURE_UNAVAILABLE = "REQUIRED_FEATURE_UNAVAILABLE"
    NO_DIRECTIONAL_ACTIVATION = "NO_DIRECTIONAL_ACTIVATION"
    M5_BULLISH_STRUCTURE_ACTIVATION = "M5_BULLISH_STRUCTURE_ACTIVATION"
    M5_BEARISH_STRUCTURE_ACTIVATION = "M5_BEARISH_STRUCTURE_ACTIVATION"
    M5_BULLISH_BREAKOUT_ACTIVATION = "M5_BULLISH_BREAKOUT_ACTIVATION"
    M5_BEARISH_BREAKOUT_ACTIVATION = "M5_BEARISH_BREAKOUT_ACTIVATION"
    M5_BULLISH_QUANT_ACTIVATION = "M5_BULLISH_QUANT_ACTIVATION"
    M5_BEARISH_QUANT_ACTIVATION = "M5_BEARISH_QUANT_ACTIVATION"
    M15_CONTEXT_SUPPORTS = "M15_CONTEXT_SUPPORTS"
    M15_CONTEXT_OPPOSES = "M15_CONTEXT_OPPOSES"
    M15_CONTEXT_NEUTRAL = "M15_CONTEXT_NEUTRAL"
    BIDIRECTIONAL_ACTIVATION = "BIDIRECTIONAL_ACTIVATION"


class ScanFeatureReference(ShadowModel):
    feature_name: str = Field(min_length=1)
    timeframe: Literal["M5", "M15"]
    value: FactScalar
    feature_snapshot_id: str = Field(min_length=1)
    feature_manifest_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    available_at: UTCDateTime


class M15ContextSnapshot(ShadowModel):
    context_id: str = ""
    event_id: str = Field(min_length=1)
    feature_snapshot_id: str = Field(min_length=1)
    feature_manifest_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    canonical_instrument: Literal["XAUUSD"]
    resolved_broker_symbol: str = Field(min_length=1)
    instrument_resolution_id: str = Field(min_length=1)
    as_of: UTCDateTime
    available_at: UTCDateTime
    structure: M15Structure
    regime: M15Regime
    facts: tuple[ScanFeatureReference, ...]

    @model_validator(mode="after")
    def bind_identity(self) -> M15ContextSnapshot:
        if self.symbol != self.canonical_instrument:
            raise ValueError("symbol must match canonical instrument")
        identity = self.model_dump(mode="json", exclude={"context_id"})
        expected = f"m15ctx-{canonical_hash(identity)[:20]}"
        if self.context_id and self.context_id != expected:
            raise ValueError("context_id does not match M15 context content")
        object.__setattr__(self, "context_id", expected)
        return self


class M5CandidateScan(ShadowModel):
    scan_id: str = ""
    event_id: str = Field(min_length=1)
    feature_snapshot_id: str | None = None
    m15_context_id: str | None = None
    symbol: str = Field(min_length=1)
    canonical_instrument: Literal["XAUUSD"]
    resolved_broker_symbol: str = Field(min_length=1)
    instrument_resolution_id: str = Field(min_length=1)
    as_of: UTCDateTime
    available_at: UTCDateTime
    result: CandidateResult
    direction: CandidateDirection | None = None
    reason_codes: tuple[ScanReason, ...] = Field(min_length=1)
    triggers: tuple[ScanFeatureReference, ...] = ()
    missing_features: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> M5CandidateScan:
        if self.symbol != self.canonical_instrument:
            raise ValueError("symbol must match canonical instrument")
        candidate = self.result in {
            CandidateResult.CANDIDATE,
            CandidateResult.CANDIDATE_CONFLICTED,
        }
        if candidate != (self.direction is not None):
            raise ValueError("candidate direction must exist exactly for candidate results")
        if self.result is CandidateResult.CANDIDATE_CONFLICTED and (
            self.direction is not CandidateDirection.CONFLICTED
        ):
            raise ValueError("conflicted result requires conflicted direction")
        if tuple(sorted(self.missing_features)) != self.missing_features:
            raise ValueError("missing features must use canonical order")
        if tuple(sorted(self.triggers, key=lambda item: item.feature_name)) != self.triggers:
            raise ValueError("scan triggers must use canonical feature order")
        identity = self.model_dump(mode="json", exclude={"scan_id"})
        expected = f"scan-{canonical_hash(identity)[:20]}"
        if self.scan_id and self.scan_id != expected:
            raise ValueError("scan_id does not match scan content")
        object.__setattr__(self, "scan_id", expected)
        return self


class PlanFieldStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class HypotheticalPlanField(ShadowModel):
    status: PlanFieldStatus
    value: FiniteFloat | None = None
    reason: str = Field(min_length=1, max_length=300)
    provenance_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_availability(self) -> HypotheticalPlanField:
        if (self.status is PlanFieldStatus.AVAILABLE) != (self.value is not None):
            raise ValueError(
                "available plan fields require a value and unavailable fields forbid it"
            )
        return self


class HypotheticalTradePlan(ShadowModel):
    plan_id: str = ""
    event_id: str = Field(min_length=1)
    scan_id: str = Field(min_length=1)
    execution_intent_id: str = Field(min_length=1)
    master_proposal_id: str = Field(min_length=1)
    discipline_outcome_id: str = Field(min_length=1)
    risk_outcome_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    canonical_instrument: Literal["XAUUSD"]
    resolved_broker_symbol: str = Field(min_length=1)
    instrument_resolution_id: str = Field(min_length=1)
    direction: Literal["BUY", "SELL"]
    as_of: UTCDateTime
    confidence: HypotheticalPlanField
    entry: HypotheticalPlanField
    stop_loss: HypotheticalPlanField
    take_profit: HypotheticalPlanField
    position_size: HypotheticalPlanField
    risk_reward: HypotheticalPlanField

    @model_validator(mode="after")
    def bind_identity(self) -> HypotheticalTradePlan:
        if self.symbol != self.canonical_instrument:
            raise ValueError("symbol must match canonical instrument")
        identity = self.model_dump(mode="json", exclude={"plan_id"})
        expected = f"stp-{canonical_hash(identity)[:20]}"
        if self.plan_id and self.plan_id != expected:
            raise ValueError("plan_id does not match trade plan content")
        object.__setattr__(self, "plan_id", expected)
        return self


class ShadowExecutionRecord(ShadowModel):
    record_id: str = ""
    event_id: str = Field(min_length=1)
    scan_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    execution_intent_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    canonical_instrument: Literal["XAUUSD"]
    resolved_broker_symbol: str = Field(min_length=1)
    instrument_resolution_id: str = Field(min_length=1)
    direction: Literal["BUY", "SELL"]
    as_of: UTCDateTime
    action: Literal["WOULD_SUBMIT"] = "WOULD_SUBMIT"
    broker_mutation: Literal[False] = False

    @model_validator(mode="after")
    def bind_identity(self) -> ShadowExecutionRecord:
        if self.symbol != self.canonical_instrument:
            raise ValueError("symbol must match canonical instrument")
        identity = self.model_dump(mode="json", exclude={"record_id"})
        expected = f"sx-{canonical_hash(identity)[:20]}"
        if self.record_id and self.record_id != expected:
            raise ValueError("record_id does not match shadow execution content")
        object.__setattr__(self, "record_id", expected)
        return self


class ShadowCycleStage(StrEnum):
    QUIET = "QUIET"
    SETUP_DETECTED = "SETUP_DETECTED"
    HOLD = "HOLD"
    TRADE_PLAN = "TRADE_PLAN"


class ShadowRuntimeCycle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["2.0"] = "2.0"
    cycle_id: str = ""
    event_id: str = Field(min_length=1)
    scan_id: str = Field(min_length=1)
    m15_context_id: str | None = None
    canonical_instrument: Literal["XAUUSD"]
    resolved_broker_symbol: str = Field(min_length=1)
    instrument_resolution_id: str = Field(min_length=1)
    stage: ShadowCycleStage
    as_of: UTCDateTime
    evidence_bundle_id: str | None = None
    master_proposal_id: str | None = None
    discipline_outcome_id: str | None = None
    risk_outcome_id: str | None = None
    execution_intent_id: str | None = None
    trade_plan_id: str | None = None
    shadow_execution_id: str | None = None
    interaction_resolution_id: str | None = None

    @classmethod
    def from_scan(cls, scan: M5CandidateScan) -> ShadowRuntimeCycle:
        if scan.result not in {
            CandidateResult.OUTSIDE_WINDOW,
            CandidateResult.UNAVAILABLE,
            CandidateResult.NO_SETUP,
        }:
            raise ValueError("candidate scan requires downstream cycle construction")
        return cls(
            event_id=scan.event_id,
            scan_id=scan.scan_id,
            m15_context_id=scan.m15_context_id,
            canonical_instrument=scan.canonical_instrument,
            resolved_broker_symbol=scan.resolved_broker_symbol,
            instrument_resolution_id=scan.instrument_resolution_id,
            stage=ShadowCycleStage.QUIET,
            as_of=scan.as_of,
        )

    @model_validator(mode="after")
    def validate_and_bind_identity(self) -> ShadowRuntimeCycle:
        downstream = (
            self.evidence_bundle_id,
            self.master_proposal_id,
            self.discipline_outcome_id,
            self.risk_outcome_id,
            self.execution_intent_id,
            self.trade_plan_id,
            self.shadow_execution_id,
            self.interaction_resolution_id,
        )
        if self.stage is ShadowCycleStage.QUIET and any(downstream):
            raise ValueError("quiet cycle cannot contain agent or trade references")
        identity = self.model_dump(mode="json", exclude={"cycle_id"})
        expected = f"scycle-{canonical_hash(identity)[:20]}"
        if self.cycle_id and self.cycle_id != expected:
            raise ValueError("cycle_id does not match shadow cycle content")
        object.__setattr__(self, "cycle_id", expected)
        return self


__all__ = [
    "CandidateDirection",
    "CandidateResult",
    "HypotheticalPlanField",
    "LiveMarketStatus",
    "HypotheticalTradePlan",
    "M15ContextSnapshot",
    "M15Regime",
    "M15Structure",
    "M5CandidateScan",
    "PlanFieldStatus",
    "ScanFeatureReference",
    "ScanReason",
    "ShadowExecutionRecord",
    "ShadowMarketAvailability",
    "ShadowCycleStage",
    "ShadowRuntimeCycle",
]
