from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from axq.reflection.__main__ import main
from axq.reflection.contracts import FindingCategory, SampleGuardStatus
from axq.reflection.evaluation_contracts import (
    CandidateKind,
    EvaluationCandidateSpec,
    SemanticArtifactRef,
)
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
from axq.reflection.weekly_contracts import (
    PatternSignalClass,
    PatternType,
    TransitionActionKind,
)

NOW = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)


def _candidate_proposal(path) -> ImprovementProposal:
    policy = ImprovementProposalPolicy()
    proposal = ImprovementProposal(
        policy_id=policy.policy_id,
        pattern_key="pattern-key-1",
        target_component=ProposalTargetComponent.MASTER_FUSION,
        category=FindingCategory.DIRECTION_OUTCOME,
        pattern_type=PatternType.FAILURE,
        signal_class=PatternSignalClass.ADVERSE,
        reason_code="NEGATIVE_AVERAGE_R",
        scope="direction",
        scope_value="BUY",
        rationale="Repeated adverse outcome.",
        proposed_change="Evaluate a frozen candidate.",
        expected_benefit="Reduce adverse outcomes if supported.",
        risks=("Overfitting",),
        validation_plan=("Use preregistered evidence.",),
        source_week_starts=(NOW - timedelta(days=21), NOW - timedelta(days=14)),
        available_at=NOW - timedelta(days=7),
        supporting_weekly_reflection_ids=("weekly-1", "weekly-2"),
        supporting_pattern_ids=("pattern-1", "pattern-2"),
        supporting_daily_reflection_ids=("daily-1", "daily-2"),
        supporting_finding_ids=("finding-1", "finding-2"),
        supporting_experience_ids=("experience-1", "experience-2"),
        supporting_weekly_guard_ids=("guard-1", "guard-2"),
        evidence_guards=(
            ProposalEvidenceGuard(
                guard_kind=ProposalGuardKind.PATTERN_RECURRENCE,
                observed_samples=2,
                required_samples=2,
                status=SampleGuardStatus.PASSED,
                supporting_pattern_ids=("pattern-1", "pattern-2"),
            ),
        ),
    )
    store = SQLiteImprovementProposalStore(path)
    store.append_policy(policy)
    store.append(proposal)
    previous: str | None = None
    for index, (source, target) in enumerate(
        (
            (ProposalStatus.OBSERVATION, ProposalStatus.HYPOTHESIS),
            (ProposalStatus.HYPOTHESIS, ProposalStatus.CANDIDATE),
        ),
        start=1,
    ):
        transition = ProposalStatusTransition(
            proposal_id=proposal.proposal_id,
            proposal_key=proposal.proposal_key,
            from_status=source,
            to_status=target,
            effective_at=proposal.available_at + timedelta(minutes=index),
            action_kind=TransitionActionKind.OPERATOR,
            actor_id="operator",
            action_id=f"promotion-{index}",
            reason_code="EXPLICIT_REVIEW",
            previous_transition_id=previous,
        )
        store.append_transition(transition)
        previous = transition.transition_id
    return proposal


def test_evaluation_cli_records_reviewed_evidence_without_promoting_proposal(
    tmp_path, capsys
) -> None:
    store_path = tmp_path / "evaluation.sqlite3"
    proposal = _candidate_proposal(store_path)
    candidate = EvaluationCandidateSpec(
        proposal_id=proposal.proposal_id,
        proposal_key=proposal.proposal_key,
        target_component=proposal.target_component,
        candidate_kind=CandidateKind.RULE,
        description="Frozen candidate.",
        implementation_version="v1",
        source_identity="git-source",
        config_identity="config-source",
        manifest_identity="manifest-source",
        artifact_refs=(SemanticArtifactRef(semantic_id="candidate", sha256="a" * 64),),
        defined_at=NOW,
    )
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(candidate.model_dump_json(), encoding="utf-8")
    assert main(
        [
            "register-evaluation-candidate",
            "--store",
            str(store_path),
            "--input",
            str(candidate_path),
        ]
    ) == 0
    registered = json.loads(capsys.readouterr().out)
    assert registered == {"candidate_id": candidate.candidate_id, "inserted": True}

    plan_input = {
        "proposal_id": proposal.proposal_id,
        "candidate_id": candidate.candidate_id,
        "deterministic_seed": 7,
        "environment_identity": "test-env",
        "defined_at": NOW.isoformat(),
        "actor_id": "operator",
        "action_id": "plan-1",
        "minimum_total_samples": 10,
        "metrics": [
            {
                "metric_key": "validation_expectancy",
                "name": "Expectancy",
                "unit": "R",
                "aggregation": "MEAN",
                "scope": "VALIDATION",
                "direction": "HIGHER_IS_BETTER",
            }
        ],
        "criteria": [
            {
                "metric_key": "validation_expectancy",
                "comparator": "GE",
                "lower_threshold": 0.0,
                "minimum_samples": 10,
                "role": "DECISION",
            }
        ],
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan_input), encoding="utf-8")
    assert main(
        ["build-evaluation-plan", "--store", str(store_path), "--input", str(plan_path)]
    ) == 0
    planned = json.loads(capsys.readouterr().out)
    assert planned["inserted"] is True

    result_input = {
        "plan_id": planned["plan_id"],
        "evaluation_run_key": "run-1",
        "available_at": (NOW + timedelta(hours=2)).isoformat(),
        "observations": [
            {
                "metric_key": "validation_expectancy",
                "scope": "VALIDATION",
                "status": "AVAILABLE",
                "value": 0.2,
                "sample_count": 20,
                "evidence_refs": [{"semantic_id": "evidence", "sha256": "b" * 64}],
                "available_at": (NOW + timedelta(hours=1)).isoformat(),
            }
        ],
    }
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result_input), encoding="utf-8")
    assert main(
        ["record-evaluation-result", "--store", str(store_path), "--input", str(result_path)]
    ) == 0
    recorded = json.loads(capsys.readouterr().out)
    assert recorded["aggregate_outcome"] == "SUPPORTED"

    decision_input = {
        "result_id": recorded["result_id"],
        "decision": "ACCEPT_EVIDENCE",
        "decision_criterion_ids": [planned["criterion_ids"][0]],
        "actor_id": "operator",
        "action_id": "decision-1",
        "reason_code": "SUPPORTED",
        "effective_at": (NOW + timedelta(hours=3)).isoformat(),
    }
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision_input), encoding="utf-8")
    assert main(
        [
            "record-operator-evaluation-decision",
            "--store",
            str(store_path),
            "--input",
            str(decision_path),
        ]
    ) == 0
    decided = json.loads(capsys.readouterr().out)
    assert decided["decision"] == "ACCEPT_EVIDENCE"

    assert main(["evaluation-summary", "--store", str(store_path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["candidate_count"] == 1
    assert summary["plan_count"] == 1
    assert summary["result_count"] == 1
    assert summary["operator_decision_count"] == 1
    assert summary["proposal_status_counts"] == {"CANDIDATE": 1}
    assert SQLiteImprovementProposalStore(store_path).current_status(
        proposal.proposal_id
    ) is ProposalStatus.CANDIDATE
