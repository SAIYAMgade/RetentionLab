# RetentionLab Certified DAX Measures Catalog

Every DAX measure below includes explicit filter-context behavior, denominators, and business interpretation.

---

### 1. Total Customers
```dax
Total Customers = 
DISTINCTCOUNT(CUSTOMER_DIMENSION[customer_id])
```
*Business Purpose*: Total count of unique registered customers in the current filter context.

---

### 2. Eligible Scored Customers
```dax
Eligible Scored Customers = 
CALCULATE(
    DISTINCTCOUNT(CUSTOMER_RISK_FACT[customer_id]),
    CUSTOMER_RISK_FACT[churn_probability] >= 0
)
```
*Business Purpose*: Count of customers meeting the 30-day minimum tenure requirement evaluated at snapshot date.

---

### 3. Total Transactions
```dax
Total Transactions = 
COUNTROWS(TRANSACTION_FACT)
```
*Business Purpose*: Total completed transaction records in the fact table (>97,000 baseline).

---

### 4. Gross Merchandise Value (GMV)
```dax
Gross Revenue = 
CALCULATE(
    SUM(TRANSACTION_FACT[transaction_amount]),
    TRANSACTION_FACT[transaction_status] = "Success"
)
```
*Business Purpose*: Gross booked transaction revenue across successful orders.

---

### 5. Average Transaction Value (ATV)
```dax
Average Transaction Value = 
DIVIDE(
    [Gross Revenue],
    CALCULATE(
        COUNTROWS(TRANSACTION_FACT),
        TRANSACTION_FACT[transaction_status] = "Success"
    ),
    0
)
```
*Business Purpose*: Mean gross order value.

---

### 6. Average Estimated Churn Probability
```dax
Average Churn Probability = 
AVERAGE(CUSTOMER_RISK_FACT[churn_probability])
```
*Business Purpose*: Portfolio average probabilistic churn propensity.

---

### 7. High & Critical Risk Customer Count
```dax
High Risk Customer Count = 
CALCULATE(
    COUNTROWS(CUSTOMER_RISK_FACT),
    CUSTOMER_RISK_FACT[risk_band] IN { "Critical Risk", "High Risk" }
)
```
*Business Purpose*: Number of active accounts requiring immediate retention monitoring.

---

### 8. High Risk Customer Share (%)
```dax
High Risk Customer Share = 
DIVIDE(
    [High Risk Customer Count],
    [Eligible Scored Customers],
    0
)
```
*Business Purpose*: Proportion of eligible portfolio identified in acute risk tiers.

---

### 9. Top 15% Prioritized Cohort Count
```dax
Top Cohort Customer Count = 
CALCULATE(
    COUNTROWS(CUSTOMER_RISK_FACT),
    CUSTOMER_RISK_FACT[is_top_15_percent] = 1
)
```
*Business Purpose*: Exact count of accounts assigned to the operational review worklist.

---

### 10. Total Portfolio Risk-Weighted Exposure
```dax
Portfolio Risk Exposure = 
SUM(CUSTOMER_RISK_FACT[risk_weighted_exposure])
```
*Business Purpose*: Aggregate risk-weighted exposure across the portfolio (`Churn Probability * Annualized Spend`).

---

### 11. Top Cohort Risk-Weighted Exposure
```dax
Top Cohort Risk Exposure = 
CALCULATE(
    SUM(CUSTOMER_RISK_FACT[risk_weighted_exposure]),
    CUSTOMER_RISK_FACT[is_top_15_percent] = 1
)
```
*Business Purpose*: Risk-weighted historical value concentrated within the prioritized top 15% worklist.

---

### 12. Top Cohort Exposure Concentration (%)
```dax
Top Cohort Exposure Concentration = 
DIVIDE(
    [Top Cohort Risk Exposure],
    [Portfolio Risk Exposure],
    0
)
```
*Business Purpose*: Share of total portfolio risk captured by the top 15% cohort (evaluates Pareto efficiency).

---

### 13. Payment Failure Rate (%)
```dax
Payment Failure Rate = 
DIVIDE(
    CALCULATE(COUNTROWS(TRANSACTION_FACT), TRANSACTION_FACT[payment_status] = "Failed"),
    COUNTROWS(TRANSACTION_FACT),
    0
)
```
*Business Purpose*: Percentage of attempted transactions resulting in gateway or settlement failure.
