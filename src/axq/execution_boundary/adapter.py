"""Demo-safe execution adapter boundary with explicit idempotency semantics."""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from axq.execution_boundary.contracts import (
    BrokerExecutionReport,
    ExecutionAccountMode,
    ExecutionIntent,
    ExecutionMode,
    ExecutionObservation,
    ExecutionPolicy,
    ExecutionReason,
    ExecutionResult,
    ExecutionResultStatus,
)
from axq.schemas import Signal


class TransportFailure(RuntimeError):
    """The transport failed before submission could be accepted."""


class UnknownSubmissionState(RuntimeError):
    """Submission may have reached the broker and requires reconciliation."""


class ExecutionAdapter(Protocol):
    def execute(self, intent: ExecutionIntent) -> ExecutionResult:
        """Process one immutable intent idempotently."""


class ExecutionTransport(Protocol):
    def submit(
        self, intent: ExecutionIntent, observation: ExecutionObservation
    ) -> BrokerExecutionReport:
        """Submit an already approved intent to the execution transport."""


class ExecutionLedger(Protocol):
    def get(self, intent_id: str) -> ExecutionResult | None: ...

    def is_reserved(self, intent_id: str) -> bool: ...

    def reserve(self, intent: ExecutionIntent) -> bool: ...

    def record(self, result: ExecutionResult) -> None: ...


class InMemoryExecutionLedger:
    """Tiny ledger reference implementation; persistent ports can implement the protocol."""

    def __init__(self) -> None:
        self._reserved: set[str] = set()
        self._results: dict[str, ExecutionResult] = {}

    def get(self, intent_id: str) -> ExecutionResult | None:
        return self._results.get(intent_id)

    def is_reserved(self, intent_id: str) -> bool:
        return intent_id in self._reserved

    def reserve(self, intent: ExecutionIntent) -> bool:
        if intent.intent_id in self._reserved:
            return False
        self._reserved.add(intent.intent_id)
        return True

    def record(self, result: ExecutionResult) -> None:
        if result.execution_intent_id not in self._reserved:
            raise ValueError("execution intent must be reserved before recording")
        previous = self._results.get(result.execution_intent_id)
        if previous is not None and previous != result:
            raise ValueError("execution intent already has a different result")
        self._results[result.execution_intent_id] = result


class DemoExecutionAdapter:
    """Guarded demo adapter; never permits a live-account submission."""

    def __init__(
        self,
        *,
        policy: ExecutionPolicy,
        ledger: ExecutionLedger,
        observation_provider: Callable[[ExecutionIntent], ExecutionObservation],
        transport: ExecutionTransport,
        preflight_validator: (
            Callable[[ExecutionIntent, ExecutionObservation], None] | None
        ) = None,
    ) -> None:
        self._policy = policy
        self._ledger = ledger
        self._observation_provider = observation_provider
        self._transport = transport
        self._preflight_validator = preflight_validator

    def execute(self, intent: ExecutionIntent) -> ExecutionResult:
        self._validate_policy_binding(intent)
        prior = self._ledger.get(intent.intent_id)
        if prior is not None:
            return prior
        if not self._ledger.reserve(intent):
            result = self._unknown_result(intent, "reserved intent requires reconciliation")
            self._ledger.record(result)
            return result

        if self._policy.mode is ExecutionMode.DISABLED:
            return self._record(
                self._known_result(
                    intent,
                    status=ExecutionResultStatus.NO_ACTION,
                    reason_code=ExecutionReason.EXECUTION_DISABLED,
                    reason=ExecutionReason.EXECUTION_DISABLED.value,
                    event_time=intent.available_at,
                )
            )

        try:
            observation = self._observation_provider(intent)
        except TransportFailure as exc:
            return self._record(self._failed_result(intent, str(exc), intent.available_at))

        preflight = self._preflight(intent, observation)
        if preflight is not None:
            return self._record(preflight)

        try:
            if self._preflight_validator is not None:
                self._preflight_validator(intent, observation)
        except TransportFailure as exc:
            return self._record(
                self._failed_result(intent, str(exc), observation.available_at, observation)
            )

        if self._policy.mode is ExecutionMode.DRY_RUN:
            return self._record(
                self._known_result(
                    intent,
                    status=ExecutionResultStatus.NO_ACTION,
                    reason_code=ExecutionReason.DRY_RUN,
                    reason=ExecutionReason.DRY_RUN.value,
                    event_time=observation.available_at,
                    observation=observation,
                )
            )

        try:
            report = self._transport.submit(intent, observation)
        except UnknownSubmissionState as exc:
            return self._record(self._unknown_result(intent, str(exc), observation=observation))
        except TransportFailure as exc:
            return self._record(
                self._failed_result(intent, str(exc), observation.available_at, observation)
            )

        result = self._result_from_report(intent, observation, report)
        return self._record(result)

    def _validate_policy_binding(self, intent: ExecutionIntent) -> None:
        if (
            intent.execution_policy_id != self._policy.policy_id
            or intent.execution_policy_version != self._policy.policy_version
            or intent.execution_mode is not self._policy.mode
        ):
            raise ValueError("execution intent is not bound to this adapter policy")

    def _preflight(
        self, intent: ExecutionIntent, observation: ExecutionObservation
    ) -> ExecutionResult | None:
        reason: ExecutionReason | None = None
        status = ExecutionResultStatus.REJECTED
        if observation.account_mode is ExecutionAccountMode.LIVE:
            reason = ExecutionReason.LIVE_ACCOUNT_BLOCKED
        elif observation.account_mode is ExecutionAccountMode.UNKNOWN:
            reason = ExecutionReason.UNKNOWN_ACCOUNT_MODE
        elif observation.broker_symbol != intent.broker_symbol:
            reason = ExecutionReason.SYMBOL_MISMATCH
        elif observation.available_at > intent.expires_at:
            reason = ExecutionReason.INTENT_EXPIRED
            status = ExecutionResultStatus.EXPIRED
        elif (
            observation.available_at - observation.observed_at
        ).total_seconds() > self._policy.max_observation_latency_seconds:
            reason = ExecutionReason.OBSERVATION_STALE
        elif observation.spread_points > self._policy.max_actual_spread_points:
            reason = ExecutionReason.SPREAD_LIMIT
        elif (
            observation.estimated_slippage_points
            > self._policy.max_pre_submit_slippage_points
        ):
            reason = ExecutionReason.SLIPPAGE_LIMIT
        else:
            deviation = (
                abs(observation.market_price - intent.requested_entry_price)
                / intent.point_size
            )
            if deviation > self._policy.max_price_deviation_points:
                reason = ExecutionReason.PRICE_DEVIATION_LIMIT
        if reason is None:
            return None
        return self._known_result(
            intent,
            status=status,
            reason_code=reason,
            reason=reason.value,
            event_time=observation.available_at,
            observation=observation,
        )

    def _result_from_report(
        self,
        intent: ExecutionIntent,
        observation: ExecutionObservation,
        report: BrokerExecutionReport,
    ) -> ExecutionResult:
        filled = report.filled_volume_lots
        if filled > intent.approved_volume_lots:
            return self._known_result(
                intent,
                status=ExecutionResultStatus.FAILED,
                reason_code=ExecutionReason.INVALID_BROKER_REPORT,
                reason="broker report exceeds approved volume",
                event_time=report.available_at,
                observation=observation,
            )
        remaining = round(max(0.0, intent.approved_volume_lots - filled), 10)
        if report.status is ExecutionResultStatus.PARTIALLY_FILLED and not (
            0.0 < filled < intent.approved_volume_lots
        ):
            return self._invalid_report(intent, observation, report)
        if report.status is ExecutionResultStatus.FILLED and not math.isclose(
            filled, intent.approved_volume_lots, abs_tol=1e-10
        ):
            return self._invalid_report(intent, observation, report)
        reason_code = {
            ExecutionResultStatus.REJECTED: ExecutionReason.BROKER_REJECTED,
            ExecutionResultStatus.CANCELLED: ExecutionReason.BROKER_CANCELLED,
            ExecutionResultStatus.EXPIRED: ExecutionReason.BROKER_EXPIRED,
            ExecutionResultStatus.FAILED: ExecutionReason.TRANSPORT_FAILED,
        }.get(report.status)
        slippage = None
        if report.fill_price is not None:
            delta = report.fill_price - intent.requested_entry_price
            if intent.direction is Signal.SELL:
                delta = -delta
            slippage = round(delta / intent.point_size, 10)
        return ExecutionResult.model_validate(
            self._provenance(intent)
            | {
                "status": report.status,
                "reason_code": reason_code,
                "reason": report.message if reason_code is not None else None,
                "requested_volume_lots": intent.approved_volume_lots,
                "filled_volume_lots": filled,
                "remaining_volume_lots": remaining,
                "requested_price": intent.requested_entry_price,
                "fill_price": report.fill_price,
                "actual_spread_points": observation.spread_points,
                "realized_slippage_points": slippage,
                "broker_ticket": report.broker_ticket,
                "transport_execution_id": report.transport_execution_id,
                "broker_retcode": report.broker_retcode,
                "broker_status": report.broker_status,
                "event_time": report.event_time,
                "observed_at": report.observed_at,
                "available_at": report.available_at,
            }
        )

    def _invalid_report(
        self,
        intent: ExecutionIntent,
        observation: ExecutionObservation,
        report: BrokerExecutionReport,
    ) -> ExecutionResult:
        return self._known_result(
            intent,
            status=ExecutionResultStatus.FAILED,
            reason_code=ExecutionReason.INVALID_BROKER_REPORT,
            reason="broker report status and fill volume are inconsistent",
            event_time=report.available_at,
            observation=observation,
        )

    def _failed_result(
        self,
        intent: ExecutionIntent,
        reason: str,
        event_time: datetime,
        observation: ExecutionObservation | None = None,
    ) -> ExecutionResult:
        return self._known_result(
            intent,
            status=ExecutionResultStatus.FAILED,
            reason_code=ExecutionReason.TRANSPORT_FAILED,
            reason=reason,
            event_time=event_time,
            observation=observation,
        )

    def _known_result(
        self,
        intent: ExecutionIntent,
        *,
        status: ExecutionResultStatus,
        reason_code: ExecutionReason,
        reason: str,
        event_time: datetime,
        observation: ExecutionObservation | None = None,
    ) -> ExecutionResult:
        return ExecutionResult.model_validate(
            self._provenance(intent)
            | {
                "status": status,
                "reason_code": reason_code,
                "reason": reason,
                "requested_volume_lots": intent.approved_volume_lots,
                "filled_volume_lots": 0.0,
                "remaining_volume_lots": intent.approved_volume_lots,
                "requested_price": intent.requested_entry_price,
                "actual_spread_points": (
                    observation.spread_points if observation else None
                ),
                "event_time": event_time,
                "observed_at": event_time,
                "available_at": event_time,
            }
        )

    def _unknown_result(
        self,
        intent: ExecutionIntent,
        reason: str,
        *,
        observation: ExecutionObservation | None = None,
    ) -> ExecutionResult:
        at = observation.available_at if observation else intent.available_at
        return ExecutionResult.model_validate(
            self._provenance(intent)
            | {
                "status": ExecutionResultStatus.UNKNOWN,
                "reason_code": ExecutionReason.UNKNOWN_SUBMISSION,
                "reason": reason,
                "requested_volume_lots": intent.approved_volume_lots,
                "filled_volume_lots": None,
                "remaining_volume_lots": None,
                "requested_price": intent.requested_entry_price,
                "actual_spread_points": (
                    observation.spread_points if observation else None
                ),
                "event_time": at,
                "observed_at": at,
                "available_at": at,
            }
        )

    @staticmethod
    def _provenance(intent: ExecutionIntent) -> dict[str, object]:
        return {
            "execution_intent_id": intent.intent_id,
            "evidence_bundle_id": intent.evidence_bundle_id,
            "master_proposal_id": intent.master_proposal_id,
            "discipline_outcome_id": intent.discipline_outcome_id,
            "risk_outcome_id": intent.risk_outcome_id,
            "setup_id": intent.setup_id,
            "thesis_id": intent.thesis_id,
            "scenario_id": intent.scenario_id,
            "symbol": intent.symbol,
            "direction": intent.direction,
        }

    def _record(self, result: ExecutionResult) -> ExecutionResult:
        self._ledger.record(result)
        return result
