"""Unit tests for modeling, preprocessing, evaluation metrics, and reproducibility."""
import numpy as np
import pandas as pd
import pytest
from retentionlab.config.settings import PipelineConfig
from retentionlab.modeling.trainer import prepare_modeling_data, build_models
from retentionlab.evaluation.metrics import evaluate_model_performance, find_optimal_threshold
from retentionlab.features.builder import FEATURE_NAMES


@pytest.fixture
def dummy_modeling_dataset():
    """Deterministic feature and target dataset with 100 customers."""
    np.random.seed(42)
    n = 100
    cust_ids = [f"C_{i:03d}" for i in range(n)]

    feat_dict = {"customer_id": cust_ids}
    for col in FEATURE_NAMES:
        feat_dict[col] = np.random.uniform(1.0, 100.0, size=n)

    feat_df = pd.DataFrame(feat_dict)
    # Recency strongly correlates with target
    target_labels = (feat_df["recency_days"] > 50).astype(int)
    target_df = pd.DataFrame({
        "customer_id": cust_ids,
        "is_inactive": target_labels
    })
    return feat_df, target_df


def test_train_test_separation(dummy_modeling_dataset):
    """Test 11: Train/test split separation and stratified proportions."""
    feat_df, target_df = dummy_modeling_dataset
    config = PipelineConfig(test_size=0.20, random_seed=42)

    X_train, X_test, y_train, y_test, _, _ = prepare_modeling_data(feat_df, target_df, config)

    assert len(X_train) == 80
    assert len(X_test) == 20
    # Stratified check
    train_ratio = y_train.mean()
    test_ratio = y_test.mean()
    assert abs(train_ratio - test_ratio) < 0.10


def test_preprocessing_fitted_only_on_train(dummy_modeling_dataset):
    """Test 12: Pipeline encapsulation ensures scaling params come strictly from X_train."""
    feat_df, target_df = dummy_modeling_dataset
    config = PipelineConfig(test_size=0.20, random_seed=42)
    X_train, X_test, y_train, y_test, _, _ = prepare_modeling_data(feat_df, target_df, config)

    models = build_models(config)
    lr_pipe = models["LogisticRegression"]
    lr_pipe.fit(X_train, y_train)

    scaler = lr_pipe.named_steps["scaler"]
    # Check that scaler mean matches X_train mean, not X_test
    np.testing.assert_allclose(scaler.mean_, X_train.mean().values, rtol=1e-4)


def test_prediction_output_shape(dummy_modeling_dataset):
    """Test 13: Prediction probability shape matches test set."""
    feat_df, target_df = dummy_modeling_dataset
    config = PipelineConfig(test_size=0.20, random_seed=42)
    X_train, X_test, y_train, y_test, _, _ = prepare_modeling_data(feat_df, target_df, config)

    models = build_models(config)
    for name, model in models.items():
        model.fit(X_train, y_train)
        probs = model.predict_proba(X_test)
        assert probs.shape == (20, 2)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()


def test_evaluation_metric_calculations():
    """Test 14: Comprehensive evaluation metrics calculation."""
    y_true = np.array([1, 1, 1, 0, 0, 0])
    y_prob = np.array([0.9, 0.8, 0.4, 0.2, 0.1, 0.6])

    metrics = evaluate_model_performance("TestModel", y_true, y_prob, threshold=0.50)
    assert "roc_auc" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "brier_score" in metrics
    assert metrics["true_positives"] == 2
    assert metrics["false_negatives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["true_negatives"] == 2


def test_threshold_selection():
    """Test 15: Optimal threshold finder returns a valid probability between 0.1 and 0.9."""
    y_true = np.array([1, 1, 1, 0, 0, 0, 1, 0])
    y_prob = np.array([0.9, 0.8, 0.7, 0.2, 0.3, 0.1, 0.6, 0.4])

    th = find_optimal_threshold(y_true, y_prob, metric="f1")
    assert 0.10 <= th <= 0.90


def test_reproducibility_under_fixed_seed(dummy_modeling_dataset):
    """Test 20: Execution with identical config yields identical model weights and predictions."""
    feat_df, target_df = dummy_modeling_dataset
    config = PipelineConfig(test_size=0.20, random_seed=42)

    X_train1, X_test1, y_train1, _, _, _ = prepare_modeling_data(feat_df, target_df, config)
    X_train2, X_test2, y_train2, _, _, _ = prepare_modeling_data(feat_df, target_df, config)

    m1 = build_models(config)["LogisticRegression"].fit(X_train1, y_train1)
    m2 = build_models(config)["LogisticRegression"].fit(X_train2, y_train2)

    p1 = m1.predict_proba(X_test1)
    p2 = m2.predict_proba(X_test2)
    np.testing.assert_array_equal(p1, p2)
