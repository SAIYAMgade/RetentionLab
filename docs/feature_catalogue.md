# RetentionLab: Behavioral Feature Catalogue

This catalogue documents all 44 customer behavioral features extracted by `retentionlab.features.builder` strictly prior to the prediction cutoff date.

---

## 1. Feature Taxonomy & Groupings

### 1. Recency Group (4 Features)
| Feature Name | Type | Formula / Logic | Business Rationale |
|---|---|---|---|
| `recency_days` | int | $T_0 - \max(t_{\text{purchase}})$ | Core recency indicator; dormancy depth. |
| `first_purchase_days` | int | $T_0 - \min(t_{\text{purchase}})$ | Customer lifetime tenure in days. |
| `days_between_last_two` | float | $t_{\text{last}} - t_{\text{second\_last}}$ | Immediate pre-cutoff purchase cycle gap. |
| `recency_to_avg_interval_ratio` | float | $\frac{\text{recency\_days}}{\text{avg\_interval} + 1}$ | Personalized recency relative to normal cadence. |

### 2. Frequency Group (10 Features)
| Feature Name | Type | Formula / Logic | Business Rationale |
|---|---|---|---|
| `total_transactions` | int | $\sum \mathbb{I}(\text{status}=\text{completed})$ | Baseline lifetime purchase volume. |
| `transactions_30d` | int | Purchases in $[T_0 - 30\text{d}, T_0]$ | Immediate short-term order frequency. |
| `transactions_60d` | int | Purchases in $[T_0 - 60\text{d}, T_0]$ | 2-month order volume. |
| `transactions_90d` | int | Purchases in $[T_0 - 90\text{d}, T_0]$ | Quarterly order volume. |
| `transactions_180d` | int | Purchases in $[T_0 - 180\text{d}, T_0]$ | Semi-annual order volume. |
| `transactions_365d` | int | Purchases in $[T_0 - 365\text{d}, T_0]$ | Trailing 12-month order volume. |
| `active_months` | int | Count of distinct calendar months with $\ge 1$ purchase | Seasonality and engagement consistency. |
| `active_month_ratio` | float | $\frac{\text{active\_months}}{\text{tenure\_months}}$ | Proportion of tenure months active. |
| `avg_monthly_transactions` | float | $\frac{\text{total\_transactions}}{\text{tenure\_months}}$ | Normalized order velocity. |
| `distinct_purchase_dates` | int | Distinct calendar dates of purchase | Distinguishes multiple daily orders from separate visits. |

### 3. Monetary Group (12 Features)
| Feature Name | Type | Formula / Logic | Business Rationale |
|---|---|---|---|
| `total_spend` | float | $\sum \text{amount}_{\text{purchase}}$ | Gross lifetime customer value. |
| `avg_transaction_amount` | float | Mean purchase spend | Average order value (AOV). |
| `median_transaction_amount` | float | Median purchase spend | Typical order value resilient to outliers. |
| `max_transaction_amount` | float | Maximum single purchase spend | Ceiling purchasing capacity. |
| `min_transaction_amount` | float | Minimum single purchase spend | Floor purchasing capacity. |
| `std_transaction_amount` | float | Std Dev of purchase spend | Basket size variability. |
| `spend_30d` | float | Spend in $[T_0 - 30\text{d}, T_0]$ | Immediate short-term spend. |
| `spend_60d` | float | Spend in $[T_0 - 60\text{d}, T_0]$ | 2-month spend. |
| `spend_90d` | float | Spend in $[T_0 - 90\text{d}, T_0]$ | Quarterly spend. |
| `spend_180d` | float | Spend in $[T_0 - 180\text{d}, T_0]$ | Semi-annual spend. |
| `spend_365d` | float | Spend in $[T_0 - 365\text{d}, T_0]$ | Trailing 12-month spend. |
| `avg_spend_per_active_month` | float | $\frac{\text{total\_spend}}{\text{active\_months}}$ | Economic value generated per active month. |

### 4. Behavioral Trends & Intervals Group (9 Features)
| Feature Name | Type | Formula / Logic | Business Rationale |
|---|---|---|---|
| `frequency_ratio_30_to_90` | float | $\frac{\text{tx\_30d}}{\text{tx\_90d}/3.0 + 0.01}$ | Short-term order frequency acceleration / decay. |
| `frequency_ratio_90_to_180` | float | $\frac{\text{tx\_90d}}{\text{tx\_180d}/2.0 + 0.01}$ | Medium-term order frequency acceleration / decay. |
| `spend_ratio_30_to_90` | float | $\frac{\text{spend\_30d}}{\text{spend\_90d}/3.0 + 0.05}$ | Short-term spend expansion / contraction. |
| `spend_ratio_90_to_180` | float | $\frac{\text{spend\_90d}}{\text{spend\_180d}/2.0 + 0.05}$ | Medium-term spend expansion / contraction. |
| `avg_interpurchase_days` | float | Mean interval between orders | Natural purchase cycle cadence. |
| `std_interpurchase_days` | float | Std Dev of order intervals | Cadence predictability vs volatility. |
| `max_interpurchase_days` | float | Maximum gap between orders | Longest historical dormancy period survived. |
| `interval_expansion_ratio` | float | $\frac{\text{days\_between\_last\_two}}{\text{avg\_interval} + 1}$ | Gap widening leading indicator. |
| `is_single_purchase_customer`| int | $\mathbb{I}(\text{total\_transactions} = 1)$ | Single-buyer indicator flag. |

### 5. Diversity, Channels & Friction Group (9 Features)
| Feature Name | Type | Formula / Logic | Business Rationale |
|---|---|---|---|
| `distinct_categories` | int | Distinct product categories | Cross-category engagement breadth. |
| `distinct_channels` | int | Distinct purchase channels | Omnichannel engagement depth. |
| `top_category_spend_share` | float | $\frac{\text{max\_category\_spend}}{\text{total\_spend}}$ | Category concentration index. |
| `top_channel_tx_share` | float | $\frac{\text{max\_channel\_tx}}{\text{total\_transactions}}$ | Channel loyalty concentration. |
| `mobile_app_tx_share` | float | Mobile purchases / total purchases | Mobile app adoption. |
| `web_tx_share` | float | Web purchases / total purchases | E-commerce web adoption. |
| `in_store_tx_share` | float | Store purchases / total purchases | Retail physical presence adoption. |
| `refund_count` | int | Count of completed refunds | Customer friction and dissatisfaction volume. |
| `refund_rate` | float | $\frac{\text{refunds}}{\text{purchases} + \text{refunds}}$ | Friction propensity. |
