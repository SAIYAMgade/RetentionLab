"""
RetentionLab End-to-End Customer Scoring Pipeline.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import joblib
import pandas as pd
from retentionlab.config.settings import settings
from retentionlab.database.connection import get_engine, save_dataframe_to_table
from retentionlab.explainability.explainer import RiskSignalExplainer
from retentionlab.features.catalog import FEATURE_NAMES
from retentionlab.prioritization.engine import RetentionPrioritizationEngine


class CustomerScorer:
    """
    Executes scoring inference on customer snapshot features, generates
    risk explanations, and outputs ranked retention worklists.
    """

    def __init__(
        self,
        model_path: Path = settings.root_dir / "models" / "retention_model_pipeline.joblib",
        metadata_path: Path = settings.root_dir / "models" / "model_metadata.json",
    ):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.pipeline = joblib.load(model_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        self.explainer = RiskSignalExplainer()
        self.prioritizer = RetentionPrioritizationEngine(
            risk_weight=settings.prioritization.risk_weight,
            value_weight=settings.prioritization.value_weight,
            top_cohort_percentage=settings.prioritization.top_cohort_percentage,
        )

    def score_customers(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate probabilities, assign risk bands, attach risk signals,
        and calculate prioritization ranks.
        """
        X = features_df[FEATURE_NAMES].copy()

        # 1. Inference: Probability of Churn (Class 1)
        probs = self.pipeline.predict_proba(X)[:, 1]

        scored = features_df.copy()
        scored["churn_probability"] = probs.round(4)
        scored["risk_band"] = scored["churn_probability"].apply(self.prioritizer.assign_risk_band)

        # 2. Explainable Risk Signals
        signals_list = []
        for _, row in scored.iterrows():
            sigs = self.explainer.extract_customer_signals(row)
            signals_list.append(" | ".join(sigs))
        scored["top_risk_signals"] = signals_list

        # 3. Revenue-Aware Prioritization
        ranked_df = self.prioritizer.prioritize_customers(scored)
        ranked_df["model_version"] = self.metadata.get("model_version", "2.0.0")
        ranked_df["score_id"] = ranked_df.apply(
            lambda r: f"SCR-{r['customer_id']}-{r['snapshot_date'].replace('-', '')}", axis=1
        )

        return ranked_df

    def persist_scores(self, scored_df: pd.DataFrame) -> None:
        """Save scored dataset to data/processed and to database table retention_scores."""
        proc_dir = settings.root_dir / "data" / "processed"
        proc_dir.mkdir(parents=True, exist_ok=True)
        csv_path = proc_dir / "customer_prioritization.csv"
        scored_df.to_csv(csv_path, index=False)

        # Columns for SQL table retention_scores
        db_cols = [
            "score_id",
            "customer_id",
            "snapshot_date",
            "churn_probability",
            "risk_band",
            "prioritization_score",
            "historical_value_proxy",
            "risk_weighted_exposure",
            "top_risk_signals",
            "suggested_action",
            "recommended_next_step",
            "is_top_15_percent",
            "model_version",
        ]
        db_df = scored_df[db_cols].copy()
        engine = get_engine()
        save_dataframe_to_table(db_df, "retention_scores", if_exists="replace", engine=engine)
