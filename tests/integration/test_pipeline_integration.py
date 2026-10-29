"""
Integration test for complete end-to-end analytical pipeline.
"""

from pathlib import Path
import pytest
from retentionlab.config.settings import settings
from retentionlab.database.connection import execute_query


def test_database_table_counts():
    """Verify that database holds expected row volumes."""
    cust_cnt = execute_query("SELECT COUNT(*) as c FROM customers")["c"].iloc[0]
    txn_cnt = execute_query("SELECT COUNT(*) as c FROM transactions")["c"].iloc[0]
    score_cnt = execute_query("SELECT COUNT(*) as c FROM retention_scores")["c"].iloc[0]

    assert cust_cnt == 5000
    assert txn_cnt >= 97000
    assert score_cnt > 0


def test_model_artifacts_exist():
    """Verify saved model pipeline and metadata JSON."""
    models_dir = settings.root_dir / "models"
    assert (models_dir / "retention_model_pipeline.joblib").exists()
    assert (models_dir / "model_metadata.json").exists()
    assert (models_dir / "model_comparison.csv").exists()
    assert (models_dir / "feature_importance.csv").exists()
