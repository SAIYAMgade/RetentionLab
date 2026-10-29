# RetentionLab Power BI Reporting Package

This directory contains the business intelligence architecture, data model specifications, DAX measure definitions, and star-schema datasets ready for direct import into Microsoft Power BI Desktop or the Power BI Service.

## Package Contents

1. **`data_model.md`**: Complete star-schema relational model, table descriptions, primary/foreign keys, cardinality, and filter directions.
2. **`dax_measures.md`**: Certified DAX calculations with business definitions, formulas, filter context explanations, and explicit denominators.
3. **`report_layout.md`**: Step-by-step visual specification for the 5 enterprise report pages:
   - Page 1: Executive Portfolio Summary
   - Page 2: Customer Retention Risk Tiers
   - Page 3: Revenue Exposure & Prioritization
   - Page 4: Cohort Retention Dynamics
   - Page 5: Model Governance & Monitoring
4. **`data/`**: Exported CSV reporting tables matching the documented relational schema:
   - `CUSTOMER_DIMENSION.csv`
   - `DATE_DIMENSION.csv`
   - `TRANSACTION_FACT.csv`
   - `CUSTOMER_SNAPSHOT_FACT.csv`
   - `CUSTOMER_RISK_FACT.csv`
   - `RETENTION_ACTION_FACT.csv`
   - `MODEL_RUN_DIMENSION.csv`

## Import Instructions for Power BI Desktop

1. Open **Power BI Desktop**.
2. Click **Get Data -> Folder** or select **Text/CSV** and point to `dashboards/powerbi/data/`.
3. Load the 7 CSV files into the Power BI Data Model.
4. Navigate to the **Model View** and establish the relationships defined in [`data_model.md`](data_model.md).
5. Create a new measure table `_DAX_Measures` and paste the DAX definitions from [`dax_measures.md`](dax_measures.md).
6. Build out the canvas pages following [`report_layout.md`](report_layout.md).
