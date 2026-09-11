CREATE TABLE IF NOT EXISTS evaluation_execution_requests (
    request_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    plan_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    evaluation_run_key TEXT NOT NULL,
    adapter_kind TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    deterministic_seed INTEGER NOT NULL,
    environment_identity TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id),
    FOREIGN KEY(candidate_id) REFERENCES evaluation_candidate_specs(candidate_id)
);

CREATE TABLE IF NOT EXISTS evaluation_execution_input_refs (
    request_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    semantic_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY(request_id, scope),
    FOREIGN KEY(request_id) REFERENCES evaluation_execution_requests(request_id)
);

CREATE TABLE IF NOT EXISTS evaluation_execution_audits (
    audit_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL UNIQUE,
    request_id TEXT NOT NULL UNIQUE,
    result_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    evaluation_run_key TEXT NOT NULL,
    adapter_kind TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    deterministic_seed INTEGER NOT NULL,
    environment_identity TEXT NOT NULL,
    result_artifact_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status = 'COMPLETED'),
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES evaluation_execution_requests(request_id),
    FOREIGN KEY(result_id) REFERENCES proposal_evaluation_results(result_id),
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id),
    FOREIGN KEY(candidate_id) REFERENCES evaluation_candidate_specs(candidate_id)
);

CREATE INDEX IF NOT EXISTS ix_evaluation_execution_plan
    ON evaluation_execution_requests(plan_id, candidate_id, request_sequence);

CREATE TRIGGER IF NOT EXISTS evaluation_execution_requests_no_update
BEFORE UPDATE ON evaluation_execution_requests BEGIN
    SELECT RAISE(ABORT, 'evaluation_execution_requests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS evaluation_execution_requests_no_delete
BEFORE DELETE ON evaluation_execution_requests BEGIN
    SELECT RAISE(ABORT, 'evaluation_execution_requests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS evaluation_execution_input_refs_no_update
BEFORE UPDATE ON evaluation_execution_input_refs BEGIN
    SELECT RAISE(ABORT, 'evaluation_execution_input_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS evaluation_execution_input_refs_no_delete
BEFORE DELETE ON evaluation_execution_input_refs BEGIN
    SELECT RAISE(ABORT, 'evaluation_execution_input_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS evaluation_execution_audits_no_update
BEFORE UPDATE ON evaluation_execution_audits BEGIN
    SELECT RAISE(ABORT, 'evaluation_execution_audits is append-only');
END;
CREATE TRIGGER IF NOT EXISTS evaluation_execution_audits_no_delete
BEFORE DELETE ON evaluation_execution_audits BEGIN
    SELECT RAISE(ABORT, 'evaluation_execution_audits is append-only');
END;
