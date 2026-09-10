CREATE TABLE IF NOT EXISTS experience_records (
    experience_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    experience_id TEXT NOT NULL UNIQUE,
    experience_type TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    available_at TEXT NOT NULL,
    symbol TEXT,
    setup_id TEXT,
    thesis_id TEXT,
    scenario_id TEXT,
    regime TEXT,
    session TEXT,
    specialist TEXT,
    outcome TEXT NOT NULL,
    attribution_complete INTEGER NOT NULL CHECK (attribution_complete IN (0, 1)),
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experience_sources (
    source_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    experience_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    source_semantic_id TEXT NOT NULL,
    UNIQUE(experience_id, source_kind, source_semantic_id),
    FOREIGN KEY(experience_id) REFERENCES experience_records(experience_id)
);

CREATE INDEX IF NOT EXISTS ix_experience_time
    ON experience_records(occurred_at, experience_id);
CREATE INDEX IF NOT EXISTS ix_experience_type
    ON experience_records(experience_type, occurred_at);
CREATE INDEX IF NOT EXISTS ix_experience_symbol
    ON experience_records(symbol, occurred_at);
CREATE INDEX IF NOT EXISTS ix_experience_setup
    ON experience_records(setup_id, occurred_at);
CREATE INDEX IF NOT EXISTS ix_experience_thesis
    ON experience_records(thesis_id, occurred_at);
CREATE INDEX IF NOT EXISTS ix_experience_regime
    ON experience_records(regime, occurred_at);
CREATE INDEX IF NOT EXISTS ix_experience_session
    ON experience_records(session, occurred_at);
CREATE INDEX IF NOT EXISTS ix_experience_specialist
    ON experience_records(specialist, occurred_at);
CREATE INDEX IF NOT EXISTS ix_experience_outcome
    ON experience_records(outcome, occurred_at);
CREATE INDEX IF NOT EXISTS ix_experience_source_semantic
    ON experience_sources(source_semantic_id, source_kind, experience_id);

CREATE TRIGGER IF NOT EXISTS experience_records_no_update
BEFORE UPDATE ON experience_records BEGIN
    SELECT RAISE(ABORT, 'experience_records is append-only');
END;
CREATE TRIGGER IF NOT EXISTS experience_records_no_delete
BEFORE DELETE ON experience_records BEGIN
    SELECT RAISE(ABORT, 'experience_records is append-only');
END;
CREATE TRIGGER IF NOT EXISTS experience_sources_no_update
BEFORE UPDATE ON experience_sources BEGIN
    SELECT RAISE(ABORT, 'experience_sources is append-only');
END;
CREATE TRIGGER IF NOT EXISTS experience_sources_no_delete
BEFORE DELETE ON experience_sources BEGIN
    SELECT RAISE(ABORT, 'experience_sources is append-only');
END;
