# RetentionLab: Model Card

## 1. Model Details
- **Model Name:** RetentionLab Production Classifier (`LogisticRegression`)
- **Version:** `1.0.0`
- **Model Type:** L2-Regularized Logistic Regression with balanced class weighting and standardized features.
- **Trained By:** RetentionLab Analytical Engine.
- **License:** MIT License.

---

## 2. Intended Use
- **Primary Intended Use:** To score customer accounts at prediction boundaries, estimating probability of operational inactivity during the subsequent 90 days.
- **Downstream Applications:** Prioritizing retention marketing outreach, allocating VIP customer success resources, and parameterizing budget scenarios.
- **Out-of-Scope Uses:** Autonomous account termination, credit underwriting, individual personal profiling, or claims of guaranteed causal retention.

---

## 3. Training & Validation Setup
- **Dataset:** 109,308 transactional records across 8,500 customers spanning 2022-01-01 to 2024-03-31.
- **Eligible Training Universe:** 8,486 customers meeting the $\ge 30$-day tenure criterion at cutoff (2023-12-31).
- **Split Strategy:** 80% Train ($N=6,788$), 20% Held-Out Test ($N=1,698$), stratified on target label.
- **Target Distribution:** 21.6% inactive in future 90-day window ($N=1,833$), 78.4% active ($N=6,653$).

---

## 4. Performance Metrics (Held-Out Test Set)

| Model Architecture | Threshold | ROC-AUC | PR-AUC | Precision | Recall | F1-Score | Brier Score |
|---|---|---|---|---|---|---|---|
| **Random Forest** | 0.55 | **0.7832** | 0.5342 | 44.9% | 59.4% | 0.5111 | 0.1345 |
| **Gradient Boosting** | 0.31 | 0.7795 | **0.5410** | **51.0%** | 53.7% | **0.5232** | 0.1332 |
| **Logistic Regression** (Prod) | 0.54 | 0.7709 | 0.5218 | 41.3% | 68.1% | 0.5144 | 0.1410 |
| **K-Nearest Neighbors** | 0.10 | 0.7372 | 0.4289 | 27.7% | **89.6%** | 0.4226 | 0.1782 |
| **Heuristic Baseline** (Recency > 90d) | 0.19 | 0.6475 | 0.3391 | 29.5% | 63.5% | 0.4028 | 0.1950 |

### Discrepancy Note Regarding Prior Claimed Metrics
- A prior benchmark claim reported ROC-AUC of 0.866 and recall of 79.1%.
- Our rigorous zero-leakage evaluation observed **ROC-AUC of 0.771 - 0.783** across linear and ensemble models.
- **Root Cause Analysis:** Models achieving >0.85 AUC on transactional churn often suffer from subtle target leakage (e.g. including refund transactions or session activity that occurred after the prediction timestamp, or over-simplifying synthetic customer behavior into deterministic rules). RetentionLab models realistic behavioral variance where loyal customers occasionally pause and occasional customers re-activate.

---

## 5. Feature Importance & Coefficients (Logistic Regression)

| Rank | Feature | Standardized Coeff ($\beta$) | Direction | Business Interpretation |
|---|---|---|---|---|
| 1 | `recency_days` | +1.184 | Inactivity Indicator | Extended dormancy strongly increases churn risk. |
| 2 | `recency_to_avg_interval_ratio` | +0.642 | Inactivity Indicator | Being overdue relative to personal cadence signals drop-off. |
| 3 | `frequency_ratio_30_to_90` | -0.589 | Retention Protector | Recent acceleration in orders sharply decreases risk. |
| 4 | `active_month_ratio` | -0.472 | Retention Protector | Regular calendar engagement protects against dormancy. |
| 5 | `total_transactions` | -0.381 | Retention Protector | Repeat purchase depth builds habituation. |
| 6 | `refund_rate` | +0.194 | Inactivity Indicator | High product returns indicate satisfaction friction. |

---

## 6. Caveats & Ethical Considerations
- **No Causal Guarantee:** Model coefficients represent associative signals in historical observational data, not causal treatment effects.
- **Demographic Neutrality:** The model utilizes strictly behavioral transaction logs; no protected demographic or personal attributes are used.
