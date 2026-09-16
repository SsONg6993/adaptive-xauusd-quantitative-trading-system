"""Deterministic position-management decisions without broker authority."""

from axq.position_management.contracts import (
    MissingEvidenceBehavior,
    PositionManagementContext,
    PositionManagementOutcome,
    PositionManagementPolicy,
    PositionManagementReason,
    PositionManagementResult,
)
from axq.position_management.evaluator import (
    default_demo_position_management_policy,
    evaluate_position,
)

__all__ = [
    "MissingEvidenceBehavior",
    "PositionManagementContext",
    "PositionManagementOutcome",
    "PositionManagementPolicy",
    "PositionManagementReason",
    "PositionManagementResult",
    "default_demo_position_management_policy",
    "evaluate_position",
]
