"""
RetentionLab Churn Target Label Construction.
Defines churn based strictly on future behavior in the prediction window following the snapshot date.
"""

from datetime import datetime, timedelta
from typing import Optional
import pandas as pd


class TargetLabeler:
    """
    Constructs future-window churn labels with explicit temporal boundaries.
    Guarantees no future label information enters feature engineering.
    """

    def __init__(
        self,
        snapshot_date: str = "2026-04-01",
        prediction_horizon_days: int = 60,
    ):
        self.snapshot_date_str = snapshot_date
        self.snapshot_date = pd.to_datetime(snapshot_date)
        self.horizon_days = prediction_horizon_days
        self.horizon_end = self.snapshot_date + pd.Timedelta(days=prediction_horizon_days)

    def create_labels(
        self,
        customers_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Label eligible customers:
        is_churn = 1 if 0 successful transactions in (snapshot_date, horizon_end]
        is_churn = 0 if >= 1 successful transaction in (snapshot_date, horizon_end]
        """
        cust = customers_df.copy()
        cust["signup_dt"] = pd.to_datetime(cust["signup_date"])
        cust["tenure_days"] = (self.snapshot_date - cust["signup_dt"]).dt.days
        eligible = cust[cust["tenure_days"] >= 30].copy()

        txns = transactions_df.copy()
        txns["txn_dt"] = pd.to_datetime(txns["transaction_date"])

        # Strictly filter to future prediction window
        future_txns = txns[
            (txns["txn_dt"] > self.snapshot_date)
            & (txns["txn_dt"] <= self.horizon_end)
            & (txns["transaction_status"] == "Success")
        ]

        active_customer_ids = set(future_txns["customer_id"].unique())

        labels = []
        for cid in eligible["customer_id"]:
            # If customer transacted in future window, retained (0); else churned (1)
            churn = 0 if cid in active_customer_ids else 1
            labels.append(
                {
                    "customer_id": cid,
                    "snapshot_date": self.snapshot_date_str,
                    "is_churn": churn,
                }
            )

        return pd.DataFrame(labels)
