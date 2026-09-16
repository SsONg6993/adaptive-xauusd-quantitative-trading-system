from __future__ import annotations

from datetime import timedelta

from paired_evaluation_test_support import NOW, persisted_paired_fixture

from axq.reflection.paired_evaluation import compare_paired_evidence
from axq.reflection.paired_evaluation_contracts import PairedEvaluationRequest
from axq.reflection.paired_evaluation_service import execute_paired_evaluation


class CountingAdapter:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request, plan, baseline_artifacts, candidate_artifacts):
        self.calls += 1
        return compare_paired_evidence(
            request, plan, baseline_artifacts, candidate_artifacts
        )


def test_completed_retry_reuses_result_and_audit_without_recomparison(tmp_path) -> None:
    store_path, _, _, _, _, baseline, candidate, request = persisted_paired_fixture(tmp_path)
    adapter = CountingAdapter()
    first = execute_paired_evaluation(
        store_path,
        request,
        (baseline,),
        (candidate,),
        started_at=NOW + timedelta(minutes=21),
        completed_at=NOW + timedelta(minutes=22),
        adapter=adapter,
    )
    later_request = PairedEvaluationRequest(
        **request.model_dump(exclude={"request_id", "requested_at"}),
        requested_at=NOW + timedelta(days=1),
    )
    second = execute_paired_evaluation(
        store_path,
        later_request,
        (baseline,),
        (candidate,),
        started_at=NOW + timedelta(days=1, minutes=21),
        completed_at=NOW + timedelta(days=1, minutes=22),
        adapter=adapter,
    )

    assert adapter.calls == 1
    assert second.reused is True
    assert second.request.request_id == first.request.request_id
    assert second.result.result_id == first.result.result_id
    assert second.audit.audit_id == first.audit.audit_id
    assert second.result_bytes == first.result_bytes
