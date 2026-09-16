CREATE TABLE IF NOT EXISTS paired_evaluation_requests (
    request_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    baseline_policy_set_id TEXT NOT NULL,
    candidate_config_id TEXT NOT NULL,
    evaluation_run_key TEXT NOT NULL,
    adapter_kind TEXT NOT NULL CHECK(adapter_kind = 'CANONICAL_PAIRED_METRICS_V1'),
    adapter_version TEXT NOT NULL,
    deterministic_seed INTEGER NOT NULL,
    environment_identity TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id),
    FOREIGN KEY(candidate_id) REFERENCES evaluation_candidate_specs(candidate_id),
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id),
    FOREIGN KEY(candidate_config_id) REFERENCES shared_kernel_candidate_configs(config_id)
);

CREATE TABLE IF NOT EXISTS paired_evaluation_input_refs (
    request_id TEXT NOT NULL,
    side TEXT NOT NULL CHECK(side IN ('BASELINE', 'CANDIDATE')),
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    artifact_id TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL,
    manifest_id TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    policy_identity TEXT NOT NULL,
    deterministic_seed INTEGER NOT NULL,
    environment_identity TEXT NOT NULL,
    PRIMARY KEY(request_id, side, scope),
    FOREIGN KEY(request_id) REFERENCES paired_evaluation_requests(request_id),
    FOREIGN KEY(manifest_id) REFERENCES shared_kernel_data_manifests(manifest_id)
);

CREATE TABLE IF NOT EXISTS paired_evaluation_results (
    result_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id TEXT NOT NULL UNIQUE,
    request_id TEXT NOT NULL UNIQUE,
    available_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES paired_evaluation_requests(request_id)
);

CREATE TABLE IF NOT EXISTS paired_evaluation_audits (
    audit_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL UNIQUE,
    request_id TEXT NOT NULL UNIQUE,
    result_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status = 'COMPLETED'),
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES paired_evaluation_requests(request_id),
    FOREIGN KEY(result_id) REFERENCES paired_evaluation_results(result_id)
);

CREATE INDEX IF NOT EXISTS ix_paired_evaluation_subject
    ON paired_evaluation_requests(proposal_id, candidate_id, plan_id, request_sequence);

CREATE TRIGGER IF NOT EXISTS paired_evaluation_requests_no_update
BEFORE UPDATE ON paired_evaluation_requests BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_requests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS paired_evaluation_requests_no_delete
BEFORE DELETE ON paired_evaluation_requests BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_requests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS paired_evaluation_input_refs_no_update
BEFORE UPDATE ON paired_evaluation_input_refs BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_input_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS paired_evaluation_input_refs_no_delete
BEFORE DELETE ON paired_evaluation_input_refs BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_input_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS paired_evaluation_results_no_update
BEFORE UPDATE ON paired_evaluation_results BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_results is append-only');
END;
CREATE TRIGGER IF NOT EXISTS paired_evaluation_results_no_delete
BEFORE DELETE ON paired_evaluation_results BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_results is append-only');
END;
CREATE TRIGGER IF NOT EXISTS paired_evaluation_audits_no_update
BEFORE UPDATE ON paired_evaluation_audits BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_audits is append-only');
END;
CREATE TRIGGER IF NOT EXISTS paired_evaluation_audits_no_delete
BEFORE DELETE ON paired_evaluation_audits BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_audits is append-only');
END;
