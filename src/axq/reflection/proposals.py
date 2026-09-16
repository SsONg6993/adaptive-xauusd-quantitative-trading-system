"""Pure deterministic construction of advisory improvement proposals."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import cast

from pydantic import Field, model_validator

from axq.experience import Experience
from axq.reflection.contracts import (
    DailyReflection,
    FindingCategory,
    ReflectionFinding,
    ReflectionModel,
    SampleGuardStatus,
)
from axq.reflection.proposal_contracts import (
    ImprovementProposal,
    ImprovementProposalPolicy,
    ProposalEvidenceGuard,
    ProposalGuardKind,
    ProposalTargetComponent,
)
from axq.reflection.weekly_contracts import (
    KnowledgeStatus,
    Pattern,
    PatternType,
    WeeklyGuardKind,
    WeeklyReflection,
    WeeklySampleGuard,
)
from axq.versioning import canonical_hash

_ACTIVE_PATTERN_STATUSES = frozenset(
    {
        KnowledgeStatus.OBSERVATION,
        KnowledgeStatus.HYPOTHESIS,
        KnowledgeStatus.CANDIDATE,
        KnowledgeStatus.VALIDATED,
    }
)

_TARGETS: dict[FindingCategory, ProposalTargetComponent] = {
    FindingCategory.DIRECTION_OUTCOME: ProposalTargetComponent.MASTER_FUSION,
    FindingCategory.SESSION_OUTCOME: ProposalTargetComponent.MASTER_FUSION,
    FindingCategory.REGIME_OUTCOME: ProposalTargetComponent.MASTER_FUSION,
    FindingCategory.CONFIDENCE_CALIBRATION: ProposalTargetComponent.MASTER_FUSION,
    FindingCategory.EXCURSION_IMBALANCE: ProposalTargetComponent.RISK_BOUNDARY,
    FindingCategory.REJECTION_ANOMALY: ProposalTargetComponent.DISCIPLINE_GUARD,
    FindingCategory.AGENT_RELIABILITY: ProposalTargetComponent.SPECIALIST_AGENT,
    FindingCategory.POSITION_MANAGEMENT_ANOMALY: ProposalTargetComponent.POSITION_MANAGEMENT,
    FindingCategory.RUNTIME_ANOMALY: ProposalTargetComponent.RUNTIME_ORCHESTRATION,
}


class ProposalEligibilityAssessment(ReflectionModel):
    assessment_id: str = ""
    pattern_key: str = Field(min_length=1)
    status: SampleGuardStatus
    observed_complete_weeks: int = Field(ge=0)
    required_complete_weeks: int = Field(ge=2)
    reason_codes: tuple[str, ...] = ()
    supporting_pattern_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def normalize_and_bind_identity(self) -> ProposalEligibilityAssessment:
        object.__setattr__(self, "reason_codes", tuple(sorted(set(self.reason_codes))))
        object.__setattr__(
            self,
            "supporting_pattern_ids",
            tuple(sorted(set(self.supporting_pattern_ids))),
        )
        if self.status is SampleGuardStatus.PASSED and self.reason_codes:
            raise ValueError("eligible assessment cannot contain rejection reasons")
        identity = self.model_dump(mode="json", exclude={"assessment_id"})
        expected = f"proposal-assessment-{canonical_hash(identity)[:20]}"
        if self.assessment_id and self.assessment_id != expected:
            raise ValueError("assessment_id does not match eligibility content")
        object.__setattr__(self, "assessment_id", expected)
        return self


class ProposalBuildResult(ReflectionModel):
    proposals: tuple[ImprovementProposal, ...] = ()
    assessments: tuple[ProposalEligibilityAssessment, ...] = ()

    @property
    def assessed_pattern_keys(self) -> int:
        return len(self.assessments)

    @property
    def eligible_pattern_keys(self) -> int:
        return sum(item.status is SampleGuardStatus.PASSED for item in self.assessments)

    @property
    def insufficient_pattern_keys(self) -> int:
        return sum(item.status is not SampleGuardStatus.PASSED for item in self.assessments)


def _index_unique[T](items: Iterable[T], attribute: str, kind: str) -> dict[str, T]:
    indexed: dict[str, T] = {}
    for item in items:
        semantic_id = str(getattr(item, attribute))
        if semantic_id in indexed:
            raise ValueError(f"duplicate {kind} identity")
        indexed[semantic_id] = item
    return indexed


def _terminal_weekly(reflections: Sequence[WeeklyReflection]) -> tuple[WeeklyReflection, ...]:
    grouped: dict[tuple[datetime, str], list[WeeklyReflection]] = defaultdict(list)
    for reflection in reflections:
        grouped[(reflection.week_start, reflection.weekly_policy_id)].append(reflection)
    selected: list[WeeklyReflection] = []
    for records in grouped.values():
        by_id = {item.reflection_id: item for item in records}
        if len(by_id) != len(records):
            raise ValueError("duplicate WeeklyReflection identity")
        children: dict[str, list[str]] = defaultdict(list)
        roots: list[WeeklyReflection] = []
        for record in records:
            predecessor = record.supersedes_weekly_reflection_id
            if predecessor is None:
                roots.append(record)
            else:
                if predecessor not in by_id:
                    raise ValueError("missing weekly predecessor")
                children[predecessor].append(record.reflection_id)
        if len(roots) != 1 or any(len(items) != 1 for items in children.values()):
            raise ValueError("weekly supersession chain is branched or disconnected")
        current = roots[0]
        visited: set[str] = set()
        while current.reflection_id in children:
            if current.reflection_id in visited:
                raise ValueError("weekly supersession chain contains a cycle")
            visited.add(current.reflection_id)
            current = by_id[children[current.reflection_id][0]]
        if len(visited) + 1 != len(records):
            raise ValueError("weekly supersession chain is disconnected")
        selected.append(current)
    return tuple(sorted(selected, key=lambda item: (item.week_start, item.weekly_policy_id)))


def _signature(pattern: Pattern) -> str:
    return "|".join(
        (
            pattern.pattern_type.value,
            pattern.category.value,
            pattern.signal_class.value,
            pattern.reason_code,
            pattern.scope,
            pattern.scope_value,
        )
    )


def _required_guards(
    reflection: WeeklyReflection, pattern: Pattern
) -> tuple[WeeklySampleGuard, ...] | None:
    selected: list[WeeklySampleGuard] = []
    signature = _signature(pattern)
    for kind in (WeeklyGuardKind.WEEK_COMPLETENESS, WeeklyGuardKind.PROVENANCE_INTEGRITY):
        matches = [guard for guard in reflection.sample_guards if guard.guard_kind is kind]
        if len(matches) != 1:
            return None
        selected.extend(matches)
    for kind in (
        WeeklyGuardKind.PATTERN_DAY_SUPPORT,
        WeeklyGuardKind.PATTERN_EXPERIENCE_SUPPORT,
    ):
        matches = [
            guard
            for guard in reflection.sample_guards
            if guard.guard_kind is kind
            and guard.scope == "pattern_signature"
            and guard.scope_value == signature
        ]
        if len(matches) != 1:
            return None
        selected.extend(matches)
    if any(guard.status is not SampleGuardStatus.PASSED for guard in selected):
        return None
    return tuple(selected)


def _validate_provenance(
    reflection: WeeklyReflection,
    pattern: Pattern,
    daily_by_id: Mapping[str, DailyReflection],
    experience_by_id: Mapping[str, Experience],
) -> None:
    if not set(pattern.supporting_daily_reflection_ids) <= set(
        reflection.input_daily_reflection_ids
    ):
        raise ValueError("pattern DailyReflection identity is not a weekly source")
    findings: dict[str, ReflectionFinding] = {}
    for daily_id in pattern.supporting_daily_reflection_ids:
        daily = daily_by_id.get(daily_id)
        if not isinstance(daily, DailyReflection):
            raise ValueError("supporting DailyReflection identity is unavailable")
        for finding in daily.findings:
            if finding.finding_id in findings:
                raise ValueError("duplicate supporting finding identity")
            findings[finding.finding_id] = finding
    if set(findings) & set(pattern.supporting_finding_ids) != set(
        pattern.supporting_finding_ids
    ):
        raise ValueError("supporting finding identity is unavailable")
    linked_experiences: set[str] = set()
    for finding_id in pattern.supporting_finding_ids:
        finding = findings[finding_id]
        if (
            finding.category is not pattern.category
            or finding.reason_code != pattern.reason_code
            or finding.scope != pattern.scope
            or finding.scope_value != pattern.scope_value
        ):
            raise ValueError("supporting finding semantics do not match pattern")
        linked_experiences.update(finding.supporting_experience_ids)
    if linked_experiences != set(pattern.supporting_experience_ids):
        raise ValueError("pattern Experience linkage does not match findings")
    if not linked_experiences <= set(reflection.input_experience_ids):
        raise ValueError("pattern Experience identity is not a weekly source")
    for experience_id in linked_experiences:
        if experience_id not in experience_by_id:
            raise ValueError("supporting Experience identity is unavailable")


def _content(pattern: Pattern, target: ProposalTargetComponent) -> tuple[str, str, str]:
    subject = (
        f"{pattern.category.value}:{pattern.reason_code}:"
        f"{pattern.scope}={pattern.scope_value}"
    )
    polarity = "successful" if pattern.pattern_type is PatternType.SUCCESS else "adverse"
    rationale = f"Recurring guarded {polarity} evidence for {subject} requires explicit evaluation."
    proposed_change = (
        f"Evaluate an offline {target.value} change candidate addressing {subject}; "
        "do not apply any production setting automatically."
    )
    benefit = (
        f"Determine whether a bounded {target.value} candidate improves {subject} "
        "without weakening deterministic safety controls."
    )
    return rationale, proposed_change, benefit


def build_improvement_proposals(
    weekly_reflections: Iterable[WeeklyReflection],
    daily_reflections: Iterable[DailyReflection],
    experiences: Iterable[Experience],
    policy: ImprovementProposalPolicy,
    pattern_statuses: Mapping[str, KnowledgeStatus] | None = None,
) -> ProposalBuildResult:
    """Build observation-only advisory proposals from exact recurring evidence."""

    weekly = _terminal_weekly(tuple(weekly_reflections))
    daily_by_id = _index_unique(daily_reflections, "reflection_id", "DailyReflection")
    experience_by_id = _index_unique(experiences, "experience_id", "Experience")
    statuses = {} if pattern_statuses is None else dict(pattern_statuses)
    grouped: dict[str, list[tuple[WeeklyReflection, Pattern]]] = defaultdict(list)
    for reflection in weekly:
        if reflection.missing_daily_periods:
            continue
        for pattern in (*reflection.success_patterns, *reflection.failure_patterns):
            grouped[pattern.pattern_key].append((reflection, cast("Pattern", pattern)))

    proposals: list[ImprovementProposal] = []
    assessments: list[ProposalEligibilityAssessment] = []
    for pattern_key in sorted(grouped):
        pairs = sorted(grouped[pattern_key], key=lambda item: item[0].week_start)
        pattern_ids = tuple(pattern.pattern_id for _, pattern in pairs)
        reasons: set[str] = set()
        if len({reflection.week_start for reflection, _ in pairs}) < (
            policy.minimum_complete_week_observations
        ):
            reasons.add("INSUFFICIENT_PATTERN_RECURRENCE")
        if any(
            statuses.get(pattern.pattern_id, KnowledgeStatus.OBSERVATION)
            not in _ACTIVE_PATTERN_STATUSES
            for _, pattern in pairs
        ):
            reasons.add("INACTIVE_PATTERN_STATUS")
        required_guards: list[WeeklySampleGuard] = []
        for reflection, pattern in pairs:
            guards = _required_guards(reflection, pattern)
            if guards is None:
                reasons.add("MISSING_OR_FAILED_REQUIRED_GUARD")
            else:
                required_guards.extend(guards)
            _validate_provenance(reflection, pattern, daily_by_id, experience_by_id)
        status = SampleGuardStatus.PASSED if not reasons else SampleGuardStatus.INSUFFICIENT
        assessment = ProposalEligibilityAssessment(
            pattern_key=pattern_key,
            status=status,
            observed_complete_weeks=len({item[0].week_start for item in pairs}),
            required_complete_weeks=policy.minimum_complete_week_observations,
            reason_codes=tuple(reasons),
            supporting_pattern_ids=pattern_ids,
        )
        assessments.append(assessment)
        if reasons:
            continue

        first = pairs[0][1]
        if any(
            (
                pattern.category,
                pattern.pattern_type,
                pattern.signal_class,
                pattern.reason_code,
                pattern.scope,
                pattern.scope_value,
            )
            != (
                first.category,
                first.pattern_type,
                first.signal_class,
                first.reason_code,
                first.scope,
                first.scope_value,
            )
            for _, pattern in pairs
        ):
            raise ValueError("one pattern_key maps to conflicting pattern semantics")
        weekly_ids = tuple(item[0].reflection_id for item in pairs)
        daily_ids = tuple(
            daily_id for _, pattern in pairs for daily_id in pattern.supporting_daily_reflection_ids
        )
        finding_ids = tuple(
            finding_id for _, pattern in pairs for finding_id in pattern.supporting_finding_ids
        )
        experience_ids = tuple(
            experience_id
            for _, pattern in pairs
            for experience_id in pattern.supporting_experience_ids
        )
        weekly_guard_ids = tuple(guard.guard_id for guard in required_guards)
        target = _TARGETS[first.category]
        rationale, change, benefit = _content(first, target)
        proposal_guards = (
            ProposalEvidenceGuard(
                guard_kind=ProposalGuardKind.PATTERN_RECURRENCE,
                observed_samples=len(pairs),
                required_samples=policy.minimum_complete_week_observations,
                status=SampleGuardStatus.PASSED,
                supporting_weekly_reflection_ids=weekly_ids,
                supporting_pattern_ids=pattern_ids,
            ),
            ProposalEvidenceGuard(
                guard_kind=ProposalGuardKind.WEEKLY_GUARDS,
                observed_samples=len(required_guards),
                required_samples=4 * len(pairs),
                status=SampleGuardStatus.PASSED,
                supporting_weekly_reflection_ids=weekly_ids,
                supporting_pattern_ids=pattern_ids,
                supporting_weekly_guard_ids=weekly_guard_ids,
            ),
            ProposalEvidenceGuard(
                guard_kind=ProposalGuardKind.EXACT_PROVENANCE,
                observed_samples=len(set(experience_ids)),
                required_samples=len(set(experience_ids)),
                status=SampleGuardStatus.PASSED,
                supporting_weekly_reflection_ids=weekly_ids,
                supporting_pattern_ids=pattern_ids,
                supporting_daily_reflection_ids=daily_ids,
                supporting_finding_ids=finding_ids,
                supporting_experience_ids=experience_ids,
            ),
        )
        proposals.append(
            ImprovementProposal(
                policy_id=policy.policy_id,
                pattern_key=pattern_key,
                target_component=target,
                category=first.category,
                pattern_type=first.pattern_type,
                signal_class=first.signal_class,
                reason_code=first.reason_code,
                scope=first.scope,
                scope_value=first.scope_value,
                rationale=rationale,
                proposed_change=change,
                expected_benefit=benefit,
                risks=(
                    "Regime dependence may invalidate the observed relationship.",
                    "Small or correlated samples may overstate the evidence.",
                    "A local change may create unintended downstream behavior.",
                ),
                validation_plan=(
                    "Define a separately reviewed candidate without production mutation.",
                    "Run a causal replay or walk-forward comparison without using Final OOS "
                    "for selection.",
                    "Require explicit operator evaluation and promotion before any deployment.",
                ),
                source_week_starts=tuple(item[0].week_start for item in pairs),
                available_at=max(item[0].available_at for item in pairs),
                supporting_weekly_reflection_ids=weekly_ids,
                supporting_pattern_ids=pattern_ids,
                supporting_daily_reflection_ids=daily_ids,
                supporting_finding_ids=finding_ids,
                supporting_experience_ids=experience_ids,
                supporting_weekly_guard_ids=weekly_guard_ids,
                evidence_guards=proposal_guards,
            )
        )
    return ProposalBuildResult(
        proposals=tuple(sorted(proposals, key=lambda item: item.proposal_key)),
        assessments=tuple(sorted(assessments, key=lambda item: item.pattern_key)),
    )
