from __future__ import annotations

import sqlite3

import pytest
from shared_kernel_candidate_test_support import persisted_shared_kernel_inputs

from axq.reflection.shared_kernel_candidate_store import SQLiteSharedKernelCandidateStore


def test_store_appends_exact_config_manifests_and_request_idempotently(tmp_path) -> None:
    (
        path,
        _,
        _,
        _,
        config,
        manifests,
        _,
        request,
    ) = persisted_shared_kernel_inputs(tmp_path)
    store = SQLiteSharedKernelCandidateStore(path)

    assert store.append_config(config) is True
    assert store.append_config(config) is False
    assert tuple(store.append_manifest(item) for item in manifests) == (True,)
    assert tuple(store.append_manifest(item) for item in manifests) == (False,)
    assert store.append_request(request) is True
    assert store.append_request(request) is False
    assert store.request(request.request_id) == request


def test_store_tables_are_append_only(tmp_path) -> None:
    path, _, _, _, config, manifests, _, request = persisted_shared_kernel_inputs(tmp_path)
    store = SQLiteSharedKernelCandidateStore(path)
    store.append_config(config)
    for manifest in manifests:
        store.append_manifest(manifest)
    store.append_request(request)

    with sqlite3.connect(path) as connection, pytest.raises(
        sqlite3.IntegrityError, match="append-only"
    ):
        connection.execute(
            "UPDATE shared_kernel_candidate_requests SET evaluation_run_key = 'changed'"
        )
