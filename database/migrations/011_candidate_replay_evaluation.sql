CREATE TABLE IF NOT EXISTS candidate_replay_requests (
    request_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
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
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id)
);

CREATE TABLE IF NOT EXISTS candidate_replay_input_refs (
    request_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    semantic_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY(request_id, scope),
    FOREIGN KEY(request_id) REFERENCES candidate_replay_requests(request_id)
);

CREATE TABLE IF NOT EXISTS candidate_replay_artifacts (
    artifact_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    sha256 TEXT NOT NULL,
    available_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidate_replay_output_refs (
    request_id TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('DEVELOPMENT', 'VALIDATION')),
    artifact_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY(request_id, scope),
    FOREIGN KEY(request_id) REFERENCES candidate_replay_requests(request_id),
    FOREIGN KEY(artifact_id) REFERENCES candidate_replay_artifacts(artifact_id)
);

CREATE TABLE IF NOT EXISTS candidate_replay_audits (
    audit_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL UNIQUE,
    request_id TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    evaluation_run_key TEXT NOT NULL,
    engine_kind TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    deterministic_seed INTEGER NOT NULL,
    environment_identity TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status = 'COMPLETED'),
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES candidate_replay_requests(request_id)
);

CREATE INDEX IF NOT EXISTS ix_candidate_replay_subject
    ON candidate_replay_requests(proposal_id, candidate_id, plan_id, request_sequence);

CREATE TRIGGER IF NOT EXISTS candidate_replay_requests_no_update
BEFORE UPDATE ON candidate_replay_requests BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_requests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_requests_no_delete
BEFORE DELETE ON candidate_replay_requests BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_requests is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_input_refs_no_update
BEFORE UPDATE ON candidate_replay_input_refs BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_input_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_input_refs_no_delete
BEFORE DELETE ON candidate_replay_input_refs BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_input_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_artifacts_no_update
BEFORE UPDATE ON candidate_replay_artifacts BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_artifacts is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_artifacts_no_delete
BEFORE DELETE ON candidate_replay_artifacts BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_artifacts is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_output_refs_no_update
BEFORE UPDATE ON candidate_replay_output_refs BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_output_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_output_refs_no_delete
BEFORE DELETE ON candidate_replay_output_refs BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_output_refs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_audits_no_update
BEFORE UPDATE ON candidate_replay_audits BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_audits is append-only');
END;
CREATE TRIGGER IF NOT EXISTS candidate_replay_audits_no_delete
BEFORE DELETE ON candidate_replay_audits BEGIN
    SELECT RAISE(ABORT, 'candidate_replay_audits is append-only');
END;
