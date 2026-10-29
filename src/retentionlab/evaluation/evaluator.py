"""
RetentionLab Model Evaluation, Artifact Serialization & Reporting.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import joblib
import numpy as np
import pandas as pd
from retentionlab.config.settings import settings


class ModelEvaluator:
    """
    Persists trained model pipelines, metadata, and generates model comparison tables.
    """

    def __init__(self, models_dir: Path = settings.root_dir / "models"):
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def extract_feature_importance(
        self, pipeline: Any, feature_names: list
    ) -> pd.DataFrame:
        """
        Extract Logistic Regression coefficients or tree feature importances.
        """
        clf = pipeline.named_steps["classifier"]
        if hasattr(clf, "coef_"):
            importances = clf.coef_[0]
            metric_type = "logistic_regression_coefficient"
        elif hasattr(clf, "feature_importances_"):
            importances = clf.feature_importances_
            metric_type = "tree_feature_importance"
        else:
            importances = np.zeros(len(feature_names))
            metric_type = "unsupported"

        df_imp = pd.DataFrame(
            {
                "feature_name": feature_names,
                "importance_value": importances,
                "abs_importance": np.abs(importances),
                "metric_type": metric_type,
            }
        ).sort_values("abs_importance", ascending=False)

        return df_imp

    def save_model_artifacts(
        self,
        training_output: Dict[str, Any],
        feature_names: list,
        version: str = "2.0.0",
    ) -> Dict[str, str]:
        """
        Save the best model pipeline and comprehensive metadata JSON.
        """
        best_name = training_output["best_model_name"]
        best_pipe = training_output["best_pipeline"]
        best_thresh = training_output["best_threshold"]
        best_results = training_output["candidate_results"][best_name]

        # 1. Save pipeline
        pipe_path = self.models_dir / "retention_model_pipeline.joblib"
        joblib.dump(best_pipe, pipe_path)

        # 2. Extract feature importance
        imp_df = self.extract_feature_importance(best_pipe, feature_names)
        imp_path = self.models_dir / "feature_importance.csv"
        imp_df.to_csv(imp_path, index=False)

        # 3. Model comparison table
        rows = []
        for model_name, res in training_output["candidate_results"].items():
            vm = res["val_metrics"]
            tm = res["test_metrics"]
            rows.append(
                {
                    "model_name": model_name,
                    "val_roc_auc": vm["roc_auc"],
                    "val_pr_auc": vm["pr_auc"],
                    "val_f1": vm["f1_score"],
                    "val_precision": vm["precision"],
                    "val_recall": vm["recall"],
                    "optimized_threshold": res["optimized_threshold"],
                    "test_roc_auc": tm["roc_auc"],
                    "test_pr_auc": tm["pr_auc"],
                    "test_f1": tm["f1_score"],
                    "test_precision": tm["precision"],
                    "test_recall": tm["recall"],
                    "test_brier_score": tm["brier_score"],
                }
            )
        comp_df = pd.DataFrame(rows)
        comp_path = self.models_dir / "model_comparison.csv"
        comp_df.to_csv(comp_path, index=False)

        # 4. Save metadata JSON
        meta = {
            "model_version": version,
            "best_model_name": best_name,
            "created_at": datetime.now().isoformat(),
            "selected_threshold": best_thresh,
            "feature_count": len(feature_names),
            "feature_names": feature_names,
            "validation_metrics": best_results["val_metrics"],
            "test_metrics": best_results["test_metrics"],
            "hyperparameters": str(best_pipe.named_steps["classifier"].get_params()),
        }
        meta_path = self.models_dir / "model_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return {
            "pipeline_path": str(pipe_path),
            "metadata_path": str(meta_path),
            "comparison_path": str(comp_path),
            "importance_path": str(imp_path),
        }
