-- ============================================================================
-- RetentionLab: Period-over-Period Behavioral Velocity (Query 15)
-- ============================================================================

-- Query 15: Period-over-Period Behavioral Changes
-- Business Question: How did each customer's order frequency and spend change between Recent Window (Oct-Dec 2023) and Prior Window (Jul-Sep 2023)?
WITH p_recent AS (
    SELECT
        customer_id,
        COUNT(transaction_id) AS tx_recent,
        SUM(transaction_amount) AS spend_recent
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp >= '2023-10-01'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
),
p_prior AS (
    SELECT
        customer_id,
        COUNT(transaction_id) AS tx_prior,
        SUM(transaction_amount) AS spend_prior
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp >= '2023-07-01'
      AND transaction_timestamp < '2023-10-01'
    GROUP BY customer_id
),
pop_merged AS (
    SELECT
        COALESCE(r.customer_id, p.customer_id) AS customer_id,
        COALESCE(r.tx_recent, 0) AS tx_recent,
        COALESCE(p.tx_prior, 0) AS tx_prior,
        ROUND(COALESCE(r.spend_recent, 0), 2) AS spend_recent,
        ROUND(COALESCE(p.spend_prior, 0), 2) AS spend_prior
    FROM p_recent r
    FULL OUTER JOIN p_prior p ON r.customer_id = p.customer_id
)
SELECT
    customer_id,
    tx_recent,
    tx_prior,
    tx_recent - tx_prior AS frequency_delta,
    spend_recent,
    spend_prior,
    ROUND(spend_recent - spend_prior, 2) AS spend_delta,
    CASE
        WHEN tx_prior > 0 AND tx_recent = 0 THEN 'Complete Stoppage'
        WHEN tx_prior > 0 AND tx_recent < tx_prior THEN 'Declining Activity'
        WHEN tx_prior = 0 AND tx_recent > 0 THEN 'New / Re-activated'
        WHEN tx_recent > tx_prior THEN 'Growing Activity'
        ELSE 'Stable / Low'
    END AS trajectory_status
FROM pop_merged
ORDER BY frequency_delta ASC
LIMIT 50;
