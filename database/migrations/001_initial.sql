CREATE TABLE IF NOT EXISTS candles (
    candle_id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL,
    tick_volume REAL NOT NULL, spread REAL NOT NULL, real_volume REAL,
    source TEXT NOT NULL DEFAULT 'MT5', ingest_id TEXT NOT NULL,
    UNIQUE(symbol, timeframe, timestamp, source)
);
CREATE INDEX IF NOT EXISTS ix_candles_lookup ON candles(symbol, timeframe, timestamp);

CREATE TABLE IF NOT EXISTS market_snapshots (
    snapshot_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, timestamp TEXT NOT NULL,
    dataset_version TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS features (
    snapshot_id TEXT NOT NULL REFERENCES market_snapshots(snapshot_id),
    feature_version TEXT NOT NULL, feature_name TEXT NOT NULL, value REAL,
    PRIMARY KEY(snapshot_id, feature_version, feature_name)
);
CREATE TABLE IF NOT EXISTS market_regimes (
    regime_id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES market_snapshots(snapshot_id),
    regime TEXT NOT NULL, confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
    method_version TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agent_predictions (
    prediction_id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES market_snapshots(snapshot_id),
    timestamp TEXT NOT NULL, symbol TEXT NOT NULL, timeframe TEXT NOT NULL,
    agent_name TEXT NOT NULL, agent_version TEXT NOT NULL, model_version TEXT NOT NULL,
    feature_version TEXT NOT NULL, signal TEXT NOT NULL CHECK(signal IN ('BUY','SELL','HOLD')),
    score REAL NOT NULL CHECK(score BETWEEN -1 AND 1),
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1), regime TEXT,
    freshness_ms INTEGER NOT NULL, reasons_json TEXT NOT NULL, metadata_json TEXT NOT NULL,
    future_outcome REAL, trade_taken INTEGER, trade_outcome REAL, mfe REAL, mae REAL
);
CREATE INDEX IF NOT EXISTS ix_predictions_eval ON agent_predictions(agent_name, symbol, timeframe, timestamp);

CREATE TABLE IF NOT EXISTS master_decisions (
    decision_id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES market_snapshots(snapshot_id),
    symbol TEXT NOT NULL, timestamp TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('BUY','SELL','HOLD')),
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1), regime TEXT NOT NULL,
    agent_scores_json TEXT NOT NULL, reasons_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS risk_decisions (
    risk_decision_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL REFERENCES master_decisions(decision_id), timestamp TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('APPROVED','REJECTED')),
    veto_reasons_json TEXT NOT NULL, risk_fraction REAL NOT NULL,
    stop_distance_points REAL, approved_volume_lots REAL
);
CREATE TABLE IF NOT EXISTS trade_signals (
    signal_id TEXT PRIMARY KEY, decision_id TEXT NOT NULL REFERENCES master_decisions(decision_id),
    risk_decision_id TEXT NOT NULL REFERENCES risk_decisions(risk_decision_id),
    idempotency_key TEXT NOT NULL UNIQUE, payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL, expires_at TEXT NOT NULL, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY, signal_id TEXT NOT NULL REFERENCES trade_signals(signal_id),
    broker_ticket TEXT, request_json TEXT NOT NULL, result_json TEXT,
    requested_at TEXT NOT NULL, executed_at TEXT, execution_price REAL, slippage REAL,
    error_code TEXT
);
CREATE TABLE IF NOT EXISTS positions (
    position_id TEXT PRIMARY KEY, broker_ticket TEXT NOT NULL UNIQUE, symbol TEXT NOT NULL,
    direction TEXT NOT NULL, volume REAL NOT NULL, open_price REAL NOT NULL,
    stop_loss REAL NOT NULL, take_profit REAL NOT NULL, opened_at TEXT NOT NULL,
    closed_at TEXT, state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trades (
    trade_id TEXT PRIMARY KEY, position_id TEXT NOT NULL REFERENCES positions(position_id),
    pnl REAL NOT NULL, commission REAL NOT NULL DEFAULT 0, swap REAL NOT NULL DEFAULT 0,
    mfe REAL, mae REAL, closed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS news_events (
    event_id TEXT PRIMARY KEY, provider TEXT NOT NULL, event_time TEXT NOT NULL,
    currency TEXT, impact TEXT, title TEXT NOT NULL, payload_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS model_registry (
    model_id TEXT PRIMARY KEY, agent_type TEXT NOT NULL, architecture TEXT NOT NULL,
    training_period TEXT NOT NULL, validation_period TEXT NOT NULL, oos_period TEXT NOT NULL,
    feature_version TEXT NOT NULL, dataset_version TEXT NOT NULL, config_hash TEXT NOT NULL,
    metrics_json TEXT NOT NULL, model_path TEXT NOT NULL, onnx_path TEXT, scaler_path TEXT,
    feature_list_json TEXT NOT NULL, created_at TEXT NOT NULL, git_commit TEXT,
    status TEXT NOT NULL DEFAULT 'CANDIDATE'
);
CREATE TABLE IF NOT EXISTS agent_performance (
    performance_id TEXT PRIMARY KEY, agent_name TEXT NOT NULL, model_version TEXT NOT NULL,
    symbol TEXT NOT NULL, timeframe TEXT NOT NULL, regime TEXT, volatility_bucket TEXT,
    session TEXT, news_period INTEGER, sample_count INTEGER NOT NULL,
    metrics_json TEXT NOT NULL, window_start TEXT NOT NULL, window_end TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS system_health (
    health_id TEXT PRIMARY KEY, component TEXT NOT NULL, state TEXT NOT NULL,
    observed_at TEXT NOT NULL, heartbeat_age_ms INTEGER, details_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS errors (
    error_id TEXT PRIMARY KEY, component TEXT NOT NULL, severity TEXT NOT NULL,
    timestamp TEXT NOT NULL, correlation_id TEXT, message TEXT NOT NULL, details_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS backtest_runs (
    run_id TEXT PRIMARY KEY, config_hash TEXT NOT NULL, dataset_version TEXT NOT NULL,
    started_at TEXT NOT NULL, completed_at TEXT, metrics_json TEXT, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS experiment_runs (
    experiment_id TEXT PRIMARY KEY, experiment_type TEXT NOT NULL, config_hash TEXT NOT NULL,
    dataset_version TEXT NOT NULL, feature_version TEXT NOT NULL,
    started_at TEXT NOT NULL, completed_at TEXT, metrics_json TEXT, status TEXT NOT NULL
);
