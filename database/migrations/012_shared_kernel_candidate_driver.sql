CREATE TABLE IF NOT EXISTS shared_kernel_candidate_configs (
    config_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    target_component TEXT NOT NULL CHECK(target_component = 'MASTER_FUSION'),
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id)
);

CREATE TABLE IF NOT EXISTS shared_kernel_data_manifests (
    manifest_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    available_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shared_kernel_candidate_requests (
    request_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    config_id TEXT NOT NULL,
    evaluation_run_key TEXT NOT NULL,
    engine_kind TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    deterministic_seed INTEGER NOT NULL,
    environment_identity TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id),
    FOREIGN KEY(candidate_id) REFERENCES evaluation_candidate_specs(candidate_id),
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id),
    FOREIGN KEY(config_id) REFERENCES shared_kernel_candidate_configs(config_id)
);

CREATE TABLE IF NOT EXISTS shared_kernel_candidate_input_refs (
    request_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    manifest_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY(request_id, scope),
    FOREIGN KEY(request_id) REFERENCES shared_kernel_candidate_requests(request_id),
    FOREIGN KEY(manifest_id) REFERENCES shared_kernel_data_manifests(manifest_id)
);

CREATE TABLE IF NOT EXISTS shared_kernel_candidate_replay_results (
    request_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    semantic_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY(request_id, scope),
    FOREIGN KEY(request_id) REFERENCES shared_kernel_candidate_requests(request_id)
);

CREATE TABLE IF NOT EXISTS shared_kernel_candidate_artifacts (
    artifact_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    sha256 TEXT NOT NULL,
    available_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shared_kernel_candidate_output_refs (
    request_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    artifact_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY(request_id, scope),
    FOREIGN KEY(request_id) REFERENCES shared_kernel_candidate_requests(request_id),
    FOREIGN KEY(artifact_id) REFERENCES shared_kernel_candidate_artifacts(artifact_id)
);

CREATE TABLE IF NOT EXISTS shared_kernel_candidate_audits (
    audit_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL UNIQUE,
    request_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status = 'COMPLETED'),
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES shared_kernel_candidate_requests(request_id)
);

CREATE INDEX IF NOT EXISTS ix_shared_kernel_candidate_subject
    ON shared_kernel_candidate_requests(proposal_id, candidate_id, plan_id, request_sequence);

CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_configs_no_update
BEFORE UPDATE ON shared_kernel_candidate_configs BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_configs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_configs_no_delete
BEFORE DELETE ON shared_kernel_candidate_configs BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_configs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_data_manifests_no_update
BEFORE UPDATE ON shared_kernel_data_manifests BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_data_manifests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_data_manifests_no_delete
BEFORE DELETE ON shared_kernel_data_manifests BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_data_manifests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_requests_no_update
BEFORE UPDATE ON shared_kernel_candidate_requests BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_requests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_requests_no_delete
BEFORE DELETE ON shared_kernel_candidate_requests BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_requests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_input_refs_no_update
BEFORE UPDATE ON shared_kernel_candidate_input_refs BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_input_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_input_refs_no_delete
BEFORE DELETE ON shared_kernel_candidate_input_refs BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_input_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_replay_results_no_update
BEFORE UPDATE ON shared_kernel_candidate_replay_results BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_replay_results is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_replay_results_no_delete
BEFORE DELETE ON shared_kernel_candidate_replay_results BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_replay_results is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_artifacts_no_update
BEFORE UPDATE ON shared_kernel_candidate_artifacts BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_artifacts is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_artifacts_no_delete
BEFORE DELETE ON shared_kernel_candidate_artifacts BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_artifacts is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_output_refs_no_update
BEFORE UPDATE ON shared_kernel_candidate_output_refs BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_output_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_output_refs_no_delete
BEFORE DELETE ON shared_kernel_candidate_output_refs BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_output_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_audits_no_update
BEFORE UPDATE ON shared_kernel_candidate_audits BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_audits is append-only');
END;
CREATE TRIGGER IF NOT EXISTS shared_kernel_candidate_audits_no_delete
BEFORE DELETE ON shared_kernel_candidate_audits BEGIN
    SELECT RAISE(ABORT, 'shared_kernel_candidate_audits is append-only');
END;
