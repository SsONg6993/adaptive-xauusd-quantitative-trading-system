"""Optional read-only local operator dashboard."""

from axq.dashboard.contracts import (
    ComponentState,
    ComponentStatus,
    CurrentCycleView,
    DecisionExplanationView,
    PerformanceSnapshot,
    PipelineStageView,
    ReasoningAttemptView,
    ReasoningSnapshot,
    RuntimeActivityView,
    RuntimeComputeSnapshot,
    RuntimeObservabilitySnapshot,
    RuntimeSnapshot,
)
from axq.dashboard.mt5_reader import (
    LiveMT5Position,
    LiveMT5Snapshot,
    MetaTrader5ReadOnlyAdapter,
    read_live_mt5_snapshot,
)
from axq.dashboard.readers import (
    load_performance_snapshot,
    load_reasoning_snapshot,
    load_runtime_observability,
    load_runtime_performance,
    load_runtime_snapshot,
    read_ollama_status,
)

__all__ = [
    "ComponentState",
    "ComponentStatus",
    "CurrentCycleView",
    "DecisionExplanationView",
    "PerformanceSnapshot",
    "PipelineStageView",
    "ReasoningAttemptView",
    "ReasoningSnapshot",
    "RuntimeSnapshot",
    "RuntimeActivityView",
    "RuntimeComputeSnapshot",
    "RuntimeObservabilitySnapshot",
    "LiveMT5Position",
    "LiveMT5Snapshot",
    "MetaTrader5ReadOnlyAdapter",
    "load_performance_snapshot",
    "load_reasoning_snapshot",
    "load_runtime_observability",
    "load_runtime_performance",
    "load_runtime_snapshot",
    "read_ollama_status",
    "read_live_mt5_snapshot",
]
