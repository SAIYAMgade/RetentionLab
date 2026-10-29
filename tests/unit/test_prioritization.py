"""
Unit tests for Customer Prioritization Engine and Risk Bands.
"""

import pytest
import pandas as pd
from retentionlab.prioritization.engine import RetentionPrioritizationEngine


def test_risk_band_boundaries():
    """Verify standard risk band cutoff boundaries."""
    engine = RetentionPrioritizationEngine()

    assert engine.assign_risk_band(0.85) == "Critical Risk"
    assert engine.assign_risk_band(0.75) == "Critical Risk"
    assert engine.assign_risk_band(0.60) == "High Risk"
    assert engine.assign_risk_band(0.50) == "High Risk"
    assert engine.assign_risk_band(0.35) == "Moderate Risk"
    assert engine.assign_risk_band(0.25) == "Moderate Risk"
    assert engine.assign_risk_band(0.10) == "Low Risk"


def test_top_cohort_selection():
    """Verify that top 15% cohort selection marks the correct count."""
    engine = RetentionPrioritizationEngine(top_cohort_percentage=0.20)
    df = pd.DataFrame(
        {
            "customer_id": [f"CUST-{i}" for i in range(10)],
            "churn_probability": [0.1 * i for i in range(10)],
            "total_spend_180d": [100.0 * i for i in range(10)],
            "failed_payment_rate_90d": [0.0] * 10,
            "complaints_180d": [0] * 10,
        }
    )

    prioritized = engine.prioritize_customers(df)

    assert prioritized["is_top_15_percent"].sum() == 2  # 20% of 10
    # Rank 1 must have highest priority score
    assert prioritized.iloc[0]["retention_rank"] == 1
    assert prioritized.iloc[0]["prioritization_score"] >= prioritized.iloc[1]["prioritization_score"]
