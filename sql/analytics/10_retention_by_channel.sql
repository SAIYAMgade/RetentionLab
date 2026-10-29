-- Query 10: Retention and Churn Rates by Acquisition Channel
-- Business Question: Which marketing channels deliver the highest retention rates and customer lifetime spend?
-- Grain: One row per acquisition_channel

WITH channel_stats AS (
    SELECT 
        c.acquisition_channel,
        COUNT(DISTINCT c.customer_id) AS total_acquired_customers,
        -- Churn definition: No successful transactions in prediction horizon (2026-04-01 to 2026-05-31)
        COUNT(DISTINCT CASE 
            WHEN NOT EXISTS (
                SELECT 1 FROM transactions t2 
                WHERE t2.customer_id = c.customer_id 
                  AND t2.transaction_date > '2026-04-01' 
                  AND t2.transaction_date <= '2026-05-31' 
                  AND t2.transaction_status = 'Success'
            ) AND c.tenure_days >= 30 THEN c.customer_id 
        END) AS churned_customers,
        ROUND(SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END), 2) AS total_channel_revenue
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.acquisition_channel
)
SELECT 
    acquisition_channel,
    total_acquired_customers,
    churned_customers,
    ROUND((CAST(churned_customers AS FLOAT) / total_acquired_customers) * 100.0, 2) AS churn_rate_pct,
    ROUND(100.0 - ((CAST(churned_customers AS FLOAT) / total_acquired_customers) * 100.0), 2) AS retention_rate_pct,
    total_channel_revenue,
    ROUND(total_channel_revenue / total_acquired_customers, 2) AS revenue_per_customer
FROM channel_stats
ORDER BY retention_rate_pct DESC;
