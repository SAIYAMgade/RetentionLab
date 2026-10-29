"""
RetentionLab Explainable Risk Signals Engine.
Generates customer-level supporting behavioral risk signals based on individual feature values.
Strictly non-causal: describes factors 'associated with higher estimated risk'.
"""

from typing import Dict, List
import pandas as pd


class RiskSignalExplainer:
    """
    Extracts top supporting behavioral risk signals for individual customers.
    """

    @staticmethod
    def extract_customer_signals(row: pd.Series) -> List[str]:
        """
        Evaluate individual feature thresholds and return top supporting risk signals.
        """
        signals = []

        # 1. Recency Decay
        recency = row.get("days_since_last_transaction", 0)
        if recency >= 45:
            signals.append(f"Acute Inactivity ({int(recency)}d since last transaction)")
        elif recency >= 30:
            signals.append(f"Extended Inactivity ({int(recency)}d since last transaction)")

        # 2. Transaction Velocity Decay
        trend_30 = row.get("transaction_count_trend_30d", 1.0)
        if trend_30 <= 0.35:
            signals.append(f"Severe Velocity Drop ({trend_30:.2f}x transaction volume vs prior month)")
        elif trend_30 <= 0.60:
            signals.append(f"Declining Transaction Pace ({trend_30:.2f}x volume vs prior month)")

        # 3. Spend Contraction
        spend_trend_30 = row.get("spend_trend_30d", 1.0)
        if spend_trend_30 <= 0.35:
            signals.append(f"Sharp Spend Contraction ({spend_trend_30:.2f}x spend vs prior month)")
        elif spend_trend_30 <= 0.60:
            signals.append(f"Softening Spend ({spend_trend_30:.2f}x spend vs prior month)")

        # 4. Payment Friction
        failed_pay_rate = row.get("failed_payment_rate_90d", 0.0)
        if failed_pay_rate >= 0.05:
            signals.append(f"Elevated Billing Declines ({failed_pay_rate:.1%} failed payment rate)")

        # 5. Customer Complaints / Support Friction
        complaints = row.get("complaints_180d", 0)
        if complaints >= 1:
            signals.append(f"Dissatisfaction Case ({int(complaints)} formal complaints logged)")

        # 6. Platform Engagement Decay
        days_login = row.get("days_since_last_login", 0)
        if days_login >= 30:
            signals.append(f"Dormant User Authentication ({int(days_login)}d since platform login)")

        # 7. Sporadic Weekly Consistency
        active_weeks = row.get("active_week_ratio_90d", 1.0)
        if active_weeks <= 0.35:
            signals.append(f"Low Engagement Consistency ({active_weeks:.0%} active weeks in quarter)")

        # 8. High Refund Rates
        ref_rate = row.get("refund_rate_90d", 0.0)
        if ref_rate >= 0.15:
            signals.append(f"Unusual Refund Volume ({ref_rate:.1%} of gross spend refunded)")

        if not signals:
            signals.append("Stable behavioral pattern across core engagement metrics")

        return signals[:3]  # Return top 3 most prominent signals
