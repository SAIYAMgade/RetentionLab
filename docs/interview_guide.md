# RetentionLab: 5-Minute Project Demonstration & Technical Walkthrough Guide

Use this script during technical interviews, portfolio walkthroughs, or stakeholder presentations.

---

### Minute 1: Business Problem & Data Foundation
- **The Core Question**: *"Which customers are at risk, why are they at risk, how should customer success prioritize them, and how do we measure the revenue exposure?"*
- **The Data Architecture**:
  - Show the SQLite relational database and the >104,000 synthetic transaction records.
  - Explain the critical distinction between transactional grain (104,990 orders across multiple dates) and customer-snapshot grain (4,850 eligible accounts at snapshot date `2026-04-01`).
  - Demonstrate the 6 automated SQL integrity checks (primary key uniqueness, orphan keys, valid dates).

---

### Minute 2: Feature Engineering & SQL Analytics
- **Relational SQL Layer**:
  - Highlight key queries: RFM quartiles (`02_rfm_analysis.sql`), cohort survival (`09_retention_churn_cohorts.sql`), and revenue concentration (`11_revenue_concentration_by_segment.sql`).
- **44-Feature Behavioral Pipeline**:
  - Open `src/retentionlab/features/catalog.py` or Page 6 of the Streamlit app.
  - Walk through the 6 vectors: Recency/Frequency, Spending, Diversity, Friction, Maturity, and Cadence.
  - Show the strict leakage guardrail: every feature is computed on $t \le \text{2026-04-01}$, while churn is evaluated exclusively in the future window $(T, T + 60\text{d}]$.

---

### Minute 3: Machine Learning Benchmark & Threshold Governance
- **Candidate Comparison**:
  - Compare **Logistic Regression** (Interpretable Baseline, ROC-AUC 0.9144), **Random Forest** (0.9398), and **HistGradientBoosting** (Champion, ROC-AUC 0.9395, PR-AUC 0.9244).
- **Decision Threshold Optimization**:
  - Explain why default 0.50 is arbitrary in business: we scanned thresholds on the **validation partition** to select 0.74, delivering 98.93% precision and 74.60% recall on the holdout test set.
  - Emphasize test set isolation: the test set was never touched during threshold search.

---

### Minute 4: Revenue-Aware Prioritization Engine
- **Why Sorting by Probability Alone Fails**:
  - A small account with 90% churn risk represents $200 in exposure, whereas an enterprise account with 65% risk represents $25,000.
  - Explain the Prioritization Score: `0.55 * Churn_Prob + 0.45 * Normalized_Annual_Spend`.
- **Top 15% Operational Cohort**:
  - Open Page 4 of the Streamlit application.
  - Show how 728 prioritized accounts concentrate over $26.7M in risk-weighted exposure.
  - Demonstrate actionable recommendation categories (VIP Human Touchpoint, Payment Review, Service Escalation, Lifecycle Nudge).

---

### Minute 5: Enterprise Reporting & Operational Limitations
- **Multi-Channel Delivery**:
  - Display the generated Excel workbook (`RetentionLab_Retention_Action_Workbook.xlsx`) with conditional formatting, frozen panes, and KPI summaries.
  - Show the Power BI star-schema tables and certified DAX measures.
- **Honest Limitations**:
  - Explicitly state that predictions represent probabilistic behavioral associations, not causal guarantees.
  - Note that customer interventions require human CSM review, and real-world impact must be measured through randomized holdout retention experiments.
