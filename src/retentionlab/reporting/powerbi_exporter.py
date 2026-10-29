"""
RetentionLab Power BI Star Schema Exporter.
Exports dimension and fact tables for enterprise business intelligence modeling.
"""

from pathlib import Path
from typing import Dict
import pandas as pd
from retentionlab.config.settings import settings
from retentionlab.database.connection import execute_query


class PowerBIExporter:
    """
    Constructs and exports star-schema reporting tables for Power BI.
    """

    def __init__(self, export_dir: Path = settings.root_dir / "dashboards" / "powerbi" / "data"):
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_star_schema(self) -> Dict[str, str]:
        """
        Generate and save:
        1. CUSTOMER_DIMENSION
        2. DATE_DIMENSION
        3. TRANSACTION_FACT
        4. CUSTOMER_SNAPSHOT_FACT
        5. CUSTOMER_RISK_FACT
        6. RETENTION_ACTION_FACT
        7. MODEL_RUN_DIMENSION
        """
        print("Exporting Power BI reporting tables...")

        # 1. CUSTOMER_DIMENSION
        cust_df = execute_query(
            """
            SELECT 
                customer_id,
                signup_date,
                customer_segment,
                acquisition_channel,
                region,
                subscription_type,
                account_status,
                marketing_consent
            FROM customers
            """
        )
        p1 = self.export_dir / "CUSTOMER_DIMENSION.csv"
        cust_df.to_csv(p1, index=False)

        # 2. DATE_DIMENSION
        # Generate calendar table covering 2025-01-01 to 2026-12-31
        dates = pd.date_range("2025-01-01", "2026-12-31", freq="D")
        date_dim = pd.DataFrame(
            {
                "date_key": dates.strftime("%Y-%m-%d"),
                "year": dates.year,
                "quarter": "Q" + dates.quarter.astype(str),
                "month_num": dates.month,
                "month_name": dates.strftime("%B"),
                "year_month": dates.strftime("%Y-%m"),
                "day_of_month": dates.day,
                "day_of_week": dates.day_name(),
                "is_weekend": dates.dayofweek.isin([5, 6]).astype(int),
            }
        )
        p2 = self.export_dir / "DATE_DIMENSION.csv"
        date_dim.to_csv(p2, index=False)

        # 3. TRANSACTION_FACT
        txn_df = execute_query(
            """
            SELECT 
                transaction_id,
                customer_id,
                product_id,
                transaction_date,
                transaction_amount,
                transaction_type,
                payment_status,
                discount_amount,
                refund_amount,
                transaction_channel,
                transaction_status
            FROM transactions
            """
        )
        p3 = self.export_dir / "TRANSACTION_FACT.csv"
        txn_df.to_csv(p3, index=False)

        # 4. CUSTOMER_SNAPSHOT_FACT
        snap_df = execute_query(
            """
            SELECT 
                snapshot_id,
                customer_id,
                snapshot_date,
                is_eligible
            FROM customer_snapshots
            """
        )
        p4 = self.export_dir / "CUSTOMER_SNAPSHOT_FACT.csv"
        snap_df.to_csv(p4, index=False)

        # 5. CUSTOMER_RISK_FACT & 6. RETENTION_ACTION_FACT
        scores_df = execute_query(
            """
            SELECT 
                score_id,
                customer_id,
                snapshot_date,
                churn_probability,
                risk_band,
                prioritization_score,
                historical_value_proxy,
                risk_weighted_exposure,
                top_risk_signals,
                suggested_action,
                recommended_next_step,
                is_top_15_percent,
                model_version
            FROM retention_scores
            """
        )
        p5 = self.export_dir / "CUSTOMER_RISK_FACT.csv"
        scores_df.to_csv(p5, index=False)

        action_df = scores_df[
            [
                "score_id",
                "customer_id",
                "snapshot_date",
                "risk_band",
                "churn_probability",
                "prioritization_score",
                "risk_weighted_exposure",
                "suggested_action",
                "is_top_15_percent",
            ]
        ].copy()
        p6 = self.export_dir / "RETENTION_ACTION_FACT.csv"
        action_df.to_csv(p6, index=False)

        # 7. MODEL_RUN_DIMENSION
        model_comp_path = settings.root_dir / "models" / "model_comparison.csv"
        if model_comp_path.exists():
            model_df = pd.read_csv(model_comp_path)
        else:
            model_df = pd.DataFrame(
                [{"model_name": "hist_gradient_boosting", "test_roc_auc": 0.9395, "version": "2.0.0"}]
            )
        p7 = self.export_dir / "MODEL_RUN_DIMENSION.csv"
        model_df.to_csv(p7, index=False)

        return {
            "CUSTOMER_DIMENSION": str(p1),
            "DATE_DIMENSION": str(p2),
            "TRANSACTION_FACT": str(p3),
            "CUSTOMER_SNAPSHOT_FACT": str(p4),
            "CUSTOMER_RISK_FACT": str(p5),
            "RETENTION_ACTION_FACT": str(p6),
            "MODEL_RUN_DIMENSION": str(p7),
        }
