"""Database loader and SQL analytics query execution runner."""
import sqlite3
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from retentionlab.config.settings import DEFAULT_CONFIG, PipelineConfig, SQL_DIR


def init_database(
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    features_df: pd.DataFrame = None,
    target_df: pd.DataFrame = None,
    predictions_df: pd.DataFrame = None,
    prioritization_df: pd.DataFrame = None,
    config: PipelineConfig = DEFAULT_CONFIG
) -> sqlite3.Connection:
    """Initialize SQLite database with schema and load all analytical tables."""
    db_path = config.processed_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))

    # Read and execute table creation DDL
    ddl_path = SQL_DIR / "schema" / "01_create_tables.sql"
    if ddl_path.exists():
        with open(ddl_path, "r", encoding="utf-8") as f:
            ddl_sql = f.read()
            conn.executescript(ddl_sql)

    # Load raw transactions
    if raw_df is not None and not raw_df.empty:
        raw_df.to_sql("raw_transactions", conn, if_exists="replace", index=False)

    # Load cleaned transactions
    if cleaned_df is not None and not cleaned_df.empty:
        cleaned_to_save = cleaned_df.copy()
        if "transaction_timestamp" in cleaned_to_save.columns:
            cleaned_to_save["transaction_timestamp"] = cleaned_to_save["transaction_timestamp"].astype(str)
        cleaned_to_save.to_sql("cleaned_transactions", conn, if_exists="replace", index=False)

    # Load customer features
    if features_df is not None and not features_df.empty:
        features_df.to_sql("customer_features", conn, if_exists="replace", index=False)

    # Load target labels
    if target_df is not None and not target_df.empty:
        target_df.to_sql("target_labels", conn, if_exists="replace", index=False)

    # Load predictions
    if predictions_df is not None and not predictions_df.empty:
        predictions_df.to_sql("model_predictions", conn, if_exists="replace", index=False)

    # Load prioritization
    if prioritization_df is not None and not prioritization_df.empty:
        prioritization_df.to_sql("customer_prioritization", conn, if_exists="replace", index=False)

    # Create indexes
    idx_path = SQL_DIR / "schema" / "02_create_indexes.sql"
    if idx_path.exists():
        with open(idx_path, "r", encoding="utf-8") as f:
            idx_sql = f.read()
            conn.executescript(idx_sql)

    conn.commit()
    return conn


def execute_sql_query(conn: sqlite3.Connection, query_sql: str) -> pd.DataFrame:
    """Execute arbitrary SQL query and return DataFrame."""
    return pd.read_sql_query(query_sql, conn)


def run_all_sql_files(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Execute all SQL analytical files to verify correctness against real tables."""
    results = {}
    sql_files = list(SQL_DIR.rglob("*.sql"))

    for sf in sql_files:
        if "schema" in str(sf):
            continue
        with open(sf, "r", encoding="utf-8") as f:
            content = f.read()

        # Split multiple queries by semicolon if needed or run individual blocks
        statements = [stmt.strip() for stmt in content.split(";") if stmt.strip() and not stmt.strip().startswith("--")]
        executed_count = 0
        last_df = None

        for stmt in statements:
            # Skip comments-only statements
            lines = [line for line in stmt.split("\n") if not line.strip().startswith("--")]
            clean_stmt = "\n".join(lines).strip()
            if not clean_stmt:
                continue
            try:
                last_df = pd.read_sql_query(clean_stmt, conn)
                executed_count += 1
            except Exception as e:
                # Store error for tracking
                results[f"{sf.stem}_{executed_count}"] = {"error": str(e), "statement": clean_stmt[:80]}
                continue

        results[sf.stem] = {
            "status": "success" if executed_count > 0 else "empty",
            "executed_queries": executed_count,
            "last_output_rows": len(last_df) if last_df is not None else 0
        }

    return results
