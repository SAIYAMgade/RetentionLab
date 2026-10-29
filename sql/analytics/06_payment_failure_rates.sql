-- Query 06: Payment Failure Rates
-- Business Question: What are payment failure rates by subscription type and billing channel over time?
-- Grain: One row per subscription_type and transaction_channel

SELECT 
    c.subscription_type,
    t.transaction_channel,
    COUNT(t.transaction_id) AS total_payment_attempts,
    COUNT(CASE WHEN t.payment_status = 'Failed' THEN 1 END) AS failed_payment_count,
    ROUND((CAST(COUNT(CASE WHEN t.payment_status = 'Failed' THEN 1 END) AS FLOAT) / COUNT(t.transaction_id)) * 100.0, 2) AS payment_failure_rate_pct,
    ROUND(SUM(CASE WHEN t.payment_status = 'Failed' THEN t.transaction_amount ELSE 0 END), 2) AS failed_revenue_at_risk,
    COUNT(DISTINCT CASE WHEN t.payment_status = 'Failed' THEN t.customer_id END) AS affected_customers_count
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.subscription_type, t.transaction_channel
ORDER BY payment_failure_rate_pct DESC;
