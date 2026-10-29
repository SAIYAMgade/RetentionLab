"""
RetentionLab Data Quality Validation Engine.
Runs SQL integrity checks and DataFrame-level schema and range assertions.
"""

from typing import Dict, List
import pandas as pd
from retentionlab.config.settings import settings
from retentionlab.database.connection import execute_query, get_engine


def run_sql_quality_checks() -> pd.DataFrame:
    """Execute SQL integrity suite and return results table."""
    sql_path = settings.root_dir / "sql" / "validation" / "01_data_quality_checks.sql"
    with open(sql_path, "r", encoding="utf-8") as f:
        query = f.read()

    results_df = execute_query(query)
    return results_df


def validate_source_dataframes(tables: Dict[str, pd.DataFrame]) -> List[str]:
    """Perform in-memory assertions on raw tables; returns list of error messages."""
    errors = []

    # 1. Transactions count >= 97,000
    txns = tables.get("transactions")
    if txns is None or len(txns) < 97000:
        errors.append(f"Transactions record count {len(txns) if txns is not None else 0} < 97,000 required.")

    # 2. Customers uniqueness
    custs = tables.get("customers")
    if custs is not None and custs["customer_id"].duplicated().any():
        errors.append("Customer IDs contain duplicate entries.")

    # 3. Product price validity
    prods = tables.get("products")
    if prods is not None and (prods["unit_price"] <= 0).any():
        errors.append("Found non-positive product unit prices.")

    # 4. Null checks
    if custs is not None and custs["signup_date"].isnull().any():
        errors.append("Found null signup_date in customers table.")

    return errors
