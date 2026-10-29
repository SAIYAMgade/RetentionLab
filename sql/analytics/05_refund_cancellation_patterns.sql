-- Query 05: Refund and Cancellation Patterns
-- Business Question: What are refund rates and cancellation frequencies across product categories and customer segments?
-- Grain: One row per customer_segment and product_category

SELECT 
    c.customer_segment,
    p.product_category,
    COUNT(t.transaction_id) AS total_order_count,
    ROUND(SUM(t.transaction_amount), 2) AS gross_booked_amount,
    COUNT(CASE WHEN t.transaction_status = 'Refunded' THEN 1 END) AS refunded_order_count,
    ROUND(SUM(t.refund_amount), 2) AS total_refunded_amount,
    ROUND((SUM(t.refund_amount) / NULLIF(SUM(t.transaction_amount), 0)) * 100.0, 2) AS refund_value_rate_pct,
    COUNT(CASE WHEN t.transaction_status = 'Cancelled' THEN 1 END) AS cancelled_order_count,
    ROUND((CAST(COUNT(CASE WHEN t.transaction_status = 'Cancelled' THEN 1 END) AS FLOAT) / COUNT(t.transaction_id)) * 100.0, 2) AS cancellation_rate_pct
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
GROUP BY c.customer_segment, p.product_category
ORDER BY c.customer_segment, total_refunded_amount DESC;
