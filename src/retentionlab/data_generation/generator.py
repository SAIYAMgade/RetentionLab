"""
RetentionLab Deterministic Synthetic Data Generator.
Produces customer, transaction, product, activity, support, and campaign records
with realistic behavioral decay, friction signals, and target churn labels.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from retentionlab.config.settings import settings


class SyntheticDataGenerator:
    """
    Generates realistic, deterministic relational datasets for churn prediction
    and customer retention prioritization.
    """

    def __init__(
        self,
        num_customers: int = 5000,
        random_seed: int = 42,
        start_date: str = "2025-01-01",
        end_date: str = "2026-06-01",
        snapshot_date: str = "2026-04-01",
        target_transaction_count: int = 100000,
    ):
        self.num_customers = num_customers
        self.random_seed = random_seed
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.snapshot_date = datetime.strptime(snapshot_date, "%Y-%m-%d")
        self.target_transaction_count = target_transaction_count
        self.rng = np.random.RandomState(random_seed)

    def generate_products(self) -> pd.DataFrame:
        """Create reference catalog of products."""
        products = [
            ("PROD-01", "Core Analytics Platform", "Analytics", 499.00),
            ("PROD-02", "Predictive Retention Suite", "Analytics", 899.00),
            ("PROD-03", "Data Pipeline Connector", "Integration", 299.00),
            ("PROD-04", "Webhook & Event Ingestion", "Integration", 199.00),
            ("PROD-05", "Enterprise Security Audit", "Security", 1200.00),
            ("PROD-06", "Access Governance Module", "Security", 650.00),
            ("PROD-07", "Automated Action Dispatcher", "Automation", 350.00),
            ("PROD-08", "Campaign Workflow Builder", "Automation", 450.00),
            ("PROD-09", "Cloud Storage Cluster", "Infrastructure", 750.00),
            ("PROD-10", "High-Throughput Node", "Infrastructure", 1500.00),
        ]
        return pd.DataFrame(
            products,
            columns=["product_id", "product_name", "product_category", "unit_price"],
        )

    def generate_customers(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Create customer demographics, segments, and latent churn propensity.
        Returns (customers_df, churn_propensities).
        """
        customer_ids = [f"CUST-{i+1:05d}" for i in range(self.num_customers)]

        # Sign-up dates staggered between start_date and snapshot_date - 15 days
        max_signup_offset = (self.snapshot_date - timedelta(days=15) - self.start_date).days
        signup_offsets = self.rng.randint(0, max_signup_offset, size=self.num_customers)
        signup_dates = [self.start_date + timedelta(days=int(offset)) for offset in signup_offsets]

        segments = self.rng.choice(
            ["Enterprise", "Mid-Market", "SMB", "Startup"],
            size=self.num_customers,
            p=[0.15, 0.30, 0.35, 0.20],
        )
        channels = self.rng.choice(
            ["Direct", "Organic Search", "Paid Search", "Referral", "Partner"],
            size=self.num_customers,
            p=[0.20, 0.25, 0.25, 0.15, 0.15],
        )
        regions = self.rng.choice(
            ["North America", "Europe", "APAC", "LATAM"],
            size=self.num_customers,
            p=[0.45, 0.30, 0.15, 0.10],
        )
        subscriptions = self.rng.choice(
            ["Annual", "Monthly", "Quarterly"],
            size=self.num_customers,
            p=[0.35, 0.50, 0.15],
        )

        tenure_days = [max(1, (self.snapshot_date - d).days) for d in signup_dates]

        # Latent churn risk propensity θ_i in [0, 1]
        base_risk = self.rng.beta(2, 5, size=self.num_customers)  # ~0.28 mean
        # Monthly subscriptions and paid search channels have slightly higher churn risk
        sub_risk = np.where(subscriptions == "Monthly", 0.12, np.where(subscriptions == "Quarterly", 0.05, -0.08))
        segment_risk = np.where(segments == "Startup", 0.10, np.where(segments == "Enterprise", -0.15, 0.0))
        channel_risk = np.where(channels == "Paid Search", 0.06, np.where(channels == "Referral", -0.05, 0.0))

        latent_risk = np.clip(base_risk + sub_risk + segment_risk + channel_risk, 0.02, 0.95)

        # Status: active or churned/suspended
        status = np.where(latent_risk > 0.85, "Suspended", "Active")

        marketing_consent = self.rng.choice([1, 0], size=self.num_customers, p=[0.85, 0.15])

        df_customers = pd.DataFrame(
            {
                "customer_id": customer_ids,
                "signup_date": [d.strftime("%Y-%m-%d") for d in signup_dates],
                "customer_segment": segments,
                "acquisition_channel": channels,
                "region": regions,
                "subscription_type": subscriptions,
                "account_status": status,
                "marketing_consent": marketing_consent,
                "tenure_days": tenure_days,
            }
        )
        return df_customers, latent_risk

    def generate_transactions(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        churn_propensities: np.ndarray,
    ) -> pd.DataFrame:
        """
        Generate >97,000 transactions across the observation and prediction horizons.
        Retained customers continue transacting through the prediction window.
        Churned customers cease or dramatically taper transactions after snapshot.
        """
        prod_ids = products_df["product_id"].values
        prod_prices = dict(zip(products_df["product_id"], products_df["unit_price"]))

        txn_records = []
        txn_id_counter = 1

        signup_dates = [datetime.strptime(d, "%Y-%m-%d") for d in customers_df["signup_date"]]
        cust_ids = customers_df["customer_id"].values
        segments = customers_df["customer_segment"].values
        tenures = customers_df["tenure_days"].values

        total_days = (self.end_date - self.start_date).days

        # Pre-assign future churn status: customers with high latent risk who cross threshold churn
        # Approx 22-26% churn rate overall
        is_churn = (churn_propensities + self.rng.normal(0, 0.08, size=self.num_customers)) > 0.46
        # Ineligible customers (tenure < 30) do not churn in target
        is_churn = np.where(tenures < 30, False, is_churn)

        # Number of transactions per customer scaled to hit target >97,000
        # Average ~21 transactions per customer -> ~105,000 transactions
        base_txn_counts = self.rng.poisson(lam=21, size=self.num_customers)
        base_txn_counts = np.clip(base_txn_counts, 6, 75)

        for i in range(self.num_customers):
            c_id = cust_ids[i]
            c_signup = signup_dates[i]
            c_churn = is_churn[i]
            c_risk = churn_propensities[i]
            c_segment = segments[i]
            n_txns = base_txn_counts[i]

            # Date boundaries
            # If churned, transactions occur strictly BEFORE or right up to snapshot date
            # with decreasing frequency as snapshot nears
            if c_churn:
                effective_end = min(self.snapshot_date, self.snapshot_date - timedelta(days=int(self.rng.randint(3, 45))))
            else:
                effective_end = self.end_date

            window_days = max(1, (effective_end - c_signup).days)
            if window_days <= 1:
                offsets = np.zeros(n_txns, dtype=int)
            else:
                if c_churn:
                    # Skew transactions earlier in the window (decaying behavior)
                    weights = self.rng.beta(1.5, 4.0, size=n_txns)
                else:
                    # Uniform or slight recency boost
                    weights = self.rng.beta(2.5, 2.0, size=n_txns)
                offsets = np.clip((weights * window_days).astype(int), 0, window_days - 1)

            offsets.sort()

            # Segment spend multipliers
            seg_mult = 3.5 if c_segment == "Enterprise" else (1.8 if c_segment == "Mid-Market" else 1.0)

            for offset in offsets:
                t_date = c_signup + timedelta(days=int(offset))
                p_id = self.rng.choice(prod_ids)
                base_price = prod_prices[p_id] * seg_mult

                # Add noise and transaction type
                amt = round(float(base_price * self.rng.uniform(0.85, 1.25)), 2)
                t_type = self.rng.choice(
                    ["Purchase", "Renewal", "Addon", "Upgrade"],
                    p=[0.55, 0.25, 0.15, 0.05],
                )

                # Payment failure: higher for risky customers
                fail_p = 0.08 if c_risk > 0.6 else 0.015
                is_failed = self.rng.random() < fail_p
                pay_status = "Failed" if is_failed else "Completed"

                # Discounts
                has_discount = self.rng.random() < 0.22
                disc_amt = round(float(amt * self.rng.uniform(0.05, 0.20)), 2) if has_discount else 0.00

                # Refunds: slightly higher for risky/complaint customers
                refund_p = 0.05 if c_risk > 0.65 else 0.01
                is_refunded = (not is_failed) and (self.rng.random() < refund_p)
                ref_amt = amt if is_refunded else 0.00

                status = "Cancelled" if is_failed else ("Refunded" if is_refunded else "Success")
                channel = self.rng.choice(["Web", "API", "Mobile", "Partner"], p=[0.50, 0.25, 0.15, 0.10])

                txn_records.append(
                    (
                        f"TXN-{txn_id_counter:07d}",
                        c_id,
                        p_id,
                        t_date.strftime("%Y-%m-%d"),
                        amt,
                        t_type,
                        pay_status,
                        disc_amt,
                        ref_amt,
                        channel,
                        status,
                    )
                )
                txn_id_counter += 1

        df_txns = pd.DataFrame(
            txn_records,
            columns=[
                "transaction_id",
                "customer_id",
                "product_id",
                "transaction_date",
                "transaction_amount",
                "transaction_type",
                "payment_status",
                "discount_amount",
                "refund_amount",
                "transaction_channel",
                "transaction_status",
            ],
        )
        return df_txns

    def generate_activity(self, customers_df: pd.DataFrame, churn_propensities: np.ndarray) -> pd.DataFrame:
        """Generate customer logins and platform activity events."""
        act_records = []
        act_id = 1
        signup_dates = [datetime.strptime(d, "%Y-%m-%d") for d in customers_df["signup_date"]]
        cust_ids = customers_df["customer_id"].values

        for i in range(self.num_customers):
            c_id = cust_ids[i]
            c_signup = signup_dates[i]
            c_risk = churn_propensities[i]

            # Number of activity events: high-risk customers have declining activity
            num_events = int(self.rng.poisson(lam=28 if c_risk < 0.4 else 14))
            num_events = max(4, num_events)

            # If risk is high, logins taper off before snapshot
            if c_risk > 0.55:
                max_date = min(self.snapshot_date, self.snapshot_date - timedelta(days=int(self.rng.randint(5, 30))))
            else:
                max_date = self.end_date

            max_offset = max(1, (max_date - c_signup).days)
            offsets = self.rng.randint(0, max_offset, size=num_events)
            offsets.sort()

            for off in offsets:
                act_date = c_signup + timedelta(days=int(off))
                act_type = self.rng.choice(
                    ["login", "dashboard_view", "report_view", "api_call", "export"],
                    p=[0.40, 0.25, 0.15, 0.12, 0.08],
                )
                act_records.append(
                    (f"ACT-{act_id:07d}", c_id, act_date.strftime("%Y-%m-%d"), act_type)
                )
                act_id += 1

        return pd.DataFrame(
            act_records,
            columns=["activity_id", "customer_id", "activity_date", "activity_type"],
        )

    def generate_support_tickets(self, customers_df: pd.DataFrame, churn_propensities: np.ndarray) -> pd.DataFrame:
        """Generate support tickets, complaints, and CSAT scores."""
        ticket_records = []
        ticket_id = 1
        signup_dates = [datetime.strptime(d, "%Y-%m-%d") for d in customers_df["signup_date"]]
        cust_ids = customers_df["customer_id"].values

        for i in range(self.num_customers):
            c_id = cust_ids[i]
            c_signup = signup_dates[i]
            c_risk = churn_propensities[i]

            # High risk customers experience more tickets and complaints
            lam_tickets = 3.8 if c_risk > 0.6 else 1.2
            num_tickets = self.rng.poisson(lam=lam_tickets)

            max_offset = max(1, (self.end_date - c_signup).days)
            offsets = self.rng.randint(0, max_offset, size=num_tickets)
            offsets.sort()

            for off in offsets:
                t_date = c_signup + timedelta(days=int(off))
                # Risky customers file more complaints
                complaint_p = 0.35 if c_risk > 0.6 else 0.08
                t_type = "complaint" if self.rng.random() < complaint_p else self.rng.choice(
                    ["technical", "billing", "feature_request"], p=[0.55, 0.25, 0.20]
                )
                status = self.rng.choice(["closed", "resolved", "open"], p=[0.70, 0.22, 0.08])
                csat = int(self.rng.choice([1, 2, 3, 4, 5], p=[0.35, 0.30, 0.20, 0.10, 0.05])) if c_risk > 0.6 else int(self.rng.choice([1, 2, 3, 4, 5], p=[0.05, 0.08, 0.15, 0.42, 0.30]))

                ticket_records.append(
                    (f"TCK-{ticket_id:06d}", c_id, t_date.strftime("%Y-%m-%d"), t_type, status, csat)
                )
                ticket_id += 1

        return pd.DataFrame(
            ticket_records,
            columns=["ticket_id", "customer_id", "ticket_date", "ticket_type", "status", "satisfaction_score"],
        )

    def generate_campaigns(self, customers_df: pd.DataFrame, churn_propensities: np.ndarray) -> pd.DataFrame:
        """Generate email, webinar, and notification campaign touchpoints."""
        camp_records = []
        camp_id = 1
        signup_dates = [datetime.strptime(d, "%Y-%m-%d") for d in customers_df["signup_date"]]
        cust_ids = customers_df["customer_id"].values

        for i in range(self.num_customers):
            c_id = cust_ids[i]
            c_signup = signup_dates[i]
            c_risk = churn_propensities[i]

            num_camps = self.rng.poisson(lam=6.5)
            max_offset = max(1, (self.end_date - c_signup).days)
            offsets = self.rng.randint(0, max_offset, size=num_camps)
            offsets.sort()

            for off in offsets:
                camp_date = c_signup + timedelta(days=int(off))
                channel = self.rng.choice(["email", "webinar", "notification"], p=[0.70, 0.15, 0.15])
                # Lower open / click rate for risky disengaged customers
                if c_risk > 0.6:
                    action = self.rng.choice(["delivered", "opened", "clicked", "unsubscribed"], p=[0.75, 0.18, 0.05, 0.02])
                else:
                    action = self.rng.choice(["delivered", "opened", "clicked", "unsubscribed"], p=[0.45, 0.35, 0.19, 0.01])

                camp_records.append(
                    (f"CAM-{camp_id:06d}", c_id, camp_date.strftime("%Y-%m-%d"), channel, action)
                )
                camp_id += 1

        return pd.DataFrame(
            camp_records,
            columns=["interaction_id", "customer_id", "campaign_date", "channel", "action"],
        )

    def generate_snapshots(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create customer scoring snapshots at snapshot_date.
        Only customers with tenure >= 30 days are eligible for scoring.
        """
        snapshots = []
        for _, row in customers_df.iterrows():
            c_id = row["customer_id"]
            tenure = row["tenure_days"]
            is_eligible = 1 if tenure >= 30 else 0
            snapshots.append(
                (f"SNAP-{c_id}-{self.snapshot_date.strftime('%Y%m%d')}", c_id, self.snapshot_date.strftime("%Y-%m-%d"), is_eligible)
            )

        return pd.DataFrame(
            snapshots,
            columns=["snapshot_id", "customer_id", "snapshot_date", "is_eligible"],
        )

    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """
        Orchestrate complete deterministic dataset generation and validate integrity.
        """
        products_df = self.generate_products()
        customers_df, churn_propensities = self.generate_customers()
        transactions_df = self.generate_transactions(customers_df, products_df, churn_propensities)
        activity_df = self.generate_activity(customers_df, churn_propensities)
        tickets_df = self.generate_support_tickets(customers_df, churn_propensities)
        campaigns_df = self.generate_campaigns(customers_df, churn_propensities)
        snapshots_df = self.generate_snapshots(customers_df)

        # Integrity check: Target transactions >= 97,000
        total_txns = len(transactions_df)
        if total_txns < 97000:
            raise ValueError(f"Transaction count {total_txns} is below required threshold of 97,000!")

        return {
            "products": products_df,
            "customers": customers_df,
            "transactions": transactions_df,
            "customer_activity": activity_df,
            "support_tickets": tickets_df,
            "campaign_interactions": campaigns_df,
            "customer_snapshots": snapshots_df,
        }
