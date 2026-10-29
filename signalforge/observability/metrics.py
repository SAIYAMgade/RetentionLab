from typing import Optional
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)

# Shared global registry
REGISTRY = CollectorRegistry()

# 1. Pipeline runs by status
PIPELINE_RUNS = Counter(
    "signalforge_pipeline_runs_total",
    "Total pipeline runs partitioned by pipeline name and execution status",
    ["pipeline", "status"],
    registry=REGISTRY
)

# 2. Pipeline duration histogram
PIPELINE_DURATION = Histogram(
    "signalforge_pipeline_duration_seconds",
    "Duration of pipeline executions in seconds",
    ["pipeline"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY
)

# 3. Records processed per stage
RECORDS_PROCESSED = Counter(
    "signalforge_records_processed_total",
    "Total records processed partitioned by pipeline and stage",
    ["pipeline", "stage"],
    registry=REGISTRY
)

# 4. Records rejected
RECORDS_REJECTED = Counter(
    "signalforge_records_rejected_total",
    "Total records rejected partitioned by pipeline and rule",
    ["pipeline", "rule"],
    registry=REGISTRY
)

# 5. Data freshness gauge (seconds since latest record timestamp)
DATA_FRESHNESS = Gauge(
    "signalforge_data_freshness_seconds",
    "Seconds since the most recent record timestamp in dataset",
    ["dataset"],
    registry=REGISTRY
)

# 6. Validation failures
VALIDATION_FAILURES = Counter(
    "signalforge_validation_failures_total",
    "Total data quality validation failures by dataset and rule",
    ["dataset", "rule"],
    registry=REGISTRY
)

# 7. Retries total
PIPELINE_RETRIES = Counter(
    "signalforge_retries_total",
    "Total pipeline extraction or loading retries",
    ["pipeline"],
    registry=REGISTRY
)

# 8. Source failures
SOURCE_FAILURES = Counter(
    "signalforge_source_failures_total",
    "Total source connectivity or extraction failures",
    ["source_type"],
    registry=REGISTRY
)

class MetricsCollector:
    @staticmethod
    def record_run(pipeline_name: str, status: str, duration_sec: float) -> None:
        PIPELINE_RUNS.labels(pipeline=pipeline_name, status=status).inc()
        PIPELINE_DURATION.labels(pipeline=pipeline_name).observe(duration_sec)

    @staticmethod
    def record_stage_records(pipeline_name: str, stage: str, count: int) -> None:
        if count > 0:
            RECORDS_PROCESSED.labels(pipeline=pipeline_name, stage=stage).inc(count)

    @staticmethod
    def record_rejection(pipeline_name: str, rule: str, count: int = 1) -> None:
        if count > 0:
            RECORDS_REJECTED.labels(pipeline=pipeline_name, rule=rule).inc(count)

    @staticmethod
    def record_validation_failure(dataset: str, rule: str, count: int = 1) -> None:
        if count > 0:
            VALIDATION_FAILURES.labels(dataset=dataset, rule=rule).inc(count)

    @staticmethod
    def set_data_freshness(dataset: str, age_seconds: float) -> None:
        DATA_FRESHNESS.labels(dataset=dataset).set(age_seconds)

    @staticmethod
    def record_source_failure(source_type: str) -> None:
        SOURCE_FAILURES.labels(source_type=source_type).inc()

    @staticmethod
    def get_metrics_payload() -> tuple[bytes, str]:
        return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
