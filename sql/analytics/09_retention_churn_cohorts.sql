-- Query 09: Customer Retention and Churn Cohorts
-- Business Question: What are month-by-month cohort retention curves for customers by signup month?
-- Grain: One row per signup_cohort_month and activity_month_offset

WITH customer_cohorts AS (
    SELECT 
        customer_id,
        SUBSTR(signup_date, 1, 7) AS signup_cohort
    FROM customers
),
customer_monthly_activity AS (
    SELECT DISTINCT
        customer_id,
        SUBSTR(transaction_date, 1, 7) AS activity_month
    FROM transactions
    WHERE transaction_status = 'Success'
),
cohort_sizes AS (
    SELECT 
        signup_cohort,
        COUNT(customer_id) AS cohort_base_size
    FROM customer_cohorts
    GROUP BY signup_cohort
),
cohort_retention AS (
    SELECT 
        cc.signup_cohort,
        cma.activity_month,
        -- Calculate month index offset from YYYY-MM strings
        (CAST(SUBSTR(cma.activity_month, 1, 4) AS INTEGER) - CAST(SUBSTR(cc.signup_cohort, 1, 4) AS INTEGER)) * 12 +
        (CAST(SUBSTR(cma.activity_month, 6, 2) AS INTEGER) - CAST(SUBSTR(cc.signup_cohort, 6, 2) AS INTEGER)) AS month_offset,
        COUNT(DISTINCT cc.customer_id) AS active_cohort_customers
    FROM customer_cohorts cc
    JOIN customer_monthly_activity cma ON cc.customer_id = cma.customer_id
    GROUP BY cc.signup_cohort, cma.activity_month
)
SELECT 
    cr.signup_cohort,
    cs.cohort_base_size,
    cr.month_offset,
    cr.active_cohort_customers,
    ROUND((CAST(cr.active_cohort_customers AS FLOAT) / cs.cohort_base_size) * 100.0, 2) AS retention_rate_pct
FROM cohort_retention cr
JOIN cohort_sizes cs ON cr.signup_cohort = cs.signup_cohort
WHERE cr.month_offset >= 0
ORDER BY cr.signup_cohort ASC, cr.month_offset ASC;
