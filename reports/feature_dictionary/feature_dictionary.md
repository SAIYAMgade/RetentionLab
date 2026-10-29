# RetentionLab: 44-Feature Behavioral Engineering Catalog

This document specifies the exact 44 behavioral features engineered at the customer-snapshot level.

## Feature Architecture

The 44 behavioral features are organized into six distinct vectors:
- **Vector A: Recency & Frequency (Features 1–10)**
- **Vector B: Spending Behavior (Features 11–22)**
- **Vector C: Engagement & Product Diversity (Features 23–30)**
- **Vector D: Payment & Service Friction (Features 31–35)**
- **Vector E: Account & Engagement Maturity (Features 36–42)**
- **Vector F: Additional Behavioral Variation (Features 43–44)**

---

## Detailed Feature Catalog

| # | Feature Name | Vector | Unit | Calculation Formula | Business Description | Risk Relationship |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `days_since_last_transaction` | A | days | $T - \max(t_{\text{txn}})$ | Days elapsed since most recent completed transaction | Higher -> Greater Risk |
| 2 | `transaction_count_30d` | A | count | Count of successful txns in $[T-30\text{d}, T]$ | Order count in trailing 30 days | Lower -> Greater Risk |
| 3 | `transaction_count_60d` | A | count | Count of successful txns in $[T-60\text{d}, T]$ | Order count in trailing 60 days | Lower -> Greater Risk |
| 4 | `transaction_count_90d` | A | count | Count of successful txns in $[T-90\text{d}, T]$ | Order count in trailing 90 days | Lower -> Greater Risk |
| 5 | `active_days_30d` | A | days | Distinct days with activity in $[T-30\text{d}, T]$ | Days active on platform in 30 days | Lower -> Greater Risk |
| 6 | `active_days_90d` | A | days | Distinct days with activity in $[T-90\text{d}, T]$ | Days active on platform in 90 days | Lower -> Greater Risk |
| 7 | `avg_days_between_transactions` | A | days | Mean gap between consecutive txns in 180d | Average purchasing interval | Higher -> Greater Risk |
| 8 | `std_days_between_transactions` | A | days | Standard dev of gaps between txns in 180d | Purchasing cadence volatility | Higher -> Greater Risk |
| 9 | `transaction_count_trend_30d` | A | ratio | $\text{txns}_{30\text{d}} / (\text{txns}_{\text{prior } 30\text{d}} + 1)$ | 30-day velocity momentum | Lower -> Greater Risk |
| 10 | `transaction_count_trend_60d` | A | ratio | $\text{txns}_{60\text{d}} / (\text{txns}_{\text{prior } 60\text{d}} + 1)$ | 60-day velocity momentum | Lower -> Greater Risk |
| 11 | `total_spend_30d` | B | USD | Sum of successful txn amounts in 30d | Gross expenditure in trailing 30 days | Lower -> Greater Risk |
| 12 | `total_spend_90d` | B | USD | Sum of successful txn amounts in 90d | Gross expenditure in trailing 90 days | Lower -> Greater Risk |
| 13 | `total_spend_180d` | B | USD | Sum of successful txn amounts in 180d | Gross expenditure in trailing 180 days | Lower -> Greater Risk |
| 14 | `avg_transaction_value_90d` | B | USD | Mean txn amount in 90d | Average basket size in 90 days | Lower -> Greater Risk |
| 15 | `median_transaction_value_90d` | B | USD | Median txn amount in 90d | Robust order value proxy | Lower -> Greater Risk |
| 16 | `std_transaction_value_90d` | B | USD | Std dev of txn amount in 90d | Spend dispersion | Contextual |
| 17 | `max_transaction_value_90d` | B | USD | Max single order amount in 90d | Peak transaction commitment | Lower -> Greater Risk |
| 18 | `spend_trend_30d` | B | ratio | $\text{spend}_{30\text{d}} / (\text{spend}_{\text{prior } 30\text{d}} + 1)$ | Short-term spend velocity | Lower -> Greater Risk |
| 19 | `spend_trend_90d` | B | ratio | $\text{spend}_{90\text{d}} / (\text{spend}_{\text{prior } 90\text{d}} + 1)$ | Medium-term spend velocity | Lower -> Greater Risk |
| 20 | `refund_amount_90d` | B | USD | Sum of refund amounts in 90d | Total dollar refunds issued | Higher -> Greater Risk |
| 21 | `refund_rate_90d` | B | ratio | $\text{refunds}_{90\text{d}} / (\text{spend}_{90\text{d}} + \text{refunds}_{90\text{d}})$ | Refund share of booked spend | Higher -> Greater Risk |
| 22 | `discount_usage_rate_90d` | B | ratio | Count of discounted txns / total txns | Coupon sensitivity | Higher -> Risk Sensitivity |
| 23 | `distinct_product_categories_90d`| C | count | Unique product categories bought in 90d | Cross-category product stickiness | Lower -> Greater Risk |
| 24 | `distinct_products_90d` | C | count | Unique product SKUs bought in 90d | Catalog depth adoption | Lower -> Greater Risk |
| 25 | `distinct_channels_90d` | C | count | Unique channels used in 90d | Omnichannel presence | Lower -> Greater Risk |
| 26 | `weekend_transaction_ratio` | C | ratio | Weekend txns / total txns in 90d | Weekend operational activity | Neutral |
| 27 | `night_transaction_ratio` | C | ratio | Off-peak txns / total txns in 90d | Non-business hours activity | Neutral |
| 28 | `online_transaction_ratio` | C | ratio | (Web + API txns) / total txns in 90d | Digital self-serve adoption | Neutral |
| 29 | `mobile_transaction_ratio` | C | ratio | Mobile txns / total txns in 90d | Mobile app engagement | Neutral |
| 30 | `cancelled_transaction_rate_90d` | C | ratio | Cancelled orders / total attempts in 90d | Checkout abandonment rate | Higher -> Greater Risk |
| 31 | `failed_payment_rate_90d` | D | ratio | Failed payments / total payment attempts in 90d | Billing failure frequency | Higher -> Greater Risk |
| 32 | `support_tickets_90d` | D | count | Support tickets filed in 90d | Service friction volume | Higher -> Greater Risk |
| 33 | `complaints_180d` | D | count | Complaint-type tickets filed in 180d | Severe customer dissatisfaction | Higher -> Greater Risk |
| 34 | `returns_count_90d` | D | count | Refunded transactions in 90d | Frequency of return events | Higher -> Greater Risk |
| 35 | `days_since_last_support_ticket` | D | days | $T - \max(t_{\text{ticket}})$ | Service interaction recency | Lower -> Friction |
| 36 | `tenure_days` | E | days | $T - \text{signup\_date}$ | Account maturity in days | Lower -> Hazard |
| 37 | `days_since_last_login` | E | days | $T - \max(t_{\text{login}})$ | Authentication dormancy | Higher -> Greater Risk |
| 38 | `login_count_30d` | E | count | Platform logins in trailing 30 days | Short-term usage frequency | Lower -> Greater Risk |
| 39 | `login_count_90d` | E | count | Platform logins in trailing 90 days | Quarterly usage frequency | Lower -> Greater Risk |
| 40 | `email_open_rate_30d` | E | ratio | Opened emails / delivered emails in 30d | Communication receptivity | Lower -> Greater Risk |
| 41 | `campaign_response_rate_90d` | E | ratio | Responded touches / delivered touches in 90d | Outbound campaign responsiveness | Lower -> Greater Risk |
| 42 | `payment_delay_count_90d` | E | count | Delayed or retried payment attempts in 90d | Billing collection friction | Higher -> Greater Risk |
| 43 | `transaction_value_coefficient_of_variation_90d` | F | ratio | $\text{std\_val}_{90\text{d}} / (\text{avg\_val}_{90\text{d}} + 10^{-5})$ | Relative order size volatility | Higher -> Unpredictable |
| 44 | `active_week_ratio_90d` | F | ratio | Active calendar weeks / 13.0 in 90d | Quarterly consistency of engagement | Lower -> Greater Risk |
