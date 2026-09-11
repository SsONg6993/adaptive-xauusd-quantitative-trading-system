CREATE TABLE IF NOT EXISTS proposal_transition_authorizations (
    authorization_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    authorization_id TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    proposal_key TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    paired_result_id TEXT NOT NULL,
    accepted_review_id TEXT NOT NULL,
    from_status TEXT NOT NULL CHECK(from_status = 'CANDIDATE'),
    to_status TEXT NOT NULL CHECK(to_status = 'VALIDATED'),
    operator_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    authorized_at TEXT NOT NULL,
    previous_authorization_id TEXT,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    UNIQUE(proposal_id, action_id),
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id),
    FOREIGN KEY(candidate_id) REFERENCES evaluation_candidate_specs(candidate_id),
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id),
    FOREIGN KEY(paired_result_id) REFERENCES paired_evaluation_results(result_id),
    FOREIGN KEY(accepted_review_id) REFERENCES paired_evaluation_reviews(review_id),
    FOREIGN KEY(previous_authorization_id)
        REFERENCES proposal_transition_authorizations(authorization_id)
);

CREATE INDEX IF NOT EXISTS ix_proposal_transition_authorization_history
    ON proposal_transition_authorizations(proposal_id, authorization_sequence);

CREATE TRIGGER IF NOT EXISTS proposal_transition_authorizations_no_update
BEFORE UPDATE ON proposal_transition_authorizations BEGIN
    SELECT RAISE(ABORT, 'proposal_transition_authorizations is append-only');
END;

CREATE TRIGGER IF NOT EXISTS proposal_transition_authorizations_no_delete
BEFORE DELETE ON proposal_transition_authorizations BEGIN
    SELECT RAISE(ABORT, 'proposal_transition_authorizations is append-only');
END;
