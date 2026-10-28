"""Model training script with zero-leakage preprocessing pipelines."""
import sys
from pathlib import Path
import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retentionlab.config.settings import DEFAULT_CONFIG
from retentionlab.modeling.trainer import prepare_modeling_data, build_models


def main():
    print("Executing scripts/train_models.py...")
    config = DEFAULT_CONFIG

    features_df = pd.read_parquet(config.features_path)
    df_raw = pd.read_csv(config.raw_transactions_path)
    from retentionlab.features.target import create_target_labels
    target_df = create_target_labels(df_raw, config)

    X_train, X_test, y_train, y_test, _, _ = prepare_modeling_data(features_df, target_df, config)
    models = build_models(config)

    models_dir = Path(__file__).resolve().parents[1] / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"Training {len(models)} models on {len(X_train)} samples...")
    for name, model in models.items():
        model.fit(X_train, y_train)
        model_path = models_dir / f"{name}.joblib"
        joblib.dump(model, model_path)
        print(f"  Saved trained pipeline: {name} -> {model_path}")

    print("Model training complete.")


if __name__ == "__main__":
    main()
