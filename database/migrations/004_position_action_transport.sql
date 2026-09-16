CREATE TABLE IF NOT EXISTS position_action_transport_transitions (
    transition_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    transition_id TEXT NOT NULL UNIQUE,
    transition_type TEXT NOT NULL,
    intent_id TEXT NOT NULL,
    available_at TEXT NOT NULL,
    transition_json TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_position_action_transport_reservation
    ON position_action_transport_transitions(intent_id)
    WHERE transition_type = 'RESERVED';
CREATE INDEX IF NOT EXISTS ix_position_action_transport_intent
    ON position_action_transport_transitions(intent_id, transition_sequence);
CREATE TRIGGER IF NOT EXISTS position_action_transport_no_update
BEFORE UPDATE ON position_action_transport_transitions BEGIN
    SELECT RAISE(ABORT, 'position_action_transport_transitions is append-only');
END;
CREATE TRIGGER IF NOT EXISTS position_action_transport_no_delete
BEFORE DELETE ON position_action_transport_transitions BEGIN
    SELECT RAISE(ABORT, 'position_action_transport_transitions is append-only');
END;
