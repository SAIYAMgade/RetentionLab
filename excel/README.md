# RetentionLab: Excel Executive Prioritization Workbook

## 1. Overview
The primary Excel deliverable, `RetentionLab_Executive_Report.xlsx`, is an automated, multi-tab financial and operational model generated directly by the Python pipeline (`retentionlab.reporting.excel_generator`).

It translates predictive model inferences into actionable lists for business stakeholders, executive leadership, and retention marketing teams.

---

## 2. Workbook Structure (7 Dedicated Sheets)

| Tab Name | Purpose & Contents |
|---|---|
| **1. Executive Summary** | Analysis scope, observation window, evaluated customer count, risk distribution KPI cards, model comparison table, and governance limitations. |
| **2. Customer Prioritization** | Top 1,000 customers ranked by financial exposure and risk score, with recency, frequency, spend, primary risk drivers, recommended actions, and outreach channels. |
| **3. Model Evaluation** | Full model benchmark comparison (Logistic Regression, KNN, Random Forest, Gradient Boosting, Baseline) across ROC-AUC, PR-AUC, Precision, Recall, F1, and Brier score. |
| **4. Customer Segments** | Strategic segment breakdown showing customer volumes, portfolio share (%), average order count, average recency, and total spend. |
| **5. Retention Scenarios** | Budget allocation scenarios ($5,000 to $50,000) detailing contact capacity, projected retained customers, spend protected, and estimated ROI. |
| **6. Data Dictionary** | Comprehensive documentation of all 44 behavioral features, data sources, calculation logic, and business interpretations. |
| **7. Methodology** | In-depth technical explanation of operational inactivity, temporal validation, zero-leakage guarantees, and statistical testing. |

---

## 3. Formatting & Design Standards
- **Color Palette:** Professional navy blue (`#1F4E79`) headers with high-contrast white text.
- **Number Formats:** Currencies formatted as `$#,##0.00`, percentages as `0.0%`, counts as `#,##0`.
- **Navigation:** Frozen top pane (`A2`) on tabular sheets for seamless scrolling.
- **Integrity:** Gridlines explicitly enabled across all sheets.
