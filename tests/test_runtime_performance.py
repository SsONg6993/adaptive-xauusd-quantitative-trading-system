from __future__ import annotations

from pathlib import Path

from axq.mt5.live_source import LiveSourcePerformance
from axq.orchestration.performance import (
    RuntimePerformanceSnapshot,
    RuntimePerformanceTracker,
    _memory_rss_bytes,
)
from axq.runtime.kernel import KernelPerformance


def test_idle_telemetry_preserves_latest_expensive_cycle(tmp_path: Path) -> None:
    path = tmp_path / "runtime-performance.json"
    tracker = RuntimePerformanceTracker(path)
    expensive = LiveSourcePerformance(
        poll_latency_ms=12.0,
        feature_latency_ms=8.0,
        m5_feature_latency_ms=5.0,
        m15_feature_latency_ms=3.0,
        expensive_cycle=True,
        m15_cache_hit=False,
    )

    first = tracker.record(
        source=expensive,
        cycle_latency_ms=4.0,
        scanner_latency_ms=0.5,
        kernel=KernelPerformance(
            tool_latency_ms=0.25,
            agent_latencies_ms=(("chart", 0.1), ("historical", 0.2)),
        ),
        master_latency_ms=0.3,
        discussion_latency_ms=0.4,
    )
    idle = tracker.record(source=LiveSourcePerformance(poll_latency_ms=0.7))

    persisted = RuntimePerformanceSnapshot.model_validate_json(
        path.read_text(encoding="utf-8")
    )
    assert first.expensive_cycle_count == 1
    assert idle.idle_poll_count == 1
    assert persisted.latest_poll_latency_ms == 0.7
    assert persisted.latest_cycle_latency_ms == 4.0
    assert persisted.historical_similarity_latency_ms == 0.2
    assert persisted.m15_cache_misses == 1
    assert persisted.llm_latency_ms is None
    assert persisted.last_expensive_computation_at is not None


def test_process_memory_telemetry_is_available() -> None:
    rss = _memory_rss_bytes()

    assert rss is not None
    assert rss > 0
