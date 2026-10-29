-- Query 08: Customer Engagement Trends
-- Business Question: What are weekly platform login and feature interaction volumes by activity type?
-- Grain: One row per calendar_week and activity_type

SELECT 
    STRFTIME('%Y-W%W', a.activity_date) AS calendar_week,
    a.activity_type,
    COUNT(a.activity_id) AS total_events,
    COUNT(DISTINCT a.customer_id) AS weekly_active_customers
FROM customer_activity a
GROUP BY STRFTIME('%Y-W%W', a.activity_date), a.activity_type
ORDER BY calendar_week ASC, total_events DESC;
