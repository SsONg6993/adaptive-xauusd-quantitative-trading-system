CREATE TABLE IF NOT EXISTS weekly_reflection_policies (
    policy_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT NOT NULL UNIQUE,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_reflections (
    reflection_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    reflection_id TEXT NOT NULL UNIQUE,
    schema_version TEXT NOT NULL,
    weekly_policy_id TEXT NOT NULL,
    daily_policy_id TEXT NOT NULL,
    week_start TEXT NOT NULL,
    week_end TEXT NOT NULL,
    available_at TEXT NOT NULL,
    complete INTEGER NOT NULL CHECK (complete IN (0, 1)),
    supersedes_reflection_id TEXT,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(weekly_policy_id) REFERENCES weekly_reflection_policies(policy_id),
    FOREIGN KEY(supersedes_reflection_id) REFERENCES weekly_reflections(reflection_id)
);

CREATE TABLE IF NOT EXISTS weekly_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_key TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    knowledge_status TEXT NOT NULL CHECK (knowledge_status = 'OBSERVATION'),
    week_start TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_reflection_patterns (
    reflection_id TEXT NOT NULL,
    pattern_id TEXT NOT NULL,
    PRIMARY KEY(reflection_id, pattern_id),
    FOREIGN KEY(reflection_id) REFERENCES weekly_reflections(reflection_id),
    FOREIGN KEY(pattern_id) REFERENCES weekly_patterns(pattern_id)
);

CREATE TABLE IF NOT EXISTS weekly_sample_guards (
    guard_id TEXT PRIMARY KEY,
    guard_kind TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_reflection_guards (
    reflection_id TEXT NOT NULL,
    guard_id TEXT NOT NULL,
    PRIMARY KEY(reflection_id, guard_id),
    FOREIGN KEY(reflection_id) REFERENCES weekly_reflections(reflection_id),
    FOREIGN KEY(guard_id) REFERENCES weekly_sample_guards(guard_id)
);

CREATE TABLE IF NOT EXISTS weekly_reflection_sources (
    source_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    reflection_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    source_semantic_id TEXT NOT NULL,
    UNIQUE(reflection_id, source_kind, source_semantic_id),
    FOREIGN KEY(reflection_id) REFERENCES weekly_reflections(reflection_id)
);

CREATE TABLE IF NOT EXISTS pattern_status_transitions (
    transition_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    transition_id TEXT NOT NULL UNIQUE,
    pattern_id TEXT NOT NULL,
    pattern_key TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    previous_transition_id TEXT,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(pattern_id) REFERENCES weekly_patterns(pattern_id),
    FOREIGN KEY(previous_transition_id) REFERENCES pattern_status_transitions(transition_id)
);

CREATE INDEX IF NOT EXISTS ix_weekly_reflection_period_policy
    ON weekly_reflections(week_start, weekly_policy_id, reflection_sequence);
CREATE INDEX IF NOT EXISTS ix_weekly_pattern_key
    ON weekly_patterns(pattern_key, week_start, pattern_id);
CREATE INDEX IF NOT EXISTS ix_weekly_source
    ON weekly_reflection_sources(source_semantic_id, source_kind, reflection_id);
CREATE INDEX IF NOT EXISTS ix_pattern_transition_chain
    ON pattern_status_transitions(pattern_id, transition_sequence);

CREATE TRIGGER IF NOT EXISTS weekly_reflection_policies_no_update
BEFORE UPDATE ON weekly_reflection_policies BEGIN
    SELECT RAISE(ABORT, 'weekly_reflection_policies is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflection_policies_no_delete
BEFORE DELETE ON weekly_reflection_policies BEGIN
    SELECT RAISE(ABORT, 'weekly_reflection_policies is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflections_no_update
BEFORE UPDATE ON weekly_reflections BEGIN
    SELECT RAISE(ABORT, 'weekly_reflections is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflections_no_delete
BEFORE DELETE ON weekly_reflections BEGIN
    SELECT RAISE(ABORT, 'weekly_reflections is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_patterns_no_update
BEFORE UPDATE ON weekly_patterns BEGIN
    SELECT RAISE(ABORT, 'weekly_patterns is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_patterns_no_delete
BEFORE DELETE ON weekly_patterns BEGIN
    SELECT RAISE(ABORT, 'weekly_patterns is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflection_patterns_no_update
BEFORE UPDATE ON weekly_reflection_patterns BEGIN
    SELECT RAISE(ABORT, 'weekly_reflection_patterns is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflection_patterns_no_delete
BEFORE DELETE ON weekly_reflection_patterns BEGIN
    SELECT RAISE(ABORT, 'weekly_reflection_patterns is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_sample_guards_no_update
BEFORE UPDATE ON weekly_sample_guards BEGIN
    SELECT RAISE(ABORT, 'weekly_sample_guards is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_sample_guards_no_delete
BEFORE DELETE ON weekly_sample_guards BEGIN
    SELECT RAISE(ABORT, 'weekly_sample_guards is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflection_guards_no_update
BEFORE UPDATE ON weekly_reflection_guards BEGIN
    SELECT RAISE(ABORT, 'weekly_reflection_guards is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflection_guards_no_delete
BEFORE DELETE ON weekly_reflection_guards BEGIN
    SELECT RAISE(ABORT, 'weekly_reflection_guards is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflection_sources_no_update
BEFORE UPDATE ON weekly_reflection_sources BEGIN
    SELECT RAISE(ABORT, 'weekly_reflection_sources is append-only');
END;
CREATE TRIGGER IF NOT EXISTS weekly_reflection_sources_no_delete
BEFORE DELETE ON weekly_reflection_sources BEGIN
    SELECT RAISE(ABORT, 'weekly_reflection_sources is append-only');
END;
CREATE TRIGGER IF NOT EXISTS pattern_status_transitions_no_update
BEFORE UPDATE ON pattern_status_transitions BEGIN
    SELECT RAISE(ABORT, 'pattern_status_transitions is append-only');
END;
CREATE TRIGGER IF NOT EXISTS pattern_status_transitions_no_delete
BEFORE DELETE ON pattern_status_transitions BEGIN
    SELECT RAISE(ABORT, 'pattern_status_transitions is append-only');
END;
