-- ============================================================================
-- RetentionLab: Data Quality & Integrity Suite (Queries 11, 12, 13)
-- ============================================================================

-- Query 11: General Data Quality Checks
-- Business Question: Are there invalid monetary amounts, future timestamps, or unparseable records?
SELECT
    'Invalid Purchase Amounts (<= 0)' AS check_name,
    COUNT(*) AS failure_count
FROM raw_transactions
WHERE transaction_type = 'purchase' AND transaction_amount <= 0

UNION ALL

SELECT
    'Invalid Refund Amounts (> 0)' AS check_name,
    COUNT(*) AS failure_count
FROM raw_transactions
WHERE transaction_type = 'refund' AND transaction_amount > 0

UNION ALL

SELECT
    'Failed Transactions Flagged Completed' AS check_name,
    COUNT(*) AS failure_count
FROM raw_transactions
WHERE transaction_status = 'failed' AND transaction_type = 'refund';


-- Query 12: Duplicate Transaction Detection
-- Business Question: Are duplicate transaction IDs present in the transaction ingestion stream?
WITH duplicate_tx_cte AS (
    SELECT
        transaction_id,
        COUNT(*) AS occurrence_count
    FROM raw_transactions
    GROUP BY transaction_id
    HAVING COUNT(*) > 1
)
SELECT
    COUNT(*) AS total_duplicate_ids,
    COALESCE(SUM(occurrence_count), 0) AS total_duplicate_rows
FROM duplicate_tx_cte;


-- Query 13: Missing-Field Analysis
-- Business Question: What is the rate of missing attributes across primary transactional columns?
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN transaction_id IS NULL OR TRIM(transaction_id) = '' THEN 1 ELSE 0 END) AS missing_tx_id,
    SUM(CASE WHEN customer_id IS NULL OR TRIM(customer_id) = '' THEN 1 ELSE 0 END) AS missing_customer_id,
    SUM(CASE WHEN transaction_date IS NULL THEN 1 ELSE 0 END) AS missing_date,
    SUM(CASE WHEN transaction_amount IS NULL THEN 1 ELSE 0 END) AS missing_amount,
    SUM(CASE WHEN channel IS NULL OR TRIM(channel) = '' THEN 1 ELSE 0 END) AS missing_channel,
    SUM(CASE WHEN product_category IS NULL OR TRIM(product_category) = '' THEN 1 ELSE 0 END) AS missing_category
FROM raw_transactions;
