-- Query 12: At-Risk Customer Summary
-- Business Question: Identify customers exhibiting acute risk indicators (recency > 45d, declining frequency, failed payments) before scoring
-- Grain: One row per at-risk customer

WITH pre_scoring_signals AS (
    SELECT 
        c.customer_id,
        c.customer_segment,
        c.subscription_type,
        c.acquisition_channel,
        CAST((JULIANDAY('2026-04-01') - JULIANDAY(MAX(t.transaction_date))) AS INTEGER) AS days_since_last_txn,
        COUNT(CASE WHEN t.transaction_date >= '2026-01-01' AND t.transaction_date <= '2026-04-01' AND t.transaction_status = 'Success' THEN 1 END) AS txns_last_90d,
        COUNT(CASE WHEN t.transaction_date >= '2025-10-01' AND t.transaction_date < '2026-01-01' AND t.transaction_status = 'Success' THEN 1 END) AS txns_prior_90d,
        COUNT(CASE WHEN t.transaction_date >= '2026-01-01' AND t.payment_status = 'Failed' THEN 1 END) AS failed_payments_90d,
        COALESCE(SUM(CASE WHEN t.transaction_date >= '2025-10-01' AND t.transaction_date <= '2026-04-01' AND t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END), 0.00) AS historical_spend_180d
    FROM customers c
    JOIN customer_snapshots s ON c.customer_id = s.customer_id AND s.snapshot_date = '2026-04-01' AND s.is_eligible = 1
    LEFT JOIN transactions t ON c.customer_id = t.customer_id AND t.transaction_date <= '2026-04-01'
    GROUP BY c.customer_id, c.customer_segment, c.subscription_type, c.acquisition_channel
)
SELECT 
    customer_id,
    customer_segment,
    subscription_type,
    acquisition_channel,
    days_since_last_txn,
    txns_last_90d,
    txns_prior_90d,
    failed_payments_90d,
    historical_spend_180d,
    CASE 
        WHEN days_since_last_txn > 45 AND txns_last_90d < txns_prior_90d THEN 'Severe Velocity Decay'
        WHEN failed_payments_90d >= 2 THEN 'Payment Friction Risk'
        WHEN days_since_last_txn > 30 THEN 'Elevated Inactivity'
        ELSE 'Moderate Early Risk'
    END AS primary_descriptive_signal
FROM pre_scoring_signals
WHERE days_since_last_txn > 30 OR failed_payments_90d >= 2
ORDER BY historical_spend_180d DESC, days_since_last_txn DESC;
