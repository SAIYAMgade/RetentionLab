-- RetentionLab: Performance Indexes

CREATE INDEX IF NOT EXISTS idx_raw_tx_cust_date ON raw_transactions(customer_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_cleaned_tx_cust_date ON cleaned_transactions(customer_id, transaction_timestamp);
CREATE INDEX IF NOT EXISTS idx_cleaned_tx_status_type ON cleaned_transactions(transaction_status, transaction_type);
CREATE INDEX IF NOT EXISTS idx_target_inactive ON target_labels(is_inactive);
CREATE INDEX IF NOT EXISTS idx_prio_tier_seg ON customer_prioritization(risk_tier, monetary_tier, priority_segment);
