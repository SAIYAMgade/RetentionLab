# RetentionLab: System Architecture & Data Lineage

## 1. End-to-End System Flow

RetentionLab is designed as a modular, testable, and reproducible customer retention platform. The system pipeline guarantees complete temporal separation and zero data leakage.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. INGESTION & AUDIT                            │
│  - Raw Transaction Stream (109k+ records across 8,500 customers)       │
│  - 12-point Data Integrity Audit (types, nulls, duplicates, anomalies) │
│  - Ingestion into SQLite / PostgreSQL (raw_transactions table)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      2. PREPROCESSING & CLEANING                       │
│  - Standardization of timestamps & currencies                          │
│  - Isolation of completed purchases from refunds and failures          │
│  - Loading into cleaned_transactions table                             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               3. FEATURE ENGINEERING & TARGET DEFINITION               │
│  - Cutoff Date: 2023-12-31 23:59:59 (Strict temporal observation)      │
│  - 44 Behavioral Features (Recency, Frequency, Spend, Trends, Mix)     │
│  - Target Definition: 90-day future outcome window (Q1 2024)           │
│  - Zero-leakage enforcement (No post-2023 data in features)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   4. STATISTICAL & SQL ANALYTICS                       │
│  - In-database CTEs & Window Functions (20 verified analytical queries)│
│  - Mann-Whitney U & Welch's t-test hypothesis evaluations              │
│  - Effect sizes: Rank-biserial correlations & Cohen's d                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     5. MODELING & EVALUATION                           │
│  - Stratified Train/Test Split (80/20)                                 │
│  - Encapsulated Scikit-Learn Pipelines (StandardScaler + Imputer)      │
│  - Benchmark Comparison: Baseline, Logistic Regression, KNN, RF, GBDT  │
│  - Precision-Recall threshold calibration                              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               6. PRIORITIZATION & BUSINESS REPORTING                   │
│  - Risk Tier × Monetary Tier matrix (High-Value At-Risk Tier 1)        │
│  - Prescriptive channel assignment (Phone, SMS, Email, Push)           │
│  - Automated 7-Sheet Executive Excel Workbook                          │
│  - Interactive Power BI Star Schema & DAX Model                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure & Component Roles

- `src/retentionlab/config/`: Central settings (dates, thresholds, paths, seed).
- `src/retentionlab/ingestion/`: Synthetic transaction generation and raw data ingestion.
- `src/retentionlab/preprocessing/`: 12-point data audit, validation, and cleaning.
- `src/retentionlab/features/`: 44 behavioral features, zero-leakage builder, target labeling, and feature registry.
- `src/retentionlab/analytics/`: SQLite database initialization and statistical hypothesis testing suite.
- `src/retentionlab/modeling/`: Scikit-Learn pipelines, heuristic baseline, model trainers.
- `src/retentionlab/evaluation/`: Multi-metric evaluation (ROC-AUC, PR-AUC, F1, calibration) and threshold tuning.
- `src/retentionlab/prioritization/`: Customer risk segmentation, action matrix, and scenario analysis.
- `src/retentionlab/reporting/`: Multi-tab openpyxl Excel business report builder.
- `sql/`: 20 SQL analytical queries across schema, validation, customer analytics, and reporting.
- `powerbi/`: Data model specification, DAX measure repository, dashboard layout specs, and CSV exports.
- `excel/`: Generated executive workbook and engineering documentation.
- `notebooks/`: 4 runnable exploratory and evaluation Jupyter notebooks.
- `tests/`: Pytest suite (unit, integration, fixtures).
