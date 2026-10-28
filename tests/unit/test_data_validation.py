"""Unit tests for dataset loading, schema checks, and data validation."""
import pandas as pd
import pytest
from retentionlab.preprocessing.cleaning import audit_transactions, clean_transactions, REQUIRED_COLUMNS


def test_schema_columns(sample_transactions_raw):
    """Test 1: Dataset loading and schema checks."""
    for col in REQUIRED_COLUMNS:
        assert col in sample_transactions_raw.columns


def test_duplicate_handling(sample_transactions_raw):
    """Test 3: Duplicate transaction handling."""
    dup_df = pd.concat([sample_transactions_raw, sample_transactions_raw.head(2)], ignore_index=True)
    assert len(dup_df) == len(sample_transactions_raw) + 2

    cleaned = clean_transactions(dup_df)
    assert len(cleaned) == len(sample_transactions_raw)
    assert cleaned["transaction_id"].duplicated().sum() == 0


def test_missing_value_handling(sample_transactions_raw):
    """Test 2: Missing value handling in clean_transactions."""
    df_missing = sample_transactions_raw.copy()
    # Add a row with null transaction date and customer_id
    null_row = pd.DataFrame([{
        "transaction_id": "T_NULL", "customer_id": None, "transaction_date": None,
        "transaction_amount": 100.0, "transaction_type": "purchase", "transaction_status": "completed",
        "product_category": "Books", "channel": "Web", "currency": "USD", "source_system": "WEB"
    }])
    df_missing = pd.concat([df_missing, null_row], ignore_index=True)
    cleaned = clean_transactions(df_missing)

    assert "T_NULL" not in cleaned["transaction_id"].values


def test_currency_handling(sample_transactions_raw):
    """Test 8: Currency uniformity check."""
    currencies = sample_transactions_raw["currency"].unique()
    assert len(currencies) == 1
    assert currencies[0] == "USD"


def test_empty_and_malformed_inputs():
    """Test 19: Empty and malformed input handling."""
    with pytest.raises(ValueError, match="Missing required column"):
        bad_df = pd.DataFrame([{"wrong_col": 123}])
        clean_transactions(bad_df)
