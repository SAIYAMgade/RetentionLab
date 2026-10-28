# RetentionLab: Power BI Executive Dashboard Architecture

## 1. Overview
The **RetentionLab Power BI Dashboard** translates machine learning risk scores and transaction analytics into an interactive three-page executive decision engine.

The dashboard connects directly to clean CSV extracts generated in `powerbi/data/` or directly to the SQLite/PostgreSQL analytical database.

---

## 2. Three-Page Dashboard Architecture

### Page 1: Executive Retention Overview
- **Objective:** High-level executive monitoring of customer base stability, at-risk revenue exposure, and predictive model reliability.
- **Key KPIs:**
  - `Eligible Customers Evaluated`: 8,486
  - `At-Risk Customer Inactive Rate`: 21.6%
  - `Portfolio Gross Revenue`: $14.1M+
  - `High-Risk Revenue Exposure`: At-risk portfolio revenue needing intervention
  - `Model Benchmark Performance`: Logistic Regression ROC-AUC (0.771) vs Baseline (0.648)
- **Visuals:**
  - Monthly active customer & revenue momentum (Line & Clustered Column)
  - Risk tier breakdown (Donut Chart)
  - Model ROC-AUC comparison bar chart

### Page 2: Customer Risk Analysis
- **Objective:** Operational deep-dive into customer behavioral decay and segmentation.
- **Visuals:**
  - Recency vs. Frequency scatter plot with Risk Score color density
  - Spend distribution across Strategic Customer Segments
  - Top 100 At-Risk Customer prioritization matrix table with clickable filters

### Page 3: Retention Scenario Planning
- **Objective:** Scenario analysis for marketing and retention outreach budgeting.
- **Visuals:**
  - Hypothetical budget selector ($5k, $10k, $25k, $50k)
  - Projected protected customer count and spend saved
  - Projected net ROI multiplier per scenario tier
  - Action channel volume distribution (Phone / Email / SMS / Push)

---

## 3. Data Ingestion & Refresh
1. Launch Power BI Desktop.
2. Select **Get Data** -> **Text/CSV** or **ODBC / PostgreSQL**.
3. Point to the CSV files in `powerbi/data/`:
   - `pbi_customer_prioritization.csv` (Fact Table)
   - `pbi_model_comparison.csv` (Dimension / Benchmark Table)
   - `pbi_retention_scenarios.csv` (Scenario Table)
4. Load tables and verify relationships per [data_model.md](data_model.md).
5. Copy the DAX measures defined in [dax_measures.md](dax_measures.md).
