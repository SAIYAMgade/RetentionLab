"""Customer risk segmentation, action matrix, and scenario analysis."""
from typing import Dict, Any, List
import numpy as np
import pandas as pd

from retentionlab.config.settings import DEFAULT_CONFIG, PipelineConfig


def assign_risk_and_prioritization(
    features_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
    config: PipelineConfig = DEFAULT_CONFIG
) -> pd.DataFrame:
    """Combine model risk scores with customer value to create actionable prioritization tiers."""
    merged = pd.merge(features_df, predictions_df, on="customer_id", how="inner")

    # Quantiles for monetary tiers
    p_high = merged["total_spend"].quantile(config.high_monetary_percentile)
    p_med = merged["total_spend"].quantile(config.medium_monetary_percentile)

    def get_monetary_tier(spend: float) -> str:
        if spend >= p_high:
            return "High Value"
        elif spend >= p_med:
            return "Medium Value"
        else:
            return "Low Value"

    def get_risk_tier(score: float) -> str:
        if score >= config.high_risk_threshold:
            return "High Risk"
        elif score >= config.medium_risk_threshold:
            return "Medium Risk"
        else:
            return "Low Risk"

    merged["monetary_tier"] = merged["total_spend"].apply(get_monetary_tier)
    merged["risk_tier"] = merged["risk_score"].apply(get_risk_tier)

    # Segment and Recommended Actions
    priority_segments = []
    recommended_actions = []
    action_channels = []
    primary_risk_drivers = []

    for _, row in merged.iterrows():
        r_tier = row["risk_tier"]
        m_tier = row["monetary_tier"]
        rec = row["recency_days"]
        freq_ratio = row.get("frequency_ratio_30_to_90", 1.0)
        rec_ratio = row.get("recency_to_avg_interval_ratio", 1.0)
        ref_rate = row.get("refund_rate", 0.0)

        # Primary risk driver
        if rec > 90:
            driver = "Prolonged inactivity (>90 days dormancy)"
        elif rec_ratio > 2.0:
            driver = f"Purchase cycle overdue ({rec_ratio:.1f}x personal cadence)"
        elif freq_ratio < 0.35:
            driver = "Severe short-term order frequency drop (>65% decline)"
        elif ref_rate > 0.08:
            driver = f"Elevated refund rate ({ref_rate:.1%}) indicating friction"
        else:
            driver = "Gradual engagement contraction"
        primary_risk_drivers.append(driver)

        # Prioritization Segment and Strategy
        if r_tier == "High Risk" and m_tier == "High Value":
            priority_segments.append("Tier 1: High-Value At-Risk (Immediate Action)")
            recommended_actions.append("Direct outreach from dedicated account rep + personalized VIP win-back incentive")
            action_channels.append("Phone / Dedicated Rep")

        elif r_tier == "High Risk" and m_tier == "Medium Value":
            priority_segments.append("Tier 2: Medium-Value At-Risk (Targeted Campaign)")
            recommended_actions.append("Automated multi-step win-back email series with limited-time discount")
            action_channels.append("Email & SMS")

        elif r_tier == "High Risk" and m_tier == "Low Value":
            priority_segments.append("Tier 3: Low-Value At-Risk (Digital Nurture)")
            recommended_actions.append("Automated push notification / low-cost re-engagement email")
            action_channels.append("Mobile Push & Email")

        elif r_tier == "Medium Risk" and m_tier == "High Value":
            priority_segments.append("Tier 4: High-Value Warning (Preventative)")
            recommended_actions.append("Proactive satisfaction check-in and loyalty bonus points")
            action_channels.append("Concierge Email / Rep")

        elif r_tier == "Medium Risk":
            priority_segments.append("Tier 5: Moderate Watchlist")
            recommended_actions.append("Category cross-sell recommendation email")
            action_channels.append("Email")

        elif r_tier == "Low Risk" and m_tier == "High Value":
            priority_segments.append("Tier 6: Champions (Sustain & Reward)")
            recommended_actions.append("Exclusive early access to new releases and brand ambassador perk")
            action_channels.append("Email & Portal")

        else:
            priority_segments.append("Tier 7: Steady / Standard Retained")
            recommended_actions.append("Standard newsletter and promotional calendar")
            action_channels.append("Standard Email")

    merged["priority_segment"] = priority_segments
    merged["recommended_action"] = recommended_actions
    merged["action_channel"] = action_channels
    merged["primary_risk_driver"] = primary_risk_drivers
    merged["transaction_frequency"] = merged["total_transactions"]

    output_cols = [
        "customer_id",
        "prediction_date",
        "risk_score",
        "risk_tier",
        "monetary_tier",
        "priority_segment",
        "recency_days",
        "transaction_frequency",
        "total_spend",
        "primary_risk_driver",
        "recommended_action",
        "action_channel",
        "model_version"
    ]
    return merged[output_cols].sort_values(["risk_score", "total_spend"], ascending=[False, False]).reset_index(drop=True)


def calculate_retention_scenarios(
    prioritization_df: pd.DataFrame,
    cost_per_contact: float = 15.0,
    assumed_retention_rate: float = 0.15,
    budget_levels: List[float] = None
) -> pd.DataFrame:
    """Run hypothetical scenario analysis for retention interventions per Section 14 specification.

    Labels output as purely illustrative scenario projections, not guaranteed outcomes.
    """
    if budget_levels is None:
        budget_levels = [5000.0, 10000.0, 25000.0, 50000.0]

    # Filter to high and medium risk customers eligible for outreach
    outreach_candidates = prioritization_df[
        prioritization_df["risk_tier"].isin(["High Risk", "Medium Risk"])
    ].sort_values("total_spend", ascending=False).reset_index(drop=True)

    scenarios = []

    for budget in budget_levels:
        max_contacts = int(budget // cost_per_contact)
        contacted_df = outreach_candidates.head(max_contacts)
        actual_contacted = len(contacted_df)

        if actual_contacted == 0:
            continue

        total_spend_contacted = float(contacted_df["total_spend"].sum())
        expected_retained_customers = int(round(actual_contacted * assumed_retention_rate))
        # Expected retained value (assuming retained customers generate spend proportional to their historical AOV)
        expected_value_protected = float(round(total_spend_contacted * assumed_retention_rate, 2))
        roi_ratio = float(round((expected_value_protected - budget) / budget, 2)) if budget > 0 else 0.0

        scenarios.append({
            "hypothetical_budget": budget,
            "cost_per_contact": cost_per_contact,
            "max_customers_contacted": actual_contacted,
            "high_value_customers_targeted": int((contacted_df["monetary_tier"] == "High Value").sum()),
            "assumed_retention_success_rate": f"{assumed_retention_rate:.0%}",
            "projected_retained_customers": expected_retained_customers,
            "portfolio_spend_exposed": round(total_spend_contacted, 2),
            "projected_spend_protected": expected_value_protected,
            "projected_net_value": round(expected_value_protected - budget, 2),
            "projected_roi_ratio": roi_ratio,
            "scenario_assumption_notice": "Illustrative scenario projection only; requires experimental uplift testing."
        })

    return pd.DataFrame(scenarios)
