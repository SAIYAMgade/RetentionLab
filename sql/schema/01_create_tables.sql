-- RetentionLab: Core Table Schemas (PostgreSQL & SQLite compatible DDL)

-- 1. Raw Transactions Table
CREATE TABLE IF NOT EXISTS raw_transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    transaction_amount NUMERIC(12, 2) NOT NULL,
    transaction_type VARCHAR(32) NOT NULL,
    transaction_status VARCHAR(32) NOT NULL,
    product_category VARCHAR(64) NOT NULL,
    channel VARCHAR(32) NOT NULL,
    currency VARCHAR(8) NOT NULL,
    source_system VARCHAR(64) NOT NULL
);

-- 2. Cleaned Transactions Table
CREATE TABLE IF NOT EXISTS cleaned_transactions (
    transaction_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL,
    transaction_date_str VARCHAR(32) NOT NULL,
    transaction_amount NUMERIC(12, 2) NOT NULL,
    transaction_type VARCHAR(32) NOT NULL,
    transaction_status VARCHAR(32) NOT NULL,
    product_category VARCHAR(64) NOT NULL,
    channel VARCHAR(32) NOT NULL,
    currency VARCHAR(8) NOT NULL,
    source_system VARCHAR(64) NOT NULL
);

-- 3. Customer Features Table (Computed as of cutoff date)
CREATE TABLE IF NOT EXISTS customer_features (
    customer_id VARCHAR(64) PRIMARY KEY,
    recency_days INTEGER NOT NULL,
    first_purchase_days INTEGER NOT NULL,
    days_between_last_two NUMERIC(10, 2),
    recency_to_avg_interval_ratio NUMERIC(10, 4),
    total_transactions INTEGER NOT NULL,
    transactions_30d INTEGER NOT NULL,
    transactions_60d INTEGER NOT NULL,
    transactions_90d INTEGER NOT NULL,
    transactions_180d INTEGER NOT NULL,
    transactions_365d INTEGER NOT NULL,
    active_months INTEGER NOT NULL,
    active_month_ratio NUMERIC(10, 4),
    avg_monthly_transactions NUMERIC(10, 4),
    distinct_purchase_dates INTEGER NOT NULL,
    total_spend NUMERIC(12, 2) NOT NULL,
    avg_transaction_amount NUMERIC(10, 2),
    median_transaction_amount NUMERIC(10, 2),
    max_transaction_amount NUMERIC(10, 2),
    min_transaction_amount NUMERIC(10, 2),
    std_transaction_amount NUMERIC(10, 2),
    spend_30d NUMERIC(12, 2),
    spend_60d NUMERIC(12, 2),
    spend_90d NUMERIC(12, 2),
    spend_180d NUMERIC(12, 2),
    spend_365d NUMERIC(12, 2),
    avg_spend_per_active_month NUMERIC(10, 2),
    frequency_ratio_30_to_90 NUMERIC(10, 4),
    frequency_ratio_90_to_180 NUMERIC(10, 4),
    spend_ratio_30_to_90 NUMERIC(10, 4),
    spend_ratio_90_to_180 NUMERIC(10, 4),
    avg_interpurchase_days NUMERIC(10, 2),
    std_interpurchase_days NUMERIC(10, 2),
    max_interpurchase_days NUMERIC(10, 2),
    interval_expansion_ratio NUMERIC(10, 4),
    is_single_purchase_customer INTEGER NOT NULL,
    distinct_categories INTEGER NOT NULL,
    distinct_channels INTEGER NOT NULL,
    top_category_spend_share NUMERIC(10, 4),
    top_channel_tx_share NUMERIC(10, 4),
    mobile_app_tx_share NUMERIC(10, 4),
    web_tx_share NUMERIC(10, 4),
    in_store_tx_share NUMERIC(10, 4),
    refund_count INTEGER NOT NULL,
    refund_rate NUMERIC(10, 4)
);

-- 4. Target Outcome Labels (Evaluated during future outcome window)
CREATE TABLE IF NOT EXISTS target_labels (
    customer_id VARCHAR(64) PRIMARY KEY,
    prediction_date DATE NOT NULL,
    tenure_days INTEGER NOT NULL,
    future_purchases INTEGER NOT NULL,
    is_inactive INTEGER NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customer_features(customer_id)
);

-- 5. Model Risk Predictions
CREATE TABLE IF NOT EXISTS model_predictions (
    customer_id VARCHAR(64) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    model_version VARCHAR(32) NOT NULL,
    prediction_date DATE NOT NULL,
    inactivity_probability NUMERIC(6, 4) NOT NULL,
    predicted_label INTEGER NOT NULL,
    threshold_used NUMERIC(6, 4) NOT NULL,
    PRIMARY KEY (customer_id, model_name, model_version)
);

-- 6. Customer Prioritization & Action Matrix
CREATE TABLE IF NOT EXISTS customer_prioritization (
    customer_id VARCHAR(64) PRIMARY KEY,
    prediction_date DATE NOT NULL,
    risk_score NUMERIC(6, 4) NOT NULL,
    risk_tier VARCHAR(32) NOT NULL,
    monetary_tier VARCHAR(32) NOT NULL,
    priority_segment VARCHAR(64) NOT NULL,
    recency_days INTEGER NOT NULL,
    transaction_frequency INTEGER NOT NULL,
    total_spend NUMERIC(12, 2) NOT NULL,
    primary_risk_driver VARCHAR(128) NOT NULL,
    recommended_action VARCHAR(256) NOT NULL,
    action_channel VARCHAR(64) NOT NULL,
    model_version VARCHAR(32) NOT NULL
);
