-- ============================================================================
-- RetentionLab: Cohort Analysis & Retention Trends (Queries 6, 7, 19)
-- ============================================================================

-- Query 6: Customer Acquisition Cohort Matrix
-- Business Question: When did customers join, and how many repeat purchases did each cohort generate?
WITH customer_cohort_base AS (
    SELECT
        customer_id,
        MIN(SUBSTR(transaction_date_str, 1, 7)) AS cohort_month
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        SUBSTR(t.transaction_date_str, 1, 7) AS activity_month,
        COUNT(DISTINCT t.customer_id) AS active_customers,
        ROUND(SUM(t.transaction_amount), 2) AS monthly_cohort_spend
    FROM cleaned_transactions t
    JOIN customer_cohort_base c ON t.customer_id = c.customer_id
    WHERE t.transaction_type = 'purchase'
      AND t.transaction_status = 'completed'
      AND t.transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY c.cohort_month, SUBSTR(t.transaction_date_str, 1, 7)
)
SELECT
    cohort_month,
    activity_month,
    active_customers,
    monthly_cohort_spend
FROM cohort_activity
ORDER BY cohort_month ASC, activity_month ASC
LIMIT 100;


-- Query 7: Monthly Retention Trends
-- Business Question: What is the month-over-month active customer count and repeat customer rate?
WITH monthly_active_cte AS (
    SELECT
        SUBSTR(transaction_date_str, 1, 7) AS year_month,
        COUNT(DISTINCT customer_id) AS active_customer_count,
        COUNT(transaction_id) AS total_orders,
        ROUND(SUM(transaction_amount), 2) AS gross_revenue
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY SUBSTR(transaction_date_str, 1, 7)
)
SELECT
    year_month,
    active_customer_count,
    total_orders,
    gross_revenue,
    LAG(active_customer_count, 1) OVER (ORDER BY year_month ASC) AS prev_month_active,
    ROUND(
        (active_customer_count - LAG(active_customer_count, 1) OVER (ORDER BY year_month ASC)) * 100.0 /
        NULLIF(LAG(active_customer_count, 1) OVER (ORDER BY year_month ASC), 0),
        2
    ) AS mom_active_growth_pct
FROM monthly_active_cte
ORDER BY year_month ASC;


-- Query 19: Retention Cohort Comparisons (Quarterly Cohorts)
-- Business Question: How do earlier quarterly cohorts compare against later cohorts in terms of 90-day retention and value?
WITH quarterly_cohort_cte AS (
    SELECT
        customer_id,
        CASE
            WHEN MIN(transaction_timestamp) < '2022-07-01' THEN '2022-H1 Cohort'
            WHEN MIN(transaction_timestamp) < '2023-01-01' THEN '2022-H2 Cohort'
            WHEN MIN(transaction_timestamp) < '2023-07-01' THEN '2023-H1 Cohort'
            ELSE '2023-H2 Cohort'
        END AS acquisition_cohort,
        COUNT(transaction_id) AS total_purchases,
        SUM(transaction_amount) AS total_spend
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
)
SELECT
    acquisition_cohort,
    COUNT(customer_id) AS cohort_size,
    ROUND(AVG(total_purchases), 2) AS avg_purchases_per_customer,
    ROUND(AVG(total_spend), 2) AS avg_spend_per_customer,
    ROUND(SUM(total_spend), 2) AS total_cohort_revenue
FROM quarterly_cohort_cte
GROUP BY acquisition_cohort
ORDER BY acquisition_cohort ASC;
