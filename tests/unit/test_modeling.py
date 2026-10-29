"""
Unit tests for Machine Learning Modeling & Threshold Optimization.
"""

import pytest
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from retentionlab.models.trainer import ModelTrainer


def test_metric_calculations():
    """Verify evaluation metric computations and confusion matrix."""
    trainer = ModelTrainer()
    y_true = np.array([0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.3, 0.7, 0.8, 0.9])

    metrics = trainer.evaluate_predictions(y_true, y_prob, threshold=0.5)

    assert metrics["roc_auc"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0
    assert metrics["confusion_matrix"]["true_positive"] == 3
    assert metrics["confusion_matrix"]["true_negative"] == 2


def test_threshold_tuning_monotonicity():
    """Verify that threshold scanning produces valid bounds [0.2, 0.8]."""
    trainer = ModelTrainer()
    y_val = np.array([0, 0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.4, 0.6, 0.7, 0.9])

    best_th, best_f1 = trainer.tune_threshold(y_val, y_prob)
    assert 0.2 <= best_th <= 0.8
    assert best_f1 > 0.0
