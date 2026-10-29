"""
Unit tests for 44-Feature Behavioral Engineering.
"""

import pytest
import pandas as pd
import numpy as np
from retentionlab.features.builder import FeatureBuilder
from retentionlab.features.catalog import FEATURE_NAMES, FEATURE_CATALOG


def test_feature_catalog_completeness():
    """Verify exact 44 documented features in catalog."""
    assert len(FEATURE_NAMES) == 44
    assert len(FEATURE_CATALOG) == 44
    assert len(set(FEATURE_NAMES)) == 44


def test_feature_builder_output():
    """Verify feature builder computes exactly 44 columns without NaNs."""
    # Synthetic mini fixture
    custs = pd.DataFrame(
        {
            "customer_id": ["CUST-001", "CUST-002"],
            "signup_date": ["2025-01-15", "2025-02-01"],
            "tenure_days": [440, 424],
        }
    )
    txns = pd.DataFrame(
        {
            "transaction_id": ["TXN-01", "TXN-02"],
            "customer_id": ["CUST-001", "CUST-002"],
            "product_id": ["PROD-01", "PROD-02"],
            "transaction_date": ["2026-03-10", "2026-03-15"],
            "transaction_amount": [100.0, 250.0],
            "transaction_type": ["Purchase", "Purchase"],
            "payment_status": ["Completed", "Completed"],
            "discount_amount": [0.0, 10.0],
            "refund_amount": [0.0, 0.0],
            "transaction_channel": ["Web", "API"],
            "transaction_status": ["Success", "Success"],
        }
    )
    acts = pd.DataFrame(
        {
            "activity_id": ["ACT-01"],
            "customer_id": ["CUST-001"],
            "activity_date": ["2026-03-20"],
            "activity_type": ["login"],
        }
    )
    tcks = pd.DataFrame(columns=["ticket_id", "customer_id", "ticket_date", "ticket_type", "status", "satisfaction_score"])
    camps = pd.DataFrame(columns=["interaction_id", "customer_id", "campaign_date", "channel", "action"])
    prods = pd.DataFrame(
        {
            "product_id": ["PROD-01", "PROD-02"],
            "product_category": ["Analytics", "Security"],
        }
    )

    builder = FeatureBuilder(snapshot_date="2026-04-01")
    features = builder.build_features(custs, txns, acts, tcks, camps, prods)

    assert len(features) == 2
    feature_cols = [c for c in features.columns if c not in ["customer_id", "snapshot_date"]]
    assert len(feature_cols) == 44
    assert not features[feature_cols].isnull().any().any()
    assert (features["transaction_count_30d"] >= 0).all()
