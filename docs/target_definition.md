# RetentionLab: Operational Target & Churn Definition

## 1. Problem Formulation

In transactional non-contractual commerce, customers do not provide formal cancellation notices. Therefore, customer churn must be modeled as **operational inactivity**.

**Formal Objective:**
> At the prediction cutoff timestamp $T_0$ (`2023-12-31 23:59:59`), estimate the probability that an eligible customer will complete **zero** qualifying transactions during a future observation horizon $H$ (`2024-01-01` to `2024-03-31`, 90 days).

---

## 2. Mathematical Definition

Let $Y_i \in \{0, 1\}$ denote the binary inactivity label for eligible customer $i$:

$$
Y_i = \begin{cases}
1 & \text{if } \sum_{t \in [T_0 + 1, T_0 + H]} \mathbb{I}(\text{status}_t = \text{'completed'} \wedge \text{type}_t = \text{'purchase'} \wedge \text{amount}_t > 0) = 0 \\
0 & \text{if } \sum_{t \in [T_0 + 1, T_0 + H]} \mathbb{I}(\text{status}_t = \text{'completed'} \wedge \text{type}_t = \text{'purchase'} \wedge \text{amount}_t > 0) \ge 1
\end{cases}
$$

Where:
- $T_0$: Cutoff timestamp (`2023-12-31 23:59:59`).
- $H$: 90-day evaluation window (`2024-01-01` through `2024-03-31`).
- $\mathbb{I}$: Indicator function identifying qualifying purchases.

---

## 3. Customer Eligibility Rules

To prevent misleading target assignments, customers must meet strict eligibility constraints at $T_0$:

1. **Prior Purchase History:** The customer must have completed at least one qualifying purchase on or before $T_0$.
2. **Minimum Observed Tenure:** The customer's first completed purchase must have occurred on or before $T_0 - 30\text{ days}$ (`2023-12-01`). Customers acquired within the final 30 days of the observation window are excluded because their inter-purchase cycle has not had sufficient time to manifest, preventing artificial misclassification.
3. **Transaction Status:** Only `completed` transactions of type `purchase` with monetary amount $> \$0.00$ constitute activity. `Refunds`, `reversals`, and `failed` checkout attempts do not reset the inactivity timer.

---

## 4. Analytical Strengths & Limitations

### Strengths
- **Empirical Grounding:** Avoids arbitrary heuristic labels (e.g. labeling customers "churned" while they are still actively buying).
- **Temporal Realism:** Mirrors exact real-world production scoring cadence, where models score customer bases at quarter-end to plan next-quarter retention outreach.
- **Zero Leakage:** Strictly enforces an impermeable time boundary between historical behavioral inputs ($t \le T_0$) and outcome evaluation ($t > T_0$).

### Limitations
- **Dormancy vs. Permanent Churn:** A customer inactive during Q1 2024 may resume purchasing in Q3 2024. The operational label captures 90-day inactivity, not permanent brand abandonment.
- **Fixed-Horizon Sensitivity:** Customers with natural 120-day purchase cadences may be labeled inactive at 90 days despite normal behavior. This is accounted for by incorporating personalized recency features (`recency_to_avg_interval_ratio`).
