# RetentionLab: Power BI Data Model Specification

## 1. Relational Schema Architecture (Star Schema)

The dashboard is structured around the primary fact table `Fact_CustomerPrioritization` linked to dimensional lookups and scenario parameter tables.

```
                  ┌───────────────────────────────┐
                  │    Dim_PrioritySegment        │
                  │───────────────────────────────│
                  │ SegmentKey (PK)               │
                  │ PrioritySegment               │
                  │ RiskTier                      │
                  │ MonetaryTier                  │
                  │ RecommendedAction             │
                  │ ActionChannel                 │
                  └───────────────┬───────────────┘
                                  │ 1
                                  │
                                  │ *
                  ┌───────────────┴───────────────┐
                  │   Fact_CustomerPrioritization │
                  │───────────────────────────────│
                  │ customer_id (PK)              │
                  │ prediction_date               │
                  │ risk_score                    │
                  │ risk_tier                     │
                  │ monetary_tier                 │
                  │ priority_segment              │
                  │ recency_days                  │
                  │ transaction_frequency         │
                  │ total_spend                   │
                  │ primary_risk_driver           │
                  │ action_channel                │
                  └───────────────┬───────────────┘
                                  │
                                  │ (Cross-filtering / Isolated)
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        │                                                   │
┌───────┴───────────────────────┐   ┌───────────────────────┴───────┐
│     Dim_ModelComparison       │   │    Fact_RetentionScenarios    │
│───────────────────────────────│   │───────────────────────────────│
│ ModelKey (PK)                 │   │ ScenarioKey (PK)              │
│ model_name                    │   │ hypothetical_budget           │
│ threshold                     │   │ cost_per_contact              │
│ roc_auc                       │   │ max_customers_contacted       │
│ pr_auc                        │   │ projected_retained_customers  │
│ precision                     │   │ projected_spend_protected     │
│ recall                        │   │ projected_roi_ratio           │
│ f1_score                      │   │ scenario_assumption_notice    │
└───────────────────────────────┘   └───────────────────────────────┘
```

---

## 2. Table Column Mappings & Types

### 1. `Fact_CustomerPrioritization`
| Field | Type | Description |
|---|---|---|
| `customer_id` | Text | Unique Customer Identifier (e.g. CUST_00124) |
| `prediction_date` | Date | Cutoff Date (2023-12-31) |
| `risk_score` | Decimal Number (0.0000 - 1.0000) | Logistic Regression predicted probability of inactivity |
| `risk_tier` | Text | High Risk (>=0.65), Medium Risk (0.40-0.65), Low Risk (<0.40) |
| `monetary_tier` | Text | High Value (>=75th pctl), Medium Value (40-75th), Low Value (<40th) |
| `priority_segment` | Text | Strategic segment name (e.g. Tier 1: High-Value At-Risk) |
| `recency_days` | Whole Number | Days since last qualifying purchase as of cutoff |
| `transaction_frequency` | Whole Number | Lifetime completed purchases |
| `total_spend` | Decimal Number (Currency) | Lifetime cumulative gross spend ($) |
| `primary_risk_driver` | Text | Behavioral root cause (e.g. Dormancy >90d, Frequency drop) |
| `recommended_action` | Text | Prescribed intervention play |
| `action_channel` | Text | Delivery medium (Phone / Dedicated Rep, Email & SMS, Mobile Push) |

### 2. `Dim_ModelComparison`
| Field | Type | Description |
|---|---|---|
| `model_name` | Text | Classifier Name (LogisticRegression, Baseline, KNN, RandomForest, GradientBoosting) |
| `threshold` | Decimal Number | Calibrated decision cutoff |
| `roc_auc` | Decimal Number | Area under ROC curve on held-out test set |
| `pr_auc` | Decimal Number | Area under Precision-Recall curve |
| `precision` | Decimal Number (Percentage) | Precision at threshold |
| `recall` | Decimal Number (Percentage) | Recall at threshold |
| `f1_score` | Decimal Number | Harmonic mean of precision and recall |
| `brier_score` | Decimal Number | Calibration error score |

### 3. `Fact_RetentionScenarios`
| Field | Type | Description |
|---|---|---|
| `hypothetical_budget` | Decimal Number (Currency) | Modeled budget ($5,000, $10,000, $25,000, $50,000) |
| `cost_per_contact` | Decimal Number (Currency) | Unit intervention cost ($15.00) |
| `max_customers_contacted` | Whole Number | Total reachable customers |
| `high_value_customers_targeted` | Whole Number | Reachable high-value customers |
| `projected_retained_customers` | Whole Number | Model-estimated retained customers |
| `portfolio_spend_exposed` | Decimal Number (Currency) | Gross spend of targeted audience |
| `projected_spend_protected` | Decimal Number (Currency) | Estimated retained spend |
| `projected_roi_ratio` | Decimal Number | Net gain over budget ratio |
