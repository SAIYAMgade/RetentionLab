-- Query 04: Customer Revenue Contribution and Pareto Distribution
-- Business Question: What percentage of total platform revenue is driven by top customer percentiles?
-- Grain: One row per customer with cumulative contribution percentage

WITH customer_spend AS (
    SELECT 
        c.customer_id,
        c.customer_segment,
        SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END) AS total_customer_spend
    FROM customers c
    JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.customer_id, c.customer_segment
),
ranked_spend AS (
    SELECT 
        customer_id,
        customer_segment,
        total_customer_spend,
        ROW_NUMBER() OVER (ORDER BY total_customer_spend DESC) AS spend_rank,
        COUNT(*) OVER () AS total_customer_count,
        SUM(total_customer_spend) OVER () AS platform_total_revenue,
        SUM(total_customer_spend) OVER (ORDER BY total_customer_spend DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_cumulative_revenue
    FROM customer_spend
)
SELECT 
    customer_id,
    customer_segment,
    ROUND(total_customer_spend, 2) AS total_customer_spend,
    spend_rank,
    ROUND((CAST(spend_rank AS FLOAT) / total_customer_count) * 100.0, 2) AS customer_percentile_rank,
    ROUND((running_cumulative_revenue / platform_total_revenue) * 100.0, 2) AS cumulative_revenue_share_pct
FROM ranked_spend
ORDER BY spend_rank ASC;
