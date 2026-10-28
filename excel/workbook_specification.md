# RetentionLab: Excel Workbook Engineering Specification

This document details the cell structures, formatting rules, and dynamic formulas applied in `RetentionLab_Executive_Report.xlsx`.

---

## 1. Sheet Specifications

### Sheet 1: `Executive Summary`
- **Cell A1:A2:** Project title and subtitle styled with Calibri 16pt Bold and Navy Blue fill.
- **Table 1 (A4:B12):** Analytical Scope & Parameters (Dates, customer count, gross spend).
- **Table 2 (D4:F8):** Portfolio Risk Breakdown Cards (High, Medium, Low Risk counts and spend).
- **Table 3 (A17:H23):** Model Evaluation Summary (Model name, threshold, ROC-AUC, PR-AUC, Precision, Recall, F1, Brier score).
- **Table 4 (A25:A29):** Principal Analytical Limitations.

### Sheet 2: `Customer Prioritization`
- **Header Row (Row 1):** Styled with `#1F4E79` navy fill and Calibri 11pt Bold White font.
- **Freeze Panes:** Positioned at `A2` to preserve headers during vertical scrolling.
- **Columns:**
  - A: `Customer ID` (Centered text)
  - B: `Risk Score` (Formatted as `0.0%`)
  - C: `Risk Tier` (Centered text)
  - D: `Monetary Tier` (Centered text)
  - E: `Priority Segment` (Calibri 11pt Bold)
  - F: `Recency (Days)` (Formatted as `#,##0`)
  - G: `Lifetime Orders` (Formatted as `#,##0`)
  - H: `Total Spend ($)` (Formatted as `$#,##0.00`)
  - I: `Primary Risk Driver` (Descriptive diagnostic text)
  - J: `Recommended Action` (Prescriptive retention play)
  - K: `Outreach Channel` (Phone / Dedicated Rep, Email & SMS, Mobile Push)

### Sheet 3: `Model Evaluation`
- Detailed metric breakdown for all 5 tested classifiers.
- Numbers formatted to 4 decimal places (`0.0000`).

### Sheet 4: `Customer Segments`
- Summarized aggregation across priority segments.
- Formatted percentages (`0.0%`) and currency sums (`$#,##0.00`).

### Sheet 5: `Retention Scenarios`
- Contains hypothetical budget allocations ($5k, $10k, $25k, $50k) with unit cost of $15/contact.
- Explicit scenario notice: *"Illustrative scenario projection only; requires experimental uplift testing."*

### Sheet 6: `Data Dictionary`
- 44 feature definitions with source columns, observation window, data type, missing handling, and business interpretation.

### Sheet 7: `Methodology`
- Documentation of target definitions, time horizons, zero-leakage constraints, and interview defensibility.
