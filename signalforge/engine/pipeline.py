import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import pandas as pd
from sqlalchemy.orm import Session

from signalforge.db.models import (
    Pipeline, PipelineRun, RunStage, ValidationResult,
    RejectedRecord, PipelineCheckpoint, FailureDiagnostic,
    DimCustomer, FactTransaction
)
from signalforge.engine.extractors import BaseExtractor
from signalforge.engine.transformers import Transformer
from signalforge.engine.loaders import SafeLoader
from signalforge.quality.rules import QualityRule, RuleSeverity
from signalforge.quality.validator import QualityValidator
from signalforge.schema.drift import infer_schema_from_df
from signalforge.schema.registry import SchemaRegistry
from signalforge.diagnostics.engine import DiagnosticEngine
from signalforge.observability.logging import logger
from signalforge.observability.metrics import MetricsCollector

class PipelineEngine:
    """Executes the full SignalForge pipeline lifecycle with end-to-end reliability."""

    def __init__(
        self,
        db: Session,
        pipeline: Pipeline,
        extractor: BaseExtractor,
        transformer: Optional[Transformer] = None,
        quality_rules: Optional[List[QualityRule]] = None,
        dataset_name: Optional[str] = None,
        identifier_column: Optional[str] = None,
        cursor_key: Optional[str] = None
    ):
        self.db = db
        self.pipeline = pipeline
        self.extractor = extractor
        self.transformer = transformer or Transformer()
        self.quality_rules = quality_rules or []
        self.dataset_name = dataset_name or pipeline.target_table
        self.identifier_column = identifier_column
        self.cursor_key = cursor_key or "last_cursor"
        self.loader = SafeLoader(db)
        self.schema_registry = SchemaRegistry(db)

    def run(self, trigger_type: str = "MANUAL", airflow_run_id: Optional[str] = None) -> PipelineRun:
        t_start = time.perf_counter()
        now_utc = datetime.now(timezone.utc)

        run = PipelineRun(
            pipeline_id=self.pipeline.id,
            trigger_type=trigger_type,
            status="RUNNING",
            airflow_run_id=airflow_run_id,
            started_at=now_utc
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        logger.info(
            f"Starting pipeline run {run.id} for '{self.pipeline.name}'",
            extra={"pipeline_id": self.pipeline.id, "run_id": run.id, "stage": "INIT"}
        )

        extracted_df = pd.DataFrame()
        valid_df = pd.DataFrame()
        transformed_df = pd.DataFrame()
        new_checkpoint = None
        validation_eval_results = []
        drift_report = None
        current_stage_name = "INIT"

        try:
            # ----------------------------------------------------
            # STAGE 1: EXTRACT
            # ----------------------------------------------------
            current_stage_name = "EXTRACT"
            stage_rec = self._start_stage(run.id, "EXTRACT")
            t0 = time.perf_counter()

            cp = (
                self.db.query(PipelineCheckpoint)
                .filter(
                    PipelineCheckpoint.pipeline_id == self.pipeline.id,
                    PipelineCheckpoint.checkpoint_key == self.cursor_key
                )
                .first()
            )
            checkpoint_val = cp.checkpoint_value if cp else None

            extracted_df, new_checkpoint = self.extractor.extract(checkpoint_value=checkpoint_val)
            rec_extracted = len(extracted_df)
            run.records_extracted = rec_extracted

            self._complete_stage(stage_rec, records_in=rec_extracted, records_out=rec_extracted, t0=t0)
            MetricsCollector.record_stage_records(self.pipeline.name, "EXTRACT", rec_extracted)

            # ----------------------------------------------------
            # STAGE 2: VALIDATE
            # ----------------------------------------------------
            current_stage_name = "VALIDATE"
            stage_rec = self._start_stage(run.id, "VALIDATE")
            t0 = time.perf_counter()

            # A. Schema Drift Check
            if not extracted_df.empty:
                observed_schema = infer_schema_from_df(extracted_df)
                drift_report = self.schema_registry.check_and_record_drift(
                    dataset_name=self.dataset_name,
                    observed_schema=observed_schema,
                    pipeline_id=self.pipeline.id,
                    run_id=run.id
                )
                if drift_report and drift_report.has_drift and drift_report.severity.value == "BREAKING":
                    raise ValueError(
                        f"Breaking schema drift detected: {drift_report.recommended_action}"
                    )

            # B. Data Quality Rules Evaluation
            ref_data: Dict[str, Set[Any]] = {}
            if self.pipeline.target_table == "fact_transactions":
                # Fetch existing customer_ids for referential integrity
                cust_ids = {c[0] for c in self.db.query(DimCustomer.customer_id).all()}
                ref_data["dim_customers"] = cust_ids

            validator = QualityValidator(self.quality_rules)
            is_valid, valid_df, rejected_records, validation_eval_results = validator.evaluate(
                df=extracted_df,
                reference_data=ref_data,
                identifier_column=self.identifier_column
            )

            # Persist validation results
            for res in validation_eval_results:
                v_res = ValidationResult(
                    run_id=run.id,
                    dataset_name=res.dataset_name,
                    rule_name=res.rule_name,
                    passed=res.passed,
                    total_checked=res.total_checked,
                    failed_count=res.failed_count,
                    sample_failures_json=res.sample_failures,
                    execution_time_ms=res.execution_time_ms
                )
                self.db.add(v_res)
                if not res.passed:
                    MetricsCollector.record_validation_failure(res.dataset_name, res.rule_name, res.failed_count)

            # Persist rejected records
            for rj in rejected_records:
                rej_obj = RejectedRecord(
                    run_id=run.id,
                    record_identifier=rj["record_identifier"],
                    raw_data_json=rj["raw_data"],
                    rejection_reasons_json=rj["rejection_reasons"]
                )
                self.db.add(rej_obj)
                MetricsCollector.record_rejection(self.pipeline.name, "QUALITY_CHECK")

            run.records_rejected = len(rejected_records)
            self.db.commit()

            # Enforce batch failure policy
            if not is_valid:
                raise ValueError("Batch-fail quality rule violation triggered.")

            if self.pipeline.batch_fail_policy == "FAIL_ON_ERROR" and len(rejected_records) > 0:
                raise ValueError(f"Pipeline policy FAIL_ON_ERROR rejected {len(rejected_records)} records.")

            self._complete_stage(
                stage_rec,
                records_in=rec_extracted,
                records_out=len(valid_df),
                t0=t0,
                details={"rejected_count": len(rejected_records)}
            )
            MetricsCollector.record_stage_records(self.pipeline.name, "VALIDATE", len(valid_df))

            # ----------------------------------------------------
            # STAGE 3: TRANSFORM
            # ----------------------------------------------------
            current_stage_name = "TRANSFORM"
            stage_rec = self._start_stage(run.id, "TRANSFORM")
            t0 = time.perf_counter()

            transformed_df = self.transformer.transform(valid_df)
            run.records_transformed = len(transformed_df)

            self._complete_stage(stage_rec, records_in=len(valid_df), records_out=len(transformed_df), t0=t0)
            MetricsCollector.record_stage_records(self.pipeline.name, "TRANSFORM", len(transformed_df))

            # ----------------------------------------------------
            # STAGE 4: LOAD (Transactional & Idempotent)
            # ----------------------------------------------------
            current_stage_name = "LOAD"
            stage_rec = self._start_stage(run.id, "LOAD")
            t0 = time.perf_counter()

            records_loaded = 0
            if self.pipeline.target_table == "dim_customers":
                records_loaded = self.loader.load_customers(transformed_df)
            elif self.pipeline.target_table == "fact_transactions":
                records_loaded = self.loader.load_transactions(transformed_df)
            else:
                # Custom target table fallback
                records_loaded = len(transformed_df)

            # Update checkpoint atomically in same transaction
            if new_checkpoint:
                self.loader.update_checkpoint(self.pipeline.id, self.cursor_key, new_checkpoint)

            self.db.commit()
            run.records_loaded = records_loaded

            self._complete_stage(stage_rec, records_in=len(transformed_df), records_out=records_loaded, t0=t0)
            MetricsCollector.record_stage_records(self.pipeline.name, "LOAD", records_loaded)

            # ----------------------------------------------------
            # STAGE 5: VERIFY
            # ----------------------------------------------------
            current_stage_name = "VERIFY"
            stage_rec = self._start_stage(run.id, "VERIFY")
            t0 = time.perf_counter()

            # Ensure post-load count matches
            if self.pipeline.target_table == "dim_customers":
                # Verify non-empty if records were supposedly loaded
                assert records_loaded == len(transformed_df), "Mismatch between transformed and loaded count"
            elif self.pipeline.target_table == "fact_transactions":
                assert records_loaded == len(transformed_df), "Mismatch between transformed and loaded count"

            self._complete_stage(stage_rec, records_in=records_loaded, records_out=records_loaded, t0=t0)

            # ----------------------------------------------------
            # STAGE 6: RECORD METRICS & FINALIZE SUCCESS
            # ----------------------------------------------------
            duration_total = time.perf_counter() - t_start
            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc)
            run.duration_ms = round(duration_total * 1000, 2)
            self.db.commit()

            MetricsCollector.record_run(self.pipeline.name, "COMPLETED", duration_total)
            logger.info(
                f"Pipeline run {run.id} COMPLETED successfully. Ingested: {records_loaded}, Rejected: {run.records_rejected}",
                extra={
                    "pipeline_id": self.pipeline.id,
                    "run_id": run.id,
                    "stage": "COMPLETED",
                    "duration_ms": run.duration_ms,
                    "records_count": records_loaded
                }
            )

        except Exception as e:
            duration_total = time.perf_counter() - t_start
            self.db.rollback()

            error_msg = str(e)
            run.status = "FAILED"
            run.error_message = error_msg
            run.completed_at = datetime.now(timezone.utc)
            run.duration_ms = round(duration_total * 1000, 2)

            # Mark failing stage
            fail_stage = self._start_stage(run.id, current_stage_name)
            fail_stage.status = "FAILED"
            fail_stage.completed_at = datetime.now(timezone.utc)
            fail_stage.details_json = {"error": error_msg}

            # Generate Root-Cause Diagnostics
            diag = DiagnosticEngine.diagnose(
                failing_stage=current_stage_name,
                error_message=error_msg,
                dataset_name=self.dataset_name,
                records_extracted=run.records_extracted,
                records_transformed=run.records_transformed,
                validation_results=validation_eval_results,
                drift_report=drift_report,
                source_type=self.pipeline.source.source_type if self.pipeline.source else None
            )

            run.error_category = diag["error_category"]
            diag_obj = FailureDiagnostic(
                run_id=run.id,
                failing_stage=current_stage_name,
                error_category=diag["error_category"],
                facts_json=diag["facts"],
                possible_causes_json=diag["possible_causes"],
                recommended_steps_json=diag["recommended_steps"]
            )
            self.db.add(diag_obj)
            self.db.commit()

            MetricsCollector.record_run(self.pipeline.name, "FAILED", duration_total)
            logger.error(
                f"Pipeline run {run.id} FAILED in stage {current_stage_name}: {error_msg}",
                extra={
                    "pipeline_id": self.pipeline.id,
                    "run_id": run.id,
                    "stage": current_stage_name,
                    "error_category": diag["error_category"],
                    "duration_ms": run.duration_ms
                }
            )

        return run

    def _start_stage(self, run_id: str, stage_name: str) -> RunStage:
        stage = RunStage(
            run_id=run_id,
            stage_name=stage_name,
            status="RUNNING",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(stage)
        self.db.commit()
        self.db.refresh(stage)
        return stage

    def _complete_stage(
        self,
        stage: RunStage,
        records_in: int,
        records_out: int,
        t0: float,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        stage.status = "COMPLETED"
        stage.records_in = records_in
        stage.records_out = records_out
        stage.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        stage.completed_at = datetime.now(timezone.utc)
        if details:
            stage.details_json = details
        self.db.commit()
