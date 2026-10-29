#!/usr/bin/env python3
"""
Seed Demo Environment for SignalForge.
Initializes default Data Sources, Pipelines, Quality Rules, Schema Baselines, and runs initial sample ETL.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from signalforge.config import settings
from signalforge.db.connection import get_db_session, init_db
from signalforge.db.models import DataSource, Pipeline, DataQualityRule, SchemaVersion
from signalforge.engine.extractors import CSVExtractor, JSONExtractor
from signalforge.engine.pipeline import PipelineEngine
from signalforge.quality.rules import QualityRule, RuleSeverity, RuleType
from signalforge.schema.registry import SchemaRegistry
from scripts.generate_synthetic_data import main as generate_data

def seed_environment(run_initial_etl: bool = True):
    print("1. Initializing database schema...")
    init_db()

    print("2. Generating synthetic data...")
    generate_data()

    with get_db_session() as db:
        print("3. Registering Data Sources...")
        # A. CSV Source for Customers
        src_cust = db.query(DataSource).filter(DataSource.name == "customers_csv_source").first()
        if not src_cust:
            src_cust = DataSource(
                name="customers_csv_source",
                source_type="CSV",
                config_json={"path": str(settings.data_dir / "customers.csv"), "identifier_column": "customer_id"}
            )
            db.add(src_cust)
            db.flush()

        # B. JSON Source for Transactions
        src_tx = db.query(DataSource).filter(DataSource.name == "transactions_json_source").first()
        if not src_tx:
            src_tx = DataSource(
                name="transactions_json_source",
                source_type="JSON",
                config_json={"path": str(settings.data_dir / "transactions.json"), "identifier_column": "transaction_id"}
            )
            db.add(src_tx)
            db.flush()

        # C. Event Stream Source
        src_stream = db.query(DataSource).filter(DataSource.name == "events_stream_source").first()
        if not src_stream:
            src_stream = DataSource(
                name="events_stream_source",
                source_type="STREAM",
                config_json={"path": str(settings.data_dir / "events_stream.jsonl")}
            )
            db.add(src_stream)
            db.flush()

        print("4. Registering Pipelines...")
        pipe_cust = db.query(Pipeline).filter(Pipeline.name == "customer_dimension_pipeline").first()
        if not pipe_cust:
            pipe_cust = Pipeline(
                name="customer_dimension_pipeline",
                description="Ingests customer master dataset with validation and SCD upsert into dim_customers.",
                source_id=src_cust.id,
                target_table="dim_customers",
                schedule="0 2 * * *",
                batch_fail_policy="REJECT_AND_CONTINUE"
            )
            db.add(pipe_cust)
            db.flush()

        pipe_tx = db.query(Pipeline).filter(Pipeline.name == "transaction_facts_pipeline").first()
        if not pipe_tx:
            pipe_tx = Pipeline(
                name="transaction_facts_pipeline",
                description="Ingests transactional ledger records, verifies referential integrity, and writes fact_transactions.",
                source_id=src_tx.id,
                target_table="fact_transactions",
                schedule="*/30 * * * *",
                batch_fail_policy="REJECT_AND_CONTINUE"
            )
            db.add(pipe_tx)
            db.flush()

        print("5. Registering Data Quality Rules...")
        default_rules = [
            # Customer Rules
            ("dim_customers", "not_null_customer_id", "NOT_NULL", {"column": "customer_id"}, "BATCH_FAIL"),
            ("dim_customers", "unique_customer_id", "UNIQUE", {"column": "customer_id"}, "BATCH_FAIL"),
            ("dim_customers", "not_null_email", "NOT_NULL", {"column": "email"}, "RECORD_REJECT"),
            # Transaction Rules
            ("fact_transactions", "not_null_tx_id", "NOT_NULL", {"column": "transaction_id"}, "BATCH_FAIL"),
            ("fact_transactions", "unique_tx_id", "UNIQUE", {"column": "transaction_id"}, "RECORD_REJECT"),
            ("fact_transactions", "non_negative_amount", "NON_NEGATIVE", {"column": "amount"}, "RECORD_REJECT"),
            ("fact_transactions", "valid_status_whitelist", "CATEGORY_WHITELIST", {"column": "status", "allowed_values": ["COMPLETED", "PENDING", "FAILED", "CANCELLED"]}, "RECORD_REJECT"),
            ("fact_transactions", "referential_customer_id", "REFERENTIAL_INTEGRITY", {"column": "customer_id", "reference_dataset": "dim_customers", "reference_column": "customer_id"}, "RECORD_REJECT"),
            ("fact_transactions", "valid_tx_timestamp", "VALID_TIMESTAMP", {"column": "transaction_timestamp"}, "RECORD_REJECT"),
            ("fact_transactions", "freshness_tx", "DATA_FRESHNESS", {"column": "transaction_timestamp", "max_age_hours": 720}, "RECORD_REJECT"),
        ]

        for dset, rname, rtype, params, sev in default_rules:
            existing_rule = db.query(DataQualityRule).filter(
                DataQualityRule.dataset_name == dset,
                DataQualityRule.rule_name == rname
            ).first()
            if not existing_rule:
                db.add(DataQualityRule(
                    dataset_name=dset,
                    rule_name=rname,
                    rule_type=rtype,
                    params_json=params,
                    severity=sev
                ))

        print("6. Registering Baseline Schemas...")
        reg = SchemaRegistry(db)
        if not reg.get_active_schema("dim_customers"):
            reg.register_version("dim_customers", {
                "customer_id": {"name": "customer_id", "data_type": "string", "nullable": False, "required": True},
                "name": {"name": "name", "data_type": "string", "nullable": False, "required": True},
                "email": {"name": "email", "data_type": "string", "nullable": False, "required": True},
                "country": {"name": "country", "data_type": "string", "nullable": False, "required": False},
                "signup_date": {"name": "signup_date", "data_type": "datetime", "nullable": False, "required": False}
            })

        if not reg.get_active_schema("fact_transactions"):
            reg.register_version("fact_transactions", {
                "transaction_id": {"name": "transaction_id", "data_type": "string", "nullable": False, "required": True},
                "customer_id": {"name": "customer_id", "data_type": "string", "nullable": False, "required": True},
                "amount": {"name": "amount", "data_type": "float", "nullable": False, "required": True},
                "currency": {"name": "currency", "data_type": "string", "nullable": False, "required": False},
                "status": {"name": "status", "data_type": "string", "nullable": False, "required": True},
                "transaction_timestamp": {"name": "transaction_timestamp", "data_type": "datetime", "nullable": False, "required": True},
                "payment_method": {"name": "payment_method", "data_type": "string", "nullable": False, "required": False}
            })

        print("Seed metadata committed successfully.")

    if run_initial_etl:
        print("7. Running Initial Customer Pipeline Run...")
        with get_db_session() as db:
            p_cust = db.query(Pipeline).filter(Pipeline.name == "customer_dimension_pipeline").first()
            cust_extractor = CSVExtractor(str(settings.data_dir / "customers.csv"))
            cust_rules = [
                QualityRule(r.rule_name, RuleType(r.rule_type), r.dataset_name, r.params_json, RuleSeverity(r.severity))
                for r in db.query(DataQualityRule).filter(DataQualityRule.dataset_name == "dim_customers").all()
            ]
            eng_cust = PipelineEngine(db, p_cust, cust_extractor, quality_rules=cust_rules, dataset_name="dim_customers", identifier_column="customer_id")
            run_c = eng_cust.run(trigger_type="SCHEDULED")
            print(f"Customer Pipeline Finished: Status={run_c.status}, Loaded={run_c.records_loaded}")

        print("8. Running Initial Transactions Pipeline Run...")
        with get_db_session() as db:
            p_tx = db.query(Pipeline).filter(Pipeline.name == "transaction_facts_pipeline").first()
            tx_extractor = JSONExtractor(str(settings.data_dir / "transactions.json"))
            tx_rules = [
                QualityRule(r.rule_name, RuleType(r.rule_type), r.dataset_name, r.params_json, RuleSeverity(r.severity))
                for r in db.query(DataQualityRule).filter(DataQualityRule.dataset_name == "fact_transactions").all()
            ]
            eng_tx = PipelineEngine(db, p_tx, tx_extractor, quality_rules=tx_rules, dataset_name="fact_transactions", identifier_column="transaction_id")
            run_t = eng_tx.run(trigger_type="SCHEDULED")
            print(f"Transactions Pipeline Finished: Status={run_t.status}, Loaded={run_t.records_loaded}, Rejected={run_t.records_rejected}")

    print("\nSignalForge environment successfully initialized and seeded!")

if __name__ == "__main__":
    seed_environment()
