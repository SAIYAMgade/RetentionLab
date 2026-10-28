# RetentionLab: Comprehensive Data Dictionary

This document details every table and column across the RetentionLab relational data architecture.

---

## 1. `raw_transactions`
| Column Name | Data Type | Nullable | Description | Sample Value |
|---|---|---|---|---|
| `transaction_id` | VARCHAR(64) | NO | Unique transaction identifier | `TXN_10000001` |
| `customer_id` | VARCHAR(64) | NO | Customer identifier | `CUST_00124` |
| `transaction_date` | TIMESTAMP | NO | Transaction event timestamp | `2023-04-12 14:22:10` |
| `transaction_amount` | NUMERIC(12,2)| NO | Transaction gross monetary value in USD | `125.50` |
| `transaction_type` | VARCHAR(32) | NO | purchase, refund | `purchase` |
| `transaction_status` | VARCHAR(32) | NO | completed, failed, reversed | `completed` |
| `product_category` | VARCHAR(64) | NO | Merchandise category | `Electronics` |
| `channel` | VARCHAR(32) | NO | Web, Mobile App, In-Store | `Web` |
| `currency` | VARCHAR(8) | NO | Currency denomination | `USD` |
| `source_system` | VARCHAR(64) | NO | Originating system | `WEB_CHECKOUT` |

---

## 2. `cleaned_transactions`
Contains deduplicated, validated, and type-standardized transaction records.
- Adds `transaction_timestamp` (Indexed TIMESTAMP).
- Adds `transaction_date_str` (Formatted ISO date string).

---

## 3. `customer_features`
Contains all 44 behavioral features evaluated as of `2023-12-31 23:59:59`.
- Refer to [feature_catalogue.md](feature_catalogue.md) for full descriptions of all 44 features.

---

## 4. `target_labels`
Contains ground-truth inactivity outcomes observed across the future window (`2024-01-01` to `2024-03-31`).
| Column Name | Data Type | Description |
|---|---|---|
| `customer_id` | VARCHAR(64) | Customer reference |
| `prediction_date` | DATE | Observation boundary (`2023-12-31`) |
| `tenure_days` | INTEGER | Observed tenure at boundary |
| `future_purchases` | INTEGER | Completed purchases in future window |
| `is_inactive` | INTEGER | Binary target (1 if 0 future purchases, 0 if $\ge 1$) |

---

## 5. `model_predictions`
Stores model inferences across evaluated candidate algorithms.
| Column Name | Data Type | Description |
|---|---|---|
| `customer_id` | VARCHAR(64) | Customer reference |
| `model_name` | VARCHAR(64) | Classifier architecture name |
| `model_version` | VARCHAR(32) | Model semantic version |
| `prediction_date` | DATE | Cutoff date |
| `inactivity_probability` | NUMERIC(6,4)| Model estimated probability of inactivity |
| `predicted_label` | INTEGER | Binary decision output |
| `threshold_used` | NUMERIC(6,4)| Decision cutoff applied |

---

## 6. `customer_prioritization`
Consolidated operational action table linking risk scores with customer lifetime value.
| Column Name | Data Type | Description |
|---|---|---|
| `customer_id` | VARCHAR(64) | Customer identifier |
| `prediction_date` | DATE | Scoring cutoff date |
| `risk_score` | NUMERIC(6,4)| Calibrated inactivity probability |
| `risk_tier` | VARCHAR(32) | High Risk, Medium Risk, Low Risk |
| `monetary_tier` | VARCHAR(32) | High Value, Medium Value, Low Value |
| `priority_segment` | VARCHAR(64) | Operational retention segment name |
| `recency_days` | INTEGER | Days since last purchase |
| `transaction_frequency`| INTEGER | Lifetime purchases |
| `total_spend` | NUMERIC(12,2)| Cumulative lifetime gross spend |
| `primary_risk_driver` | VARCHAR(128)| Diagnostic root cause description |
| `recommended_action` | VARCHAR(256)| Prescribed intervention strategy |
| `action_channel` | VARCHAR(64) | Delivery medium |
| `model_version` | VARCHAR(32) | Model version applied |
