from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from signalforge.db.models import DataSource, Pipeline, PipelineRun, RunStage, DimCustomer
from signalforge.engine.extractors import CSVExtractor
from signalforge.engine.pipeline import PipelineEngine
from signalforge.quality.rules import QualityRule, RuleSeverity, RuleType

def test_pipeline_successful_run(db_session: Session, temp_dir: Path):
    csv_file = temp_dir / "customers.csv"
    df = pd.DataFrame([
        {"customer_id": "CUST_1", "name": "Alice", "email": "alice@example.com", "country": "USA", "signup_date": "2026-01-01T00:00:00Z"},
        {"customer_id": "CUST_2", "name": "Bob", "email": "bob@example.com", "country": "CAN", "signup_date": "2026-01-02T00:00:00Z"},
    ])
    df.to_csv(csv_file, index=False)

    source = DataSource(name="test_cust_source", source_type="CSV", config_json={"path": str(csv_file)})
    db_session.add(source)
    db_session.commit()

    pipeline = Pipeline(
        name="test_cust_pipeline",
        source_id=source.id,
        target_table="dim_customers",
        batch_fail_policy="REJECT_AND_CONTINUE"
    )
    db_session.add(pipeline)
    db_session.commit()

    extractor = CSVExtractor(str(csv_file))
    rules = [
        QualityRule("not_null_id", RuleType.NOT_NULL, "dim_customers", {"column": "customer_id"}, RuleSeverity.BATCH_FAIL),
        QualityRule("unique_id", RuleType.UNIQUE, "dim_customers", {"column": "customer_id"}, RuleSeverity.BATCH_FAIL),
    ]

    engine = PipelineEngine(db_session, pipeline, extractor, quality_rules=rules, dataset_name="dim_customers", identifier_column="customer_id")
    run = engine.run(trigger_type="MANUAL")

    assert run.status == "COMPLETED"
    assert run.records_extracted == 2
    assert run.records_loaded == 2
    assert run.records_rejected == 0
    assert run.duration_ms > 0

    # Verify stage progression
    stages = db_session.query(RunStage).filter(RunStage.run_id == run.id).order_by(RunStage.started_at.asc()).all()
    stage_names = [s.stage_name for s in stages]
    assert "EXTRACT" in stage_names
    assert "VALIDATE" in stage_names
    assert "TRANSFORM" in stage_names
    assert "LOAD" in stage_names
    assert "VERIFY" in stage_names

    # Verify target table records in DB
    customers_in_db = db_session.query(DimCustomer).all()
    assert len(customers_in_db) == 2

def test_pipeline_transaction_rollback_on_batch_fail(db_session: Session, temp_dir: Path):
    csv_file = temp_dir / "bad_customers.csv"
    # Null customer_id violates batch fail rule
    df = pd.DataFrame([
        {"customer_id": None, "name": "Invalid", "email": "bad@example.com", "country": "USA", "signup_date": "2026-01-01T00:00:00Z"},
    ])
    df.to_csv(csv_file, index=False)

    source = DataSource(name="bad_source", source_type="CSV", config_json={"path": str(csv_file)})
    db_session.add(source)
    db_session.commit()

    pipeline = Pipeline(
        name="bad_pipeline",
        source_id=source.id,
        target_table="dim_customers",
        batch_fail_policy="FAIL_ON_ERROR"
    )
    db_session.add(pipeline)
    db_session.commit()

    extractor = CSVExtractor(str(csv_file))
    rules = [
        QualityRule("not_null_id", RuleType.NOT_NULL, "dim_customers", {"column": "customer_id"}, RuleSeverity.BATCH_FAIL),
    ]

    engine = PipelineEngine(db_session, pipeline, extractor, quality_rules=rules, dataset_name="dim_customers")
    run = engine.run(trigger_type="MANUAL")

    assert run.status == "FAILED"
    assert run.error_category == "DATA_QUALITY_VIOLATION"
    assert run.records_loaded == 0

    # Ensure zero records written to DB (rollback verified)
    assert db_session.query(DimCustomer).count() == 0
