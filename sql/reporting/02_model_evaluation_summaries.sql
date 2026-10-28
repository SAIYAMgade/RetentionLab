-- ============================================================================
-- RetentionLab: Model Scoring & Evaluation Analysis (Query 17)
-- ============================================================================

-- Query 17: In-Database Model Performance & Risk Decile Calibration
-- Business Question: How well does predicted inactivity probability correlate with actual ground-truth inactivity across deciles?
WITH scored_deciles AS (
    SELECT
        p.customer_id,
        p.model_name,
        p.inactivity_probability,
        t.is_inactive,
        NTILE(10) OVER (ORDER BY p.inactivity_probability DESC) AS risk_decile
    FROM model_predictions p
    JOIN target_labels t ON p.customer_id = t.customer_id
    WHERE p.model_name = 'LogisticRegression'
)
SELECT
    risk_decile,
    COUNT(customer_id) AS customer_count,
    ROUND(MIN(inactivity_probability), 4) AS min_predicted_prob,
    ROUND(AVG(inactivity_probability), 4) AS avg_predicted_prob,
    ROUND(MAX(inactivity_probability), 4) AS max_predicted_prob,
    SUM(is_inactive) AS actual_inactive_customers,
    ROUND(SUM(is_inactive) * 100.0 / COUNT(customer_id), 2) AS actual_inactivity_rate_pct,
    ROUND(
        (SUM(is_inactive) * 100.0 / COUNT(customer_id)) /
        NULLIF((SELECT AVG(is_inactive) * 100.0 FROM target_labels), 0),
        2
    ) AS lift_vs_baseline
FROM scored_deciles
GROUP BY risk_decile
ORDER BY risk_decile ASC;
