"""
RetentionLab Page 8: Business Reports & BI Exports.
Download operational Excel workbooks and Power BI reporting packages.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
from app.components.ui import inject_custom_css, render_header, render_kpi
from retentionlab.config.settings import settings

st.set_page_config(page_title="Business Reports | RetentionLab", page_icon="📁", layout="wide")
inject_custom_css()

render_header(
    title="Business Reports & BI Export Center",
    subtitle="Download Executive Excel Workbooks, Operational Worklists & Power BI Reporting Packages",
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📗 Excel Retention-Action Workbook")
    st.markdown(
        """
        A formatted multi-worksheet Excel report generated using `openpyxl`:
        - **Executive Summary**: Portfolio KPIs, risk tier breakdown, and methodology notice.
        - **Prioritized Customers**: Top 15% actionable worklist with conditional formatting and auto-filters.
        - **Full Risk Scores**: Complete scoring table across all 4,850 eligible accounts.
        - **Feature Dictionary**: Full documentation of all 44 behavioral features.
        - **Model Metrics**: Benchmark comparison across candidate models.
        """
    )
    excel_path = settings.root_dir / "data" / "exports" / "RetentionLab_Retention_Action_Workbook.xlsx"
    if excel_path.exists():
        with open(excel_path, "rb") as f:
            st.download_button(
                label="📥 Download Excel Workbook (.xlsx)",
                data=f,
                file_name="RetentionLab_Retention_Action_Workbook.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.warning("Excel workbook not found. Run 'scripts/export_reports.py' to generate.")

with col2:
    st.markdown("### 📊 Power BI Reporting Package")
    st.markdown(
        """
        Ready-to-import star schema tables and technical DAX specifications:
        - `CUSTOMER_DIMENSION.csv` & `DATE_DIMENSION.csv`
        - `TRANSACTION_FACT.csv` (>104,000 rows)
        - `CUSTOMER_RISK_FACT.csv` & `RETENTION_ACTION_FACT.csv`
        - Certified DAX measures and page layout guides.
        """
    )
    pbi_dir = settings.root_dir / "dashboards" / "powerbi" / "data"
    pbi_cust = pbi_dir / "CUSTOMER_RISK_FACT.csv"
    if pbi_cust.exists():
        with open(pbi_cust, "rb") as f:
            st.download_button(
                label="📥 Download Power BI Customer Risk Fact (CSV)",
                data=f,
                file_name="CUSTOMER_RISK_FACT.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.warning("Power BI tables not found. Run 'scripts/export_reports.py' to generate.")

st.markdown("---")

st.markdown("### 📋 Power BI Certified DAX Measures Preview")
dax_path = settings.root_dir / "dashboards" / "powerbi" / "dax_measures.md"
if dax_path.exists():
    with open(dax_path, "r", encoding="utf-8") as f:
        dax_text = f.read()
    st.markdown(dax_text)
