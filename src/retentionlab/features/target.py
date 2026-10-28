"""Operational churn / inactivity target definition for RetentionLab."""
from datetime import datetime
from typing import Tuple
import pandas as pd
from retentionlab.config.settings import DEFAULT_CONFIG, PipelineConfig


def create_target_labels(df: pd.DataFrame, config: PipelineConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """Assign operational inactivity labels per Section 5 specification.

    Eligibility:
    1. Customer must have >= 1 completed purchase on or before cutoff_date.
    2. Customer tenure at cutoff_date must be >= min_tenure_days (first purchase <= cutoff - min_tenure_days).

    Target definition (is_inactive):
    1 if customer has 0 qualifying transactions in future observation window (future_start_date to future_end_date).
    0 if customer has >= 1 qualifying transactions in future window.
    """
    df_tx = df.copy()
    df_tx["tx_dt"] = pd.to_datetime(df_tx["transaction_date"])

    cutoff_dt = pd.to_datetime(config.cutoff_date) + pd.Timedelta(days=1, microseconds=-1)
    future_start_dt = pd.to_datetime(config.future_start_date)
    future_end_dt = pd.to_datetime(config.future_end_date) + pd.Timedelta(days=1, microseconds=-1)

    # Historical completed purchases
    hist_qualifying = df_tx[
        (df_tx["tx_dt"] <= cutoff_dt) &
        (df_tx["transaction_status"] == "completed") &
        (df_tx["transaction_type"] == "purchase") &
        (df_tx["transaction_amount"] > 0)
    ]

    # Evaluate eligibility: tenure and >= 1 purchase
    cust_hist = hist_qualifying.groupby("customer_id").agg(
        first_purchase_dt=("tx_dt", "min"),
        last_purchase_dt=("tx_dt", "max"),
        hist_purchases=("transaction_id", "count")
    ).reset_index()

    cutoff_point = pd.to_datetime(config.cutoff_date)
    cust_hist["tenure_days"] = (cutoff_point - cust_hist["first_purchase_dt"]).dt.days

    # Filter eligible customers
    eligible = cust_hist[
        (cust_hist["hist_purchases"] >= 1) &
        (cust_hist["tenure_days"] >= config.min_tenure_days)
    ].copy()

    # Future qualifying purchases
    future_qualifying = df_tx[
        (df_tx["tx_dt"] >= future_start_dt) &
        (df_tx["tx_dt"] <= future_end_dt) &
        (df_tx["transaction_status"] == "completed") &
        (df_tx["transaction_type"] == "purchase") &
        (df_tx["transaction_amount"] > 0)
    ]

    future_counts = future_qualifying.groupby("customer_id")["transaction_id"].count().rename("future_purchases").reset_index()

    # Merge with eligible customers
    target_df = pd.merge(eligible[["customer_id", "tenure_days"]], future_counts, on="customer_id", how="left")
    target_df["future_purchases"] = target_df["future_purchases"].fillna(0).astype(int)

    # Inactivity definition: 1 if 0 future purchases, 0 if >= 1
    target_df[config.target_col] = (target_df["future_purchases"] == 0).astype(int)
    target_df["prediction_date"] = config.cutoff_date
    target_df["future_window_days"] = config.outcome_window_days

    return target_df[["customer_id", "prediction_date", "tenure_days", "future_purchases", config.target_col]]
