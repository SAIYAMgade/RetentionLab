# Model Card: RetentionLab Churn Prediction Models

## Model Overview
- **Model Name**: RetentionLab HistGradientBoosting Classifier (Champion) & Logistic Regression (Interpretable Baseline).
- **Model Version**: 2.0.0
- **Model Type**: Supervised Binary Classification.
- **Primary Objective**: Estimate customer-level churn probability over a 60-day prediction horizon following a quarterly scoring snapshot.
- **Framework**: `scikit-learn` Pipeline with median imputation and standard scaling.

## Training Data & Splits
- **Source**: Deterministic synthetic relational enterprise dataset (Seed: 42).
- **Total Eligible Population**: 4,850 accounts with $\ge 30$ days tenure at snapshot `2026-04-01`.
- **Training Partition (70%)**: 3,396 accounts (34.0% churn prevalence).
- **Validation Partition (15%)**: 727 accounts (34.3% churn prevalence).
- **Holdout Test Partition (15%)**: 727 accounts (34.1% churn prevalence).

## Quantitative Evaluation on Holdout Test Set

| Metric | HistGradientBoosting (Champion) | Random Forest | Logistic Regression (Baseline) |
| :--- | :--- | :--- | :--- |
| **ROC-AUC** | **0.9395** | 0.9398 | 0.9144 |
| **PR-AUC** | **0.9244** | 0.9234 | 0.8949 |
| **F1-Score** | **0.8506** | 0.8462 | 0.8105 |
| **Precision** | **0.9893** | 0.9639 | 0.8815 |
| **Recall** | **0.7460** | 0.7540 | 0.7500 |
| **Brier Score** | **0.0573** | 0.0592 | 0.0768 |
| **Decision Threshold** | **0.74** | 0.58 | 0.61 |

## Ethical Considerations & Fairness
- **Protected Attributes**: Models strictly exclude personal demographic indicators (race, gender, age, personal address).
- **Intended Use**: Operational prioritization for Customer Success Managers to schedule proactive reviews, assist with technical blockers, or resolve billing friction.
- **Prohibited Use**: Automated denial of service, unilateral cancellation of contracts, or discriminatory pricing.
