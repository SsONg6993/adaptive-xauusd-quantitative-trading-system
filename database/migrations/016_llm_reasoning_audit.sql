CREATE TABLE IF NOT EXISTS llm_reasoning_requests (
    request_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    task TEXT NOT NULL,
    provider_kind TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_digest TEXT NOT NULL,
    prompt_template_digest TEXT NOT NULL,
    response_schema_digest TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_reasoning_responses (
    response_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id TEXT NOT NULL UNIQUE,
    request_id TEXT NOT NULL,
    provider_kind TEXT NOT NULL,
    model_digest TEXT NOT NULL,
    structured_response_digest TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(request_id) REFERENCES llm_reasoning_requests(request_id)
);

CREATE INDEX IF NOT EXISTS ix_llm_reasoning_responses_request
    ON llm_reasoning_responses(request_id, response_sequence);

CREATE TABLE IF NOT EXISTS llm_reasoning_attempts (
    attempt_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id TEXT NOT NULL UNIQUE,
    request_id TEXT NOT NULL,
    attempt_key TEXT NOT NULL,
    status TEXT NOT NULL,
    response_id TEXT,
    failure_code TEXT,
    requested_at TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    UNIQUE(request_id, attempt_key),
    FOREIGN KEY(request_id) REFERENCES llm_reasoning_requests(request_id),
    FOREIGN KEY(response_id) REFERENCES llm_reasoning_responses(response_id),
    CHECK (
        (status IN ('COMPLETED', 'REUSED') AND response_id IS NOT NULL AND failure_code IS NULL)
        OR
        (status NOT IN ('COMPLETED', 'REUSED') AND response_id IS NULL AND failure_code IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_llm_reasoning_attempt_history
    ON llm_reasoning_attempts(request_id, attempt_sequence);

CREATE TRIGGER IF NOT EXISTS llm_reasoning_requests_no_update
BEFORE UPDATE ON llm_reasoning_requests BEGIN
    SELECT RAISE(ABORT, 'llm_reasoning_requests is append-only');
END;

CREATE TRIGGER IF NOT EXISTS llm_reasoning_requests_no_delete
BEFORE DELETE ON llm_reasoning_requests BEGIN
    SELECT RAISE(ABORT, 'llm_reasoning_requests is append-only');
END;

CREATE TRIGGER IF NOT EXISTS llm_reasoning_responses_no_update
BEFORE UPDATE ON llm_reasoning_responses BEGIN
    SELECT RAISE(ABORT, 'llm_reasoning_responses is append-only');
END;

CREATE TRIGGER IF NOT EXISTS llm_reasoning_responses_no_delete
BEFORE DELETE ON llm_reasoning_responses BEGIN
    SELECT RAISE(ABORT, 'llm_reasoning_responses is append-only');
END;

CREATE TRIGGER IF NOT EXISTS llm_reasoning_attempts_no_update
BEFORE UPDATE ON llm_reasoning_attempts BEGIN
    SELECT RAISE(ABORT, 'llm_reasoning_attempts is append-only');
END;

CREATE TRIGGER IF NOT EXISTS llm_reasoning_attempts_no_delete
BEFORE DELETE ON llm_reasoning_attempts BEGIN
    SELECT RAISE(ABORT, 'llm_reasoning_attempts is append-only');
END;
