-- ============================================================================
-- RetentionLab: Rolling-Window Transaction Counts (Query 5)
-- ============================================================================

-- Query 5: Rolling Window Historical Transaction Counts
-- Business Question: How many transactions did each customer make across 30d, 60d, 90d, and 180d windows before cutoff?
WITH rolling_windows_cte AS (
    SELECT
        customer_id,
        COUNT(CASE WHEN transaction_timestamp >= DATETIME('2023-12-31 23:59:59', '-30 days') THEN 1 END) AS count_30d,
        COUNT(CASE WHEN transaction_timestamp >= DATETIME('2023-12-31 23:59:59', '-60 days') THEN 1 END) AS count_60d,
        COUNT(CASE WHEN transaction_timestamp >= DATETIME('2023-12-31 23:59:59', '-90 days') THEN 1 END) AS count_90d,
        COUNT(CASE WHEN transaction_timestamp >= DATETIME('2023-12-31 23:59:59', '-180 days') THEN 1 END) AS count_180d,
        COUNT(*) AS count_lifetime,
        ROUND(SUM(CASE WHEN transaction_timestamp >= DATETIME('2023-12-31 23:59:59', '-30 days') THEN transaction_amount ELSE 0 END), 2) AS spend_30d,
        ROUND(SUM(CASE WHEN transaction_timestamp >= DATETIME('2023-12-31 23:59:59', '-90 days') THEN transaction_amount ELSE 0 END), 2) AS spend_90d
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
)
SELECT
    customer_id,
    count_30d,
    count_60d,
    count_90d,
    count_180d,
    count_lifetime,
    spend_30d,
    spend_90d,
    CASE
        WHEN count_90d > 0 AND count_30d = 0 THEN 'Slowing (Active 90d, 0 in 30d)'
        WHEN count_90d = 0 AND count_180d > 0 THEN 'Lapsing (Active 180d, 0 in 90d)'
        WHEN count_30d > 0 THEN 'Actively Purchasing'
        ELSE 'Long-term Dormant'
    END AS short_term_momentum
FROM rolling_windows_cte
ORDER BY count_lifetime DESC
LIMIT 50;
