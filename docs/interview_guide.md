# RetentionLab: Technical Interview & Defense Guide

This guide prepares engineers and data scientists to walk hiring managers and senior architects through the design choices, trade-offs, and failure modes of RetentionLab.

---

## 1. Top 5 Questions & Defensible Answers

### Q1: How did you define customer churn in a non-contractual business?
**Answer:**
> "In non-contractual commerce, customers don't send cancellation notices. We formulated churn operationally as a 90-day window of complete purchasing inactivity following a designated prediction timestamp ($T_0 = 2023-12-31$). If a customer completed zero qualifying purchases in Q1 2024, they were labeled inactive.
> We also enforced an eligibility requirement: customers had to have at least 30 days of observed tenure prior to $T_0$. This prevented misclassifying newly acquired customers who simply hadn't reached their second natural purchase cycle yet."

### Q2: How did you prevent data leakage between features and outcomes?
**Answer:**
> "We enforced strict temporal splitting. Every one of the 44 behavioral features was derived strictly using transactions timestamped on or before $2023-12-31 23:59:59$. Future transactions in Q1 2024 were only used to construct the ground-truth target vector $y$.
> Furthermore, all data transformations (scaling and median imputation) were encapsulated inside Scikit-learn `Pipeline` objects fitted strictly on the 80% training split, preventing any test set distribution statistics from leaking into training."

### Q3: Why didn't you achieve >0.85 ROC-AUC? What caused the discrepancy with prior benchmark claims?
**Answer:**
> "A prior external claim reported an ROC-AUC of 0.866 and recall of 79.1%. When we built and audited the pipeline with zero-leakage constraints, our models achieved an honest, reproducible ROC-AUC of **0.771 - 0.783** across Logistic Regression, Random Forest, and Gradient Boosting.
> In real customer behavior, churn is stochastic: some frequent customers pause unexpectedly, while some dormant customers re-engage organically. Achieving >0.85 on transactional churn usually signals either feature leakage (e.g. including refund transactions or session activity that occurred after the prediction timestamp) or synthetic over-simplification. We prioritized realistic, defensible analytics over manufactured scores."

### Q4: Why select Logistic Regression for production scoring if Random Forest had a slightly higher ROC-AUC?
**Answer:**
> "Random Forest achieved 0.783 vs Logistic Regression's 0.771 (+0.012 AUC). However, Logistic Regression offers critical advantages in business operations:
> 1. **Direct Probabilistic Interpretability:** Well-calibrated probabilities (Brier score 0.141) allow linear prioritization without complex Platt scaling.
> 2. **Auditable Risk Drivers:** Standardized coefficients clearly map to operational drivers (`recency_days`, `frequency_ratio_30_to_90`), enabling automated prescriptive recommendations for account reps.
> 3. **SQL Portability:** Logistic regression weights can be translated directly into a simple SQL scoring view, eliminating heavy inference dependencies in production."

### Q5: How do you translate predictions into business actions without claiming guaranteed ROI?
**Answer:**
> "We built a Prioritization Matrix combining model risk scores with customer spend percentiles. High-risk, high-value accounts are prioritized for high-touch human outreach, whereas lower-value at-risk accounts receive low-cost automated email/SMS plays.
> For financial evaluation, we built an explicit Scenario Analysis module with clear governance notices: historical spend is not guaranteed future revenue, and response rates must be treated as hypothetical scenarios until validated through randomized A/B holdout testing."
