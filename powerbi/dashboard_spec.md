# RetentionLab: Power BI Visual Specification & Layout Guide

This specification details the canvas coordinates, card metrics, chart configurations, and color styling for all three pages of the Power BI executive report.

---

## Page 1: Executive Retention Overview

### Canvas Layout & Grid
- **Page Size:** 16:9 Standard (1280 x 720 px)
- **Background Color:** `#F8F9FA` (Soft Neutral)
- **Primary Accent:** `#1F4E79` (Navy Blue)
- **Alert / Risk Color:** `#C00000` (Crimson)
- **Warning Color:** `#ED7D31` (Amber)
- **Safe / Retained Color:** `#385723` (Forest Green)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  RETENTIONLAB | EXECUTIVE CUSTOMER RETENTION DASHBOARD                   Cutoff: 2023-12-31 │
├───────────────┬───────────────┬────────────────────────┬───────────────────────────────┤
│ [Card 1]      │ [Card 2]      │ [Card 3]               │ [Card 4]                      │
│ Evaluated     │ At-Risk Rate  │ Portfolio Spend        │ High-Risk Exposure            │
│ 8,486 Cust    │ 21.6%         │ $14,142,500            │ $3,054,780 (21.6%)            │
├───────────────┴───────────────┴────────────────────────┴───────────────────────────────┤
│ [Chart 1: Line & Column]                               │ [Chart 2: Donut Chart]        │
│ Monthly Active Customers & Revenue Trajectory          │ Portfolio Risk Distribution   │
│ (24-Month Observation Trend)                           │ High (21.6%) | Med | Low      │
├────────────────────────────────────────────────────────┼───────────────────────────────┤
│ [Chart 3: Clustered Bar Chart]                         │ [Card 5: Model Calibration]   │
│ Benchmark Model ROC-AUC & Recall Comparison            │ Production LogisticRegression │
│ LogisticRegression: 0.771 | Baseline: 0.648           │ Precision: 41.3% | F1: 0.514  │
└────────────────────────────────────────────────────────┴───────────────────────────────┘
```

---

## Page 2: Customer Risk Analysis

### Visual Elements
1. **Interactive Slicers (Top Ribbon):**
   - Slicer 1: `Risk Tier` (Multi-select: High Risk, Medium Risk, Low Risk)
   - Slicer 2: `Monetary Tier` (High Value, Medium Value, Low Value)
   - Slicer 3: `Action Channel` (Phone, Email & SMS, Mobile Push)

2. **Visual 1 (Scatter Plot): Recency vs. Frequency Matrix**
   - X-Axis: `recency_days` (0 to 365 days)
   - Y-Axis: `transaction_frequency` (1 to 60 orders)
   - Size: `total_spend`
   - Color: `risk_score` (Gradient from Green [0.0] to Red [1.0])
   - Tooltip: Customer ID, Primary Risk Driver, Total Spend

3. **Visual 2 (Bar Chart): Spend Exposure by Priority Segment**
   - Category: `priority_segment`
   - Value: `total_spend`
   - Data labels: Sum of Spend ($M)

4. **Visual 3 (Interactive Table): Prioritized Customer Action List**
   - Columns: `customer_id`, `risk_score`, `priority_segment`, `recency_days`, `total_spend`, `primary_risk_driver`, `recommended_action`, `action_channel`
   - Conditional formatting on `risk_score` (Red data bar)

---

## Page 3: Retention Scenario Planning

### Visual Elements
1. **Scenario Parameter Slicer:**
   - Single-select Slicer bound to `Fact_RetentionScenarios[hypothetical_budget]`
   - Options: `$5,000`, `$10,000`, `$25,000`, `$50,000`

2. **Scenario Impact KPI Cards:**
   - Card 1: `Max Customers Contacted` (e.g. 666 at $10k budget)
   - Card 2: `Projected Retained Customers` (e.g. 100 customers @ 15% success rate)
   - Card 3: `Projected Spend Protected` (e.g. $167,400 protected)
   - Card 4: `Projected Net ROI Ratio` (e.g. 15.74x Net Return)

3. **Visual 1 (Waterfall / Grouped Bar): Spend Exposed vs. Spend Protected**
   - Compares total candidate portfolio spend against expected retained revenue across budget scenarios.

4. **Visual 2 (Channel Allocation Treemap):**
   - Shows customer volume allocation by recommended intervention medium (Phone, SMS, Email, Push).

5. **Assumption Banner (Bottom Text Box):**
   - *"Notice: All retention figures reflect modeled scenario projections based on historical customer value and assumed response rates. Prior to full-scale budget allocation, execute randomized A/B holdout testing to establish causal uplift."*
