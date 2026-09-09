CREATE TABLE IF NOT EXISTS runtime_journal (
    journal_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    record_type TEXT NOT NULL,
    semantic_id TEXT NOT NULL,
    event_id TEXT,
    parent_id TEXT,
    previous_id TEXT,
    available_at TEXT NOT NULL,
    record_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_runtime_journal_event
    ON runtime_journal(event_id, journal_sequence);
CREATE INDEX IF NOT EXISTS ix_runtime_journal_semantic
    ON runtime_journal(record_type, semantic_id);
CREATE TRIGGER IF NOT EXISTS runtime_journal_no_update
BEFORE UPDATE ON runtime_journal BEGIN
    SELECT RAISE(ABORT, 'runtime_journal is append-only');
END;
CREATE TRIGGER IF NOT EXISTS runtime_journal_no_delete
BEFORE DELETE ON runtime_journal BEGIN
    SELECT RAISE(ABORT, 'runtime_journal is append-only');
END;
