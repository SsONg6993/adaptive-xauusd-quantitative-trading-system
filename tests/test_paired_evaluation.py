from __future__ import annotations

from paired_evaluation_test_support import artifact, artifact_ref, paired_fixture

from axq.reflection.evaluation_contracts import MetricScope
from axq.reflection.paired_evaluation import compare_paired_evidence
from axq.reflection.paired_evaluation_contracts import (
    PairedCriterionStatus,
    PairedEvaluationRequest,
    PairedMetricStatus,
    PairedParityStatus,
)


def test_candidate_criterion_and_decimal_delta_are_deterministic(tmp_path) -> None:
    _, _, plan, baseline, candidate, request = paired_fixture(tmp_path / "store.sqlite3")

    output = compare_paired_evidence(request, plan, (baseline,), (candidate,))

    comparison = next(
        item
        for item in output.result.metric_comparisons
        if item.metric_key == "validation_expectancy"
    )
    outcome = next(
        item
        for item in output.result.criterion_outcomes
        if item.metric_key == "validation_expectancy"
    )
    assert comparison.status is PairedMetricStatus.AVAILABLE
    assert comparison.baseline_value == "0"
    assert comparison.candidate_value == "0.2"
    assert comparison.delta == "0.2"
    assert outcome.status is PairedCriterionStatus.PASS


def test_positive_delta_cannot_override_candidate_criterion_failure(tmp_path) -> None:
    _, _, plan, baseline, _, request = paired_fixture(tmp_path / "store.sqlite3")
    candidate = artifact(
        MetricScope.VALIDATION,
        "validation_expectancy",
        (-0.2, 0.0),
    )
    candidate_ref = artifact_ref(
        candidate,
        policy_identity=request.candidate_config_id,
        marker="a",
    )
    request = PairedEvaluationRequest(
        **request.model_dump(
            exclude={"request_id", "candidate_artifact_refs"}
        ),
        candidate_artifact_refs=(candidate_ref,),
    )
    baseline = artifact(
        MetricScope.VALIDATION,
        "validation_expectancy",
        (-0.4, -0.2),
    )
    baseline_ref = artifact_ref(
        baseline,
        policy_identity=request.baseline_policy_set_id,
        marker="a",
    )
    request = PairedEvaluationRequest(
        **request.model_dump(exclude={"request_id", "baseline_artifact_refs"}),
        baseline_artifact_refs=(baseline_ref,),
    )

    result = compare_paired_evidence(request, plan, (baseline,), (candidate,)).result
    comparison = next(
        item for item in result.metric_comparisons if item.scope is MetricScope.VALIDATION
    )
    outcome = next(item for item in result.criterion_outcomes if item.role.value == "DECISION")
    assert comparison.delta == "0.2"
    assert outcome.status is PairedCriterionStatus.FAIL


def test_environment_mismatch_makes_pair_unavailable(tmp_path) -> None:
    _, _, plan, baseline, candidate, request = paired_fixture(tmp_path / "store.sqlite3")
    changed = request.candidate_artifact_refs[0].model_copy(
        update={"environment_identity": "different-lock"}
    )
    request = PairedEvaluationRequest(
        **request.model_dump(exclude={"request_id", "candidate_artifact_refs"}),
        candidate_artifact_refs=(changed,),
    )

    result = compare_paired_evidence(request, plan, (baseline,), (candidate,)).result

    assert any(
        item.check_key == "ENVIRONMENT_PARITY"
        and item.status is PairedParityStatus.FAIL
        for item in result.parity_checks
    )
    assert all(
        item.status is PairedMetricStatus.UNAVAILABLE
        for item in result.metric_comparisons
    )
    assert all(
        item.status is PairedCriterionStatus.UNAVAILABLE
        for item in result.criterion_outcomes
    )


def test_manifest_mismatch_makes_pair_unavailable(tmp_path) -> None:
    _, _, plan, baseline, candidate, request = paired_fixture(tmp_path / "store.sqlite3")
    changed_manifest = request.candidate_artifact_refs[0].manifest_ref.model_copy(
        update={"semantic_id": "different-manifest"}
    )
    changed = request.candidate_artifact_refs[0].model_copy(
        update={"manifest_ref": changed_manifest}
    )
    request = PairedEvaluationRequest(
        **request.model_dump(exclude={"request_id", "candidate_artifact_refs"}),
        candidate_artifact_refs=(changed,),
    )

    result = compare_paired_evidence(request, plan, (baseline,), (candidate,)).result

    assert next(
        item for item in result.parity_checks if item.check_key == "MANIFEST_PARITY"
    ).status is PairedParityStatus.FAIL
    assert all(
        item.status is PairedCriterionStatus.UNAVAILABLE
        for item in result.criterion_outcomes
    )


def test_missing_candidate_scope_makes_pair_unavailable(tmp_path) -> None:
    _, _, plan, baseline, _, request = paired_fixture(tmp_path / "store.sqlite3")

    result = compare_paired_evidence(request, plan, (baseline,), ()).result

    assert next(
        item for item in result.parity_checks if item.check_key == "SCOPE_PARITY"
    ).status is PairedParityStatus.FAIL
    assert all(
        item.status is PairedCriterionStatus.UNAVAILABLE
        for item in result.criterion_outcomes
    )


def test_duplicate_supplied_scope_makes_pair_unavailable(tmp_path) -> None:
    _, _, plan, baseline, candidate, request = paired_fixture(tmp_path / "store.sqlite3")

    result = compare_paired_evidence(
        request,
        plan,
        (baseline, baseline),
        (candidate,),
    ).result

    assert next(
        item for item in result.parity_checks if item.check_key == "SCOPE_PARITY"
    ).status is PairedParityStatus.FAIL


def test_final_oos_is_unavailable_without_input_artifact(tmp_path) -> None:
    _, _, plan, baseline, candidate, request = paired_fixture(tmp_path / "store.sqlite3")

    result = compare_paired_evidence(request, plan, (baseline,), (candidate,)).result
    final_oos = next(
        item for item in result.metric_comparisons if item.scope is MetricScope.FINAL_OOS
    )

    assert final_oos.status is PairedMetricStatus.UNAVAILABLE
    assert final_oos.reason_code == "FINAL_OOS_NOT_ACCESSED"
