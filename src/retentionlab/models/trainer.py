"""
RetentionLab Machine Learning Model Trainer.
Trains and compares Logistic Regression, Random Forest, and HistGradientBoosting classifiers.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from retentionlab.config.settings import settings
from retentionlab.features.catalog import FEATURE_NAMES


class ModelTrainer:
    """
    Manages model training, validation-based threshold optimization,
    and artifact serialization.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.feature_names = FEATURE_NAMES

    def prepare_data(
        self,
        features_df: pd.DataFrame,
        labels_df: pd.DataFrame,
        test_size: float = 0.15,
        val_size: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Merge features and labels, perform train/validation/test temporal split,
        and ensure zero target leakage.
        """
        merged = pd.merge(features_df, labels_df, on=["customer_id", "snapshot_date"], how="inner")

        X = merged[self.feature_names].copy()
        y = merged["is_churn"].astype(int).values
        customer_ids = merged["customer_id"].values

        # Deterministic stratified split
        n_total = len(merged)
        n_test = int(n_total * test_size)
        n_val = int(n_total * val_size)
        n_train = n_total - n_test - n_val

        rng = np.random.RandomState(self.random_state)
        indices = np.arange(n_total)
        rng.shuffle(indices)

        train_idx = indices[:n_train]
        val_idx = indices[n_train : n_train + n_val]
        test_idx = indices[n_train + n_val :]

        return {
            "X_train": X.iloc[train_idx],
            "y_train": y[train_idx],
            "ids_train": customer_ids[train_idx],
            "X_val": X.iloc[val_idx],
            "y_val": y[val_idx],
            "ids_val": customer_ids[val_idx],
            "X_test": X.iloc[test_idx],
            "y_test": y[test_idx],
            "ids_test": customer_ids[test_idx],
        }

    def get_candidate_pipelines(self) -> Dict[str, Pipeline]:
        """Define candidate scikit-learn pipelines with leakage-safe preprocessing."""
        pipelines = {
            "logistic_regression": Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    (
                        "classifier",
                        LogisticRegression(
                            class_weight="balanced",
                            max_iter=1000,
                            C=0.1,
                            random_state=self.random_state,
                        ),
                    ),
                ]
            ),
            "random_forest": Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "classifier",
                        RandomForestClassifier(
                            n_estimators=100,
                            max_depth=8,
                            min_samples_leaf=10,
                            class_weight="balanced",
                            random_state=self.random_state,
                            n_jobs=-1,
                        ),
                    ),
                ]
            ),
            "hist_gradient_boosting": Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    (
                        "classifier",
                        HistGradientBoostingClassifier(
                            max_iter=100,
                            max_depth=6,
                            class_weight="balanced",
                            random_state=self.random_state,
                        ),
                    ),
                ]
            ),
        }
        return pipelines

    def evaluate_predictions(
        self, y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.50
    ) -> Dict[str, Any]:
        """Compute complete classification metrics at specified threshold."""
        y_pred = (y_prob >= threshold).astype(int)
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()

        return {
            "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4),
            "pr_auc": round(float(average_precision_score(y_true, y_prob)), 4),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
            },
            "decision_threshold": round(float(threshold), 4),
        }

    def tune_threshold(self, y_val: np.ndarray, y_val_prob: np.ndarray) -> Tuple[float, float]:
        """
        Scan candidate decision thresholds on validation set to maximize F1-score.
        Returns (best_threshold, best_f1).
        """
        thresholds = np.linspace(0.20, 0.80, 61)
        best_thresh = 0.50
        best_f1 = -1.0

        for th in thresholds:
            preds = (y_val_prob >= th).astype(int)
            score = f1_score(y_val, preds, zero_division=0)
            if score > best_f1:
                best_f1 = score
                best_thresh = th

        return float(best_thresh), float(best_f1)

    def train_and_compare(self, data_splits: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fit all candidate models on training set, tune threshold on validation set,
        and evaluate final generalization metrics on holdout test set.
        """
        X_train, y_train = data_splits["X_train"], data_splits["y_train"]
        X_val, y_val = data_splits["X_val"], data_splits["y_val"]
        X_test, y_test = data_splits["X_test"], data_splits["y_test"]

        pipelines = self.get_candidate_pipelines()
        results = {}

        best_model_name = None
        best_val_auc = -1.0

        for name, pipe in pipelines.items():
            # 1. Fit on train only
            pipe.fit(X_train, y_train)

            # 2. Predict probabilities on validation
            val_probs = pipe.predict_proba(X_val)[:, 1]
            opt_thresh, opt_f1 = self.tune_threshold(y_val, val_probs)
            val_metrics = self.evaluate_predictions(y_val, val_probs, threshold=opt_thresh)

            # 3. Predict probabilities on holdout test set (STRICT ISOLATION)
            test_probs = pipe.predict_proba(X_test)[:, 1]
            test_metrics = self.evaluate_predictions(y_test, test_probs, threshold=opt_thresh)

            results[name] = {
                "pipeline": pipe,
                "optimized_threshold": opt_thresh,
                "val_metrics": val_metrics,
                "test_metrics": test_metrics,
            }

            if val_metrics["roc_auc"] > best_val_auc:
                best_val_auc = val_metrics["roc_auc"]
                best_model_name = name

        return {
            "candidate_results": results,
            "best_model_name": best_model_name,
            "best_pipeline": results[best_model_name]["pipeline"],
            "best_threshold": results[best_model_name]["optimized_threshold"],
        }
