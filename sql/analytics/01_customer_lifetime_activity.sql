-- Query 01: Customer Lifetime Activity
-- Business Question: What is each customer's lifetime spending, transaction count, tenure, and average order value?
-- Grain: One row per customer (customer_id)

SELECT 
    c.customer_id,
    c.customer_segment,
    c.acquisition_channel,
    c.signup_date,
    c.tenure_days,
    COUNT(t.transaction_id) AS lifetime_transactions,
    COALESCE(SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END), 0.00) AS lifetime_net_spend,
    COALESCE(AVG(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE NULL END), 0.00) AS avg_transaction_value,
    MIN(t.transaction_date) AS first_transaction_date,
    MAX(t.transaction_date) AS last_transaction_date
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY 
    c.customer_id,
    c.customer_segment,
    c.acquisition_channel,
    c.signup_date,
    c.tenure_days
ORDER BY lifetime_net_spend DESC;
