# RetentionLab Power BI Multi-Page Report Layout Specification

This visual guide defines the 5 certified canvas pages for Power BI implementation.

---

## Page 1: Executive Portfolio Summary
**Objective**: High-level briefing for VP of Customer Success and Chief Revenue Officer.

### Layout Elements:
1. **Top Slicer Bar**:
   - `CUSTOMER_DIMENSION[customer_segment]` (Dropdown)
   - `CUSTOMER_DIMENSION[region]` (Dropdown)
   - `CUSTOMER_DIMENSION[subscription_type]` (Buttons)
2. **KPI Scorecard Row (4 Cards)**:
   - Card 1: `[Total Customers]` (e.g. 5,000)
   - Card 2: `[Total Transactions]` (e.g. 104,990)
   - Card 3: `[Top Cohort Customer Count]` (e.g. 728)
   - Card 4: `[Top Cohort Risk Exposure]` (e.g. $26.8M)
3. **Main Visual (Left 60%)**:
   - Clustered Bar Chart: `CUSTOMER_RISK_FACT[risk_band]` vs. `[Top Cohort Risk Exposure]` & `[High Risk Customer Count]`.
4. **Secondary Visual (Right 40%)**:
   - Donut Chart: `CUSTOMER_DIMENSION[customer_segment]` share of `[Portfolio Risk Exposure]`.
5. **Bottom Ribbon**:
   - Callout Table: Action Category distribution across the top 15% cohort.

---

## Page 2: Customer Retention Risk Tiers
**Objective**: Detailed risk tier exploration for Retention Managers.

### Layout Elements:
1. **Left Slicer Pane**: Risk Band multi-select, Acquisition Channel, Tenure Tier.
2. **Visual 1**: Scatter Plot:
   - X-Axis: `CUSTOMER_RISK_FACT[churn_probability]`
   - Y-Axis: `CUSTOMER_RISK_FACT[historical_value_proxy]`
   - Bubble Size: `CUSTOMER_RISK_FACT[risk_weighted_exposure]`
   - Color: `CUSTOMER_RISK_FACT[risk_band]`
3. **Visual 2**: Stacked Column Chart:
   - X-Axis: `CUSTOMER_DIMENSION[acquisition_channel]`
   - Y-Axis: `[Eligible Scored Customers]` broken down by `risk_band`.
4. **Bottom Grid**: Paginated Customer Detail Table with Customer ID, Segment, Prob, Tier, Exposure, Top Signals.

---

## Page 3: Revenue Exposure & Prioritization
**Objective**: Actionable worklist and prioritization queue for Customer Success Managers (CSMs).

### Layout Elements:
1. **Top KPI Row**: Top Cohort Exposure, Top Cohort Average Spend, VIP Human Touchpoint Count.
2. **Prioritization Ranked Table**:
   - Columns: `Rank`, `Customer ID`, `Risk Band`, `Priority Score`, `Risk Exposure`, `Suggested Action`, `Operational Next Step`.
   - Conditional formatting: Priority Score (Data bar gradient), Risk Band (Soft background fill).
3. **Action Breakdown Waterfall**:
   - Total Exposure -> VIP Touchpoints -> Payment Friction -> Support Escalations -> Automated Nudges.

---

## Page 4: Cohort Retention Dynamics
**Objective**: Long-term retention trajectory analysis by signup cohort.

### Layout Elements:
1. **Cohort Heatmap / Matrix**:
   - Rows: `CUSTOMER_DIMENSION[signup_cohort]` (YYYY-MM)
   - Columns: Month Offset (M0, M1, M2, M3, M6, M12)
   - Values: `[Cohort Retention Rate %]` (Gradient fill from light blue to deep navy).
2. **Line Chart**:
   - Comparative 12-month retention curves by `customer_segment` (Enterprise vs SMB vs Startup).

---

## Page 5: Model Governance & Monitoring
**Objective**: Transparency, validation integrity, and threshold governance for data science reviewers.

### Layout Elements:
1. **Header Cards**: Model Name (`HistGradientBoosting`), Model Version (`2.0.0`), Operating Threshold (`0.74`), Test ROC-AUC (`0.9395`).
2. **Visual 1**: Model Comparison Bar Chart (ROC-AUC, PR-AUC, F1 across Logistic Regression, Random Forest, and HistGradientBoosting).
3. **Visual 2**: Confusion Matrix Grid (True Negatives, False Positives, False Negatives, True Positives).
4. **Governance Callout Box**:
   - Strict notice documenting temporal data split, leakage tests passed, and non-causal interpretation guidelines.
