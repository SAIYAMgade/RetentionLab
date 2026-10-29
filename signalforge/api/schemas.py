from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# ----------------------------------------------------------------
# Data Source Schemas
# ----------------------------------------------------------------
class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    source_type: str = Field(..., pattern="^(CSV|JSON|REST_API|POSTGRES|STREAM)$")
    config_json: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class DataSourceResponse(BaseModel):
    id: str
    name: str
    source_type: str
    config_json: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------------------------------------------------------
# Pipeline Schemas
# ----------------------------------------------------------------
class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    source_id: str
    target_table: str
    schedule: str = "manual"
    batch_fail_policy: str = "REJECT_AND_CONTINUE"  # FAIL_ON_ERROR | REJECT_AND_CONTINUE
    is_active: bool = True

class PipelineResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    source_id: str
    target_table: str
    schedule: str
    batch_fail_policy: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------------------------------------------------------
# Run & Stage Schemas
# ----------------------------------------------------------------
class RunStageResponse(BaseModel):
    id: str
    stage_name: str
    status: str
    records_in: int
    records_out: int
    duration_ms: float
    details_json: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class FailureDiagnosticResponse(BaseModel):
    id: str
    failing_stage: str
    error_category: str
    facts: List[str]
    possible_causes: List[str]
    recommended_steps: List[str]
    created_at: datetime

class PipelineRunResponse(BaseModel):
    id: str
    pipeline_id: str
    trigger_type: str
    status: str
    records_extracted: int
    records_transformed: int
    records_rejected: int
    records_loaded: int
    error_message: Optional[str]
    error_category: Optional[str]
    airflow_run_id: Optional[str]
    duration_ms: float
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class PipelineRunDetailResponse(PipelineRunResponse):
    stages: List[RunStageResponse] = []
    diagnostics: Optional[FailureDiagnosticResponse] = None

# ----------------------------------------------------------------
# Quality & Schema Schemas
# ----------------------------------------------------------------
class QualityRuleCreate(BaseModel):
    dataset_name: str
    rule_name: str
    rule_type: str
    params_json: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "RECORD_REJECT"

class QualityRuleResponse(BaseModel):
    id: str
    dataset_name: str
    rule_name: str
    rule_type: str
    params_json: Dict[str, Any]
    severity: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ValidationResultResponse(BaseModel):
    id: str
    run_id: str
    dataset_name: str
    rule_name: str
    passed: bool
    total_checked: int
    failed_count: int
    sample_failures_json: List[Any]
    execution_time_ms: float
    created_at: datetime

    class Config:
        from_attributes = True

class RejectedRecordResponse(BaseModel):
    id: str
    run_id: str
    record_identifier: Optional[str]
    raw_data_json: Dict[str, Any]
    rejection_reasons_json: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

class SchemaVersionResponse(BaseModel):
    id: str
    dataset_name: str
    version: int
    columns_json: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SchemaDriftEventResponse(BaseModel):
    id: str
    pipeline_id: Optional[str]
    run_id: Optional[str]
    dataset_name: str
    baseline_version: int
    drift_type: str
    severity: str
    diff_json: Dict[str, Any]
    recommended_action: str
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------------------------------------------------------
# Failure Lab Schemas
# ----------------------------------------------------------------
class TriggerScenarioRequest(BaseModel):
    scenario_id: str

# ----------------------------------------------------------------
# Summary & System Status
# ----------------------------------------------------------------
class SystemSummaryResponse(BaseModel):
    total_pipelines: int
    active_pipelines: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    failure_rate_percent: float
    total_records_ingested: int
    total_records_rejected: int
    recent_incidents: List[Dict[str, Any]]
