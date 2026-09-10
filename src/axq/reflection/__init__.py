"""Deterministic Phase 8 reflection contracts and services."""

from axq.reflection.contracts import (
    DailyReflection,
    FindingCategory,
    FindingSignal,
    MetricFact,
    ReflectionFinding,
    ReflectionPolicy,
    SampleGuardRecord,
    SampleGuardStatus,
)
from axq.reflection.daily import build_daily_reflection
from axq.reflection.store import SQLiteReflectionStore
from axq.reflection.weekly import build_weekly_reflection
from axq.reflection.weekly_contracts import (
    FailurePattern,
    KnowledgeStatus,
    PatternMetricSummary,
    PatternSignalClass,
    PatternStatusTransition,
    PatternType,
    SuccessPattern,
    TransitionActionKind,
    WeeklyGuardKind,
    WeeklyReflection,
    WeeklyReflectionPolicy,
    WeeklySampleGuard,
)
from axq.reflection.weekly_store import SQLiteWeeklyReflectionStore

__all__ = [
    "DailyReflection",
    "FindingCategory",
    "FindingSignal",
    "MetricFact",
    "ReflectionFinding",
    "ReflectionPolicy",
    "SampleGuardRecord",
    "SampleGuardStatus",
    "build_daily_reflection",
    "SQLiteReflectionStore",
    "FailurePattern",
    "KnowledgeStatus",
    "PatternMetricSummary",
    "PatternSignalClass",
    "PatternStatusTransition",
    "PatternType",
    "SuccessPattern",
    "TransitionActionKind",
    "WeeklyGuardKind",
    "WeeklyReflection",
    "WeeklyReflectionPolicy",
    "WeeklySampleGuard",
    "build_weekly_reflection",
    "SQLiteWeeklyReflectionStore",
]
