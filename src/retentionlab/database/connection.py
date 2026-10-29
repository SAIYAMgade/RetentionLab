"""
RetentionLab Database Connection & Schema Management.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from retentionlab.config.settings import settings

_ENGINE: Optional[Engine] = None


def get_engine(db_url: Optional[str] = None) -> Engine:
    """Return a singleton SQLAlchemy engine."""
    global _ENGINE
    if _ENGINE is None or db_url is not None:
        url = db_url or settings.database.connection_url
        _ENGINE = create_engine(url, echo=settings.database.echo)
    return _ENGINE


def init_db(engine: Optional[Engine] = None, schema_path: Optional[Path] = None) -> None:
    """Initialize database tables using the SQL schema definition."""
    eng = engine or get_engine()
    if schema_path is None:
        schema_path = settings.root_dir / "sql" / "schema" / "01_create_tables.sql"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Split by semicolon to execute DDL statements cleanly
    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
    with eng.connect() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()


def execute_query(query: str, params: Optional[dict] = None, engine: Optional[Engine] = None) -> pd.DataFrame:
    """Execute a SQL query and return results as a pandas DataFrame."""
    eng = engine or get_engine()
    with eng.connect() as conn:
        return pd.read_sql_query(text(query), conn, params=params)


def execute_script(script_path: Path, engine: Optional[Engine] = None) -> None:
    """Execute a SQL script containing multiple statements."""
    eng = engine or get_engine()
    with open(script_path, "r", encoding="utf-8") as f:
        sql = f.read()
    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
    with eng.connect() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()


def save_dataframe_to_table(df: pd.DataFrame, table_name: str, if_exists: str = "append", engine: Optional[Engine] = None) -> int:
    """Insert DataFrame records into a SQL table and return inserted row count."""
    eng = engine or get_engine()
    df.to_sql(table_name, eng, if_exists=if_exists, index=False)
    return len(df)
