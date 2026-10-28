"""Model training pipelines with strict zero-leakage preprocessing."""
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split

from retentionlab.config.settings import DEFAULT_CONFIG, PipelineConfig
from retentionlab.features.builder import FEATURE_NAMES


class HeuristicRecencyBaseline:
    """Simple rule-based baseline: Predicts inactivity if recency > threshold."""
    def __init__(self, recency_threshold: int = 90):
        self.recency_threshold = recency_threshold
        self.classes_ = np.array([0, 1])

    def fit(self, X: pd.DataFrame, y: np.ndarray = None):
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            rec = X["recency_days"].values
        else:
            rec = X[:, 0]  # assumes recency is first feature
        # Smooth proxy probability based on recency
        prob_inactive = np.clip(rec / (self.recency_threshold * 2.0), 0.05, 0.95)
        prob_active = 1.0 - prob_inactive
        return np.column_stack([prob_active, prob_inactive])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            rec = X["recency_days"].values
        else:
            rec = X[:, 0]
        return (rec >= self.recency_threshold).astype(int)


def prepare_modeling_data(
    features_df: pd.DataFrame,
    target_df: pd.DataFrame,
    config: PipelineConfig = DEFAULT_CONFIG
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.DataFrame, pd.DataFrame]:
    """Join features and target, then split into train/test splits deterministically."""
    merged = pd.merge(features_df, target_df[["customer_id", config.target_col]], on="customer_id", how="inner")

    feature_cols = [c for c in FEATURE_NAMES if c in merged.columns]
    X = merged[feature_cols].copy()
    y = merged[config.target_col].copy()
    cust_ids = merged[["customer_id"]].copy()

    X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
        X, y, cust_ids,
        test_size=config.test_size,
        random_state=config.random_seed,
        stratify=y
    )

    return X_train, X_test, y_train, y_test, ids_train, ids_test


def build_models(config: PipelineConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Build standardized scikit-learn model pipelines.

    Preprocessing (imputation + scaling) is strictly encapsulated inside each pipeline.
    """
    models = {
        "HeuristicBaseline": HeuristicRecencyBaseline(recency_threshold=90),

        "LogisticRegression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                C=0.5,
                class_weight="balanced",
                max_iter=1000,
                random_state=config.random_seed
            ))
        ]),

        "KNN": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", KNeighborsClassifier(
                n_neighbors=15,
                weights="distance"
            ))
        ]),

        "RandomForest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", RandomForestClassifier(
                n_estimators=150,
                max_depth=8,
                min_samples_split=10,
                class_weight="balanced",
                random_state=config.random_seed,
                n_jobs=-1
            ))
        ]),

        "GradientBoosting": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", HistGradientBoostingClassifier(
                max_iter=100,
                max_depth=6,
                learning_rate=0.08,
                random_state=config.random_seed
            ))
        ])
    }
    return models
