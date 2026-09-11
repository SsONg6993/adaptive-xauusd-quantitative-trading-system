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
from axq.reflection.proposal_contracts import (
    ImprovementProposal,
    ImprovementProposalPolicy,
    ProposalEvidenceGuard,
    ProposalGuardKind,
    ProposalStatus,
    ProposalStatusTransition,
    ProposalTargetComponent,
)
from axq.reflection.proposal_store import SQLiteImprovementProposalStore
from axq.reflection.proposals import (
    ProposalBuildResult,
    ProposalEligibilityAssessment,
    build_improvement_proposals,
)
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
    "ImprovementProposal",
    "ImprovementProposalPolicy",
    "ProposalEvidenceGuard",
    "ProposalGuardKind",
    "ProposalStatus",
    "ProposalStatusTransition",
    "ProposalTargetComponent",
    "SQLiteImprovementProposalStore",
    "ProposalBuildResult",
    "ProposalEligibilityAssessment",
    "build_improvement_proposals",
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
