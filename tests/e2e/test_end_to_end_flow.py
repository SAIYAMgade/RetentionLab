from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session
from signalforge.db.models import (
    DataSource, Pipeline, PipelineRun, DimCustomer,
    FactTransaction, RejectedRecord, ValidationResult
)
from signalforge.engine.extractors import CSVExtractor
from signalforge.engine.pipeline import PipelineEngine
from signalforge.quality.rules import QualityRule, RuleSeverity, RuleType

def test_full_pipeline_end_to_end_lifecycle(db_session: Session, temp_dir: Path):
    # -------------------------------------------------------------
    # Step 1: Ingest Customer Dimension
    # -------------------------------------------------------------
    cust_file = temp_dir / "e2e_customers.csv"
    pd.DataFrame([
        {"customer_id": "C_E2E_1", "name": "Alice Corp", "email": "alice@corp.com", "country": "USA", "signup_date": "2026-01-01T00:00:00Z"},
        {"customer_id": "C_E2E_2", "name": "Bob Ltd", "email": "bob@ltd.com", "country": "GBR", "signup_date": "2026-01-02T00:00:00Z"},
    ]).to_csv(cust_file, index=False)

    src_cust = DataSource(name="e2e_cust_src", source_type="CSV", config_json={"path": str(cust_file)})
    db_session.add(src_cust)
    db_session.commit()

    pipe_cust = Pipeline(name="e2e_cust_pipe", source_id=src_cust.id, target_table="dim_customers")
    db_session.add(pipe_cust)
    db_session.commit()

    eng_cust = PipelineEngine(
        db_session, pipe_cust, CSVExtractor(str(cust_file)),
        dataset_name="dim_customers", identifier_column="customer_id"
    )
    run_cust = eng_cust.run()
    assert run_cust.status == "COMPLETED"
    assert run_cust.records_loaded == 2
    assert db_session.query(DimCustomer).count() == 2

    # -------------------------------------------------------------
    # Step 2: Ingest Transactions with Faulty Records (RECORD_REJECT)
    # -------------------------------------------------------------
    tx_file = temp_dir / "e2e_transactions.csv"
    # Row 1: Valid
    # Row 2: Negative amount -> rejected
    # Row 3: Orphan FK -> rejected
    # Row 4: Valid
    pd.DataFrame([
        {"transaction_id": "T_1", "customer_id": "C_E2E_1", "amount": 100.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:00:00Z"},
        {"transaction_id": "T_2", "customer_id": "C_E2E_1", "amount": -50.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:05:00Z"},
        {"transaction_id": "T_3", "customer_id": "C_GHOST", "amount": 25.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:10:00Z"},
        {"transaction_id": "T_4", "customer_id": "C_E2E_2", "amount": 300.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:15:00Z"},
    ]).to_csv(tx_file, index=False)

    src_tx = DataSource(name="e2e_tx_src", source_type="CSV", config_json={"path": str(tx_file)})
    db_session.add(src_tx)
    db_session.commit()

    pipe_tx = Pipeline(
        name="e2e_tx_pipe", source_id=src_tx.id, target_table="fact_transactions",
        batch_fail_policy="REJECT_AND_CONTINUE"
    )
    db_session.add(pipe_tx)
    db_session.commit()

    rules_tx = [
        QualityRule("non_neg", RuleType.NON_NEGATIVE, "fact_transactions", {"column": "amount"}, RuleSeverity.RECORD_REJECT),
        QualityRule("fk_cust", RuleType.REFERENTIAL_INTEGRITY, "fact_transactions", {"column": "customer_id", "reference_dataset": "dim_customers", "reference_column": "customer_id"}, RuleSeverity.RECORD_REJECT),
    ]

    eng_tx = PipelineEngine(
        db_session, pipe_tx, CSVExtractor(str(tx_file)),
        quality_rules=rules_tx, dataset_name="fact_transactions", identifier_column="transaction_id"
    )
    run_tx = eng_tx.run()

    # Verify run completed with 2 loaded and 2 rejected
    assert run_tx.status == "COMPLETED"
    assert run_tx.records_extracted == 4
    assert run_tx.records_loaded == 2
    assert run_tx.records_rejected == 2

    # Verify rejected records stored with diagnostic reasons
    rejections = db_session.query(RejectedRecord).filter(RejectedRecord.run_id == run_tx.id).all()
    assert len(rejections) == 2
    rejected_ids = {r.record_identifier for r in rejections}
    assert "T_2" in rejected_ids
    assert "T_3" in rejected_ids

    # -------------------------------------------------------------
    # Step 3: Idempotent Re-Run (Zero Duplicates)
    # -------------------------------------------------------------
    initial_tx_count = db_session.query(FactTransaction).count()
    assert initial_tx_count == 2

    run_tx_rerun = eng_tx.run()
    assert run_tx_rerun.status == "COMPLETED"
    assert db_session.query(FactTransaction).count() == 2  # Idempotent!

    # -------------------------------------------------------------
    # Step 4: Validate Historical Metrics
    # -------------------------------------------------------------
    all_runs = db_session.query(PipelineRun).all()
    assert len(all_runs) == 3
    assert all(r.status == "COMPLETED" for r in all_runs)
