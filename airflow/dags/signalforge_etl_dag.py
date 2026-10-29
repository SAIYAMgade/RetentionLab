"""
SignalForge Orchestration DAG: Scheduled ETL with End-to-End Reliability.
Orchestrates customer dimensions and transaction facts pipelines with retries,
Airflow run_id linkage, and reconciliation validation.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "data_platform",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(seconds=15),
}

def check_environment():
    """Validates DB connectivity and required data directories."""
    import sys
    from pathlib import Path
    sys.path.insert(0, "/opt/signalforge" if Path("/opt/signalforge").exists() else str(Path(__file__).resolve().parent.parent.parent))

    from signalforge.db.connection import get_db_session
    from signalforge.db.models import Pipeline
    with get_db_session() as db:
        pipeline_count = db.query(Pipeline).count()
        print(f"Environment check passed. Registered pipelines: {pipeline_count}")

def run_customers_pipeline(**context):
    """Executes customer dimension pipeline and links airflow_run_id."""
    import sys
    from pathlib import Path
    sys.path.insert(0, "/opt/signalforge" if Path("/opt/signalforge").exists() else str(Path(__file__).resolve().parent.parent.parent))

    from signalforge.config import settings
    from signalforge.db.connection import get_db_session
    from signalforge.db.models import Pipeline, DataQualityRule
    from signalforge.engine.extractors import CSVExtractor
    from signalforge.engine.pipeline import PipelineEngine
    from signalforge.quality.rules import QualityRule, RuleSeverity, RuleType

    run_id = context.get("run_id", "manual_airflow_run")

    with get_db_session() as db:
        pipe = db.query(Pipeline).filter(Pipeline.name == "customer_dimension_pipeline").first()
        if not pipe:
            raise ValueError("customer_dimension_pipeline not found in database.")

        extractor = CSVExtractor(str(settings.data_dir / "customers.csv"))
        rules = [
            QualityRule(r.rule_name, RuleType(r.rule_type), r.dataset_name, r.params_json, RuleSeverity(r.severity))
            for r in db.query(DataQualityRule).filter(DataQualityRule.dataset_name == "dim_customers").all()
        ]

        engine = PipelineEngine(
            db=db,
            pipeline=pipe,
            extractor=extractor,
            quality_rules=rules,
            dataset_name="dim_customers",
            identifier_column="customer_id"
        )

        run = engine.run(trigger_type="SCHEDULED", airflow_run_id=run_id)
        if run.status != "COMPLETED":
            raise RuntimeError(f"Customers pipeline run {run.id} failed: {run.error_message}")
        print(f"Customer dimension pipeline completed successfully: {run.records_loaded} records loaded.")

def run_transactions_pipeline(**context):
    """Executes transaction facts pipeline with referential integrity verification."""
    import sys
    from pathlib import Path
    sys.path.insert(0, "/opt/signalforge" if Path("/opt/signalforge").exists() else str(Path(__file__).resolve().parent.parent.parent))

    from signalforge.config import settings
    from signalforge.db.connection import get_db_session
    from signalforge.db.models import Pipeline, DataQualityRule
    from signalforge.engine.extractors import JSONExtractor
    from signalforge.engine.pipeline import PipelineEngine
    from signalforge.quality.rules import QualityRule, RuleSeverity, RuleType

    run_id = context.get("run_id", "manual_airflow_run")

    with get_db_session() as db:
        pipe = db.query(Pipeline).filter(Pipeline.name == "transaction_facts_pipeline").first()
        if not pipe:
            raise ValueError("transaction_facts_pipeline not found in database.")

        extractor = JSONExtractor(str(settings.data_dir / "transactions.json"))
        rules = [
            QualityRule(r.rule_name, RuleType(r.rule_type), r.dataset_name, r.params_json, RuleSeverity(r.severity))
            for r in db.query(DataQualityRule).filter(DataQualityRule.dataset_name == "fact_transactions").all()
        ]

        engine = PipelineEngine(
            db=db,
            pipeline=pipe,
            extractor=extractor,
            quality_rules=rules,
            dataset_name="fact_transactions",
            identifier_column="transaction_id"
        )

        run = engine.run(trigger_type="SCHEDULED", airflow_run_id=run_id)
        if run.status != "COMPLETED":
            raise RuntimeError(f"Transactions pipeline run {run.id} failed: {run.error_message}")
        print(f"Transaction facts pipeline completed successfully: {run.records_loaded} records loaded, {run.records_rejected} rejected.")

def reconcile_and_verify():
    """Post-pipeline business reconciliation check."""
    import sys
    from pathlib import Path
    sys.path.insert(0, "/opt/signalforge" if Path("/opt/signalforge").exists() else str(Path(__file__).resolve().parent.parent.parent))

    from signalforge.db.connection import get_db_session
    from signalforge.db.models import DimCustomer, FactTransaction
    with get_db_session() as db:
        cust_count = db.query(DimCustomer).count()
        tx_count = db.query(FactTransaction).count()
        print(f"Reconciliation verified. Total Customers: {cust_count}, Total Transactions: {tx_count}")

with DAG(
    dag_id="signalforge_daily_etl",
    default_args=default_args,
    description="SignalForge production ETL workflow for customers & transactions",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["signalforge", "etl", "production"],
) as dag:

    t1_check_env = PythonOperator(
        task_id="check_environment",
        python_callable=check_environment,
    )

    t2_customers = PythonOperator(
        task_id="run_customers_etl",
        python_callable=run_customers_pipeline,
    )

    t3_transactions = PythonOperator(
        task_id="run_transactions_etl",
        python_callable=run_transactions_pipeline,
    )

    t4_reconciliation = PythonOperator(
        task_id="reconcile_and_verify",
        python_callable=reconcile_and_verify,
    )

    t1_check_env >> t2_customers >> t3_transactions >> t4_reconciliation
