"""Evaluation metrics, calibration analysis, and threshold optimization."""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    brier_score_loss,
    precision_recall_curve,
    roc_curve,
)


def evaluate_model_performance(
    model_name: str,
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.50
) -> Dict[str, Any]:
    """Calculate comprehensive evaluation metrics per Section 12 specification."""
    y_pred = (y_prob >= threshold).astype(int)

    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    # Specificity / False Positive Rate
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    fpr = 1.0 - specificity

    return {
        "model_name": model_name,
        "threshold": round(threshold, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "brier_score": round(brier, 4),
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "true_positives": tp,
        "specificity": round(specificity, 4),
        "false_positive_rate": round(fpr, 4),
    }


def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric: str = "f1",
    target_recall: float = 0.75
) -> float:
    """Find the optimal decision threshold based on business objective.

    Options:
    - 'f1': Maximizes F1-score
    - 'target_recall': Finds lowest threshold meeting or exceeding target_recall
    - 'balanced': Minimizes distance between precision and recall
    """
    thresholds = np.linspace(0.10, 0.90, 81)
    best_th = 0.50
    best_val = -1.0

    for th in thresholds:
        preds = (y_prob >= th).astype(int)
        p = precision_score(y_true, preds, zero_division=0)
        r = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)

        if metric == "f1":
            if f1 > best_val:
                best_val = f1
                best_th = th
        elif metric == "target_recall":
            if r >= target_recall:
                # pick threshold closest to target recall while maximizing precision
                if p > best_val:
                    best_val = p
                    best_th = th
        elif metric == "balanced":
            diff = abs(p - r)
            if diff < best_val or best_val < 0:
                best_val = diff
                best_th = th

    return float(round(best_th, 2))


def generate_model_comparison_table(eval_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Produce standardized model comparison table per Section 12.2 specification."""
    df_comp = pd.DataFrame(eval_results)
    cols = [
        "model_name", "threshold", "roc_auc", "pr_auc",
        "precision", "recall", "f1_score", "brier_score",
        "true_positives", "false_positives", "false_negatives", "true_negatives"
    ]
    available_cols = [c for c in cols if c in df_comp.columns]
    return df_comp[available_cols].sort_values("roc_auc", ascending=False).reset_index(drop=True)
