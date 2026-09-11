CREATE TABLE IF NOT EXISTS improvement_proposal_policies (
    policy_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id TEXT NOT NULL UNIQUE,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS improvement_proposals (
    proposal_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id TEXT NOT NULL UNIQUE,
    proposal_key TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    target_component TEXT NOT NULL,
    pattern_key TEXT NOT NULL,
    available_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status = 'OBSERVATION'),
    supersedes_proposal_id TEXT,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(policy_id) REFERENCES improvement_proposal_policies(policy_id),
    FOREIGN KEY(supersedes_proposal_id) REFERENCES improvement_proposals(proposal_id)
);

CREATE TABLE IF NOT EXISTS proposal_evidence_guards (
    proposal_id TEXT NOT NULL,
    guard_id TEXT NOT NULL,
    guard_kind TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status = 'PASSED'),
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    PRIMARY KEY(proposal_id, guard_id),
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id)
);

CREATE TABLE IF NOT EXISTS improvement_proposal_sources (
    source_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    source_semantic_id TEXT NOT NULL,
    UNIQUE(proposal_id, source_kind, source_semantic_id),
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id)
);

CREATE TABLE IF NOT EXISTS proposal_status_transitions (
    transition_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    transition_id TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    proposal_key TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    previous_transition_id TEXT,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id),
    FOREIGN KEY(previous_transition_id) REFERENCES proposal_status_transitions(transition_id)
);

CREATE INDEX IF NOT EXISTS ix_improvement_proposal_key
    ON improvement_proposals(proposal_key, policy_id, proposal_sequence);
CREATE INDEX IF NOT EXISTS ix_improvement_proposal_pattern_key
    ON improvement_proposals(pattern_key, proposal_sequence);
CREATE INDEX IF NOT EXISTS ix_improvement_proposal_source
    ON improvement_proposal_sources(source_semantic_id, source_kind, proposal_id);
CREATE INDEX IF NOT EXISTS ix_proposal_transition_chain
    ON proposal_status_transitions(proposal_id, transition_sequence);

CREATE TRIGGER IF NOT EXISTS improvement_proposal_policies_no_update
BEFORE UPDATE ON improvement_proposal_policies BEGIN
    SELECT RAISE(ABORT, 'improvement_proposal_policies is append-only');
END;
CREATE TRIGGER IF NOT EXISTS improvement_proposal_policies_no_delete
BEFORE DELETE ON improvement_proposal_policies BEGIN
    SELECT RAISE(ABORT, 'improvement_proposal_policies is append-only');
END;
CREATE TRIGGER IF NOT EXISTS improvement_proposals_no_update
BEFORE UPDATE ON improvement_proposals BEGIN
    SELECT RAISE(ABORT, 'improvement_proposals is append-only');
END;
CREATE TRIGGER IF NOT EXISTS improvement_proposals_no_delete
BEFORE DELETE ON improvement_proposals BEGIN
    SELECT RAISE(ABORT, 'improvement_proposals is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evidence_guards_no_update
BEFORE UPDATE ON proposal_evidence_guards BEGIN
    SELECT RAISE(ABORT, 'proposal_evidence_guards is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evidence_guards_no_delete
BEFORE DELETE ON proposal_evidence_guards BEGIN
    SELECT RAISE(ABORT, 'proposal_evidence_guards is append-only');
END;
CREATE TRIGGER IF NOT EXISTS improvement_proposal_sources_no_update
BEFORE UPDATE ON improvement_proposal_sources BEGIN
    SELECT RAISE(ABORT, 'improvement_proposal_sources is append-only');
END;
CREATE TRIGGER IF NOT EXISTS improvement_proposal_sources_no_delete
BEFORE DELETE ON improvement_proposal_sources BEGIN
    SELECT RAISE(ABORT, 'improvement_proposal_sources is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_status_transitions_no_update
BEFORE UPDATE ON proposal_status_transitions BEGIN
    SELECT RAISE(ABORT, 'proposal_status_transitions is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_status_transitions_no_delete
BEFORE DELETE ON proposal_status_transitions BEGIN
    SELECT RAISE(ABORT, 'proposal_status_transitions is append-only');
END;
