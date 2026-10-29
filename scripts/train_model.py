"""
RetentionLab Model Training & Evaluation CLI Script.
Fits candidate models, tunes operating threshold on validation split, evaluates test holdout,
and exports model artifacts.
"""

import sys
import time
from pathlib import Path
import pandas as pd
from retentionlab.config.settings import settings
from retentionlab.database.connection import execute_query
from retentionlab.evaluation.evaluator import ModelEvaluator
from retentionlab.features.builder import FeatureBuilder
from retentionlab.labels.target import TargetLabeler
from retentionlab.models.trainer import ModelTrainer


def run_training() -> None:
    print("=== RetentionLab: Starting Model Training & Benchmark Pipeline ===")
    t0 = time.time()

    # Load raw tables from database
    print("Loading entity tables from database...")
    cust = execute_query("SELECT * FROM customers")
    txns = execute_query("SELECT * FROM transactions")
    acts = execute_query("SELECT * FROM customer_activity")
    tcks = execute_query("SELECT * FROM support_tickets")
    camps = execute_query("SELECT * FROM campaign_interactions")
    prods = execute_query("SELECT * FROM products")

    # 1. Feature Engineering (strictly historical <= snapshot)
    print(f"Engineering 44 behavioral features at snapshot date {settings.features.snapshot_date}...")
    builder = FeatureBuilder(snapshot_date=settings.features.snapshot_date)
    features_df = builder.build_features(cust, txns, acts, tcks, camps, prods)

    # 2. Target Labeling (future window > snapshot)
    print(f"Constructing leakage-free target labels (prediction horizon: {settings.data_gen.prediction_horizon_days}d)...")
    labeler = TargetLabeler(
        snapshot_date=settings.features.snapshot_date,
        prediction_horizon_days=settings.data_gen.prediction_horizon_days,
    )
    labels_df = labeler.create_labels(cust, txns)

    # Save processed features & labels
    proc_dir = settings.root_dir / "data" / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(proc_dir / "customer_features_44.csv", index=False)
    labels_df.to_csv(proc_dir / "churn_labels.csv", index=False)

    # 3. Model Training & Comparison
    trainer = ModelTrainer(random_state=settings.modeling.random_state)
    data_splits = trainer.prepare_data(
        features_df,
        labels_df,
        test_size=settings.modeling.test_size,
        val_size=settings.modeling.val_size,
    )

    print(f"\nDataset Splits:")
    print(f"  * Train set: {len(data_splits['y_train'])} customers ({data_splits['y_train'].mean():.1%} churn)")
    print(f"  * Val set:   {len(data_splits['y_val'])} customers ({data_splits['y_val'].mean():.1%} churn)")
    print(f"  * Test set:  {len(data_splits['y_test'])} customers ({data_splits['y_test'].mean():.1%} churn)")

    print("\nTraining and comparing candidate models...")
    train_output = trainer.train_and_compare(data_splits)

    print("\n--- Model Benchmark Results ---")
    for name, res in train_output["candidate_results"].items():
        tm = res["test_metrics"]
        print(f"[{name.upper()}] (Threshold: {res['optimized_threshold']:.2f})")
        print(f"  Test ROC-AUC: {tm['roc_auc']:.4f} | PR-AUC: {tm['pr_auc']:.4f} | F1: {tm['f1_score']:.4f} | Recall: {tm['recall']:.4f} | Precision: {tm['precision']:.4f}")

    print(f"\nSelected Best Model: {train_output['best_model_name']} with threshold {train_output['best_threshold']:.2f}")

    # 4. Serialize artifacts
    evaluator = ModelEvaluator()
    paths = evaluator.save_model_artifacts(train_output, trainer.feature_names)
    print(f"\nArtifacts saved successfully:")
    for k, v in paths.items():
        print(f"  * {k}: {v}")

    print(f"[SUCCESS] Model training and evaluation finished in {time.time() - t0:.2f}s.\n")


if __name__ == "__main__":
    run_training()
