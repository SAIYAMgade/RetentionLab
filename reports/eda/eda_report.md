# RetentionLab: Exploratory Data Analysis & Integrity Audit Report

## 1. Executive Dataset Overview
- **Customer Entity Volume**: 5,000 synthetic account profiles across 4 business tiers (Enterprise, Mid-Market, SMB, Startup).
- **Transaction Entity Volume**: 104,990 recorded orders spanning January 1, 2025 through May 31, 2026 (>97,000 target scale requirement).
- **Activity & Interaction Touchpoints**:
  - Platform Activity: 115,813 session authentications, dashboard views, and data exports.
  - Support Tickets: 7,115 cases with issue classification and customer satisfaction (CSAT) ratings.
  - Marketing Lifecycle: 32,655 email, webinar, and notification touches.
- **Relational Integrity**: 100% referential integrity across all foreign keys; 0 orphan records.

---

## 2. Relational Data Dictionary

| Table Name | Primary Key | Foreign Key(s) | Record Count | Description |
| :--- | :--- | :--- | :--- | :--- |
| `products` | `product_id` | - | 10 | Reference catalog of software modules and pricing tiers |
| `customers` | `customer_id` | - | 5,000 | Account demographics, acquisition channels, and signup dates |
| `transactions` | `transaction_id` | `customer_id`, `product_id` | 104,990 | Individual order line items, dollar amounts, and settlement statuses |
| `customer_activity` | `activity_id` | `customer_id` | 115,813 | Granular in-app usage events and authentication timestamps |
| `support_tickets` | `ticket_id` | `customer_id` | 7,115 | Customer service interactions, ticket categories, and CSAT scores |
| `campaign_interactions` | `interaction_id` | `customer_id` | 32,655 | Lifecycle outbound communications and engagement actions |
| `customer_snapshots` | `snapshot_id` | `customer_id` | 5,000 | Periodic observation records for model scoring |

---

## 3. Data Quality Findings & Schema Integrity
Six automated SQL validation assertions were executed against the relational database layer:
1. `customers_primary_key_uniqueness`: **0 duplicate IDs (PASS)**.
2. `transactions_primary_key_uniqueness`: **0 duplicate IDs (PASS)**.
3. `orphan_transactions_check`: **0 unmapped transaction records (PASS)**.
4. `non_negative_transaction_amounts`: **0 non-positive order values (PASS)**.
5. `temporal_order_txn_after_signup`: **0 orders occurring prior to customer signup (PASS)**.
6. `csat_score_bounds_validity`: **100% of CSAT ratings fall within [1, 5] (PASS)**.

---

## 4. Missing Value Analysis & Strategy
- Core transactional tables (`customers`, `transactions`, `products`) exhibit 0% missingness in primary and foreign keys.
- Behavioral aggregations (such as standard deviation of order values for accounts with only one order) are deterministically handled using domain-safe imputations:
  - Intervals between transactions: imputed with median historical interval (45.0 days) when transaction count < 2.
  - Volatility metrics: defaulted to `0.0`.
  - Inactive rates: filled with neutral values (`0.0` or `1.0` where logically appropriate).

---

## 5. Customer & Segment Distribution
- **Enterprise (15.0%)**: Low transaction frequency, high basket size (mean ATV: $3,200+), long tenure, lowest natural churn rate.
- **Mid-Market (30.0%)**: Steady monthly transactions, moderate ATV ($1,600+), balanced churn propensity.
- **SMB (35.0%)**: Higher order frequency, lower contract sizes ($800+), moderate sensitivity to payment friction.
- **Startup (20.0%)**: High early-tenure velocity, variable lifetime, elevated churn propensity under marketing disengagement.

---

## 6. Churn Target Label Distribution
- **Snapshot Date**: `2026-04-01`
- **Prediction Horizon**: 60 days (`2026-04-01` to `2026-05-31`).
- **Eligible Accounts** (Tenure $\ge$ 30 days): 4,850 accounts.
- **Observed Churn Label (`is_churn = 1`)**: 34.06% (1,652 accounts).
- **Observed Retention Label (`is_churn = 0`)**: 65.94% (3,198 accounts).
- The class distribution represents a realistic SaaS attrition pattern without extreme pathological imbalance.

---

## 7. Behavioral Trends Associated with Churn
Accounts that subsequently churned in the 60-day prediction horizon exhibited pronounced leading behavioral signals in the 90 days preceding snapshot:
1. **Recency Expansion**: At-risk accounts experienced a median of 48.2 days since last transaction at snapshot date, compared to 14.1 days for retained accounts.
2. **Velocity Decay**: 30-day transaction velocity dropped by an average of 64% relative to prior-month pace for churning accounts.
3. **Spend Contraction**: Trailing 30-day expenditure contracted by 58% on average prior to complete cessation of purchasing.
4. **Payment Friction**: At-risk accounts exhibited a 7.2x higher rate of failed billing transactions in the 90 days prior to snapshot.
5. **Support Dissatisfaction**: Complaint tickets were 4.1x more prevalent among future churners.

---

## 8. Data Leakage Prevention Guarantees
- Strict temporal boundary at $T =$ `2026-04-01`.
- Any transaction, activity, support ticket, or campaign logged with a timestamp $> T$ is strictly excluded from feature computation.
- Target labels (`is_churn`) are computed exclusively on future window data ($T < t \le T + 60\text{d}$) and never included as an input predictor.
- Preprocessing transformers (`StandardScaler`, `SimpleImputer`) are fitted solely on training partition data and applied downstream to validation and test holdouts.

---

## 9. Limitations of Synthetic Data
- While synthetic simulation allows rigorous mathematical validation of temporal separation and feature pipelines, it lacks uncontrolled real-world anomalies (e.g. sudden macroeconomic shocks, competitor launches).
- Findings establish probabilistic behavioral associations, not causal mechanisms.
