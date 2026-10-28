# RetentionLab: Power BI DAX Measures Repository

This document contains production DAX measure definitions for the RetentionLab Power BI reporting model.

---

## 1. Portfolio Volume & Customer Base Measures

### 1.1 Total Customers Evaluated
```dax
Total Customers Evaluated = 
COUNTROWS('Fact_CustomerPrioritization')
```

### 1.2 High-Risk Customer Count
```dax
High Risk Customer Count = 
CALCULATE(
    COUNTROWS('Fact_CustomerPrioritization'),
    'Fact_CustomerPrioritization'[risk_tier] = "High Risk"
)
```

### 1.3 High-Risk Inactivity Rate (%)
```dax
High Risk Customer Rate = 
DIVIDE(
    [High Risk Customer Count],
    [Total Customers Evaluated],
    0
)
```

### 1.4 Medium-Risk Customer Count
```dax
Medium Risk Customer Count = 
CALCULATE(
    COUNTROWS('Fact_CustomerPrioritization'),
    'Fact_CustomerPrioritization'[risk_tier] = "Medium Risk"
)
```

### 1.5 Retained / Low-Risk Customer Count
```dax
Low Risk Customer Count = 
CALCULATE(
    COUNTROWS('Fact_CustomerPrioritization'),
    'Fact_CustomerPrioritization'[risk_tier] = "Low Risk"
)
```

---

## 2. Revenue & Financial Exposure Measures

### 2.1 Total Portfolio Revenue
```dax
Total Portfolio Revenue = 
SUM('Fact_CustomerPrioritization'[total_spend])
```

### 2.2 High-Risk Revenue Exposure ($)
```dax
High Risk Revenue Exposure = 
CALCULATE(
    SUM('Fact_CustomerPrioritization'[total_spend]),
    'Fact_CustomerPrioritization'[risk_tier] = "High Risk"
)
```

### 2.3 High-Risk Revenue Exposure Share (%)
```dax
High Risk Revenue Share Pct = 
DIVIDE(
    [High Risk Revenue Exposure],
    [Total Portfolio Revenue],
    0
)
```

### 2.4 Tier 1 High-Value At-Risk Revenue ($)
```dax
Tier 1 At-Risk Revenue = 
CALCULATE(
    SUM('Fact_CustomerPrioritization'[total_spend]),
    'Fact_CustomerPrioritization'[priority_segment] = "Tier 1: High-Value At-Risk (Immediate Action)"
)
```

---

## 3. Average Customer Behavioral Metrics

### 3.1 Average Portfolio Recency (Days)
```dax
Avg Recency Days = 
AVERAGE('Fact_CustomerPrioritization'[recency_days])
```

### 3.2 High-Risk Average Recency (Days)
```dax
High Risk Avg Recency Days = 
CALCULATE(
    AVERAGE('Fact_CustomerPrioritization'[recency_days]),
    'Fact_CustomerPrioritization'[risk_tier] = "High Risk"
)
```

### 3.3 Average Lifetime Orders
```dax
Avg Lifetime Orders = 
AVERAGE('Fact_CustomerPrioritization'[transaction_frequency])
```

### 3.4 Average Customer Spend (AOV)
```dax
Avg Customer Spend = 
AVERAGE('Fact_CustomerPrioritization'[total_spend])
```

---

## 4. Scenario Planning Measures

### 4.1 Selected Hypothetical Budget ($)
```dax
Selected Budget = 
SELECTEDVALUE(
    'Fact_RetentionScenarios'[hypothetical_budget],
    10000
)
```

### 4.2 Projected Retained Customers
```dax
Projected Retained Customers = 
SUM('Fact_RetentionScenarios'[projected_retained_customers])
```

### 4.3 Projected Revenue Saved ($)
```dax
Projected Spend Protected = 
SUM('Fact_RetentionScenarios'[projected_spend_protected])
```

### 4.4 Scenario Net Return ($)
```dax
Projected Net Value = 
[Projected Spend Protected] - [Selected Budget]
```

### 4.5 Projected Return on Investment Ratio (ROI)
```dax
Scenario Projected ROI = 
DIVIDE(
    [Projected Net Value],
    [Selected Budget],
    0
)
```
