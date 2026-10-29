"""
RetentionLab Customer Prioritization Engine.
Combines predicted churn risk with historical business value and friction signals
to prioritize actionable customer retention cohorts.
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd
from retentionlab.config.settings import settings


class RetentionPrioritizationEngine:
    """
    Ranks customers using revenue-aware exposure scores and determines
    operational action recommendations.
    """

    def __init__(
        self,
        risk_weight: float = 0.55,
        value_weight: float = 0.45,
        top_cohort_percentage: float = 0.15,
    ):
        self.risk_weight = risk_weight
        self.value_weight = value_weight
        self.top_cohort_percentage = top_cohort_percentage

    @staticmethod
    def assign_risk_band(prob: float) -> str:
        """Categorize continuous churn probability into business risk tiers."""
        if prob >= 0.75:
            return "Critical Risk"
        elif prob >= 0.50:
            return "High Risk"
        elif prob >= 0.25:
            return "Moderate Risk"
        else:
            return "Low Risk"

    @staticmethod
    def assign_action_recommendation(row: pd.Series) -> Tuple[str, str]:
        """
        Determine tailored operational action category and specific next step.
        """
        prob = row["churn_probability"]
        val = row["historical_value_proxy"]
        signals_text = str(row.get("top_risk_signals", ""))

        if prob >= 0.50 and val >= 5000:
            return (
                "VIP Human Touchpoint",
                "Schedule high-touch Account Executive review and offer customized retention contract.",
            )
        elif "Billing Declines" in signals_text or row.get("failed_payment_rate_90d", 0) >= 0.05:
            return (
                "Payment Experience Review",
                "Audit merchant gateway billing logs and proactively contact finance team for updated card.",
            )
        elif "Dissatisfaction Case" in signals_text or row.get("complaints_180d", 0) >= 1:
            return (
                "Service Escalation",
                "Escalate to Customer Support Lead for priority resolution and service credit evaluation.",
            )
        elif prob >= 0.50:
            return (
                "Targeted Re-Engagement",
                "Deploy personalized product adoption guide and high-value workflow activation incentives.",
            )
        elif prob >= 0.25:
            return (
                "Automated Lifecycle Nudge",
                "Trigger automated onboarding check-in and educational webinar invitations.",
            )
        else:
            return (
                "Standard Health Cadence",
                "Maintain baseline relationship management without incurring specialized retention cost.",
            )

    def prioritize_customers(
        self, scored_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute risk-weighted exposure, composite prioritization score,
        and flag the top operational cohort.
        """
        df = scored_df.copy()

        # 1. Historical value proxy (Annualized spend: 180d * 2.0)
        df["historical_value_proxy"] = (df["total_spend_180d"] * 2.0).round(2)

        # 2. Risk Exposure Proxy (Estimated Risk-Weighted Value)
        # Clearly documented: NOT guaranteed future loss; it is an analytical exposure metric
        df["risk_weighted_exposure"] = (df["churn_probability"] * df["historical_value_proxy"]).round(2)

        # 3. Composite Prioritization Score (0.0 to 1.0)
        # Normalize value proxy against 95th percentile to prevent extreme outlier distortion
        val_norm_cap = np.percentile(df["historical_value_proxy"], 95)
        val_norm = np.clip(df["historical_value_proxy"] / (val_norm_cap + 1e-5), 0.0, 1.0)

        df["prioritization_score"] = (
            self.risk_weight * df["churn_probability"] + self.value_weight * val_norm
        ).round(4)

        # 4. Action recommendations
        actions = []
        next_steps = []
        for _, row in df.iterrows():
            act, step = self.assign_action_recommendation(row)
            actions.append(act)
            next_steps.append(step)
        df["suggested_action"] = actions
        df["recommended_next_step"] = next_steps

        # 5. Top Operational Cohort (default top 15% ranked by prioritization_score)
        df = df.sort_values(
            by=["prioritization_score", "risk_weighted_exposure", "churn_probability"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

        n_top = int(np.ceil(len(df) * self.top_cohort_percentage))
        df["is_top_15_percent"] = 0
        df.loc[: n_top - 1, "is_top_15_percent"] = 1
        df["retention_rank"] = np.arange(1, len(df) + 1)

        return df
