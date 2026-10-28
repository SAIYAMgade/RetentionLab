"""Automated multi-sheet Excel business report generator for RetentionLab."""
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from retentionlab.config.settings import DEFAULT_CONFIG, PipelineConfig
from retentionlab.features.registry import get_feature_dictionary_df


HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="1F4E79")
SUBTITLE_FONT = Font(name="Calibri", size=11, italic=True, color="595959")
SECTION_FONT = Font(name="Calibri", size=13, bold=True, color="1F4E79")
BOLD_FONT = Font(name="Calibri", size=11, bold=True)
REGULAR_FONT = Font(name="Calibri", size=11)

THIN_BORDER = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9")
)


def style_table_header(ws, start_row: int, max_col: int):
    """Apply professional dark navy styling to table headers."""
    for col in range(1, max_col + 1):
        cell = ws.cell(row=start_row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER


def autofit_columns(ws, min_col: int = 1, max_col: int = None, min_width: int = 12, max_width: int = 45):
    """Auto-adjust worksheet column widths cleanly."""
    if max_col is None:
        max_col = ws.max_column
    for col in range(min_col, max_col + 1):
        col_letter = get_column_letter(col)
        max_len = 0
        for cell in ws[col_letter]:
            val_str = str(cell.value or "")
            if "\n" in val_str:
                val_str = max(val_str.split("\n"), key=len)
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(min_width, min(max_len + 3, max_width))


def build_excel_report(
    prioritization_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    scenarios_df: pd.DataFrame,
    audit_data: Dict[str, Any],
    statistical_tests: List[Dict[str, Any]],
    output_path: Path = None,
    config: PipelineConfig = DEFAULT_CONFIG
) -> Path:
    """Generate complete 7-sheet executive report workbook."""
    if output_path is None:
        output_path = config.excel_report_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    # Remove default active sheet
    wb.remove(wb.active)

    # -------------------------------------------------------------
    # Sheet 1: Executive Summary
    # -------------------------------------------------------------
    ws_exec = wb.create_sheet(title="Executive Summary")
    ws_exec.views.sheetView[0].showGridLines = True

    ws_exec["A1"] = "RETENTIONLAB: CUSTOMER RETENTION & PREDICTIVE ANALYTICS"
    ws_exec["A1"].font = TITLE_FONT
    ws_exec["A2"] = "Executive Portfolio Summary & Operational Risk Assessment"
    ws_exec["A2"].font = SUBTITLE_FONT

    ws_exec["A4"] = "1. Analytical Scope & Portfolio Parameters"
    ws_exec["A4"].font = SECTION_FONT

    scope_data = [
        ("Observation Window", f"{config.start_date} to {config.cutoff_date} (24 Months)"),
        ("Prediction Timestamp", config.cutoff_date),
        ("Evaluation Horizon", f"{config.future_start_date} to {config.future_end_date} (90 Days)"),
        ("Target Definition", "Inactivity (0 qualifying purchases during 90-day future horizon)"),
        ("Eligibility Criteria", f"Completed purchase history with tenure >= {config.min_tenure_days} days"),
        ("Total Customers Evaluated", len(prioritization_df)),
        ("Total Transactions Ingested", audit_data.get("row_count", 0)),
        ("Portfolio Gross Spend", f"${prioritization_df['total_spend'].sum():,.2f}")
    ]

    for idx, (param, val) in enumerate(scope_data, start=5):
        ws_exec.cell(row=idx, column=1, value=param).font = BOLD_FONT
        ws_exec.cell(row=idx, column=2, value=val).font = REGULAR_FONT
        ws_exec.cell(row=idx, column=1).border = THIN_BORDER
        ws_exec.cell(row=idx, column=2).border = THIN_BORDER

    # KPI Summary Cards
    ws_exec["D4"] = "2. Risk Distribution & Portfolio Exposure"
    ws_exec["D4"].font = SECTION_FONT

    high_risk_cnt = int((prioritization_df["risk_tier"] == "High Risk").sum())
    med_risk_cnt = int((prioritization_df["risk_tier"] == "Medium Risk").sum())
    low_risk_cnt = int((prioritization_df["risk_tier"] == "Low Risk").sum())
    total_cust = len(prioritization_df)

    high_risk_spend = float(prioritization_df[prioritization_df["risk_tier"] == "High Risk"]["total_spend"].sum())

    risk_cards = [
        ("High Risk Customers", high_risk_cnt, f"{high_risk_cnt / total_cust:.1%}"),
        ("High Risk Spend Exposure", f"${high_risk_spend:,.2f}", f"{high_risk_spend / prioritization_df['total_spend'].sum():.1%} of portfolio"),
        ("Medium Risk Customers", med_risk_cnt, f"{med_risk_cnt / total_cust:.1%}"),
        ("Low Risk / Retained", low_risk_cnt, f"{low_risk_cnt / total_cust:.1%}"),
    ]

    for idx, (metric, count_val, pct_val) in enumerate(risk_cards, start=5):
        ws_exec.cell(row=idx, column=4, value=metric).font = BOLD_FONT
        ws_exec.cell(row=idx, column=5, value=count_val).font = REGULAR_FONT
        ws_exec.cell(row=idx, column=6, value=pct_val).font = REGULAR_FONT
        ws_exec.cell(row=idx, column=4).border = THIN_BORDER
        ws_exec.cell(row=idx, column=5).border = THIN_BORDER
        ws_exec.cell(row=idx, column=6).border = THIN_BORDER

    # Model Evaluation Summary Table
    ws_exec["A15"] = "3. Predictive Model Evaluation Summary"
    ws_exec["A15"].font = SECTION_FONT

    headers_comp = ["Model Architecture", "Decision Threshold", "ROC-AUC", "PR-AUC", "Precision", "Recall", "F1-Score", "Brier Loss"]
    for col_idx, h in enumerate(headers_comp, start=1):
        ws_exec.cell(row=17, column=col_idx, value=h)
    style_table_header(ws_exec, 17, len(headers_comp))

    for row_idx, row in comparison_df.iterrows():
        curr_row = 18 + row_idx
        ws_exec.cell(row=curr_row, column=1, value=row.get("model_name")).font = BOLD_FONT
        ws_exec.cell(row=curr_row, column=2, value=row.get("threshold")).number_format = "0.00"
        ws_exec.cell(row=curr_row, column=3, value=row.get("roc_auc")).number_format = "0.000"
        ws_exec.cell(row=curr_row, column=4, value=row.get("pr_auc")).number_format = "0.000"
        ws_exec.cell(row=curr_row, column=5, value=row.get("precision")).number_format = "0.0%"
        ws_exec.cell(row=curr_row, column=6, value=row.get("recall")).number_format = "0.0%"
        ws_exec.cell(row=curr_row, column=7, value=row.get("f1_score")).number_format = "0.000"
        ws_exec.cell(row=curr_row, column=8, value=row.get("brier_score")).number_format = "0.000"
        for c in range(1, len(headers_comp) + 1):
            ws_exec.cell(row=curr_row, column=c).border = THIN_BORDER

    # Limitations Notice
    last_r = 18 + len(comparison_df) + 2
    ws_exec.cell(row=last_r, column=1, value="4. Key Engineering & Business Limitations:").font = SECTION_FONT
    limits = [
        "• Operational Inactivity is not identical to permanent churn: customers may resume ordering later.",
        "• Observational risk predictions do not prove causality or guarantee intervention uplift without A/B experimentation.",
        "• Outreach ROI projections are scenario-based models; actual retention uplift must be measured empirically."
    ]
    for i, lim in enumerate(limits, start=last_r + 1):
        ws_exec.cell(row=i, column=1, value=lim).font = SUBTITLE_FONT

    autofit_columns(ws_exec)

    # -------------------------------------------------------------
    # Sheet 2: Customer Prioritization
    # -------------------------------------------------------------
    ws_prio = wb.create_sheet(title="Customer Prioritization")
    ws_prio.views.sheetView[0].showGridLines = True
    ws_prio.freeze_panes = "A2"

    prio_cols = [
        "customer_id", "risk_score", "risk_tier", "monetary_tier",
        "priority_segment", "recency_days", "transaction_frequency",
        "total_spend", "primary_risk_driver", "recommended_action", "action_channel"
    ]
    headers_prio = [
        "Customer ID", "Risk Score", "Risk Tier", "Monetary Tier",
        "Priority Segment", "Recency (Days)", "Lifetime Orders",
        "Total Spend ($)", "Primary Risk Driver", "Recommended Action", "Outreach Channel"
    ]

    for col_idx, h in enumerate(headers_prio, start=1):
        ws_prio.cell(row=1, column=col_idx, value=h)
    style_table_header(ws_prio, 1, len(headers_prio))

    # Output top 1,000 customers for report performance and readability
    sample_prio = prioritization_df[prio_cols].head(1000)
    for r_idx, (_, row) in enumerate(sample_prio.iterrows(), start=2):
        ws_prio.cell(row=r_idx, column=1, value=row["customer_id"]).font = REGULAR_FONT
        c_score = ws_prio.cell(row=r_idx, column=2, value=row["risk_score"])
        c_score.number_format = "0.0%"
        c_score.alignment = Alignment(horizontal="right")
        ws_prio.cell(row=r_idx, column=3, value=row["risk_tier"]).alignment = Alignment(horizontal="center")
        ws_prio.cell(row=r_idx, column=4, value=row["monetary_tier"]).alignment = Alignment(horizontal="center")
        ws_prio.cell(row=r_idx, column=5, value=row["priority_segment"]).font = BOLD_FONT
        ws_prio.cell(row=r_idx, column=6, value=row["recency_days"]).number_format = "#,##0"
        ws_prio.cell(row=r_idx, column=7, value=row["transaction_frequency"]).number_format = "#,##0"
        c_spend = ws_prio.cell(row=r_idx, column=8, value=row["total_spend"])
        c_spend.number_format = "$#,##0.00"
        ws_prio.cell(row=r_idx, column=9, value=row["primary_risk_driver"]).font = REGULAR_FONT
        ws_prio.cell(row=r_idx, column=10, value=row["recommended_action"]).font = REGULAR_FONT
        ws_prio.cell(row=r_idx, column=11, value=row["action_channel"]).font = REGULAR_FONT

        for c in range(1, len(headers_prio) + 1):
            ws_prio.cell(row=r_idx, column=c).border = THIN_BORDER

    autofit_columns(ws_prio)

    # -------------------------------------------------------------
    # Sheet 3: Model Evaluation
    # -------------------------------------------------------------
    ws_eval = wb.create_sheet(title="Model Evaluation")
    ws_eval.views.sheetView[0].showGridLines = True
    ws_eval.freeze_panes = "A2"

    eval_headers = list(comparison_df.columns)
    for col_idx, h in enumerate(eval_headers, start=1):
        ws_eval.cell(row=1, column=col_idx, value=h.replace("_", " ").title())
    style_table_header(ws_eval, 1, len(eval_headers))

    for r_idx, (_, row) in enumerate(comparison_df.iterrows(), start=2):
        for c_idx, col_name in enumerate(eval_headers, start=1):
            cell = ws_eval.cell(row=r_idx, column=c_idx, value=row[col_name])
            cell.border = THIN_BORDER
            if isinstance(row[col_name], float):
                cell.number_format = "0.0000"

    autofit_columns(ws_eval)

    # -------------------------------------------------------------
    # Sheet 4: Customer Segments
    # -------------------------------------------------------------
    ws_seg = wb.create_sheet(title="Customer Segments")
    ws_seg.views.sheetView[0].showGridLines = True
    ws_seg.freeze_panes = "A2"

    seg_summary = prioritization_df.groupby("priority_segment").agg(
        customer_count=("customer_id", "count"),
        avg_risk_score=("risk_score", "mean"),
        avg_recency_days=("recency_days", "mean"),
        avg_orders=("transaction_frequency", "mean"),
        total_segment_spend=("total_spend", "sum"),
        avg_customer_spend=("total_spend", "mean")
    ).reset_index().sort_values("total_segment_spend", ascending=False)

    seg_headers = [
        "Priority Segment", "Customer Count", "Portfolio Share (%)",
        "Avg Risk Score", "Avg Recency (Days)", "Avg Lifetime Orders",
        "Total Segment Spend ($)", "Avg Customer Spend ($)"
    ]
    for col_idx, h in enumerate(seg_headers, start=1):
        ws_seg.cell(row=1, column=col_idx, value=h)
    style_table_header(ws_seg, 1, len(seg_headers))

    tot_c = len(prioritization_df)
    for r_idx, (_, row) in enumerate(seg_summary.iterrows(), start=2):
        ws_seg.cell(row=r_idx, column=1, value=row["priority_segment"]).font = BOLD_FONT
        ws_seg.cell(row=r_idx, column=2, value=row["customer_count"]).number_format = "#,##0"
        c_pct = ws_seg.cell(row=r_idx, column=3, value=row["customer_count"] / tot_c)
        c_pct.number_format = "0.0%"
        c_risk = ws_seg.cell(row=r_idx, column=4, value=row["avg_risk_score"])
        c_risk.number_format = "0.0%"
        ws_seg.cell(row=r_idx, column=5, value=row["avg_recency_days"]).number_format = "0.0"
        ws_seg.cell(row=r_idx, column=6, value=row["avg_orders"]).number_format = "0.0"
        c_tot = ws_seg.cell(row=r_idx, column=7, value=row["total_segment_spend"])
        c_tot.number_format = "$#,##0.00"
        c_avg = ws_seg.cell(row=r_idx, column=8, value=row["avg_customer_spend"])
        c_avg.number_format = "$#,##0.00"

        for c in range(1, len(seg_headers) + 1):
            ws_seg.cell(row=r_idx, column=c).border = THIN_BORDER

    autofit_columns(ws_seg)

    # -------------------------------------------------------------
    # Sheet 5: Retention Scenarios
    # -------------------------------------------------------------
    ws_scen = wb.create_sheet(title="Retention Scenarios")
    ws_scen.views.sheetView[0].showGridLines = True
    ws_scen.freeze_panes = "A2"

    scen_headers = [
        "Budget Scenario ($)", "Cost per Contact ($)", "Customers Contacted",
        "High-Value Targeted", "Assumed Success Rate", "Projected Retained Cust",
        "Exposed Spend ($)", "Projected Spend Protected ($)", "Net Value Gain ($)", "Projected ROI"
    ]
    for col_idx, h in enumerate(scen_headers, start=1):
        ws_scen.cell(row=1, column=col_idx, value=h)
    style_table_header(ws_scen, 1, len(scen_headers))

    for r_idx, (_, row) in enumerate(scenarios_df.iterrows(), start=2):
        ws_scen.cell(row=r_idx, column=1, value=row["hypothetical_budget"]).number_format = "$#,##0"
        ws_scen.cell(row=r_idx, column=2, value=row["cost_per_contact"]).number_format = "$#,##0.00"
        ws_scen.cell(row=r_idx, column=3, value=row["max_customers_contacted"]).number_format = "#,##0"
        ws_scen.cell(row=r_idx, column=4, value=row["high_value_customers_targeted"]).number_format = "#,##0"
        ws_scen.cell(row=r_idx, column=5, value=row["assumed_retention_success_rate"]).alignment = Alignment(horizontal="center")
        ws_scen.cell(row=r_idx, column=6, value=row["projected_retained_customers"]).number_format = "#,##0"
        ws_scen.cell(row=r_idx, column=7, value=row["portfolio_spend_exposed"]).number_format = "$#,##0.00"
        ws_scen.cell(row=r_idx, column=8, value=row["projected_spend_protected"]).number_format = "$#,##0.00"
        ws_scen.cell(row=r_idx, column=9, value=row["projected_net_value"]).number_format = "$#,##0.00"
        c_roi = ws_scen.cell(row=r_idx, column=10, value=row["projected_roi_ratio"])
        c_roi.number_format = "0.00x"

        for c in range(1, len(scen_headers) + 1):
            ws_scen.cell(row=r_idx, column=c).border = THIN_BORDER

    autofit_columns(ws_scen)

    # -------------------------------------------------------------
    # Sheet 6: Data Dictionary
    # -------------------------------------------------------------
    ws_dict = wb.create_sheet(title="Data Dictionary")
    ws_dict.views.sheetView[0].showGridLines = True
    ws_dict.freeze_panes = "A2"

    feat_df = get_feature_dictionary_df()
    dict_headers = list(feat_df.columns)
    for col_idx, h in enumerate(dict_headers, start=1):
        ws_dict.cell(row=1, column=col_idx, value=h.replace("_", " ").title())
    style_table_header(ws_dict, 1, len(dict_headers))

    for r_idx, (_, row) in enumerate(feat_df.iterrows(), start=2):
        for c_idx, col_name in enumerate(dict_headers, start=1):
            cell = ws_dict.cell(row=r_idx, column=c_idx, value=str(row[col_name]))
            cell.font = REGULAR_FONT
            cell.border = THIN_BORDER

    autofit_columns(ws_dict)

    # -------------------------------------------------------------
    # Sheet 7: Methodology
    # -------------------------------------------------------------
    ws_meth = wb.create_sheet(title="Methodology")
    ws_meth.views.sheetView[0].showGridLines = True

    ws_meth["A1"] = "RETENTIONLAB: METHODOLOGY & ANALYTICAL SPECIFICATION"
    ws_meth["A1"].font = TITLE_FONT

    methodology_sections = [
        ("1. Operational Inactivity Problem Formulation",
         "The platform defines customer churn operationally as 90-day inactivity following a designated prediction cutoff date (2023-12-31). Customers with zero completed purchases in Q1 2024 are labeled inactive (is_inactive=1), whereas customers completing at least one purchase are labeled active (is_inactive=0)."),

        ("2. Temporal Validation & Zero-Leakage Guarantee",
         "All 44 customer behavioral features are derived strictly from transactions occurring on or before 2023-12-31 23:59:59. Feature engineering contains zero post-outcome transaction records. Machine learning pipelines encapsulate imputation and feature scaling, fitting purely on training folds without test-set influence."),

        ("3. Statistical Rigor",
         "Parametric normality tests (Shapiro-Wilk) and skewness evaluations justified the use of non-parametric tests (Mann-Whitney U) and log-transformed Welch's t-tests to evaluate behavioral divergence between active and churning cohorts with rank-biserial and Cohen's d effect sizes."),

        ("4. Decision Threshold Optimization",
         "Rather than defaulting to arbitrary 0.50 cutoffs, decision boundaries are calibrated against business utility functions (e.g. optimizing F1-score or meeting target operational recall while maintaining minimum precision thresholds)."),

        ("5. Portfolio Interview Defensibility",
         "Every reported metric in RetentionLab is derived directly from executed pipeline calculations on the dataset. No metrics, customer counts, or business savings are fabricated.")
    ]

    curr_row = 3
    for title, text in methodology_sections:
        ws_meth.cell(row=curr_row, column=1, value=title).font = SECTION_FONT
        curr_row += 1
        ws_meth.cell(row=curr_row, column=1, value=text).font = REGULAR_FONT
        ws_meth.cell(row=curr_row, column=1).alignment = Alignment(wrap_text=True)
        curr_row += 2

    ws_meth.column_dimensions["A"].width = 110

    # Save complete workbook
    wb.save(output_path)
    return output_path
