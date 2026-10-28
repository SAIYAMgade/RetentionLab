-- ============================================================================
-- RetentionLab: Customer Segmentation & Reporting Views (Queries 8, 10, 18, 20)
-- ============================================================================

-- Query 8: Customer Inactivity Analysis
-- Business Question: What proportion of eligible customers experienced complete inactivity during the 90-day future horizon?
SELECT
    CASE WHEN is_inactive = 1 THEN 'Inactive (0 Future Purchases)' ELSE 'Active (>=1 Future Purchases)' END AS future_status,
    COUNT(customer_id) AS customer_count,
    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM target_labels), 2) AS pct_of_eligible_base,
    ROUND(AVG(future_purchases), 2) AS avg_future_purchases
FROM target_labels
GROUP BY is_inactive;


-- Query 10: Strategic Customer Segmentation
-- Business Question: How are customers distributed across behavioral segments based on historical recency and spend?
WITH rfm_scored AS (
    SELECT
        customer_id,
        recency_days,
        total_transactions,
        total_spend,
        CASE
            WHEN recency_days <= 30 AND total_spend >= 1500 THEN 'Champions (Active & High Spend)'
            WHEN recency_days <= 60 AND total_transactions >= 5 THEN 'Loyal Customers (Recent & Frequent)'
            WHEN recency_days <= 60 THEN 'Promising / Developing'
            WHEN recency_days <= 120 AND total_spend >= 1000 THEN 'High-Value At-Risk (Needs Urgent Contact)'
            WHEN recency_days <= 120 THEN 'Warming Inactive (At-Risk)'
            ELSE 'Lapsed / Dormant'
        END AS strategic_segment
    FROM customer_features
)
SELECT
    strategic_segment,
    COUNT(customer_id) AS customer_count,
    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM customer_features), 2) AS segment_share_pct,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(total_transactions), 1) AS avg_orders,
    ROUND(AVG(total_spend), 2) AS avg_total_spend,
    ROUND(SUM(total_spend), 2) AS aggregate_segment_spend
FROM rfm_scored
GROUP BY strategic_segment
ORDER BY aggregate_segment_spend DESC;


-- Query 18: Customer Prioritization Table
-- Business Question: Which top 50 customers present the highest financial risk of inactivity requiring immediate outreach?
SELECT
    customer_id,
    risk_score,
    risk_tier,
    monetary_tier,
    priority_segment,
    recency_days,
    transaction_frequency,
    total_spend,
    primary_risk_driver,
    recommended_action,
    action_channel
FROM customer_prioritization
WHERE risk_tier = 'High Risk'
ORDER BY total_spend DESC, risk_score DESC
LIMIT 50;


-- Query 20: Executive Business Reporting Summary View
-- Business Question: What is the consolidated executive overview of customer base size, at-risk exposure, and monetary concentration?
SELECT
    COUNT(p.customer_id) AS total_customers_evaluated,
    COUNT(CASE WHEN p.risk_tier = 'High Risk' THEN 1 END) AS high_risk_customer_count,
    ROUND(COUNT(CASE WHEN p.risk_tier = 'High Risk' THEN 1 END) * 100.0 / COUNT(p.customer_id), 2) AS high_risk_pct,
    ROUND(SUM(p.total_spend), 2) AS total_customer_portfolio_value,
    ROUND(SUM(CASE WHEN p.risk_tier = 'High Risk' THEN p.total_spend ELSE 0 END), 2) AS high_risk_spend_exposure,
    ROUND(
        SUM(CASE WHEN p.risk_tier = 'High Risk' THEN p.total_spend ELSE 0 END) * 100.0 /
        NULLIF(SUM(p.total_spend), 0),
        2
    ) AS high_risk_revenue_share_pct
FROM customer_prioritization p;
