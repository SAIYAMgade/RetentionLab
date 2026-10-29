"""
Automated tests for reporting assets, Power BI exports, and Excel workbook.
"""

from pathlib import Path
import openpyxl
import pytest
from retentionlab.config.settings import settings


def test_excel_workbook_structure():
    """Verify that generated Excel workbook exists and contains all 5 required sheets."""
    excel_path = settings.root_dir / "data" / "exports" / "RetentionLab_Retention_Action_Workbook.xlsx"
    assert excel_path.exists(), f"Excel workbook not found at {excel_path}"

    wb = openpyxl.load_workbook(excel_path, read_only=True)
    expected_sheets = [
        "Executive Summary",
        "Prioritized Customers",
        "Full Risk Scores",
        "Feature Dictionary",
        "Model Metrics",
    ]
    for s in expected_sheets:
        assert s in wb.sheetnames, f"Missing required sheet: {s}"


def test_powerbi_tables_exist():
    """Verify that all 7 star-schema Power BI tables exist."""
    pbi_dir = settings.root_dir / "dashboards" / "powerbi" / "data"
    required_tables = [
        "CUSTOMER_DIMENSION.csv",
        "DATE_DIMENSION.csv",
        "TRANSACTION_FACT.csv",
        "CUSTOMER_SNAPSHOT_FACT.csv",
        "CUSTOMER_RISK_FACT.csv",
        "RETENTION_ACTION_FACT.csv",
        "MODEL_RUN_DIMENSION.csv",
    ]
    for tbl in required_tables:
        p = pbi_dir / tbl
        assert p.exists(), f"Missing Power BI table: {tbl}"
