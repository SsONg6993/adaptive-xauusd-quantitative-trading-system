from __future__ import annotations

import hashlib
import sqlite3
from datetime import timedelta

import pytest
from paired_evaluation_test_support import NOW, persisted_paired_fixture

from axq.reflection.execution_adapter import canonical_record_bytes
from axq.reflection.paired_evaluation import compare_paired_evidence
from axq.reflection.paired_evaluation_contracts import PairedEvaluationAudit
from axq.reflection.paired_evaluation_store import SQLitePairedEvaluationStore


def test_store_is_append_only_and_exact_linked(tmp_path) -> None:
    store_path, _, _, plan, _, baseline, candidate, request = persisted_paired_fixture(
        tmp_path
    )
    store = SQLitePairedEvaluationStore(store_path)
    result = compare_paired_evidence(request, plan, (baseline,), (candidate,)).result
    audit = PairedEvaluationAudit(
        request_id=request.request_id,
        result_id=result.result_id,
        proposal_id=request.proposal_id,
        candidate_id=request.candidate_id,
        plan_id=request.plan_id,
        baseline_policy_set_id=request.baseline_policy_set_id,
        candidate_config_id=request.candidate_config_id,
        deterministic_seed=request.deterministic_seed,
        environment_identity=request.environment_identity,
        result_sha256=hashlib.sha256(canonical_record_bytes(result)).hexdigest(),
        started_at=NOW + timedelta(minutes=21),
        completed_at=NOW + timedelta(minutes=22),
    )

    assert store.append_request(request) is True
    assert store.append_request(request) is False
    assert store.append_result(result) is True
    assert store.append_result(result) is False
    assert store.append_audit(audit) is True
    assert store.append_audit(audit) is False
    assert store.request(request.request_id) == request
    assert store.result(request.request_id) == result
    assert store.audit(request.request_id) == audit

    with (
        pytest.raises(sqlite3.IntegrityError, match="append-only"),
        sqlite3.connect(store_path) as connection,
    ):
        connection.execute(
            "UPDATE paired_evaluation_requests SET evaluation_run_key = 'changed'"
        )


def test_store_rejects_missing_authoritative_config(tmp_path) -> None:
    store_path, _, _, _, _, _, _, request = persisted_paired_fixture(tmp_path)
    with sqlite3.connect(store_path) as connection:
        connection.execute("DROP TRIGGER shared_kernel_candidate_configs_no_delete")
        connection.execute("DELETE FROM shared_kernel_candidate_configs")

    with pytest.raises(ValueError, match="authoritative"):
        SQLitePairedEvaluationStore(store_path).append_request(request)
