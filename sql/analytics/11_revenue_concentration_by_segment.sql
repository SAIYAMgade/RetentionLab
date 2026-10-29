-- Query 11: Revenue Concentration and Top 5% Concentration by Segment
-- Business Question: How concentrated is platform revenue across customer tiers and segments?
-- Grain: One row per customer_segment

WITH segment_totals AS (
    SELECT 
        c.customer_segment,
        COUNT(DISTINCT c.customer_id) AS total_customers_in_segment,
        SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END) AS segment_revenue
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.customer_segment
),
customer_ranks AS (
    SELECT 
        c.customer_id,
        c.customer_segment,
        SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END) AS customer_spend,
        NTILE(20) OVER (PARTITION BY c.customer_segment ORDER BY SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END) DESC) AS ventile_rank
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.customer_id, c.customer_segment
),
top_5_pct AS (
    SELECT 
        customer_segment,
        SUM(customer_spend) AS top_5_pct_spend
    FROM customer_ranks
    WHERE ventile_rank = 1  -- Top 5% of customers in segment
    GROUP BY customer_segment
)
SELECT 
    st.customer_segment,
    st.total_customers_in_segment,
    ROUND(st.segment_revenue, 2) AS total_segment_revenue,
    ROUND(t5.top_5_pct_spend, 2) AS top_5_pct_revenue,
    ROUND((t5.top_5_pct_spend / NULLIF(st.segment_revenue, 0)) * 100.0, 2) AS top_5_pct_revenue_share
FROM segment_totals st
LEFT JOIN top_5_pct t5 ON st.customer_segment = t5.customer_segment
ORDER BY total_segment_revenue DESC;
