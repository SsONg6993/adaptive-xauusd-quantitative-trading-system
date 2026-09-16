"""Lightweight operational performance telemetry outside semantic decision identity."""

from __future__ import annotations

import ctypes
import json
import os
import time
from ctypes import wintypes
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from axq.mt5.live_source import LiveSourcePerformance
from axq.runtime.kernel import KernelPerformance


class RuntimePerformanceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    observed_at: datetime
    poll_count: int = Field(ge=0)
    idle_poll_count: int = Field(ge=0)
    expensive_cycle_count: int = Field(ge=0)
    latest_poll_latency_ms: float = Field(ge=0.0)
    latest_cycle_latency_ms: float | None = Field(default=None, ge=0.0)
    scanner_latency_ms: float | None = Field(default=None, ge=0.0)
    feature_latency_ms: float | None = Field(default=None, ge=0.0)
    m5_feature_latency_ms: float | None = Field(default=None, ge=0.0)
    m15_feature_latency_ms: float | None = Field(default=None, ge=0.0)
    tool_latency_ms: float | None = Field(default=None, ge=0.0)
    agent_latencies_ms: dict[str, float] = Field(default_factory=dict)
    historical_similarity_latency_ms: float | None = Field(default=None, ge=0.0)
    llm_latency_ms: float | None = Field(default=None, ge=0.0)
    master_latency_ms: float | None = Field(default=None, ge=0.0)
    discussion_latency_ms: float | None = Field(default=None, ge=0.0)
    m15_cache_hits: int = Field(ge=0)
    m15_cache_misses: int = Field(ge=0)
    cpu_percent: float | None = Field(default=None, ge=0.0)
    memory_rss_bytes: int | None = Field(default=None, ge=0)
    last_expensive_computation_at: datetime | None = None


def _memory_rss_bytes() -> int | None:
    if os.name != "nt":
        try:
            statm = Path("/proc/self/statm").read_text(encoding="ascii").split()
            sysconf = getattr(os, "sysconf")  # noqa: B009 - absent from Windows stubs
            page_size = int(sysconf("SC_PAGE_SIZE"))
            return int(statm[1]) * page_size
        except (OSError, ValueError, IndexError):
            return None

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        process = kernel32.GetCurrentProcess()
        success = psapi.GetProcessMemoryInfo(
            process,
            ctypes.byref(counters),
            counters.cb,
        )
    except (AttributeError, OSError):
        return None
    return int(counters.WorkingSetSize) if success else None


class RuntimePerformanceTracker:
    """Accumulate small process-local counters and replace one JSON snapshot."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._poll_count = 0
        self._idle_poll_count = 0
        self._expensive_cycle_count = 0
        self._m15_cache_hits = 0
        self._m15_cache_misses = 0
        self._last_wall = time.monotonic()
        self._last_cpu = time.process_time()
        self._latest_cycle: dict[str, object] = {}
        self._last_expensive_at: datetime | None = None

    def record(
        self,
        *,
        source: LiveSourcePerformance,
        cycle_latency_ms: float | None = None,
        scanner_latency_ms: float | None = None,
        kernel: KernelPerformance | None = None,
        master_latency_ms: float | None = None,
        discussion_latency_ms: float | None = None,
    ) -> RuntimePerformanceSnapshot:
        self._poll_count += 1
        now = datetime.now(UTC)
        if source.expensive_cycle:
            self._expensive_cycle_count += 1
            self._last_expensive_at = now
            if source.m15_cache_hit is True:
                self._m15_cache_hits += 1
            elif source.m15_cache_hit is False:
                self._m15_cache_misses += 1
            self._latest_cycle = {
                "latest_cycle_latency_ms": cycle_latency_ms,
                "scanner_latency_ms": scanner_latency_ms,
                "feature_latency_ms": source.feature_latency_ms,
                "m5_feature_latency_ms": source.m5_feature_latency_ms,
                "m15_feature_latency_ms": source.m15_feature_latency_ms,
                "tool_latency_ms": None if kernel is None else kernel.tool_latency_ms,
                "agent_latencies_ms": ({} if kernel is None else dict(kernel.agent_latencies_ms)),
                "historical_similarity_latency_ms": (
                    None if kernel is None else kernel.historical_similarity_latency_ms
                ),
                "master_latency_ms": master_latency_ms,
                "discussion_latency_ms": discussion_latency_ms,
            }
        else:
            self._idle_poll_count += 1

        wall = time.monotonic()
        cpu = time.process_time()
        wall_delta = wall - self._last_wall
        cpu_percent = (
            None if wall_delta <= 0.0 else max(0.0, (cpu - self._last_cpu) / wall_delta * 100.0)
        )
        self._last_wall = wall
        self._last_cpu = cpu
        snapshot = RuntimePerformanceSnapshot.model_validate(
            {
                "observed_at": now,
                "poll_count": self._poll_count,
                "idle_poll_count": self._idle_poll_count,
                "expensive_cycle_count": self._expensive_cycle_count,
                "latest_poll_latency_ms": source.poll_latency_ms,
                "m15_cache_hits": self._m15_cache_hits,
                "m15_cache_misses": self._m15_cache_misses,
                "cpu_percent": cpu_percent,
                "memory_rss_bytes": _memory_rss_bytes(),
                "last_expensive_computation_at": self._last_expensive_at,
                **self._latest_cycle,
            }
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(self._path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(snapshot.model_dump(mode="json"), sort_keys=True, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self._path)
        return snapshot


__all__ = ["RuntimePerformanceSnapshot", "RuntimePerformanceTracker"]
