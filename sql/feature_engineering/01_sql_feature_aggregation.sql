-- ============================================================================
-- RetentionLab: In-Database Feature Aggregation (Query 16)
-- ============================================================================

-- Query 16: Customer-Level Feature Aggregation via SQL
-- Business Question: Can we derive primary RFM and behavioral velocity features directly in the SQL database?
WITH raw_rfm AS (
    SELECT
        customer_id,
        MIN(transaction_timestamp) AS first_tx_dt,
        MAX(transaction_timestamp) AS last_tx_dt,
        COUNT(transaction_id) AS total_purchases,
        SUM(transaction_amount) AS total_spend,
        AVG(transaction_amount) AS aov,
        MAX(transaction_amount) AS max_spend,
        MIN(transaction_amount) AS min_spend,
        COUNT(CASE WHEN transaction_timestamp >= '2023-12-01' THEN 1 END) AS tx_30d,
        COUNT(CASE WHEN transaction_timestamp >= '2023-10-01' THEN 1 END) AS tx_90d,
        SUM(CASE WHEN transaction_timestamp >= '2023-12-01' THEN transaction_amount ELSE 0 END) AS spend_30d,
        SUM(CASE WHEN transaction_timestamp >= '2023-10-01' THEN transaction_amount ELSE 0 END) AS spend_90d,
        COUNT(DISTINCT product_category) AS distinct_categories,
        COUNT(DISTINCT channel) AS distinct_channels
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
),
refund_agg AS (
    SELECT
        customer_id,
        COUNT(transaction_id) AS refund_cnt
    FROM cleaned_transactions
    WHERE transaction_type = 'refund'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
)
SELECT
    r.customer_id,
    ROUND(JULIANDAY('2023-12-31 23:59:59') - JULIANDAY(r.last_tx_dt)) AS recency_days,
    ROUND(JULIANDAY('2023-12-31 23:59:59') - JULIANDAY(r.first_tx_dt)) AS tenure_days,
    r.total_purchases,
    r.tx_30d,
    r.tx_90d,
    ROUND(r.total_spend, 2) AS total_spend,
    ROUND(r.aov, 2) AS avg_transaction_amount,
    ROUND(r.spend_30d, 2) AS spend_30d,
    ROUND(r.spend_90d, 2) AS spend_90d,
    r.distinct_categories,
    r.distinct_channels,
    COALESCE(ref.refund_cnt, 0) AS refund_count,
    ROUND(COALESCE(ref.refund_cnt, 0) * 1.0 / (r.total_purchases + COALESCE(ref.refund_cnt, 0)), 4) AS refund_rate
FROM raw_rfm r
LEFT JOIN refund_agg ref ON r.customer_id = ref.customer_id
WHERE ROUND(JULIANDAY('2023-12-31 23:59:59') - JULIANDAY(r.first_tx_dt)) >= 30
ORDER BY total_spend DESC
LIMIT 50;
