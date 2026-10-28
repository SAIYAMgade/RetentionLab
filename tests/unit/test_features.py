"""Unit tests for feature engineering, zero-leakage, and target definition."""
import pandas as pd
import pytest
from retentionlab.config.settings import PipelineConfig
from retentionlab.features.target import create_target_labels
from retentionlab.features.builder import build_customer_features, FEATURE_NAMES


@pytest.fixture
def custom_config():
    return PipelineConfig(
        cutoff_date="2023-12-31",
        future_start_date="2024-01-01",
        future_end_date="2024-03-31",
        min_tenure_days=30
    )


def test_target_label_correctness(sample_transactions_raw, custom_config):
    """Test 9: Verify target-label correctness for active vs inactive customers."""
    target_df = create_target_labels(sample_transactions_raw, custom_config)

    # C1 made a purchase on 2024-01-15 -> Active (is_inactive = 0)
    c1_row = target_df[target_df["customer_id"] == "C1"].iloc[0]
    assert c1_row["is_inactive"] == 0
    assert c1_row["future_purchases"] == 1

    # C2 made no purchases in 2024 -> Inactive (is_inactive = 1)
    c2_row = target_df[target_df["customer_id"] == "C2"].iloc[0]
    assert c2_row["is_inactive"] == 1
    assert c2_row["future_purchases"] == 0

    # C3 joined on 2023-12-15 (tenure = 16 days < 30 days) -> Excluded from eligible universe
    assert "C3" not in target_df["customer_id"].values


def test_zero_leakage_guarantee(sample_transactions_raw, custom_config):
    """Test 10: Features must be computed ONLY using data up to cutoff_date (2023-12-31)."""
    target_df = create_target_labels(sample_transactions_raw, custom_config)
    feat_df = build_customer_features(sample_transactions_raw, eligible_customers=target_df, config=custom_config)

    # C1 had 3 purchases on or before 2023-12-31 ($100, $150, $200 = $450)
    # The 2024 purchase of $120 must NOT be included in total_spend or total_transactions
    c1_feat = feat_df[feat_df["customer_id"] == "C1"].iloc[0]
    assert c1_feat["total_transactions"] == 3
    assert c1_feat["total_spend"] == 450.0


def test_recency_at_boundary(sample_transactions_raw, custom_config):
    """Test 5: Recency calculations at cutoff date boundary."""
    target_df = create_target_labels(sample_transactions_raw, custom_config)
    feat_df = build_customer_features(sample_transactions_raw, eligible_customers=target_df, config=custom_config)

    # C1 last purchase was 2023-12-20. Cutoff is 2023-12-31.
    # 2023-12-31 - 2023-12-20 = 11 days
    c1_feat = feat_df[feat_df["customer_id"] == "C1"].iloc[0]
    assert c1_feat["recency_days"] == 11


def test_monetary_and_frequency_aggregation(sample_transactions_raw, custom_config):
    """Test 6 & 7: Transaction frequency and monetary aggregations."""
    target_df = create_target_labels(sample_transactions_raw, custom_config)
    feat_df = build_customer_features(sample_transactions_raw, eligible_customers=target_df, config=custom_config)

    # C4: 1 purchase ($200), 1 refund (-$50), 1 failed (ignored)
    c4_feat = feat_df[feat_df["customer_id"] == "C4"].iloc[0]
    assert c4_feat["total_transactions"] == 1
    assert c4_feat["total_spend"] == 200.0
    assert c4_feat["refund_count"] == 1
    assert c4_feat["refund_rate"] == 0.5  # 1 refund / (1 purchase + 1 refund)


def test_all_44_features_present(sample_transactions_raw, custom_config):
    """Test 4: Verify exactly 44 features are computed."""
    target_df = create_target_labels(sample_transactions_raw, custom_config)
    feat_df = build_customer_features(sample_transactions_raw, eligible_customers=target_df, config=custom_config)

    computed_features = [c for c in feat_df.columns if c != "customer_id"]
    assert len(computed_features) == 44
    for fname in FEATURE_NAMES:
        assert fname in computed_features
