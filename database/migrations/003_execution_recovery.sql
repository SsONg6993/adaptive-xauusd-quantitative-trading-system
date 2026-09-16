CREATE TABLE IF NOT EXISTS execution_transitions (
    transition_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    transition_id TEXT NOT NULL UNIQUE,
    transition_type TEXT NOT NULL,
    intent_id TEXT,
    available_at TEXT NOT NULL,
    transition_json TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_execution_intent_reservation
    ON execution_transitions(intent_id) WHERE transition_type = 'RESERVED';
CREATE INDEX IF NOT EXISTS ix_execution_transition_intent
    ON execution_transitions(intent_id, transition_sequence);
CREATE TABLE IF NOT EXISTS recovery_checkpoints (
    checkpoint_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_id TEXT NOT NULL UNIQUE,
    available_at TEXT NOT NULL,
    checkpoint_json TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS execution_transitions_no_update
BEFORE UPDATE ON execution_transitions BEGIN
    SELECT RAISE(ABORT, 'execution_transitions is append-only');
END;
CREATE TRIGGER IF NOT EXISTS execution_transitions_no_delete
BEFORE DELETE ON execution_transitions BEGIN
    SELECT RAISE(ABORT, 'execution_transitions is append-only');
END;
CREATE TRIGGER IF NOT EXISTS recovery_checkpoints_no_update
BEFORE UPDATE ON recovery_checkpoints BEGIN
    SELECT RAISE(ABORT, 'recovery_checkpoints is append-only');
END;
CREATE TRIGGER IF NOT EXISTS recovery_checkpoints_no_delete
BEFORE DELETE ON recovery_checkpoints BEGIN
    SELECT RAISE(ABORT, 'recovery_checkpoints is append-only');
END;
