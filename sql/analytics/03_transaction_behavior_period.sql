-- Query 03: Transaction Behavior by Time Period
-- Business Question: What are monthly GMV, transaction volume, active purchasing customer counts, and average order value?
-- Grain: One row per month (calendar_month)

SELECT 
    STRFTIME('%Y-%m', t.transaction_date) AS calendar_month,
    COUNT(t.transaction_id) AS total_transactions,
    COUNT(DISTINCT t.customer_id) AS active_purchasing_customers,
    ROUND(SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END), 2) AS gross_merchandise_value,
    ROUND(AVG(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE NULL END), 2) AS avg_transaction_value,
    ROUND(SUM(t.refund_amount), 2) AS total_refunds,
    ROUND(SUM(t.discount_amount), 2) AS total_discounts
FROM transactions t
GROUP BY STRFTIME('%Y-%m', t.transaction_date)
ORDER BY calendar_month ASC;
