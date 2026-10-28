"""Feature engineering pipeline for RetentionLab.

Computes 44 customer behavioral features strictly using historical transactions
observed on or before the cutoff date, preventing any data leakage.
"""

from datetime import datetime
from typing import List
import numpy as np
import pandas as pd

from retentionlab.config.settings import DEFAULT_CONFIG, PipelineConfig


FEATURE_NAMES: List[str] = [
    # Recency (4)
    "recency_days",
    "first_purchase_days",
    "days_between_last_two",
    "recency_to_avg_interval_ratio",
    # Frequency (10)
    "total_transactions",
    "transactions_30d",
    "transactions_60d",
    "transactions_90d",
    "transactions_180d",
    "transactions_365d",
    "active_months",
    "active_month_ratio",
    "avg_monthly_transactions",
    "distinct_purchase_dates",
    # Monetary (12)
    "total_spend",
    "avg_transaction_amount",
    "median_transaction_amount",
    "max_transaction_amount",
    "min_transaction_amount",
    "std_transaction_amount",
    "spend_30d",
    "spend_60d",
    "spend_90d",
    "spend_180d",
    "spend_365d",
    "avg_spend_per_active_month",
    # Behavioral trends & intervals (9)
    "frequency_ratio_30_to_90",
    "frequency_ratio_90_to_180",
    "spend_ratio_30_to_90",
    "spend_ratio_90_to_180",
    "avg_interpurchase_days",
    "std_interpurchase_days",
    "max_interpurchase_days",
    "interval_expansion_ratio",
    "is_single_purchase_customer",
    # Diversity, channels & refunds (9)
    "distinct_categories",
    "distinct_channels",
    "top_category_spend_share",
    "top_channel_tx_share",
    "mobile_app_tx_share",
    "web_tx_share",
    "in_store_tx_share",
    "refund_count",
    "refund_rate",
]


def build_customer_features(
    df: pd.DataFrame,
    eligible_customers: pd.DataFrame = None,
    config: PipelineConfig = DEFAULT_CONFIG
) -> pd.DataFrame:
    """Extract 44 behavioral features strictly as of cutoff_date.

    Args:
        df: Raw or cleaned transaction dataframe.
        eligible_customers: Optional dataframe with eligible customer_id.
        config: Pipeline configuration.

    Returns:
        DataFrame with customer_id and 44 behavioral features.
    """
    df_tx = df.copy()
    df_tx["tx_dt"] = pd.to_datetime(df_tx["transaction_date"])
    cutoff_dt = pd.to_datetime(config.cutoff_date) + pd.Timedelta(days=1, microseconds=-1)

    # STRICT TEMPORAL FILTER: Only transactions up to cutoff date
    hist_tx = df_tx[df_tx["tx_dt"] <= cutoff_dt].copy()

    # Completed purchases
    purchases = hist_tx[
        (hist_tx["transaction_status"] == "completed") &
        (hist_tx["transaction_type"] == "purchase") &
        (hist_tx["transaction_amount"] > 0)
    ].copy()

    # All refunds
    refunds = hist_tx[
        (hist_tx["transaction_type"] == "refund") &
        (hist_tx["transaction_status"] == "completed")
    ].copy()

    # Time boundaries (using full cutoff day)
    cutoff_point = cutoff_dt
    d30 = cutoff_point - pd.Timedelta(days=30)
    if eligible_customers is not None and "customer_id" in eligible_customers.columns:
        cust_list = eligible_customers["customer_id"].unique()
        purchases = purchases[purchases["customer_id"].isin(cust_list)].copy()
        refunds = refunds[refunds["customer_id"].isin(cust_list)].copy()
    else:
        cust_list = purchases["customer_id"].unique()

    # Sort purchases chronologically per customer
    purchases = purchases.sort_values(["customer_id", "tx_dt"]).reset_index(drop=True)
    purchases["date_only"] = purchases["tx_dt"].dt.date
    purchases["year_month"] = purchases["tx_dt"].dt.to_period("M")

    # Time boundaries
    d30 = cutoff_point - pd.Timedelta(days=30)
    d60 = cutoff_point - pd.Timedelta(days=60)
    d90 = cutoff_point - pd.Timedelta(days=90)
    d180 = cutoff_point - pd.Timedelta(days=180)
    d365 = cutoff_point - pd.Timedelta(days=365)

    # 1. Base aggregations per customer
    base_grp = purchases.groupby("customer_id")
    cust_min_dt = base_grp["tx_dt"].min()
    cust_max_dt = base_grp["tx_dt"].max()
    cust_cnt = base_grp["transaction_id"].count()
    cust_spend = base_grp["transaction_amount"].sum()
    cust_mean_spend = base_grp["transaction_amount"].mean()
    cust_median_spend = base_grp["transaction_amount"].median()
    cust_max_spend = base_grp["transaction_amount"].max()
    cust_min_spend = base_grp["transaction_amount"].min()
    cust_std_spend = base_grp["transaction_amount"].std().fillna(0.0)
    cust_distinct_dates = base_grp["date_only"].nunique()
    cust_active_months = base_grp["year_month"].nunique()

    # Window aggregations
    tx_30d = purchases[purchases["tx_dt"] >= d30].groupby("customer_id")["transaction_id"].count()
    tx_60d = purchases[purchases["tx_dt"] >= d60].groupby("customer_id")["transaction_id"].count()
    tx_90d = purchases[purchases["tx_dt"] >= d90].groupby("customer_id")["transaction_id"].count()
    tx_180d = purchases[purchases["tx_dt"] >= d180].groupby("customer_id")["transaction_id"].count()
    tx_365d = purchases[purchases["tx_dt"] >= d365].groupby("customer_id")["transaction_id"].count()

    spend_30d = purchases[purchases["tx_dt"] >= d30].groupby("customer_id")["transaction_amount"].sum()
    spend_60d = purchases[purchases["tx_dt"] >= d60].groupby("customer_id")["transaction_amount"].sum()
    spend_90d = purchases[purchases["tx_dt"] >= d90].groupby("customer_id")["transaction_amount"].sum()
    spend_180d = purchases[purchases["tx_dt"] >= d180].groupby("customer_id")["transaction_amount"].sum()
    spend_365d = purchases[purchases["tx_dt"] >= d365].groupby("customer_id")["transaction_amount"].sum()

    # Interpurchase intervals and last two transactions
    # Shift within customer to compute consecutive intervals
    purchases["prev_tx_dt"] = purchases.groupby("customer_id")["tx_dt"].shift(1)
    purchases["interval_days"] = (purchases["tx_dt"] - purchases["prev_tx_dt"]).dt.total_seconds() / 86400.0

    interval_stats = purchases.dropna(subset=["interval_days"]).groupby("customer_id")["interval_days"].agg(
        avg_interpurchase_days="mean",
        std_interpurchase_days="std",
        max_interpurchase_days="max"
    )

    # Last two purchase gap
    # For customers with >= 2 purchases, get interval between 2nd-to-last and last
    last_two = purchases.groupby("customer_id").tail(2)
    last_two_interval = last_two.groupby("customer_id")["interval_days"].last()

    # Category and Channel diversity
    distinct_cats = purchases.groupby("customer_id")["product_category"].nunique()
    distinct_chans = purchases.groupby("customer_id")["channel"].nunique()

    # Top category spend share
    cat_spend = purchases.groupby(["customer_id", "product_category"])["transaction_amount"].sum().reset_index()
    top_cat_spend = cat_spend.groupby("customer_id")["transaction_amount"].max()

    # Channel shares
    chan_counts = purchases.groupby(["customer_id", "channel"])["transaction_id"].count().unstack(fill_value=0)
    top_chan_count = chan_counts.max(axis=1)
    mobile_share = chan_counts.get("Mobile App", pd.Series(0, index=chan_counts.index)) / cust_cnt
    web_share = chan_counts.get("Web", pd.Series(0, index=chan_counts.index)) / cust_cnt
    store_share = chan_counts.get("In-Store", pd.Series(0, index=chan_counts.index)) / cust_cnt

    # Refunds
    cust_refunds = refunds.groupby("customer_id")["transaction_id"].count()

    # Assemble feature dataframe
    feat = pd.DataFrame(index=cust_list)
    feat.index.name = "customer_id"

    # Recency features
    feat["recency_days"] = (cutoff_point - cust_max_dt).dt.days.clip(lower=0)
    feat["first_purchase_days"] = (cutoff_point - cust_min_dt).dt.days.clip(lower=0)

    # Frequency features
    feat["total_transactions"] = cust_cnt
    feat["transactions_30d"] = tx_30d.reindex(feat.index).fillna(0).astype(int)
    feat["transactions_60d"] = tx_60d.reindex(feat.index).fillna(0).astype(int)
    feat["transactions_90d"] = tx_90d.reindex(feat.index).fillna(0).astype(int)
    feat["transactions_180d"] = tx_180d.reindex(feat.index).fillna(0).astype(int)
    feat["transactions_365d"] = tx_365d.reindex(feat.index).fillna(0).astype(int)
    feat["active_months"] = cust_active_months
    feat["distinct_purchase_dates"] = cust_distinct_dates

    # Monetary features
    feat["total_spend"] = cust_spend
    feat["avg_transaction_amount"] = cust_mean_spend
    feat["median_transaction_amount"] = cust_median_spend
    feat["max_transaction_amount"] = cust_max_spend
    feat["min_transaction_amount"] = cust_min_spend
    feat["std_transaction_amount"] = cust_std_spend.fillna(0.0)
    feat["spend_30d"] = spend_30d.reindex(feat.index).fillna(0.0)
    feat["spend_60d"] = spend_60d.reindex(feat.index).fillna(0.0)
    feat["spend_90d"] = spend_90d.reindex(feat.index).fillna(0.0)
    feat["spend_180d"] = spend_180d.reindex(feat.index).fillna(0.0)
    feat["spend_365d"] = spend_365d.reindex(feat.index).fillna(0.0)
    feat["avg_spend_per_active_month"] = (feat["total_spend"] / feat["active_months"].clip(lower=1)).round(2)

    # Derived tenure and active ratios
    tenure_months = np.maximum(1.0, feat["first_purchase_days"] / 30.4375)
    feat["active_month_ratio"] = (feat["active_months"] / tenure_months).clip(upper=1.0).round(4)
    feat["avg_monthly_transactions"] = (feat["total_transactions"] / tenure_months).round(4)

    # Intervals
    feat["avg_interpurchase_days"] = interval_stats["avg_interpurchase_days"].reindex(feat.index).fillna(feat["first_purchase_days"])
    feat["std_interpurchase_days"] = interval_stats["std_interpurchase_days"].reindex(feat.index).fillna(0.0)
    feat["max_interpurchase_days"] = interval_stats["max_interpurchase_days"].reindex(feat.index).fillna(feat["first_purchase_days"])
    feat["days_between_last_two"] = last_two_interval.reindex(feat.index).fillna(feat["first_purchase_days"])

    feat["recency_to_avg_interval_ratio"] = (feat["recency_days"] / (feat["avg_interpurchase_days"] + 1.0)).round(4)
    feat["interval_expansion_ratio"] = (feat["days_between_last_two"] / (feat["avg_interpurchase_days"] + 1.0)).round(4)
    feat["is_single_purchase_customer"] = (feat["total_transactions"] == 1).astype(int)

    # Behavioral trend ratios
    feat["frequency_ratio_30_to_90"] = (feat["transactions_30d"] / (feat["transactions_90d"] / 3.0 + 0.01)).round(4)
    feat["frequency_ratio_90_to_180"] = (feat["transactions_90d"] / (feat["transactions_180d"] / 2.0 + 0.01)).round(4)
    feat["spend_ratio_30_to_90"] = (feat["spend_30d"] / (feat["spend_90d"] / 3.0 + 0.05)).round(4)
    feat["spend_ratio_90_to_180"] = (feat["spend_90d"] / (feat["spend_180d"] / 2.0 + 0.05)).round(4)

    # Diversity & Channels
    feat["distinct_categories"] = distinct_cats.reindex(feat.index).fillna(1).astype(int)
    feat["distinct_channels"] = distinct_chans.reindex(feat.index).fillna(1).astype(int)
    feat["top_category_spend_share"] = (top_cat_spend.reindex(feat.index) / feat["total_spend"].clip(lower=0.01)).clip(upper=1.0).round(4)
    feat["top_channel_tx_share"] = (top_chan_count.reindex(feat.index) / feat["total_transactions"]).clip(upper=1.0).round(4)
    feat["mobile_app_tx_share"] = mobile_share.reindex(feat.index).fillna(0.0).round(4)
    feat["web_tx_share"] = web_share.reindex(feat.index).fillna(0.0).round(4)
    feat["in_store_tx_share"] = store_share.reindex(feat.index).fillna(0.0).round(4)

    # Refunds
    feat["refund_count"] = cust_refunds.reindex(feat.index).fillna(0).astype(int)
    feat["refund_rate"] = (feat["refund_count"] / (feat["total_transactions"] + feat["refund_count"])).round(4)

    # Fill any remaining NaNs safely
    feat = feat.fillna(0.0).reset_index()

    # Reorder exactly matching FEATURE_NAMES
    ordered_cols = ["customer_id"] + [col for col in FEATURE_NAMES if col in feat.columns]
    return feat[ordered_cols]
