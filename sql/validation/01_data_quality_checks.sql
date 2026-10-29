-- RetentionLab Relational Integrity & Data Quality Validation Suite
-- Each check outputs check_name, records_failed, status ('PASS' or 'FAIL')

-- Check 1: Primary key uniqueness in customers
SELECT 
    'customers_primary_key_uniqueness' AS check_name,
    COUNT(*) - COUNT(DISTINCT customer_id) AS records_failed,
    CASE WHEN COUNT(*) = COUNT(DISTINCT customer_id) THEN 'PASS' ELSE 'FAIL' END AS status
FROM customers

UNION ALL

-- Check 2: Primary key uniqueness in transactions
SELECT 
    'transactions_primary_key_uniqueness' AS check_name,
    COUNT(*) - COUNT(DISTINCT transaction_id) AS records_failed,
    CASE WHEN COUNT(*) = COUNT(DISTINCT transaction_id) THEN 'PASS' ELSE 'FAIL' END AS status
FROM transactions

UNION ALL

-- Check 3: Orphan transactions missing valid customer reference
SELECT 
    'orphan_transactions_check' AS check_name,
    COUNT(*) AS records_failed,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM transactions t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL

-- Check 4: Negative or impossible transaction amounts
SELECT 
    'non_negative_transaction_amounts' AS check_name,
    COUNT(*) AS records_failed,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM transactions
WHERE transaction_amount <= 0

UNION ALL

-- Check 5: Transaction dates occurring strictly before customer signup
SELECT 
    'temporal_order_txn_after_signup' AS check_name,
    COUNT(*) AS records_failed,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date < c.signup_date

UNION ALL

-- Check 6: CSAT scores within valid bounds [1, 5]
SELECT 
    'csat_score_bounds_validity' AS check_name,
    COUNT(*) AS records_failed,
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM support_tickets
WHERE satisfaction_score IS NOT NULL AND (satisfaction_score < 1 OR satisfaction_score > 5);
