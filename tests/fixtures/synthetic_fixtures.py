"""Deterministic test fixtures for RetentionLab test suite."""
import pandas as pd
import pytest


@pytest.fixture
def sample_transactions_raw():
    """Deterministic transaction dataset covering all edge cases."""
    return pd.DataFrame([
        # Customer 1: Regular frequent purchaser, stays active in 2024
        {"transaction_id": "T1", "customer_id": "C1", "transaction_date": "2023-01-10 10:00:00", "transaction_amount": 100.0, "transaction_type": "purchase", "transaction_status": "completed", "product_category": "Apparel", "channel": "Web", "currency": "USD", "source_system": "WEB"},
        {"transaction_id": "T2", "customer_id": "C1", "transaction_date": "2023-06-15 12:00:00", "transaction_amount": 150.0, "transaction_type": "purchase", "transaction_status": "completed", "product_category": "Apparel", "channel": "Web", "currency": "USD", "source_system": "WEB"},
        {"transaction_id": "T3", "customer_id": "C1", "transaction_date": "2023-12-20 15:00:00", "transaction_amount": 200.0, "transaction_type": "purchase", "transaction_status": "completed", "product_category": "Electronics", "channel": "Mobile App", "currency": "USD", "source_system": "APP"},
        {"transaction_id": "T4", "customer_id": "C1", "transaction_date": "2024-01-15 11:00:00", "transaction_amount": 120.0, "transaction_type": "purchase", "transaction_status": "completed", "product_category": "Apparel", "channel": "Web", "currency": "USD", "source_system": "WEB"},

        # Customer 2: Active in early 2023, stops buying (churns in 2024)
        {"transaction_id": "T5", "customer_id": "C2", "transaction_date": "2023-02-01 09:00:00", "transaction_amount": 80.0, "transaction_type": "purchase", "transaction_status": "completed", "product_category": "Books", "channel": "Web", "currency": "USD", "source_system": "WEB"},
        {"transaction_id": "T6", "customer_id": "C2", "transaction_date": "2023-04-10 14:00:00", "transaction_amount": 90.0, "transaction_type": "purchase", "transaction_status": "completed", "product_category": "Books", "channel": "Web", "currency": "USD", "source_system": "WEB"},

        # Customer 3: Joined too late (less than 30 days before cutoff date 2023-12-31) -> Ineligible
        {"transaction_id": "T7", "customer_id": "C3", "transaction_date": "2023-12-15 16:00:00", "transaction_amount": 50.0, "transaction_type": "purchase", "transaction_status": "completed", "product_category": "Home & Kitchen", "channel": "In-Store", "currency": "USD", "source_system": "POS"},

        # Customer 4: Refund and failed transaction handling
        {"transaction_id": "T8", "customer_id": "C4", "transaction_date": "2023-03-01 10:00:00", "transaction_amount": 200.0, "transaction_type": "purchase", "transaction_status": "completed", "product_category": "Electronics", "channel": "Web", "currency": "USD", "source_system": "WEB"},
        {"transaction_id": "T9", "customer_id": "C4", "transaction_date": "2023-03-05 11:00:00", "transaction_amount": -50.0, "transaction_type": "refund", "transaction_status": "completed", "product_category": "Electronics", "channel": "Web", "currency": "USD", "source_system": "WEB"},
        {"transaction_id": "T10", "customer_id": "C4", "transaction_date": "2023-08-10 14:00:00", "transaction_amount": 100.0, "transaction_type": "purchase", "transaction_status": "failed", "product_category": "Electronics", "channel": "Web", "currency": "USD", "source_system": "WEB"},
    ])
