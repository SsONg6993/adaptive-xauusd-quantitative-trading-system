"""Pure fail-closed startup readiness evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from axq.agents import ContinuityStatus
from axq.execution_boundary.recovery_contracts import (
    ReconciliationReport,
    ResolutionStatus,
    ResumeBlockReason,
    ResumeReadiness,
    ResumeStatus,
)
from axq.runtime import ComponentFreshness, FreshnessStatus, SharedRuntimeState


class RecoveryThesis(Protocol):
    continuity_status: ContinuityStatus
    expires_at: datetime


def evaluate_resume_readiness(
    runtime_state: SharedRuntimeState,
    reconciliation: ReconciliationReport,
    theses: Sequence[RecoveryThesis],
    *,
    as_of: datetime,
    continuity_status: ContinuityStatus = ContinuityStatus.COMPLETE,
) -> ResumeReadiness:
    reasons: list[ResumeBlockReason] = []
    checks = (
        (runtime_state.market.freshness, ResumeBlockReason.MARKET_NOT_FRESH),
        (runtime_state.account.freshness, ResumeBlockReason.ACCOUNT_NOT_FRESH),
        (runtime_state.positions.freshness, ResumeBlockReason.POSITIONS_NOT_FRESH),
        (runtime_state.orders.freshness, ResumeBlockReason.ORDERS_NOT_FRESH),
        (runtime_state.exposure.freshness, ResumeBlockReason.EXPOSURE_NOT_FRESH),
        (
            runtime_state.broker_constraints.freshness,
            ResumeBlockReason.BROKER_CONSTRAINTS_NOT_FRESH,
        ),
    )
    reasons.extend(reason for freshness, reason in checks if not _is_fresh(freshness, as_of))
    if reconciliation.status is ResolutionStatus.RECONCILIATION_REQUIRED:
        reasons.append(ResumeBlockReason.UNRESOLVED_EXECUTION_ANOMALY)
    if continuity_status is not ContinuityStatus.COMPLETE or any(
        thesis.continuity_status is not ContinuityStatus.COMPLETE for thesis in theses
    ):
        reasons.append(ResumeBlockReason.MISSING_INTRABAR_CONTINUITY)
    if any(as_of >= thesis.expires_at for thesis in theses):
        reasons.append(ResumeBlockReason.THESIS_EXPIRED)
    ordered = tuple(dict.fromkeys(reasons))
    return ResumeReadiness(
        runtime_state_id=runtime_state.state_id,
        reconciliation_report_id=reconciliation.report_id,
        as_of=as_of,
        status=ResumeStatus.BLOCKED if ordered else ResumeStatus.SAFE,
        reason_codes=ordered,
    )


def _is_fresh(freshness: ComponentFreshness, as_of: datetime) -> bool:
    if freshness.status is not FreshnessStatus.AVAILABLE:
        return False
    if freshness.available_at is None or freshness.stale_after_ms is None:
        return False
    age_ms = (as_of - freshness.available_at).total_seconds() * 1_000
    return 0 <= age_ms <= freshness.stale_after_ms
