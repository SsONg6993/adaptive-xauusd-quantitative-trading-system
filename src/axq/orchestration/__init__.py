"""Deterministic orchestration of existing Phase 6/7 runtime boundaries."""

from axq.mt5 import MetaTrader5Gateway
from axq.orchestration.config import RuntimeConfig, load_runtime_config
from axq.orchestration.contracts import (
    DecisionCycle,
    DecisionPlan,
    OperatorControls,
    OutcomeCount,
    RuntimeMode,
    RuntimeRunSummary,
    RuntimeStatus,
    StartupPhase,
)
from axq.orchestration.processor import (
    DeterministicDecisionProcessor,
    EntryDecisionInputs,
)
from axq.orchestration.service import RuntimeOrchestrator


def build_mt5_gateway(config: RuntimeConfig) -> MetaTrader5Gateway:
    """Build the lazy gateway; operational paths are not semantic identity."""
    return MetaTrader5Gateway(
        terminal_path=(str(config.mt5_terminal_path) if config.mt5_terminal_path else None)
    )


__all__ = [
    "DecisionCycle",
    "DecisionPlan",
    "DeterministicDecisionProcessor",
    "EntryDecisionInputs",
    "OperatorControls",
    "OutcomeCount",
    "RuntimeConfig",
    "RuntimeMode",
    "RuntimeOrchestrator",
    "RuntimeRunSummary",
    "RuntimeStatus",
    "StartupPhase",
    "build_mt5_gateway",
    "load_runtime_config",
]
