-- Query 02: Recency, Frequency, and Monetary (RFM) Analysis
-- Business Question: How do customers rank across standard RFM quantiles at the snapshot date?
-- Grain: One row per customer (customer_id)

WITH customer_rfm_raw AS (
    SELECT 
        c.customer_id,
        c.customer_segment,
        -- Recency: Days between snapshot date (2026-04-01) and latest transaction
        CAST((JULIANDAY('2026-04-01') - JULIANDAY(MAX(t.transaction_date))) AS INTEGER) AS recency_days,
        COUNT(CASE WHEN t.transaction_date <= '2026-04-01' AND t.transaction_status = 'Success' THEN t.transaction_id END) AS frequency_count,
        COALESCE(SUM(CASE WHEN t.transaction_date <= '2026-04-01' AND t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END), 0.00) AS monetary_total
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.customer_id, c.customer_segment
),
customer_rfm_scored AS (
    SELECT 
        customer_id,
        customer_segment,
        recency_days,
        frequency_count,
        monetary_total,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,     -- Lower recency days = higher score
        NTILE(4) OVER (ORDER BY frequency_count ASC) AS f_score,  -- Higher frequency = higher score
        NTILE(4) OVER (ORDER BY monetary_total ASC) AS m_score    -- Higher spend = higher score
    FROM customer_rfm_raw
)
SELECT 
    customer_id,
    customer_segment,
    recency_days,
    frequency_count,
    monetary_total,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score) AS composite_rfm_score
FROM customer_rfm_scored
ORDER BY composite_rfm_score DESC;
