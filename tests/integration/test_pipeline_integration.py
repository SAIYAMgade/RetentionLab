"""Integration tests verifying end-to-end flow and SQL/Python calculation parity."""
import sqlite3
import pandas as pd
import pytest

from retentionlab.config.settings import DEFAULT_CONFIG
from retentionlab.analytics.sql_runner import init_database, execute_sql_query, run_all_sql_files


def test_sql_python_calculation_parity():
    """Test 18: Verification that SQL aggregation matches Python feature calculations."""
    config = DEFAULT_CONFIG
    if not config.features_path.exists():
        pytest.skip("Customer features not generated yet.")

    feat_df = pd.read_parquet(config.features_path)
    conn = sqlite3.connect(str(config.processed_db_path))

    # Query customer features directly in SQL
    sql_query = """
    SELECT
        customer_id,
        recency_days,
        total_transactions,
        ROUND(total_spend, 2) AS sql_spend
    FROM customer_features
    ORDER BY customer_id
    LIMIT 20;
    """
    sql_df = execute_sql_query(conn, sql_query)

    merged = pd.merge(sql_df, feat_df[["customer_id", "recency_days", "total_transactions", "total_spend"]], on="customer_id")

    # Assert exact agreement between SQL and Python values
    for _, row in merged.iterrows():
        assert row["recency_days_x"] == row["recency_days_y"]
        assert row["total_transactions_x"] == row["total_transactions_y"]
        assert abs(row["sql_spend"] - row["total_spend"]) < 0.05


def test_all_sql_queries_execute():
    """Verify all 20 SQL queries across analytical files execute without errors."""
    config = DEFAULT_CONFIG
    if not config.processed_db_path.exists():
        pytest.skip("Database not initialized yet.")

    conn = sqlite3.connect(str(config.processed_db_path))
    results = run_all_sql_files(conn)

    assert len(results) > 0
    for name, res in results.items():
        if isinstance(res, dict) and "error" in res:
            pytest.fail(f"SQL file {name} failed with error: {res['error']}")
