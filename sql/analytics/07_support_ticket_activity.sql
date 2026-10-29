-- Query 07: Support Ticket and Complaint Activity
-- Business Question: How does customer service friction (complaint rates, CSAT) vary by customer segment?
-- Grain: One row per customer_segment and ticket_type

SELECT 
    c.customer_segment,
    s.ticket_type,
    COUNT(s.ticket_id) AS total_tickets,
    COUNT(DISTINCT s.customer_id) AS distinct_customers_contacting_support,
    ROUND(AVG(s.satisfaction_score), 2) AS avg_customer_satisfaction_csat,
    COUNT(CASE WHEN s.satisfaction_score <= 2 THEN 1 END) AS negative_csat_tickets_count,
    ROUND((CAST(COUNT(CASE WHEN s.satisfaction_score <= 2 THEN 1 END) AS FLOAT) / COUNT(s.ticket_id)) * 100.0, 2) AS negative_csat_pct
FROM support_tickets s
JOIN customers c ON s.customer_id = c.customer_id
GROUP BY c.customer_segment, s.ticket_type
ORDER BY c.customer_segment, total_tickets DESC;
