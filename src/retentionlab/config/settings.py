"""Central configuration settings for RetentionLab."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
EXCEL_DIR = PROJECT_ROOT / "excel"
POWERBI_DIR = PROJECT_ROOT / "powerbi"
SQL_DIR = PROJECT_ROOT / "sql"


@dataclass
class PipelineConfig:
    """Configuration parameters for RetentionLab analytical pipeline."""
    # Random seed for reproducibility
    random_seed: int = 42

    # Timeline definitions
    start_date: str = "2022-01-01"
    cutoff_date: str = "2023-12-31"  # Prediction timestamp (end of observation window)
    future_start_date: str = "2024-01-01"
    future_end_date: str = "2024-03-31"  # 90-day future outcome evaluation window

    # Operational churn definition criteria
    outcome_window_days: int = 90
    min_tenure_days: int = 30  # Minimum customer tenure required at cutoff date

    # Synthetic generation parameters
    n_customers: int = 8500
    approx_transactions: int = 100000

    # Model training
    test_size: float = 0.20
    target_col: str = "is_inactive"
    id_col: str = "customer_id"

    # Business Prioritization
    high_risk_threshold: float = 0.65
    medium_risk_threshold: float = 0.40
    high_monetary_percentile: float = 0.75
    medium_monetary_percentile: float = 0.40

    # Paths
    raw_transactions_path: Path = RAW_DATA_DIR / "transactions.csv"
    sample_transactions_path: Path = SAMPLE_DATA_DIR / "transactions_sample.csv"
    processed_db_path: Path = PROCESSED_DATA_DIR / "retentionlab.db"
    features_path: Path = PROCESSED_DATA_DIR / "customer_features.parquet"
    predictions_path: Path = PROCESSED_DATA_DIR / "customer_predictions.parquet"
    prioritization_path: Path = PROCESSED_DATA_DIR / "customer_prioritization.csv"
    excel_report_path: Path = EXCEL_DIR / "RetentionLab_Executive_Report.xlsx"


DEFAULT_CONFIG = PipelineConfig()
