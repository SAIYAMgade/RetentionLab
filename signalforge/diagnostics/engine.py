from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from signalforge.quality.rules import RuleEvaluationResult, RuleSeverity
from signalforge.schema.drift import DriftReport, DriftSeverity

class DiagnosticEngine:
    """Deterministic rule-based root-cause diagnostic engine."""

    @classmethod
    def diagnose(
        cls,
        failing_stage: str,
        error_message: str,
        dataset_name: str,
        records_extracted: int = 0,
        records_transformed: int = 0,
        validation_results: Optional[List[RuleEvaluationResult]] = None,
        drift_report: Optional[DriftReport] = None,
        source_type: Optional[str] = None
    ) -> Dict[str, Any]:
        facts: List[str] = []
        possible_causes: List[str] = []
        recommended_steps: List[str] = []
        error_category = "UNKNOWN_ERROR"

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Check for schema drift issues
        if drift_report and drift_report.has_drift and drift_report.severity == DriftSeverity.BREAKING:
            error_category = "SCHEMA_DRIFT"
            facts.append(f"Pipeline stage {failing_stage} failed due to breaking schema drift on dataset '{dataset_name}'.")
            if drift_report.missing_required:
                facts.append(f"Missing required baseline columns: {drift_report.missing_required}.")
                possible_causes.append("Upstream data provider modified export schema or dropped required fields without prior notification.")
                recommended_steps.append("Contact upstream producer to restore required fields or update pipeline contract.")
            if drift_report.type_changes:
                facts.append(f"Incompatible type changes detected: {drift_report.type_changes}.")
                possible_causes.append("Source database column alter or serialization format altered.")
                recommended_steps.append("Update pipeline transformer to cast the new type or increment active schema version.")

        # 2. Check for data quality violations
        elif validation_results and any(r.severity == RuleSeverity.BATCH_FAIL and not r.passed for r in validation_results):
            error_category = "DATA_QUALITY_VIOLATION"
            failing_rules = [r for r in validation_results if not r.passed and r.severity == RuleSeverity.BATCH_FAIL]
            facts.append(f"Stage {failing_stage} failed policy check at {now_str}. Records processed before failure: {records_extracted}.")
            for r in failing_rules:
                facts.append(f"Batch-fail quality rule '{r.rule_name}' ({r.rule_type}) failed with {r.failed_count} violations out of {r.total_checked} rows.")
                if r.rule_type == "NOT_NULL":
                    possible_causes.append(f"Upstream pipeline emitted incomplete payloads with null required fields in '{r.rule_name}'.")
                    recommended_steps.append("Investigate upstream ingestion step or modify rule policy to RECORD_REJECT if non-fatal.")
                elif r.rule_type == "UNIQUE":
                    possible_causes.append("Source system re-emitted duplicate primary keys or upstream idempotency token was reused.")
                    recommended_steps.append("Inspect upstream CDC or webhook producer. Enable deduplication in TRANSFORM stage or set severity to RECORD_REJECT.")
                elif r.rule_type == "REFERENTIAL_INTEGRITY":
                    possible_causes.append("Foreign key records missing in dimension table (e.g. transactions arriving before customer profile creation).")
                    recommended_steps.append("Ensure customer ingestion pipeline completes before transaction pipeline executes.")
                elif r.rule_type == "NON_NEGATIVE":
                    possible_causes.append("Financial records contain negative amounts (e.g. refunds or reversals logged as negative debits).")
                    recommended_steps.append("Verify if refunds should be normalized in TRANSFORM stage or rejected at source.")
                elif r.rule_type == "DATA_FRESHNESS":
                    possible_causes.append("Data feed delay, upstream batch processing stall, or source clock desynchronization.")
                    recommended_steps.append("Verify upstream cron scheduler and source database replication lag.")
                else:
                    possible_causes.append(f"Data quality constraints breached on rule '{r.rule_name}'.")
                    recommended_steps.append(f"Remediate upstream data anomalies matching rule '{r.rule_name}'.")

        # 3. Check for Upstream / Network / API errors
        elif any(term in error_message.lower() for term in ["http", "connection", "connect", "timeout", "503", "500", "502"]):
            error_category = "UPSTREAM_UNAVAILABLE"
            facts.append(f"Stage {failing_stage} encountered network or external service error: {error_message}")
            possible_causes.append("External API service downtime, network partition, DNS resolution failure, or rate limiting.")
            recommended_steps.append("Check external service status page. Safe bounded retry with exponential backoff is recommended.")

        # 4. Check for File / Parse errors
        elif any(term in error_message.lower() for term in ["filenotfound", "no such file", "jsondecode", "parsererror", "csv", "trailing comma", "expecting value", "syntax error in json"]):
            error_category = "SOURCE_FORMAT_ERROR"
            facts.append(f"Source file access or parsing error during {failing_stage}: {error_message}")
            possible_causes.append("Source file missing at specified storage location, malformed delimiter, or truncated file transfer.")
            recommended_steps.append("Verify file path existence, file transfer completion, and encoding parameters.")

        # 5. Check for Database errors
        elif any(term in error_message.lower() for term in ["integrityerror", "constraint", "deadlock", "syntaxerror", "database"]):
            error_category = "DATABASE_ERROR"
            facts.append(f"Database transaction failure in stage {failing_stage}: {error_message}")
            possible_causes.append("Database constraint violation, lock acquisition timeout, or database connection pool exhaustion.")
            recommended_steps.append("Inspect unique constraint keys, database logs, and connection pool sizing.")

        # Fallback
        else:
            error_category = "PIPELINE_EXECUTION_ERROR"
            facts.append(f"Unclassified exception in stage {failing_stage}: {error_message}")
            possible_causes.append("Unexpected runtime exception during execution.")
            recommended_steps.append("Review detailed pipeline logs and execution stack trace.")

        return {
            "error_category": error_category,
            "failing_stage": failing_stage,
            "facts": facts,
            "possible_causes": possible_causes,
            "recommended_steps": recommended_steps
        }
