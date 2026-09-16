CREATE TABLE IF NOT EXISTS paired_evaluation_reviews (
    review_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL UNIQUE,
    result_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('ACCEPT_EVIDENCE', 'REJECT_EVIDENCE', 'DEFER')),
    operator_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    previous_review_id TEXT,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    UNIQUE(result_id, action_id),
    FOREIGN KEY(result_id) REFERENCES paired_evaluation_results(result_id),
    FOREIGN KEY(request_id) REFERENCES paired_evaluation_requests(request_id),
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id),
    FOREIGN KEY(candidate_id) REFERENCES evaluation_candidate_specs(candidate_id),
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id),
    FOREIGN KEY(previous_review_id) REFERENCES paired_evaluation_reviews(review_id)
);

CREATE INDEX IF NOT EXISTS ix_paired_evaluation_reviews_history
    ON paired_evaluation_reviews(result_id, review_sequence);

CREATE TRIGGER IF NOT EXISTS paired_evaluation_reviews_no_update
BEFORE UPDATE ON paired_evaluation_reviews BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_reviews is append-only');
END;

CREATE TRIGGER IF NOT EXISTS paired_evaluation_reviews_no_delete
BEFORE DELETE ON paired_evaluation_reviews BEGIN
    SELECT RAISE(ABORT, 'paired_evaluation_reviews is append-only');
END;
