from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from signalforge.db.models import DataSource, Pipeline, DimCustomer, FactTransaction, PipelineCheckpoint
from signalforge.engine.extractors import CSVExtractor
from signalforge.engine.pipeline import PipelineEngine

def test_idempotent_customer_loading(db_session: Session, temp_dir: Path):
    csv_file = temp_dir / "cust_idemp.csv"
    df = pd.DataFrame([
        {"customer_id": "C_101", "name": "Initial Name", "email": "initial@example.com", "country": "USA", "signup_date": "2026-01-01T00:00:00Z"},
    ])
    df.to_csv(csv_file, index=False)

    source = DataSource(name="cust_idemp_source", source_type="CSV", config_json={"path": str(csv_file)})
    db_session.add(source)
    db_session.commit()

    pipeline = Pipeline(name="cust_idemp_pipe", source_id=source.id, target_table="dim_customers")
    db_session.add(pipeline)
    db_session.commit()

    extractor = CSVExtractor(str(csv_file))
    engine = PipelineEngine(db_session, pipeline, extractor, dataset_name="dim_customers", identifier_column="customer_id")

    # First run
    run1 = engine.run()
    assert run1.status == "COMPLETED"
    assert db_session.query(DimCustomer).count() == 1
    assert db_session.query(DimCustomer).first().name == "Initial Name"

    # Second run (exact duplicate payload)
    run2 = engine.run()
    assert run2.status == "COMPLETED"
    assert db_session.query(DimCustomer).count() == 1  # No duplicate rows created!

    # Third run (updated name)
    df_updated = pd.DataFrame([
        {"customer_id": "C_101", "name": "Updated Name", "email": "initial@example.com", "country": "USA", "signup_date": "2026-01-01T00:00:00Z"},
    ])
    df_updated.to_csv(csv_file, index=False)

    run3 = engine.run()
    assert run3.status == "COMPLETED"
    assert db_session.query(DimCustomer).count() == 1
    assert db_session.query(DimCustomer).first().name == "Updated Name"  # Successfully upserted!

def test_checkpoint_tracking(db_session: Session, temp_dir: Path):
    csv_file = temp_dir / "tx_cursor.csv"
    df = pd.DataFrame([
        {"customer_id": "C_1", "name": "User 1", "email": "u1@example.com", "country": "USA", "signup_date": "2026-01-01T00:00:00Z"},
        {"customer_id": "C_2", "name": "User 2", "email": "u2@example.com", "country": "USA", "signup_date": "2026-01-02T00:00:00Z"},
    ])
    df.to_csv(csv_file, index=False)

    source = DataSource(name="cursor_source", source_type="CSV", config_json={"path": str(csv_file)})
    db_session.add(source)
    db_session.commit()

    pipeline = Pipeline(name="cursor_pipeline", source_id=source.id, target_table="dim_customers")
    db_session.add(pipeline)
    db_session.commit()

    extractor = CSVExtractor(str(csv_file), cursor_column="signup_date")
    engine = PipelineEngine(db_session, pipeline, extractor, dataset_name="dim_customers", cursor_key="signup_date_cursor")

    run1 = engine.run()
    assert run1.status == "COMPLETED"

    cp = db_session.query(PipelineCheckpoint).filter(
        PipelineCheckpoint.pipeline_id == pipeline.id,
        PipelineCheckpoint.checkpoint_key == "signup_date_cursor"
    ).first()

    assert cp is not None
    assert cp.checkpoint_value == "2026-01-02T00:00:00Z"
