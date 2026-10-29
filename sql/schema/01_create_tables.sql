-- RetentionLab Relational Analytics Schema
-- Standard ANSI SQL / SQLite / PostgreSQL compatible

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    signup_date DATE NOT NULL,
    customer_segment VARCHAR(32) NOT NULL,
    acquisition_channel VARCHAR(32) NOT NULL,
    region VARCHAR(32) NOT NULL,
    subscription_type VARCHAR(32) NOT NULL,
    account_status VARCHAR(32) NOT NULL,
    marketing_consent INTEGER NOT NULL DEFAULT 1,
    tenure_days INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_name VARCHAR(128) NOT NULL,
    product_category VARCHAR(64) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_amount NUMERIC(10, 2) NOT NULL,
    transaction_type VARCHAR(32) NOT NULL,
    payment_status VARCHAR(32) NOT NULL,
    discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    refund_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    transaction_channel VARCHAR(32) NOT NULL,
    transaction_status VARCHAR(32) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS customer_activity (
    activity_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    activity_date DATE NOT NULL,
    activity_type VARCHAR(32) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    ticket_date DATE NOT NULL,
    ticket_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    satisfaction_score INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS campaign_interactions (
    interaction_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    campaign_date DATE NOT NULL,
    channel VARCHAR(32) NOT NULL,
    action VARCHAR(32) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS customer_snapshots (
    snapshot_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    snapshot_date DATE NOT NULL,
    is_eligible INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS retention_scores (
    score_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    snapshot_date DATE NOT NULL,
    churn_probability NUMERIC(6, 4) NOT NULL,
    risk_band VARCHAR(32) NOT NULL,
    prioritization_score NUMERIC(6, 4) NOT NULL,
    historical_value_proxy NUMERIC(12, 2) NOT NULL,
    risk_weighted_exposure NUMERIC(12, 2) NOT NULL,
    top_risk_signals TEXT,
    suggested_action VARCHAR(64),
    recommended_next_step TEXT,
    is_top_15_percent INTEGER NOT NULL DEFAULT 0,
    model_version VARCHAR(32) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Core indexes for analytical performance
CREATE INDEX IF NOT EXISTS idx_txn_cust_date ON transactions(customer_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_act_cust_date ON customer_activity(customer_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_sup_cust_date ON support_tickets(customer_id, ticket_date);
CREATE INDEX IF NOT EXISTS idx_cam_cust_date ON campaign_interactions(customer_id, campaign_date);
CREATE INDEX IF NOT EXISTS idx_snap_cust_date ON customer_snapshots(customer_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_scores_cust_date ON retention_scores(customer_id, snapshot_date);
