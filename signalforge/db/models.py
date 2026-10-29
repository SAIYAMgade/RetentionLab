import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from signalforge.db.connection import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

# ---------------------------------------------------------
# Metadata & Control Plane Entities
# ---------------------------------------------------------

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # CSV, JSON, REST_API, POSTGRES, STREAM
    config_json = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    pipelines = relationship("Pipeline", back_populates="source", cascade="all, delete-orphan")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    source_id = Column(String(36), ForeignKey("data_sources.id"), nullable=False)
    target_table = Column(String(100), nullable=False)
    schedule = Column(String(50), nullable=False, default="manual")  # cron or 'manual'
    batch_fail_policy = Column(String(50), nullable=False, default="REJECT_AND_CONTINUE")  # FAIL_ON_ERROR | REJECT_AND_CONTINUE
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    source = relationship("DataSource", back_populates="pipelines")
    runs = relationship("PipelineRun", back_populates="pipeline", cascade="all, delete-orphan")
    checkpoints = relationship("PipelineCheckpoint", back_populates="pipeline", cascade="all, delete-orphan")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    pipeline_id = Column(String(36), ForeignKey("pipelines.id"), nullable=False, index=True)
    trigger_type = Column(String(50), nullable=False, default="MANUAL")  # MANUAL, SCHEDULED, LAB_TEST
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, RUNNING, COMPLETED, FAILED
    records_extracted = Column(Integer, default=0, nullable=False)
    records_transformed = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0, nullable=False)
    records_loaded = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    error_category = Column(String(100), nullable=True)  # DATA_QUALITY, SCHEMA_DRIFT, UPSTREAM_FAILURE, DB_ERROR, etc.
    airflow_run_id = Column(String(100), nullable=True)
    duration_ms = Column(Float, default=0.0, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    pipeline = relationship("Pipeline", back_populates="runs")
    stages = relationship("RunStage", back_populates="run", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="run", cascade="all, delete-orphan")
    rejected_records = relationship("RejectedRecord", back_populates="run", cascade="all, delete-orphan")
    diagnostics = relationship("FailureDiagnostic", back_populates="run", uselist=False, cascade="all, delete-orphan")


class RunStage(Base):
    __tablename__ = "run_stages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("pipeline_runs.id"), nullable=False, index=True)
    stage_name = Column(String(50), nullable=False)  # EXTRACT, VALIDATE, TRANSFORM, LOAD, VERIFY
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    records_in = Column(Integer, default=0, nullable=False)
    records_out = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Float, default=0.0, nullable=False)
    details_json = Column(JSON, nullable=False, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    run = relationship("PipelineRun", back_populates="stages")


class SchemaVersion(Base):
    __tablename__ = "schema_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_name = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    columns_json = Column(JSON, nullable=False)  # Dict[col_name, {type, nullable, required}]
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("dataset_name", "version", name="uq_dataset_version"),
    )


class SchemaDriftEvent(Base):
    __tablename__ = "schema_drift_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    pipeline_id = Column(String(36), ForeignKey("pipelines.id"), nullable=True, index=True)
    run_id = Column(String(36), ForeignKey("pipeline_runs.id"), nullable=True, index=True)
    dataset_name = Column(String(100), nullable=False, index=True)
    baseline_version = Column(Integer, nullable=False)
    drift_type = Column(String(50), nullable=False)  # ADDED_COLUMNS, REMOVED_COLUMNS, TYPE_CHANGED, MISSING_REQUIRED
    severity = Column(String(50), nullable=False)    # COMPATIBLE, POTENTIALLY_BREAKING, BREAKING
    diff_json = Column(JSON, nullable=False)
    recommended_action = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DataQualityRule(Base):
    __tablename__ = "data_quality_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_name = Column(String(100), nullable=False, index=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)  # NOT_NULL, UNIQUE, NON_NEGATIVE, VALID_TIMESTAMP, etc.
    params_json = Column(JSON, nullable=False, default=dict)
    severity = Column(String(50), nullable=False, default="RECORD_REJECT")  # RECORD_REJECT, BATCH_FAIL
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("pipeline_runs.id"), nullable=False, index=True)
    rule_id = Column(String(36), nullable=True)
    dataset_name = Column(String(100), nullable=False, index=True)
    rule_name = Column(String(100), nullable=False)
    passed = Column(Boolean, nullable=False)
    total_checked = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    sample_failures_json = Column(JSON, nullable=False, default=list)
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("PipelineRun", back_populates="validation_results")


class RejectedRecord(Base):
    __tablename__ = "rejected_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("pipeline_runs.id"), nullable=False, index=True)
    record_identifier = Column(String(100), nullable=True, index=True)
    raw_data_json = Column(JSON, nullable=False)
    rejection_reasons_json = Column(JSON, nullable=False)  # List[str]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("PipelineRun", back_populates="rejected_records")


class PipelineCheckpoint(Base):
    __tablename__ = "pipeline_checkpoints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    pipeline_id = Column(String(36), ForeignKey("pipelines.id"), nullable=False)
    checkpoint_key = Column(String(100), nullable=False)
    checkpoint_value = Column(String(255), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    pipeline = relationship("Pipeline", back_populates="checkpoints")

    __table_args__ = (
        UniqueConstraint("pipeline_id", "checkpoint_key", name="uq_pipeline_checkpoint"),
    )


class FailureDiagnostic(Base):
    __tablename__ = "failure_diagnostics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("pipeline_runs.id"), nullable=False, unique=True, index=True)
    failing_stage = Column(String(50), nullable=False)
    error_category = Column(String(100), nullable=False)
    facts_json = Column(JSON, nullable=False, default=list)            # Confirmed empirical evidence
    possible_causes_json = Column(JSON, nullable=False, default=list)  # Inferred hypotheses
    recommended_steps_json = Column(JSON, nullable=False, default=list)# Concrete remediation actions
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("PipelineRun", back_populates="diagnostics")


# ---------------------------------------------------------
# Target Domain Business Tables (Idempotent Load Targets)
# ---------------------------------------------------------

class DimCustomer(Base):
    __tablename__ = "dim_customers"

    customer_id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    country = Column(String(50), nullable=False)
    signup_date = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    transactions = relationship("FactTransaction", back_populates="customer")


class FactTransaction(Base):
    __tablename__ = "fact_transactions"

    transaction_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("dim_customers.customer_id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(30), nullable=False)
    transaction_timestamp = Column(DateTime, nullable=False, index=True)
    payment_method = Column(String(50), nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("DimCustomer", back_populates="transactions")

    __table_args__ = (
        Index("ix_fact_tx_cust_time", "customer_id", "transaction_timestamp"),
    )
