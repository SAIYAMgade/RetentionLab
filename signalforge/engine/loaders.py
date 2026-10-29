from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from signalforge.db.models import DimCustomer, FactTransaction, PipelineCheckpoint

class SafeLoader:
    """Handles transactional, idempotent data loading into PostgreSQL / SQLite."""

    def __init__(self, db: Session):
        self.db = db

    def load_customers(self, df: pd.DataFrame) -> int:
        """
        Idempotently upserts customers into dim_customers within active transaction.
        Returns count of loaded/updated records.
        """
        if df.empty:
            return 0

        loaded_count = 0
        for _, row in df.iterrows():
            customer_id = str(row["customer_id"])
            existing = self.db.query(DimCustomer).filter(DimCustomer.customer_id == customer_id).first()

            signup_dt = pd.to_datetime(row["signup_date"]).to_pydatetime()

            if existing:
                existing.name = str(row["name"])
                existing.email = str(row["email"])
                existing.country = str(row["country"])
                existing.signup_date = signup_dt
            else:
                new_cust = DimCustomer(
                    customer_id=customer_id,
                    name=str(row["name"]),
                    email=str(row["email"]),
                    country=str(row["country"]),
                    signup_date=signup_dt
                )
                self.db.add(new_cust)

            loaded_count += 1

        self.db.flush()
        return loaded_count

    def load_transactions(self, df: pd.DataFrame) -> int:
        """
        Idempotently upserts transactions into fact_transactions within active transaction.
        Returns count of loaded/updated records.
        """
        if df.empty:
            return 0

        loaded_count = 0
        for _, row in df.iterrows():
            tx_id = str(row["transaction_id"])
            existing = self.db.query(FactTransaction).filter(FactTransaction.transaction_id == tx_id).first()

            tx_dt = pd.to_datetime(row["transaction_timestamp"]).to_pydatetime()
            amt = float(row["amount"])

            if existing:
                existing.customer_id = str(row["customer_id"])
                existing.amount = amt
                existing.currency = str(row.get("currency", "USD"))
                existing.status = str(row["status"])
                existing.transaction_timestamp = tx_dt
                existing.payment_method = str(row.get("payment_method", "credit_card"))
            else:
                new_tx = FactTransaction(
                    transaction_id=tx_id,
                    customer_id=str(row["customer_id"]),
                    amount=amt,
                    currency=str(row.get("currency", "USD")),
                    status=str(row["status"]),
                    transaction_timestamp=tx_dt,
                    payment_method=str(row.get("payment_method", "credit_card"))
                )
                self.db.add(new_tx)

            loaded_count += 1

        self.db.flush()
        return loaded_count

    def update_checkpoint(self, pipeline_id: str, checkpoint_key: str, checkpoint_value: str) -> None:
        """Atomically persists pipeline checkpoint in the same database transaction."""
        cp = (
            self.db.query(PipelineCheckpoint)
            .filter(
                PipelineCheckpoint.pipeline_id == pipeline_id,
                PipelineCheckpoint.checkpoint_key == checkpoint_key
            )
            .first()
        )
        if cp:
            cp.checkpoint_value = checkpoint_value
        else:
            cp = PipelineCheckpoint(
                pipeline_id=pipeline_id,
                checkpoint_key=checkpoint_key,
                checkpoint_value=checkpoint_value
            )
            self.db.add(cp)
        self.db.flush()
