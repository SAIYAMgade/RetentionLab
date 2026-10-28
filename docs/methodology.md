# RetentionLab: Analytical Methodology & Validation Protocol

## 1. Zero-Leakage Pipeline Architecture

Data leakage is the single most common failure mode in customer retention analytics. RetentionLab enforces a strict protocol:

1. **Temporal Horizon Immutability:**
   - Cutoff boundary: $T_0 =$ `2023-12-31 23:59:59`.
   - Observation window: $[2022-01-01, T_0]$.
   - Target outcome window: $[2024-01-01, 2024-03-31]$.
   - No event with timestamp $> T_0$ is accessible during feature engineering.

2. **Preprocessing Fitting Protocol:**
   - Imputers and Scalers (`StandardScaler`, `SimpleImputer`) are fitted strictly on $X_{\text{train}}$.
   - $X_{\text{test}}$ is transformed using frozen parameters learned on $X_{\text{train}}$.
   - Decision thresholds are selected on cross-validation or training splits, then applied to the held-out test split.

---

## 2. Statistical Validation Protocol

To assess behavioral divergence between active and churning customers, we evaluate distribution characteristics:

- **Normality Check:** Transaction amount and recency distributions display extreme positive skewness ($> 2.5$), violating normality assumptions required for standard Student's t-tests.
- **Non-Parametric Testing:** We employ two-sided and one-sided **Mann-Whitney U tests** to compare median ranks, computing the **rank-biserial correlation** ($r = 1 - \frac{2U}{n_1 n_2}$) as an unstandardized effect size.
- **Transformed Parametric Testing:** Total spend is evaluated using Welch's t-test with unequal variances under log-transformation ($\log(1 + x)$), reporting **Cohen's d** effect size.
- **Significance Criteria:** Standard $\alpha = 0.05$ threshold with reporting of exact p-values down to machine precision.

---

## 3. Threshold Calibration & Decision Science

In retention analytics, the standard default threshold ($p = 0.50$) is rarely optimal:

- **False Negatives Cost:** An at-risk high-value customer who is missed costs hundreds or thousands in lost lifetime gross margin.
- **False Positives Cost:** Sending an automated email to an active customer costs pennies, whereas calling an active customer with a heavy discount risks margin erosion.
- **Operational Objective:** RetentionLab parameterizes threshold selection to balance precision and recall, or to enforce a minimum operational recall (e.g. 70-75%) while maximizing precision to protect outreach ROI.
