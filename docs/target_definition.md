# RetentionLab Churn Target Definition & Temporal Framing

## Prediction Problem Framing

Churn prediction in subscription and contractual B2B SaaS is modeled as a **snapshot observation problem** with strict temporal non-overlap.

```
Historical Observation Window (180 Days)       Snapshot Date (T)       Prediction Horizon (60 Days)
[============================================]|=======================>[----------------------------]
2025-10-03                             2026-04-01                       2026-05-31
(44 Features computed here strictly <= T)                                (Target 'is_churn' evaluated here > T)
```

### Definitions:
1. **Observation Snapshot Date ($T$)**: `2026-04-01`.
2. **Historical Observation Window**: Trailing 180 calendar days ($[T - 180\text{d}, T]$), with sub-windows of 30d, 60d, 90d, and 180d.
3. **Prediction Horizon**: 60 calendar days following the snapshot date ($(T, T + 60\text{d}]$).
4. **Target Label (`is_churn`)**:
   - `is_churn = 1`: The customer recorded **0 qualifying/successful transactions** during the 60-day prediction horizon.
   - `is_churn = 0`: The customer recorded **1 or more qualifying/successful transactions** during the 60-day prediction horizon.
5. **Eligibility Rules**:
   - Customers must have signed up at least 30 days prior to snapshot date ($\text{tenure\_days} \ge 30$).
   - Accounts registered $< 30$ days before snapshot are marked ineligible to prevent new-account volatility distortion.
