"""Optional read-only local operator dashboard."""

from axq.dashboard.contracts import (
    ComponentState,
    ComponentStatus,
    PerformanceSnapshot,
    ReasoningAttemptView,
    ReasoningSnapshot,
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
    load_runtime_snapshot,
    read_ollama_status,
)

__all__ = [
    "ComponentState",
    "ComponentStatus",
    "PerformanceSnapshot",
    "ReasoningAttemptView",
    "ReasoningSnapshot",
    "RuntimeSnapshot",
    "LiveMT5Position",
    "LiveMT5Snapshot",
    "MetaTrader5ReadOnlyAdapter",
    "load_performance_snapshot",
    "load_reasoning_snapshot",
    "load_runtime_snapshot",
    "read_ollama_status",
    "read_live_mt5_snapshot",
]
