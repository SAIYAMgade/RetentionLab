-- ============================================================================
-- RetentionLab: Customer RFM & Lifetime Summaries (Queries 1, 2, 3, 4, 14)
-- ============================================================================

-- Query 1 & 14: Customer Lifetime & Transaction Summaries
-- Business Question: What is the lifetime activity, first/last purchase date, and gross value for each customer?
WITH customer_lifetime_base AS (
    SELECT
        customer_id,
        MIN(transaction_timestamp) AS first_transaction_dt,
        MAX(transaction_timestamp) AS last_transaction_dt,
        COUNT(CASE WHEN transaction_type = 'purchase' AND transaction_status = 'completed' THEN 1 END) AS lifetime_completed_purchases,
        SUM(CASE WHEN transaction_type = 'purchase' AND transaction_status = 'completed' THEN transaction_amount ELSE 0 END) AS lifetime_gross_spend,
        SUM(CASE WHEN transaction_type = 'refund' AND transaction_status = 'completed' THEN transaction_amount ELSE 0 END) AS lifetime_refund_amount,
        COUNT(DISTINCT product_category) AS distinct_categories_explored,
        COUNT(DISTINCT channel) AS distinct_channels_used
    FROM cleaned_transactions
    WHERE transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
)
SELECT
    customer_id,
    first_transaction_dt,
    last_transaction_dt,
    lifetime_completed_purchases,
    ROUND(lifetime_gross_spend, 2) AS lifetime_gross_spend,
    ROUND(lifetime_refund_amount, 2) AS lifetime_refund_amount,
    ROUND(lifetime_gross_spend + lifetime_refund_amount, 2) AS lifetime_net_spend,
    distinct_categories_explored,
    distinct_channels_used
FROM customer_lifetime_base
ORDER BY lifetime_gross_spend DESC
LIMIT 50;


-- Query 2: Transaction Frequency by Customer
-- Business Question: How frequently do customers purchase, and what are the customer percentiles?
WITH customer_frequency_cte AS (
    SELECT
        customer_id,
        COUNT(transaction_id) AS purchase_count,
        NTILE(5) OVER (ORDER BY COUNT(transaction_id) DESC) AS frequency_quintile
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
)
SELECT
    frequency_quintile,
    COUNT(customer_id) AS customer_count,
    MIN(purchase_count) AS min_purchases,
    ROUND(AVG(purchase_count), 2) AS avg_purchases,
    MAX(purchase_count) AS max_purchases
FROM customer_frequency_cte
GROUP BY frequency_quintile
ORDER BY frequency_quintile ASC;


-- Query 3: Recency Calculations
-- Business Question: How many days have elapsed since each customer's last purchase relative to cutoff date (2023-12-31)?
WITH customer_recency_cte AS (
    SELECT
        customer_id,
        MAX(transaction_timestamp) AS last_purchase_time,
        ROUND(JULIANDAY('2023-12-31 23:59:59') - JULIANDAY(MAX(transaction_timestamp))) AS days_since_last_purchase
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
)
SELECT
    CASE
        WHEN days_since_last_purchase <= 30 THEN '01. Active (0-30 days)'
        WHEN days_since_last_purchase <= 60 THEN '02. Recent (31-60 days)'
        WHEN days_since_last_purchase <= 90 THEN '03. Warming (61-90 days)'
        WHEN days_since_last_purchase <= 180 THEN '04. Dormant (91-180 days)'
        ELSE '05. Inactive (>180 days)'
    END AS recency_bucket,
    COUNT(customer_id) AS customer_count,
    ROUND(AVG(days_since_last_purchase), 1) AS avg_days_recency
FROM customer_recency_cte
GROUP BY 1
ORDER BY 1 ASC;


-- Query 4: Monetary Summaries
-- Business Question: What is the distribution of total spend, average order value, and spending tiers across customer segments?
WITH customer_monetary_cte AS (
    SELECT
        customer_id,
        SUM(transaction_amount) AS total_spend,
        AVG(transaction_amount) AS avg_order_value,
        MAX(transaction_amount) AS max_single_order
    FROM cleaned_transactions
    WHERE transaction_type = 'purchase'
      AND transaction_status = 'completed'
      AND transaction_timestamp <= '2023-12-31 23:59:59'
    GROUP BY customer_id
)
SELECT
    CASE
        WHEN total_spend >= 2500 THEN 'Tier 1: High Net Worth ($2500+)'
        WHEN total_spend >= 1000 THEN 'Tier 2: Mid-High ($1000-$2499)'
        WHEN total_spend >= 400 THEN 'Tier 3: Moderate ($400-$999)'
        ELSE 'Tier 4: Occasional/Entry (<$400)'
    END AS monetary_segment,
    COUNT(customer_id) AS customer_count,
    ROUND(SUM(total_spend), 2) AS aggregate_spend,
    ROUND(AVG(avg_order_value), 2) AS avg_basket_size,
    ROUND(AVG(total_spend), 2) AS mean_customer_spend
FROM customer_monetary_cte
GROUP BY 1
ORDER BY aggregate_spend DESC;
