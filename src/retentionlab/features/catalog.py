"""
RetentionLab 44-Feature Behavioral Engineering Catalog.
Metadata definitions for all 44 behavioral features.
"""

from typing import Dict, List, Any

FEATURE_CATALOG: List[Dict[str, Any]] = [
    # A. Recency and frequency (1-10)
    {
        "name": "days_since_last_transaction",
        "category": "Recency & Frequency",
        "unit": "days",
        "formula": "snapshot_date - max(transaction_date)",
        "description": "Days elapsed since the customer's most recent completed transaction.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Default to historical window maximum (180 days)"
    },
    {
        "name": "transaction_count_30d",
        "category": "Recency & Frequency",
        "unit": "count",
        "formula": "count(successful txns in [T-30d, T])",
        "description": "Number of successful purchase transactions in the past 30 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "transaction_count_60d",
        "category": "Recency & Frequency",
        "unit": "count",
        "formula": "count(successful txns in [T-60d, T])",
        "description": "Number of successful purchase transactions in the past 60 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "transaction_count_90d",
        "category": "Recency & Frequency",
        "unit": "count",
        "formula": "count(successful txns in [T-90d, T])",
        "description": "Number of successful purchase transactions in the past 90 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "active_days_30d",
        "category": "Recency & Frequency",
        "unit": "days",
        "formula": "distinct days with transactions or logins in [T-30d, T]",
        "description": "Number of distinct calendar days with product or transactional activity in 30 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "active_days_90d",
        "category": "Recency & Frequency",
        "unit": "days",
        "formula": "distinct days with transactions or logins in [T-90d, T]",
        "description": "Number of distinct calendar days with product or transactional activity in 90 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "avg_days_between_transactions",
        "category": "Recency & Frequency",
        "unit": "days",
        "formula": "mean(diff(sorted transaction dates)) in [T-180d, T]",
        "description": "Average interval in days between consecutive transactions.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 45.0 (median window interval)"
    },
    {
        "name": "std_days_between_transactions",
        "category": "Recency & Frequency",
        "unit": "days",
        "formula": "std(diff(sorted transaction dates)) in [T-180d, T]",
        "description": "Standard deviation of intervals between consecutive transactions (volatility).",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "transaction_count_trend_30d",
        "category": "Recency & Frequency",
        "unit": "ratio",
        "formula": "transaction_count_30d / (transaction_count_prior_30d + 1)",
        "description": "Short-term momentum: transaction velocity in recent 30d relative to prior 30d.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Default 1.0 (neutral velocity)"
    },
    {
        "name": "transaction_count_trend_60d",
        "category": "Recency & Frequency",
        "unit": "ratio",
        "formula": "transaction_count_60d / (transaction_count_prior_60d + 1)",
        "description": "Medium-term momentum: transaction velocity in recent 60d relative to prior 60d.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Default 1.0 (neutral velocity)"
    },

    # B. Spending behavior (11-22)
    {
        "name": "total_spend_30d",
        "category": "Spending Behavior",
        "unit": "USD",
        "formula": "sum(amount of successful txns in [T-30d, T])",
        "description": "Total gross expenditure across successful orders in past 30 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "total_spend_90d",
        "category": "Spending Behavior",
        "unit": "USD",
        "formula": "sum(amount of successful txns in [T-90d, T])",
        "description": "Total gross expenditure across successful orders in past 90 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "total_spend_180d",
        "category": "Spending Behavior",
        "unit": "USD",
        "formula": "sum(amount of successful txns in [T-180d, T])",
        "description": "Total gross expenditure across successful orders in past 180 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "avg_transaction_value_90d",
        "category": "Spending Behavior",
        "unit": "USD",
        "formula": "mean(transaction_amount) in [T-90d, T]",
        "description": "Average order size across completed transactions in 90 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "median_transaction_value_90d",
        "category": "Spending Behavior",
        "unit": "USD",
        "formula": "median(transaction_amount) in [T-90d, T]",
        "description": "Median order value, robust to single enterprise outliers.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "std_transaction_value_90d",
        "category": "Spending Behavior",
        "unit": "USD",
        "formula": "std(transaction_amount) in [T-90d, T]",
        "description": "Standard deviation of order amounts in 90 days.",
        "risk_direction": "Neutral / Contextual",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "max_transaction_value_90d",
        "category": "Spending Behavior",
        "unit": "USD",
        "formula": "max(transaction_amount) in [T-90d, T]",
        "description": "Maximum single transaction amount recorded in 90 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "spend_trend_30d",
        "category": "Spending Behavior",
        "unit": "ratio",
        "formula": "total_spend_30d / (spend_prior_30d + 1)",
        "description": "Short-term spend velocity ratio (recent 30d vs prior 30d).",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Default 1.0"
    },
    {
        "name": "spend_trend_90d",
        "category": "Spending Behavior",
        "unit": "ratio",
        "formula": "total_spend_90d / (spend_prior_90d + 1)",
        "description": "Medium-term spend velocity ratio (recent 90d vs prior 90d).",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Default 1.0"
    },
    {
        "name": "refund_amount_90d",
        "category": "Spending Behavior",
        "unit": "USD",
        "formula": "sum(refund_amount) in [T-90d, T]",
        "description": "Total refunded dollar amount over the trailing 90 days.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "refund_rate_90d",
        "category": "Spending Behavior",
        "unit": "ratio",
        "formula": "refund_amount_90d / (total_spend_90d + refund_amount_90d + 1e-5)",
        "description": "Share of dollar volume refunded in 90 days.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "discount_usage_rate_90d",
        "category": "Spending Behavior",
        "unit": "ratio",
        "formula": "count(txns with discount > 0) / count(total txns) in [T-90d, T]",
        "description": "Proportion of orders utilizing promotional or coupon discounts.",
        "risk_direction": "Higher -> Sensitivity / Risk",
        "missing_handling": "Filled with 0.0"
    },

    # C. Engagement and product diversity (23-30)
    {
        "name": "distinct_product_categories_90d",
        "category": "Engagement & Diversity",
        "unit": "count",
        "formula": "count(distinct product_category) in [T-90d, T]",
        "description": "Breadth of product categories purchased; proxy for multi-product stickiness.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "distinct_products_90d",
        "category": "Engagement & Diversity",
        "unit": "count",
        "formula": "count(distinct product_id) in [T-90d, T]",
        "description": "Number of unique SKUs / modules purchased in 90 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "distinct_channels_90d",
        "category": "Engagement & Diversity",
        "unit": "count",
        "formula": "count(distinct transaction_channel) in [T-90d, T]",
        "description": "Number of distinct buying channels utilized (Web, API, Mobile, Partner).",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "weekend_transaction_ratio",
        "category": "Engagement & Diversity",
        "unit": "ratio",
        "formula": "count(weekend txns) / count(total txns) in [T-90d, T]",
        "description": "Proportion of transactions processed on Saturday or Sunday.",
        "risk_direction": "Neutral / Segment Specific",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "night_transaction_ratio",
        "category": "Engagement & Diversity",
        "unit": "ratio",
        "formula": "count(off_peak txns) / count(total txns) in [T-90d, T]",
        "description": "Proportion of transactions occurring outside standard business hours.",
        "risk_direction": "Neutral",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "online_transaction_ratio",
        "category": "Engagement & Diversity",
        "unit": "ratio",
        "formula": "count(Web or API txns) / count(total txns) in [T-90d, T]",
        "description": "Share of orders originating from self-serve online interfaces.",
        "risk_direction": "Neutral",
        "missing_handling": "Filled with 1.0 if no txns"
    },
    {
        "name": "mobile_transaction_ratio",
        "category": "Engagement & Diversity",
        "unit": "ratio",
        "formula": "count(Mobile txns) / count(total txns) in [T-90d, T]",
        "description": "Share of orders originating from mobile applications.",
        "risk_direction": "Neutral",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "cancelled_transaction_rate_90d",
        "category": "Engagement & Diversity",
        "unit": "ratio",
        "formula": "count(cancelled txns) / count(total attempts) in [T-90d, T]",
        "description": "Rate of cancelled orders indicating checkout abandonment or buyer second thoughts.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },

    # D. Payment and service friction (31-35)
    {
        "name": "failed_payment_rate_90d",
        "category": "Payment & Friction",
        "unit": "ratio",
        "formula": "count(failed payments) / count(payment attempts) in [T-90d, T]",
        "description": "Frequency of card declines, expired credentials, or bank settlement failures.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "support_tickets_90d",
        "category": "Payment & Friction",
        "unit": "count",
        "formula": "count(support_tickets in [T-90d, T])",
        "description": "Volume of customer support cases submitted in 90 days.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "complaints_180d",
        "category": "Payment & Friction",
        "unit": "count",
        "formula": "count(complaint-type tickets in [T-180d, T])",
        "description": "Severe friction count: explicit escalation or dissatisfaction complaints in 180 days.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "returns_count_90d",
        "category": "Payment & Friction",
        "unit": "count",
        "formula": "count(refunded transactions in [T-90d, T])",
        "description": "Number of distinct refund/return events initiated in 90 days.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "days_since_last_support_ticket",
        "category": "Payment & Friction",
        "unit": "days",
        "formula": "snapshot_date - max(ticket_date)",
        "description": "Recency of last customer service interaction.",
        "risk_direction": "Lower -> Recent Friction",
        "missing_handling": "Default to 180 (no recent tickets)"
    },

    # E. Account and engagement maturity (36-42)
    {
        "name": "tenure_days",
        "category": "Account Maturity",
        "unit": "days",
        "formula": "snapshot_date - signup_date",
        "description": "Account age in days as of the scoring snapshot date.",
        "risk_direction": "Lower -> Early-Life Hazard",
        "missing_handling": "Strictly required; calculated from signup_date"
    },
    {
        "name": "days_since_last_login",
        "category": "Account Maturity",
        "unit": "days",
        "formula": "snapshot_date - max(login_date)",
        "description": "Days since the customer last authenticated into the platform.",
        "risk_direction": "Higher -> Greater Inactivity",
        "missing_handling": "Default to 90"
    },
    {
        "name": "login_count_30d",
        "category": "Account Maturity",
        "unit": "count",
        "formula": "count(logins in [T-30d, T])",
        "description": "Active session authentication count over trailing 30 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "login_count_90d",
        "category": "Account Maturity",
        "unit": "count",
        "formula": "count(logins in [T-90d, T])",
        "description": "Active session authentication count over trailing 90 days.",
        "risk_direction": "Lower -> Greater Risk",
        "missing_handling": "Filled with 0"
    },
    {
        "name": "email_open_rate_30d",
        "category": "Account Maturity",
        "unit": "ratio",
        "formula": "count(opened emails) / count(delivered emails) in [T-30d, T]",
        "description": "Receptivity to outbound communications and marketing touches in past 30 days.",
        "risk_direction": "Lower -> Disengagement",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "campaign_response_rate_90d",
        "category": "Account Maturity",
        "unit": "ratio",
        "formula": "count(clicked campaigns) / count(delivered campaigns) in [T-90d, T]",
        "description": "High-intent response rate (clicks/registrations) to lifecycle campaigns in 90 days.",
        "risk_direction": "Lower -> Disengagement",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "payment_delay_count_90d",
        "category": "Account Maturity",
        "unit": "count",
        "formula": "count(failed or retried payments in [T-90d, T])",
        "description": "Number of billing collection delays or initial charge failures in 90 days.",
        "risk_direction": "Higher -> Greater Risk",
        "missing_handling": "Filled with 0"
    },

    # F. Additional behavioral variation (43-44)
    {
        "name": "transaction_value_coefficient_of_variation_90d",
        "category": "Behavioral Variation",
        "unit": "ratio",
        "formula": "std_transaction_value_90d / (avg_transaction_value_90d + 1e-5)",
        "description": "Relative dispersion of order basket sizes; indicates predictability of spend.",
        "risk_direction": "Higher -> Unpredictable Spend",
        "missing_handling": "Filled with 0.0"
    },
    {
        "name": "active_week_ratio_90d",
        "category": "Behavioral Variation",
        "unit": "ratio",
        "formula": "count(distinct calendar weeks active) / 13.0 in [T-90d, T]",
        "description": "Consistency of engagement across the trailing 13 calendar weeks.",
        "risk_direction": "Lower -> Sporadic / At-Risk",
        "missing_handling": "Filled with 0.0"
    }
]

FEATURE_NAMES: List[str] = [f["name"] for f in FEATURE_CATALOG]
assert len(FEATURE_NAMES) == 44, f"Expected exactly 44 features, found {len(FEATURE_NAMES)}"
