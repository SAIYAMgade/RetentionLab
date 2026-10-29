"""
RetentionLab Professional Excel Retention-Action Workbook Generator.
Produces executive and operational workbooks formatted for business teams.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from retentionlab.config.settings import settings
from retentionlab.features.catalog import FEATURE_CATALOG


class ExcelReportGenerator:
    """
    Generates multi-sheet formatted Excel workbook:
    1. Executive Summary
    2. Prioritized Customers
    3. Full Risk Scores
    4. Feature Dictionary
    5. Model Metrics
    """

    def __init__(self, output_path: Optional[Path] = None):
        self.output_path = (
            output_path
            or settings.root_dir / "data" / "exports" / "RetentionLab_Retention_Action_Workbook.xlsx"
        )
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Style definitions (Navy & Teal palette)
        self.navy_fill = PatternFill(start_color="0F2942", end_color="0F2942", fill_type="solid")
        self.teal_fill = PatternFill(start_color="028090", end_color="028090", fill_type="solid")
        self.gray_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        self.header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        self.title_font = Font(name="Calibri", size=16, bold=True, color="0F2942")
        self.subtitle_font = Font(name="Calibri", size=11, italic=True, color="64748B")
        self.bold_font = Font(name="Calibri", size=11, bold=True, color="1E293B")
        self.regular_font = Font(name="Calibri", size=11, color="1E293B")

        # Risk band fills
        self.critical_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        self.high_fill = PatternFill(start_color="FFEDD5", end_color="FFEDD5", fill_type="solid")
        self.mod_fill = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")
        self.low_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")

        thin_side = Side(border_style="thin", color="CBD5E1")
        self.border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    def generate_workbook(
        self,
        scored_df: pd.DataFrame,
        model_comp_df: pd.DataFrame,
    ) -> Path:
        """Create and populate all 5 worksheets with styling, formulas, and auto-filters."""
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # Sheet 1: Executive Summary
        ws1 = wb.create_sheet(title="Executive Summary")
        self._build_executive_summary_sheet(ws1, scored_df, model_comp_df)

        # Sheet 2: Prioritized Customers (Top Operational Cohort)
        ws2 = wb.create_sheet(title="Prioritized Customers")
        self._build_prioritized_customers_sheet(ws2, scored_df)

        # Sheet 3: Full Risk Scores
        ws3 = wb.create_sheet(title="Full Risk Scores")
        self._build_full_scores_sheet(ws3, scored_df)

        # Sheet 4: Feature Dictionary
        ws4 = wb.create_sheet(title="Feature Dictionary")
        self._build_feature_dictionary_sheet(ws4)

        # Sheet 5: Model Metrics
        ws5 = wb.create_sheet(title="Model Metrics")
        self._build_model_metrics_sheet(ws5, model_comp_df)

        wb.save(self.output_path)
        return self.output_path

    def _build_executive_summary_sheet(
        self, ws: openpyxl.worksheet.worksheet.Worksheet, scored_df: pd.DataFrame, model_comp_df: pd.DataFrame
    ) -> None:
        ws.views.sheetView[0].showGridLines = True

        ws["B2"] = "RetentionLab: Customer Retention & Revenue Prioritization"
        ws["B2"].font = self.title_font
        ws["B3"] = f"Executive Portfolio Briefing | Scoring Date: 2026-04-01 | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws["B3"].font = self.subtitle_font

        # KPI Summary Table
        ws["B5"] = "PORTFOLIO CORE METRICS"
        ws["B5"].font = self.bold_font

        total_eligible = len(scored_df)
        top_cohort_count = int(scored_df["is_top_15_percent"].sum())
        total_exposure = scored_df["risk_weighted_exposure"].sum()
        top_exposure = scored_df.loc[scored_df["is_top_15_percent"] == 1, "risk_weighted_exposure"].sum()
        avg_churn_prob = scored_df["churn_probability"].mean()

        kpi_data = [
            ("Eligible Scored Customers", total_eligible, "#,##0"),
            ("Prioritized Review Cohort (Top 15%)", top_cohort_count, "#,##0"),
            ("Top Cohort Share of Total Base", top_cohort_count / total_eligible, "0.0%"),
            ("Portfolio Risk-Weighted Exposure", total_exposure, "$#,##0.00"),
            ("Top Cohort Risk-Weighted Exposure", top_exposure, "$#,##0.00"),
            ("Top Cohort Exposure Concentration", top_exposure / total_exposure, "0.0%"),
            ("Mean Portfolio Churn Probability", avg_churn_prob, "0.0%"),
        ]

        row_idx = 6
        for label, val, num_fmt in kpi_data:
            ws.cell(row=row_idx, column=2, value=label).font = self.regular_font
            c = ws.cell(row=row_idx, column=3, value=val)
            c.font = self.bold_font
            c.number_format = num_fmt
            c.alignment = Alignment(horizontal="right")
            ws.cell(row=row_idx, column=2).border = self.border
            ws.cell(row=row_idx, column=3).border = self.border
            row_idx += 1

        # Risk Band Distribution
        ws["E5"] = "RISK TIER BREAKDOWN"
        ws["E5"].font = self.bold_font

        headers = ["Risk Band", "Customers", "Share", "Exposure Proxy"]
        for c_idx, h in enumerate(headers, start=5):
            cell = ws.cell(row=6, column=c_idx, value=h)
            cell.fill = self.navy_fill
            cell.font = self.header_font
            cell.alignment = Alignment(horizontal="center")
            cell.border = self.border

        band_order = ["Critical Risk", "High Risk", "Moderate Risk", "Low Risk"]
        r_band = 7
        for band in band_order:
            sub = scored_df[scored_df["risk_band"] == band]
            cnt = len(sub)
            pct = cnt / total_eligible if total_eligible > 0 else 0
            exp = sub["risk_weighted_exposure"].sum()

            ws.cell(row=r_band, column=5, value=band).font = self.regular_font
            c1 = ws.cell(row=r_band, column=6, value=cnt)
            c1.number_format = "#,##0"
            c2 = ws.cell(row=r_band, column=7, value=pct)
            c2.number_format = "0.0%"
            c3 = ws.cell(row=r_band, column=8, value=exp)
            c3.number_format = "$#,##0.00"

            for col in range(5, 9):
                ws.cell(row=r_band, column=col).border = self.border

            r_band += 1

        # Limitations & Operational Notice
        notice_row = max(row_idx, r_band) + 2
        ws.cell(row=notice_row, column=2, value="METHODOLOGY & OPERATIONAL GOVERNANCE NOTICE:").font = self.bold_font
        notices = [
            "1. Predictions are probabilistic estimates derived from historical behavioral trends; they do not guarantee churn or retention.",
            "2. 'Risk-Weighted Exposure' = Churn Probability * Annualized Historical Spend. It represents analytical exposure, not guaranteed lost revenue.",
            "3. Actions are advisory suggestions for customer success analysts; interventions require professional review before deployment.",
            "4. Top 15% cohort corresponds to score ranking based on 55% model risk and 45% historical account value weighting.",
        ]
        for i, text in enumerate(notices):
            cell = ws.cell(row=notice_row + 1 + i, column=2, value=text)
            cell.font = self.subtitle_font

        # Column widths
        ws.column_dimensions["B"].width = 36
        ws.column_dimensions["C"].width = 24
        ws.column_dimensions["D"].width = 6
        ws.column_dimensions["E"].width = 20
        ws.column_dimensions["F"].width = 16
        ws.column_dimensions["G"].width = 14
        ws.column_dimensions["H"].width = 22

    def _build_prioritized_customers_sheet(
        self, ws: openpyxl.worksheet.worksheet.Worksheet, scored_df: pd.DataFrame
    ) -> None:
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "A2"

        # Filter to top 15% operational cohort
        top_cohort = scored_df[scored_df["is_top_15_percent"] == 1].copy()
        top_cohort = top_cohort.sort_values("prioritization_score", ascending=False).reset_index(drop=True)

        cols = [
            ("retention_rank", "Rank", "#,##0", 8),
            ("customer_id", "Customer ID", "@", 16),
            ("risk_band", "Risk Band", "@", 16),
            ("churn_probability", "Churn Prob", "0.0%", 12),
            ("historical_value_proxy", "Annualized Spend", "$#,##0.00", 18),
            ("risk_weighted_exposure", "Risk Exposure", "$#,##0.00", 18),
            ("prioritization_score", "Priority Score", "0.000", 14),
            ("top_risk_signals", "Leading Behavioral Risk Signals", "@", 45),
            ("suggested_action", "Recommended Action Category", "@", 28),
            ("recommended_next_step", "Operational Next Step", "@", 50),
        ]

        # Headers
        for col_idx, (_, header, _, width) in enumerate(cols, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = self.navy_fill
            cell.font = self.header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = self.border
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        # Data rows
        for row_idx, row in top_cohort.iterrows():
            excel_row = row_idx + 2
            band = row["risk_band"]
            row_fill = self.critical_fill if band == "Critical Risk" else (
                self.high_fill if band == "High Risk" else (
                    self.mod_fill if band == "Moderate Risk" else self.low_fill
                )
            )

            for col_idx, (col_name, _, num_fmt, _) in enumerate(cols, start=1):
                val = row[col_name]
                cell = ws.cell(row=excel_row, column=col_idx, value=val)
                cell.font = self.regular_font
                cell.border = self.border
                cell.number_format = num_fmt

                if col_name == "risk_band":
                    cell.fill = row_fill
                    cell.alignment = Alignment(horizontal="center")
                elif num_fmt in ["$#,##0.00", "0.0%", "0.000", "#,##0"]:
                    cell.alignment = Alignment(horizontal="right")

        ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(top_cohort)+1}"

    def _build_full_scores_sheet(
        self, ws: openpyxl.worksheet.worksheet.Worksheet, scored_df: pd.DataFrame
    ) -> None:
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "A2"

        cols = [
            ("retention_rank", "Rank", "#,##0", 8),
            ("customer_id", "Customer ID", "@", 16),
            ("risk_band", "Risk Tier", "@", 16),
            ("churn_probability", "Churn Prob", "0.0%", 12),
            ("prioritization_score", "Priority Score", "0.000", 14),
            ("historical_value_proxy", "Annualized Spend", "$#,##0.00", 18),
            ("risk_weighted_exposure", "Risk Exposure", "$#,##0.00", 18),
            ("is_top_15_percent", "Top 15% Cohort", "#,##0", 14),
            ("days_since_last_transaction", "Days Since Txn", "#,##0", 16),
            ("transaction_count_90d", "Txn Count 90d", "#,##0", 14),
            ("total_spend_90d", "Spend 90d", "$#,##0.00", 16),
            ("suggested_action", "Action Category", "@", 26),
        ]

        for col_idx, (_, header, _, width) in enumerate(cols, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = self.navy_fill
            cell.font = self.header_font
            cell.alignment = Alignment(horizontal="center")
            cell.border = self.border
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        for row_idx, row in scored_df.iterrows():
            excel_row = row_idx + 2
            for col_idx, (col_name, _, num_fmt, _) in enumerate(cols, start=1):
                val = row[col_name]
                cell = ws.cell(row=excel_row, column=col_idx, value=val)
                cell.font = self.regular_font
                cell.border = self.border
                cell.number_format = num_fmt

        ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(scored_df)+1}"

    def _build_feature_dictionary_sheet(self, ws: openpyxl.worksheet.worksheet.Worksheet) -> None:
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "A2"

        headers = ["#", "Feature Name", "Category", "Unit", "Calculation Formula", "Business Description", "Risk Direction"]
        widths = [6, 32, 22, 10, 36, 45, 25]

        for col_idx, (h, w) in enumerate(zip(headers, widths), start=1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = self.teal_fill
            cell.font = self.header_font
            cell.alignment = Alignment(horizontal="center")
            cell.border = self.border
            ws.column_dimensions[get_column_letter(col_idx)].width = w

        for idx, feat in enumerate(FEATURE_CATALOG, start=1):
            row_idx = idx + 1
            vals = [
                idx,
                feat["name"],
                feat["category"],
                feat["unit"],
                feat["formula"],
                feat["description"],
                feat["risk_direction"],
            ]
            for col_idx, v in enumerate(vals, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=v)
                cell.font = self.regular_font
                cell.border = self.border
                if col_idx == 1:
                    cell.alignment = Alignment(horizontal="center")

        ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(FEATURE_CATALOG)+1}"

    def _build_model_metrics_sheet(
        self, ws: openpyxl.worksheet.worksheet.Worksheet, model_comp_df: pd.DataFrame
    ) -> None:
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "A2"

        headers = [
            "Model Name",
            "Threshold",
            "Test ROC-AUC",
            "Test PR-AUC",
            "Test F1-Score",
            "Test Recall",
            "Test Precision",
            "Test Brier Score",
            "Val ROC-AUC",
            "Val F1-Score",
        ]
        widths = [24, 12, 14, 14, 14, 14, 14, 16, 14, 14]

        for col_idx, (h, w) in enumerate(zip(headers, widths), start=1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = self.navy_fill
            cell.font = self.header_font
            cell.alignment = Alignment(horizontal="center")
            cell.border = self.border
            ws.column_dimensions[get_column_letter(col_idx)].width = w

        for row_idx, row in model_comp_df.iterrows():
            excel_row = row_idx + 2
            vals = [
                row.get("model_name", ""),
                row.get("optimized_threshold", 0.50),
                row.get("test_roc_auc", 0.0),
                row.get("test_pr_auc", 0.0),
                row.get("test_f1", 0.0),
                row.get("test_recall", 0.0),
                row.get("test_precision", 0.0),
                row.get("test_brier_score", 0.0),
                row.get("val_roc_auc", 0.0),
                row.get("val_f1", 0.0),
            ]
            for col_idx, v in enumerate(vals, start=1):
                cell = ws.cell(row=excel_row, column=col_idx, value=v)
                cell.font = self.regular_font
                cell.border = self.border
                if col_idx == 1:
                    cell.alignment = Alignment(horizontal="left")
                elif col_idx == 2:
                    cell.number_format = "0.00"
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.number_format = "0.0000"
                    cell.alignment = Alignment(horizontal="right")
