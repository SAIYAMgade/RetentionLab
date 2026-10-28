-- ============================================================================
-- RetentionLab: Refund & Reversal Analysis (Query 9)
-- ============================================================================

-- Query 9: Refund & Friction Analysis by Category and Channel
-- Business Question: Where are refunds concentrated, and do high-refund customers show higher risk?
WITH refund_metrics_cte AS (
    SELECT
        product_category,
        channel,
        COUNT(CASE WHEN transaction_type = 'purchase' AND transaction_status = 'completed' THEN 1 END) AS purchase_count,
        COUNT(CASE WHEN transaction_type = 'refund' AND transaction_status = 'completed' THEN 1 END) AS refund_count,
        ROUND(SUM(CASE WHEN transaction_type = 'purchase' AND transaction_status = 'completed' THEN transaction_amount ELSE 0 END), 2) AS gross_sales,
        ROUND(ABS(SUM(CASE WHEN transaction_type = 'refund' AND transaction_status = 'completed' THEN transaction_amount ELSE 0 END)), 2) AS refunded_amount
    FROM cleaned_transactions
    WHERE transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY product_category, channel
)
SELECT
    product_category,
    channel,
    purchase_count,
    refund_count,
    gross_sales,
    refunded_amount,
    ROUND(refund_count * 100.0 / NULLIF(purchase_count + refund_count, 0), 2) AS refund_rate_pct,
    ROUND(refunded_amount * 100.0 / NULLIF(gross_sales, 0), 2) AS refund_value_pct
FROM refund_metrics_cte
ORDER BY refunded_amount DESC;
