from signalforge.diagnostics.engine import DiagnosticEngine
from signalforge.quality.rules import RuleEvaluationResult, RuleSeverity, RuleType
from signalforge.schema.drift import DriftReport, DriftSeverity, DriftType

def test_diagnose_breaking_schema_drift():
    drift_report = DriftReport(
        has_drift=True,
        severity=DriftSeverity.BREAKING,
        drift_types=[DriftType.REQUIRED_MISSING],
        diff={"missing_required": ["amount"]},
        recommended_action="Contact upstream",
        missing_required=["amount"]
    )
    diag = DiagnosticEngine.diagnose(
        failing_stage="VALIDATE",
        error_message="Breaking schema drift detected",
        dataset_name="fact_transactions",
        drift_report=drift_report
    )

    assert diag["error_category"] == "SCHEMA_DRIFT"
    assert diag["failing_stage"] == "VALIDATE"
    assert any("amount" in fact for fact in diag["facts"])
    assert len(diag["possible_causes"]) > 0
    assert len(diag["recommended_steps"]) > 0

def test_diagnose_quality_violation():
    eval_res = RuleEvaluationResult(
        rule_name="not_null_amount",
        rule_type=RuleType.NOT_NULL,
        dataset_name="fact_transactions",
        passed=False,
        total_checked=100,
        failed_count=5,
        severity=RuleSeverity.BATCH_FAIL
    )
    diag = DiagnosticEngine.diagnose(
        failing_stage="VALIDATE",
        error_message="Batch-fail quality rule violation triggered",
        dataset_name="fact_transactions",
        records_extracted=100,
        validation_results=[eval_res]
    )

    assert diag["error_category"] == "DATA_QUALITY_VIOLATION"
    assert any("100" in fact for fact in diag["facts"])
    assert any("not_null_amount" in fact for fact in diag["facts"])

def test_diagnose_upstream_api_timeout():
    diag = DiagnosticEngine.diagnose(
        failing_stage="EXTRACT",
        error_message="REST API extraction failed: HTTP connection timeout 503",
        dataset_name="partner_data"
    )

    assert diag["error_category"] == "UPSTREAM_UNAVAILABLE"
    assert any("503" in fact for fact in diag["facts"])
    assert any("retry" in step.lower() for step in diag["recommended_steps"])
