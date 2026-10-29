from sqlalchemy.orm import Session
from signalforge.failure_lab.scenarios import FailureLab

def test_all_failure_lab_scenarios(db_session: Session):
    lab = FailureLab(db_session)
    scenarios = lab.list_scenarios()

    assert len(scenarios) == 8

    expected_categories = {
        "duplicate_records": "DATA_QUALITY_VIOLATION",
        "missing_required_fields": "DATA_QUALITY_VIOLATION",
        "breaking_schema_drift": "SCHEMA_DRIFT",
        "malformed_input": "SOURCE_FORMAT_ERROR",
        "unavailable_api": "UPSTREAM_UNAVAILABLE",
        "referential_integrity_violation": "DATA_QUALITY_VIOLATION",
        "stale_data": "DATA_QUALITY_VIOLATION",
        "interrupted_run_idempotent_retry": None,
    }

    for sc in scenarios:
        sid = sc["id"]
        res = lab.run_scenario(sid)

        expected_cat = expected_categories[sid]
        if expected_cat:
            assert res["status"] == "FAILED", f"Scenario {sid} was expected to fail"
            assert res["error_category"] == expected_cat, f"Scenario {sid} category mismatch"
            assert res["diagnostic"] is not None
            assert len(res["diagnostic"]["facts"]) > 0
            assert len(res["diagnostic"]["recommended_steps"]) > 0
        else:
            # Idempotency scenario succeeds
            assert res["status"] == "COMPLETED"
            assert res["duplicate_created"] == 0
            assert res["idempotency_verified"] is True
