from datetime import datetime, timezone, timedelta
import pandas as pd
from signalforge.quality.rules import QualityRule, RuleSeverity, RuleType
from signalforge.quality.validator import QualityValidator

def test_not_null_rule():
    df = pd.DataFrame([
        {"id": "A", "val": 10},
        {"id": None, "val": 20},
        {"id": "", "val": 30},
    ])
    rule = QualityRule("not_null_id", RuleType.NOT_NULL, "test_ds", {"column": "id"}, RuleSeverity.RECORD_REJECT)
    validator = QualityValidator([rule])

    is_valid, valid_df, rejections, results = validator.evaluate(df, identifier_column="val")

    assert is_valid is True
    assert len(valid_df) == 1
    assert valid_df.iloc[0]["id"] == "A"
    assert len(rejections) == 2
    assert results[0].failed_count == 2
    assert results[0].passed is False

def test_unique_rule():
    df = pd.DataFrame([
        {"id": "A", "val": 10},
        {"id": "B", "val": 20},
        {"id": "A", "val": 30},
    ])
    rule = QualityRule("unique_id", RuleType.UNIQUE, "test_ds", {"column": "id"}, RuleSeverity.RECORD_REJECT)
    validator = QualityValidator([rule])

    is_valid, valid_df, rejections, results = validator.evaluate(df)

    assert is_valid is True
    assert len(valid_df) == 2
    assert len(rejections) == 1
    assert "Duplicate value 'A'" in rejections[0]["rejection_reasons"][0]

def test_non_negative_and_category_whitelist():
    df = pd.DataFrame([
        {"id": "1", "amount": 100.0, "status": "COMPLETED"},
        {"id": "2", "amount": -50.0, "status": "COMPLETED"},   # Negative amount
        {"id": "3", "amount": 200.0, "status": "INVALID_ST"},  # Invalid status
    ])
    rules = [
        QualityRule("non_neg", RuleType.NON_NEGATIVE, "test_ds", {"column": "amount"}, RuleSeverity.RECORD_REJECT),
        QualityRule("valid_status", RuleType.CATEGORY_WHITELIST, "test_ds", {"column": "status", "allowed_values": ["COMPLETED", "PENDING"]}, RuleSeverity.RECORD_REJECT)
    ]
    validator = QualityValidator(rules)

    is_valid, valid_df, rejections, results = validator.evaluate(df, identifier_column="id")

    assert is_valid is True
    assert len(valid_df) == 1
    assert valid_df.iloc[0]["id"] == "1"
    assert len(rejections) == 2

def test_referential_integrity():
    df = pd.DataFrame([
        {"tx_id": "T1", "customer_id": "CUST_1"},
        {"tx_id": "T2", "customer_id": "CUST_999"}, # Orphaned FK
    ])
    rule = QualityRule("fk_check", RuleType.REFERENTIAL_INTEGRITY, "transactions", {"column": "customer_id", "reference_dataset": "customers", "reference_column": "customer_id"}, RuleSeverity.RECORD_REJECT)
    validator = QualityValidator([rule])
    ref_data = {"customers": {"CUST_1", "CUST_2"}}

    is_valid, valid_df, rejections, results = validator.evaluate(df, reference_data=ref_data, identifier_column="tx_id")

    assert is_valid is True
    assert len(valid_df) == 1
    assert valid_df.iloc[0]["tx_id"] == "T1"
    assert len(rejections) == 1
    assert "does not exist in customers" in rejections[0]["rejection_reasons"][0]

def test_batch_fail_severity():
    df = pd.DataFrame([
        {"id": "1", "required_field": None},
    ])
    rule = QualityRule("strict_not_null", RuleType.NOT_NULL, "test_ds", {"column": "required_field"}, RuleSeverity.BATCH_FAIL)
    validator = QualityValidator([rule])

    is_valid, valid_df, rejections, results = validator.evaluate(df)

    assert is_valid is False
    assert results[0].passed is False
    assert results[0].severity == RuleSeverity.BATCH_FAIL

def test_data_freshness_check():
    now = datetime.now(timezone.utc)
    stale_time = (now - timedelta(hours=48)).isoformat()
    df = pd.DataFrame([{"timestamp": stale_time}])

    rule = QualityRule("freshness_24h", RuleType.DATA_FRESHNESS, "test_ds", {"column": "timestamp", "max_age_hours": 24}, RuleSeverity.BATCH_FAIL)
    validator = QualityValidator([rule])

    is_valid, valid_df, rejections, results = validator.evaluate(df)
    assert is_valid is False
    assert results[0].passed is False
    assert "Data stale" in results[0].sample_failures[0]["error"]
