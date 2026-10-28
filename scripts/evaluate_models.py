"""Model evaluation script comparing baseline, logistic regression, and benchmarks."""
import sys
from pathlib import Path
import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retentionlab.config.settings import DEFAULT_CONFIG
from retentionlab.modeling.trainer import prepare_modeling_data
from retentionlab.evaluation.metrics import (
    evaluate_model_performance,
    find_optimal_threshold,
    generate_model_comparison_table,
)
from retentionlab.features.target import create_target_labels


def main():
    print("Executing scripts/evaluate_models.py...")
    config = DEFAULT_CONFIG

    features_df = pd.read_parquet(config.features_path)
    df_raw = pd.read_csv(config.raw_transactions_path)
    target_df = create_target_labels(df_raw, config)

    X_train, X_test, y_train, y_test, _, _ = prepare_modeling_data(features_df, target_df, config)

    models_dir = Path(__file__).resolve().parents[1] / "models"
    eval_list = []

    for model_path in models_dir.glob("*.joblib"):
        name = model_path.stem
        model = joblib.load(model_path)

        y_prob_train = model.predict_proba(X_train)[:, 1]
        opt_thresh = find_optimal_threshold(y_train, y_prob_train, metric="f1")

        y_prob_test = model.predict_proba(X_test)[:, 1]
        metrics = evaluate_model_performance(name, y_test.values, y_prob_test, threshold=opt_thresh)
        eval_list.append(metrics)

    comp_df = generate_model_comparison_table(eval_list)
    print("\n" + "=" * 80)
    print("MODEL COMPARISON TABLE (Held-Out Test Set)")
    print("=" * 80)
    print(comp_df.to_string(index=False))
    print("=" * 80)


if __name__ == "__main__":
    main()
