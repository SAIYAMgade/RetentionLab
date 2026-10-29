"""
RetentionLab Configuration Module.
Provides centralized access to application parameters, paths, and business rules.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_FILE = ROOT_DIR / "config" / "settings.yaml"


@dataclass
class DataGenConfig:
    random_seed: int = 42
    num_customers: int = 5000
    target_transaction_count: int = 100000
    start_date: str = "2025-01-01"
    end_date: "2026-06-01" = "2026-06-01"
    snapshot_date: str = "2026-04-01"
    prediction_horizon_days: int = 60
    historical_window_days: int = 180
    min_tenure_days: int = 30


@dataclass
class DatabaseConfig:
    dialect: str = "sqlite"
    db_path: str = "data/retentionlab.db"
    echo: bool = False

    @property
    def connection_url(self) -> str:
        full_path = ROOT_DIR / self.db_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{full_path}"


@dataclass
class FeaturesConfig:
    feature_count: int = 44
    snapshot_date: str = "2026-04-01"


@dataclass
class ModelingConfig:
    random_state: int = 42
    test_size: float = 0.15
    val_size: float = 0.15
    candidate_models: List[str] = field(
        default_factory=lambda: ["logistic_regression", "random_forest", "hist_gradient_boosting"]
    )
    primary_metric: str = "roc_auc"
    default_decision_threshold: float = 0.45


@dataclass
class PrioritizationConfig:
    top_cohort_percentage: float = 0.15
    risk_weight: float = 0.55
    value_weight: float = 0.45
    risk_bands: Dict[str, float] = field(
        default_factory=lambda: {
            "critical": 0.75,
            "high": 0.50,
            "moderate": 0.25,
            "low": 0.0,
        }
    )


@dataclass
class Settings:
    root_dir: Path = ROOT_DIR
    data_gen: DataGenConfig = field(default_factory=DataGenConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    modeling: ModelingConfig = field(default_factory=ModelingConfig)
    prioritization: PrioritizationConfig = field(default_factory=PrioritizationConfig)

    @classmethod
    def load(cls, config_path: Path = CONFIG_FILE) -> "Settings":
        if not config_path.exists():
            return cls()

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        dg = data.get("data_generation", {})
        db = data.get("database", {})
        feat = data.get("features", {})
        mod = data.get("modeling", {})
        prio = data.get("prioritization", {})

        return cls(
            data_gen=DataGenConfig(**dg) if dg else DataGenConfig(),
            database=DatabaseConfig(**db) if db else DatabaseConfig(),
            features=FeaturesConfig(**feat) if feat else FeaturesConfig(),
            modeling=ModelingConfig(**mod) if mod else ModelingConfig(),
            prioritization=PrioritizationConfig(**prio) if prio else PrioritizationConfig(),
        )


settings = Settings.load()
