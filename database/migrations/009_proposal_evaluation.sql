CREATE TABLE IF NOT EXISTS evaluation_candidate_specs (
    candidate_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    proposal_key TEXT NOT NULL,
    target_component TEXT NOT NULL,
    defined_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id)
);

CREATE TABLE IF NOT EXISTS proposal_evaluation_plans (
    plan_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL UNIQUE,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    defined_at TEXT NOT NULL,
    supersedes_plan_id TEXT,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(proposal_id) REFERENCES improvement_proposals(proposal_id),
    FOREIGN KEY(candidate_id) REFERENCES evaluation_candidate_specs(candidate_id),
    FOREIGN KEY(supersedes_plan_id) REFERENCES proposal_evaluation_plans(plan_id)
);

CREATE TABLE IF NOT EXISTS proposal_evaluation_sources (
    plan_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    source_semantic_id TEXT NOT NULL,
    PRIMARY KEY(plan_id, source_kind, source_semantic_id),
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id)
);

CREATE TABLE IF NOT EXISTS proposal_evaluation_metrics (
    plan_id TEXT NOT NULL,
    metric_id TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    scope TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    PRIMARY KEY(plan_id, metric_id),
    UNIQUE(plan_id, metric_key),
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id)
);

CREATE TABLE IF NOT EXISTS proposal_acceptance_criteria (
    plan_id TEXT NOT NULL,
    criterion_id TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    role TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    PRIMARY KEY(plan_id, criterion_id),
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id)
);

CREATE TABLE IF NOT EXISTS proposal_evaluation_results (
    result_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id TEXT NOT NULL UNIQUE,
    plan_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    evaluation_run_key TEXT NOT NULL,
    available_at TEXT NOT NULL,
    aggregate_outcome TEXT NOT NULL,
    supersedes_result_id TEXT,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(plan_id) REFERENCES proposal_evaluation_plans(plan_id),
    FOREIGN KEY(supersedes_result_id) REFERENCES proposal_evaluation_results(result_id)
);

CREATE TABLE IF NOT EXISTS proposal_metric_observations (
    result_id TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    scope TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    PRIMARY KEY(result_id, observation_id),
    UNIQUE(result_id, metric_key),
    FOREIGN KEY(result_id) REFERENCES proposal_evaluation_results(result_id)
);

CREATE TABLE IF NOT EXISTS proposal_metric_evidence (
    result_id TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    semantic_id TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY(result_id, observation_id, semantic_id),
    FOREIGN KEY(result_id, observation_id)
        REFERENCES proposal_metric_observations(result_id, observation_id)
);

CREATE TABLE IF NOT EXISTS proposal_criterion_outcomes (
    result_id TEXT NOT NULL,
    outcome_id TEXT NOT NULL,
    criterion_id TEXT NOT NULL,
    status TEXT NOT NULL,
    role TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    PRIMARY KEY(result_id, outcome_id),
    UNIQUE(result_id, criterion_id),
    FOREIGN KEY(result_id) REFERENCES proposal_evaluation_results(result_id)
);

CREATE TABLE IF NOT EXISTS operator_evaluation_decisions (
    decision_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL UNIQUE,
    result_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    proposal_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    previous_decision_id TEXT,
    schema_version TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    record_json TEXT NOT NULL,
    FOREIGN KEY(result_id) REFERENCES proposal_evaluation_results(result_id),
    FOREIGN KEY(previous_decision_id) REFERENCES operator_evaluation_decisions(decision_id)
);

CREATE INDEX IF NOT EXISTS ix_evaluation_plan_subject
    ON proposal_evaluation_plans(proposal_id, candidate_id, plan_sequence);
CREATE INDEX IF NOT EXISTS ix_evaluation_result_run
    ON proposal_evaluation_results(plan_id, evaluation_run_key, result_sequence);
CREATE INDEX IF NOT EXISTS ix_operator_evaluation_history
    ON operator_evaluation_decisions(result_id, decision_sequence);

CREATE TRIGGER IF NOT EXISTS evaluation_candidate_specs_no_update
BEFORE UPDATE ON evaluation_candidate_specs BEGIN
    SELECT RAISE(ABORT, 'evaluation_candidate_specs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS evaluation_candidate_specs_no_delete
BEFORE DELETE ON evaluation_candidate_specs BEGIN
    SELECT RAISE(ABORT, 'evaluation_candidate_specs is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evaluation_plans_no_update
BEFORE UPDATE ON proposal_evaluation_plans BEGIN
    SELECT RAISE(ABORT, 'proposal_evaluation_plans is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evaluation_plans_no_delete
BEFORE DELETE ON proposal_evaluation_plans BEGIN
    SELECT RAISE(ABORT, 'proposal_evaluation_plans is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evaluation_sources_no_update
BEFORE UPDATE ON proposal_evaluation_sources BEGIN
    SELECT RAISE(ABORT, 'proposal_evaluation_sources is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evaluation_sources_no_delete
BEFORE DELETE ON proposal_evaluation_sources BEGIN
    SELECT RAISE(ABORT, 'proposal_evaluation_sources is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evaluation_metrics_no_update
BEFORE UPDATE ON proposal_evaluation_metrics BEGIN
    SELECT RAISE(ABORT, 'proposal_evaluation_metrics is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evaluation_metrics_no_delete
BEFORE DELETE ON proposal_evaluation_metrics BEGIN
    SELECT RAISE(ABORT, 'proposal_evaluation_metrics is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_acceptance_criteria_no_update
BEFORE UPDATE ON proposal_acceptance_criteria BEGIN
    SELECT RAISE(ABORT, 'proposal_acceptance_criteria is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_acceptance_criteria_no_delete
BEFORE DELETE ON proposal_acceptance_criteria BEGIN
    SELECT RAISE(ABORT, 'proposal_acceptance_criteria is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evaluation_results_no_update
BEFORE UPDATE ON proposal_evaluation_results BEGIN
    SELECT RAISE(ABORT, 'proposal_evaluation_results is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_evaluation_results_no_delete
BEFORE DELETE ON proposal_evaluation_results BEGIN
    SELECT RAISE(ABORT, 'proposal_evaluation_results is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_metric_observations_no_update
BEFORE UPDATE ON proposal_metric_observations BEGIN
    SELECT RAISE(ABORT, 'proposal_metric_observations is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_metric_observations_no_delete
BEFORE DELETE ON proposal_metric_observations BEGIN
    SELECT RAISE(ABORT, 'proposal_metric_observations is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_metric_evidence_no_update
BEFORE UPDATE ON proposal_metric_evidence BEGIN
    SELECT RAISE(ABORT, 'proposal_metric_evidence is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_metric_evidence_no_delete
BEFORE DELETE ON proposal_metric_evidence BEGIN
    SELECT RAISE(ABORT, 'proposal_metric_evidence is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_criterion_outcomes_no_update
BEFORE UPDATE ON proposal_criterion_outcomes BEGIN
    SELECT RAISE(ABORT, 'proposal_criterion_outcomes is append-only');
END;
CREATE TRIGGER IF NOT EXISTS proposal_criterion_outcomes_no_delete
BEFORE DELETE ON proposal_criterion_outcomes BEGIN
    SELECT RAISE(ABORT, 'proposal_criterion_outcomes is append-only');
END;
CREATE TRIGGER IF NOT EXISTS operator_evaluation_decisions_no_update
BEFORE UPDATE ON operator_evaluation_decisions BEGIN
    SELECT RAISE(ABORT, 'operator_evaluation_decisions is append-only');
END;
CREATE TRIGGER IF NOT EXISTS operator_evaluation_decisions_no_delete
BEFORE DELETE ON operator_evaluation_decisions BEGIN
    SELECT RAISE(ABORT, 'operator_evaluation_decisions is append-only');
END;
