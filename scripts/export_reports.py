"""
RetentionLab Reports & Business Intelligence Export Script.
Exports star-schema Power BI tables and generates the formatted Excel Retention-Action Workbook.
"""

import sys
import time
from pathlib import Path
import pandas as pd
from retentionlab.config.settings import settings
from retentionlab.reporting.excel_generator import ExcelReportGenerator
from retentionlab.reporting.powerbi_exporter import PowerBIExporter


def run_exports() -> None:
    print("=== RetentionLab: Generating Business Intelligence & Excel Assets ===")
    t0 = time.time()

    # 1. Power BI Star Schema Tables
    pbi_exporter = PowerBIExporter()
    exported_tables = pbi_exporter.export_star_schema()
    print("\n--- Power BI Star-Schema Tables Exported ---")
    for tbl, path in exported_tables.items():
        print(f"  * {tbl:<24} -> {Path(path).name}")

    # 2. Formatted Excel Retention-Action Workbook
    scores_path = settings.root_dir / "data" / "processed" / "customer_prioritization.csv"
    comp_path = settings.root_dir / "models" / "model_comparison.csv"

    if not scores_path.exists():
        print(f"Error: Scored dataset not found at {scores_path}. Run scoring first.")
        sys.exit(1)

    scored_df = pd.read_csv(scores_path)
    model_comp_df = pd.read_csv(comp_path) if comp_path.exists() else pd.DataFrame()

    print("\nBuilding professional Excel Retention-Action Workbook...")
    excel_gen = ExcelReportGenerator()
    wb_path = excel_gen.generate_workbook(scored_df, model_comp_df)
    print(f"  * Excel Workbook saved -> {wb_path}")

    print(f"\n[SUCCESS] Reporting assets generated in {time.time() - t0:.2f}s.\n")


if __name__ == "__main__":
    run_exports()
