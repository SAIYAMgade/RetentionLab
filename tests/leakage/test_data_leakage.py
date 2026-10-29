"""
Automated Data Leakage & Temporal Boundary Tests.
"""

import pytest
import pandas as pd
from retentionlab.features.builder import FeatureBuilder
from retentionlab.features.catalog import FEATURE_NAMES
from retentionlab.labels.target import TargetLabeler


def test_no_future_transactions_leak_into_features():
    """
    Assert that adding a massive future transaction (> snapshot_date)
    does NOT alter the historical feature values at snapshot date.
    """
    snapshot_date = "2026-04-01"

    custs = pd.DataFrame(
        {
            "customer_id": ["CUST-001"],
            "signup_date": ["2025-01-01"],
            "tenure_days": [455],
        }
    )
    # Baseline historical transaction
    hist_txns = pd.DataFrame(
        {
            "transaction_id": ["TXN-01"],
            "customer_id": ["CUST-001"],
            "product_id": ["PROD-01"],
            "transaction_date": ["2026-03-15"],
            "transaction_amount": [500.0],
            "transaction_type": ["Purchase"],
            "payment_status": ["Completed"],
            "discount_amount": [0.0],
            "refund_amount": [0.0],
            "transaction_channel": ["Web"],
            "transaction_status": ["Success"],
        }
    )
    empty_acts = pd.DataFrame(columns=["activity_id", "customer_id", "activity_date", "activity_type"])
    empty_tcks = pd.DataFrame(columns=["ticket_id", "customer_id", "ticket_date", "ticket_type", "status", "satisfaction_score"])
    empty_camps = pd.DataFrame(columns=["interaction_id", "customer_id", "campaign_date", "channel", "action"])
    prods = pd.DataFrame({"product_id": ["PROD-01"], "product_category": ["Analytics"]})

    builder = FeatureBuilder(snapshot_date=snapshot_date)
    features_base = builder.build_features(custs, hist_txns, empty_acts, empty_tcks, empty_camps, prods)

    # Now add a future transaction on 2026-04-15 with $1,000,000 spend
    future_txns = hist_txns.copy()
    future_row = pd.DataFrame(
        [
            {
                "transaction_id": "TXN-FUTURE",
                "customer_id": "CUST-001",
                "product_id": "PROD-01",
                "transaction_date": "2026-04-15",
                "transaction_amount": 1000000.0,
                "transaction_type": "Purchase",
                "payment_status": "Completed",
                "discount_amount": 0.0,
                "refund_amount": 0.0,
                "transaction_channel": "Web",
                "transaction_status": "Success",
            }
        ]
    )
    txns_with_future = pd.concat([future_txns, future_row], ignore_index=True)

    features_leaked_test = builder.build_features(custs, txns_with_future, empty_acts, empty_tcks, empty_camps, prods)

    # Values must be 100% identical: future transaction must NOT enter features
    pd.testing.assert_frame_equal(features_base, features_leaked_test)
    assert features_leaked_test["total_spend_30d"].iloc[0] == 500.0


def test_target_label_not_in_features():
    """Assert that target label 'is_churn' is strictly absent from feature matrix."""
    assert "is_churn" not in FEATURE_NAMES
    assert "churn" not in [f.lower() for f in FEATURE_NAMES]
