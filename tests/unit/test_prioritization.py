"""Unit tests for customer prioritization rules and Excel business report generation."""
from pathlib import Path
import pandas as pd
import pytest
import openpyxl

from retentionlab.config.settings import PipelineConfig
from retentionlab.prioritization.framework import (
    assign_risk_and_prioritization,
    calculate_retention_scenarios,
)
from retentionlab.reporting.excel_generator import build_excel_report


@pytest.fixture
def sample_prioritization_inputs():
    features_df = pd.DataFrame([
        {"customer_id": "C1", "recency_days": 15, "total_transactions": 25, "total_spend": 3500.0, "frequency_ratio_30_to_90": 1.2, "recency_to_avg_interval_ratio": 0.8, "refund_rate": 0.01},
        {"customer_id": "C2", "recency_days": 110, "total_transactions": 18, "total_spend": 3600.0, "frequency_ratio_30_to_90": 0.1, "recency_to_avg_interval_ratio": 3.2, "refund_rate": 0.02},
        {"customer_id": "C3", "recency_days": 40, "total_transactions": 4, "total_spend": 250.0, "frequency_ratio_30_to_90": 0.8, "recency_to_avg_interval_ratio": 1.0, "refund_rate": 0.00},
        {"customer_id": "C4", "recency_days": 60, "total_transactions": 6, "total_spend": 500.0, "frequency_ratio_30_to_90": 0.9, "recency_to_avg_interval_ratio": 1.1, "refund_rate": 0.00},
    ])
    predictions_df = pd.DataFrame([
        {"customer_id": "C1", "risk_score": 0.12, "prediction_date": "2023-12-31", "model_version": "v1.0.0"},
        {"customer_id": "C2", "risk_score": 0.85, "prediction_date": "2023-12-31", "model_version": "v1.0.0"},
        {"customer_id": "C3", "risk_score": 0.45, "prediction_date": "2023-12-31", "model_version": "v1.0.0"},
        {"customer_id": "C4", "risk_score": 0.35, "prediction_date": "2023-12-31", "model_version": "v1.0.0"},
    ])
    return features_df, predictions_df


def test_customer_prioritization_rules(sample_prioritization_inputs):
    """Test 16: Customer prioritization rules and tier assignments."""
    features_df, predictions_df = sample_prioritization_inputs
    prio_df = assign_risk_and_prioritization(features_df, predictions_df)

    c2_row = prio_df[prio_df["customer_id"] == "C2"].iloc[0]
    # C2 has risk_score 0.85 (High Risk) and spend $2800 (High Value)
    assert c2_row["risk_tier"] == "High Risk"
    assert c2_row["monetary_tier"] == "High Value"
    assert "Tier 1: High-Value At-Risk" in c2_row["priority_segment"]
    assert "Phone" in c2_row["action_channel"]


def test_retention_scenario_calculations(sample_prioritization_inputs):
    """Test scenario calculation logic."""
    features_df, predictions_df = sample_prioritization_inputs
    prio_df = assign_risk_and_prioritization(features_df, predictions_df)

    scenarios = calculate_retention_scenarios(prio_df, cost_per_contact=15.0, assumed_retention_rate=0.20, budget_levels=[100.0])
    assert len(scenarios) > 0
    assert scenarios.iloc[0]["projected_spend_protected"] > 0
    assert "Illustrative" in scenarios.iloc[0]["scenario_assumption_notice"]


def test_excel_report_generation(tmp_path, sample_prioritization_inputs):
    """Test 17: Excel workbook generation with all 7 sheets."""
    features_df, predictions_df = sample_prioritization_inputs
    prio_df = assign_risk_and_prioritization(features_df, predictions_df)
    scenarios_df = calculate_retention_scenarios(prio_df)

    comp_df = pd.DataFrame([{
        "model_name": "LogisticRegression", "threshold": 0.54, "roc_auc": 0.77,
        "pr_auc": 0.52, "precision": 0.41, "recall": 0.68, "f1_score": 0.51, "brier_score": 0.14
    }])

    audit_data = {"row_count": 1000, "distinct_customer_count": 100}
    stat_tests = []

    out_excel = tmp_path / "test_report.xlsx"
    build_excel_report(prio_df, comp_df, scenarios_df, audit_data, stat_tests, output_path=out_excel)

    assert out_excel.exists()

    # Inspect openpyxl sheets
    wb = openpyxl.load_workbook(out_excel)
    expected_sheets = [
        "Executive Summary", "Customer Prioritization", "Model Evaluation",
        "Customer Segments", "Retention Scenarios", "Data Dictionary", "Methodology"
    ]
    for s in expected_sheets:
        assert s in wb.sheetnames
