"""
Unit tests for Deterministic Synthetic Data Generator.
"""

import pytest
import pandas as pd
import numpy as np
from retentionlab.data_generation.generator import SyntheticDataGenerator


def test_generator_determinism():
    """Verify that identical seeds produce identical datasets."""
    gen1 = SyntheticDataGenerator(num_customers=50, random_seed=42, target_transaction_count=1000)
    gen2 = SyntheticDataGenerator(num_customers=50, random_seed=42, target_transaction_count=1000)

    cust1, _ = gen1.generate_customers()
    cust2, _ = gen2.generate_customers()

    pd.testing.assert_frame_equal(cust1, cust2)


def test_generator_foreign_keys_and_ranges():
    """Verify customer references, non-negative amounts, and date ordering."""
    gen = SyntheticDataGenerator(num_customers=100, random_seed=42, target_transaction_count=2000)
    prods = gen.generate_products()
    custs, risk = gen.generate_customers()
    txns = gen.generate_transactions(custs, prods, risk)

    # 1. Foreign keys
    valid_cids = set(custs["customer_id"])
    valid_pids = set(prods["product_id"])
    assert txns["customer_id"].isin(valid_cids).all()
    assert txns["product_id"].isin(valid_pids).all()

    # 2. Non-negative amounts
    assert (txns["transaction_amount"] > 0).all()
    assert (txns["discount_amount"] >= 0).all()
    assert (txns["refund_amount"] >= 0).all()

    # 3. Transaction ID uniqueness
    assert txns["transaction_id"].nunique() == len(txns)


def test_target_scale_constraint():
    """Verify target transaction count threshold."""
    gen = SyntheticDataGenerator(num_customers=5000, random_seed=42, target_transaction_count=100000)
    prods = gen.generate_products()
    custs, risk = gen.generate_customers()
    txns = gen.generate_transactions(custs, prods, risk)

    assert len(txns) >= 97000, f"Expected >= 97,000 transactions, got {len(txns)}"
