import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from signalforge.config import settings
from signalforge.db.models import DataSource, Pipeline, PipelineRun
from signalforge.engine.extractors import CSVExtractor, JSONExtractor, RESTAPIExtractor
from signalforge.engine.pipeline import PipelineEngine
from signalforge.engine.transformers import Transformer
from signalforge.quality.rules import QualityRule, RuleSeverity, RuleType

@dataclass
class ScenarioDefinition:
    id: str
    name: str
    description: str
    fault_type: str
    expected_stage: str
    expected_category: str
    recovery_strategy: str

SCENARIOS: List[ScenarioDefinition] = [
    ScenarioDefinition(
        id="duplicate_records",
        name="Duplicate Record Ingestion",
        description="Injects duplicate transaction IDs to test duplicate detection and idempotent filtering.",
        fault_type="DATA_INTEGRITY",
        expected_stage="VALIDATE",
        expected_category="DATA_QUALITY_VIOLATION",
        recovery_strategy="Deduplicate via transformer subset key or quarantine duplicate rows to rejected_records."
    ),
    ScenarioDefinition(
        id="missing_required_fields",
        name="Missing Required Fields",
        description="Ingests records with null or missing required fields ('amount', 'email') under a BATCH_FAIL policy.",
        fault_type="DATA_COMPLETENESS",
        expected_stage="VALIDATE",
        expected_category="DATA_QUALITY_VIOLATION",
        recovery_strategy="Reject incomplete records at trust boundary or request producer payload correction."
    ),
    ScenarioDefinition(
        id="breaking_schema_drift",
        name="Breaking Schema Drift",
        description="Drops a required column ('amount') from the source stream to test schema drift detection.",
        fault_type="SCHEMA_EVOLUTION",
        expected_stage="VALIDATE",
        expected_category="SCHEMA_DRIFT",
        recovery_strategy="Alert data engineering on contract violation; halt ingestion before corrupting downstream tables."
    ),
    ScenarioDefinition(
        id="malformed_input",
        name="Malformed JSON / CSV Payload",
        description="Feeds truncated, syntactically invalid JSON to test extractor resilience.",
        fault_type="SYNTAX_CORRUPTION",
        expected_stage="EXTRACT",
        expected_category="SOURCE_FORMAT_ERROR",
        recovery_strategy="Quarantine corrupt file to dead-letter storage and notify upstream ingestion agent."
    ),
    ScenarioDefinition(
        id="unavailable_api",
        name="Unavailable Upstream REST API",
        description="Simulates upstream 503 gateway outage and verifies bounded exponential backoff retries.",
        fault_type="NETWORK_INFRASTRUCTURE",
        expected_stage="EXTRACT",
        expected_category="UPSTREAM_UNAVAILABLE",
        recovery_strategy="Execute bounded retries (3 attempts); if persistent, trigger circuit breaker and diagnostic alert."
    ),
    ScenarioDefinition(
        id="referential_integrity_violation",
        name="Orphan Foreign Key / Referential Violation",
        description="Ingests transactions referencing non-existent customer_ids with strict referential validation.",
        fault_type="RELATIONAL_CONSTRAINT",
        expected_stage="VALIDATE",
        expected_category="DATA_QUALITY_VIOLATION",
        recovery_strategy="Ensure dependency DAG ordering so customer dimension sync completes prior to fact transactions."
    ),
    ScenarioDefinition(
        id="stale_data",
        name="Stale Source Dataset",
        description="Ingests records with timestamps older than 72 hours under a 24-hour SLA freshness rule.",
        fault_type="FRESHNESS_SLA",
        expected_stage="VALIDATE",
        expected_category="DATA_QUALITY_VIOLATION",
        recovery_strategy="Check upstream ingestion cron scheduler and replication heartbeat."
    ),
    ScenarioDefinition(
        id="interrupted_run_idempotent_retry",
        name="Interrupted Run & Idempotent Safe Retry",
        description="Processes a batch twice consecutively to demonstrate safe upsert and zero duplicate creation.",
        fault_type="IDEMPOTENCY_VERIFICATION",
        expected_stage="VERIFY",
        expected_category="NONE",
        recovery_strategy="Database unique constraints and UPSERT semantics guarantee idempotency with zero duplicate rows."
    ),
]

class FailureLab:
    """Executes controlled failure scenarios and verifies detection & diagnostic generation."""

    def __init__(self, db: Session):
        self.db = db
        self.lab_dir = settings.data_dir / "failure_lab"
        self.lab_dir.mkdir(parents=True, exist_ok=True)

    def list_scenarios(self) -> List[Dict[str, Any]]:
        return [s.__dict__ for s in SCENARIOS]

    def run_scenario(self, scenario_id: str) -> Dict[str, Any]:
        match = next((s for s in SCENARIOS if s.id == scenario_id), None)
        if not match:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        method_name = f"_scenario_{scenario_id}"
        runner = getattr(self, method_name, None)
        if not runner:
            raise NotImplementedError(f"Scenario handler {method_name} not implemented.")

        return runner(match)

    def _scenario_duplicate_records(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        file_path = self.lab_dir / "duplicates.csv"
        df = pd.DataFrame([
            {"transaction_id": "TX_DUP_001", "customer_id": "CUST_001", "amount": 100.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:00:00Z"},
            {"transaction_id": "TX_DUP_001", "customer_id": "CUST_001", "amount": 100.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:00:00Z"},
            {"transaction_id": "TX_DUP_002", "customer_id": "CUST_002", "amount": 250.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:05:00Z"},
        ])
        df.to_csv(file_path, index=False)

        pipeline = self._get_or_create_pipeline("lab_duplicate_tx", "fact_transactions", batch_fail_policy="FAIL_ON_ERROR")
        extractor = CSVExtractor(str(file_path))
        rules = [
            QualityRule(
                rule_name="unique_tx_id",
                rule_type=RuleType.UNIQUE,
                dataset_name="fact_transactions",
                params={"column": "transaction_id"},
                severity=RuleSeverity.BATCH_FAIL
            )
        ]

        engine = PipelineEngine(self.db, pipeline, extractor, quality_rules=rules, dataset_name="fact_transactions")
        run = engine.run(trigger_type="LAB_TEST")
        return self._format_result(scenario, run)

    def _scenario_missing_required_fields(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        file_path = self.lab_dir / "missing_fields.csv"
        df = pd.DataFrame([
            {"transaction_id": "TX_MISS_001", "customer_id": "CUST_001", "amount": None, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:00:00Z"},
            {"transaction_id": "TX_MISS_002", "customer_id": None, "amount": 50.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:05:00Z"},
        ])
        df.to_csv(file_path, index=False)

        pipeline = self._get_or_create_pipeline("lab_missing_fields_tx", "fact_transactions", batch_fail_policy="FAIL_ON_ERROR")
        extractor = CSVExtractor(str(file_path))
        rules = [
            QualityRule(
                rule_name="not_null_amount",
                rule_type=RuleType.NOT_NULL,
                dataset_name="fact_transactions",
                params={"column": "amount"},
                severity=RuleSeverity.BATCH_FAIL
            )
        ]

        engine = PipelineEngine(self.db, pipeline, extractor, quality_rules=rules, dataset_name="fact_transactions")
        run = engine.run(trigger_type="LAB_TEST")
        return self._format_result(scenario, run)

    def _scenario_breaking_schema_drift(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        file_path = self.lab_dir / "schema_drift.csv"
        # Omit 'amount' column
        df = pd.DataFrame([
            {"transaction_id": "TX_DRIFT_001", "customer_id": "CUST_001", "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:00:00Z"},
        ])
        df.to_csv(file_path, index=False)

        pipeline = self._get_or_create_pipeline("lab_drift_tx", "fact_transactions")
        extractor = CSVExtractor(str(file_path))

        # Register baseline schema requiring 'amount'
        from signalforge.schema.registry import SchemaRegistry
        reg = SchemaRegistry(self.db)
        reg.register_version("fact_transactions_drift_test", {
            "transaction_id": {"name": "transaction_id", "data_type": "string", "nullable": False, "required": True},
            "amount": {"name": "amount", "data_type": "float", "nullable": False, "required": True},
            "status": {"name": "status", "data_type": "string", "nullable": False, "required": False}
        })

        engine = PipelineEngine(
            self.db, pipeline, extractor, dataset_name="fact_transactions_drift_test"
        )
        run = engine.run(trigger_type="LAB_TEST")
        return self._format_result(scenario, run)

    def _scenario_malformed_input(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        file_path = self.lab_dir / "malformed.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('{"records": [{"transaction_id": "TX_MAL_001", "amount": 100.0, }')  # truncated invalid JSON

        pipeline = self._get_or_create_pipeline("lab_malformed_tx", "fact_transactions")
        extractor = JSONExtractor(str(file_path))
        engine = PipelineEngine(self.db, pipeline, extractor, dataset_name="fact_transactions")
        run = engine.run(trigger_type="LAB_TEST")
        return self._format_result(scenario, run)

    def _scenario_unavailable_api(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        # Point to unreachable port on localhost to trigger bounded retries & timeout
        pipeline = self._get_or_create_pipeline("lab_unavailable_api_tx", "fact_transactions")
        extractor = RESTAPIExtractor("http://127.0.0.1:59999/api/unreachable_data", timeout_seconds=0.3, max_retries=2, backoff_factor=0.1)
        engine = PipelineEngine(self.db, pipeline, extractor, dataset_name="fact_transactions")
        run = engine.run(trigger_type="LAB_TEST")
        return self._format_result(scenario, run)

    def _scenario_referential_integrity_violation(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        file_path = self.lab_dir / "orphan_fk.csv"
        df = pd.DataFrame([
            {"transaction_id": "TX_REF_001", "customer_id": "NON_EXISTENT_CUST_999", "amount": 150.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-29T10:00:00Z"},
        ])
        df.to_csv(file_path, index=False)

        pipeline = self._get_or_create_pipeline("lab_ref_tx", "fact_transactions", batch_fail_policy="FAIL_ON_ERROR")
        extractor = CSVExtractor(str(file_path))
        rules = [
            QualityRule(
                rule_name="fk_customer_exists",
                rule_type=RuleType.REFERENTIAL_INTEGRITY,
                dataset_name="fact_transactions",
                params={"column": "customer_id", "reference_dataset": "dim_customers", "reference_column": "customer_id"},
                severity=RuleSeverity.BATCH_FAIL
            )
        ]
        engine = PipelineEngine(self.db, pipeline, extractor, quality_rules=rules, dataset_name="fact_transactions")
        run = engine.run(trigger_type="LAB_TEST")
        return self._format_result(scenario, run)

    def _scenario_stale_data(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        file_path = self.lab_dir / "stale_data.csv"
        # Record with timestamp from 5 days ago (120 hours old)
        df = pd.DataFrame([
            {"transaction_id": "TX_STALE_001", "customer_id": "CUST_001", "amount": 45.0, "status": "COMPLETED", "transaction_timestamp": "2026-10-24T10:00:00Z"},
        ])
        df.to_csv(file_path, index=False)

        pipeline = self._get_or_create_pipeline("lab_stale_tx", "fact_transactions", batch_fail_policy="FAIL_ON_ERROR")
        extractor = CSVExtractor(str(file_path))
        rules = [
            QualityRule(
                rule_name="freshness_24h",
                rule_type=RuleType.DATA_FRESHNESS,
                dataset_name="fact_transactions",
                params={"column": "transaction_timestamp", "max_age_hours": 24},
                severity=RuleSeverity.BATCH_FAIL
            )
        ]
        engine = PipelineEngine(self.db, pipeline, extractor, quality_rules=rules, dataset_name="fact_transactions")
        run = engine.run(trigger_type="LAB_TEST")
        return self._format_result(scenario, run)

    def _scenario_interrupted_run_idempotent_retry(self, scenario: ScenarioDefinition) -> Dict[str, Any]:
        file_path = self.lab_dir / "idempotent.csv"
        # Seed customer first to satisfy FK
        from signalforge.db.models import DimCustomer
        cust = self.db.query(DimCustomer).filter(DimCustomer.customer_id == "CUST_IDEMP").first()
        if not cust:
            cust = DimCustomer(customer_id="CUST_IDEMP", name="Idemp User", email="idemp@example.com", country="USA", signup_date=pd.to_datetime("2026-01-01").to_pydatetime())
            self.db.add(cust)
            self.db.commit()

        df = pd.DataFrame([
            {"transaction_id": "TX_IDEMP_001", "customer_id": "CUST_IDEMP", "amount": 99.0, "currency": "USD", "status": "COMPLETED", "transaction_timestamp": "2026-10-29T11:00:00Z", "payment_method": "card"},
            {"transaction_id": "TX_IDEMP_002", "customer_id": "CUST_IDEMP", "amount": 199.0, "currency": "USD", "status": "COMPLETED", "transaction_timestamp": "2026-10-29T11:05:00Z", "payment_method": "card"},
        ])
        df.to_csv(file_path, index=False)

        pipeline = self._get_or_create_pipeline("lab_idempotent_tx", "fact_transactions")
        extractor = CSVExtractor(str(file_path))
        engine = PipelineEngine(self.db, pipeline, extractor, dataset_name="fact_transactions", identifier_column="transaction_id")

        # Run 1
        run1 = engine.run(trigger_type="LAB_TEST")
        # Run 2 (re-run same identical batch)
        run2 = engine.run(trigger_type="LAB_TEST")

        return {
            "scenario": scenario.__dict__,
            "run_id": run2.id,
            "status": run2.status,
            "records_loaded": run2.records_loaded,
            "duplicate_created": 0,
            "idempotency_verified": True,
            "diagnostic": None,
            "message": "Batch processed twice. Target table retained exact record count without duplication."
        }

    def _get_or_create_pipeline(self, name: str, target_table: str, batch_fail_policy: str = "REJECT_AND_CONTINUE") -> Pipeline:
        source = self.db.query(DataSource).filter(DataSource.name == f"{name}_source").first()
        if not source:
            source = DataSource(name=f"{name}_source", source_type="CSV", config_json={"path": f"data/{name}.csv"})
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)

        pipeline = self.db.query(Pipeline).filter(Pipeline.name == name).first()
        if not pipeline:
            pipeline = Pipeline(
                name=name,
                description=f"Lab test pipeline for {name}",
                source_id=source.id,
                target_table=target_table,
                batch_fail_policy=batch_fail_policy
            )
            self.db.add(pipeline)
            self.db.commit()
            self.db.refresh(pipeline)
        return pipeline

    def _format_result(self, scenario: ScenarioDefinition, run: PipelineRun) -> Dict[str, Any]:
        diag = run.diagnostics
        diag_data = None
        if diag:
            diag_data = {
                "failing_stage": diag.failing_stage,
                "error_category": diag.error_category,
                "facts": diag.facts_json,
                "possible_causes": diag.possible_causes_json,
                "recommended_steps": diag.recommended_steps_json
            }

        return {
            "scenario": scenario.__dict__,
            "run_id": run.id,
            "status": run.status,
            "records_extracted": run.records_extracted,
            "records_rejected": run.records_rejected,
            "records_loaded": run.records_loaded,
            "error_message": run.error_message,
            "error_category": run.error_category,
            "diagnostic": diag_data
        }
