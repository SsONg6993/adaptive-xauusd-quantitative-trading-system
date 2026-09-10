CREATE TABLE IF NOT EXISTS reflection_policies (
    policy_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT NOT NULL UNIQUE,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_reflections (
    reflection_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    reflection_id TEXT NOT NULL UNIQUE,
    schema_version TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    available_at TEXT NOT NULL,
    supersedes_reflection_id TEXT,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(policy_id) REFERENCES reflection_policies(policy_id),
    FOREIGN KEY(supersedes_reflection_id) REFERENCES daily_reflections(reflection_id)
);

CREATE TABLE IF NOT EXISTS reflection_findings (
    finding_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    reflection_id TEXT NOT NULL,
    finding_id TEXT NOT NULL,
    category TEXT NOT NULL,
    signal TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    scope TEXT NOT NULL,
    scope_value TEXT NOT NULL,
    sample_size INTEGER NOT NULL,
    record_json TEXT NOT NULL,
    UNIQUE(reflection_id, finding_id),
    FOREIGN KEY(reflection_id) REFERENCES daily_reflections(reflection_id)
);

CREATE TABLE IF NOT EXISTS reflection_sample_guards (
    guard_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    reflection_id TEXT NOT NULL,
    guard_id TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    scope TEXT NOT NULL,
    scope_value TEXT NOT NULL,
    observed_samples INTEGER NOT NULL,
    required_samples INTEGER NOT NULL,
    record_json TEXT NOT NULL,
    UNIQUE(reflection_id, guard_id),
    FOREIGN KEY(reflection_id) REFERENCES daily_reflections(reflection_id)
);

CREATE TABLE IF NOT EXISTS reflection_sources (
    source_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    reflection_id TEXT NOT NULL,
    experience_id TEXT NOT NULL,
    UNIQUE(reflection_id, experience_id),
    FOREIGN KEY(reflection_id) REFERENCES daily_reflections(reflection_id)
);

CREATE INDEX IF NOT EXISTS ix_daily_reflection_period_policy
    ON daily_reflections(period_start, policy_id, reflection_sequence);
CREATE INDEX IF NOT EXISTS ix_reflection_finding_category
    ON reflection_findings(category, reason_code, reflection_id);
CREATE INDEX IF NOT EXISTS ix_reflection_guard_status
    ON reflection_sample_guards(status, category, reflection_id);
CREATE INDEX IF NOT EXISTS ix_reflection_source_experience
    ON reflection_sources(experience_id, reflection_id);

CREATE TRIGGER IF NOT EXISTS reflection_policies_no_update
BEFORE UPDATE ON reflection_policies BEGIN
    SELECT RAISE(ABORT, 'reflection_policies is append-only');
END;
CREATE TRIGGER IF NOT EXISTS reflection_policies_no_delete
BEFORE DELETE ON reflection_policies BEGIN
    SELECT RAISE(ABORT, 'reflection_policies is append-only');
END;
CREATE TRIGGER IF NOT EXISTS daily_reflections_no_update
BEFORE UPDATE ON daily_reflections BEGIN
    SELECT RAISE(ABORT, 'daily_reflections is append-only');
END;
CREATE TRIGGER IF NOT EXISTS daily_reflections_no_delete
BEFORE DELETE ON daily_reflections BEGIN
    SELECT RAISE(ABORT, 'daily_reflections is append-only');
END;
CREATE TRIGGER IF NOT EXISTS reflection_findings_no_update
BEFORE UPDATE ON reflection_findings BEGIN
    SELECT RAISE(ABORT, 'reflection_findings is append-only');
END;
CREATE TRIGGER IF NOT EXISTS reflection_findings_no_delete
BEFORE DELETE ON reflection_findings BEGIN
    SELECT RAISE(ABORT, 'reflection_findings is append-only');
END;
CREATE TRIGGER IF NOT EXISTS reflection_sample_guards_no_update
BEFORE UPDATE ON reflection_sample_guards BEGIN
    SELECT RAISE(ABORT, 'reflection_sample_guards is append-only');
END;
CREATE TRIGGER IF NOT EXISTS reflection_sample_guards_no_delete
BEFORE DELETE ON reflection_sample_guards BEGIN
    SELECT RAISE(ABORT, 'reflection_sample_guards is append-only');
END;
CREATE TRIGGER IF NOT EXISTS reflection_sources_no_update
BEFORE UPDATE ON reflection_sources BEGIN
    SELECT RAISE(ABORT, 'reflection_sources is append-only');
END;
CREATE TRIGGER IF NOT EXISTS reflection_sources_no_delete
BEFORE DELETE ON reflection_sources BEGIN
    SELECT RAISE(ABORT, 'reflection_sources is append-only');
END;
